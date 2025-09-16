"""
Sunbiz SFTP Working Downloader - Corrected Navigation
Downloads all files from the doc folder in the Florida Department of State Data Access Portal
"""

import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright, Page
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_working.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunbizWorkingDownloader:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        """Initialize the downloader"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        self.page: Page = None
        self.downloaded_files = []
        self.failed_downloads = []
        
    async def run(self):
        """Main execution"""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            
            self.page = await context.new_page()
            self.page.set_default_timeout(60000)
            
            try:
                # Step 1: Navigate to site
                logger.info(f"Navigating to {self.url}")
                await self.page.goto(self.url, wait_until='networkidle')
                await asyncio.sleep(2)
                
                # Step 2: Login
                logger.info("Logging in...")
                await self.page.fill('input#username', self.username)
                await self.page.fill('input#password', self.password)
                await self.page.click('button:has-text("Login")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                logger.info("Login successful")
                
                # Step 3: Click on doc folder to enter it
                logger.info("Navigating into doc folder...")
                await self.page.click('td.link.folder:has-text("doc")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Verify we're in doc folder
                current_path = await self.get_current_path()
                logger.info(f"Current path: {current_path}")
                
                if 'doc' not in current_path.lower():
                    logger.warning("May not be in doc folder, trying double-click...")
                    await self.page.dblclick('td.link.folder:has-text("doc")')
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                
                # Step 4: Now we should be inside doc folder - list its contents
                logger.info("Listing contents of doc folder...")
                items = await self.list_current_directory_items()
                
                # Create local doc folder
                doc_path = self.base_path / 'doc'
                doc_path.mkdir(exist_ok=True)
                
                # Step 5: Process all items in doc folder
                await self.process_items_in_current_directory(doc_path, items)
                
                # Generate report
                self.generate_report()
                
            except Exception as e:
                logger.error(f"Error: {e}")
                raise
            finally:
                await browser.close()
                
    async def get_current_path(self) -> str:
        """Get current path from breadcrumb"""
        try:
            breadcrumb = await self.page.query_selector('#crumbtrail')
            if breadcrumb:
                text = await breadcrumb.inner_text()
                return text
            return "Unknown"
        except:
            return "Unknown"
            
    async def list_current_directory_items(self) -> List[Dict]:
        """List all items in the current directory"""
        items = []
        
        # Get all rows from the results table
        rows = await self.page.query_selector_all('#results_body tr')
        
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 4:
                name = await cells[0].inner_text()
                
                # Skip parent directory
                if name == "..":
                    continue
                    
                item_type = await cells[1].inner_text()
                date_modified = await cells[2].inner_text()
                size = await cells[3].inner_text()
                
                is_folder = "folder" in item_type.lower()
                
                items.append({
                    'name': name,
                    'type': item_type,
                    'date_modified': date_modified,
                    'size': size,
                    'is_folder': is_folder
                })
                
        logger.info(f"Found {len(items)} items in current directory")
        return items
        
    async def process_items_in_current_directory(self, local_path: Path, items: List[Dict]):
        """Process all items in the current directory"""
        
        # Separate folders and files
        folders = [item for item in items if item['is_folder']]
        files = [item for item in items if not item['is_folder']]
        
        logger.info(f"Processing {len(folders)} folders and {len(files)} files")
        
        # Download all files first
        for file_item in files:
            await self.download_file(file_item['name'], local_path)
            
        # Then process each folder
        for folder in folders:
            folder_name = folder['name']
            logger.info(f"Processing folder: {folder_name}")
            
            # Create local folder
            local_folder = local_path / folder_name
            local_folder.mkdir(exist_ok=True)
            
            # Navigate into the folder
            await self.page.click(f'td.link.folder:has-text("{folder_name}")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
            # List items in this folder
            sub_items = await self.list_current_directory_items()
            
            # Recursively process subfolder
            await self.process_items_in_current_directory(local_folder, sub_items)
            
            # Navigate back to parent
            logger.info("Going back to parent folder...")
            await self.page.click('td.link.folder:has-text("..")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
    async def download_file(self, file_name: str, local_path: Path):
        """Download a single file"""
        try:
            file_path = local_path / file_name
            
            # Skip if already exists
            if file_path.exists():
                logger.info(f"Skipping existing file: {file_name}")
                return
                
            logger.info(f"Downloading: {file_name}")
            
            # Click on the file to select it
            await self.page.click(f'td.link.file:has-text("{file_name}")')
            await asyncio.sleep(0.5)
            
            # Click download button
            async with self.page.expect_download() as download_info:
                await self.page.click('#download-link')
                download = await download_info.value
                
            # Save the file
            await download.save_as(file_path)
            
            self.downloaded_files.append(str(file_path))
            logger.info(f"Successfully downloaded: {file_name}")
            
        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")
            self.failed_downloads.append(file_name)
            
    def generate_report(self):
        """Generate and save download report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_downloaded': len(self.downloaded_files),
            'failed_downloads': len(self.failed_downloads),
            'downloaded_files': self.downloaded_files,
            'failed_files': self.failed_downloads
        }
        
        report_file = self.base_path / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("SUNBIZ DOWNLOAD COMPLETE")
        print("="*60)
        print(f"✓ Downloaded: {len(self.downloaded_files)} files")
        print(f"✗ Failed: {len(self.failed_downloads)} files")
        if self.failed_downloads:
            print(f"Failed files: {', '.join(self.failed_downloads[:5])}")
            if len(self.failed_downloads) > 5:
                print(f"  ... and {len(self.failed_downloads) - 5} more")
        print(f"\nFiles saved to: {self.base_path}")
        print(f"Report saved to: {report_file}")
        print("="*60)

async def main():
    downloader = SunbizWorkingDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\nStarting Sunbiz SFTP Downloader")
    print("This will download all files from the doc folder")
    print("-" * 50)
    asyncio.run(main())