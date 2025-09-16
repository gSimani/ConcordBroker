"""
Sunbiz SFTP Final Downloader - Complete Implementation
Downloads all files and folders from the Florida Department of State Data Access Portal
"""

import asyncio
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, Download
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_downloader_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunbizDownloader:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        """Initialize the Sunbiz Downloader"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        self.browser = None
        self.context = None
        self.page = None
        
        # Track downloads
        self.downloaded_files = []
        self.failed_downloads = []
        self.folder_structure = {}
        
    async def initialize_browser(self):
        """Initialize browser with optimal settings"""
        logger.info("Initializing browser...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--start-maximized']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        # Set page timeout (not context timeout)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)
        
        logger.info("Browser initialized")
        
    async def login(self):
        """Login to the SFTP portal"""
        logger.info(f"Navigating to {self.url}")
        await self.page.goto(self.url, wait_until='networkidle')
        
        # Wait for page to load
        await asyncio.sleep(2)
        
        # Fill username
        logger.info("Filling credentials...")
        await self.page.fill('input#username', self.username)
        await self.page.fill('input#password', self.password)
        
        # Click login
        await self.page.click('button:has-text("Login")')
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        logger.info("Login successful")
        
    async def navigate_to_folder(self, folder_name: str):
        """Navigate to a specific folder by clicking on it"""
        logger.info(f"Navigating to folder: {folder_name}")
        
        # Click on the folder link
        await self.page.click(f'td.link.folder:has-text("{folder_name}")')
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
        logger.info(f"Entered folder: {folder_name}")
        
    async def go_to_parent_folder(self):
        """Navigate to parent folder"""
        logger.info("Going to parent folder...")
        
        # Click on parent folder link or .. folder
        try:
            await self.page.click('td.link.folder:has-text("..")')
        except:
            await self.page.click('#parent-link')
        
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
    async def get_current_path(self) -> str:
        """Get current directory path from breadcrumb"""
        try:
            crumbs = await self.page.query_selector_all('#crumb-list a')
            path_parts = []
            for crumb in crumbs:
                text = await crumb.inner_text()
                path_parts.append(text)
            return '\\'.join(path_parts)
        except:
            return "Unknown"
            
    async def list_items(self) -> List[Dict]:
        """List all items in current directory"""
        logger.info("Listing items in current directory...")
        
        items = []
        
        # Get all table rows except header
        rows = await self.page.query_selector_all('#results_body tr')
        
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) < 4:
                continue
                
            name = await cells[0].inner_text()
            item_type = await cells[1].inner_text()
            date_modified = await cells[2].inner_text()
            size = await cells[3].inner_text() if len(cells) > 3 else ""
            
            # Skip parent directory
            if name == "..":
                continue
                
            is_folder = "folder" in item_type.lower()
            
            items.append({
                'name': name,
                'type': item_type,
                'date_modified': date_modified,
                'size': size,
                'is_folder': is_folder
            })
            
        logger.info(f"Found {len(items)} items")
        return items
        
    async def download_file(self, file_name: str, save_path: Path):
        """Download a single file"""
        try:
            logger.info(f"Downloading file: {file_name}")
            
            # First click on the file to select it
            await self.page.click(f'td.link.file:has-text("{file_name}")')
            await asyncio.sleep(0.5)
            
            # Click download button
            async with self.page.expect_download() as download_info:
                await self.page.click('#download-link')
                download = await download_info.value
                
            # Save the file
            await download.save_as(save_path)
            
            self.downloaded_files.append(str(save_path))
            logger.info(f"Downloaded: {file_name} -> {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")
            self.failed_downloads.append(file_name)
            
    async def process_directory(self, local_base: Path, path_prefix: str = ""):
        """Recursively process directory and download all contents"""
        current_path = await self.get_current_path()
        logger.info(f"Processing directory: {current_path}")
        
        # List items in current directory
        items = await self.list_items()
        
        # Separate folders and files
        folders = [item for item in items if item['is_folder']]
        files = [item for item in items if not item['is_folder']]
        
        # Download all files in current directory
        for file_item in files:
            file_path = local_base / file_item['name']
            
            # Skip if already downloaded
            if file_path.exists():
                logger.info(f"Skipping existing file: {file_item['name']}")
                continue
                
            await self.download_file(file_item['name'], file_path)
            await asyncio.sleep(1)  # Rate limiting
            
        # Process each subfolder
        for folder in folders:
            folder_name = folder['name']
            
            # Create local folder
            local_folder = local_base / folder_name
            local_folder.mkdir(exist_ok=True)
            
            # Navigate into folder
            await self.navigate_to_folder(folder_name)
            
            # Recursively process subfolder
            await self.process_directory(local_folder, f"{path_prefix}/{folder_name}")
            
            # Navigate back to parent
            await self.go_to_parent_folder()
            
    async def run(self):
        """Main execution flow"""
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Login
            await self.login()
            
            # Navigate to doc folder
            await self.navigate_to_folder('doc')
            
            # Create doc folder locally
            doc_path = self.base_path / 'doc'
            doc_path.mkdir(exist_ok=True)
            
            # Process the doc directory and all subdirectories
            await self.process_directory(doc_path, "doc")
            
            # Generate report
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"Critical error: {e}")
            raise
            
        finally:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
                
    async def generate_report(self):
        """Generate download report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_downloaded': len(self.downloaded_files),
            'failed_downloads': len(self.failed_downloads),
            'downloaded_files': self.downloaded_files,
            'failed_files': self.failed_downloads,
            'base_path': str(self.base_path)
        }
        
        report_file = self.base_path / f'download_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE")
        print("="*60)
        print(f"Total files downloaded: {len(self.downloaded_files)}")
        print(f"Failed downloads: {len(self.failed_downloads)}")
        if self.failed_downloads:
            print(f"Failed files: {', '.join(self.failed_downloads)}")
        print(f"Files saved to: {self.base_path}")
        print(f"Report saved to: {report_file}")
        print("="*60)

async def main():
    """Main entry point"""
    downloader = SunbizDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("Starting Sunbiz SFTP Downloader...")
    print("This will download all files from the doc folder.")
    print("-" * 50)
    asyncio.run(main())