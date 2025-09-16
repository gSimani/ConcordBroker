"""
Florida Revenue NAV Data Downloader
Downloads NAV N and NAV D files (Non Ad Valorem assessment data)
Based on the navlayout.pdf specifications
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
        logging.FileHandler('florida_nav_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaNAVDownloader:
    """
    Downloads NAV (Non Ad Valorem) assessment files from Florida Revenue
    
    NAV N (Table N) - Parcel account records:
    - Roll Type, County number, PA Parcel Number, TC Account number
    - Tax year, Total assessments, Number of assessments, Tax roll sequence
    
    NAV D (Table D) - Assessment detail records:
    - Record Type, County number, PA Parcel Number, Levy identifier
    - Local government code, Function code, Assessment amount, Tax roll sequence
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024"
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
        
        if "NAVN" in filename or "NAVD" in filename:
            # Extract county code (2 digits after NAV[N/D])
            try:
                if "NAVN" in filename:
                    code = filename.split("NAVN")[1][:2]
                elif "NAVD" in filename:
                    code = filename.split("NAVD")[1][:2]
                else:
                    return None
                
                # Find county by code
                for county, county_code in self.counties.items():
                    if county_code == code:
                        return county
            except:
                pass
        
        # Try to match county name directly in filename
        for county in self.counties.keys():
            if county.replace(" ", "").upper() in filename.upper():
                return county
        
        return None
    
    async def extract_links_async(self, data_type: str) -> List[Dict]:
        """Extract download links for NAV files using Playwright"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                url = self.base_url
                logger.info(f"Extracting NAV {data_type} links from {url}")
                
                await page.goto(url, wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(3000)
                
                # Find all NAV files
                if data_type == "N":
                    # Look for NAVN files
                    links = await page.locator('a:has-text("NAVN")').all()
                elif data_type == "D":
                    # Look for NAVD files
                    links = await page.locator('a:has-text("NAVD")').all()
                else:
                    links = []
                
                download_links = []
                for link in links:
                    try:
                        text = await link.inner_text()
                        href = await link.get_attribute('href')
                        
                        # Convert relative URLs to absolute
                        if href and not href.startswith('http'):
                            href = f"https://floridarevenue.com{href}"
                        
                        download_links.append({
                            'filename': text.strip(),
                            'url': href,
                            'nav_type': data_type
                        })
                    except:
                        continue
                
                logger.info(f"Found {len(download_links)} NAV {data_type} files")
                return download_links
                
            except Exception as e:
                logger.error(f"Failed to extract NAV {data_type} links: {e}")
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
            logger.error(f"Download error: {e}")
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
        
        # Get download links
        links = await self.extract_links_async(nav_type)
        
        if not links:
            logger.warning(f"No NAV {nav_type} files found")
            return
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for link in links:
            filename = link['filename']
            url = link['url']
            
            # Extract county
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
            if await self.download_file_async(url, dest_file):
                # Extract if it's a zip
                if filename.endswith('.zip'):
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
        logger.info("Starting Florida NAV Data Download")
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
        
        print("\n" + "="*60)
        print("NAV DOWNLOAD COMPLETE")
        print("="*60)
        print("\nNAV File Types:")
        print("  NAV N (Parcel Account Records): Summary totals for each parcel")
        print("  NAV D (Assessment Detail Records): Detailed levy information")
        print("\nDownload Results:")
        print(f"  NAV N files downloaded: {nav_n_success}")
        print(f"  NAV D files downloaded: {nav_d_success}")
        print(f"  Total NAV files: {nav_n_success + nav_d_success}")
        print("="*60)


async def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue NAV Data Downloader")
    print("="*60)
    print("NAV = Non Ad Valorem Assessment Data")
    print("  NAV N = Parcel account records (summary)")
    print("  NAV D = Assessment detail records (detailed levies)")
    print("="*60)
    
    downloader = FloridaNAVDownloader(base_path)
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())