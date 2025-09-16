"""
Playwright SFTP Active Downloader - Downloads missing files with visible browser
Compares local files with remote and downloads what's missing
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

class ActiveSFTPDownloader:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local base path
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
        # Track files
        self.local_files = {}
        self.remote_files = {}
        self.downloaded_count = 0
        self.current_location = "root"
        
    def scan_local_files(self):
        """Scan all local files recursively"""
        print("\n" + "="*60)
        print("📂 SCANNING LOCAL FILES")
        print("="*60)
        
        # Scan root TEMP\DATABASE
        for item in self.base_path.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                self.local_files[item.name] = size_mb
                print(f"✅ {item.name}: {size_mb:.1f} MB")
                
        # Scan doc folder and subfolders
        doc_path = self.base_path / "doc"
        if doc_path.exists():
            for root, dirs, files in os.walk(doc_path):
                for file in files:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.base_path)
                    size_mb = full_path.stat().st_size / (1024 * 1024)
                    self.local_files[str(rel_path).replace('\\', '/')] = size_mb
                    
            # Show summary by folder
            for folder in doc_path.iterdir():
                if folder.is_dir():
                    count = sum(1 for _ in folder.rglob("*") if _.is_file())
                    print(f"📁 doc/{folder.name}: {count} files")
                    
        print(f"\n✅ Total local files: {len(self.local_files)}")
        
    async def initialize_browser(self):
        """Start visible browser"""
        print("\n🚀 Starting VISIBLE browser...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # VISIBLE
            args=['--start-maximized'],
            slow_mo=300  # Slow actions for visibility
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Set download path
        await context.route("**/*", lambda route: route.continue_())
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        print("✅ Browser window opened - VISIBLE for monitoring")
        
    async def login(self):
        """Login to portal"""
        print("\n🔐 Logging in...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Fill credentials
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        # Click login
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Verify login
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            print("✅ Logged in successfully!")
            self.current_location = "root"
            return True
        except:
            print("❌ Login failed")
            return False
            
    async def get_current_files(self):
        """Get files in current directory"""
        print(f"\n📊 Getting files in {self.current_location}...")
        
        # Scroll to load all items
        for _ in range(3):
            await self.page.keyboard.press('PageDown')
            await asyncio.sleep(0.5)
            
        # Parse table rows
        rows = await self.page.query_selector_all('tr')
        items = []
        
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 4:
                name_elem = cells[0]
                type_elem = cells[1]
                size_elem = cells[3]
                
                name = await name_elem.text_content() if name_elem else ""
                type_text = await type_elem.text_content() if type_elem else ""
                size = await size_elem.text_content() if size_elem else ""
                
                if name and name not in ['..', 'WELCOME.TXT']:
                    is_folder = type_text == "Folder" or "/" in type_text or not "." in name
                    items.append({
                        'name': name.strip(),
                        'type': 'folder' if is_folder else 'file',
                        'size': size.strip()
                    })
                    
        return items
        
    async def explore_and_download(self):
        """Main download logic"""
        print("\n" + "="*60)
        print("🔍 EXPLORING AND DOWNLOADING")
        print("="*60)
        
        # Get items in root
        root_items = await self.get_current_files()
        
        # Look for ZIP files in root first
        print("\n📄 Checking root for ZIP files...")
        for item in root_items:
            if item['type'] == 'file' and item['name'].endswith('.zip'):
                if item['name'] not in self.local_files:
                    print(f"   ❌ MISSING: {item['name']} - {item['size']}")
                    await self.download_file(item['name'])
                else:
                    print(f"   ✅ HAVE: {item['name']}")
                    
        # Enter doc folder
        print("\n📂 Entering doc folder...")
        await self.page.dblclick('tr:has-text("doc")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        self.current_location = "doc"
        
        # Get doc contents
        doc_items = await self.get_current_files()
        
        # Process doc folder
        folders_to_check = ['cor', 'AG', 'fic', 'gen', 'DHE', 'FLR']
        
        for folder_name in folders_to_check:
            folder_item = next((i for i in doc_items if i['name'] == folder_name and i['type'] == 'folder'), None)
            
            if folder_item:
                print(f"\n📁 Checking folder: {folder_name}")
                
                # Check if we have any files from this folder
                local_folder_files = [f for f in self.local_files if f.startswith(f"doc/{folder_name}/")]
                
                if len(local_folder_files) == 0:
                    print(f"   ❌ No files from {folder_name} - downloading some...")
                    
                    # Enter folder
                    await self.page.dblclick(f'tr:has-text("{folder_name}")')
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                    # Get files
                    folder_files = await self.get_current_files()
                    
                    # Download first 5 files as sample
                    files_to_download = [f for f in folder_files if f['type'] == 'file'][:5]
                    
                    for file in files_to_download:
                        await self.download_file(file['name'], f"doc/{folder_name}")
                        
                    # Go back to doc
                    await self.page.click('tr:has-text("..")')
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                else:
                    print(f"   ✅ Have {len(local_folder_files)} files from {folder_name}")
                    
        # Look for any ZIP files in doc folder
        print("\n📄 Looking for ZIP files in doc folder...")
        
        # Scroll down to find files after folders
        for _ in range(5):
            await self.page.keyboard.press('End')
            await asyncio.sleep(1)
            
        # Get updated items
        doc_items = await self.get_current_files()
        
        for item in doc_items:
            if item['type'] == 'file' and '.zip' in item['name']:
                local_path = f"doc/{item['name']}"
                if local_path not in self.local_files:
                    print(f"   ❌ MISSING: {item['name']} - {item['size']}")
                    await self.download_file(item['name'], "doc")
                else:
                    print(f"   ✅ HAVE: {item['name']}")
                    
    async def download_file(self, filename, subfolder=""):
        """Download a single file"""
        try:
            print(f"\n📥 Downloading: {filename}")
            
            # Click on file
            await self.page.click(f'tr:has-text("{filename}")')
            await asyncio.sleep(0.5)
            
            # Start download
            async with self.page.expect_download(timeout=120000) as download_info:
                await self.page.click('button:has-text("Download")')
                print("   ⏳ Download started...")
                
            download = await download_info.value
            
            # Determine save path
            if subfolder:
                save_dir = self.base_path / subfolder
                save_dir.mkdir(parents=True, exist_ok=True)
            else:
                save_dir = self.base_path
                
            save_path = save_dir / filename
            await download.save_as(str(save_path))
            
            self.downloaded_count += 1
            print(f"   ✅ Saved to: {save_path}")
            
            # Update local files
            rel_path = str(save_path.relative_to(self.base_path)).replace('\\', '/')
            self.local_files[rel_path] = save_path.stat().st_size / (1024 * 1024)
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return False
            
    async def continuous_monitor(self):
        """Keep browser open for manual downloads"""
        print("\n" + "="*60)
        print("🔄 CONTINUOUS MONITORING MODE")
        print("="*60)
        print("Browser will stay open - you can manually download files")
        print("Press Ctrl+C to stop when done")
        
        start_time = time.time()
        
        try:
            while True:
                elapsed = int(time.time() - start_time)
                mins = elapsed // 60
                secs = elapsed % 60
                
                status = f"⏱️ Active: {mins:02d}:{secs:02d} | Downloads: {self.downloaded_count} | Location: {self.current_location}"
                print(f"\r{status}", end="")
                
                await asyncio.sleep(5)
                
                # Take periodic screenshot
                if elapsed % 120 == 0 and elapsed > 0:
                    screenshot = self.base_path / f"active_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot))
                    print(f"\n📸 Screenshot: {screenshot.name}")
                    
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("ACTIVE SFTP DOWNLOADER")
        print("Browser stays VISIBLE for monitoring")
        print("="*60)
        
        try:
            # Scan local files
            self.scan_local_files()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                print("❌ Login failed")
                await asyncio.sleep(60)
                return
                
            # Explore and download
            await self.explore_and_download()
            
            # Summary
            print("\n" + "="*60)
            print("DOWNLOAD SUMMARY")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"📁 Total local files: {len(self.local_files)}")
            
            # Keep browser open for monitoring
            await self.continuous_monitor()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Keep browser open on error
            print("\n⏸️ Keeping browser open for debugging...")
            await asyncio.sleep(300)
            
        finally:
            # Save report
            report = {
                'timestamp': datetime.now().isoformat(),
                'downloaded_count': self.downloaded_count,
                'local_files_count': len(self.local_files),
                'current_location': self.current_location
            }
            
            report_path = self.base_path / f"active_download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            print(f"\n📄 Report saved: {report_path}")
            
            if self.browser:
                print("🔒 Closing browser...")
                await self.browser.close()

async def main():
    downloader = ActiveSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Active SFTP Downloader")
    print("The browser will stay VISIBLE throughout")
    print("You can watch downloads happening in real-time")
    print("-" * 60)
    
    asyncio.run(main())