"""
Sunbiz SFTP Portal File Downloader Agent
Downloads all files and folders from the Florida Department of State Data Access Portal
"""

import asyncio
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import aiofiles
import aiohttp
from playwright.async_api import async_playwright, Page, Browser, Download
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunbizSFTPDownloader:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        """
        Initialize the Sunbiz SFTP Downloader
        
        Args:
            base_path: Base directory where all files will be downloaded
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.download_queue: List[Dict] = []
        self.folder_structure: Dict = {}
        
        # Track download progress
        self.total_files = 0
        self.downloaded_files = 0
        self.failed_downloads = []
        
    async def initialize_browser(self):
        """Initialize Playwright browser with optimal settings"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        
        # Launch browser with download handling
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ],
            downloads_path=str(self.base_path)
        )
        
        # Create new context with specific settings
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(60000)
        
        logger.info("Browser initialized successfully")
        
    async def login(self):
        """Login to the SFTP portal"""
        logger.info(f"Navigating to {self.url}")
        await self.page.goto(self.url, wait_until='networkidle')
        
        # Wait for login form
        await self.page.wait_for_selector('input[type="text"], input[name="username"], #username', timeout=30000)
        
        logger.info("Entering credentials...")
        
        # Try multiple selectors for username field
        username_selectors = [
            'input[name="username"]',
            'input[type="text"]:first-of-type',
            '#username',
            'input[placeholder*="Username" i]'
        ]
        
        for selector in username_selectors:
            try:
                await self.page.fill(selector, self.username)
                logger.info(f"Username entered using selector: {selector}")
                break
            except:
                continue
        
        # Try multiple selectors for password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#password',
            'input[placeholder*="Password" i]'
        ]
        
        for selector in password_selectors:
            try:
                await self.page.fill(selector, self.password)
                logger.info(f"Password entered using selector: {selector}")
                break
            except:
                continue
        
        # Click login button
        login_button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'input[value="Login" i]',
            '.login-button',
            '#login-button'
        ]
        
        for selector in login_button_selectors:
            try:
                await self.page.click(selector)
                logger.info(f"Login button clicked using selector: {selector}")
                break
            except:
                continue
        
        # Wait for navigation after login
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)  # Additional wait for dynamic content
        
        logger.info("Login successful, navigated to root directory")
        
    async def navigate_to_doc_folder(self):
        """Navigate to the doc folder"""
        logger.info("Looking for doc folder...")
        
        # Try multiple approaches to find and click the doc folder
        doc_folder_selectors = [
            'a:has-text("doc")',
            'tr:has-text("doc") a',
            'td:has-text("doc")',
            '[href*="doc"]',
            'a[title="doc"]',
            '.folder-link:has-text("doc")'
        ]
        
        for selector in doc_folder_selectors:
            try:
                # Wait for the element to be visible
                element = await self.page.wait_for_selector(selector, timeout=10000)
                if element:
                    await element.click()
                    logger.info(f"Clicked doc folder using selector: {selector}")
                    break
            except:
                continue
        
        # Alternative: Try double-clicking if single click doesn't work
        try:
            await self.page.dblclick('text=doc')
        except:
            pass
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        logger.info("Navigated to doc folder")
        
    async def extract_folder_structure(self):
        """Extract the folder structure from the current page"""
        logger.info("Extracting folder structure...")
        
        # Wait for the file listing to load
        await self.page.wait_for_selector('table, .file-list, .folder-list', timeout=30000)
        
        # Extract all folders and files
        folders = await self.page.evaluate('''
            () => {
                const items = [];
                
                // Try different table structures
                const rows = document.querySelectorAll('tr, .file-row, .folder-row');
                
                rows.forEach(row => {
                    // Skip header rows
                    if (row.querySelector('th')) return;
                    
                    // Extract folder/file information
                    const nameElement = row.querySelector('a, .name, td:first-child');
                    const typeElement = row.querySelector('.type, td:nth-child(2)');
                    const sizeElement = row.querySelector('.size, td:nth-child(3), td:last-child');
                    const dateElement = row.querySelector('.date, td:nth-child(4)');
                    
                    if (nameElement) {
                        const name = nameElement.textContent.trim();
                        // Skip parent directory links
                        if (name === '..' || name === '.') return;
                        
                        items.push({
                            name: name,
                            type: typeElement ? typeElement.textContent.trim() : 'Folder',
                            size: sizeElement ? sizeElement.textContent.trim() : '',
                            date: dateElement ? dateElement.textContent.trim() : '',
                            isFolder: !name.includes('.') || (typeElement && typeElement.textContent.toLowerCase().includes('folder'))
                        });
                    }
                });
                
                return items;
            }
        ''')
        
        self.folder_structure = {
            'root': 'doc',
            'items': folders
        }
        
        logger.info(f"Found {len(folders)} items in doc folder")
        
        # Save folder structure
        structure_file = self.base_path / 'folder_structure.json'
        with open(structure_file, 'w') as f:
            json.dump(self.folder_structure, f, indent=2)
        
        return folders
        
    async def download_item(self, item: Dict, parent_path: Path):
        """Download a single item (file or folder)"""
        item_name = item['name']
        item_path = parent_path / item_name
        
        if item['isFolder']:
            # Create folder locally
            item_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created folder: {item_path}")
            
            # Navigate into folder on website
            try:
                await self.page.click(f'a:has-text("{item_name}")')
                await self.page.wait_for_load_state('networkidle')
                
                # Recursively download folder contents
                sub_items = await self.extract_folder_structure()
                for sub_item in sub_items:
                    await self.download_item(sub_item, item_path)
                
                # Navigate back
                await self.page.go_back()
                await self.page.wait_for_load_state('networkidle')
                
            except Exception as e:
                logger.error(f"Error processing folder {item_name}: {e}")
                self.failed_downloads.append(item_name)
        else:
            # Download file
            try:
                logger.info(f"Downloading file: {item_name}")
                
                # Look for download button/link
                download_selectors = [
                    f'tr:has-text("{item_name}") button.download',
                    f'tr:has-text("{item_name}") a.download',
                    f'tr:has-text("{item_name}") [title="Download"]',
                    f'button[onclick*="{item_name}"]',
                    f'a[href*="{item_name}"][download]'
                ]
                
                # Start waiting for download before clicking
                async with self.page.expect_download() as download_info:
                    # Try different selectors
                    clicked = False
                    for selector in download_selectors:
                        try:
                            await self.page.click(selector)
                            clicked = True
                            break
                        except:
                            continue
                    
                    # If no download button found, try clicking the file name itself
                    if not clicked:
                        await self.page.click(f'a:has-text("{item_name}")')
                
                download = await download_info.value
                
                # Save the download
                save_path = item_path
                await download.save_as(save_path)
                
                self.downloaded_files += 1
                logger.info(f"Downloaded: {item_name} to {save_path}")
                
            except Exception as e:
                logger.error(f"Error downloading {item_name}: {e}")
                self.failed_downloads.append(item_name)
                
    async def download_all_items(self):
        """Download all items from the current directory"""
        items = await self.extract_folder_structure()
        self.total_files = len(items)
        
        logger.info(f"Starting download of {self.total_files} items...")
        
        # Create doc folder locally
        doc_path = self.base_path / 'doc'
        doc_path.mkdir(exist_ok=True)
        
        # Download each item
        for item in items:
            await self.download_item(item, doc_path)
            
            # Add small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
        
        logger.info(f"Download complete! Downloaded {self.downloaded_files} files")
        if self.failed_downloads:
            logger.warning(f"Failed downloads: {self.failed_downloads}")
            
    async def run(self):
        """Main execution flow"""
        try:
            # Initialize browser
            await self.initialize_browser()
            
            # Login to portal
            await self.login()
            
            # Navigate to doc folder
            await self.navigate_to_doc_folder()
            
            # Download all items
            await self.download_all_items()
            
            # Generate report
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"Critical error: {e}")
            raise
        finally:
            if self.browser:
                await self.browser.close()
                
    async def generate_report(self):
        """Generate a download report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_items': self.total_files,
            'downloaded_files': self.downloaded_files,
            'failed_downloads': self.failed_downloads,
            'folder_structure': self.folder_structure,
            'base_path': str(self.base_path)
        }
        
        report_file = self.base_path / 'download_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("DOWNLOAD SUMMARY")
        print("="*50)
        print(f"Total items: {self.total_files}")
        print(f"Successfully downloaded: {self.downloaded_files}")
        print(f"Failed downloads: {len(self.failed_downloads)}")
        if self.failed_downloads:
            print(f"Failed items: {', '.join(self.failed_downloads)}")
        print(f"Files saved to: {self.base_path}")
        print("="*50)


async def main():
    """Main entry point"""
    downloader = SunbizSFTPDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())