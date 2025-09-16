"""
SFTP Single File Downloader - Downloads one file at a time
Processes ALL files in a folder before moving to next folder
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

class SingleFileSFTPDownloader:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public" 
        self.password = "PubAccess1845!"
        
        # Local base path - matches SFTP structure
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        self.context = None
        
        # Track progress
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "DOWNLOAD": "📥", "INFO": "ℹ️", "FOLDER": "📁"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    async def initialize_browser(self):
        """Start visible browser with download handling"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=200  # Slightly faster but still visible
        )
        
        # Set download directory
        downloads_path = self.base_path / "temp_downloads"
        downloads_path.mkdir(exist_ok=True)
        
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)
        
        self.log("Browser is VISIBLE - Watch single file downloads!", "SUCCESS")
        
    async def login(self):
        """Login to SFTP portal"""
        self.log("Logging into SFTP portal...", "INFO")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            self.log("Login successful!", "SUCCESS")
            return True
        except:
            self.log("Login failed", "ERROR")
            return False
            
    async def navigate_to_folder(self, path_parts):
        """Navigate to specific folder"""
        self.log(f"Navigating to: {' → '.join(path_parts)}", "FOLDER")
        
        for part in path_parts:
            self.log(f"   Entering folder: {part}", "INFO")
            await self.page.dblclick(f'tr:has-text("{part}")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
    async def return_to_root(self, depth):
        """Return to root directory"""
        self.log(f"Returning to root (going up {depth} levels)...", "INFO")
        
        for _ in range(depth):
            try:
                # Click on ".." to go up one level
                await self.page.dblclick('tr:has-text("..")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(0.5)
            except:
                # If ".." doesn't work, we might already be at root
                break
                
    async def click_download_button(self):
        """Click the Download button/element"""
        # Try multiple selectors for the Download element
        selectors = [
            'text=Download',
            ':has-text("Download")',
            'a:has-text("Download")',
            'input[value*="Download" i]',
            '[role="button"]:has-text("Download")',
            '[title*="Download" i]',
            '[aria-label*="Download" i]',
            '.button:has-text("Download")',
            '.btn:has-text("Download")',
            '*:has-text("Download")'
        ]
        
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    return True
            except:
                continue
                
        # If selectors don't work, try JavaScript
        clicked = await self.page.evaluate("""
            () => {
                const allElements = document.getElementsByTagName('*');
                for (let el of allElements) {
                    const text = el.textContent?.trim() || '';
                    if (text === 'Download' && el.offsetParent !== null) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        
        return clicked
        
    async def download_single_file(self, filename, local_folder):
        """Download a single file"""
        try:
            # Click on the file to select it
            await self.page.click(f'tr:has-text("{filename}")')
            await asyncio.sleep(0.5)
            
            # Click Download button
            async with self.page.expect_download(timeout=30000) as download_info:
                if await self.click_download_button():
                    download = await download_info.value
                    
                    # Save to correct location
                    save_path = local_folder / filename
                    await download.save_as(str(save_path))
                    
                    if save_path.exists():
                        size = save_path.stat().st_size
                        self.log(f"✅ Downloaded: {filename} ({size:,} bytes)", "SUCCESS")
                        return True
                    else:
                        self.log(f"❌ File not saved: {filename}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Could not click Download for: {filename}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Error downloading {filename}: {str(e)[:100]}", "ERROR")
            return False
            
    async def download_all_files_in_folder(self, folder_path):
        """Download ALL files in a folder, one at a time"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"DOWNLOADING ALL FILES FROM: {folder_path}", "FOLDER")
        self.log(f"{'='*60}", "INFO")
        
        # Navigate to folder
        path_parts = folder_path.split('/')
        await self.navigate_to_folder(path_parts)
        
        # Create local folder
        local_folder = self.base_path / folder_path
        local_folder.mkdir(parents=True, exist_ok=True)
        
        self.log(f"Local folder: {local_folder}", "FOLDER")
        
        # Get list of existing files
        existing_files = {f.name for f in local_folder.glob("*.txt")}
        self.log(f"Already have {len(existing_files)} files locally", "INFO")
        
        # Scroll to load all files
        self.log("Loading all files in folder...", "INFO")
        last_count = 0
        while True:
            # Count current files
            file_rows = await self.page.query_selector_all('tr:has(td:has-text(".txt"))')
            current_count = len(file_rows)
            
            if current_count == last_count:
                break  # No new files loaded
                
            last_count = current_count
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
        # Get all filenames
        self.log(f"Found {len(file_rows)} total files in folder", "INFO")
        
        # Process each file ONE AT A TIME
        downloaded_in_folder = 0
        skipped_in_folder = 0
        failed_in_folder = 0
        
        for i, row in enumerate(file_rows, 1):
            try:
                # Get filename
                first_cell = await row.query_selector('td:first-child')
                if not first_cell:
                    continue
                    
                filename = await first_cell.text_content()
                filename = filename.strip()
                
                if not filename or not '.txt' in filename:
                    continue
                    
                # Progress indicator
                self.log(f"\n[{i}/{len(file_rows)}] Processing: {filename}", "INFO")
                
                # Check if file exists
                if filename in existing_files:
                    self.log(f"   ⏭️ Skipping (already exists): {filename}", "INFO")
                    self.skipped_count += 1
                    skipped_in_folder += 1
                    continue
                    
                # Download the file
                self.log(f"   📥 Downloading: {filename}", "DOWNLOAD")
                
                if await self.download_single_file(filename, local_folder):
                    self.downloaded_count += 1
                    downloaded_in_folder += 1
                    existing_files.add(filename)  # Add to set so we don't re-download
                else:
                    self.failed_count += 1
                    failed_in_folder += 1
                    
                # Small delay between downloads
                await asyncio.sleep(0.5)
                
                # Show progress every 10 files
                if i % 10 == 0:
                    self.log(f"\n📊 Progress: {i}/{len(file_rows)} files processed", "INFO")
                    self.log(f"   Downloaded: {downloaded_in_folder}, Skipped: {skipped_in_folder}, Failed: {failed_in_folder}", "INFO")
                    
            except Exception as e:
                self.log(f"❌ Error processing file {i}: {str(e)[:100]}", "ERROR")
                failed_in_folder += 1
                continue
                
        # Summary for this folder
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"✅ FOLDER COMPLETE: {folder_path}", "SUCCESS")
        self.log(f"   Downloaded: {downloaded_in_folder} files", "SUCCESS")
        self.log(f"   Skipped: {skipped_in_folder} files", "INFO")
        self.log(f"   Failed: {failed_in_folder} files", "ERROR" if failed_in_folder > 0 else "INFO")
        self.log(f"   Total in folder: {len(list(local_folder.glob('*.txt')))} files", "FOLDER")
        self.log(f"{'='*60}", "INFO")
        
        # Return to root for next folder
        await self.return_to_root(len(path_parts))
        
    async def run(self):
        """Main execution"""
        print("="*60)
        print("SINGLE FILE SFTP DOWNLOADER")
        print("="*60)
        print("📥 Downloads one file at a time")
        print("📁 Processes ALL files in each folder")
        print("✅ Continues until folder is complete")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login", "ERROR")
                await asyncio.sleep(30)
                return
                
            # Folders to download - will process ALL files in each
            folders_to_download = [
                "doc/fic/2014",
                "doc/fic/2015", 
                "doc/fic/2016",
                "doc/fic/2017",
                "doc/fic/2018",
                "doc/DHE",
                "doc/AG",
                "doc/FLR/DEBTORS",
                "doc/gen/Events"
            ]
            
            # Process each folder completely
            for folder in folders_to_download:
                await self.download_all_files_in_folder(folder)
                
                # Overall progress
                self.log(f"\n📊 OVERALL PROGRESS:", "INFO")
                self.log(f"   Total Downloaded: {self.downloaded_count}", "SUCCESS")
                self.log(f"   Total Skipped: {self.skipped_count}", "INFO")
                self.log(f"   Total Failed: {self.failed_count}", "ERROR" if self.failed_count > 0 else "INFO")
                
            # Final summary
            print("\n" + "="*60)
            print("DOWNLOAD SESSION COMPLETE")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"⏭️ Skipped: {self.skipped_count} files (already existed)")
            print(f"❌ Failed: {self.failed_count} files")
            print(f"📁 Files saved to: {self.base_path}")
            
            # Keep browser open
            self.log("\n🔄 Browser stays open for manual operations", "INFO")
            self.log("Press Ctrl+C to close", "INFO")
            
            while True:
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            self.log("\n⏹️ Stopped by user", "INFO")
            
        except Exception as e:
            self.log(f"\n❌ Error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            
            self.log("\n⏸️ Browser stays open for debugging...", "INFO")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                self.log("Closing browser...", "INFO")
                await self.browser.close()

async def main():
    downloader = SingleFileSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Single File SFTP Downloader")
    print("This will:")
    print("  📥 Download ONE file at a time (not batches)")
    print("  📁 Process ALL files in a folder before moving on")
    print("  ✅ Continue until each folder is complete")
    print("  📊 Show progress for each folder")
    print("-" * 60)
    
    asyncio.run(main())