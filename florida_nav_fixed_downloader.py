#!/usr/bin/env python3
"""
Florida Revenue NAV Data Downloader - Fixed Version
Downloads NAV N and NAV D files from their respective subdirectories
"""

import os
import time
import json
import zipfile
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_nav_download_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaNAVDownloader:
    """
    Downloads NAV (Non Ad Valorem) assessment files from Florida Revenue
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024"
        
        # URLs for NAV subdirectories
        self.nav_urls = {
            "N": "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20N",
            "D": "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20D"
        }
        
        self.download_log = []
        
        # Florida counties with codes
        self.counties = {
            "ALACHUA": "11", "BAKER": "12", "BAY": "13", "BRADFORD": "14",
            "BREVARD": "15", "BROWARD": "16", "CALHOUN": "17", "CHARLOTTE": "18",
            "CITRUS": "19", "CLAY": "20", "COLLIER": "21", "COLUMBIA": "22",
            "DADE": "23", "DESOTO": "24", "DIXIE": "25", "DUVAL": "26",
            "ESCAMBIA": "27", "FLAGLER": "28", "FRANKLIN": "29", "GADSDEN": "30",
            "GILCHRIST": "31", "GLADES": "32", "GULF": "33", "HAMILTON": "34",
            "HARDEE": "35", "HENDRY": "36", "HERNANDO": "37", "HIGHLANDS": "38",
            "HILLSBOROUGH": "39", "HOLMES": "40", "INDIAN RIVER": "41", "JACKSON": "42",
            "JEFFERSON": "43", "LAFAYETTE": "44", "LAKE": "45", "LEE": "46",
            "LEON": "47", "LEVY": "48", "LIBERTY": "49", "MADISON": "50",
            "MANATEE": "51", "MARION": "52", "MARTIN": "53", "MONROE": "54",
            "NASSAU": "55", "OKALOOSA": "56", "OKEECHOBEE": "57", "ORANGE": "58",
            "OSCEOLA": "59", "PALM BEACH": "60", "PASCO": "61", "PINELLAS": "62",
            "POLK": "63", "PUTNAM": "64", "SANTA ROSA": "65", "SARASOTA": "66",
            "SEMINOLE": "67", "ST. JOHNS": "68", "ST. LUCIE": "69", "SUMTER": "70",
            "SUWANNEE": "71", "TAYLOR": "72", "UNION": "73", "VOLUSIA": "74",
            "WAKULLA": "75", "WALTON": "76", "WASHINGTON": "77"
        }
    
    def get_county_folder(self, county: str, nav_type: str) -> Path:
        """
        Get the folder path for NAV files
        Structure: COUNTY_NAME/NAV/NAV_N/ or COUNTY_NAME/NAV/NAV_D/
        """
        folder = self.base_path / county.upper() / "NAV" / f"NAV_{nav_type}"
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    def extract_county_from_filename(self, filename: str) -> Optional[str]:
        """Extract county name from NAV filename"""
        # NAV files are named like: NAVN110901.TXT or NAVD110901.TXT
        # Where 11 is the county code
        
        filename_upper = filename.upper()
        
        # Try to extract county code from filename pattern
        if "NAVN" in filename_upper or "NAVD" in filename_upper:
            try:
                # Get the 2 digits after NAV[N/D]
                start_idx = filename_upper.find("NAVN") if "NAVN" in filename_upper else filename_upper.find("NAVD")
                if start_idx != -1:
                    code_part = filename_upper[start_idx+4:start_idx+6]
                    if code_part.isdigit():
                        # Find county by code
                        for county, county_code in self.counties.items():
                            if county_code == code_part:
                                return county
            except:
                pass
        
        # Fallback: try to match county name in filename
        for county in self.counties.keys():
            if county.replace(" ", "").upper() in filename_upper:
                return county
        
        return None
    
    async def extract_nav_files(self, nav_type: str, url: str) -> List[Dict]:
        """Extract NAV file links from a specific NAV subdirectory"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                logger.info(f"Extracting NAV {nav_type} files from {url}")
                
                await page.goto(url, wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(3000)
                
                # Extract all file links (looking for .TXT files)
                file_links = await page.evaluate('''
                    () => {
                        const links = [];
                        const anchors = document.querySelectorAll('a');
                        anchors.forEach(anchor => {
                            const href = anchor.href;
                            const text = anchor.textContent.trim();
                            // Look for .TXT files
                            if (text && (text.includes('.TXT') || text.includes('.txt'))) {
                                links.push({
                                    filename: text,
                                    url: href
                                });
                            }
                        });
                        return links;
                    }
                ''')
                
                # Process the links
                download_links = []
                for link in file_links:
                    filename = link['filename'].strip()
                    url = link['url']
                    
                    # Ensure URL is absolute
                    if not url.startswith('http'):
                        url = f"https://floridarevenue.com{url}"
                    
                    download_links.append({
                        'filename': filename,
                        'url': url,
                        'nav_type': nav_type
                    })
                
                logger.info(f"Found {len(download_links)} NAV {nav_type} files")
                return download_links
                
            except Exception as e:
                logger.error(f"Failed to extract NAV {nav_type} files: {e}")
                return []
            finally:
                await browser.close()
    
    async def download_file_async(self, url: str, dest_path: Path) -> bool:
        """Download a file asynchronously"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        async with aiofiles.open(dest_path, 'wb') as f:
                            await f.write(content)
                        logger.info(f"Downloaded: {dest_path.name}")
                        return True
                    else:
                        logger.warning(f"Failed to download (status {response.status}): {url}")
                        return False
        except Exception as e:
            logger.error(f"Download error for {dest_path.name}: {e}")
            return False
    
    def extract_zip(self, zip_path: Path):
        """Extract a zip file and delete it"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_path.parent)
            zip_path.unlink()
            logger.info(f"Extracted and removed: {zip_path.name}")
        except Exception as e:
            logger.error(f"Failed to extract {zip_path}: {e}")
    
    async def download_nav_files(self, nav_type: str):
        """Download all NAV files of a specific type (N or D)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading NAV {nav_type} files")
        logger.info(f"{'='*60}")
        
        # Get the specific URL for this NAV type
        url = self.nav_urls.get(nav_type)
        if not url:
            logger.error(f"No URL defined for NAV type {nav_type}")
            return
        
        # Extract file links from the subdirectory
        links = await self.extract_nav_files(nav_type, url)
        
        if not links:
            logger.warning(f"No NAV {nav_type} files found")
            return
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for link in links:
            filename = link['filename']
            file_url = link['url']
            
            # Extract county from filename
            county = self.extract_county_from_filename(filename)
            if not county:
                logger.warning(f"Could not determine county for {filename}")
                fail_count += 1
                continue
            
            # Get destination folder
            dest_folder = self.get_county_folder(county, nav_type)
            dest_file = dest_folder / filename
            
            # Check if file exists
            if dest_file.exists():
                logger.info(f"File already exists: {county}/NAV/NAV_{nav_type}/{filename}")
                skip_count += 1
                continue
            
            # Download file
            logger.info(f"Downloading: {filename} for {county}")
            if await self.download_file_async(file_url, dest_file):
                # Extract if it's a zip
                if filename.lower().endswith('.zip'):
                    self.extract_zip(dest_file)
                
                success_count += 1
                self.download_log.append({
                    "county": county,
                    "nav_type": nav_type,
                    "filename": filename,
                    "status": "success",
                    "path": str(dest_file),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                fail_count += 1
                self.download_log.append({
                    "county": county,
                    "nav_type": nav_type,
                    "filename": filename,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Small delay between downloads
            await asyncio.sleep(1)
        
        logger.info(f"\nNAV {nav_type} Summary:")
        logger.info(f"  Downloaded: {success_count}")
        logger.info(f"  Skipped: {skip_count}")
        logger.info(f"  Failed: {fail_count}")
    
    async def run(self):
        """Main execution"""
        logger.info("Starting Florida NAV Data Download (Fixed Version)")
        logger.info(f"Base path: {self.base_path}")
        
        # Download NAV N files (parcel account records)
        await self.download_nav_files("N")
        
        # Download NAV D files (assessment detail records)
        await self.download_nav_files("D")
        
        # Save report
        self.save_report()
        self.print_summary()
    
    def save_report(self):
        """Save download report"""
        report_file = self.base_path / f"nav_download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        logger.info(f"Report saved to {report_file}")
    
    def print_summary(self):
        """Print final summary"""
        nav_n_success = sum(1 for r in self.download_log if r["nav_type"] == "N" and r["status"] == "success")
        nav_d_success = sum(1 for r in self.download_log if r["nav_type"] == "D" and r["status"] == "success")
        nav_n_failed = sum(1 for r in self.download_log if r["nav_type"] == "N" and r["status"] == "failed")
        nav_d_failed = sum(1 for r in self.download_log if r["nav_type"] == "D" and r["status"] == "failed")
        
        print("\n" + "="*60)
        print("NAV DOWNLOAD COMPLETE")
        print("="*60)
        print("\nNAV File Types:")
        print("  NAV N (Parcel Account Records): Summary totals for each parcel")
        print("  NAV D (Assessment Detail Records): Detailed levy information")
        print("\nDownload Results:")
        print(f"  NAV N files downloaded: {nav_n_success}")
        print(f"  NAV D files downloaded: {nav_d_success}")
        print(f"  NAV N files failed: {nav_n_failed}")
        print(f"  NAV D files failed: {nav_d_failed}")
        print(f"  Total NAV files successful: {nav_n_success + nav_d_success}")
        print("="*60)


async def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue NAV Data Downloader - Fixed Version")
    print("="*60)
    print("NAV = Non Ad Valorem Assessment Data")
    print("  NAV N = Parcel account records (summary)")
    print("  NAV D = Assessment detail records (detailed levies)")
    print("="*60)
    print("\nThis version navigates to the NAV N and NAV D subdirectories")
    print("to find and download the actual TXT files.")
    print("="*60)
    
    downloader = FloridaNAVDownloader(base_path)
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())