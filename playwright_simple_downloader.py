"""
Simple SFTP Downloader - Downloads files with visible browser
Focuses on downloading actual files, not navigating folders
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

class SimpleSFTPDownloader:
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
        
    async def initialize_browser(self):
        """Start VISIBLE browser"""
        print("\n🚀 Starting VISIBLE browser...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # VISIBLE
            args=['--start-maximized'],
            slow_mo=300  # Slow enough to see
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(90000)  # 90 second timeout
        
        print("✅ Browser is VISIBLE - Watch the downloads!")
        
    async def login(self):
        """Login to SFTP portal"""
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
            print("✅ Login successful!")
            return True
        except:
            print("❌ Login failed")
            return False
            
    async def download_from_location(self, path_to_navigate):
        """Navigate to a location and download files"""
        print(f"\n" + "="*60)
        print(f"📁 Going to: {' -> '.join(path_to_navigate)}")
        print("="*60)
        
        # Navigate through folders
        for folder in path_to_navigate:
            print(f"   📂 Double-clicking: {folder}")
            try:
                # Double-click to enter folder
                await self.page.dblclick(f'tr:has-text("{folder}")', timeout=5000)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"   ❌ Could not enter {folder}: {e}")
                return
                
        # Now we're in the target folder - get files
        print("\n   🔍 Looking for files to download...")
        
        # Scroll to see all files
        for _ in range(3):
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
        # Get all rows
        rows = await self.page.query_selector_all('tr')
        
        files_found = []
        for row in rows:
            try:
                # Get first cell (name)
                name_cell = await row.query_selector('td:first-child')
                if name_cell:
                    name = await name_cell.text_content()
                    if name and '.txt' in name.lower():  # Look for text files
                        files_found.append(name.strip())
            except:
                pass
                
        if not files_found:
            print("   📭 No files found in this location")
        else:
            print(f"   📄 Found {len(files_found)} files")
            
            # Download first 5 files as a test
            for filename in files_found[:5]:
                await self.download_single_file(filename, '/'.join(path_to_navigate))
                
        # Go back to root for next location
        print("\n   ⬆️ Returning to root...")
        for _ in range(len(path_to_navigate)):
            try:
                await self.page.dblclick('tr:has-text("..")', timeout=3000)
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
            except:
                break
                
    async def download_single_file(self, filename, folder_path):
        """Download a single file"""
        # Check if file exists
        local_dir = self.base_path / folder_path.replace(' -> ', '/')
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file = local_dir / filename
        
        if local_file.exists():
            print(f"      ⏭️ Skipping (exists): {filename}")
            self.skipped_count += 1
            return
            
        try:
            print(f"      📥 Downloading: {filename}")
            
            # Click on file to select
            await self.page.click(f'tr:has-text("{filename}")')
            await asyncio.sleep(0.5)
            
            # Click download button
            async with self.page.expect_download(timeout=60000) as download_info:
                # Try different download button selectors
                try:
                    await self.page.click('button:has-text("Download")')
                except:
                    try:
                        await self.page.click('button[title="Download"]')
                    except:
                        await self.page.click('#download-button')
                        
            download = await download_info.value
            
            # Save file
            await download.save_as(str(local_file))
            
            self.downloaded_count += 1
            print(f"      ✅ Saved: {filename}")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"      ❌ Failed: {str(e)[:50]}")
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("SIMPLE SFTP DOWNLOADER")
        print("="*60)
        print("📺 Browser stays VISIBLE")
        print("📥 Downloading files from specific locations")
        print("-"*60)
        
        try:
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                print("❌ Cannot proceed without login")
                await asyncio.sleep(30)
                return
                
            # Download from specific locations we know have files
            locations_to_check = [
                ["doc", "fic", "2014"],  # fic 2014 folder
                ["doc", "fic", "2015"],  # fic 2015 folder
                ["doc", "fic", "2016"],  # fic 2016 folder
                ["doc", "FLR", "DEBTORS"],  # FLR debtors
                ["doc", "gen", "Events"],  # gen events
                ["doc", "DHE"],  # DHE files
                ["doc", "Quarterly", "Cor"],  # Quarterly cor
            ]
            
            for location in locations_to_check:
                await self.download_from_location(location)
                
                # Show progress
                print(f"\n📊 Progress: {self.downloaded_count} downloaded, {self.skipped_count} skipped")
                
            # Final summary
            print("\n" + "="*60)
            print("✅ DOWNLOAD SESSION COMPLETE")
            print("="*60)
            print(f"📥 Files downloaded: {self.downloaded_count}")
            print(f"⏭️ Files skipped: {self.skipped_count}")
            
            # Keep browser open
            print("\n🔄 Browser stays open for manual downloads")
            print("Press Ctrl+C to close")
            
            while True:
                await asyncio.sleep(10)
                print(f"\r⏱️ Browser open | Downloads: {self.downloaded_count} | Skipped: {self.skipped_count}", end="")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            print("\n⏸️ Browser stays open for debugging...")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                print("\n🔒 Closing browser...")
                await self.browser.close()

async def main():
    downloader = SimpleSFTPDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("\n🚀 Starting Simple SFTP Downloader")
    print("This will:")
    print("  📺 Keep browser VISIBLE")
    print("  📥 Download files from specific folders")
    print("  ⏭️ Skip files that already exist")
    print("-" * 60)
    
    asyncio.run(main())