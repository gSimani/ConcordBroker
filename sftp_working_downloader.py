"""
SFTP Working Downloader - Actually clicks the green Download button
Monitors both Playwright and PC to ensure files are being saved
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

class WorkingSFTPDownloader:
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
        self.downloaded_count = 0
        self.skipped_count = 0
        self.batch_size = 4
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def check_local_file(self, folder_path, filename):
        """Check if file exists locally"""
        local_file = self.base_path / folder_path / filename
        exists = local_file.exists()
        if exists:
            size = local_file.stat().st_size
            self.log(f"    ✅ File exists locally: {filename} ({size:,} bytes)")
        else:
            self.log(f"    ❌ File missing locally: {filename}")
        return exists
        
    def monitor_download_folder(self, folder_path):
        """Monitor the local folder for new files"""
        local_folder = self.base_path / folder_path
        if local_folder.exists():
            files = list(local_folder.glob("*.txt"))
            self.log(f"📁 Local folder has {len(files)} files")
            return len(files)
        else:
            self.log(f"📁 Local folder doesn't exist yet")
            return 0
            
    async def initialize_browser(self):
        """Start visible browser"""
        self.log("🚀 Starting VISIBLE browser...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=500  # Slower to see what's happening
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(90000)
        
        self.log("✅ Browser is VISIBLE - Watch the downloads!")
        
    async def login(self):
        """Login to SFTP portal"""
        self.log("🔐 Logging in...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            self.log("✅ Login successful!")
            return True
        except:
            self.log("❌ Login failed")
            return False
            
    async def navigate_to_folder(self, path_parts):
        """Navigate to specific folder"""
        self.log(f"📁 Navigating to: {' → '.join(path_parts)}")
        
        for part in path_parts:
            self.log(f"   Entering: {part}")
            await self.page.dblclick(f'tr:has-text("{part}")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1.5)
            
    async def download_files_correctly(self, folder_path):
        """Download files by actually clicking the green Download button"""
        self.log(f"\n{'='*60}")
        self.log(f"DOWNLOADING FROM: {folder_path}")
        self.log(f"{'='*60}")
        
        # Monitor local folder before starting
        initial_count = self.monitor_download_folder(folder_path)
        
        # Navigate to folder
        path_parts = folder_path.split('/')
        await self.navigate_to_folder(path_parts)
        
        # Create local folder if needed
        local_folder = self.base_path / folder_path
        local_folder.mkdir(parents=True, exist_ok=True)
        
        # Get all file rows
        self.log("🔍 Looking for files...")
        
        # Scroll to see all files
        for _ in range(3):
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
        # Find all .txt files
        file_rows = await self.page.query_selector_all('tr:has-text(".txt")')
        self.log(f"📄 Found {len(file_rows)} .txt files")
        
        if not file_rows:
            self.log("No files to download")
            return
            
        # Process files in batches of 4
        downloaded_in_session = 0
        
        for i in range(0, len(file_rows), self.batch_size):
            batch = file_rows[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            self.log(f"\n📦 Batch {batch_num} ({len(batch)} files):")
            
            for file_row in batch:
                try:
                    # Get filename
                    first_cell = await file_row.query_selector('td:first-child')
                    filename = await first_cell.text_content() if first_cell else ""
                    filename = filename.strip()
                    
                    if not filename or not '.txt' in filename:
                        continue
                        
                    # Check if file exists locally
                    if self.check_local_file(folder_path, filename):
                        self.skipped_count += 1
                        continue
                        
                    self.log(f"   📥 Downloading: {filename}")
                    
                    # CLICK ON THE FILE ROW TO SELECT IT
                    await file_row.click()
                    await asyncio.sleep(0.5)
                    
                    # The file should now be highlighted (blue background as in screenshot)
                    self.log(f"      ✓ Selected: {filename}")
                    
                    # NOW CLICK THE GREEN DOWNLOAD BUTTON AT THE TOP
                    try:
                        # The Download button is in the toolbar at the top
                        # It's a green button with download icon
                        download_button = await self.page.query_selector('button.btn-success:has-text("Download")')
                        
                        if not download_button:
                            # Try alternative selector for the green button
                            download_button = await self.page.query_selector('button:has-text("Download")')
                            
                        if download_button:
                            # Start download
                            async with self.page.expect_download(timeout=30000) as download_info:
                                await download_button.click()
                                self.log(f"      ✓ Clicked Download button")
                                
                            download = await download_info.value
                            
                            # Save to correct location
                            save_path = local_folder / filename
                            await download.save_as(str(save_path))
                            
                            self.downloaded_count += 1
                            downloaded_in_session += 1
                            
                            self.log(f"      ✅ SAVED: {filename} to {save_path}")
                            
                            # Verify file was actually saved
                            if save_path.exists():
                                size = save_path.stat().st_size
                                self.log(f"      ✅ VERIFIED: File saved ({size:,} bytes)")
                            else:
                                self.log(f"      ❌ WARNING: File not found after download!")
                                
                        else:
                            self.log(f"      ❌ Could not find Download button!")
                            
                    except Exception as e:
                        self.log(f"      ❌ Download failed: {str(e)[:100]}")
                        
                    await asyncio.sleep(1)  # Pause between downloads
                    
                except Exception as e:
                    self.log(f"   ❌ Error processing file: {str(e)[:100]}")
                    
            # Monitor folder after each batch
            current_count = self.monitor_download_folder(folder_path)
            self.log(f"\n📊 Progress: {current_count - initial_count} new files downloaded to PC")
            
            # Pause between batches
            if i + self.batch_size < len(file_rows):
                self.log("⏸️ Pausing between batches...")
                await asyncio.sleep(3)
                
        # Final monitoring
        final_count = self.monitor_download_folder(folder_path)
        self.log(f"\n✅ FOLDER COMPLETE: {final_count - initial_count} files downloaded")
        self.log(f"📁 Total files in {folder_path}: {final_count}")
        
        # Return to root for next folder
        self.log("⬆️ Returning to root...")
        for _ in range(len(path_parts)):
            await self.page.dblclick('tr:has-text("..")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("WORKING SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE")
        print("📥 Actually clicks the green Download button")
        print("📊 Monitors both Playwright and PC")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login")
                await asyncio.sleep(30)
                return
                
            # Download from specific folders
            folders_to_download = [
                "doc/fic/2014",  # Start with 2014 to test
                "doc/fic/2015",
                "doc/fic/2016",
                "doc/DHE",
                "doc/AG"
            ]
            
            for folder in folders_to_download:
                await self.download_files_correctly(folder)
                
                # Show overall progress
                self.log(f"\n📊 OVERALL: {self.downloaded_count} downloaded, {self.skipped_count} skipped")
                
            # Final summary
            print("\n" + "="*60)
            print("DOWNLOAD COMPLETE")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"⏭️ Skipped: {self.skipped_count} files")
            
            # Keep browser open
            self.log("\n🔄 Browser stays open for manual downloads")
            self.log("Press Ctrl+C to close")
            
            while True:
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            self.log("\n⏹️ Stopped by user")
            
        except Exception as e:
            self.log(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            self.log("\n⏸️ Browser stays open for debugging...")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                self.log("🔒 Closing browser...")
                await self.browser.close()

async def main():
    downloader = WorkingSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Working SFTP Downloader")
    print("This will:")
    print("  ✅ Actually click the green Download button")
    print("  📺 Keep browser visible")
    print("  📊 Monitor both Playwright and your PC")
    print("  📁 Show files appearing in folders")
    print("-" * 60)
    
    asyncio.run(main())