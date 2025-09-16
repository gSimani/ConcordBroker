"""
SFTP Correct Downloader - Uses the actual Download button location
Downloads files to the correct folder structure
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
import shutil

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CorrectSFTPDownloader:
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
        self.batch_size = 4  # Download 4 files at once
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "DOWNLOAD": "📥", "INFO": "ℹ️", "BUTTON": "🔘"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    async def handle_timeout_popup(self):
        """Handle session timeout popup if it appears"""
        try:
            # Check if timeout popup is visible
            continue_button = await self.page.query_selector('button:has-text("Continue")', state='visible', timeout=1000)
            if continue_button:
                self.log("⏰ Session timeout detected - clicking Continue", "INFO")
                await continue_button.click()
                await asyncio.sleep(1)
                return True
        except:
            pass
        return False
        
    async def initialize_browser(self):
        """Start visible browser with download handling"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=300  # Slow enough to see actions
        )
        
        # Create context with download handling
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(90000)
        
        # Set up handler for timeout popup
        self.page.on("dialog", lambda dialog: dialog.accept())
        
        self.log("Browser is VISIBLE - Watch the downloads!", "SUCCESS")
        
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
        self.log(f"Navigating to: {' → '.join(path_parts)}", "INFO")
        
        for part in path_parts:
            self.log(f"   Entering: {part}", "INFO")
            await self.page.dblclick(f'tr:has-text("{part}")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1.5)
            
            # Check for timeout popup
            await self.handle_timeout_popup()
            
    async def click_download_button(self):
        """Click the Download button in the toolbar"""
        self.log("🔘 Looking for Download button in toolbar...", "BUTTON")
        
        # Based on the screenshot, the Download button is in the toolbar between Upload and Delete
        # It has a download icon and text "Download"
        
        # Method 1: Try finding by the visible text and icon
        try:
            # Look for the Download button specifically
            # It appears to be a button with class that includes download functionality
            download_button = await self.page.query_selector('button:has-text("Download"):visible')
            
            if download_button:
                self.log("Found Download button by text", "BUTTON")
                await download_button.click()
                self.log("✅ Clicked Download button!", "SUCCESS")
                return True
        except Exception as e:
            self.log(f"Text search failed: {str(e)[:50]}", "ERROR")
            
        # Method 2: Try finding by position in toolbar
        try:
            # The Download button appears to be after Upload button
            all_buttons = await self.page.query_selector_all('button:visible')
            
            for i, button in enumerate(all_buttons):
                try:
                    # Get button text or title
                    text = await button.text_content() or ""
                    
                    # Check innerHTML for download icon
                    inner_html = await button.inner_html()
                    
                    if "download" in text.lower() or "download" in inner_html.lower():
                        self.log(f"Found Download button at position {i}", "BUTTON")
                        await button.click()
                        self.log("✅ Clicked Download button by position!", "SUCCESS")
                        return True
                except:
                    continue
                    
        except Exception as e:
            self.log(f"Position search failed: {str(e)[:50]}", "ERROR")
            
        # Method 3: Try using nth-child based on toolbar position
        try:
            # Based on screenshot, Download appears to be around the 7th button in toolbar
            toolbar_button = await self.page.query_selector('div.toolbar button:nth-child(7)')
            if toolbar_button:
                await toolbar_button.click()
                self.log("✅ Clicked Download button by toolbar position!", "SUCCESS")
                return True
        except:
            pass
            
        # Method 4: Use JavaScript to find and click
        try:
            clicked = await self.page.evaluate("""
                () => {
                    // Find all buttons
                    const buttons = document.querySelectorAll('button');
                    
                    for (let button of buttons) {
                        // Check button text and icon
                        const text = button.textContent || '';
                        const html = button.innerHTML || '';
                        
                        // Look for Download text or download icon class
                        if (text.includes('Download') || 
                            html.includes('fa-download') || 
                            html.includes('icon-download') ||
                            button.className.includes('download')) {
                            
                            // Make sure it's visible
                            if (button.offsetParent !== null) {
                                button.click();
                                return true;
                            }
                        }
                    }
                    
                    // If not found by text, look for button with download icon
                    const icons = document.querySelectorAll('i.fa-download, span.icon-download');
                    for (let icon of icons) {
                        const button = icon.closest('button');
                        if (button && button.offsetParent !== null) {
                            button.click();
                            return true;
                        }
                    }
                    
                    return false;
                }
            """)
            
            if clicked:
                self.log("✅ Clicked Download button via JavaScript!", "SUCCESS")
                return True
                
        except Exception as e:
            self.log(f"JavaScript method failed: {str(e)[:50]}", "ERROR")
            
        self.log("❌ Could not find Download button with any method!", "ERROR")
        return False
            
    async def download_files_batch(self, folder_path):
        """Download files in batches with proper folder structure"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"DOWNLOADING FROM: {folder_path}", "INFO")
        self.log(f"{'='*60}", "INFO")
        
        # Navigate to folder
        path_parts = folder_path.split('/')
        await self.navigate_to_folder(path_parts)
        
        # Create local folder structure matching SFTP
        local_folder = self.base_path / folder_path
        local_folder.mkdir(parents=True, exist_ok=True)
        
        self.log(f"📁 Local folder: {local_folder}", "INFO")
        
        # Count existing files
        existing_files = list(local_folder.glob("*.txt"))
        self.log(f"📁 Already have {len(existing_files)} files locally", "INFO")
        
        # Scroll to see all files
        self.log("Scrolling to load all files...", "INFO")
        for _ in range(3):
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
        # Get all file rows
        file_rows = await self.page.query_selector_all('tr:has(td:has-text(".txt"))')
        self.log(f"Found {len(file_rows)} .txt files in folder", "INFO")
        
        if not file_rows:
            self.log("No files to download", "INFO")
            return
            
        # Process files in batches
        downloaded_in_session = 0
        
        for i in range(0, len(file_rows), self.batch_size):
            batch = file_rows[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(file_rows) + self.batch_size - 1) // self.batch_size
            
            self.log(f"\n📦 Batch {batch_num}/{total_batches} - Processing {len(batch)} files:", "INFO")
            
            # Check for timeout popup before batch
            await self.handle_timeout_popup()
            
            # Collect filenames in this batch
            batch_filenames = []
            files_to_download = []
            
            for row in batch:
                try:
                    first_cell = await row.query_selector('td:first-child')
                    filename = await first_cell.text_content() if first_cell else ""
                    filename = filename.strip()
                    
                    if filename and '.txt' in filename:
                        # Check if file already exists locally
                        local_file = local_folder / filename
                        if local_file.exists():
                            self.log(f"   ⏭️ Skipping (exists): {filename}", "INFO")
                            self.skipped_count += 1
                        else:
                            batch_filenames.append(filename)
                            files_to_download.append(row)
                except:
                    continue
                    
            if not files_to_download:
                self.log("   All files in batch already exist, skipping", "INFO")
                continue
                
            # MULTI-SELECT: Click first file normally, then Ctrl+Click the rest
            try:
                self.log(f"   🖱️ Multi-selecting {len(files_to_download)} files:", "INFO")
                
                # Clear any previous selection first
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(0.2)
                
                for idx, (row, filename) in enumerate(zip(files_to_download, batch_filenames)):
                    if idx == 0:
                        # First file - normal click to select
                        await row.click()
                        self.log(f"      • Selected: {filename}", "INFO")
                    else:
                        # Additional files - Ctrl+Click to multi-select
                        await row.click(modifiers=['Control'])
                        self.log(f"      • Ctrl+Selected: {filename}", "INFO")
                    
                    await asyncio.sleep(0.2)  # Small delay between selections
                    
                # All files are now selected (should be highlighted)
                self.log(f"   ✓ {len(files_to_download)} files selected", "SUCCESS")
                await asyncio.sleep(0.5)
                
                # Now click the Download button
                self.log("   📥 Clicking Download button...", "DOWNLOAD")
                
                # Set up download handling before clicking
                async with self.page.expect_download(timeout=30000) as download_info:
                    # Click the Download button
                    if await self.click_download_button():
                        self.log("   ⏳ Waiting for download to start...", "INFO")
                        
                        try:
                            download = await download_info.value
                            
                            # Save to correct location
                            if batch_filenames:
                                save_path = local_folder / batch_filenames[0]
                                await download.save_as(str(save_path))
                                
                                self.downloaded_count += 1
                                downloaded_in_session += 1
                                
                                if save_path.exists():
                                    size = save_path.stat().st_size
                                    self.log(f"      ✅ Downloaded: {batch_filenames[0]} ({size:,} bytes)", "SUCCESS")
                                    self.log(f"      📁 Saved to: {save_path}", "SUCCESS")
                                    
                        except Exception as e:
                            self.log(f"   ⚠️ Download handling error: {str(e)[:100]}", "ERROR")
                            
                    else:
                        self.log("   ❌ Could not click Download button!", "ERROR")
                        
                        # Manual fallback message
                        self.log("   📸 PLEASE CLICK THE DOWNLOAD BUTTON MANUALLY", "ERROR")
                        self.log("   The Download button is in the toolbar (circled in green)", "INFO")
                        self.log("   Waiting 10 seconds for manual download...", "INFO")
                        await asyncio.sleep(10)
                        
            except Exception as e:
                self.log(f"   ❌ Batch processing error: {str(e)[:100]}", "ERROR")
                
            # Show progress
            current_files = len(list(local_folder.glob("*.txt")))
            new_files = current_files - len(existing_files)
            self.log(f"\n📊 Folder progress: {new_files} new files in {local_folder.name}", "INFO")
            
            # Check for timeout popup after batch
            await self.handle_timeout_popup()
            
            # Pause between batches
            if i + self.batch_size < len(file_rows):
                self.log("⏸️ Pausing before next batch...", "INFO")
                await asyncio.sleep(3)
                
        # Final count for this folder
        final_files = len(list(local_folder.glob("*.txt")))
        total_downloaded = final_files - len(existing_files)
        self.log(f"\n✅ FOLDER COMPLETE: {total_downloaded} new files downloaded", "SUCCESS")
        self.log(f"📁 Total files in {local_folder}: {final_files}", "INFO")
        
        # Return to root for next folder
        self.log("⬆️ Returning to root...", "INFO")
        for _ in range(len(path_parts)):
            await self.page.dblclick('tr:has-text("..")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
            # Check for timeout popup
            await self.handle_timeout_popup()
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("CORRECT SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE")
        print("🔘 Uses correct Download button location")
        print("📁 Downloads to proper folder structure")
        print("⏰ Handles session timeout popups")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login", "ERROR")
                await asyncio.sleep(30)
                return
                
            # Download from folders - maintaining SFTP structure
            folders_to_download = [
                "doc/fic/2014",  # Will save to TEMP/DATABASE/doc/fic/2014/
                "doc/fic/2015",  # Will save to TEMP/DATABASE/doc/fic/2015/
                "doc/fic/2016",  # Will save to TEMP/DATABASE/doc/fic/2016/
                "doc/DHE",       # Will save to TEMP/DATABASE/doc/DHE/
                "doc/AG",        # Will save to TEMP/DATABASE/doc/AG/
            ]
            
            for folder in folders_to_download:
                await self.download_files_batch(folder)
                
                # Show overall progress
                self.log(f"\n📊 OVERALL PROGRESS: {self.downloaded_count} downloaded, {self.skipped_count} skipped", "INFO")
                
                # Check for timeout popup between folders
                await self.handle_timeout_popup()
                
            # Final summary
            print("\n" + "="*60)
            print("DOWNLOAD SESSION COMPLETE")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"⏭️ Skipped (already exist): {self.skipped_count} files")
            print(f"📁 Files saved to: {self.base_path}")
            
            # Show folder structure
            print("\n📁 Folder Structure:")
            for folder in folders_to_download:
                folder_path = self.base_path / folder
                if folder_path.exists():
                    file_count = len(list(folder_path.glob("*.txt")))
                    print(f"   {folder}: {file_count} files")
            
            # Keep browser open
            self.log("\n🔄 Browser stays open for manual operations", "INFO")
            self.log("You can continue downloading other folders manually", "INFO")
            self.log("Press Ctrl+C to close", "INFO")
            
            # Monitor for timeout popups while idle
            while True:
                await self.handle_timeout_popup()
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
    downloader = CorrectSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Correct SFTP Downloader")
    print("This will:")
    print("  🔘 Click the Download button in the toolbar")
    print("  📁 Save files to correct folder structure:")
    print("     C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE\\")
    print("     └── doc/")
    print("         ├── fic/2014/")
    print("         ├── fic/2015/")
    print("         └── DHE/")
    print("  ⏰ Handle session timeouts")
    print("-" * 60)
    
    asyncio.run(main())