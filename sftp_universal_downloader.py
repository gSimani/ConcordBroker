"""
SFTP Universal Downloader - Finds Download button regardless of HTML element type
Works with <button>, <a>, <div>, <input>, or any clickable element
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

class UniversalSFTPDownloader:
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
        self.batch_size = 4
        
    def log(self, message, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"SUCCESS": "✅", "ERROR": "❌", "DOWNLOAD": "📥", "INFO": "ℹ️", "FOUND": "🎯"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    async def initialize_browser(self):
        """Start visible browser with download handling"""
        self.log("Starting VISIBLE browser...", "INFO")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized'],
            slow_mo=300
        )
        
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(90000)
        
        self.log("Browser is VISIBLE - Watch the universal download solution!", "SUCCESS")
        
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
            
    async def find_download_element(self):
        """Find the Download element regardless of HTML tag type"""
        self.log("🔍 Searching for Download element (any type)...", "INFO")
        
        # Use JavaScript to find ALL elements that might be the Download button
        download_info = await self.page.evaluate("""
            () => {
                // Search all possible element types
                const selectors = [
                    'button', 'a', 'input[type="button"]', 'input[type="submit"]',
                    'div[onclick]', 'span[onclick]', '[role="button"]',
                    '.button', '.btn', '[class*="download"]', '[class*="Download"]',
                    'div', 'span', 'li', 'td'
                ];
                
                const results = [];
                const seenElements = new Set();
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            // Skip if already seen
                            if (seenElements.has(el)) return;
                            seenElements.add(el);
                            
                            // Check various properties for "download"
                            const text = el.textContent?.trim() || '';
                            const title = el.title || '';
                            const ariaLabel = el.getAttribute('aria-label') || '';
                            const value = el.value || '';
                            const className = el.className || '';
                            const id = el.id || '';
                            const innerHTML = el.innerHTML || '';
                            
                            // Check if this might be the Download button
                            if (text.toLowerCase().includes('download') ||
                                title.toLowerCase().includes('download') ||
                                ariaLabel.toLowerCase().includes('download') ||
                                value.toLowerCase().includes('download') ||
                                className.toLowerCase().includes('download') ||
                                id.toLowerCase().includes('download') ||
                                innerHTML.toLowerCase().includes('download')) {
                                
                                const rect = el.getBoundingClientRect();
                                results.push({
                                    tagName: el.tagName,
                                    text: text.substring(0, 50),
                                    selector: selector,
                                    className: className,
                                    id: id,
                                    title: title,
                                    isVisible: el.offsetParent !== null,
                                    position: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y)
                                    },
                                    hasOnClick: !!el.onclick,
                                    href: el.href || null
                                });
                            }
                        });
                    } catch (e) {
                        console.error('Error with selector:', selector, e);
                    }
                });
                
                return results;
            }
        """)
        
        # Report findings
        if download_info and len(download_info) > 0:
            self.log(f"Found {len(download_info)} potential Download elements:", "FOUND")
            for info in download_info[:5]:  # Show first 5
                if info['isVisible']:
                    self.log(f"  {info['tagName']}: '{info['text']}' at ({info['position']['x']}, {info['position']['y']})", "INFO")
            return download_info
        else:
            self.log("No Download elements found yet", "ERROR")
            return []
            
    async def click_download_universal(self):
        """Try multiple methods to click the Download element"""
        self.log("🎯 Attempting to click Download element...", "DOWNLOAD")
        
        # Method 1: Try common selectors for any element type
        selectors = [
            # Text-based selectors (work for any element)
            'text=Download',
            ':has-text("Download")',
            
            # Anchor tags
            'a:has-text("Download")',
            'a[title*="Download" i]',
            'a[href*="download" i]',
            
            # Input elements
            'input[value*="Download" i]',
            'input[type="button"][value*="Download" i]',
            
            # Role-based
            '[role="button"]:has-text("Download")',
            '[role="link"]:has-text("Download")',
            
            # Class-based
            '.button:has-text("Download")',
            '.btn:has-text("Download")',
            '[class*="download" i]',
            
            # Div/Span with handlers
            'div[onclick]:has-text("Download")',
            'span[onclick]:has-text("Download")',
            
            # Title/aria-label
            '[title*="Download" i]',
            '[aria-label*="Download" i]',
            
            # Generic - any element with Download text
            '*:has-text("Download")'
        ]
        
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        self.log(f"Found element with selector: {selector}", "FOUND")
                        await element.click()
                        self.log(f"✅ Clicked Download using: {selector}", "SUCCESS")
                        return True
            except Exception as e:
                continue
                
        # Method 2: Use JavaScript to find and click
        self.log("Trying JavaScript click method...", "INFO")
        clicked = await self.page.evaluate("""
            () => {
                // Find ANY element with Download text
                const allElements = document.getElementsByTagName('*');
                for (let el of allElements) {
                    const text = el.textContent?.trim() || '';
                    const title = el.title || '';
                    const value = el.value || '';
                    
                    if ((text === 'Download' || title.includes('Download') || value.includes('Download')) &&
                        el.offsetParent !== null) {  // Is visible
                        
                        console.log('Found Download element:', el);
                        el.click();
                        
                        // Try multiple click methods
                        if (el.onclick) el.onclick();
                        el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if clicked:
            self.log("✅ Clicked Download via JavaScript!", "SUCCESS")
            return True
            
        # Method 3: Click between Upload and Delete buttons
        self.log("Trying position-based click (between Upload and Delete)...", "INFO")
        try:
            # Find Upload button position
            upload_element = await self.page.query_selector(':has-text("Upload")')
            delete_element = await self.page.query_selector(':has-text("Delete")')
            
            if upload_element and delete_element:
                upload_box = await upload_element.bounding_box()
                delete_box = await delete_element.bounding_box()
                
                if upload_box and delete_box:
                    # Click between them
                    x = (upload_box['x'] + upload_box['width'] + delete_box['x']) / 2
                    y = upload_box['y'] + upload_box['height'] / 2
                    
                    self.log(f"Clicking between Upload and Delete at ({x}, {y})", "INFO")
                    await self.page.mouse.click(x, y)
                    return True
        except:
            pass
            
        self.log("❌ Could not click Download with any method!", "ERROR")
        return False
        
    async def download_files_universal(self, folder_path):
        """Download files using universal element detection"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"UNIVERSAL DOWNLOAD FROM: {folder_path}", "INFO")
        self.log(f"{'='*60}", "INFO")
        
        # Navigate to folder
        path_parts = folder_path.split('/')
        await self.navigate_to_folder(path_parts)
        
        # Create local folder
        local_folder = self.base_path / folder_path
        local_folder.mkdir(parents=True, exist_ok=True)
        
        # Count existing files
        existing_files = list(local_folder.glob("*.txt"))
        self.log(f"📁 Local folder has {len(existing_files)} existing files", "INFO")
        
        # First, find what the Download element actually is
        download_elements = await self.find_download_element()
        
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
            
        # Process first batch as test
        batch = file_rows[:self.batch_size]
        self.log(f"\n📦 Testing with first {len(batch)} files:", "INFO")
        
        # Collect filenames
        batch_filenames = []
        for row in batch:
            try:
                first_cell = await row.query_selector('td:first-child')
                filename = await first_cell.text_content() if first_cell else ""
                filename = filename.strip()
                
                if filename and '.txt' in filename:
                    local_file = local_folder / filename
                    if not local_file.exists():
                        batch_filenames.append(filename)
            except:
                continue
                
        if batch_filenames:
            # Select files
            self.log(f"Selecting {len(batch_filenames)} files...", "INFO")
            
            for idx, filename in enumerate(batch_filenames):
                row = await self.page.query_selector(f'tr:has-text("{filename}")')
                if row:
                    if idx == 0:
                        await row.click()
                        self.log(f"  Selected: {filename}", "INFO")
                    else:
                        await row.click(modifiers=['Control'])
                        self.log(f"  Ctrl+Selected: {filename}", "INFO")
                    await asyncio.sleep(0.2)
                    
            self.log("Files selected, now clicking Download...", "INFO")
            await asyncio.sleep(1)
            
            # Try to click Download
            try:
                async with self.page.expect_download(timeout=30000) as download_info:
                    if await self.click_download_universal():
                        self.log("Waiting for download to start...", "INFO")
                        
                        download = await download_info.value
                        
                        # Save file
                        save_path = local_folder / batch_filenames[0]
                        await download.save_as(str(save_path))
                        
                        self.downloaded_count += 1
                        self.log(f"✅ Downloaded: {batch_filenames[0]}", "SUCCESS")
                        self.log(f"📁 Saved to: {save_path}", "SUCCESS")
                    else:
                        self.log("Download button click failed!", "ERROR")
                        
            except Exception as e:
                self.log(f"Download error: {str(e)[:100]}", "ERROR")
                
                # Show manual instructions
                self.log("\n" + "="*60, "INFO")
                self.log("📸 MANUAL INTERVENTION NEEDED", "ERROR")
                self.log("The Download button could not be clicked automatically", "ERROR")
                self.log("Please manually click the Download button in the browser", "INFO")
                self.log("It should be in the toolbar, circled in green", "INFO")
                self.log("="*60, "INFO")
                
        # Return to root
        self.log("⬆️ Returning to root...", "INFO")
        for _ in range(len(path_parts)):
            await self.page.dblclick('tr:has-text("..")')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("UNIVERSAL SFTP DOWNLOADER")
        print("="*60)
        print("🔍 Finds Download button regardless of HTML element type")
        print("🎯 Works with <button>, <a>, <div>, <input>, etc.")
        print("📥 Uses multiple click strategies")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login", "ERROR")
                await asyncio.sleep(30)
                return
                
            # Test with one folder
            test_folders = [
                "doc/fic/2014",
            ]
            
            for folder in test_folders:
                await self.download_files_universal(folder)
                
                # Show progress
                self.log(f"\n📊 Progress: {self.downloaded_count} downloaded, {self.skipped_count} skipped", "INFO")
                
            # Final summary
            print("\n" + "="*60)
            print("SESSION COMPLETE")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"⏭️ Skipped: {self.skipped_count} files")
            
            # Keep browser open
            self.log("\n🔄 Browser stays open", "INFO")
            self.log("If download didn't work, please click Download button manually", "INFO")
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
    downloader = UniversalSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Universal SFTP Downloader")
    print("This will:")
    print("  🔍 Find Download element regardless of HTML tag")
    print("  🎯 Try multiple click strategies")
    print("  📸 Show what element type Download actually is")
    print("-" * 60)
    
    asyncio.run(main())