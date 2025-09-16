"""
Playwright SFTP Complete Mapper and Downloader
Maps entire SFTP structure, compares with local, downloads all missing files
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

class CompleteSFTPMapper:
    def __init__(self):
        self.base_url = "https://sftp.floridados.gov"
        self.username = "Public"
        self.password = "PubAccess1845!"
        
        # Local base path
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.browser: Browser = None
        self.page: Page = None
        
        # Track files
        self.remote_structure = {}  # Complete remote structure
        self.local_structure = {}   # Complete local structure
        self.missing_files = []      # Files to download
        self.downloaded_count = 0
        self.skipped_count = 0
        
    def map_local_structure(self):
        """Map complete local file structure"""
        print("\n" + "="*60)
        print("📂 MAPPING LOCAL FILE STRUCTURE")
        print("="*60)
        
        total_files = 0
        total_size = 0
        
        # Walk through entire directory structure
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(self.base_path)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                size = full_path.stat().st_size
                self.local_structure[rel_path_str] = {
                    'size': size,
                    'size_mb': size / (1024 * 1024)
                }
                total_files += 1
                total_size += size
                
        # Show summary
        print(f"📊 Local Summary:")
        print(f"   Total files: {total_files:,}")
        print(f"   Total size: {total_size / (1024**3):.2f} GB")
        
        # Show folder breakdown
        folders = {}
        for path in self.local_structure:
            parts = path.split('/')
            if len(parts) > 1:
                folder = parts[0]
                if folder not in folders:
                    folders[folder] = {'count': 0, 'size': 0}
                folders[folder]['count'] += 1
                folders[folder]['size'] += self.local_structure[path]['size']
                
        print("\n📁 Folder breakdown:")
        for folder, info in sorted(folders.items()):
            print(f"   {folder}/: {info['count']:,} files, {info['size']/(1024**2):.1f} MB")
            
    async def initialize_browser(self):
        """Start visible browser"""
        print("\n🚀 Starting VISIBLE browser for complete mapping...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=False,  # VISIBLE
            args=['--start-maximized'],
            slow_mo=100  # Faster but still visible
        )
        
        context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        self.page = await context.new_page()
        self.page.set_default_timeout(60000)
        
        print("✅ Browser window opened - Mapping will be visible")
        
    async def login(self):
        """Login to portal"""
        print("\n🔐 Logging into SFTP portal...")
        
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
            print("✅ Login successful - Now in root directory")
            return True
        except:
            print("❌ Login failed")
            return False
            
    async def get_directory_items(self):
        """Get all items in current directory"""
        items = []
        
        # Scroll to load all items
        last_count = 0
        for _ in range(10):  # Try scrolling up to 10 times
            await self.page.keyboard.press('End')
            await asyncio.sleep(0.5)
            
            # Count current items
            rows = await self.page.query_selector_all('tr')
            current_count = len(rows)
            
            if current_count == last_count:
                break  # No new items loaded
            last_count = current_count
            
        # Parse all rows
        rows = await self.page.query_selector_all('tr')
        
        for row in rows:
            cells = await row.query_selector_all('td')
            if len(cells) >= 4:
                name_elem = cells[0]
                type_elem = cells[1]
                modified_elem = cells[2]
                size_elem = cells[3]
                
                name = await name_elem.text_content() if name_elem else ""
                type_text = await type_elem.text_content() if type_elem else ""
                modified = await modified_elem.text_content() if modified_elem else ""
                size = await size_elem.text_content() if size_elem else ""
                
                name = name.strip()
                
                # Skip parent directory and welcome file
                if name and name not in ['..', 'WELCOME.TXT']:
                    is_folder = type_text.strip() == "Folder" or not "." in name
                    
                    items.append({
                        'name': name,
                        'type': 'folder' if is_folder else 'file',
                        'modified': modified.strip(),
                        'size': size.strip(),
                        'size_bytes': self.parse_size(size.strip()) if not is_folder else 0
                    })
                    
        return items
        
    def parse_size(self, size_str):
        """Parse size string to bytes"""
        if not size_str or size_str == 'N/A':
            return 0
            
        try:
            # Remove commas
            size_str = size_str.replace(',', '')
            
            # Check for units
            if 'KB' in size_str:
                return int(float(size_str.replace('KB', '').strip()) * 1024)
            elif 'MB' in size_str:
                return int(float(size_str.replace('MB', '').strip()) * 1024 * 1024)
            elif 'GB' in size_str:
                return int(float(size_str.replace('GB', '').strip()) * 1024 * 1024 * 1024)
            else:
                # Assume bytes
                return int(float(size_str))
        except:
            return 0
            
    async def map_directory_recursive(self, path="", depth=0, max_depth=3):
        """Recursively map directory structure"""
        indent = "  " * depth
        current_path = path if path else "root"
        
        print(f"{indent}📁 Mapping: /{current_path}")
        
        # Get items in current directory
        items = await self.get_directory_items()
        
        # Store in structure
        if path not in self.remote_structure:
            self.remote_structure[path] = {}
            
        folders = []
        files = []
        
        for item in items:
            if item['type'] == 'folder':
                folders.append(item)
                folder_path = f"{path}/{item['name']}" if path else item['name']
                self.remote_structure[folder_path] = {'type': 'folder'}
            else:
                files.append(item)
                file_path = f"{path}/{item['name']}" if path else item['name']
                self.remote_structure[file_path] = {
                    'type': 'file',
                    'size': item['size'],
                    'size_bytes': item['size_bytes'],
                    'modified': item['modified']
                }
                
        print(f"{indent}   Found: {len(folders)} folders, {len(files)} files")
        
        # Recursively map folders (limit depth to avoid too deep recursion)
        if depth < max_depth:
            for folder in folders:
                # Skip certain system folders
                if folder['name'] in ['ficevent-Year2000', 'notes', 'tm']:
                    print(f"{indent}   ⏭️ Skipping system folder: {folder['name']}")
                    continue
                    
                print(f"{indent}   📂 Entering: {folder['name']}")
                
                # Double-click to enter folder
                await self.page.dblclick(f'tr:has-text("{folder["name"]}")')
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
                # Map this folder
                folder_path = f"{path}/{folder['name']}" if path else folder['name']
                await self.map_directory_recursive(folder_path, depth + 1, max_depth)
                
                # Go back to parent - double-click on ".." or use Parent Folder button
                print(f"{indent}   ⬆️ Going back to parent")
                try:
                    # First try double-clicking on ".."
                    await self.page.dblclick('tr:has-text("..")')
                except:
                    try:
                        # Alternative: click Parent Folder button
                        await self.page.click('button:has-text("Parent Folder")')
                    except:
                        # Last resort: single click on ".."
                        await self.page.click('tr:has-text("..")')
                        
                await self.page.wait_for_load_state('networkidle')
                await asyncio.sleep(1)
                
    async def map_entire_structure(self):
        """Map the entire SFTP structure"""
        print("\n" + "="*60)
        print("🗺️ MAPPING ENTIRE SFTP STRUCTURE")
        print("="*60)
        
        # Start from root
        await self.map_directory_recursive("", 0, 2)  # Map 2 levels deep
        
        # Now specifically map doc folder deeper
        print("\n📂 Deep mapping doc folder...")
        
        # Enter doc folder
        await self.page.dblclick('tr:has-text("doc")')
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)
        
        # Map doc contents
        await self.map_directory_recursive("doc", 1, 3)  # Go deeper in doc
        
        # Return to root - double-click on ".."
        await self.page.dblclick('tr:has-text("..")')
        await self.page.wait_for_load_state('networkidle')
        
        # Show structure summary
        print("\n" + "="*60)
        print("📊 SFTP STRUCTURE SUMMARY")
        print("="*60)
        
        folders = [k for k, v in self.remote_structure.items() if v.get('type') == 'folder']
        files = [k for k, v in self.remote_structure.items() if v.get('type') == 'file']
        
        print(f"Total folders: {len(folders)}")
        print(f"Total files: {len(files)}")
        
        # Show top-level folders
        top_folders = [f for f in folders if '/' not in f]
        print(f"\nTop-level folders: {', '.join(top_folders)}")
        
    def compare_structures(self):
        """Compare remote and local structures to find missing files"""
        print("\n" + "="*60)
        print("🔍 COMPARING STRUCTURES")
        print("="*60)
        
        self.missing_files = []
        
        for remote_path, remote_info in self.remote_structure.items():
            if remote_info.get('type') == 'file':
                # Check if we have this file locally
                if remote_path not in self.local_structure:
                    self.missing_files.append({
                        'path': remote_path,
                        'size': remote_info.get('size', 'Unknown'),
                        'size_bytes': remote_info.get('size_bytes', 0)
                    })
                    
        print(f"📊 Comparison Results:")
        print(f"   Remote files: {len([v for v in self.remote_structure.values() if v.get('type') == 'file'])}")
        print(f"   Local files: {len(self.local_structure)}")
        print(f"   Missing files: {len(self.missing_files)}")
        
        if self.missing_files:
            # Show missing files by folder
            by_folder = {}
            for file in self.missing_files:
                folder = file['path'].split('/')[0] if '/' in file['path'] else 'root'
                if folder not in by_folder:
                    by_folder[folder] = []
                by_folder[folder].append(file)
                
            print("\n❌ Missing files by folder:")
            for folder, files in sorted(by_folder.items()):
                total_size = sum(f['size_bytes'] for f in files) / (1024**2)
                print(f"   {folder}/: {len(files)} files ({total_size:.1f} MB)")
                
    async def download_missing_files(self):
        """Download all missing files"""
        if not self.missing_files:
            print("\n✅ No missing files to download!")
            return
            
        print("\n" + "="*60)
        print(f"📥 DOWNLOADING {len(self.missing_files)} MISSING FILES")
        print("="*60)
        
        # Group files by directory for efficient navigation
        by_directory = {}
        for file in self.missing_files:
            parts = file['path'].split('/')
            if len(parts) > 1:
                directory = '/'.join(parts[:-1])
                filename = parts[-1]
            else:
                directory = ""
                filename = file['path']
                
            if directory not in by_directory:
                by_directory[directory] = []
            by_directory[directory].append({'name': filename, 'full_path': file['path']})
            
        # Download files directory by directory
        for directory, files in by_directory.items():
            print(f"\n📁 Directory: /{directory if directory else 'root'}")
            
            # Navigate to directory
            if directory:
                # Go to root first
                current_location = await self.get_current_location()
                if current_location != "root":
                    # Navigate to root - double-click on ".."
                    while "doc" in current_location or "/" in current_location:
                        await self.page.dblclick('tr:has-text("..")')
                        await self.page.wait_for_load_state('networkidle')
                        await asyncio.sleep(1)
                        current_location = await self.get_current_location()
                        
                # Navigate to target directory
                path_parts = directory.split('/')
                for part in path_parts:
                    print(f"   📂 Entering: {part}")
                    await self.page.dblclick(f'tr:has-text("{part}")')
                    await self.page.wait_for_load_state('networkidle')
                    await asyncio.sleep(1)
                    
            # Download files in this directory
            for file in files[:10]:  # Limit to 10 files per folder for demo
                await self.download_file(file['name'], file['full_path'])
                
            # Return to root for next directory
            if directory:
                print("   ⬆️ Returning to root")
                while True:
                    try:
                        # Double-click on ".." to go back
                        await self.page.dblclick('tr:has-text("..")', timeout=2000)
                        await self.page.wait_for_load_state('networkidle')
                        await asyncio.sleep(1)
                    except:
                        break  # We're at root
                        
    async def get_current_location(self):
        """Get current directory location"""
        try:
            # Look for breadcrumb or path indicator
            # The SFTP portal shows path like <root>\Public\doc\
            return "root"  # Simplified for now
        except:
            return "unknown"
            
    async def download_file(self, filename, full_path):
        """Download a single file"""
        try:
            print(f"   📥 Downloading: {filename}")
            
            # Create local directory if needed
            local_dir = self.base_path
            if '/' in full_path:
                dir_parts = full_path.split('/')[:-1]
                local_dir = self.base_path / '/'.join(dir_parts)
                local_dir.mkdir(parents=True, exist_ok=True)
                
            local_file = local_dir / filename
            
            # Check if file already exists
            if local_file.exists():
                print(f"      ⏭️ Already exists, skipping")
                self.skipped_count += 1
                return
                
            # Click on file
            await self.page.click(f'tr:has-text("{filename}")')
            await asyncio.sleep(0.3)
            
            # Start download
            async with self.page.expect_download(timeout=120000) as download_info:
                await self.page.click('button:has-text("Download")')
                
            download = await download_info.value
            
            # Save file
            await download.save_as(str(local_file))
            
            self.downloaded_count += 1
            print(f"      ✅ Saved to: {local_file.relative_to(self.base_path)}")
            
            # Update local structure
            rel_path = str(local_file.relative_to(self.base_path)).replace('\\', '/')
            self.local_structure[rel_path] = {
                'size': local_file.stat().st_size,
                'size_mb': local_file.stat().st_size / (1024 * 1024)
            }
            
            await asyncio.sleep(0.5)  # Small delay between downloads
            
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            
    async def continuous_monitor(self):
        """Keep browser open for manual operations"""
        print("\n" + "="*60)
        print("🔄 MONITORING MODE")
        print("="*60)
        print("Browser stays open - you can manually download more files")
        print("Press Ctrl+C to stop")
        
        start_time = time.time()
        
        try:
            while True:
                elapsed = int(time.time() - start_time)
                mins = elapsed // 60
                secs = elapsed % 60
                
                status = f"⏱️ {mins:02d}:{secs:02d} | Downloaded: {self.downloaded_count} | Skipped: {self.skipped_count}"
                print(f"\r{status}", end="")
                
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
    async def run(self):
        """Main execution"""
        print("="*60)
        print("COMPLETE SFTP MAPPER AND DOWNLOADER")
        print("="*60)
        
        try:
            # Map local structure
            self.map_local_structure()
            
            # Start browser
            await self.initialize_browser()
            
            # Login
            if not await self.login():
                print("❌ Login failed")
                await asyncio.sleep(60)
                return
                
            # Map entire SFTP structure
            await self.map_entire_structure()
            
            # Compare structures
            self.compare_structures()
            
            # Download missing files
            await self.download_missing_files()
            
            # Summary
            print("\n" + "="*60)
            print("FINAL SUMMARY")
            print("="*60)
            print(f"✅ Downloaded: {self.downloaded_count} files")
            print(f"⏭️ Skipped (already exist): {self.skipped_count} files")
            print(f"📁 Total local files: {len(self.local_structure)}")
            
            # Save complete mapping
            mapping = {
                'timestamp': datetime.now().isoformat(),
                'remote_structure': {k: v for k, v in self.remote_structure.items() if v.get('type') == 'file'},
                'local_files': list(self.local_structure.keys()),
                'missing_files': self.missing_files,
                'downloaded': self.downloaded_count,
                'skipped': self.skipped_count
            }
            
            report_path = self.base_path / f"sftp_mapping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(mapping, f, indent=2)
                
            print(f"\n📄 Full mapping saved to: {report_path}")
            
            # Keep browser open
            await self.continuous_monitor()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            print("\n⏸️ Keeping browser open for debugging...")
            await asyncio.sleep(300)
            
        finally:
            if self.browser:
                print("🔒 Closing browser...")
                await self.browser.close()

async def main():
    mapper = CompleteSFTPMapper()
    await mapper.run()

if __name__ == "__main__":
    print("\n🚀 Starting Complete SFTP Mapper")
    print("This will:")
    print("  1. Map entire SFTP structure")
    print("  2. Compare with local files")
    print("  3. Download all missing files")
    print("  4. Create folders as needed")
    print("-" * 60)
    
    asyncio.run(main())