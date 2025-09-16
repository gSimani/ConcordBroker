"""
Playwright SFTP Monitor - Keeps browser open for extended monitoring
Shows real-time download progress with visual feedback
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

class SFTPMonitor:
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
        self.files_to_download = []
        
    def scan_existing_files(self):
        """Scan what we already have downloaded"""
        print("\n" + "="*60)
        print("📂 SCANNING EXISTING FILES")
        print("="*60)
        
        # Check main directory
        for item in self.base_path.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                self.existing_files[item.name] = f"{size_mb:.1f} MB"
                print(f"✅ {item.name}: {size_mb:.1f} MB")
                
        # Check doc folder
        doc_path = self.base_path / "doc"
        if doc_path.exists():
            for item in doc_path.iterdir():
                if item.is_dir():
                    file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                    self.existing_files[f"doc/{item.name}"] = f"{file_count} files"
                    print(f"📁 doc/{item.name}/: {file_count} files")
                elif item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    self.existing_files[f"doc/{item.name}"] = f"{size_mb:.1f} MB"
                    print(f"✅ doc/{item.name}: {size_mb:.1f} MB")
                    
        print(f"\nTotal existing locations: {len(self.existing_files)}")
                
    async def initialize_browser(self):
        """Initialize Playwright browser - VISIBLE"""
        print("\n" + "="*60)
        print("🖥️ STARTING VISIBLE BROWSER")
        print("="*60)
        print("Browser will stay open for monitoring...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # KEEP VISIBLE
            args=['--start-maximized'],
            slow_mo=500  # Slow down actions so user can see
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        # Add console message listener for debugging
        self.page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        print("✅ Browser window opened - MONITORING ACTIVE")
        print("⏱️ Browser will stay open for extended monitoring")
        
    async def login(self):
        """Login to SFTP portal"""
        print("\n" + "="*60)
        print("🔐 LOGGING INTO SFTP PORTAL")
        print("="*60)
        
        print(f"📍 Navigating to {self.base_url}...")
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Take screenshot
        screenshot_path = self.base_path / f"monitor_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        print(f"📸 Login page screenshot: {screenshot_path.name}")
        
        print("\n🔑 Entering credentials...")
        
        # Fill username
        await self.page.fill('input[placeholder="Username"]', self.username)
        print("   ✓ Username: Public")
        await asyncio.sleep(0.5)
        
        # Fill password
        await self.page.fill('input[placeholder="Password"]', self.password)
        print("   ✓ Password: ********")
        await asyncio.sleep(0.5)
        
        # Click login
        print("   ⏳ Clicking Login button...")
        await self.page.click('button:has-text("Login")')
        
        # Wait for navigation
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Verify login
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            print("\n✅ LOGIN SUCCESSFUL!")
            print("📍 Current location: <root>\\Public\\")
            
            # Take screenshot
            after_login = self.base_path / f"monitor_after_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(after_login))
            print(f"📸 Main directory screenshot: {after_login.name}")
            return True
        except:
            print("❌ Login failed or timeout")
            return False
            
    async def explore_root_files(self):
        """Check for files in root Public folder"""
        print("\n" + "="*60)
        print("🔍 EXPLORING ROOT PUBLIC FOLDER")
        print("="*60)
        
        # Scroll to bottom to see all files
        print("📜 Scrolling to see all items...")
        for i in range(5):
            await self.page.keyboard.press('End')
            await asyncio.sleep(1)
            print(f"   Scroll {i+1}/5")
            
        # Get all items
        items = await self.page.evaluate('''
            () => {
                const items = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    if (row.querySelector('th')) return;
                    
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const name = cells[0]?.textContent?.trim();
                        const type = cells[1]?.textContent?.trim();
                        const size = cells[3]?.textContent?.trim();
                        
                        if (name && name !== '..' && name !== 'WELCOME.TXT') {
                            items.push({
                                name: name,
                                type: type || 'Unknown',
                                size: size || 'N/A',
                                isFolder: !name.includes('.')
                            });
                        }
                    }
                });
                
                return items;
            }
        ''')
        
        print(f"\n📊 Found {len(items)} items in root")
        
        # Separate folders and files
        folders = [i for i in items if i['isFolder']]
        files = [i for i in items if not i['isFolder']]
        
        if files:
            print(f"\n📄 FILES IN ROOT ({len(files)}):")
            for file in files:
                if file['name'] not in self.existing_files:
                    print(f"   ❌ MISSING: {file['name']} - {file['size']}")
                    self.files_to_download.append(('root', file))
                else:
                    print(f"   ✅ HAVE: {file['name']} - {self.existing_files[file['name']]}")
                    
        print(f"\n📁 FOLDERS ({len(folders)}):")
        for folder in folders[:10]:
            status = "✅" if f"doc/{folder['name']}" in self.existing_files else "❓"
            print(f"   {status} {folder['name']}/")
            
    async def enter_doc_folder(self):
        """Navigate into doc folder"""
        print("\n" + "="*60)
        print("📂 ENTERING DOC FOLDER")
        print("="*60)
        
        print("🖱️ Double-clicking on 'doc' folder...")
        await self.page.dblclick('tr:has-text("doc")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        print("✅ Entered doc folder")
        
        # Take screenshot
        doc_screenshot = self.base_path / f"monitor_doc_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(doc_screenshot))
        print(f"📸 Doc folder screenshot: {doc_screenshot.name}")
        
    async def check_doc_files(self):
        """Check for actual files in doc folder"""
        print("\n" + "="*60)
        print("🔍 CHECKING DOC FOLDER FOR FILES")
        print("="*60)
        
        # Scroll down multiple times
        print("📜 Scrolling to find files...")
        for i in range(10):
            await self.page.keyboard.press('End')
            await asyncio.sleep(1)
            
            # Check if we can see any .zip files
            zip_files = await self.page.query_selector_all('tr:has-text(".zip")')
            if zip_files:
                print(f"   ✓ Found {len(zip_files)} ZIP files after scroll {i+1}")
                break
            else:
                print(f"   Scroll {i+1}/10 - looking for files...")
                
        # Get all items after scrolling
        items = await self.page.evaluate('''
            () => {
                const items = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    if (row.querySelector('th')) return;
                    
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const name = cells[0]?.textContent?.trim();
                        const size = cells[3]?.textContent?.trim();
                        
                        if (name && name.includes('.')) {
                            items.push({
                                name: name,
                                size: size || 'N/A'
                            });
                        }
                    }
                });
                
                return items;
            }
        ''')
        
        if items:
            print(f"\n📄 FOUND {len(items)} FILES IN DOC FOLDER:")
            for file in items[:20]:
                if f"doc/{file['name']}" not in self.existing_files:
                    print(f"   ❌ MISSING: {file['name']} - {file['size']}")
                    self.files_to_download.append(('doc', file))
                else:
                    print(f"   ✅ HAVE: {file['name']}")
                    
    async def download_missing_files(self):
        """Download any missing files"""
        if not self.files_to_download:
            print("\n" + "="*60)
            print("✅ NO MISSING FILES TO DOWNLOAD")
            print("="*60)
            print("All important files are already downloaded!")
            return
            
        print("\n" + "="*60)
        print(f"📥 DOWNLOADING {len(self.files_to_download)} MISSING FILES")
        print("="*60)
        
        for location, file in self.files_to_download[:3]:  # Limit to 3 for demo
            print(f"\n📥 Downloading: {file['name']} from {location}")
            
            # Navigate to correct location if needed
            if location == 'root' and await self.page.query_selector('text=/doc/'):
                print("   📍 Going back to root...")
                await self.page.go_back()
                await asyncio.sleep(2)
                
            try:
                # Select file
                await self.page.click(f'tr:has-text("{file["name"]}")')
                print(f"   ✓ Selected {file['name']}")
                await asyncio.sleep(1)
                
                # Start download
                async with self.page.expect_download(timeout=120000) as download_info:
                    await self.page.click('button:has-text("Download")')
                    print(f"   ⏳ Download started...")
                    
                download = await download_info.value
                
                # Save file
                save_path = self.base_path / location if location != 'root' else self.base_path
                save_path.mkdir(exist_ok=True)
                full_path = save_path / file['name']
                
                await download.save_as(str(full_path))
                self.downloaded_files.append(str(full_path))
                
                print(f"   ✅ DOWNLOADED: {full_path}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                self.failed_downloads.append(file['name'])
                
            await asyncio.sleep(2)
            
    async def monitor_loop(self):
        """Keep browser open and monitor"""
        print("\n" + "="*60)
        print("🔄 ENTERING MONITORING MODE")
        print("="*60)
        print("Browser will stay open for you to monitor and explore")
        print("You can manually download additional files")
        print("\nPress Ctrl+C in terminal to stop monitoring")
        
        start_time = time.time()
        
        while True:
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            
            print(f"\r⏱️ Monitoring active: {minutes:02d}:{seconds:02d} | Downloads: {len(self.downloaded_files)} | Browser: OPEN", end="")
            
            await asyncio.sleep(5)
            
            # Periodically take screenshots
            if elapsed % 60 == 0 and elapsed > 0:
                screenshot = self.base_path / f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=str(screenshot))
                print(f"\n📸 Periodic screenshot: {screenshot.name}")
                
    async def run(self):
        """Main execution"""
        print("="*60)
        print("SFTP DOWNLOAD MONITOR - EXTENDED SESSION")
        print("="*60)
        print("Browser will stay VISIBLE for continuous monitoring")
        print("-"*60)
        
        try:
            # Scan existing files
            self.scan_existing_files()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                print("❌ Login failed, keeping browser open for manual intervention")
                await asyncio.sleep(300)  # Keep open for 5 minutes
                return
                
            # Explore root for files
            await self.explore_root_files()
            
            # Enter doc folder
            await self.enter_doc_folder()
            
            # Check for files in doc
            await self.check_doc_files()
            
            # Download missing files
            await self.download_missing_files()
            
            # Enter monitoring mode - keeps browser open
            await self.monitor_loop()
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitoring stopped by user")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("\n⏸️ Keeping browser open for debugging...")
            await asyncio.sleep(300)  # Keep open for 5 minutes
            
        finally:
            # Save report
            report = {
                'timestamp': datetime.now().isoformat(),
                'downloaded': self.downloaded_files,
                'failed': self.failed_downloads,
                'existing_files': list(self.existing_files.keys()),
                'session_duration': 'Extended monitoring session'
            }
            
            report_path = self.base_path / f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            print(f"\n📄 Report saved: {report_path}")
            
            if self.browser:
                print("\n🔒 Closing browser...")
                await self.browser.close()
                
            print("✅ Monitoring session complete!")

async def main():
    """Main entry point"""
    monitor = SFTPMonitor()
    await monitor.run()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("STARTING SFTP MONITOR WITH EXTENDED VISIBILITY")
    print("="*60)
    print("The browser will:")
    print("  1. Stay VISIBLE throughout the entire session")
    print("  2. Show real-time download progress")
    print("  3. Remain open for continuous monitoring")
    print("  4. Allow manual file downloads")
    print("\nPress Ctrl+C to stop monitoring when done")
    print("-" * 60 + "\n")
    
    asyncio.run(main())