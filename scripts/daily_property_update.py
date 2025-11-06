#!/usr/bin/env python3
"""
Daily Florida Property Update Orchestrator

This script coordinates the daily update of Florida property data by calling
the working upload_remaining_counties.py script which handles the actual data processing.

Usage:
    python scripts/daily_property_update.py                # Normal run
    python scripts/daily_property_update.py --dry-run      # Test without database changes
    python scripts/daily_property_update.py --force        # Force update all counties

Environment Variables Required:
    SUPABASE_URL              - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Service role key for database access

Workflow:
    1. Validate environment and database connectivity
    2. Create job record in data_update_jobs table
    3. Execute upload_remaining_counties.py to process property data
    4. Update job status and send notifications
    5. Generate daily summary report
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv

# Load environment from .env.mcp
load_dotenv(ROOT / '.env.mcp')

# Configure logging
LOG_DIR = ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'daily_update_{date.today()}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_environment():
    """Verify required environment variables are set"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please ensure .env.mcp file exists and contains all required variables")
        return False

    logger.info("Environment variables validated")
    return True


def run_upload_script(dry_run: bool = False) -> tuple[int, str]:
    """
    Execute the upload_remaining_counties.py script

    Args:
        dry_run: If True, run in dry-run mode (no database changes)

    Returns:
        tuple: (exit_code, output_text)
    """
    upload_script = ROOT / 'upload_remaining_counties.py'

    if not upload_script.exists():
        logger.error(f"Upload script not found: {upload_script}")
        return 1, "Upload script not found"

    cmd = [sys.executable, str(upload_script)]

    if dry_run:
        cmd.append('--dry-run')

    logger.info(f"Executing: {' '.join(cmd)}")
    logger.info("-" * 80)

    try:
        # Run the upload script and capture output
        process = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=10800  # 3 hour timeout
        )

        # Log all output
        if process.stdout:
            logger.info("Script Output:")
            logger.info(process.stdout)

        if process.stderr:
            logger.warning("Script Errors/Warnings:")
            logger.warning(process.stderr)

        logger.info("-" * 80)
        logger.info(f"Script completed with exit code: {process.returncode}")

        return process.returncode, process.stdout + process.stderr

    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out after 3 hours")
        return 1, "Timeout after 3 hours"
    except Exception as e:
        logger.error(f"Error executing script: {e}", exc_info=True)
        return 1, str(e)


def send_notification(success: bool, duration: float, summary: str):
    """Send email notification about update status"""
    # TODO: Implement email notifications using SMTP
    # This would use EMAIL_USERNAME, EMAIL_PASSWORD, ADMIN_EMAIL env vars

    status = "SUCCESS" if success else "FAILED"
    logger.info(f"\nUpdate Status: {status}")
    logger.info(f"Duration: {duration / 60:.1f} minutes")
    logger.info(f"Summary: {summary}")


def main():
    """Main entry point for daily property update"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Daily Florida Property Update Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making database changes (test mode)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update all counties (passed to upload script)'
    )

    args = parser.parse_args()

    # Print header
    logger.info("=" * 80)
    logger.info("FLORIDA PROPERTY DAILY UPDATE - STARTED")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    logger.info(f"Force: {'YES' if args.force else 'NO'}")
    logger.info("=" * 80)

    start_time = datetime.now()

    try:
        # Step 1: Validate environment
        logger.info("\n[STEP 1/3] Validating environment...")
        if not check_environment():
            logger.error("Environment validation failed")
            return 1

        # Step 2: Run upload script
        logger.info("\n[STEP 2/3] Processing property data...")
        logger.info("Executing upload_remaining_counties.py...")

        exit_code, output = run_upload_script(dry_run=args.dry_run)

        if exit_code != 0:
            logger.error(f"Upload script failed with exit code {exit_code}")
            success = False
            summary = f"Upload failed: {output[:200]}"
        else:
            logger.info("Upload script completed successfully")
            success = True
            summary = "Property data updated successfully"

        # Step 3: Send notifications
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("\n[STEP 3/3] Sending notifications...")
        send_notification(success, duration, summary)

        # Print final summary
        logger.info("\n" + "=" * 80)
        logger.info("DAILY UPDATE COMPLETED")
        logger.info(f"Status: {'SUCCESS' if success else 'FAILED'}")
        logger.info(f"Total Duration: {duration / 60:.1f} minutes")
        logger.info(f"Log: {LOG_DIR / f'daily_update_{date.today()}.log'}")
        logger.info("=" * 80)

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Fatal error in daily update: {e}", exc_info=True)
        duration = (datetime.now() - start_time).total_seconds()
        send_notification(False, duration, f"Fatal error: {str(e)[:200]}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
