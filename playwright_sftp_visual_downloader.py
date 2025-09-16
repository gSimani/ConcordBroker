"""
Playwright SFTP Visual Downloader - Properly navigates the Data Access Portal
Downloads missing files while keeping browser visible for monitoring
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

class VisualSFTPDownloader:
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
        self.existing_files = {}
        
    def scan_existing_files(self):
        """Scan what we already have downloaded"""
        print("\n📂 Scanning existing files...")
        
        doc_path = self.base_path / "doc"
        if doc_path.exists():
            # Count files in each directory
            for item in doc_path.iterdir():
                if item.is_dir():
                    file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                    self.existing_files[item.name] = file_count
                elif item.is_file():
                    self.existing_files[item.name] = "file"
                    
        print(f"✅ Found data in {len(self.existing_files)} locations")
        for name, count in list(self.existing_files.items())[:10]:
            if count == "file":
                print(f"   📄 {name}")
            else:
                print(f"   📁 {name}/: {count} files")
                
    async def initialize_browser(self):
        """Initialize Playwright browser - VISIBLE"""
        print("\n🚀 Starting browser (VISIBLE for monitoring)...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # KEEP VISIBLE
            args=['--start-maximized']
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(30000)
        
        print("✅ Browser window opened - you can watch the progress!")
        
    async def login(self):
        """Login to SFTP portal"""
        print(f"\n🔐 Navigating to {self.base_url}...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        print("📸 Taking screenshot of login page...")
        screenshot_path = self.base_path / f"sftp_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        
        print("🔑 Entering credentials...")
        
        # Fill username - try multiple selectors
        try:
            await self.page.fill('input[placeholder="Username"]', self.username)
        except:
            try:
                await self.page.fill('input[name="username"]', self.username)
            except:
                await self.page.fill('input[type="text"]', self.username)
        print("   ✓ Username: Public")
        
        # Fill password - try multiple selectors
        try:
            await self.page.fill('input[placeholder="Password"]', self.password)
        except:
            try:
                await self.page.fill('input[name="password"]', self.password)
            except:
                await self.page.fill('input[type="password"]', self.password)
        print("   ✓ Password: ********")
        
        # Click login button - the green Login button
        try:
            await self.page.click('button:has-text("Login")')
        except:
            try:
                await self.page.click('button.btn-success')
            except:
                await self.page.click('button[type="submit"]')
        print("   ✓ Clicking login...")
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Verify we're logged in by checking for the doc folder
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=5000)
            print("✅ Successfully logged in! Now in <root>\\Public\\")
            
            # Take screenshot
            after_login = self.base_path / f"sftp_main_directory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(after_login))
            print(f"📸 Screenshot saved: {after_login.name}")
        except:
            print("⚠️ Login may have failed or page structure changed")
            
    async def enter_doc_folder(self):
        """Navigate into the doc folder"""
        print("\n📁 Entering 'doc' folder...")
        
        try:
            # Method 1: Double-click on the doc row
            await self.page.dblclick('tr:has-text("doc")')
            print("   ✓ Double-clicked on doc folder")
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Verify we're in doc folder
            current_folder = await self.page.text_content('text=/Current folder/')
            if current_folder:
                print(f"   ✓ Current location: {current_folder}")
            
            # Take screenshot of doc folder contents
            doc_screenshot = self.base_path / f"sftp_doc_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(doc_screenshot))
            print(f"📸 Doc folder contents: {doc_screenshot.name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Could not enter doc folder: {e}")
            
            # Try alternative method - click Open button
            try:
                print("   🔄 Trying alternative method...")
                await self.page.click('tr:has-text("doc")')  # Select row
                await self.page.click('button:has-text("Open")')  # Click Open
                await self.page.wait_for_load_state('networkidle')
                return True
            except:
                return False
                
    async def get_folder_contents(self):
        """Get list of items in current folder"""
        print("\n📊 Analyzing folder contents...")
        
        # First scroll to see if there are more items
        await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)
        
        items = await self.page.evaluate('''
            () => {
                const items = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    // Skip header row and parent directory
                    if (row.querySelector('th')) return;
                    
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const name = cells[0]?.textContent?.trim();
                        const type = cells[1]?.textContent?.trim();
                        const dateModified = cells[2]?.textContent?.trim();
                        const size = cells[3]?.textContent?.trim();
                        
                        // Skip parent directory (..)
                        if (name && name !== '..' && name !== 'WELCOME.TXT') {
                            items.push({
                                name: name,
                                type: type,
                                isFolder: type === 'Folder',
                                dateModified: dateModified,
                                size: size
                            });
                        }
                    }
                });
                
                return items;
            }
        ''')
        
        # Categorize items
        folders = [i for i in items if i['isFolder']]
        files = [i for i in items if not i['isFolder']]
        
        print(f"Found {len(folders)} folders and {len(files)} files")
        
        # Show folders
        if folders:
            print("\n📁 Folders:")
            for folder in folders[:10]:
                status = "✅ Have data" if folder['name'] in self.existing_files else "❌ Missing"
                print(f"   {status} {folder['name']}/")
                
        # Show files
        if files:
            print("\n📄 Files:")
            for file in files[:10]:
                status = "✅ Downloaded" if file['name'] in self.existing_files else "❌ Need"
                print(f"   {status} {file['name']} ({file['size']})")
                
        return folders, files
        
    async def download_file(self, filename, save_path):
        """Download a single file"""
        print(f"\n📥 Downloading: {filename}")
        
        try:
            # Select the file row
            await self.page.click(f'tr:has-text("{filename}")')
            print(f"   ✓ Selected {filename}")
            
            # Click download button
            async with self.page.expect_download(timeout=60000) as download_info:
                await self.page.click('button:has-text("Download")')
                print(f"   ⏳ Download started...")
                
            download = await download_info.value
            
            # Save file
            full_path = save_path / filename
            await download.save_as(str(full_path))
            
            self.downloaded_files.append(str(full_path))
            print(f"   ✅ Saved to: {full_path}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            self.failed_downloads.append(filename)
            return False
            
    async def explore_and_download(self):
        """Explore folders and download missing files"""
        print("\n" + "="*60)
        print("STARTING INTELLIGENT DOWNLOAD")
        print("="*60)
        
        # Get current folder contents
        folders, files = await self.get_folder_contents()
        
        # Look for ZIP files by scrolling down
        print("\n🔍 Looking for ZIP files...")
        
        # Scroll down to see if there are files below folders
        for _ in range(3):  # Try scrolling multiple times
            await self.page.keyboard.press('End')
            await asyncio.sleep(1)
            
        # Get contents again after scrolling
        folders, files = await self.get_folder_contents()
        
        # Priority folders for officer/contact data
        priority_folders = ['AG', 'cor', 'fic']
        
        # Download priority files first
        priority_files = ['corprindata.zip', 'cordata_quarterly.zip', 'SAMPLE_OFFICERS.txt']
        
        doc_path = self.base_path / "doc"
        doc_path.mkdir(exist_ok=True)
        
        # Look for and download priority files if missing
        print(f"\n📄 Looking for priority files among {len(files)} files...")
        for filename in priority_files:
            file_item = next((f for f in files if filename in f['name']), None)
            if file_item and filename not in self.existing_files:
                print(f"\n⭐ Priority file found: {filename}")
                await self.download_file(filename, doc_path)
                await asyncio.sleep(2)
                
        # Explore priority folders
        for folder_name in priority_folders:
            folder_item = next((f for f in folders if f['name'] == folder_name), None)
            if folder_item and folder_name not in self.existing_files:
                print(f"\n📂 Exploring priority folder: {folder_name}")
                
                # Enter folder
                await self.page.dblclick(f'tr:has-text("{folder_name}")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Get contents
                sub_folders, sub_files = await self.get_folder_contents()
                
                # Create local folder
                folder_path = doc_path / folder_name
                folder_path.mkdir(exist_ok=True)
                
                # Download some files (limit for demo)
                for file in sub_files[:3]:
                    await self.download_file(file['name'], folder_path)
                    await asyncio.sleep(1)
                    
                # Go back to doc folder
                await self.page.go_back()
                await self.page.wait_for_load_state('networkidle')
                
        print("\n" + "="*60)
        print("DOWNLOAD SESSION SUMMARY")
        print("="*60)
        print(f"✅ Downloaded: {len(self.downloaded_files)} files")
        print(f"❌ Failed: {len(self.failed_downloads)} files")
        
        if self.downloaded_files:
            print("\n📥 Downloaded files:")
            for file in self.downloaded_files[:10]:
                print(f"   - {Path(file).name}")
                
    async def run(self):
        """Main execution"""
        print("="*60)
        print("VISUAL SFTP DOWNLOADER")
        print("Browser stays VISIBLE - Watch the download progress!")
        print("="*60)
        
        try:
            # Scan existing files
            self.scan_existing_files()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            await self.login()
            
            # Enter doc folder
            if await self.enter_doc_folder():
                # Start downloading
                await self.explore_and_download()
            else:
                print("❌ Could not access doc folder")
                
            # Keep browser open for inspection
            print("\n⏸️  Keeping browser open for 20 seconds...")
            print("You can manually browse or download additional files")
            await asyncio.sleep(20)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.browser:
                print("\n🔒 Closing browser...")
                await self.browser.close()
                
        # Save session report
        report = {
            'timestamp': datetime.now().isoformat(),
            'downloaded': self.downloaded_files,
            'failed': self.failed_downloads,
            'existing_folders': list(self.existing_files.keys())
        }
        
        report_path = self.base_path / f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Report saved: {report_path}")
        print("✅ Session complete!")

async def main():
    """Main entry point"""
    downloader = VisualSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("Starting Visual SFTP Downloader...")
    print("The browser window will stay visible throughout")
    print("-" * 60)
    asyncio.run(main())