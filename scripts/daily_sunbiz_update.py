#!/usr/bin/env python3
"""
Daily Sunbiz Update Orchestrator

Downloads and processes Florida Department of State business entity data.
Runs daily to keep Sunbiz database synchronized with state records.

Source: SFTP sftp.floridados.gov
Files: Corporate (c), Events (ce), Fictitious (fn)
Format: Fixed-width text files (date-based naming: yyyymmddTYPE.txt)

Workflow:
1. Connect to SFTP server
2. Download today's files (c, ce, fn)
3. Parse fixed-width format
4. Load to staging tables
5. Merge to production tables
6. Log changes
7. Send notifications

Environment Variables Required:
    SUNBIZ_SFTP_HOST      - SFTP hostname (default: sftp.floridados.gov)
    SUNBIZ_SFTP_USER      - SFTP username (default: Public)
    SUNBIZ_SFTP_PASSWORD  - SFTP password
    SUPABASE_URL          - Database URL
    SUPABASE_SERVICE_ROLE_KEY - Database key
"""

import os
import sys
import logging
import argparse
import tempfile
from datetime import datetime, date
from pathlib import Path
import subprocess

# Add parent directory to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv

# Load environment
load_dotenv(ROOT / '.env.mcp')

# Configure logging
LOG_DIR = ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'sunbiz_update_{date.today()}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# SFTP Configuration
SFTP_HOST = os.getenv('SUNBIZ_SFTP_HOST', 'sftp.floridados.gov')
SFTP_USER = os.getenv('SUNBIZ_SFTP_USER', 'Public')
SFTP_PASSWORD = os.getenv('SUNBIZ_SFTP_PASSWORD', 'PubAccess1845!')
SFTP_CORPORATE_DIR = '/doc/cor'
SFTP_FICTITIOUS_DIR = '/doc/fic'

# Database configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')


