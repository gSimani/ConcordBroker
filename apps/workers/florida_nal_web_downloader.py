"""
Florida Revenue NAL Data Web Downloader
Downloads NAL files using Playwright to navigate the website
"""

import os
import time
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaNALWebDownloader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P"
        self.download_log = []
        
    def get_county_folder(self, county_name: str) -> Path:
        """Get the NAL folder path for a county"""
        county_folder = self.base_path / county_name.upper() / "NAL"
        county_folder.mkdir(parents=True, exist_ok=True)
        return county_folder
    
    def extract_county_name(self, filename: str) -> str:
        """Extract county name from filename"""
        # Files are named like NAL25P_01.xlsx or NAL25P_ALACHUA.xlsx
        county_codes = {
            "01": "ALACHUA", "02": "BAKER", "03": "BAY", "04": "BRADFORD",
            "05": "BREVARD", "06": "BROWARD", "07": "CALHOUN", "08": "CHARLOTTE",
            "09": "CITRUS", "10": "CLAY", "11": "COLLIER", "12": "COLUMBIA",
            "13": "DESOTO", "14": "DIXIE", "15": "DUVAL", "16": "ESCAMBIA",
            "17": "FLAGLER", "18": "FRANKLIN", "19": "GADSDEN", "20": "GILCHRIST",
            "21": "GLADES", "22": "GULF", "23": "HAMILTON", "24": "HARDEE",
            "25": "HENDRY", "26": "HERNANDO", "27": "HIGHLANDS", "28": "HILLSBOROUGH",
            "29": "HOLMES", "30": "INDIAN RIVER", "31": "JACKSON", "32": "JEFFERSON",
            "33": "LAFAYETTE", "34": "LAKE", "35": "LEE", "36": "LEON",
            "37": "LEVY", "38": "LIBERTY", "39": "MADISON", "40": "MANATEE",
            "41": "MARION", "42": "MARTIN", "43": "MIAMI-DADE", "44": "MONROE",
            "45": "NASSAU", "46": "OKALOOSA", "47": "OKEECHOBEE", "48": "ORANGE",
            "49": "OSCEOLA", "50": "PALM BEACH", "51": "PASCO", "52": "PINELLAS",
            "53": "POLK", "54": "PUTNAM", "55": "SANTA ROSA", "56": "SARASOTA",
            "57": "SEMINOLE", "58": "ST. JOHNS", "59": "ST. LUCIE", "60": "SUMTER",
            "61": "SUWANNEE", "62": "TAYLOR", "63": "UNION", "64": "VOLUSIA",
            "65": "WAKULLA", "66": "WALTON", "67": "WASHINGTON"
        }
        
        # Try to extract county code from filename
        if "NAL25P_" in filename:
            code = filename.split("NAL25P_")[1].split(".")[0]
            if code in county_codes:
                return county_codes[code]
        
        # Try to match county name directly
        for county in county_codes.values():
            if county.replace(" ", "").replace(".", "").upper() in filename.upper():
                return county
                
        return None
    
    def download_all_files(self):
        """Download all NAL files using Playwright"""
        with sync_playwright() as p:
            # Launch browser with download handling
            browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                logger.info(f"Navigating to {self.base_url}")
                page.goto(self.base_url, wait_until='networkidle', timeout=60000)
                
                # Wait for the page to load
                page.wait_for_timeout(3000)
                
                # Find all Excel/ZIP file links
                file_links = page.locator("a[href*='.xlsx'], a[href*='.zip']").all()
                logger.info(f"Found {len(file_links)} potential file links")
                
                if len(file_links) == 0:
                    # Try alternative selectors
                    file_links = page.locator("a:has-text('NAL25P')").all()
                    logger.info(f"Found {len(file_links)} NAL files using text search")
                
                downloaded_count = 0
                
                for i, link in enumerate(file_links):
                    try:
                        # Get link text and href
                        link_text = link.inner_text()
                        link_href = link.get_attribute('href')
                        
                        if not link_text or 'NAL25P' not in link_text:
                            continue
                        
                        logger.info(f"Processing {i+1}/{len(file_links)}: {link_text}")
                        
                        # Extract county name
                        county_name = self.extract_county_name(link_text)
                        if not county_name:
                            logger.warning(f"Could not determine county for {link_text}")
                            continue
                        
                        # Get destination folder
                        dest_folder = self.get_county_folder(county_name)
                        dest_file = dest_folder / link_text
                        
                        # Check if file already exists
                        if dest_file.exists() or (dest_folder / link_text.replace('.zip', '.xlsx')).exists():
                            logger.info(f"File already exists for {county_name}, skipping")
                            self.download_log.append({
                                "county": county_name,
                                "status": "exists",
                                "file": link_text,
                                "timestamp": datetime.now().isoformat()
                            })
                            continue
                        
                        # Start download
                        with page.expect_download(timeout=30000) as download_info:
                            link.click()
                        
                        download = download_info.value
                        
                        # Save to county folder
                        download.save_as(dest_file)
                        logger.info(f"Downloaded {link_text} to {dest_file}")
                        
                        # Extract if it's a zip file
                        if link_text.endswith('.zip'):
                            self.extract_zip(dest_file)
                        
                        downloaded_count += 1
                        self.download_log.append({
                            "county": county_name,
                            "status": "success",
                            "file": link_text,
                            "path": str(dest_file),
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Small delay between downloads
                        page.wait_for_timeout(2000)
                        
                    except PlaywrightTimeout:
                        logger.error(f"Download timeout for {link_text}")
                        self.download_log.append({
                            "county": county_name if county_name else "Unknown",
                            "status": "timeout",
                            "file": link_text,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.error(f"Error downloading {link_text}: {e}")
                        self.download_log.append({
                            "county": county_name if county_name else "Unknown",
                            "status": "error",
                            "file": link_text if 'link_text' in locals() else "Unknown",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                
                logger.info(f"Downloaded {downloaded_count} files")
                
            except Exception as e:
                logger.error(f"Browser automation error: {e}")
            finally:
                browser.close()
                self.save_log()
                self.print_summary()
    
    def extract_zip(self, zip_path: Path):
        """Extract a zip file"""
        try:
            logger.info(f"Extracting {zip_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_path.parent)
            logger.info(f"Extracted successfully")
            # Remove zip after extraction
            zip_path.unlink()
        except Exception as e:
            logger.error(f"Failed to extract {zip_path}: {e}")
    
    def save_log(self):
        """Save download log"""
        log_file = self.base_path / f"nal_web_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        logger.info(f"Log saved to {log_file}")
    
    def print_summary(self):
        """Print download summary"""
        success = sum(1 for r in self.download_log if r["status"] == "success")
        exists = sum(1 for r in self.download_log if r["status"] == "exists")
        failed = sum(1 for r in self.download_log if r["status"] in ["error", "timeout"])
        
        print("\n" + "="*60)
        print("NAL DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Successfully downloaded: {success}")
        print(f"Already existed: {exists}")
        print(f"Failed: {failed}")
        print("="*60)
        
        if failed > 0:
            print("\nFailed downloads:")
            for r in self.download_log:
                if r["status"] in ["error", "timeout"]:
                    print(f"  - {r.get('county', 'Unknown')}: {r.get('error', r['status'])}")


def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue NAL Web Downloader")
    print("="*60)
    print(f"Base path: {base_path}")
    print(f"Target: NAL 2025P files from Florida Revenue website")
    print("="*60)
    print("Note: Browser window will open to download files")
    print("="*60)
    
    downloader = FloridaNALWebDownloader(base_path)
    downloader.download_all_files()


if __name__ == "__main__":
    main()