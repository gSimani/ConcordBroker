#!/usr/bin/env python3
"""
Florida Revenue NAL Data Downloader - 2025 Edition
Downloads NAL (Name and Address Listing) files for all 67 Florida counties
from the Florida Revenue Data Portal using Playwright

Data Source: https://floridarevenue.com/property/dataportal
"""

import os
import sys
import time
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nal_download.log')
    ]
)
logger = logging.getLogger(__name__)

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

# Reverse mapping: county name to code
COUNTY_NAME_TO_CODE = {v: k for k, v in COUNTY_CODES.items()}


class FloridaNALDownloader:
    """Download NAL files from Florida Revenue Data Portal"""

    def __init__(self, output_dir: str, year: str = "2025", file_type: str = "P"):
        """
        Initialize downloader

        Args:
            output_dir: Base directory for downloaded files
            year: Data year (2025, 2024, etc)
            file_type: P=Preliminary, F=Final, S=Supplemental
        """
        self.output_dir = Path(output_dir)
        self.year = year
        self.file_type = file_type
        self.download_log = []
        self.base_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx"

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_county_folder(self, county_name: str) -> Path:
        """Get or create county NAL folder"""
        # Normalize county name for folder
        folder_name = county_name.upper().replace(" ", "_").replace(".", "")
        county_folder = self.output_dir / folder_name / "NAL"
        county_folder.mkdir(parents=True, exist_ok=True)
        return county_folder

    def extract_county_from_filename(self, filename: str) -> Optional[str]:
        """Extract county name from NAL filename"""
        # NAL files are named like: NAL11P202501.csv or NAL_ALACHUA_2025P.csv
        filename_upper = filename.upper()

        # Try to find county code (2 digits after NAL)
        import re
        match = re.search(r'NAL(\d{2})', filename_upper)
        if match:
            code = int(match.group(1))
            if code in COUNTY_CODES:
                return COUNTY_CODES[code]

        # Try to match county name in filename
        for name in COUNTY_CODES.values():
            name_clean = name.replace(" ", "").replace(".", "").replace("-", "")
            if name_clean in filename_upper.replace(" ", "").replace(".", "").replace("-", ""):
                return name

        return None

    def download_with_playwright(self, headless: bool = False):
        """Download all NAL files using Playwright browser automation"""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return

        logger.info("="*70)
        logger.info("FLORIDA NAL DATA DOWNLOADER")
        logger.info("="*70)
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Target: NAL {self.year}{self.file_type} files")
        logger.info(f"Headless mode: {headless}")
        logger.info("="*70)

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=headless,
                slow_mo=100  # Slow down for visibility
            )

            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )

            page = context.new_page()

            try:
                # Navigate to data portal
                logger.info(f"Navigating to Florida Revenue Data Portal...")
                page.goto(self.base_url, wait_until='networkidle', timeout=60000)
                page.wait_for_timeout(3000)

                # Take screenshot for debugging
                page.screenshot(path=str(self.output_dir / "portal_screenshot.png"))
                logger.info("Saved portal screenshot")

                # Try to navigate to NAL section
                # The portal uses SharePoint, so we need to navigate through the folder structure
                nal_paths = [
                    f"Tax Roll Data Files/NAL/{self.year}{self.file_type}",
                    f"NAL/{self.year}{self.file_type}",
                    f"PTO Data Portal/Tax Roll Data Files/NAL/{self.year}{self.file_type}"
                ]

                found_nal = False
                for nal_path in nal_paths:
                    try:
                        # Look for folder links
                        folder_link = page.locator(f"a:has-text('{nal_path.split('/')[-1]}')")
                        if folder_link.count() > 0:
                            logger.info(f"Found NAL folder link: {nal_path}")
                            folder_link.first.click()
                            page.wait_for_timeout(3000)
                            found_nal = True
                            break
                    except:
                        continue

                if not found_nal:
                    # Try direct URL navigation
                    direct_url = f"{self.base_url}?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{self.year}{self.file_type}"
                    logger.info(f"Trying direct URL: {direct_url}")
                    page.goto(direct_url, wait_until='networkidle', timeout=60000)
                    page.wait_for_timeout(5000)

                # Take screenshot after navigation
                page.screenshot(path=str(self.output_dir / "nal_folder_screenshot.png"))

                # Find all downloadable files (ZIP, CSV, XLSX)
                file_selectors = [
                    "a[href*='.zip']",
                    "a[href*='.csv']",
                    "a[href*='.xlsx']",
                    "a:has-text('NAL')"
                ]

                all_links = []
                for selector in file_selectors:
                    links = page.locator(selector).all()
                    all_links.extend(links)

                # Deduplicate
                seen_hrefs = set()
                unique_links = []
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique_links.append(link)

                logger.info(f"Found {len(unique_links)} potential file links")

                # Download each file
                downloaded = 0
                skipped = 0
                failed = 0

                for i, link in enumerate(unique_links):
                    try:
                        link_text = link.inner_text().strip()
                        link_href = link.get_attribute('href')

                        # Skip if not a NAL file
                        if 'NAL' not in link_text.upper() and 'NAL' not in (link_href or '').upper():
                            continue

                        logger.info(f"[{i+1}/{len(unique_links)}] Processing: {link_text}")

                        # Determine county
                        county = self.extract_county_from_filename(link_text)
                        if not county:
                            logger.warning(f"  Could not determine county, skipping")
                            continue

                        # Get destination
                        dest_folder = self.get_county_folder(county)
                        dest_file = dest_folder / link_text

                        # Check if already exists
                        if dest_file.exists():
                            logger.info(f"  Already exists, skipping")
                            skipped += 1
                            self.download_log.append({
                                "county": county,
                                "file": link_text,
                                "status": "skipped",
                                "reason": "exists",
                                "timestamp": datetime.now().isoformat()
                            })
                            continue

                        # Download
                        try:
                            with page.expect_download(timeout=120000) as download_info:
                                link.click()

                            download = download_info.value
                            download.save_as(str(dest_file))

                            logger.info(f"  Downloaded to {dest_file}")
                            downloaded += 1

                            # Extract if ZIP
                            if dest_file.suffix.lower() == '.zip':
                                self.extract_zip(dest_file)

                            self.download_log.append({
                                "county": county,
                                "file": link_text,
                                "path": str(dest_file),
                                "status": "success",
                                "timestamp": datetime.now().isoformat()
                            })

                        except PlaywrightTimeout:
                            logger.error(f"  Download timeout")
                            failed += 1
                            self.download_log.append({
                                "county": county,
                                "file": link_text,
                                "status": "timeout",
                                "timestamp": datetime.now().isoformat()
                            })

                        # Brief pause between downloads
                        page.wait_for_timeout(1000)

                    except Exception as e:
                        logger.error(f"  Error: {e}")
                        failed += 1
                        self.download_log.append({
                            "county": county if 'county' in locals() else "Unknown",
                            "file": link_text if 'link_text' in locals() else "Unknown",
                            "status": "error",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })

                logger.info("="*70)
                logger.info(f"DOWNLOAD COMPLETE")
                logger.info(f"  Downloaded: {downloaded}")
                logger.info(f"  Skipped (exists): {skipped}")
                logger.info(f"  Failed: {failed}")
                logger.info("="*70)

            except Exception as e:
                logger.error(f"Browser automation error: {e}")
                page.screenshot(path=str(self.output_dir / "error_screenshot.png"))

            finally:
                browser.close()
                self.save_log()

    def extract_zip(self, zip_path: Path):
        """Extract ZIP file and remove archive"""
        try:
            logger.info(f"  Extracting {zip_path.name}...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(zip_path.parent)
            zip_path.unlink()  # Remove ZIP after extraction
            logger.info(f"  Extracted successfully")
        except Exception as e:
            logger.error(f"  Extraction failed: {e}")

    def save_log(self):
        """Save download log to JSON"""
        log_file = self.output_dir / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                "generated": datetime.now().isoformat(),
                "year": self.year,
                "file_type": self.file_type,
                "output_dir": str(self.output_dir),
                "downloads": self.download_log
            }, f, indent=2)
        logger.info(f"Log saved to {log_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Download Florida NAL property data")
    parser.add_argument(
        "--output", "-o",
        default=r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP",
        help="Output directory"
    )
    parser.add_argument(
        "--year", "-y",
        default="2025",
        help="Data year (default: 2025)"
    )
    parser.add_argument(
        "--type", "-t",
        default="P",
        choices=["P", "F", "S"],
        help="File type: P=Preliminary, F=Final, S=Supplemental (default: P)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    args = parser.parse_args()

    print("="*70)
    print("FLORIDA REVENUE NAL DATA DOWNLOADER")
    print("="*70)
    print(f"Output: {args.output}")
    print(f"Year: {args.year}")
    print(f"Type: {args.type}")
    print(f"Headless: {args.headless}")
    print("="*70)
    print()
    print("This will open a browser window to navigate the Florida Revenue")
    print("Data Portal and download NAL files for all 67 counties.")
    print()
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")

    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

    downloader = FloridaNALDownloader(
        output_dir=args.output,
        year=args.year,
        file_type=args.type
    )

    downloader.download_with_playwright(headless=args.headless)


if __name__ == "__main__":
    main()
