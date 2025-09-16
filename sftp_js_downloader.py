"""
SFTP JavaScript Downloader - Uses JS injection to find and click buttons
Directly manipulates the DOM to ensure Download button is clicked
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

class JSSFTPDownloader:
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
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "DOWNLOAD": "📥", "INFO": "ℹ️", "JS": "🔧"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    async def handle_timeout_popup(self):
        """Handle session timeout popup if it appears"""
        try:
            # Use JavaScript to check and click Continue
            result = await self.page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (let button of buttons) {
                        if (button.textContent.includes('Continue')) {
                            button.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if result:
                self.log("⏰ Session timeout handled via JS", "JS")
                await asyncio.sleep(1)
            return result
        except:
            return False
            
    async def initialize_browser(self):
        """Start visible browser"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=300  # Slow enough to see actions
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(90000)
        
        # Set up handler for timeout popup
        self.page.on("dialog", lambda dialog: dialog.accept())
        
        self.log("Browser is VISIBLE - Watch the JS-powered downloads!", "SUCCESS")
        
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
            
    async def find_download_button_js(self):
        """Use JavaScript to find and return info about the Download button"""
        button_info = await self.page.evaluate("""
            () => {
                // Method 1: Find all buttons and check their text/icons
                const buttons = document.querySelectorAll('button');
                const buttonInfo = [];
                
                for (let i = 0; i < buttons.length; i++) {
                    const button = buttons[i];
                    const text = button.textContent || '';
                    const title = button.title || '';
                    const className = button.className || '';
                    const innerHTML = button.innerHTML || '';
                    
                    // Store info about all buttons
                    buttonInfo.push({
                        index: i,
                        text: text.trim(),
                        title: title,
                        className: className,
                        hasDownloadText: text.toLowerCase().includes('download'),
                        hasDownloadIcon: innerHTML.includes('download') || innerHTML.includes('fa-download'),
                        isVisible: button.offsetParent !== null,
                        isEnabled: !button.disabled
                    });
                    
                    // Check if this is the Download button
                    if ((text.toLowerCase().includes('download') || 
                         title.toLowerCase().includes('download') ||
                         innerHTML.includes('fa-download')) &&
                        button.offsetParent !== null && 
                        !button.disabled) {
                        return {
                            found: true,
                            index: i,
                            text: text.trim(),
                            title: title,
                            className: className
                        };
                    }
                }
                
                // If not found by text, look for common download button patterns
                // Check for buttons with download icons (FontAwesome, Material Icons, etc.)
                for (let i = 0; i < buttons.length; i++) {
                    const button = buttons[i];
                    const icons = button.querySelectorAll('i, svg, span');
                    for (let icon of icons) {
                        const iconClass = icon.className || '';
                        if (iconClass.includes('download') || 
                            iconClass.includes('fa-download') ||
                            iconClass.includes('cloud-download')) {
                            if (button.offsetParent !== null && !button.disabled) {
                                return {
                                    found: true,
                                    index: i,
                                    text: button.textContent?.trim() || 'Icon Only',
                                    title: button.title || '',
                                    className: button.className || '',
                                    method: 'icon-search'
                                };
                            }
                        }
                    }
                }
                
                return {
                    found: false,
                    totalButtons: buttons.length,
                    buttonInfo: buttonInfo.slice(0, 10) // First 10 buttons for debugging
                };
            }
        """)
        
        return button_info
        
    async def click_download_button_js(self):
        """Use JavaScript to directly click the Download button"""
        self.log("🔧 Using JavaScript to click Download button...", "JS")
        
        # First, find the button
        button_info = await self.find_download_button_js()
        
        if button_info.get('found'):
            self.log(f"Found Download button: Index {button_info['index']}, Text: '{button_info['text']}'", "JS")
            
            # Click it using JavaScript
            clicked = await self.page.evaluate(f"""
                () => {{
                    const buttons = document.querySelectorAll('button');
                    const button = buttons[{button_info['index']}];
                    if (button) {{
                        // Try multiple click methods
                        button.click();
                        button.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                        return true;
                    }}
                    return false;
                }}
            """)
            
            if clicked:
                self.log("✅ Successfully clicked Download button via JavaScript!", "SUCCESS")
                return True
        else:
            self.log(f"❌ Download button not found. Total buttons: {button_info.get('totalButtons', 0)}", "ERROR")
            
            # Show info about available buttons
            if 'buttonInfo' in button_info:
                self.log("📋 Available buttons:", "JS")
                for btn in button_info['buttonInfo']:
                    if btn['isVisible']:
                        self.log(f"   Button {btn['index']}: '{btn['text']}' (class: {btn['className'][:30]}...)", "INFO")
                        
        return False
        
    async def select_files_js(self, file_indices):
        """Use JavaScript to select multiple files"""
        self.log(f"🔧 Selecting {len(file_indices)} files via JavaScript...", "JS")
        
        selected = await self.page.evaluate(f"""
            (indices) => {{
                const rows = document.querySelectorAll('tr');
                let selectedCount = 0;
                
                for (let index of indices) {{
                    if (rows[index]) {{
                        // Simulate click event
                        rows[index].click();
                        
                        // Also try to set selected class/attribute
                        rows[index].classList.add('selected');
                        rows[index].setAttribute('aria-selected', 'true');
                        
                        selectedCount++;
                    }}
                }}
                
                return selectedCount;
            }}
        """, file_indices)
        
        self.log(f"✅ Selected {selected} files", "JS")
        return selected > 0
        
    async def download_with_js(self, folder_path):
        """Download files using JavaScript manipulation"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"JS-POWERED DOWNLOAD FROM: {folder_path}", "INFO")
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
            
        # Get file info using JavaScript
        file_info = await self.page.evaluate("""
            () => {
                const rows = document.querySelectorAll('tr');
                const files = [];
                
                for (let i = 0; i < rows.length; i++) {
                    const firstCell = rows[i].querySelector('td:first-child');
                    if (firstCell) {
                        const text = firstCell.textContent || '';
                        if (text.includes('.txt')) {
                            files.push({
                                index: i,
                                filename: text.trim()
                            });
                        }
                    }
                }
                
                return files;
            }
        """)
        
        self.log(f"Found {len(file_info)} .txt files in folder", "INFO")
        
        if not file_info:
            self.log("No files to download", "INFO")
            return
            
        # Process files in batches
        downloaded_in_session = 0
        
        for i in range(0, len(file_info), self.batch_size):
            batch = file_info[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(file_info) + self.batch_size - 1) // self.batch_size
            
            self.log(f"\n📦 Batch {batch_num}/{total_batches} - Processing {len(batch)} files:", "INFO")
            
            # Check for timeout popup before batch
            await self.handle_timeout_popup()
            
            # Filter files that need downloading
            files_to_download = []
            indices_to_select = []
            
            for file in batch:
                filename = file['filename']
                local_file = local_folder / filename
                
                if local_file.exists():
                    self.log(f"   ⏭️ Skipping (exists): {filename}", "INFO")
                    self.skipped_count += 1
                else:
                    files_to_download.append(filename)
                    indices_to_select.append(file['index'])
                    
            if not files_to_download:
                self.log("   All files in batch already exist, skipping", "INFO")
                continue
                
            # Select files using JavaScript
            self.log(f"   🖱️ Selecting {len(files_to_download)} files:", "INFO")
            
            # Clear any previous selection
            await self.page.evaluate("""
                () => {
                    document.querySelectorAll('tr.selected').forEach(row => {
                        row.classList.remove('selected');
                        row.setAttribute('aria-selected', 'false');
                    });
                }
            """)
            
            # Select the files
            if await self.select_files_js(indices_to_select):
                for filename in files_to_download:
                    self.log(f"      • Selected: {filename}", "INFO")
                    
                await asyncio.sleep(1)  # Let UI update
                
                # Click Download button using JavaScript
                self.log("   📥 Attempting to click Download button via JavaScript...", "DOWNLOAD")
                
                # Start download expectation before clicking
                try:
                    async with self.page.expect_download(timeout=30000) as download_info:
                        # Try to click the Download button
                        if await self.click_download_button_js():
                            self.log("   ⏳ Waiting for download to start...", "INFO")
                            
                            download = await download_info.value
                            
                            # Save the first file (or handle multiple)
                            if files_to_download:
                                save_path = local_folder / files_to_download[0]
                                await download.save_as(str(save_path))
                                
                                self.downloaded_count += 1
                                downloaded_in_session += 1
                                
                                size = save_path.stat().st_size if save_path.exists() else 0
                                self.log(f"      ✅ Downloaded: {files_to_download[0]} ({size:,} bytes)", "SUCCESS")
                        else:
                            self.log("   ❌ Could not click Download button!", "ERROR")
                            
                except Exception as e:
                    self.log(f"   ❌ Download failed: {str(e)[:100]}", "ERROR")
                    
                    # Last resort: Try clicking by coordinates
                    self.log("   🎯 Attempting click by coordinates...", "JS")
                    await self.page.mouse.click(400, 100)  # Approximate Download button position
                    await asyncio.sleep(2)
                    
            # Show progress
            current_files = len(list(local_folder.glob("*.txt")))
            new_files = current_files - len(existing_files)
            self.log(f"\n📊 Folder progress: {new_files} new files downloaded", "INFO")
            
            # Check for timeout popup after batch
            await self.handle_timeout_popup()
            
            # Pause between batches
            if i + self.batch_size < len(file_info):
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
        print("JAVASCRIPT SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE")
        print("🔧 Uses JavaScript injection")
        print("📥 Direct DOM manipulation")
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
                await self.download_with_js(folder)
                
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
            self.log("Watch the browser - you can click Download manually if needed", "INFO")
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
    downloader = JSSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting JavaScript SFTP Downloader")
    print("This will:")
    print("  🔧 Use JavaScript injection to find buttons")
    print("  📥 Directly manipulate DOM elements")
    print("  📋 Show debug info about all buttons")
    print("  🎯 Try coordinate clicking as last resort")
    print("-" * 60)
    
    asyncio.run(main())