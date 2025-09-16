"""
Florida Revenue Data Portal Navigator
Uses Playwright to navigate and download NAL, NAP, NAV, SDF files for all counties
"""

import os
import time
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import json
import asyncio
from playwright.async_api import async_playwright
import requests

class FloridaRevenueNavigator:
    def __init__(self):
        self.base_url = "https://floridarevenue.com/property/dataportal/Pages/default.aspx"
        self.root_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.session = requests.Session()
        self.download_log = []
        
        # Florida counties (67 total)
        self.counties = [
            "ALACHUA", "BAKER", "BAY", "BRADFORD", "BREVARD", "BROWARD",
            "CALHOUN", "CHARLOTTE", "CITRUS", "CLAY", "COLLIER", "COLUMBIA",
            "DESOTO", "DIXIE", "DUVAL", "ESCAMBIA", "FLAGLER", "FRANKLIN",
            "GADSDEN", "GILCHRIST", "GLADES", "GULF", "HAMILTON", "HARDEE",
            "HENDRY", "HERNANDO", "HIGHLANDS", "HILLSBOROUGH", "HOLMES", "INDIAN RIVER",
            "JACKSON", "JEFFERSON", "LAFAYETTE", "LAKE", "LEE", "LEON",
            "LEVY", "LIBERTY", "MADISON", "MANATEE", "MARION", "MARTIN",
            "MIAMI-DADE", "MONROE", "NASSAU", "OKALOOSA", "OKEECHOBEE", "ORANGE",
            "OSCEOLA", "PALM BEACH", "PASCO", "PINELLAS", "POLK", "PUTNAM",
            "SANTA ROSA", "SARASOTA", "SEMINOLE", "ST. JOHNS", "ST. LUCIE", "SUMTER",
            "SUWANNEE", "TAYLOR", "UNION", "VOLUSIA", "WAKULLA", "WALTON", "WASHINGTON"
        ]
        
        # File types to download
        self.file_types = ["NAL", "NAP", "NAV", "SDF"]
        
        # Current year
        self.year = "2025"
        
        print(f"[INIT] Root directory: {self.root_dir}")
        print(f"[INIT] Target year: {self.year}")
        print(f"[INIT] Counties: {len(self.counties)}")
        print(f"[INIT] File types: {', '.join(self.file_types)}")
        
    def create_folder_structure(self):
        """Create the folder structure for all counties"""
        print("\n[FOLDERS] Creating folder structure...")
        
        for county in self.counties:
            county_dir = self.root_dir / county
            
            for file_type in self.file_types:
                type_dir = county_dir / file_type
                type_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[FOLDERS] Created structure for {len(self.counties)} counties")
        
    def try_direct_urls(self):
        """Try direct URL patterns based on common Florida Revenue structures"""
        print("\n[DIRECT] Trying direct URL patterns...")
        
        successful_downloads = []
        
        # Common URL patterns for Florida Revenue data
        url_patterns = [
            # Pattern 1: Direct file in Tax Roll Data Files
            "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/{file_type}/{year}/{county}_{file_type}_{year}.zip",
            
            # Pattern 2: Without year folder
            "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/{file_type}/{county}_{file_type}_{year}.zip",
            
            # Pattern 3: Alternative path
            "https://floridarevenue.com/property/dataportal/Documents/{file_type}/{year}/{county}_{file_type}_{year}.zip",
            
            # Pattern 4: With P suffix for preliminary
            "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/{file_type}/{year}P/{county}_{file_type}_{year}P.zip",
            
            # Pattern 5: Direct in Documents
            "https://floridarevenue.com/property/Documents/{file_type}/{county}_{file_type}_{year}.zip",
        ]
        
        for county in self.counties[:3]:  # Test with first 3 counties
            print(f"\n[COUNTY] Testing {county}...")
            
            for file_type in self.file_types:
                print(f"  [TYPE] {file_type}...")
                
                for pattern in url_patterns:
                    # Format URL with county and file type
                    county_code = county.replace(" ", "_").replace(".", "")
                    url = pattern.format(
                        county=county_code,
                        file_type=file_type,
                        year=self.year
                    )
                    
                    try:
                        # Try HEAD request first to check if file exists
                        response = self.session.head(url, timeout=5, allow_redirects=True)
                        
                        if response.status_code == 200:
                            print(f"    [FOUND] {url}")
                            
                            # Download the file
                            self.download_and_extract(url, county, file_type)
                            successful_downloads.append({
                                'county': county,
                                'file_type': file_type,
                                'url': url,
                                'pattern': pattern
                            })
                            break  # Found working pattern, skip others
                            
                    except Exception as e:
                        continue  # Try next pattern
        
        return successful_downloads
    
    def download_and_extract(self, url, county, file_type):
        """Download a file and extract it to the appropriate folder"""
        try:
            county_dir = self.root_dir / county / file_type
            filename = os.path.basename(url)
            zip_path = county_dir / filename
            
            print(f"    [DOWNLOAD] Downloading {filename}...")
            
            # Download file
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"      Progress: {progress:.1f}%", end='\r')
            
            print(f"\n    [EXTRACT] Extracting {filename}...")
            
            # Extract ZIP file
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Extract all files
                    zip_ref.extractall(county_dir)
                    extracted_files = zip_ref.namelist()
                    print(f"    [EXTRACTED] {len(extracted_files)} files")
                
                # Remove ZIP file after extraction
                zip_path.unlink()
                print(f"    [CLEANUP] Removed ZIP file")
                
                # Log success
                self.download_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'county': county,
                    'file_type': file_type,
                    'url': url,
                    'status': 'success',
                    'files_extracted': len(extracted_files)
                })
                
                return True
                
            except zipfile.BadZipFile:
                print(f"    [ERROR] Not a valid ZIP file")
                # Check if it's an HTML error page
                with open(zip_path, 'rb') as f:
                    content = f.read(1000)
                    if b'<html' in content or b'<!DOCTYPE' in content:
                        print(f"    [ERROR] Downloaded HTML error page instead of ZIP")
                        zip_path.unlink()
                        
        except Exception as e:
            print(f"    [ERROR] Download failed: {e}")
            
            self.download_log.append({
                'timestamp': datetime.now().isoformat(),
                'county': county,
                'file_type': file_type,
                'url': url,
                'status': 'failed',
                'error': str(e)
            })
            
            return False
    
    async def navigate_with_playwright(self):
        """Use Playwright to navigate the site and find actual file links"""
        print("\n[PLAYWRIGHT] Starting browser navigation...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Show browser for debugging
            page = await browser.new_page()
            
            try:
                # Navigate to the data portal
                print("[NAVIGATE] Going to data portal...")
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                
                # Look for Tax Roll Data Files link
                print("[SEARCH] Looking for Tax Roll Data Files...")
                
                # Try to find and click on PTO Data Portal or Tax Roll Data Files
                links_to_try = [
                    "PTO Data Portal",
                    "Tax Roll Data Files",
                    "Download Tax Rolls",
                    "Data Files"
                ]
                
                for link_text in links_to_try:
                    try:
                        link = page.locator(f"text={link_text}").first
                        if await link.is_visible():
                            print(f"[FOUND] Clicking on '{link_text}'...")
                            await link.click()
                            await page.wait_for_load_state('networkidle')
                            break
                    except:
                        continue
                
                # Look for NAL, NAP, NAV, SDF folders
                print("[SEARCH] Looking for file type folders...")
                
                for file_type in self.file_types:
                    try:
                        folder = page.locator(f"text={file_type}").first
                        if await folder.is_visible():
                            print(f"[FOUND] {file_type} folder")
                            await folder.click()
                            await page.wait_for_load_state('networkidle')
                            
                            # Get all links on the page
                            links = await page.locator("a").all()
                            
                            for link in links:
                                href = await link.get_attribute("href")
                                text = await link.text_content()
                                
                                if href and ".zip" in href:
                                    print(f"  [FILE] Found: {text} -> {href}")
                            
                            # Go back for next file type
                            await page.go_back()
                            await page.wait_for_load_state('networkidle')
                            
                    except Exception as e:
                        print(f"[ERROR] Could not find {file_type}: {e}")
                
            except Exception as e:
                print(f"[ERROR] Navigation failed: {e}")
                
            finally:
                await browser.close()
    
    def run(self):
        """Main execution"""
        print("="*70)
        print("FLORIDA REVENUE DATA PORTAL COMPREHENSIVE DOWNLOADER")
        print("="*70)
        
        # Create folder structure
        self.create_folder_structure()
        
        # Try direct URLs first
        successful = self.try_direct_urls()
        
        if successful:
            print(f"\n[SUCCESS] Found working pattern for {len(successful)} downloads")
            
            # If we found a working pattern, use it for all counties
            if successful:
                working_pattern = successful[0]['pattern']
                print(f"\n[PATTERN] Using working pattern: {working_pattern}")
                
                # Download for all counties using the working pattern
                for county in self.counties:
                    for file_type in self.file_types:
                        county_code = county.replace(" ", "_").replace(".", "")
                        url = working_pattern.format(
                            county=county_code,
                            file_type=file_type,
                            year=self.year
                        )
                        
                        print(f"\n[DOWNLOAD] {county} - {file_type}")
                        self.download_and_extract(url, county, file_type)
                        time.sleep(1)  # Be respectful to the server
        else:
            print("\n[FALLBACK] Direct URLs didn't work, trying Playwright navigation...")
            # Try Playwright navigation
            asyncio.run(self.navigate_with_playwright())
        
        # Save download log
        log_file = self.root_dir / f"florida_revenue_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'total_counties': len(self.counties),
                'file_types': self.file_types,
                'year': self.year,
                'downloads': self.download_log
            }, f, indent=2)
        
        print(f"\n[LOG] Download log saved to: {log_file}")
        
        # Summary
        successful_count = sum(1 for log in self.download_log if log['status'] == 'success')
        failed_count = sum(1 for log in self.download_log if log['status'] == 'failed')
        
        print("\n" + "="*70)
        print("DOWNLOAD SUMMARY")
        print("="*70)
        print(f"[SUCCESS] {successful_count} files downloaded successfully")
        print(f"[FAILED] {failed_count} downloads failed")
        print(f"[LOCATION] {self.root_dir}")

if __name__ == "__main__":
    navigator = FloridaRevenueNavigator()
    navigator.run()