class SunbizUpdater:
    """Orchestrates daily Sunbiz data updates"""

    def __init__(self, dry_run: bool = False, target_date: date = None):
        """
        Initialize updater

        Args:
            dry_run: If True, don't make database changes
            target_date: Date to process (default: today)
        """
        self.dry_run = dry_run
        self.target_date = target_date or date.today()
        self.temp_dir = None
        self.stats = {
            'files_downloaded': 0,
            'records_parsed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'errors': []
        }

    def check_environment(self) -> bool:
        """Verify required environment variables"""
        required = ['SUNBIZ_SFTP_PASSWORD', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing = [var for var in required if not os.getenv(var)]

        if missing:
            logger.error(f"Missing environment variables: {', '.join(missing)}")
            return False

        logger.info("Environment validated")
        return True

    def download_file_sftp(self, remote_path: str, local_path: Path) -> bool:
        """
        Download file from SFTP using Python subprocess

        Args:
            remote_path: Path on SFTP server
            local_path: Local destination path

        Returns:
            True if successful
        """
        try:
            # Create SFTP batch commands file
            batch_file = self.temp_dir / 'sftp_batch.txt'
            with open(batch_file, 'w') as f:
                f.write(f"get {remote_path} {local_path}\n")
                f.write("bye\n")

            # Use sftp command with batch file
            # Note: This requires sshpass or similar on Linux, or manual password entry
            cmd = f'sshpass -p "{SFTP_PASSWORD}" sftp -oBatchMode=no -b {batch_file} {SFTP_USER}@{SFTP_HOST}'

            logger.info(f"Downloading: {remote_path}")

            # For Windows, we'll use a simpler approach - just document the manual process
            logger.warning("SFTP download requires manual intervention or paramiko library")
            logger.info(f"Manual download required:")
            logger.info(f"  sftp {SFTP_USER}@{SFTP_HOST}")
            logger.info(f"  get {remote_path} {local_path}")

            # For now, check if file already exists locally (manual download)
            if local_path.exists():
                logger.info(f"File found locally: {local_path}")
                return True
            else:
                logger.warning(f"File not found: {local_path}")
                logger.warning("Please download manually or install paramiko")
                return False

        except Exception as e:
            logger.error(f"SFTP download error: {e}")
            return False

    def get_daily_filenames(self) -> dict:
        """
        Get expected filenames for target date

        Returns:
            Dict with file types and names
        """
        date_str = self.target_date.strftime('%Y%m%d')

        return {
            'corporate': {
                'remote': f'{SFTP_CORPORATE_DIR}/{date_str}c.txt',
                'local': self.temp_dir / f'{date_str}c.txt',
                'type': 'corporate'
            },
            'events': {
                'remote': f'{SFTP_CORPORATE_DIR}/{date_str}ce.txt',
                'local': self.temp_dir / f'{date_str}ce.txt',
                'type': 'events'
            },
            'fictitious': {
                'remote': f'{SFTP_FICTITIOUS_DIR}/{date_str}fn.txt',
                'local': self.temp_dir / f'{date_str}fn.txt',
                'type': 'fictitious'
            }
        }

    def parse_file(self, file_info: dict) -> Path:
        """
        Parse fixed-width file to JSONL

        Args:
            file_info: File information dict

        Returns:
            Path to parsed JSONL file
        """
        parser_script = ROOT / 'scripts' / 'parse_sunbiz_files.py'
        output_file = file_info['local'].with_suffix('.jsonl')

        logger.info(f"Parsing {file_info['type']} file...")

        cmd = [
            sys.executable,
            str(parser_script),
            file_info['type'],
            str(file_info['local']),
            str(output_file)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Parse successful: {output_file}")
            return output_file

        except subprocess.CalledProcessError as e:
            logger.error(f"Parse failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise

    def load_to_database(self, jsonl_file: Path, file_type: str) -> dict:
        """
        Load parsed data to database staging tables

        Args:
            jsonl_file: Path to JSONL file
            file_type: Type of data (corporate, events, fictitious)

        Returns:
            Load statistics
        """
        if self.dry_run:
            logger.info(f"DRY RUN: Would load {jsonl_file} to database")
            return {'inserted': 0, 'updated': 0}

        logger.info(f"Loading {file_type} data to database...")

        # TODO: Implement actual database loading using Supabase staging tables
        # This would:
        # 1. Read JSONL file
        # 2. Batch insert to staging table (sunbiz_corporate_staging, etc)
        # 3. Call merge function to update production tables
        # 4. Return statistics

        logger.warning("Database loading not yet implemented")
        return {'inserted': 0, 'updated': 0}

    def run(self):
        """Execute full update workflow"""
        try:
            logger.info("=" * 80)
            logger.info("SUNBIZ DAILY UPDATE - STARTED")
            logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Target Date: {self.target_date}")
            logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
            logger.info("=" * 80)

            # Step 1: Environment check
            logger.info("\n[STEP 1/5] Checking environment...")
            if not self.check_environment():
                raise RuntimeError("Environment check failed")

            # Step 2: Setup temp directory
            logger.info("\n[STEP 2/5] Setting up temporary directory...")
            self.temp_dir = Path(tempfile.mkdtemp(prefix='sunbiz_'))
            logger.info(f"Temp directory: {self.temp_dir}")

            # Step 3: Download files
            logger.info("\n[STEP 3/5] Downloading files from SFTP...")
            files = self.get_daily_filenames()

            for name, file_info in files.items():
                success = self.download_file_sftp(file_info['remote'], file_info['local'])
                if success:
                    self.stats['files_downloaded'] += 1
                else:
                    logger.warning(f"Skipping {name} - file not available")

            if self.stats['files_downloaded'] == 0:
                logger.warning("No files downloaded - nothing to process")
                return

            # Step 4: Parse files
            logger.info("\n[STEP 4/5] Parsing fixed-width files...")
            parsed_files = []

            for name, file_info in files.items():
                if file_info['local'].exists():
                    try:
                        jsonl_file = self.parse_file(file_info)
                        parsed_files.append((jsonl_file, file_info['type']))
                    except Exception as e:
                        logger.error(f"Failed to parse {name}: {e}")
                        self.stats['errors'].append(f"Parse error: {name}")

            # Step 5: Load to database
            logger.info("\n[STEP 5/5] Loading to database...")
            for jsonl_file, file_type in parsed_files:
                try:
                    result = self.load_to_database(jsonl_file, file_type)
                    self.stats['records_inserted'] += result['inserted']
                    self.stats['records_updated'] += result['updated']
                except Exception as e:
                    logger.error(f"Failed to load {file_type}: {e}")
                    self.stats['errors'].append(f"Load error: {file_type}")

            # Print summary
            self.print_summary()

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            raise

        finally:
            # Cleanup temp directory
            if self.temp_dir and self.temp_dir.exists():
                logger.info(f"Cleaning up: {self.temp_dir}")
                # Keep temp files for inspection in dry-run
                if not self.dry_run:
                    import shutil
                    shutil.rmtree(self.temp_dir, ignore_errors=True)

    def print_summary(self):
        """Print update summary"""
        logger.info("\n" + "=" * 80)
        logger.info("SUNBIZ UPDATE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Files Downloaded: {self.stats['files_downloaded']}")
        logger.info(f"Records Parsed: {self.stats['records_parsed']}")
        logger.info(f"Records Inserted: {self.stats['records_inserted']}")
        logger.info(f"Records Updated: {self.stats['records_updated']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.info("\nErrors:")
            for error in self.stats['errors'][:10]:
                logger.info(f"  - {error}")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Daily Sunbiz Update Orchestrator')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without database changes')
    parser.add_argument('--date', type=str,
                        help='Target date (YYYY-MM-DD, default: today)')

    args = parser.parse_args()

    # Parse date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Run updater
    updater = SunbizUpdater(dry_run=args.dry_run, target_date=target_date)
    updater.run()


if __name__ == '__main__':
    main()
