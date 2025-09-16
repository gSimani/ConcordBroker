"""
Systematic Sunbiz SFTP Downloader for Missing Folders
======================================================
Downloads all missing folders from the Florida Department of State SFTP server
Uses chain of thought approach to ensure complete data extraction
"""

import asyncio
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
import aiofiles
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_missing_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunbizMissingDataDownloader:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        """Initialize the downloader for missing Sunbiz data"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Track what we need to download (missing folders)
        self.missing_folders = [
            'comp',           # Company/Compliance data
            'DHE',           # Department of Highway Safety
            'fic',           # Fictitious names (DBAs) - CRITICAL
            'ficevent-Year2000', # Historical fictitious name events
            'FLR',           # Florida Lien Registry - CRITICAL
            'gen',           # General partnerships
            'notes',         # Documentation
            'Quarterly',     # Quarterly reports
            'tm'             # Trademarks
        ]
        
        # Already downloaded folders (to skip)
        self.existing_folders = ['AG', 'cor', 'doc']
        
        # Track download progress
        self.download_stats = {
            'folders_processed': 0,
            'files_downloaded': 0,
            'bytes_downloaded': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        
    async def initialize_browser(self):
        """Initialize the browser with proper settings"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        
        # Use chromium with specific settings for file downloads
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for monitoring
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
        )
        
        # Create context with download handling
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        
        # Set download behavior
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            })
        """)
        
        logger.info("Browser initialized successfully")
        
    async def login(self) -> bool:
        """Login to the SFTP portal"""
        try:
            logger.info(f"Navigating to {self.url}")
            await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            
            # Wait for login form
            await self.page.wait_for_selector('input[name="j_username"]', timeout=10000)
            
            logger.info("Filling login credentials...")
            await self.page.fill('input[name="j_username"]', self.username)
            await self.page.fill('input[name="j_password"]', self.password)
            
            # Click login button
            await self.page.click('input[type="submit"][value="Login"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Check if we're in the doc folder
            current_url = self.page.url
            if 'doc' in current_url or await self.page.query_selector('text="Current folder"'):
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login may have failed - unexpected page state")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
            
    async def navigate_to_folder(self, folder_name: str) -> bool:
        """Navigate to a specific folder"""
        try:
            logger.info(f"Navigating to folder: {folder_name}")
            
            # Look for the folder in the current directory
            folder_link = await self.page.query_selector(f'a[title="{folder_name}"]')
            
            if not folder_link:
                # Try alternative selector
                folder_link = await self.page.query_selector(f'text="{folder_name}"')
                
            if folder_link:
                await folder_link.dblclick()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                logger.info(f"Entered folder: {folder_name}")
                return True
            else:
                logger.warning(f"Folder not found: {folder_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to folder {folder_name}: {e}")
            return False
            
    async def go_to_parent_folder(self):
        """Navigate to parent folder"""
        try:
            parent_button = await self.page.query_selector('button[title="Parent Folder"]')
            if not parent_button:
                parent_button = await self.page.query_selector('img[src*="up.gif"]')
                
            if parent_button:
                await parent_button.click()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                logger.info("Navigated to parent folder")
                return True
        except Exception as e:
            logger.error(f"Error navigating to parent: {e}")
        return False
        
    async def get_folder_contents(self) -> List[Dict]:
        """Get list of files and folders in current directory"""
        contents = []
        try:
            # Wait for the table to load
            await self.page.wait_for_selector('table', timeout=10000)
            
            # Find all rows in the file listing table
            rows = await self.page.query_selector_all('tr')
            
            for row in rows:
                # Get all cells in the row
                cells = await row.query_selector_all('td')
                
                if len(cells) >= 3:
                    # First cell usually has the name/link
                    name_element = await cells[0].query_selector('a')
                    if name_element:
                        name = await name_element.inner_text()
                        
                        # Check if it's a folder or file
                        img_element = await cells[0].query_selector('img')
                        img_src = await img_element.get_attribute('src') if img_element else ''
                        
                        is_folder = 'folder' in img_src.lower() or 'dir' in img_src.lower()
                        
                        # Get type from second cell
                        type_text = await cells[1].inner_text() if len(cells) > 1 else ''
                        
                        # Get date from third cell
                        date_text = await cells[2].inner_text() if len(cells) > 2 else ''
                        
                        contents.append({
                            'name': name.strip(),
                            'is_folder': is_folder or 'Folder' in type_text,
                            'type': type_text.strip(),
                            'date': date_text.strip()
                        })
                        
            logger.info(f"Found {len(contents)} items in current directory")
            return contents
            
        except Exception as e:
            logger.error(f"Error getting folder contents: {e}")
            return []
            
    async def download_file(self, filename: str, target_path: Path):
        """Download a single file"""
        try:
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if target_path.exists():
                logger.info(f"File already exists, skipping: {filename}")
                return True
                
            logger.info(f"Downloading: {filename}")
            
            # Find and click the file link
            file_link = await self.page.query_selector(f'a:has-text("{filename}")')
            
            if file_link:
                # Start waiting for download before clicking
                async with self.page.expect_download() as download_info:
                    await file_link.click()
                    download = await download_info.value
                    
                # Save the file
                await download.save_as(str(target_path))
                
                # Update stats
                self.download_stats['files_downloaded'] += 1
                if target_path.exists():
                    self.download_stats['bytes_downloaded'] += target_path.stat().st_size
                    
                logger.info(f"Downloaded: {filename} -> {target_path}")
                return True
            else:
                logger.warning(f"Could not find download link for: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            self.download_stats['errors'].append(f"Download failed: {filename} - {str(e)}")
            return False
            
    async def download_folder_recursive(self, folder_name: str, current_path: Path, max_depth: int = 5, current_depth: int = 0):
        """Recursively download all contents of a folder"""
        if current_depth >= max_depth:
            logger.warning(f"Maximum depth {max_depth} reached for {folder_name}")
            return
            
        logger.info(f"Processing folder: {folder_name} (depth: {current_depth})")
        
        # Navigate to the folder
        if not await self.navigate_to_folder(folder_name):
            logger.error(f"Could not navigate to folder: {folder_name}")
            return
            
        # Get folder contents
        contents = await self.get_folder_contents()
        
        # Create local folder
        local_folder = current_path / folder_name
        local_folder.mkdir(parents=True, exist_ok=True)
        
        # Process each item
        for item in contents:
            if item['name'] in ['.', '..', 'WELCOME.TXT']:
                continue
                
            if item['is_folder']:
                # Recursively download subfolder
                await self.download_folder_recursive(
                    item['name'], 
                    local_folder, 
                    max_depth, 
                    current_depth + 1
                )
                # Navigate back to parent after processing subfolder
                await self.go_to_parent_folder()
            else:
                # Download file
                target_file = local_folder / item['name']
                await self.download_file(item['name'], target_file)
                
        self.download_stats['folders_processed'] += 1
        
    async def download_all_missing_folders(self):
        """Main method to download all missing folders"""
        self.download_stats['start_time'] = datetime.now()
        
        try:
            # Initialize browser and login
            await self.initialize_browser()
            
            if not await self.login():
                logger.error("Failed to login to SFTP portal")
                return
                
            logger.info(f"Starting download of {len(self.missing_folders)} missing folders")
            logger.info(f"Missing folders: {', '.join(self.missing_folders)}")
            
            # Download each missing folder
            for folder_name in self.missing_folders:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing folder: {folder_name}")
                logger.info(f"{'='*60}")
                
                try:
                    # Navigate back to root/doc folder first
                    await self.page.goto(f"{self.url}/#!/%3Croot%3E%5CPublic%5Cdoc%5C", wait_until='networkidle')
                    await asyncio.sleep(2)
                    
                    # Download the folder
                    await self.download_folder_recursive(
                        folder_name,
                        self.base_path / 'doc',
                        max_depth=10  # Increase depth for thorough download
                    )
                    
                    logger.info(f"Completed downloading folder: {folder_name}")
                    
                except Exception as e:
                    logger.error(f"Error downloading folder {folder_name}: {e}")
                    self.download_stats['errors'].append(f"Folder download failed: {folder_name}")
                    
                # Small delay between folders
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Critical error during download: {e}")
            self.download_stats['errors'].append(f"Critical error: {str(e)}")
            
        finally:
            self.download_stats['end_time'] = datetime.now()
            
            # Close browser
            if self.browser:
                await self.browser.close()
                
            # Print summary
            self.print_summary()
            
    def print_summary(self):
        """Print download summary"""
        duration = (self.download_stats['end_time'] - self.download_stats['start_time']).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("="*60)
        logger.info(f"Start Time: {self.download_stats['start_time']}")
        logger.info(f"End Time: {self.download_stats['end_time']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Folders Processed: {self.download_stats['folders_processed']}")
        logger.info(f"Files Downloaded: {self.download_stats['files_downloaded']}")
        logger.info(f"Data Downloaded: {self.download_stats['bytes_downloaded'] / (1024*1024):.2f} MB")
        
        if self.download_stats['errors']:
            logger.warning(f"\nErrors ({len(self.download_stats['errors'])}):")
            for error in self.download_stats['errors'][:10]:  # Show first 10 errors
                logger.warning(f"  - {error}")
                
        # Save stats to file
        stats_file = self.base_path / 'download_stats.json'
        with open(stats_file, 'w') as f:
            json.dump(self.download_stats, f, indent=2, default=str)
        logger.info(f"\nStats saved to: {stats_file}")
        
async def main():
    """Main function to run the downloader"""
    logger.info("Starting Sunbiz Missing Data Downloader")
    logger.info("="*60)
    
    downloader = SunbizMissingDataDownloader()
    await downloader.download_all_missing_folders()
    
    logger.info("\n" + "="*60)
    logger.info("Download process completed!")
    logger.info("Check the log file for details: sunbiz_missing_download.log")

if __name__ == "__main__":
    asyncio.run(main())