#!/usr/bin/env python3
"""
Florida NAL Data Monitor and Auto-Updater
==========================================
Monitors the Florida Revenue Data Portal for new NAL files and automatically
downloads and uploads them to Supabase.

This agent:
1. Checks the Florida Revenue portal for available NAL files
2. Compares file metadata (size, date) against stored checksums
3. Downloads only new or updated files
4. Triggers the upload process to Supabase
5. Logs all activity for audit trail

Schedule: Daily at 2:00 AM EST (via GitHub Actions or cron)

Usage:
    python scripts/monitor_florida_nal_updates.py              # Check and update
    python scripts/monitor_florida_nal_updates.py --dry-run    # Check only, no downloads
    python scripts/monitor_florida_nal_updates.py --force      # Force re-download all
    python scripts/monitor_florida_nal_updates.py --county ORANGE  # Specific county
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import subprocess

# Add parent to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env.mcp')

# Configure logging
LOG_DIR = ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / f'nal_monitor_{date.today()}.log')
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

# Data paths
DATA_PATH = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
CHECKSUM_FILE = ROOT / 'data' / 'nal_file_checksums.json'

# Florida county codes (DOR standard)
COUNTY_CODES = {
    11: "ALACHUA", 12: "BAKER", 13: "BAY", 14: "BRADFORD", 15: "BREVARD",
    16: "BROWARD", 17: "CALHOUN", 18: "CHARLOTTE", 19: "CITRUS", 20: "CLAY",
    21: "COLLIER", 22: "COLUMBIA", 23: "MIAMI-DADE", 24: "DESOTO", 25: "DIXIE",
    26: "DUVAL", 27: "ESCAMBIA", 28: "FLAGLER", 29: "FRANKLIN", 30: "GADSDEN",
    31: "GILCHRIST", 32: "GLADES", 33: "GULF", 34: "HAMILTON", 35: "HARDEE",
    36: "HENDRY", 37: "HERNANDO", 38: "HIGHLANDS", 39: "HILLSBOROUGH", 40: "HOLMES",
    41: "INDIAN RIVER", 42: "JACKSON", 43: "JEFFERSON", 44: "LAFAYETTE", 45: "LAKE",
    46: "LEE", 47: "LEON", 48: "LEVY", 49: "LIBERTY", 50: "MADISON",
    51: "MANATEE", 52: "MARION", 53: "MARTIN", 54: "MONROE", 55: "NASSAU",
    56: "OKALOOSA", 57: "OKEECHOBEE", 58: "ORANGE", 59: "OSCEOLA", 60: "PALM BEACH",
    61: "PASCO", 62: "PINELLAS", 63: "POLK", 64: "PUTNAM", 65: "ST. JOHNS",
    66: "ST. LUCIE", 67: "SANTA ROSA", 68: "SARASOTA", 69: "SEMINOLE", 70: "SUMTER",
    71: "SUWANNEE", 72: "TAYLOR", 73: "UNION", 74: "VOLUSIA", 75: "WAKULLA",
    76: "WALTON", 77: "WASHINGTON"
}


class NALFileMonitor:
    """Monitors Florida Revenue portal for NAL file updates"""

    def __init__(self, data_path: Path, year: str = "2025", file_type: str = "P"):
        self.data_path = data_path
        self.year = year
        self.file_type = file_type  # P=Preliminary, F=Final
        self.portal_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx"
        self.checksums = self.load_checksums()
        self.stats = {
            'files_checked': 0,
            'files_new': 0,
            'files_updated': 0,
            'files_unchanged': 0,
            'downloads_successful': 0,
            'downloads_failed': 0,
            'uploads_successful': 0,
            'uploads_failed': 0
        }

    def load_checksums(self) -> Dict:
        """Load stored file checksums"""
        if CHECKSUM_FILE.exists():
            try:
                with open(CHECKSUM_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load checksums: {e}")
        return {}

    def save_checksums(self):
        """Save file checksums"""
        CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKSUM_FILE, 'w') as f:
            json.dump(self.checksums, f, indent=2, default=str)
        logger.info(f"Saved checksums to {CHECKSUM_FILE}")

    def get_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_local_nal_status(self) -> Dict[str, Dict]:
        """Get status of all local NAL files"""
        local_files = {}

        for county_code, county_name in COUNTY_CODES.items():
            folder_name = county_name.upper().replace(" ", "_").replace(".", "").replace("-", "_")
            nal_folder = self.data_path / folder_name / "NAL"

            if nal_folder.exists():
                for csv_file in nal_folder.glob("*.csv"):
                    file_key = f"{county_name}_{csv_file.name}"
                    file_stat = csv_file.stat()

                    local_files[file_key] = {
                        'county': county_name,
                        'county_code': county_code,
                        'file_name': csv_file.name,
                        'file_path': str(csv_file),
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'checksum': self.get_file_checksum(csv_file)
                    }

        return local_files

    def check_portal_for_updates(self) -> List[Dict]:
        """
        Check Florida Revenue portal for available NAL files.
        Uses Playwright to scrape the portal since it's a SharePoint site.

        Returns list of files that need to be downloaded.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return []

        files_to_download = []

        logger.info("Checking Florida Revenue Data Portal for updates...")
        logger.info(f"Target: NAL {self.year}{self.file_type} files")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                # Navigate to portal
                direct_url = f"{self.portal_url}?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{self.year}{self.file_type}"
                logger.info(f"Navigating to: {direct_url}")

                page.goto(direct_url, wait_until='networkidle', timeout=60000)
                page.wait_for_timeout(5000)

                # Find all file links
                file_links = page.locator("a[href*='.csv'], a[href*='.xlsx'], a[href*='.zip'], a:has-text('NAL')").all()

                logger.info(f"Found {len(file_links)} potential NAL files on portal")

                for link in file_links:
                    try:
                        link_text = link.inner_text().strip()
                        link_href = link.get_attribute('href')

                        # Filter for NAL files
                        if 'NAL' not in link_text.upper() and 'NAL' not in (link_href or '').upper():
                            continue

                        # Extract county info from filename
                        # Formats: "NAL49P202502.csv", "Liberty 49 Preliminary NAL 2025.zip", etc.
                        import re
                        county_name = None
                        county_code = None

                        # Try pattern 1: NAL##P format (e.g., NAL49P202502.csv)
                        match = re.search(r'NAL(\d{2})[PFS]', link_text.upper())
                        if match:
                            county_code = int(match.group(1))
                            if county_code in COUNTY_CODES:
                                county_name = COUNTY_CODES[county_code]

                        # Try pattern 2: "CountyName ## ... NAL" format (e.g., "Liberty 49 Preliminary NAL 2025.zip")
                        if not county_name:
                            for code, name in COUNTY_CODES.items():
                                # Check if county name is in filename
                                name_clean = name.replace(" ", "").replace(".", "").replace("-", "").upper()
                                link_clean = link_text.replace(" ", "").replace(".", "").replace("-", "").upper()
                                if name_clean in link_clean or name.upper() in link_text.upper():
                                    county_name = name
                                    county_code = code
                                    break

                        if county_name and county_code:
                            file_key = f"{county_name}_{link_text}"

                            # Check if file is new or updated
                            stored_info = self.checksums.get(file_key, {})

                            files_to_download.append({
                                'county': county_name,
                                'county_code': county_code,
                                'file_name': link_text,
                                'href': link_href,
                                'is_new': file_key not in self.checksums,
                                'stored_checksum': stored_info.get('checksum')
                            })

                            self.stats['files_checked'] += 1
                            logger.info(f"    Found: {link_text} -> {county_name}")

                    except Exception as e:
                        logger.warning(f"Error processing link: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error checking portal: {e}")
                page.screenshot(path=str(LOG_DIR / "portal_error.png"))
            finally:
                browser.close()

        return files_to_download

    def download_file(self, file_info: Dict, dry_run: bool = False) -> bool:
        """Download a single NAL file from the portal"""
        if dry_run:
            logger.info(f"  [DRY RUN] Would download: {file_info['file_name']}")
            return True

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return False

        county_name = file_info['county']
        folder_name = county_name.upper().replace(" ", "_").replace(".", "").replace("-", "_")
        dest_folder = self.data_path / folder_name / "NAL"
        dest_folder.mkdir(parents=True, exist_ok=True)
        dest_file = dest_folder / file_info['file_name']

        logger.info(f"  Downloading {file_info['file_name']} for {county_name}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                # Navigate to portal
                direct_url = f"{self.portal_url}?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{self.year}{self.file_type}"
                page.goto(direct_url, wait_until='networkidle', timeout=60000)
                page.wait_for_timeout(3000)

                # Find and click the specific file link
                file_link = page.locator(f"a:has-text('{file_info['file_name']}')").first

                with page.expect_download(timeout=120000) as download_info:
                    file_link.click()

                download = download_info.value
                download.save_as(str(dest_file))

                logger.info(f"  Downloaded to {dest_file}")

                # Update checksum
                file_key = f"{county_name}_{file_info['file_name']}"
                self.checksums[file_key] = {
                    'county': county_name,
                    'file_name': file_info['file_name'],
                    'checksum': self.get_file_checksum(dest_file),
                    'size': dest_file.stat().st_size,
                    'downloaded': datetime.now().isoformat()
                }

                self.stats['downloads_successful'] += 1
                return True

            except Exception as e:
                logger.error(f"  Download failed: {e}")
                self.stats['downloads_failed'] += 1
                return False
            finally:
                browser.close()

    def upload_to_supabase(self, county: str, dry_run: bool = False) -> bool:
        """Upload NAL data for a county to Supabase"""
        if dry_run:
            logger.info(f"  [DRY RUN] Would upload {county} to Supabase")
            return True

        upload_script = ROOT / 'scripts' / 'upload_nal_to_supabase.py'

        if not upload_script.exists():
            logger.error(f"Upload script not found: {upload_script}")
            return False

        logger.info(f"  Uploading {county} to Supabase...")

        try:
            result = subprocess.run(
                [sys.executable, str(upload_script), '--county', county],
                capture_output=True,
                text=True,
                timeout=1800  # 30 min timeout per county
            )

            if result.returncode == 0:
                logger.info(f"  Upload successful for {county}")
                self.stats['uploads_successful'] += 1
                return True
            else:
                logger.error(f"  Upload failed for {county}: {result.stderr}")
                self.stats['uploads_failed'] += 1
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"  Upload timeout for {county}")
            self.stats['uploads_failed'] += 1
            return False
        except Exception as e:
            logger.error(f"  Upload error for {county}: {e}")
            self.stats['uploads_failed'] += 1
            return False

    def run_check(self, dry_run: bool = False, force: bool = False,
                  specific_county: str = None) -> Dict:
        """
        Main monitoring routine.

        Args:
            dry_run: Check only, don't download or upload
            force: Force re-download all files
            specific_county: Only check specific county

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 70)
        logger.info("FLORIDA NAL DATA MONITOR")
        logger.info("=" * 70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
        logger.info(f"Force: {'YES' if force else 'NO'}")
        if specific_county:
            logger.info(f"County Filter: {specific_county}")
        logger.info("=" * 70)

        start_time = datetime.now()

        # Step 1: Get local file status
        logger.info("\n[STEP 1/4] Scanning local NAL files...")
        local_files = self.get_local_nal_status()
        logger.info(f"  Found {len(local_files)} local NAL files")

        # Step 2: Check portal for updates
        logger.info("\n[STEP 2/4] Checking Florida Revenue portal...")
        portal_files = self.check_portal_for_updates()
        logger.info(f"  Found {len(portal_files)} NAL files on portal")

        # Step 3: Determine what needs downloading
        logger.info("\n[STEP 3/4] Comparing files...")
        files_to_download = []

        for pf in portal_files:
            # Filter by county if specified
            if specific_county and pf['county'].upper() != specific_county.upper():
                continue

            file_key = f"{pf['county']}_{pf['file_name']}"
            local_info = local_files.get(file_key)

            if force:
                files_to_download.append(pf)
                self.stats['files_updated'] += 1
                logger.info(f"  [FORCE] Will re-download: {pf['file_name']}")
            elif pf['is_new']:
                files_to_download.append(pf)
                self.stats['files_new'] += 1
                logger.info(f"  [NEW] Will download: {pf['file_name']}")
            elif local_info and pf.get('stored_checksum') != local_info.get('checksum'):
                files_to_download.append(pf)
                self.stats['files_updated'] += 1
                logger.info(f"  [UPDATED] Will re-download: {pf['file_name']}")
            else:
                self.stats['files_unchanged'] += 1

        logger.info(f"\n  Summary: {self.stats['files_new']} new, {self.stats['files_updated']} updated, {self.stats['files_unchanged']} unchanged")

        # Step 4: Download and upload
        if files_to_download:
            logger.info(f"\n[STEP 4/4] Processing {len(files_to_download)} files...")

            counties_to_upload = set()

            for file_info in files_to_download:
                if self.download_file(file_info, dry_run):
                    counties_to_upload.add(file_info['county'])

            # Upload each county that had downloads
            logger.info(f"\n  Uploading {len(counties_to_upload)} counties to Supabase...")
            for county in sorted(counties_to_upload):
                self.upload_to_supabase(county, dry_run)
        else:
            logger.info("\n[STEP 4/4] No files need downloading")

        # Save checksums
        if not dry_run:
            self.save_checksums()

        # Final report
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("MONITOR RUN COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Files checked:        {self.stats['files_checked']}")
        logger.info(f"Files new:            {self.stats['files_new']}")
        logger.info(f"Files updated:        {self.stats['files_updated']}")
        logger.info(f"Files unchanged:      {self.stats['files_unchanged']}")
        logger.info(f"Downloads successful: {self.stats['downloads_successful']}")
        logger.info(f"Downloads failed:     {self.stats['downloads_failed']}")
        logger.info(f"Uploads successful:   {self.stats['uploads_successful']}")
        logger.info(f"Uploads failed:       {self.stats['uploads_failed']}")
        logger.info(f"Duration:             {elapsed / 60:.1f} minutes")
        logger.info("=" * 70)

        return self.stats


def log_to_supabase(stats: Dict, dry_run: bool = False):
    """Log monitor run to Supabase for tracking"""
    if dry_run or not SUPABASE_KEY:
        return

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        client.table('data_update_jobs').insert({
            'job_type': 'nal_monitor',
            'status': 'completed' if stats['downloads_failed'] == 0 else 'partial',
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'records_processed': stats['files_checked'],
            'records_created': stats['files_new'],
            'records_updated': stats['files_updated'],
            'errors': stats['downloads_failed'] + stats['uploads_failed'],
            'metadata': json.dumps(stats)
        }).execute()

        logger.info("Logged monitor run to Supabase")
    except Exception as e:
        logger.warning(f"Could not log to Supabase: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor Florida Revenue portal for NAL data updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check only, do not download or upload'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download all files'
    )
    parser.add_argument(
        '--county',
        type=str,
        help='Only process specific county (e.g., ORANGE, MIAMI-DADE)'
    )
    parser.add_argument(
        '--year',
        type=str,
        default='2025',
        help='Data year (default: 2025)'
    )
    parser.add_argument(
        '--type',
        type=str,
        default='P',
        choices=['P', 'F', 'S'],
        help='File type: P=Preliminary, F=Final, S=Supplemental (default: P)'
    )

    args = parser.parse_args()

    try:
        monitor = NALFileMonitor(
            data_path=DATA_PATH,
            year=args.year,
            file_type=args.type
        )

        stats = monitor.run_check(
            dry_run=args.dry_run,
            force=args.force,
            specific_county=args.county
        )

        # Log to Supabase
        log_to_supabase(stats, args.dry_run)

        # Return exit code based on success
        if stats['downloads_failed'] > 0 or stats['uploads_failed'] > 0:
            return 1
        return 0

    except Exception as e:
        logger.error(f"Monitor failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
