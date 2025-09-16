"""
Florida Revenue Data Download Agent
Uses Playwright to intelligently scrape and download all NAL, NAP, and SDF files
Similar architecture to the Sunbiz agent system
"""

import os
import sys
import time
import json
import zipfile
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from playwright.async_api import async_playwright, Page, Browser, Download
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_revenue_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataType(Enum):
    """Types of data files available"""
    NAL = "NAL"  # Non Ad Valorem
    NAP = "NAP"  # Non Ad Valorem Property  
    SDF = "SDF"  # Sales Data File

@dataclass
class DownloadTask:
    """Represents a file download task"""
    county: str
    data_type: DataType
    url: str
    filename: str
    status: str = "pending"
    file_path: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

class FloridaRevenueAgent:
    """
    Intelligent agent for downloading Florida Revenue data files
    Uses Playwright to navigate and download files from the Florida Revenue website
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.download_tasks: List[DownloadTask] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.download_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Base URLs for each data type
        self.base_urls = {
            DataType.NAL: "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P",
            DataType.NAP: "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P",
            DataType.SDF: "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P"
        }
        
    async def initialize(self):
        """Initialize the browser and page"""
        logger.info("Initializing Florida Revenue Agent...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        logger.info("Browser initialized successfully")
        
    async def navigate_to_data_page(self, data_type: DataType) -> bool:
        """Navigate to the specific data type page"""
        try:
            url = self.base_urls[data_type]
            logger.info(f"Navigating to {data_type.value} page: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await self.page.wait_for_timeout(3000)  # Wait for dynamic content
            
            # Check if we're on the right page
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {data_type.value} page: {e}")
            return False
    
    async def scrape_file_links(self, data_type: DataType) -> List[Dict]:
        """Scrape all downloadable file links from the current page"""
        try:
            logger.info(f"Scraping {data_type.value} file links...")
            
            # Wait for the file list to load
            await self.page.wait_for_selector('a[href*=".zip"], a[href*=".xlsx"]', timeout=10000)
            
            # Get all file links
            file_links = await self.page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href*=".zip"], a[href*=".xlsx"]');
                    return Array.from(links).map(link => ({
                        text: link.innerText.trim(),
                        href: link.href,
                        filename: link.innerText.trim()
                    }));
                }
            """)
            
            logger.info(f"Found {len(file_links)} {data_type.value} files")
            
            # Parse and create download tasks
            tasks = []
            for link in file_links:
                county = self.extract_county_from_filename(link['filename'])
                if county:
                    task = DownloadTask(
                        county=county,
                        data_type=data_type,
                        url=link['href'],
                        filename=link['filename']
                    )
                    tasks.append(task)
                    self.download_tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to scrape {data_type.value} links: {e}")
            return []
    
    def extract_county_from_filename(self, filename: str) -> Optional[str]:
        """Extract county name from filename"""
        # Remove file extension and clean up
        name = filename.replace('.zip', '').replace('.xlsx', '').strip()
        
        # Common patterns: "County 11 Preliminary NAL 2025", "County NAL 2025", etc.
        parts = name.split()
        if parts:
            # First word is usually the county name
            county = parts[0].upper()
            
            # Handle special cases
            county_mapping = {
                "MIAMI": "MIAMI-DADE",
                "SAINT": "ST.",  # For St. Johns, St. Lucie
                "DESOTO": "DESOTO",
                "INDIAN": "INDIAN RIVER",
                "PALM": "PALM BEACH",
                "SANTA": "SANTA ROSA"
            }
            
            if county in county_mapping:
                if county == "SAINT" and len(parts) > 1:
                    return f"ST. {parts[1].upper()}"
                elif county == "INDIAN" and len(parts) > 1 and parts[1].upper() == "RIVER":
                    return "INDIAN RIVER"
                elif county == "PALM" and len(parts) > 1 and parts[1].upper() == "BEACH":
                    return "PALM BEACH"
                elif county == "SANTA" and len(parts) > 1 and parts[1].upper() == "ROSA":
                    return "SANTA ROSA"
                else:
                    return county_mapping.get(county, county)
            
            return county
        
        return None
    
    def get_county_folder(self, county: str, data_type: DataType) -> Path:
        """Get the destination folder for a county and data type"""
        folder = self.base_path / county / data_type.value
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    async def download_file(self, task: DownloadTask) -> bool:
        """Download a single file"""
        try:
            dest_folder = self.get_county_folder(task.county, task.data_type)
            
            # Check if file already exists
            existing_files = list(dest_folder.glob("*.csv")) + list(dest_folder.glob("*.xlsx")) + list(dest_folder.glob("*.xls"))
            if existing_files:
                logger.info(f"File already exists for {task.county}/{task.data_type.value}")
                task.status = "skipped"
                task.file_path = str(existing_files[0])
                self.download_stats["skipped"] += 1
                return True
            
            logger.info(f"Downloading {task.filename} for {task.county}")
            
            # Click the link to download
            link_selector = f'a[href="{task.url}"]'
            
            # Handle the download
            async with self.page.expect_download() as download_info:
                await self.page.click(link_selector)
            
            download = await download_info.value
            
            # Save the file
            dest_path = dest_folder / task.filename
            await download.save_as(dest_path)
            
            # Extract if it's a zip file
            if task.filename.endswith('.zip'):
                await self.extract_zip(dest_path)
            
            task.status = "success"
            task.file_path = str(dest_path)
            task.timestamp = datetime.now().isoformat()
            self.download_stats["success"] += 1
            
            logger.info(f"Successfully downloaded {task.filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {task.filename}: {e}")
            task.status = "failed"
            task.error = str(e)
            task.timestamp = datetime.now().isoformat()
            self.download_stats["failed"] += 1
            return False
    
    async def extract_zip(self, zip_path: Path):
        """Extract a zip file and delete it"""
        try:
            logger.info(f"Extracting {zip_path.name}")
            
            # Run extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._extract_zip_sync, zip_path)
            
        except Exception as e:
            logger.error(f"Failed to extract {zip_path}: {e}")
    
    def _extract_zip_sync(self, zip_path: Path):
        """Synchronous zip extraction"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(zip_path.parent)
        zip_path.unlink()  # Delete zip after extraction
        logger.info(f"Extracted and removed {zip_path.name}")
    
    async def download_all_files(self, data_type: DataType):
        """Download all files for a specific data type"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading {data_type.value} files")
        logger.info(f"{'='*60}")
        
        # Navigate to the data page
        if not await self.navigate_to_data_page(data_type):
            logger.error(f"Failed to navigate to {data_type.value} page")
            return
        
        # Scrape file links
        tasks = await self.scrape_file_links(data_type)
        
        if not tasks:
            logger.warning(f"No {data_type.value} files found")
            return
        
        # Download each file
        for i, task in enumerate(tasks, 1):
            logger.info(f"\n[{i}/{len(tasks)}] Processing {task.county} - {data_type.value}")
            await self.download_file(task)
            
            # Small delay between downloads
            if task.status == "success":
                await self.page.wait_for_timeout(2000)
        
        logger.info(f"\nCompleted {data_type.value} downloads")
        logger.info(f"Success: {sum(1 for t in tasks if t.status == 'success')}")
        logger.info(f"Skipped: {sum(1 for t in tasks if t.status == 'skipped')}")
        logger.info(f"Failed: {sum(1 for t in tasks if t.status == 'failed')}")
    
    async def run(self):
        """Main execution method"""
        try:
            await self.initialize()
            
            # Download files for each data type
            for data_type in DataType:
                await self.download_all_files(data_type)
            
            # Save results
            await self.save_report()
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
        finally:
            if self.browser:
                await self.browser.close()
    
    async def save_report(self):
        """Save a detailed report of all downloads"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.download_stats,
            "tasks": [
                {
                    "county": task.county,
                    "data_type": task.data_type.value,
                    "filename": task.filename,
                    "status": task.status,
                    "file_path": task.file_path,
                    "error": task.error,
                    "timestamp": task.timestamp
                }
                for task in self.download_tasks
            ]
        }
        
        report_file = self.base_path / f"florida_revenue_agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json.dumps(report, indent=2))
        
        logger.info(f"Report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("FLORIDA REVENUE AGENT - FINAL SUMMARY")
        print("="*60)
        print(f"Total files processed: {self.download_stats['total']}")
        print(f"Successfully downloaded: {self.download_stats['success']}")
        print(f"Already existed: {self.download_stats['skipped']}")
        print(f"Failed: {self.download_stats['failed']}")
        print("="*60)
        
        # Show failed downloads
        failed_tasks = [t for t in self.download_tasks if t.status == "failed"]
        if failed_tasks:
            print("\nFailed downloads:")
            for task in failed_tasks:
                print(f"  - {task.county}/{task.data_type.value}: {task.error}")


async def main():
    """Main entry point"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue Data Download Agent")
    print("="*60)
    print(f"Base path: {base_path}")
    print(f"Data types: NAL, NAP, SDF")
    print(f"Year: 2025P")
    print("="*60)
    print("\nStarting intelligent download agent...")
    
    agent = FloridaRevenueAgent(base_path)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())