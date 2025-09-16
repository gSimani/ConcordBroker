"""
Complete Sunbiz SFTP Mapper and Downloader
Maps the entire directory structure and downloads missing files
"""

import asyncio
import os
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from playwright.async_api import async_playwright, Page, Browser
import logging

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SunbizSFTPCompleteMapper:
    def __init__(self):
        """Initialize the complete mapper and downloader"""
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local paths
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
        # Directory mapping
        self.remote_structure = {}
        self.local_structure = {}
        self.missing_files = []
        
    def analyze_local_files(self) -> Dict:
        """Analyze what we already have downloaded"""
        print("📁 Analyzing local files...")
        local_structure = {}
        
        for item in self.base_path.iterdir():
            if item.is_dir():
                file_count = sum(1 for _ in item.rglob('*.txt'))
                zip_count = sum(1 for _ in item.rglob('*.zip'))
                total_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                
                local_structure[item.name] = {
                    'type': 'directory',
                    'txt_files': file_count,
                    'zip_files': zip_count,
                    'total_size_mb': total_size / (1024 * 1024),
                    'path': str(item)
                }
            elif item.is_file():
                local_structure[item.name] = {
                    'type': 'file',
                    'size_mb': item.stat().st_size / (1024 * 1024),
                    'path': str(item)
                }
        
        # Print summary
        print("\n📊 LOCAL DATA SUMMARY:")
        print("-" * 50)
        for name, info in sorted(local_structure.items()):
            if info['type'] == 'directory':
                print(f"📁 {name:20} - {info['txt_files']:,} txt files, {info['total_size_mb']:.1f} MB")
            else:
                print(f"📄 {name:20} - {info['size_mb']:.1f} MB")
        
        self.local_structure = local_structure
        return local_structure
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("\n🚀 Initializing browser...")
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        print("✅ Browser ready")
        
    async def login_to_sftp(self):
        """Login to the SFTP web interface"""
        print(f"\n🔐 Logging into {self.base_url}...")
        
        await self.page.goto(self.base_url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Take screenshot of login page
        screenshot_path = self.base_path / f"sftp_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")
        
        # Try to find and fill login form
        try:
            # Look for username field
            username_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[id="username"]',
                'input[placeholder*="user" i]',
                'input[type="text"]:first-of-type'
            ]
            
            for selector in username_selectors:
                try:
                    await self.page.fill(selector, self.username, timeout=3000)
                    print(f"✅ Username entered using: {selector}")
                    break
                except:
                    continue
            
            # Look for password field
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]'
            ]
            
            for selector in password_selectors:
                try:
                    await self.page.fill(selector, self.password, timeout=3000)
                    print(f"✅ Password entered")
                    break
                except:
                    continue
            
            # Submit login
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")'
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    print(f"✅ Login submitted")
                    break
                except:
                    continue
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Login form not found or login not required: {e}")
            # May already be in the file browser
        
        # Take screenshot after login
        after_login_screenshot = self.base_path / f"sftp_after_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=after_login_screenshot)
        print(f"📸 Post-login screenshot: {after_login_screenshot}")
        
    async def map_directory_structure(self) -> Dict:
        """Map the complete directory structure"""
        print("\n🗺️ Mapping directory structure...")
        
        structure = {}
        
        # Get all links on the page
        links = await self.page.query_selector_all('a')
        
        for link in links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                
                if text and href:
                    # Clean up the text
                    text = text.strip()
                    
                    # Skip parent directory and special links
                    if text in ['..', '.', 'Parent Directory']:
                        continue
                    
                    # Determine if it's a file or directory
                    is_file = any(ext in text.lower() for ext in ['.txt', '.zip', '.csv', '.dat'])
                    
                    structure[text] = {
                        'href': href,
                        'type': 'file' if is_file else 'directory',
                        'text': text
                    }
                    
            except:
                continue
        
        print(f"📊 Found {len(structure)} items in current directory")
        
        # Print structure
        print("\n📁 DIRECTORY STRUCTURE:")
        print("-" * 50)
        
        # Group by type
        directories = [k for k, v in structure.items() if v['type'] == 'directory']
        files = [k for k, v in structure.items() if v['type'] == 'file']
        
        if directories:
            print("\n📁 DIRECTORIES:")
            for dir_name in sorted(directories):
                print(f"  📁 {dir_name}")
        
        if files:
            print("\n📄 FILES:")
            for file_name in sorted(files)[:20]:  # Show first 20 files
                print(f"  📄 {file_name}")
            if len(files) > 20:
                print(f"  ... and {len(files) - 20} more files")
        
        self.remote_structure = structure
        return structure
    
    async def navigate_to_directory(self, directory_name: str):
        """Navigate into a specific directory"""
        print(f"\n📂 Navigating to {directory_name}...")
        
        try:
            # Find and click the directory link
            link_selector = f'a:has-text("{directory_name}")'
            await self.page.click(link_selector)
            
            # Wait for navigation
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            print(f"✅ Entered {directory_name} directory")
            return True
            
        except Exception as e:
            print(f"❌ Could not navigate to {directory_name}: {e}")
            return False
    
    async def compare_and_identify_missing(self):
        """Compare remote and local files to identify what's missing"""
        print("\n🔍 Comparing remote and local files...")
        
        missing = []
        
        # Priority directories for officer/contact data
        priority_dirs = ['off', 'officers', 'principals', 'AG', 'annual']
        
        for item_name, item_info in self.remote_structure.items():
            # Check if this is a priority item
            is_priority = any(p in item_name.lower() for p in priority_dirs)
            
            # Check if we have this locally
            if item_name not in self.local_structure:
                missing.append({
                    'name': item_name,
                    'type': item_info['type'],
                    'href': item_info['href'],
                    'priority': is_priority
                })
        
        # Sort by priority
        missing.sort(key=lambda x: (not x['priority'], x['name']))
        
        print(f"\n📊 MISSING FILES ANALYSIS:")
        print(f"  Total missing: {len(missing)}")
        print(f"  Priority items: {sum(1 for m in missing if m['priority'])}")
        
        if missing:
            print("\n🎯 PRIORITY MISSING ITEMS:")
            for item in missing[:10]:
                if item['priority']:
                    print(f"  ⭐ {item['name']} ({item['type']})")
            
            print("\n📄 OTHER MISSING ITEMS:")
            for item in missing[:10]:
                if not item['priority']:
                    print(f"  - {item['name']} ({item['type']})")
        
        self.missing_files = missing
        return missing
    
    async def download_missing_files(self, limit: int = 5):
        """Download missing files, prioritizing officer/contact data"""
        print(f"\n📥 Downloading up to {limit} missing files...")
        
        downloaded = 0
        
        for item in self.missing_files[:limit]:
            if item['type'] == 'directory':
                # Navigate into directory
                success = await self.navigate_to_directory(item['name'])
                if success:
                    # Map subdirectory
                    sub_structure = await self.map_directory_structure()
                    
                    # Download files from subdirectory
                    for sub_item_name, sub_item_info in list(sub_structure.items())[:3]:
                        if sub_item_info['type'] == 'file':
                            await self.download_file(sub_item_name, sub_item_info['href'])
                            downloaded += 1
                    
                    # Navigate back
                    await self.page.go_back()
                    await self.page.wait_for_load_state('networkidle')
            else:
                # Download file directly
                await self.download_file(item['name'], item['href'])
                downloaded += 1
            
            if downloaded >= limit:
                break
        
        print(f"✅ Downloaded {downloaded} files")
        
    async def download_file(self, filename: str, href: str):
        """Download a specific file"""
        print(f"  📥 Downloading {filename}...")
        
        try:
            # Start download
            async with self.page.expect_download() as download_info:
                await self.page.click(f'a[href="{href}"]')
            
            download = await download_info.value
            
            # Save to local path
            save_path = self.base_path / filename
            await download.save_as(save_path)
            
            print(f"  ✅ Saved: {save_path}")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to download {filename}: {e}")
            return False
    
    async def create_mapping_report(self):
        """Create a comprehensive mapping report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sftp_url': self.base_url,
            'local_path': str(self.base_path),
            'local_structure': self.local_structure,
            'remote_structure': {k: v['type'] for k, v in self.remote_structure.items()},
            'missing_files': self.missing_files[:20],  # First 20 missing
            'statistics': {
                'local_directories': sum(1 for v in self.local_structure.values() if v['type'] == 'directory'),
                'local_files': sum(1 for v in self.local_structure.values() if v['type'] == 'file'),
                'remote_items': len(self.remote_structure),
                'missing_items': len(self.missing_files),
                'priority_missing': sum(1 for m in self.missing_files if m['priority'])
            }
        }
        
        report_path = self.base_path / f"sftp_mapping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Mapping report saved: {report_path}")
        return report_path
    
    async def run_complete_mapping(self):
        """Run the complete mapping and download process"""
        print("=" * 60)
        print("SUNBIZ SFTP COMPLETE MAPPING & DOWNLOAD")
        print("=" * 60)
        
        try:
            # Analyze local files first
            self.analyze_local_files()
            
            # Initialize browser
            await self.initialize_browser()
            
            # Login to SFTP
            await self.login_to_sftp()
            
            # Map directory structure
            await self.map_directory_structure()
            
            # Compare and identify missing
            await self.compare_and_identify_missing()
            
            # Download missing files
            await self.download_missing_files(limit=5)
            
            # Create report
            await self.create_mapping_report()
            
            print("\n✅ Mapping and download complete!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            if self.browser:
                await self.browser.close()
                print("🔒 Browser closed")


async def main():
    """Main entry point"""
    mapper = SunbizSFTPCompleteMapper()
    await mapper.run_complete_mapping()


if __name__ == "__main__":
    asyncio.run(main())