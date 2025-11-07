"""
DOR Code Assignment - Multi-County Batch Processor (Production Version)
========================================================================
Processes properties with NULL/empty/99 DOR codes using intelligent classification.

Features:
- Multi-county support with configurable targets
- Comprehensive error handling and retry logic
- Structured logging with rotation
- Failed batch recovery (saves to JSON)
- Progress tracking and resumption
- Performance metrics
- No hardcoded credentials (environment variables only)

SECURITY:
- ALL credentials via environment variables
- NO fallback default values
- Service key validation on startup

USAGE:
    Set environment variables:
        SUPABASE_URL=https://your-project.supabase.co
        SUPABASE_SERVICE_KEY=your_service_role_key_here
        TARGET_COUNTY=DADE  # Optional, default: DADE
        BATCH_SIZE=5000     # Optional, default: 5000

    Run:
        python assign_dor_codes_improved.py

    Or for multiple counties:
        python assign_dor_codes_improved.py --counties DADE,BROWARD,PALM_BEACH

LOGGING:
    Logs are written to: logs/dor_code_assignment_YYYYMMDD_HHMMSS.log
    Failed batches saved to: logs/failed_batches_YYYYMMDD_HHMMSS.json

REQUIREMENTS:
    pip install supabase python-dotenv
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from supabase import create_client, Client

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# ============================================
# CONFIGURATION (All from environment)
# ============================================

def get_config():
    """Load and validate configuration from environment variables."""
    config = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
        "BATCH_SIZE": int(os.getenv("BATCH_SIZE", "5000")),
        "TARGET_COUNTY": os.getenv("TARGET_COUNTY", "DADE"),
        "MAX_BATCHES": int(os.getenv("MAX_BATCHES", "200")),
        "RETRY_ATTEMPTS": int(os.getenv("RETRY_ATTEMPTS", "3")),
        "RETRY_DELAY": float(os.getenv("RETRY_DELAY", "1.0")),
    }

    # Validate required fields
    if not config["SUPABASE_URL"]:
        raise RuntimeError(
            "SUPABASE_URL environment variable is required. "
            "Set it to your Supabase project URL."
        )

    if not config["SUPABASE_SERVICE_KEY"]:
        raise RuntimeError(
            "SUPABASE_SERVICE_KEY environment variable is required. "
            "Set it to your service role key. "
            "NEVER hardcode this value in the script!"
        )

    return config


# ============================================
# LOGGING SETUP
# ============================================

def setup_logging() -> Tuple[logging.Logger, Path]:
    """Configure structured logging with file rotation."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"dor_code_assignment_{timestamp}.log"

    # Configure logger
    logger = logging.getLogger("DORCodeAssignment")
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file


# ============================================
# CLASSIFICATION LOGIC
# ============================================

def get_classification(building_value: float, land_value: float, just_value: float) -> Tuple[str, str]:
    """
    Apply intelligent DOR classification logic based on property values.

    Returns:
        Tuple of (land_use_code, property_use_description)

    Classification priority:
    1. Large multi-family (high building value)
    2. Industrial (very high building, low land)
    3. Commercial (high just value + significant building)
    4. Agricultural (land value >> building value)
    5. Condo (mid-range values)
    6. Vacant (minimal building value)
    7. Single-family residential (default)
    """
    building_value = building_value or 0
    land_value = land_value or 0
    just_value = just_value or 0

    # Priority-ordered classification
    if building_value > 500000 and building_value > land_value * 2:
        return ("02", "MF 10+")
    elif building_value > 1000000 and land_value < 500000:
        return ("24", "Industrial")
    elif just_value > 500000 and building_value > 200000:
        return ("17", "Commercial")
    elif land_value > building_value * 5 and land_value > 100000:
        return ("01", "Agricultural")
    elif 100000 <= just_value <= 500000 and 50000 <= building_value <= 300000:
        return ("03", "Condo")
    elif land_value > 0 and building_value < 1000:
        return ("10", "Vacant Res")
    elif building_value > 50000 and building_value > land_value:
        return ("00", "SFR")
    else:
        return ("00", "SFR")


# ============================================
# DATABASE OPERATIONS
# ============================================

