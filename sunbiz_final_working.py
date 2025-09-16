"""
Sunbiz SFTP Final Working Downloader
Uses the Open button to properly navigate into folders
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SunbizFinalDownloader:
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        self.downloaded_files = []
        self.failed_downloads = []
        self.processed_folders = []
        
    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            page = await context.new_page()
            
            try:
                # Login
                logger.info("Logging in...")
                await page.goto(self.url, wait_until='networkidle')
                await page.fill('input#username', self.username)
                await page.fill('input#password', self.password)
                await page.click('button:has-text("Login")')
                await page.wait_for_load_state('networkidle')
                logger.info("Login successful")
                
                # Navigate to doc folder using Open button
                logger.info("Opening doc folder...")
                
                # First select the doc folder by clicking on it
                await page.click('td.link.folder:has-text("doc")')
                await asyncio.sleep(1)
                
                # Now click the Open button to enter the folder
                await page.click('#open-link')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Verify we're in doc folder
                breadcrumb = await page.inner_text('#crumbtrail')
                logger.info(f"Current location: {breadcrumb}")
                
                # Create local doc folder
                doc_path = self.base_path / 'doc'
                doc_path.mkdir(exist_ok=True)
                
                # Process doc folder contents
                await self.process_current_folder(page, doc_path)
                
                # Generate report
                self.generate_report()
                
            except Exception as e:
                logger.error(f"Error: {e}")
                # Take error screenshot
                await page.screenshot(path=self.base_path / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                raise
            finally:
                await browser.close()
                
    async def process_current_folder(self, page, local_path: Path, depth=0):
        """Process all items in current folder"""
        if depth > 10:  # Prevent infinite recursion
            logger.warning(f"Max depth reached at {local_path}")
            return
            
        logger.info(f"Processing folder: {local_path.name} (depth: {depth})")
        
        # Get all items in current folder
        items = await self.get_folder_items(page)
        
        # Separate files and folders
        files = [i for i in items if not i['is_folder']]
        folders = [i for i in items if i['is_folder']]
        
        logger.info(f"Found {len(files)} files and {len(folders)} folders")
        
        # Download all files first
        for file_item in files:
            await self.download_file(page, file_item['name'], local_path)
            
        # Process each subfolder
        for folder in folders:
            folder_name = folder['name']
            
            # Create local folder
            local_folder = local_path / folder_name
            local_folder.mkdir(exist_ok=True)
            
            # Track processed folders to avoid loops
            folder_key = f"{local_path}/{folder_name}"
            if folder_key in self.processed_folders:
                logger.warning(f"Already processed {folder_key}, skipping")
                continue
            self.processed_folders.append(folder_key)
            
            # Select and open the folder
            logger.info(f"Opening folder: {folder_name}")
            await page.click(f'td.link.folder:has-text("{folder_name}")')
            await asyncio.sleep(0.5)
            await page.click('#open-link')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
            # Process subfolder recursively
            await self.process_current_folder(page, local_folder, depth + 1)
            
            # Go back to parent folder
            logger.info("Returning to parent folder...")
            await page.click('#parent-link')
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
    async def get_folder_items(self, page) -> List[Dict]:
        """Get all items in current folder"""
        items = []
        
        # Execute JavaScript to get table data
        table_data = await page.evaluate('''
            () => {
                const items = [];
                const rows = document.querySelectorAll('#results_body tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const name = cells[0].textContent.trim();
                        // Skip parent directory
                        if (name === '..') return;
                        
                        const type = cells[1].textContent.trim();
                        const date = cells[2].textContent.trim();
                        const size = cells[3].textContent.trim();
                        
                        items.push({
                            name: name,
                            type: type,
                            date: date,
                            size: size,
                            is_folder: type.toLowerCase().includes('folder')
                        });
                    }
                });
                
                return items;
            }
        ''')
        
        return table_data
        
    async def download_file(self, page, file_name: str, local_path: Path):
        """Download a single file"""
        file_path = local_path / file_name
        
        # Skip if exists
        if file_path.exists():
            logger.info(f"Skipping existing: {file_name}")
            return
            
        try:
            logger.info(f"Downloading: {file_name}")
            
            # Select the file
            await page.click(f'td.link.file:has-text("{file_name}")')
            await asyncio.sleep(0.5)
            
            # Download
            async with page.expect_download() as download_info:
                await page.click('#download-link')
                download = await download_info.value
                
            # Save
            await download.save_as(file_path)
            self.downloaded_files.append(str(file_path))
            logger.info(f"✓ Downloaded: {file_name}")
            
        except Exception as e:
            logger.error(f"✗ Failed: {file_name} - {e}")
            self.failed_downloads.append(file_name)
            
    def generate_report(self):
        """Generate final report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'downloaded': len(self.downloaded_files),
            'failed': len(self.failed_downloads),
            'processed_folders': len(self.processed_folders),
            'files': self.downloaded_files,
            'failures': self.failed_downloads
        }
        
        report_file = self.base_path / f'final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print("\n" + "="*60)
        print("SUNBIZ DOWNLOAD COMPLETE")
        print("="*60)
        print(f"✓ Downloaded: {len(self.downloaded_files)} files")
        print(f"✓ Processed: {len(self.processed_folders)} folders")
        print(f"✗ Failed: {len(self.failed_downloads)} files")
        print(f"\nBase path: {self.base_path}")
        print(f"Report: {report_file}")
        print("="*60)

if __name__ == "__main__":
    print("\nSunbiz SFTP Downloader - Final Version")
    print("Using Open button for proper navigation")
    print("-" * 50)
    asyncio.run(SunbizFinalDownloader().run())