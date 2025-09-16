import asyncio
import os
import zipfile
import shutil
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import aiohttp
import aiofiles
from playwright.async_api import async_playwright, Page, Browser
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'florida_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaRevenueDownloader:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.data_types = {
            'NAL': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P',
            'NAP': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P',
            'SDF': 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P'
        }
        
        # Florida counties (67 total)
        self.florida_counties = [
            'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
            'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DADE', 'DESOTO',
            'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST',
            'GLADES', 'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS',
            'HILLSBOROUGH', 'HOLMES', 'INDIAN_RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE',
            'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION',
            'MARTIN', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA',
            'PALM_BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA_ROSA', 'SARASOTA',
            'SEMINOLE', 'ST_JOHNS', 'ST_LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION',
            'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
        ]
        
        self.downloaded_files = set()
        self.failed_downloads = []
        self.stats = {
            'total_files': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'extracted': 0
        }

    async def setup_browser(self) -> Browser:
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        return browser

    async def extract_download_links(self, page: Page, url: str, data_type: str) -> List[Tuple[str, str]]:
        """Extract all download links from a Florida Revenue page"""
        logger.info(f"Extracting download links for {data_type} from {url}")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Wait for the file listing to load
            await page.wait_for_selector('a[href*=".zip"]', timeout=30000)
            
            # Extract all ZIP file links
            links = await page.evaluate('''
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href*=".zip"]');
                    anchors.forEach(anchor => {
                        const href = anchor.href;
                        const text = anchor.textContent.trim();
                        if (href && text && href.includes('.zip')) {
                            links.push({
                                url: href,
                                filename: text.includes('.zip') ? text : text + '.zip'
                            });
                        }
                    });
                    return links;
                }
            ''')
            
            # Filter and format links
            download_links = []
            for link in links:
                filename = link['filename'].replace('.zip', '').strip()
                if any(county.lower() in filename.lower() for county in self.florida_counties):
                    download_links.append((link['url'], filename + '.zip'))
            
            logger.info(f"Found {len(download_links)} download links for {data_type}")
            return download_links
            
        except Exception as e:
            logger.error(f"Failed to extract links for {data_type}: {e}")
            return []

    def get_county_from_filename(self, filename: str) -> str:
        """Extract county name from filename"""
        filename_upper = filename.upper()
        for county in self.florida_counties:
            if county in filename_upper:
                return county
        return 'UNKNOWN'

    async def download_file(self, session: aiohttp.ClientSession, url: str, filepath: Path) -> bool:
        """Download a single file"""
        try:
            logger.info(f"Downloading: {filepath.name}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"Successfully downloaded: {filepath.name}")
                    return True
                else:
                    logger.error(f"Failed to download {filepath.name}: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error downloading {filepath.name}: {e}")
            return False

    def extract_zip_file(self, zip_path: Path, extract_dir: Path) -> bool:
        """Extract ZIP file and delete the ZIP"""
        try:
            logger.info(f"Extracting: {zip_path.name}")
            
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Delete the ZIP file after successful extraction
            zip_path.unlink()
            
            logger.info(f"Successfully extracted and removed: {zip_path.name}")
            self.stats['extracted'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error extracting {zip_path.name}: {e}")
            return False

    def file_already_exists(self, county_dir: Path, filename: str) -> bool:
        """Check if file or its extracted contents already exist"""
        zip_path = county_dir / filename
        
        # Check if ZIP file exists
        if zip_path.exists():
            return True
        
        # Check if extracted files exist (common patterns)
        base_name = filename.replace('.zip', '')
        possible_extensions = ['.txt', '.csv', '.dat', '']
        
        for ext in possible_extensions:
            if (county_dir / f"{base_name}{ext}").exists():
                return True
        
        # Check for any files that start with the base name
        if county_dir.exists():
            for existing_file in county_dir.iterdir():
                if existing_file.name.startswith(base_name.split('_')[0]):
                    return True
        
        return False

    async def download_data_type(self, browser: Browser, data_type: str, url: str) -> None:
        """Download all files for a specific data type"""
        logger.info(f"Starting download for {data_type}")
        
        page = await browser.new_page()
        
        try:
            # Extract download links
            download_links = await self.extract_download_links(page, url, data_type)
            
            if not download_links:
                logger.warning(f"No download links found for {data_type}")
                return
            
            # Create aiohttp session for downloads
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes per file
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                for download_url, filename in download_links:
                    try:
                        # Determine county from filename
                        county = self.get_county_from_filename(filename)
                        
                        # Create directory structure
                        county_dir = self.base_path / county / data_type
                        county_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Check if file already exists
                        if self.file_already_exists(county_dir, filename):
                            logger.info(f"Skipping existing file: {filename}")
                            self.stats['skipped'] += 1
                            continue
                        
                        # Download file
                        filepath = county_dir / filename
                        success = await self.download_file(session, download_url, filepath)
                        
                        if success:
                            self.stats['downloaded'] += 1
                            self.downloaded_files.add(str(filepath))
                            
                            # Extract ZIP file
                            if filepath.suffix.lower() == '.zip':
                                self.extract_zip_file(filepath, county_dir)
                        else:
                            self.stats['failed'] += 1
                            self.failed_downloads.append({
                                'url': download_url,
                                'filename': filename,
                                'data_type': data_type,
                                'county': county
                            })
                        
                        # Small delay between downloads
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing {filename}: {e}")
                        self.stats['failed'] += 1
                        continue
                        
        except Exception as e:
            logger.error(f"Error downloading {data_type}: {e}")
        finally:
            await page.close()

    async def run_comprehensive_download(self) -> None:
        """Run the complete download process for all data types"""
        start_time = datetime.now()
        logger.info("Starting comprehensive Florida Revenue download")
        logger.info(f"Base directory: {self.base_path}")
        
        browser = await self.setup_browser()
        
        try:
            # Download each data type
            for data_type, url in self.data_types.items():
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing {data_type}")
                logger.info(f"{'='*50}")
                
                await self.download_data_type(browser, data_type, url)
                
                # Brief pause between data types
                await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Critical error during download process: {e}")
        finally:
            await browser.close()
        
        # Final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*50}")
        logger.info("DOWNLOAD COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Total files processed: {self.stats['downloaded'] + self.stats['skipped'] + self.stats['failed']}")
        logger.info(f"Successfully downloaded: {self.stats['downloaded']}")
        logger.info(f"Skipped (already exist): {self.stats['skipped']}")
        logger.info(f"Failed downloads: {self.stats['failed']}")
        logger.info(f"ZIP files extracted: {self.stats['extracted']}")
        
        if self.failed_downloads:
            logger.info(f"\nFailed downloads ({len(self.failed_downloads)}):")
            for failed in self.failed_downloads[:10]:  # Show first 10
                logger.info(f"  - {failed['filename']} ({failed['data_type']}, {failed['county']})")
            if len(self.failed_downloads) > 10:
                logger.info(f"  ... and {len(self.failed_downloads) - 10} more")

        # Save failed downloads to file for retry
        if self.failed_downloads:
            import json
            failed_file = self.base_path / f"failed_downloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(failed_file, 'w') as f:
                json.dump(self.failed_downloads, f, indent=2)
            logger.info(f"Failed downloads saved to: {failed_file}")

async def main():
    """Main execution function"""
    downloader = FloridaRevenueDownloader()
    await downloader.run_comprehensive_download()

if __name__ == "__main__":
    asyncio.run(main())