class DORCodeProcessor:
    """Handles DOR code assignment with retry logic and error recovery."""

    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.supabase = self._init_supabase()
        self.failed_batches = []
        self.stats = {
            "total_processed": 0,
            "total_failed": 0,
            "batches_completed": 0,
            "batches_failed": 0,
            "start_time": datetime.now(),
        }

    def _init_supabase(self) -> Client:
        """Initialize Supabase client with validation."""
        self.logger.info("Initializing Supabase client...")
        try:
            client = create_client(
                self.config["SUPABASE_URL"],
                self.config["SUPABASE_SERVICE_KEY"]
            )
            # Test connection
            client.table("florida_parcels").select("id").limit(1).execute()
            self.logger.info("✓ Supabase connection established")
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase: {e}")
            raise

    def fetch_batch(self, county: str) -> List[Dict]:
        """Fetch one batch of properties needing DOR codes with retry logic."""
        for attempt in range(self.config["RETRY_ATTEMPTS"]):
            try:
                properties = []

                # Fetch NULL land_use_code
                resp = (
                    self.supabase.from_("florida_parcels")
                    .select("id,parcel_id,building_value,land_value,just_value")
                    .eq("year", 2025)
                    .eq("county", county)
                    .is_("land_use_code", "null")
                    .order("id")
                    .limit(self.config["BATCH_SIZE"])
                    .execute()
                )
                properties.extend(resp.data or [])

                # Also fetch empty string codes
                if len(properties) < self.config["BATCH_SIZE"]:
                    resp2 = (
                        self.supabase.from_("florida_parcels")
                        .select("id,parcel_id,building_value,land_value,just_value")
                        .eq("year", 2025)
                        .eq("county", county)
                        .eq("land_use_code", "")
                        .order("id")
                        .limit(self.config["BATCH_SIZE"] - len(properties))
                        .execute()
                    )
                    properties.extend(resp2.data or [])

                # Also fetch '99' codes (unknown)
                if len(properties) < self.config["BATCH_SIZE"]:
                    resp3 = (
                        self.supabase.from_("florida_parcels")
                        .select("id,parcel_id,building_value,land_value,just_value")
                        .eq("year", 2025)
                        .eq("county", county)
                        .eq("land_use_code", "99")
                        .order("id")
                        .limit(self.config["BATCH_SIZE"] - len(properties))
                        .execute()
                    )
                    properties.extend(resp3.data or [])

                return properties

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.config['RETRY_ATTEMPTS']} failed: {e}"
                )
                if attempt < self.config["RETRY_ATTEMPTS"] - 1:
                    delay = self.config["RETRY_DELAY"] * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error("All retry attempts exhausted")
                    return []

        return []

    def bulk_update(self, rows: List[Dict]) -> int:
        """Bulk update properties with DOR codes and retry on failure."""
        if not rows:
            return 0

        # Prepare payload with classifications
        payload = []
        for r in rows:
            code, use = get_classification(
                r.get("building_value"),
                r.get("land_value"),
                r.get("just_value")
            )
            payload.append({
                "id": r["id"],
                "land_use_code": code,
                "property_use": use,
            })

        # Attempt update with retries
        for attempt in range(self.config["RETRY_ATTEMPTS"]):
            try:
                self.supabase.from_("florida_parcels").upsert(
                    payload, on_conflict="id"
                ).execute()
                return len(payload)

            except Exception as e:
                self.logger.warning(
                    f"Update attempt {attempt + 1}/{self.config['RETRY_ATTEMPTS']} failed: {e}"
                )
                if attempt < self.config["RETRY_ATTEMPTS"] - 1:
                    delay = self.config["RETRY_DELAY"] * (2 ** attempt)
                    time.sleep(delay)
                else:
                    # Save failed batch for recovery
                    self.failed_batches.append({
                        "timestamp": datetime.now().isoformat(),
                        "rows": rows,
                        "error": str(e)
                    })
                    self.stats["batches_failed"] += 1
                    return 0

        return 0

    def get_remaining_count(self, county: str) -> int:
        """Count remaining properties needing DOR codes."""
        try:
            counts = []
            for condition in ["null", "", "99"]:
                if condition == "null":
                    resp = (
                        self.supabase.from_("florida_parcels")
                        .select("id", count="exact")
                        .eq("year", 2025)
                        .eq("county", county)
                        .is_("land_use_code", "null")
                        .execute()
                    )
                else:
                    resp = (
                        self.supabase.from_("florida_parcels")
                        .select("id", count="exact")
                        .eq("year", 2025)
                        .eq("county", county)
                        .eq("land_use_code", condition)
                        .execute()
                    )
                counts.append(resp.count or 0)

            return sum(counts)
        except Exception as e:
            self.logger.error(f"Error counting remaining properties: {e}")
            return -1

    def get_coverage_stats(self, county: str) -> Tuple[int, int, float]:
        """Get current coverage statistics for a county."""
        try:
            # Total properties
            total_resp = (
                self.supabase.from_("florida_parcels")
                .select("id", count="exact")
                .eq("year", 2025)
                .eq("county", county)
                .execute()
            )

            # Properties with valid codes
            coded_resp = (
                self.supabase.from_("florida_parcels")
                .select("id", count="exact")
                .eq("year", 2025)
                .eq("county", county)
                .not_.is_("land_use_code", "null")
                .neq("land_use_code", "")
                .neq("land_use_code", "99")
                .execute()
            )

            total = total_resp.count or 0
            coded = coded_resp.count or 0
            coverage = (coded / total * 100) if total > 0 else 0

            return total, coded, coverage

        except Exception as e:
            self.logger.error(f"Error getting coverage stats: {e}")
            return 0, 0, 0

    def process_county(self, county: str) -> bool:
        """Process all batches for a single county."""
        self.logger.info("=" * 80)
        self.logger.info(f"PROCESSING COUNTY: {county}")
        self.logger.info("=" * 80)

        # Initial stats
        initial_remaining = self.get_remaining_count(county)
        total, coded, coverage = self.get_coverage_stats(county)

        self.logger.info(f"Initial NULL properties: {initial_remaining:,}")
        self.logger.info(f"Initial coverage: {coded:,}/{total:,} ({coverage:.2f}%)")

        # Process batches
        batch_num = 1
        county_processed = 0

        while batch_num <= self.config["MAX_BATCHES"]:
            self.logger.info(
                f"[Batch {batch_num}] Fetching {self.config['BATCH_SIZE']} "
                f"properties from {county}..."
            )

            rows = self.fetch_batch(county)

            if not rows:
                self.logger.info(f"[Batch {batch_num}] No more properties found!")
                break

            self.logger.info(f"[Batch {batch_num}] Retrieved {len(rows)} properties")

            updated = self.bulk_update(rows)
            if updated > 0:
                self.logger.info(f"[Batch {batch_num}] ✓ Updated {updated} properties")
                county_processed += updated
                self.stats["total_processed"] += updated
                self.stats["batches_completed"] += 1
            else:
                self.logger.error(f"[Batch {batch_num}] ✗ Failed to update batch")
                self.stats["total_failed"] += len(rows)

            # Progress update
            remaining = self.get_remaining_count(county)
            total, coded, coverage = self.get_coverage_stats(county)

            self.logger.info(f"  Processed this county: {county_processed:,}")
            self.logger.info(f"  Remaining NULL: {remaining:,}")
            self.logger.info(f"  Current coverage: {coded:,}/{total:,} ({coverage:.2f}%)")

            # Small delay to respect rate limits
            time.sleep(0.25)

            batch_num += 1

        # County summary
        final_total, final_coded, final_coverage = self.get_coverage_stats(county)
        self.logger.info(f"\n{county} Summary:")
        self.logger.info(f"  Processed: {county_processed:,}")
        self.logger.info(
            f"  Final coverage: {final_coded:,}/{final_total:,} ({final_coverage:.2f}%)"
        )

        return county_processed > 0

    def save_failed_batches(self, log_file: Path):
        """Save failed batches to JSON for manual recovery."""
        if not self.failed_batches:
            return

        failed_file = log_file.parent / f"failed_batches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_batches, f, indent=2)
            self.logger.warning(f"Saved {len(self.failed_batches)} failed batches to: {failed_file}")
        except Exception as e:
            self.logger.error(f"Failed to save failed batches: {e}")

    def print_final_summary(self):
        """Print final processing summary with performance metrics."""
        duration = datetime.now() - self.stats["start_time"]
        duration_seconds = duration.total_seconds()

        self.logger.info("\n" + "=" * 80)
        self.logger.info("FINAL SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Total processed: {self.stats['total_processed']:,} properties")
        self.logger.info(f"Total failed: {self.stats['total_failed']:,} properties")
        self.logger.info(f"Successful batches: {self.stats['batches_completed']}")
        self.logger.info(f"Failed batches: {self.stats['batches_failed']}")
        self.logger.info(f"Duration: {duration}")

        if duration_seconds > 0:
            rate = self.stats['total_processed'] / duration_seconds
            self.logger.info(f"Processing rate: {rate:.1f} properties/second")

        self.logger.info("=" * 80)


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Assign DOR codes to Florida properties"
    )
    parser.add_argument(
        "--counties",
        type=str,
        help="Comma-separated list of counties (default: from TARGET_COUNTY env var)"
    )
    args = parser.parse_args()

    # Setup logging
    logger, log_file = setup_logging()

    try:
        # Load configuration
        config = get_config()

        # Determine counties to process
        if args.counties:
            counties = [c.strip().upper() for c in args.counties.split(",")]
        else:
            counties = [config["TARGET_COUNTY"].upper()]

        logger.info("=" * 80)
        logger.info("DOR CODE ASSIGNMENT - PRODUCTION VERSION")
        logger.info("=" * 80)
        logger.info(f"Target counties: {', '.join(counties)}")
        logger.info(f"Batch size: {config['BATCH_SIZE']} properties")
        logger.info(f"Max batches per county: {config['MAX_BATCHES']}")
        logger.info(f"Retry attempts: {config['RETRY_ATTEMPTS']}")
        logger.info(f"Log file: {log_file}")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        # Initialize processor
        processor = DORCodeProcessor(config, logger)

        # Process each county
        for county in counties:
            success = processor.process_county(county)
            if not success:
                logger.warning(f"No properties processed for {county}")

        # Save any failed batches
        processor.save_failed_batches(log_file)

        # Print summary
        processor.print_final_summary()

        logger.info(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log file: {log_file}")

        # Exit with error code if any failures
        if processor.stats["batches_failed"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
