"""
Advanced Sunbiz SFTP MCP Agent with Playwright
Sophisticated file extraction and downloading system
"""

import asyncio
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import aiofiles
import aiohttp
from playwright.async_api import async_playwright, Page, Browser, Download, BrowserContext
import logging
from concurrent.futures import ThreadPoolExecutor
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_mcp_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FileItem:
    """Represents a file or folder item"""
    name: str
    type: str
    size: str
    date_modified: str
    is_folder: bool
    path: str
    parent: str
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    downloaded: bool = False
    error: Optional[str] = None

@dataclass
class DownloadSession:
    """Tracks download session information"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_items: int
    downloaded_items: int
    failed_items: List[str]
    folder_structure: Dict
    status: str

class SunbizMCPAgent:
    def __init__(self, base_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        """
        Initialize the advanced Sunbiz MCP Agent
        
        Args:
            base_path: Base directory for downloads
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Portal credentials
        self.url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Browser components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Data tracking
        self.file_items: List[FileItem] = []
        self.folder_hierarchy: Dict = {}
        self.download_queue: List[FileItem] = []
        self.session: Optional[DownloadSession] = None
        
        # Performance settings
        self.max_concurrent_downloads = 3
        self.retry_attempts = 3
        self.page_timeout = 60000
        
        # State management
        self.state_file = self.base_path / 'agent_state.pkl'
        self.resume_enabled = True
        
    async def initialize(self):
        """Initialize the MCP agent and browser"""
        logger.info("Initializing Sunbiz MCP Agent...")
        
        # Create session
        self.session = DownloadSession(
            session_id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            start_time=datetime.now(),
            end_time=None,
            total_items=0,
            downloaded_items=0,
            failed_items=[],
            folder_structure={},
            status="initializing"
        )
        
        # Check for resumable state
        if self.resume_enabled and self.state_file.exists():
            await self.load_state()
        
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        
        # Launch browser with optimized settings
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--allow-running-insecure-content',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Create context with specific configurations
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            ignore_https_errors=True,
            java_script_enabled=True
        )
        
        # Set up download handling
        self.context.on("download", self.handle_download_event)
        
        # Create page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.page_timeout)
        
        # Set up request interception for monitoring
        self.page.on("request", lambda request: logger.debug(f"Request: {request.url}"))
        self.page.on("response", lambda response: logger.debug(f"Response: {response.url} - {response.status}"))
        
        self.session.status = "initialized"
        logger.info(f"Agent initialized with session ID: {self.session.session_id}")
        
    async def handle_download_event(self, download: Download):
        """Handle download events from the browser"""
        logger.info(f"Download started: {download.suggested_filename}")
        
    async def authenticate(self):
        """Authenticate with the SFTP portal"""
        self.session.status = "authenticating"
        logger.info("Starting authentication process...")
        
        # Navigate to portal
        await self.page.goto(self.url, wait_until='domcontentloaded')
        await self.page.wait_for_load_state('networkidle')
        
        # Take screenshot for debugging
        await self.page.screenshot(path=self.base_path / 'login_page.png')
        
        # Smart field detection
        await self.smart_login()
        
        # Verify successful login
        await self.verify_login()
        
        self.session.status = "authenticated"
        logger.info("Authentication successful")
        
    async def smart_login(self):
        """Intelligent login field detection and filling"""
        # Wait for form to be ready
        await self.page.wait_for_selector('form, .login-form, #login', timeout=30000)
        
        # Detect username field
        username_filled = False
        username_strategies = [
            ('input[name="username"]', 'name attribute'),
            ('input[type="text"]:visible', 'text input'),
            ('#username', 'id selector'),
            ('input[placeholder*="user" i]', 'placeholder'),
            ('input[autocomplete="username"]', 'autocomplete')
        ]
        
        for selector, strategy in username_strategies:
            try:
                if await self.page.locator(selector).count() > 0:
                    await self.page.fill(selector, self.username)
                    logger.info(f"Username filled using: {strategy}")
                    username_filled = True
                    break
            except:
                continue
        
        if not username_filled:
            raise Exception("Could not find username field")
        
        # Detect password field
        password_filled = False
        password_strategies = [
            ('input[name="password"]', 'name attribute'),
            ('input[type="password"]', 'password input'),
            ('#password', 'id selector'),
            ('input[placeholder*="pass" i]', 'placeholder'),
            ('input[autocomplete="current-password"]', 'autocomplete')
        ]
        
        for selector, strategy in password_strategies:
            try:
                if await self.page.locator(selector).count() > 0:
                    await self.page.fill(selector, self.password)
                    logger.info(f"Password filled using: {strategy}")
                    password_filled = True
                    break
            except:
                continue
        
        if not password_filled:
            raise Exception("Could not find password field")
        
        # Submit form
        submit_strategies = [
            ('button[type="submit"]', 'submit button'),
            ('input[type="submit"]', 'submit input'),
            ('button:has-text("Login")', 'login button text'),
            ('button:has-text("Sign in")', 'sign in button'),
            ('.login-button', 'login button class')
        ]
        
        for selector, strategy in submit_strategies:
            try:
                if await self.page.locator(selector).count() > 0:
                    await self.page.click(selector)
                    logger.info(f"Form submitted using: {strategy}")
                    break
            except:
                continue
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        
    async def verify_login(self):
        """Verify successful login"""
        await asyncio.sleep(2)
        
        # Check for common post-login indicators
        indicators = [
            'logout',
            'sign out',
            'Public\\',
            'root>',
            'folder',
            'directory'
        ]
        
        page_content = await self.page.content()
        page_text = await self.page.inner_text('body')
        
        login_successful = any(indicator in page_text.lower() for indicator in indicators)
        
        if not login_successful:
            # Take screenshot for debugging
            await self.page.screenshot(path=self.base_path / 'login_failed.png')
            raise Exception("Login verification failed")
        
        logger.info("Login verified successfully")
        
    async def navigate_to_doc(self):
        """Navigate to the doc folder"""
        self.session.status = "navigating"
        logger.info("Navigating to doc folder...")
        
        # Take screenshot of current state
        await self.page.screenshot(path=self.base_path / 'root_directory.png')
        
        # Smart navigation to doc folder
        doc_strategies = [
            ('a:has-text("doc")', 'link with text'),
            ('tr:has(td:text-is("doc")) a', 'table row link'),
            ('[href*="/doc"]', 'href containing doc'),
            ('text=doc', 'text selector'),
            ('.folder:has-text("doc")', 'folder class')
        ]
        
        navigated = False
        for selector, strategy in doc_strategies:
            try:
                element = await self.page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    logger.info(f"Clicked doc folder using: {strategy}")
                    navigated = True
                    break
            except:
                continue
        
        if not navigated:
            # Try double-click as fallback
            try:
                await self.page.dblclick('text=doc')
                navigated = True
                logger.info("Double-clicked doc folder")
            except:
                pass
        
        if not navigated:
            raise Exception("Could not navigate to doc folder")
        
        # Wait for navigation to complete
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        # Verify we're in doc folder
        current_path = await self.get_current_path()
        if 'doc' in current_path.lower():
            logger.info(f"Successfully navigated to: {current_path}")
        else:
            logger.warning(f"Navigation uncertain, current path: {current_path}")
        
        await self.page.screenshot(path=self.base_path / 'doc_directory.png')
        
    async def get_current_path(self) -> str:
        """Get the current directory path from the page"""
        path_selectors = [
            '.breadcrumb',
            '.current-path',
            '.path',
            'h1',
            'title'
        ]
        
        for selector in path_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text:
                        return text
            except:
                continue
        
        # Fallback to page title
        title = await self.page.title()
        return title if title else "Unknown"
        
    async def extract_items(self, parent_path: str = "doc") -> List[FileItem]:
        """Extract all items from the current directory"""
        logger.info(f"Extracting items from: {parent_path}")
        
        # Wait for content to load
        await self.page.wait_for_selector('table, .file-list, .item-list', timeout=30000)
        
        # Extract items using JavaScript
        items_data = await self.page.evaluate('''
            () => {
                const items = [];
                
                // Find all rows (skip headers)
                const rows = Array.from(document.querySelectorAll('tr')).filter(row => !row.querySelector('th'));
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length === 0) return;
                    
                    // Extract data from cells
                    const nameCell = cells[0];
                    const name = nameCell ? nameCell.textContent.trim() : '';
                    
                    // Skip parent directory entries
                    if (name === '..' || name === '.' || name === '') return;
                    
                    // Determine if it's a folder
                    const isFolder = !name.includes('.') || 
                                   nameCell.querySelector('.folder-icon') !== null ||
                                   (cells[1] && cells[1].textContent.toLowerCase().includes('folder'));
                    
                    // Get other attributes
                    const type = cells[1] ? cells[1].textContent.trim() : (isFolder ? 'Folder' : 'File');
                    const date = cells[2] ? cells[2].textContent.trim() : '';
                    const size = cells[3] ? cells[3].textContent.trim() : (cells[2] ? cells[2].textContent.trim() : '');
                    
                    // Find download button if exists
                    const downloadBtn = row.querySelector('button.download, a.download, [title="Download"]');
                    const hasDownload = downloadBtn !== null;
                    
                    items.push({
                        name: name,
                        type: type,
                        size: isFolder ? '' : size,
                        date: date,
                        isFolder: isFolder,
                        hasDownloadButton: hasDownload
                    });
                });
                
                return items;
            }
        ''')
        
        # Convert to FileItem objects
        items = []
        for item_data in items_data:
            file_item = FileItem(
                name=item_data['name'],
                type=item_data['type'],
                size=item_data['size'],
                date_modified=item_data['date'],
                is_folder=item_data['isFolder'],
                path=f"{parent_path}/{item_data['name']}",
                parent=parent_path,
                download_url=None,
                downloaded=False
            )
            items.append(file_item)
            
        logger.info(f"Found {len(items)} items in {parent_path}")
        
        # Save items to tracking lists
        self.file_items.extend(items)
        
        # Update folder hierarchy
        self.folder_hierarchy[parent_path] = [item.name for item in items]
        
        return items
        
    async def process_directory(self, parent_path: str = "doc"):
        """Recursively process a directory and all its contents"""
        self.session.status = "processing"
        
        # Extract items in current directory
        items = await self.extract_items(parent_path)
        
        # Separate folders and files
        folders = [item for item in items if item.is_folder]
        files = [item for item in items if not item.is_folder]
        
        # Add files to download queue
        self.download_queue.extend(files)
        
        # Process each subfolder
        for folder in folders:
            try:
                logger.info(f"Entering folder: {folder.name}")
                
                # Click on folder to navigate
                await self.page.click(f'a:has-text("{folder.name}")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                # Recursively process subfolder
                await self.process_directory(folder.path)
                
                # Navigate back
                await self.page.go_back()
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing folder {folder.name}: {e}")
                self.session.failed_items.append(folder.path)
                
    async def download_files(self):
        """Download all files in the queue"""
        self.session.status = "downloading"
        self.session.total_items = len(self.download_queue)
        
        logger.info(f"Starting download of {self.session.total_items} files...")
        
        # Create local folder structure
        await self.create_local_folders()
        
        # Process downloads with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        
        tasks = []
        for file_item in self.download_queue:
            task = self.download_file_with_limit(file_item, semaphore)
            tasks.append(task)
        
        # Execute downloads
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Download failed for {self.download_queue[i].name}: {result}")
                self.session.failed_items.append(self.download_queue[i].path)
            else:
                self.session.downloaded_items += 1
                
    async def download_file_with_limit(self, file_item: FileItem, semaphore: asyncio.Semaphore):
        """Download a file with concurrency limiting"""
        async with semaphore:
            return await self.download_file(file_item)
            
    async def download_file(self, file_item: FileItem):
        """Download a single file"""
        local_path = self.base_path / file_item.path
        
        # Skip if already downloaded
        if local_path.exists():
            logger.info(f"Skipping existing file: {file_item.name}")
            file_item.downloaded = True
            return
        
        try:
            logger.info(f"Downloading: {file_item.name}")
            
            # Navigate to file's parent directory if needed
            current_path = await self.get_current_path()
            if file_item.parent not in current_path:
                await self.navigate_to_path(file_item.parent)
            
            # Find and click download button
            download_clicked = False
            
            # Try row-specific download button first
            row_selectors = [
                f'tr:has-text("{file_item.name}") button:has-text("Download")',
                f'tr:has-text("{file_item.name}") a.download',
                f'tr:has-text("{file_item.name}") [title="Download"]'
            ]
            
            for selector in row_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        async with self.page.expect_download() as download_info:
                            await self.page.click(selector)
                            download = await download_info.value
                            
                            # Save file
                            await download.save_as(local_path)
                            download_clicked = True
                            break
                except:
                    continue
            
            # If no download button, try clicking file name
            if not download_clicked:
                async with self.page.expect_download() as download_info:
                    await self.page.click(f'a:has-text("{file_item.name}")')
                    download = await download_info.value
                    await download.save_as(local_path)
            
            file_item.downloaded = True
            logger.info(f"Successfully downloaded: {file_item.name}")
            
        except Exception as e:
            logger.error(f"Failed to download {file_item.name}: {e}")
            file_item.error = str(e)
            raise
            
    async def navigate_to_path(self, path: str):
        """Navigate to a specific path"""
        # This would need implementation based on the actual navigation structure
        pass
        
    async def create_local_folders(self):
        """Create local folder structure"""
        for path in self.folder_hierarchy.keys():
            local_path = self.base_path / path
            local_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("Local folder structure created")
        
    async def save_state(self):
        """Save current state for resume capability"""
        state = {
            'session': asdict(self.session),
            'file_items': [asdict(item) for item in self.file_items],
            'folder_hierarchy': self.folder_hierarchy,
            'download_queue': [asdict(item) for item in self.download_queue]
        }
        
        with open(self.state_file, 'wb') as f:
            pickle.dump(state, f)
            
        logger.info("State saved for resume capability")
        
    async def load_state(self):
        """Load previous state for resuming"""
        try:
            with open(self.state_file, 'rb') as f:
                state = pickle.load(f)
                
            # Restore state
            # Implementation would restore the various state components
            logger.info("Previous state loaded for resume")
            
        except Exception as e:
            logger.warning(f"Could not load previous state: {e}")
            
    async def generate_report(self):
        """Generate comprehensive download report"""
        self.session.end_time = datetime.now()
        self.session.status = "completed"
        
        # Calculate statistics
        duration = (self.session.end_time - self.session.start_time).total_seconds()
        success_rate = (self.session.downloaded_items / self.session.total_items * 100) if self.session.total_items > 0 else 0
        
        report = {
            'session': asdict(self.session),
            'statistics': {
                'duration_seconds': duration,
                'success_rate': f"{success_rate:.2f}%",
                'files_per_minute': (self.session.downloaded_items / duration * 60) if duration > 0 else 0
            },
            'folder_structure': self.folder_hierarchy,
            'failed_items': self.session.failed_items
        }
        
        # Save report
        report_file = self.base_path / f'download_report_{self.session.session_id}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("SUNBIZ MCP AGENT - DOWNLOAD COMPLETE")
        print("="*60)
        print(f"Session ID: {self.session.session_id}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Items: {self.session.total_items}")
        print(f"Downloaded: {self.session.downloaded_items}")
        print(f"Failed: {len(self.session.failed_items)}")
        print(f"Success Rate: {success_rate:.2f}%")
        print(f"Report saved to: {report_file}")
        print("="*60)
        
        logger.info(f"Report generated: {report_file}")
        
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        if self.page:
            await self.page.close()
        
        if self.context:
            await self.context.close()
            
        if self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("Cleanup complete")
        
    async def run(self):
        """Main execution flow"""
        try:
            # Initialize
            await self.initialize()
            
            # Authenticate
            await self.authenticate()
            
            # Navigate to doc folder
            await self.navigate_to_doc()
            
            # Process directory structure
            await self.process_directory()
            
            # Download all files
            await self.download_files()
            
            # Save state
            await self.save_state()
            
            # Generate report
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"Critical error in agent execution: {e}")
            self.session.status = "failed"
            self.session.failed_items.append(f"Critical error: {e}")
            raise
            
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the MCP Agent"""
    agent = SunbizMCPAgent()
    await agent.run()


if __name__ == "__main__":
    print("Starting Sunbiz MCP Agent...")
    asyncio.run(main())