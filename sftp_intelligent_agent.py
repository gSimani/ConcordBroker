"""
Intelligent SFTP Download Agent
Permanent solution for Florida Department of State SFTP downloads
Downloads 4 files at a time, monitors progress, avoids duplicates
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
from typing import List, Dict, Set

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class IntelligentSFTPAgent:
    def __init__(self):
        # SFTP Credentials
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local paths
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Browser
        self.browser: Browser = None
        self.page: Page = None
        
        # Tracking
        self.local_files: Set[str] = set()
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_files = []
        self.current_location = ""
        self.session_downloads = []
        
        # Configuration
        self.batch_size = 4  # Download 4 files at a time
        self.timeout = 90000  # 90 second timeout
        
    def log(self, message, level="INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "DOWNLOAD": "📥", "FOLDER": "📁"}.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
        
    def scan_local_files(self):
        """Build complete map of existing files"""
        self.log("Scanning local files to prevent duplicates...", "INFO")
        
        total_size = 0
        folder_stats = {}
        
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                self.local_files.add(rel_path_str)
                total_size += full_path.stat().st_size
                
                # Track folder statistics
                folder = rel_path_str.split('/')[0] if '/' in rel_path_str else 'root'
                if folder not in folder_stats:
                    folder_stats[folder] = {'count': 0, 'size': 0}
                folder_stats[folder]['count'] += 1
                folder_stats[folder]['size'] += full_path.stat().st_size
                
        self.log(f"Found {len(self.local_files):,} existing files ({total_size/(1024**3):.2f} GB)", "SUCCESS")
        
        # Show folder breakdown
        for folder, stats in sorted(folder_stats.items()):
            self.log(f"  {folder}: {stats['count']:,} files, {stats['size']/(1024**2):.1f} MB", "INFO")
            
    async def initialize_browser(self):
        """Start visible browser with proper settings"""
        self.log("Starting VISIBLE browser for monitoring...", "INFO")
        
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
        
        # Set download behavior
        await context.route("**/*", lambda route: route.continue_())
        
        self.page = await context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        self.log("Browser window is OPEN and VISIBLE", "SUCCESS")
        
    async def login(self):
        """Login to SFTP portal"""
        self.log("Logging into SFTP portal...", "INFO")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Screenshot before login
        screenshot = self.base_path / f"agent_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot))
        
        # Fill credentials
        await self.page.fill('input[placeholder="Username"]', self.username)
        await self.page.fill('input[placeholder="Password"]', self.password)
        
        self.log("Credentials entered, clicking login...", "INFO")
        
        # Click login
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        # Verify login
        try:
            await self.page.wait_for_selector('tr:has-text("doc")', timeout=10000)
            self.current_location = "root"
            self.log("Login successful! Now in <root>\\Public\\", "SUCCESS")
            return True
        except:
            self.log("Login failed!", "ERROR")
            return False
            
    async def navigate_to_folder(self, path_parts: List[str]):
        """Navigate to specific folder path"""
        target = " → ".join(path_parts)
        self.log(f"Navigating to: {target}", "FOLDER")
        
        # Always start from root
        if self.current_location != "root":
            await self.return_to_root()
            
        # Navigate through each folder
        for part in path_parts:
            try:
                self.log(f"  Entering: {part}", "INFO")
                await self.page.dblclick(f'tr:has-text("{part}")', timeout=5000)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1.5)
                
            except Exception as e:
                self.log(f"  Failed to enter {part}: {str(e)[:50]}", "ERROR")
                return False
                
        self.current_location = "/".join(path_parts)
        self.log(f"Successfully navigated to: {self.current_location}", "SUCCESS")
        return True
        
    async def return_to_root(self):
        """Navigate back to root directory"""
        self.log("Returning to root...", "INFO")
        
        while self.current_location != "root":
            try:
                await self.page.dblclick('tr:has-text("..")', timeout=3000)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                # Update location
                parts = self.current_location.split('/')
                if len(parts) > 1:
                    self.current_location = '/'.join(parts[:-1])
                else:
                    self.current_location = "root"
                    
            except:
                self.current_location = "root"
                break
                
    async def get_files_in_current_folder(self):
        """Get all files (not folders) in current location"""
        self.log("Scanning for files in current folder...", "INFO")
        
        files = []
        
        # Scroll to load all items
        last_count = 0
        for i in range(10):
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
            # Count rows
            rows = await self.page.query_selector_all('tr')
            current_count = len(rows)
            
            if current_count == last_count:
                break  # No new items
            last_count = current_count
            
        # Parse all rows to find files
        rows = await self.page.query_selector_all('tr')
        
        for row in rows:
            try:
                cells = await row.query_selector_all('td')
                if len(cells) >= 4:
                    name_elem = cells[0]
                    type_elem = cells[1]
                    size_elem = cells[3]
                    
                    name = await name_elem.text_content() if name_elem else ""
                    type_text = await type_elem.text_content() if type_elem else ""
                    size = await size_elem.text_content() if size_elem else ""
                    
                    name = name.strip()
                    
                    # Check if it's a file (has extension or type is not Folder)
                    if name and name not in ['..', 'WELCOME.TXT']:
                        is_file = ('.' in name and type_text != "Folder") or type_text == "File"
                        if is_file:
                            files.append({
                                'name': name,
                                'size': size.strip()
                            })
                            
            except:
                continue
                
        self.log(f"Found {len(files)} files in current folder", "INFO")
        return files
        
    async def download_file_batch(self, files: List[Dict], folder_path: str):
        """Download a batch of files (4 at a time)"""
        batch_success = 0
        
        for file in files:
            filename = file['name']
            
            # Check if file exists locally
            local_path = f"{folder_path}/{filename}" if folder_path else filename
            
            if local_path in self.local_files:
                self.log(f"    ⏭️ Skipping (exists): {filename}", "INFO")
                self.skipped_count += 1
                continue
                
            # Create local directory if needed
            if folder_path:
                local_dir = self.base_path / folder_path
                local_dir.mkdir(parents=True, exist_ok=True)
            else:
                local_dir = self.base_path
                
            local_file = local_dir / filename
            
            # Double-check file doesn't exist
            if local_file.exists():
                self.log(f"    ⏭️ Skipping (exists): {filename}", "INFO")
                self.skipped_count += 1
                self.local_files.add(local_path)
                continue
                
            # Download the file
            try:
                self.log(f"    Downloading: {filename}", "DOWNLOAD")
                
                # Click on file to select it
                await self.page.click(f'tr:has-text("{filename}")', timeout=5000)
                await asyncio.sleep(0.3)
                
                # Click download button
                download_started = False
                
                # Try different download button selectors
                for selector in ['button:has-text("Download")', 'button[title="Download"]', '#download-button']:
                    try:
                        async with self.page.expect_download(timeout=30000) as download_info:
                            await self.page.click(selector, timeout=2000)
                            download_started = True
                            
                        download = await download_info.value
                        break
                    except:
                        continue
                        
                if not download_started:
                    raise Exception("Could not find download button")
                    
                # Save file
                await download.save_as(str(local_file))
                
                self.downloaded_count += 1
                batch_success += 1
                self.local_files.add(local_path)
                self.session_downloads.append(local_path)
                
                self.log(f"    ✅ Downloaded: {filename}", "SUCCESS")
                
                # Small delay between downloads
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.log(f"    ❌ Failed: {filename} - {str(e)[:50]}", "ERROR")
                self.failed_files.append({'file': local_path, 'error': str(e)})
                
        return batch_success
        
    async def download_folder_contents(self, folder_path: str):
        """Download all files from a folder in batches"""
        path_parts = folder_path.split('/')
        
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"Processing folder: {folder_path}", "FOLDER")
        self.log(f"{'='*60}", "INFO")
        
        # Navigate to folder
        if not await self.navigate_to_folder(path_parts):
            self.log(f"Could not navigate to {folder_path}", "ERROR")
            return
            
        # Get all files
        files = await self.get_files_in_current_folder()
        
        if not files:
            self.log("No files to download in this folder", "INFO")
            return
            
        # Process files in batches
        total_files = len(files)
        downloaded_in_folder = 0
        
        self.log(f"Starting batch download of {total_files} files (4 at a time)...", "INFO")
        
        for i in range(0, total_files, self.batch_size):
            batch = files[i:i+self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_files + self.batch_size - 1) // self.batch_size
            
            self.log(f"\nBatch {batch_num}/{total_batches} ({len(batch)} files):", "INFO")
            
            success = await self.download_file_batch(batch, folder_path)
            downloaded_in_folder += success
            
            # Show progress
            progress = ((i + len(batch)) / total_files) * 100
            self.log(f"Folder progress: {progress:.1f}% ({downloaded_in_folder} downloaded, {self.skipped_count} skipped)", "INFO")
            
            # Pause between batches
            if i + self.batch_size < total_files:
                await asyncio.sleep(2)
                
        self.log(f"Folder complete: {downloaded_in_folder} new files downloaded", "SUCCESS")
        
    async def intelligent_download_process(self):
        """Main intelligent download process"""
        self.log("\n" + "="*60, "INFO")
        self.log("INTELLIGENT DOWNLOAD PROCESS", "INFO")
        self.log("="*60, "INFO")
        
        # Priority folders based on what's missing
        priority_folders = [
            "doc/fic/2014",
            "doc/fic/2015", 
            "doc/fic/2016",
            "doc/fic/2017",
            "doc/fic/2018",
            "doc/fic/2019",
            "doc/fic/2020",
            "doc/fic/2021",
            "doc/FLR/DEBTORS",
            "doc/FLR/EVENTS",
            "doc/FLR/FILINGS",
            "doc/FLR/SECURED",
            "doc/gen/Events",
            "doc/gen/Filings",
            "doc/DHE",
            "doc/Quarterly/Cor",
            "doc/Quarterly/Fic",
            "doc/Quarterly/FLR",
            "doc/AG",
            "doc/cornp"
        ]
        
        for folder in priority_folders:
            await self.download_folder_contents(folder)
            
            # Return to root for next folder
            await self.return_to_root()
            
            # Show overall progress
            self.log(f"\n📊 Overall Progress: {self.downloaded_count} downloaded, {self.skipped_count} skipped, {len(self.failed_files)} failed", "INFO")
            
    async def generate_report(self):
        """Generate download report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'downloaded_count': self.downloaded_count,
            'skipped_count': self.skipped_count,
            'failed_count': len(self.failed_files),
            'total_local_files': len(self.local_files),
            'session_downloads': self.session_downloads,
            'failed_files': self.failed_files
        }
        
        report_path = self.base_path / f"agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"\nReport saved: {report_path}", "SUCCESS")
        
        # Print summary
        print("\n" + "="*60)
        print("DOWNLOAD SESSION COMPLETE")
        print("="*60)
        print(f"✅ Downloaded: {self.downloaded_count} files")
        print(f"⏭️ Skipped (already exist): {self.skipped_count} files")
        print(f"❌ Failed: {len(self.failed_files)} files")
        print(f"📁 Total local files: {len(self.local_files):,}")
        
        if self.failed_files:
            print("\n⚠️ Failed downloads:")
            for fail in self.failed_files[:5]:
                print(f"   - {fail['file']}: {fail['error'][:50]}")
                
    async def run(self):
        """Main execution"""
        print("="*60)
        print("INTELLIGENT SFTP DOWNLOAD AGENT")
        print("="*60)
        print("📺 Browser stays VISIBLE for monitoring")
        print("📥 Downloads 4 files at a time")
        print("⏭️ Skips duplicates automatically")
        print("📊 Shows real-time progress")
        print("-"*60)
        
        try:
            # Scan existing files
            self.scan_local_files()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                self.log("Cannot proceed without login", "ERROR")
                await asyncio.sleep(30)
                return
                
            # Run intelligent download process
            await self.intelligent_download_process()
            
            # Generate report
            await self.generate_report()
            
            # Keep browser open for manual operations
            self.log("\n🔄 Browser stays open for manual downloads", "INFO")
            self.log("Press Ctrl+C to close when done", "INFO")
            
            start_time = time.time()
            while True:
                elapsed = int(time.time() - start_time)
                mins = elapsed // 60
                secs = elapsed % 60
                
                status = (f"\r⏱️ Session: {mins:02d}:{secs:02d} | "
                         f"Downloaded: {self.downloaded_count} | "
                         f"Skipped: {self.skipped_count} | "
                         f"Failed: {len(self.failed_files)}")
                
                print(status, end="")
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            self.log("\n\nStopped by user", "INFO")
            
        except Exception as e:
            self.log(f"\nCritical error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            
            self.log("\nKeeping browser open for debugging...", "INFO")
            await asyncio.sleep(300)
            
        finally:
            # Always generate report
            await self.generate_report()
            
            if self.browser:
                self.log("Closing browser...", "INFO")
                await self.browser.close()
                
            self.log("Agent session complete!", "SUCCESS")

async def main():
    agent = IntelligentSFTPAgent()
    await agent.run()

if __name__ == "__main__":
    print("\n🤖 INTELLIGENT SFTP DOWNLOAD AGENT")
    print("This agent will:")
    print("  ✅ Download missing files intelligently")
    print("  📺 Keep browser visible for monitoring")
    print("  📦 Download 4 files at a time")
    print("  ⏭️ Skip all duplicates")
    print("  📊 Track and report progress")
    print("  📁 Maintain proper folder structure")
    print("-" * 60)
    
    asyncio.run(main())