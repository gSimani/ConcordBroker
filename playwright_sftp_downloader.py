"""
Playwright-based SFTP Downloader with Visual Progress
Downloads missing files from Florida Department of State SFTP portal
"""

import asyncio
import os
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
import time

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class PlaywrightSFTPDownloader:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local base path
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
        # Track downloads
        self.downloaded_files = []
        self.failed_downloads = []
        self.existing_files = set()
        
    def scan_existing_files(self):
        """Scan what we already have downloaded"""
        print("\n📂 Scanning existing files...")
        
        doc_path = self.base_path / "doc"
        if doc_path.exists():
            # Scan all subdirectories
            for item in doc_path.rglob("*"):
                if item.is_file():
                    # Store relative path from doc folder
                    rel_path = item.relative_to(doc_path)
                    self.existing_files.add(str(rel_path).replace("\\", "/"))
                    
        print(f"✅ Found {len(self.existing_files)} existing files")
        
        # Show sample of what we have
        if self.existing_files:
            print("\n📁 Sample existing files:")
            for file in list(self.existing_files)[:10]:
                print(f"   - {file}")
                
    async def initialize_browser(self):
        """Initialize Playwright browser - KEEP VISIBLE"""
        print("\n🚀 Starting browser (keeping it visible)...")
        
        playwright = await async_playwright().start()
        
        # Launch browser with headless=False to keep it visible
        self.browser = await playwright.chromium.launch(
            headless=False,  # KEEP BROWSER VISIBLE
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ]
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Set download path
        await context.route("**/*", lambda route: route.continue_())
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        print("✅ Browser ready and visible")
        
    async def login(self):
        """Login to SFTP portal"""
        print(f"\n🔐 Navigating to {self.base_url}...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Take screenshot
        screenshot_path = self.base_path / f"sftp_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        print(f"📸 Screenshot: {screenshot_path}")
        
        print("🔑 Entering credentials...")
        
        # Try multiple selectors for username
        try:
            await self.page.fill('input[name="username"]', self.username, timeout=5000)
        except:
            try:
                await self.page.fill('input[type="text"]:first-of-type', self.username)
            except:
                await self.page.fill('#username', self.username)
                
        print("   ✓ Username entered")
        
        # Enter password
        try:
            await self.page.fill('input[name="password"]', self.password, timeout=5000)
        except:
            await self.page.fill('input[type="password"]', self.password)
            
        print("   ✓ Password entered")
        
        # Click login
        try:
            await self.page.click('button[type="submit"]', timeout=5000)
        except:
            try:
                await self.page.click('input[type="submit"]')
            except:
                await self.page.click('button:has-text("Login")')
                
        print("   ✓ Login clicked")
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Screenshot after login
        after_login = self.base_path / f"sftp_after_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(after_login))
        print(f"📸 Logged in: {after_login}")
        
    async def navigate_to_folder(self, folder_name):
        """Navigate to a specific folder"""
        print(f"\n📁 Navigating to {folder_name}...")
        
        try:
            # Try clicking the folder link
            await self.page.click(f'a:has-text("{folder_name}")', timeout=5000)
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            print(f"   ✓ Entered {folder_name}")
            return True
        except:
            print(f"   ✗ Could not find {folder_name}")
            return False
            
    async def get_current_directory_files(self):
        """Get list of files in current directory"""
        files = await self.page.evaluate('''
            () => {
                const items = [];
                const links = document.querySelectorAll('a');
                
                links.forEach(link => {
                    const text = link.textContent.trim();
                    const href = link.getAttribute('href');
                    
                    // Skip navigation links
                    if (text && !text.includes('..') && !text.includes('Parent')) {
                        items.push({
                            name: text,
                            href: href,
                            isFile: text.includes('.') || href?.includes('download')
                        });
                    }
                });
                
                return items;
            }
        ''')
        
        return files
        
    async def download_file(self, file_info, save_path):
        """Download a single file"""
        filename = file_info['name']
        
        # Check if we already have it
        if filename in self.existing_files:
            print(f"   ⏭️  Skipping {filename} (already exists)")
            return True
            
        print(f"   📥 Downloading {filename}...")
        
        try:
            # Start download
            async with self.page.expect_download() as download_info:
                # Click the file link
                await self.page.click(f'a:has-text("{filename}")')
                
            download = await download_info.value
            
            # Save to specified path
            full_save_path = Path(save_path) / filename
            full_save_path.parent.mkdir(parents=True, exist_ok=True)
            
            await download.save_as(str(full_save_path))
            
            self.downloaded_files.append(str(full_save_path))
            print(f"   ✅ Saved: {full_save_path}")
            
            # Add small delay
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.failed_downloads.append(filename)
            return False
            
    async def download_directory_contents(self, dir_name, local_path, max_files=10):
        """Download contents of a directory"""
        print(f"\n📂 Processing directory: {dir_name}")
        
        # Navigate to directory
        if not await self.navigate_to_folder(dir_name):
            return
            
        # Get files in directory
        files = await self.get_current_directory_files()
        
        # Filter to actual files
        file_list = [f for f in files if f.get('isFile')]
        
        print(f"   Found {len(file_list)} files")
        
        # Download files (limit for demo)
        download_count = 0
        for file_info in file_list[:max_files]:
            if await self.download_file(file_info, local_path / dir_name):
                download_count += 1
                
        print(f"   ✅ Downloaded {download_count} files from {dir_name}")
        
        # Navigate back
        await self.page.go_back()
        await self.page.wait_for_load_state('networkidle')
        
    async def download_missing_files(self):
        """Main download process"""
        print("\n" + "="*60)
        print("STARTING DOWNLOAD PROCESS")
        print("="*60)
        
        # Navigate to doc folder first
        await self.navigate_to_folder("doc")
        
        # Get current directory listing
        items = await self.get_current_directory_files()
        
        # Separate files and folders
        folders = [i for i in items if not i.get('isFile')]
        files = [i for i in items if i.get('isFile')]
        
        print(f"\n📊 Found in doc folder:")
        print(f"   - {len(folders)} subdirectories")
        print(f"   - {len(files)} files")
        
        # Priority folders for officer data
        priority_folders = ['off', 'officers', 'principals', 'AG', 'annual', 'cor', 'fic']
        
        # Download from priority folders first
        doc_path = self.base_path / "doc"
        
        for folder_name in priority_folders:
            folder_item = next((f for f in folders if folder_name in f['name'].lower()), None)
            if folder_item:
                await self.download_directory_contents(
                    folder_item['name'], 
                    doc_path,
                    max_files=5  # Limit for demonstration
                )
                
        # Download some root files
        print("\n📄 Downloading root files...")
        for file_info in files[:5]:  # Limit for demonstration
            await self.download_file(file_info, doc_path)
            
        print("\n" + "="*60)
        print("DOWNLOAD SESSION COMPLETE")
        print("="*60)
        print(f"✅ Downloaded: {len(self.downloaded_files)} files")
        print(f"❌ Failed: {len(self.failed_downloads)} files")
        
        # Create report
        report = {
            'timestamp': datetime.now().isoformat(),
            'downloaded_files': self.downloaded_files,
            'failed_downloads': self.failed_downloads,
            'total_existing': len(self.existing_files),
            'session_downloads': len(self.downloaded_files)
        }
        
        report_path = self.base_path / f"download_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Report saved: {report_path}")
        
    async def run(self):
        """Main execution"""
        print("="*60)
        print("PLAYWRIGHT SFTP DOWNLOADER")
        print("Browser will stay VISIBLE during entire process")
        print("="*60)
        
        try:
            # Scan existing files
            self.scan_existing_files()
            
            # Initialize browser (stays visible)
            await self.initialize_browser()
            
            # Login
            await self.login()
            
            # Download missing files
            await self.download_missing_files()
            
            print("\n⏸️  Keeping browser open for 30 seconds...")
            print("You can interact with the page if needed")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            
        finally:
            if self.browser:
                print("\n🔒 Closing browser...")
                await self.browser.close()
                
        print("\n✅ Session complete!")

async def main():
    """Main entry point"""
    downloader = PlaywrightSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("Starting Playwright SFTP Downloader...")
    print("The browser will remain visible throughout the process")
    asyncio.run(main())