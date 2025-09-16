"""
SFTP Force Download - Uses multiple methods to find and click Download button
Including coordinate-based clicking and visual inspection
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

class ForceSFTPDownloader:
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
        """Start visible browser"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=500  # Slower to see actions clearly
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
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
            
    async def find_and_click_download_button(self):
        """Try multiple methods to find and click the Download button"""
        self.log("🔍 Looking for Download button using multiple methods...", "BUTTON")
        
        # Method 1: Look for any button containing "Download" text
        try:
            buttons = await self.page.query_selector_all('button')
            for button in buttons:
                text = await button.text_content()
                if text and 'Download' in text:
                    self.log(f"Found button with text: '{text}'", "BUTTON")
                    await button.click(force=True)
                    self.log("✅ Clicked Download button (Method 1: text search)", "SUCCESS")
                    return True
        except Exception as e:
            self.log(f"Method 1 failed: {str(e)[:50]}", "ERROR")
            
        # Method 2: Look for button by class names (common for download buttons)
        try:
            selectors = [
                'button.btn-success',  # Green button
                'button.btn-primary',  # Primary button
                'button[class*="download"]',  # Any button with download in class
                'button[title*="Download"]',  # Button with Download in title
                'button[aria-label*="Download"]',  # Button with Download in aria-label
            ]
            
            for selector in selectors:
                button = await self.page.query_selector(selector)
                if button:
                    # Check if visible
                    is_visible = await button.is_visible()
                    if is_visible:
                        self.log(f"Found button with selector: {selector}", "BUTTON")
                        await button.click(force=True)
                        self.log(f"✅ Clicked Download button (Method 2: {selector})", "SUCCESS")
                        return True
        except Exception as e:
            self.log(f"Method 2 failed: {str(e)[:50]}", "ERROR")
            
        # Method 3: Look in toolbar/header area (common location for action buttons)
        try:
            toolbar_selectors = [
                '.toolbar button:has-text("Download")',
                '.header button:has-text("Download")',
                '.actions button:has-text("Download")',
                'div[class*="toolbar"] button:has-text("Download")',
                'div[class*="header"] button:has-text("Download")',
                'div[class*="actions"] button:has-text("Download")',
            ]
            
            for selector in toolbar_selectors:
                button = await self.page.query_selector(selector)
                if button:
                    self.log(f"Found button in toolbar: {selector}", "BUTTON")
                    await button.click(force=True)
                    self.log(f"✅ Clicked Download button (Method 3: toolbar)", "SUCCESS")
                    return True
        except Exception as e:
            self.log(f"Method 3 failed: {str(e)[:50]}", "ERROR")
            
        # Method 4: Click by coordinates (top area where Download button typically is)
        try:
            # Get page viewport
            viewport = self.page.viewport_size
            if viewport:
                # Try clicking in top toolbar area (typically where Download is)
                # Try multiple positions across the top
                positions = [
                    (viewport['width'] // 2, 100),  # Center top
                    (viewport['width'] // 3, 100),  # Left third
                    (viewport['width'] * 2 // 3, 100),  # Right third
                    (200, 100),  # Specific left position
                    (400, 100),  # Another position
                ]
                
                for x, y in positions:
                    self.log(f"Trying coordinate click at ({x}, {y})", "BUTTON")
                    await self.page.mouse.click(x, y)
                    await asyncio.sleep(0.5)
                    
                    # Check if download started
                    try:
                        # If a download dialog appears, we found it
                        download_started = await self.page.wait_for_event('download', timeout=1000)
                        if download_started:
                            self.log(f"✅ Download started after clicking at ({x}, {y})", "SUCCESS")
                            return True
                    except:
                        continue
        except Exception as e:
            self.log(f"Method 4 failed: {str(e)[:50]}", "ERROR")
            
        # Method 5: Use keyboard shortcut (sometimes Download is bound to a key)
        try:
            await self.page.keyboard.press('Control+d')  # Common download shortcut
            await asyncio.sleep(0.5)
            self.log("Tried Ctrl+D shortcut", "BUTTON")
        except:
            pass
            
        # Method 6: Get ALL buttons and show their text for debugging
        try:
            self.log("📋 Listing ALL visible buttons on page:", "BUTTON")
            all_buttons = await self.page.query_selector_all('button')
            for i, button in enumerate(all_buttons[:20]):  # First 20 buttons
                try:
                    text = await button.text_content()
                    is_visible = await button.is_visible()
                    if is_visible and text:
                        self.log(f"   Button {i}: '{text.strip()}'", "INFO")
                        
                        # If we find one that looks like Download, click it
                        if 'download' in text.lower():
                            await button.click(force=True)
                            self.log(f"✅ Clicked button {i} with text: {text}", "SUCCESS")
                            return True
                except:
                    continue
        except Exception as e:
            self.log(f"Method 6 failed: {str(e)[:50]}", "ERROR")
            
        self.log("❌ Could not find Download button with any method!", "ERROR")
        return False
            
    async def download_with_force(self, folder_path):
        """Download files using multiple methods to find Download button"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"FORCE DOWNLOAD FROM: {folder_path}", "INFO")
        self.log(f"{'='*60}", "INFO")
        
        # Navigate to folder
        path_parts = folder_path.split('/')
        await self.navigate_to_folder(path_parts)
        
        # Create local folder if needed
        local_folder = self.base_path / folder_path
        local_folder.mkdir(parents=True, exist_ok=True)
        
        # Count existing files
        existing_files = list(local_folder.glob("*.txt"))
        self.log(f"📁 Local folder has {len(existing_files)} existing files", "INFO")
        
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
            
        # Process files in batches using multi-select
        downloaded_in_session = 0
        
        for i in range(0, len(file_rows), self.batch_size):
            batch = file_rows[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(file_rows) + self.batch_size - 1) // self.batch_size
            
            self.log(f"\n📦 Batch {batch_num}/{total_batches} - Selecting {len(batch)} files:", "INFO")
            
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
                        # Check if file already exists
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
                
                for idx, (row, filename) in enumerate(zip(files_to_download, batch_filenames)):
                    if idx == 0:
                        # First file - normal click
                        await row.click()
                        self.log(f"      • Selected: {filename}", "INFO")
                    else:
                        # Additional files - Ctrl+Click
                        await row.click(modifiers=['Control'])
                        self.log(f"      • Ctrl+Selected: {filename}", "INFO")
                    
                    await asyncio.sleep(0.3)  # Small delay between selections
                    
                # All files are now selected (highlighted)
                self.log(f"   ✓ {len(files_to_download)} files selected and highlighted", "SUCCESS")
                
                # NOW USE OUR ADVANCED METHOD TO FIND AND CLICK DOWNLOAD
                self.log("   📥 Attempting to click Download button...", "DOWNLOAD")
                
                # Wait a moment for UI to update
                await asyncio.sleep(1)
                
                # Try to find and click the Download button
                success = await self.find_and_click_download_button()
                
                if success:
                    # Wait for downloads to process
                    self.log("   ⏳ Waiting for downloads to complete...", "INFO")
                    await asyncio.sleep(5)
                    
                    # Check if files appeared locally
                    import shutil
                    downloads_folder = Path.home() / "Downloads"
                    
                    for filename in batch_filenames:
                        # Check if file appeared in Downloads
                        download_file = downloads_folder / filename
                        target_file = local_folder / filename
                        
                        if download_file.exists():
                            # Move file to correct folder
                            shutil.move(str(download_file), str(target_file))
                            self.downloaded_count += 1
                            downloaded_in_session += 1
                            size = target_file.stat().st_size
                            self.log(f"      ✅ Downloaded & moved: {filename} ({size:,} bytes)", "SUCCESS")
                        elif target_file.exists():
                            # File somehow got to right place
                            self.downloaded_count += 1
                            downloaded_in_session += 1
                            size = target_file.stat().st_size
                            self.log(f"      ✅ Downloaded: {filename} ({size:,} bytes)", "SUCCESS")
                        else:
                            self.log(f"      ⚠️ File not found after download: {filename}", "INFO")
                else:
                    self.log("   ❌ Could not activate download despite trying all methods!", "ERROR")
                    self.log("   📸 MANUAL INTERVENTION NEEDED - Please click Download button manually", "ERROR")
                    
                    # Wait for manual intervention
                    self.log("   ⏸️ Waiting 10 seconds for manual download...", "INFO")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                self.log(f"   ❌ Batch download failed: {str(e)[:100]}", "ERROR")
                
            # Show progress
            current_files = len(list(local_folder.glob("*.txt")))
            new_files = current_files - len(existing_files)
            self.log(f"\n📊 Folder progress: {new_files} new files downloaded", "INFO")
            
            # Check for timeout popup after batch
            await self.handle_timeout_popup()
            
            # Pause between batches
            if i + self.batch_size < len(file_rows):
                self.log("⏸️ Pausing before next batch...", "INFO")
                await asyncio.sleep(3)
                
        # Final count
        final_files = len(list(local_folder.glob("*.txt")))
        total_downloaded = final_files - len(existing_files)
        self.log(f"\n✅ FOLDER COMPLETE: {total_downloaded} new files downloaded", "SUCCESS")
        self.log(f"📁 Total files in {folder_path}: {final_files}", "INFO")
        
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
        print("FORCE SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE")
        print("🔍 Uses multiple methods to find Download button")
        print("📥 Downloads batch with forced clicking")
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
                
            # Test with one folder first
            test_folders = [
                "doc/fic/2014",  # Test with 2014 first
            ]
            
            for folder in test_folders:
                await self.download_with_force(folder)
                
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
            
            # Keep browser open
            self.log("\n🔄 Browser stays open for manual operations", "INFO")
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
    downloader = ForceSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Force SFTP Downloader")
    print("This will:")
    print("  🔍 Try MULTIPLE methods to find Download button")
    print("  📥 Use coordinate clicking if needed")
    print("  📋 List all buttons for debugging")
    print("  ⏰ Handle session timeout popups")
    print("-" * 60)
    
    asyncio.run(main())