"""
Playwright Targeted SFTP Downloader
Downloads only missing files, keeps browser visible, avoids duplicates
Based on mapping: 14,201 remote files, 6,359 local files, 9,713 missing
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

class TargetedDownloader:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local base path
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
        # Track progress
        self.local_files = set()
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.current_location = ""
        
        # Priority folders to download from (based on missing files)
        self.priority_folders = [
            "doc/fic",  # Fictitious names - many missing
            "doc/FLR",  # Florida records - many missing
            "doc/gen",  # General records - many missing
            "doc/DHE",  # DHE records - small folder
            "doc/Quarterly",  # Quarterly reports
            "doc/AG",   # AG records - 1 file
            "doc/cornp" # Non-profit - 1 file
        ]
        
    def scan_local_files(self):
        """Build set of existing local files to avoid duplicates"""
        print("\n" + "="*60)
        print("📂 SCANNING LOCAL FILES TO AVOID DUPLICATES")
        print("="*60)
        
        total_count = 0
        total_size = 0
        
        # Scan all files recursively
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                self.local_files.add(rel_path_str)
                total_count += 1
                total_size += full_path.stat().st_size
                
        print(f"✅ Found {total_count:,} existing files ({total_size/(1024**3):.2f} GB)")
        
        # Show breakdown by main folders
        folder_counts = {}
        for file_path in self.local_files:
            parts = file_path.split('/')
            if len(parts) > 1:
                folder = f"{parts[0]}/{parts[1]}" if len(parts) > 2 else parts[0]
                folder_counts[folder] = folder_counts.get(folder, 0) + 1
                
        print("\n📁 Existing files by folder:")
        for folder, count in sorted(folder_counts.items()):
            print(f"   {folder}: {count:,} files")
            
    async def initialize_browser(self):
        """Start VISIBLE browser for monitoring"""
        print("\n" + "="*60)
        print("🚀 STARTING VISIBLE BROWSER")
        print("="*60)
        print("Browser will stay VISIBLE so you can watch downloads")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # KEEP VISIBLE
            args=['--start-maximized'],
            slow_mo=200  # Slow enough to see actions
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        print("✅ Browser window is OPEN and VISIBLE")
        print("📺 You can watch the download progress!")
        
    async def login(self):
        """Login to SFTP portal"""
        print("\n🔐 Logging into SFTP portal...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Fill credentials
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        print("   ✓ Credentials entered")
        
        # Click login
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Verify login
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            print("✅ Login successful!")
            self.current_location = "root"
            
            # Take screenshot
            screenshot = self.base_path / f"targeted_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(screenshot))
            
            return True
        except:
            print("❌ Login failed")
            return False
            
    async def navigate_to_folder(self, folder_path):
        """Navigate to a specific folder from root"""
        print(f"\n📁 Navigating to: {folder_path}")
        
        # Always start from root
        if self.current_location != "root":
            print("   ⬆️ Returning to root first...")
            while self.current_location != "root":
                try:
                    await self.page.dblclick('tr:has-text("..")', timeout=3000)
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(1)
                    
                    # Check if we're at root
                    if not await self.page.query_selector('tr:has-text("..")'):
                        self.current_location = "root"
                        break
                except:
                    self.current_location = "root"
                    break
                    
        # Navigate to target folder
        path_parts = folder_path.split('/')
        for i, part in enumerate(path_parts):
            print(f"   📂 Entering: {part}")
            
            try:
                # Double-click to enter folder
                await self.page.dblclick(f'tr:has-text("{part}")', timeout=5000)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                self.current_location = '/'.join(path_parts[:i+1])
                
            except Exception as e:
                print(f"   ❌ Could not enter {part}: {e}")
                return False
                
        print(f"   ✅ Now in: {folder_path}")
        return True
        
    async def get_files_in_current_folder(self):
        """Get list of files in current folder"""
        files = []
        
        # Scroll to load all files
        for _ in range(5):
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
        # Get all rows
        rows = await self.page.query_selector_all('tr')
        
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 4:
                name_elem = cells[0]
                type_elem = cells[1]
                size_elem = cells[3]
                
                name = await name_elem.text_content() if name_elem else ""
                type_text = await type_elem.text_content() if type_elem else ""
                size = await size_elem.text_content() if size_elem else ""
                
                name = name.strip()
                
                # Only get files, not folders
                if name and name not in ['..', 'WELCOME.TXT']:
                    is_file = "." in name or type_text != "Folder"
                    if is_file:
                        files.append({
                            'name': name,
                            'size': size.strip()
                        })
                        
        return files
        
    async def download_file_if_missing(self, filename, folder_path):
        """Download a file only if we don't have it"""
        # Check if file exists locally
        local_path = f"{folder_path}/{filename}" if folder_path else filename
        
        if local_path in self.local_files:
            self.skipped_count += 1
            return False  # Skip - already have it
            
        # Create local directory if needed
        if folder_path:
            local_dir = self.base_path / folder_path
            local_dir.mkdir(parents=True, exist_ok=True)
        else:
            local_dir = self.base_path
            
        local_file = local_dir / filename
        
        # Double-check file doesn't exist
        if local_file.exists():
            self.skipped_count += 1
            self.local_files.add(local_path)  # Add to set
            return False
            
        # Download the file
        try:
            print(f"      📥 Downloading: {filename}")
            
            # Click on file to select it
            await self.page.click(f'tr:has-text("{filename}")')
            await asyncio.sleep(0.3)
            
            # Click download button
            async with self.page.expect_download(timeout=120000) as download_info:
                await self.page.click('button:has-text("Download")')
                
            download = await download_info.value
            
            # Save file
            await download.save_as(str(local_file))
            
            self.downloaded_count += 1
            self.local_files.add(local_path)  # Add to set to avoid re-download
            
            print(f"      ✅ Saved: {local_file.name}")
            return True
            
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            self.failed_count += 1
            return False
            
    async def download_folder_contents(self, folder_path):
        """Download all missing files from a folder"""
        print(f"\n" + "="*60)
        print(f"📂 PROCESSING FOLDER: {folder_path}")
        print("="*60)
        
        # Navigate to folder
        if not await self.navigate_to_folder(folder_path):
            print(f"❌ Could not navigate to {folder_path}")
            return
            
        # Get files in folder
        files = await self.get_files_in_current_folder()
        
        if not files:
            print("   📭 No files in this folder")
            return
            
        print(f"   📊 Found {len(files)} files")
        
        # Download missing files
        new_downloads = 0
        for file in files:
            if await self.download_file_if_missing(file['name'], folder_path):
                new_downloads += 1
                await asyncio.sleep(0.5)  # Small delay between downloads
                
                # Show progress every 10 downloads
                if new_downloads % 10 == 0:
                    print(f"   📊 Progress: {new_downloads} new downloads in this folder")
                    
        print(f"   ✅ Folder complete: {new_downloads} downloaded, {len(files)-new_downloads} skipped")
        
    async def download_all_missing(self):
        """Main download process for all missing files"""
        print("\n" + "="*60)
        print("🎯 TARGETED DOWNLOAD OF MISSING FILES")
        print("="*60)
        print("Downloading ONLY files we don't have")
        print("Skipping all duplicates")
        
        # Process each priority folder
        for folder in self.priority_folders:
            await self.download_folder_contents(folder)
            
            # Also check subfolders for some directories
            if folder == "doc/fic":
                # Download from year folders
                for year in range(2011, 2022):
                    await self.download_folder_contents(f"doc/fic/{year}")
                    
            elif folder == "doc/FLR":
                # Download from FLR subfolders
                for subfolder in ["DEBTORS", "EVENTS", "FILINGS", "SECURED"]:
                    await self.download_folder_contents(f"doc/FLR/{subfolder}")
                    
            elif folder == "doc/gen":
                # Download from gen subfolders
                for subfolder in ["Events", "Filings"]:
                    await self.download_folder_contents(f"doc/gen/{subfolder}")
                    
            # Show running totals
            print(f"\n📊 Running totals: {self.downloaded_count} downloaded, {self.skipped_count} skipped, {self.failed_count} failed")
            
    async def show_live_status(self):
        """Show live download status"""
        start_time = time.time()
        
        while True:
            elapsed = int(time.time() - start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            
            status = (f"\r⏱️ {mins:02d}:{secs:02d} | "
                     f"✅ Downloaded: {self.downloaded_count} | "
                     f"⏭️ Skipped: {self.skipped_count} | "
                     f"❌ Failed: {self.failed_count} | "
                     f"📍 Location: {self.current_location}")
            
            print(status, end="")
            await asyncio.sleep(5)
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("TARGETED SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE - Watch downloads happen!")
        print("📥 Downloads ONLY missing files - No duplicates!")
        print("-"*60)
        
        try:
            # Scan existing files
            self.scan_local_files()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                print("❌ Login failed")
                await asyncio.sleep(60)
                return
                
            # Download all missing files
            await self.download_all_missing()
            
            # Final summary
            print("\n" + "="*60)
            print("✅ DOWNLOAD COMPLETE")
            print("="*60)
            print(f"📥 New files downloaded: {self.downloaded_count}")
            print(f"⏭️ Duplicates skipped: {self.skipped_count}")
            print(f"❌ Failed downloads: {self.failed_count}")
            print(f"📁 Total local files now: {len(self.local_files):,}")
            
            # Save summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'downloaded': self.downloaded_count,
                'skipped': self.skipped_count,
                'failed': self.failed_count,
                'total_local_files': len(self.local_files)
            }
            
            summary_path = self.base_path / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
                
            print(f"\n📄 Summary saved: {summary_path}")
            
            # Keep browser open for manual operations
            print("\n" + "="*60)
            print("🔄 BROWSER STAYS OPEN")
            print("="*60)
            print("You can manually browse and download more files")
            print("Press Ctrl+C to close when done")
            
            # Show live status
            await self.show_live_status()
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            print("\n⏸️ Keeping browser open for debugging...")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                print("\n🔒 Closing browser...")
                await self.browser.close()
                
            print("✅ Session complete!")

async def main():
    downloader = TargetedDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Targeted SFTP Downloader")
    print("This will:")
    print("  ✅ Download ONLY missing files (no duplicates)")
    print("  📺 Keep browser VISIBLE so you can watch")
    print("  📊 Show real-time progress")
    print("  📁 Create folders as needed")
    print("-" * 60)
    
    asyncio.run(main())