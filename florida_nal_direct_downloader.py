"""
Florida NAL Direct Downloader
Downloads NAL files directly from known URLs
"""

import os
import requests
import zipfile
import time
from pathlib import Path
import json
from datetime import datetime

class FloridaNALDownloader:
    def __init__(self):
        self.base_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.nal_dir = self.base_dir / "NAL_2025"
        self.session = requests.Session()
        self.download_log = []
        
        # Create directories
        self.nal_dir.mkdir(parents=True, exist_ok=True)
        
        # Known NAL URLs for Florida counties (2025)
        # These are the standard patterns for Florida Revenue NAL files
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
        
        print(f"[DIR] Download directory: {self.nal_dir}")
        
    def try_download_url(self, url, county, filename):
        """Try to download from a specific URL"""
        try:
            print(f"    Trying: {url}")
            response = self.session.head(url, timeout=5)
            
            if response.status_code == 200:
                # File exists, download it
                print(f"    [FOUND] File exists! Downloading...")
                
                county_dir = self.nal_dir / county
                county_dir.mkdir(exist_ok=True)
                zip_path = county_dir / filename
                
                # Download with progress
                response = self.session.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"    Progress: {progress:.1f}%", end='\r')
                
                print(f"\n    [OK] Downloaded {filename} ({downloaded:,} bytes)")
                
                # Extract files
                print(f"    [EXTRACT] Extracting files...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    zip_ref.extractall(county_dir)
                    print(f"    [EXTRACTED] {len(file_list)} files")
                
                # Delete ZIP
                zip_path.unlink()
                print(f"    [CLEANUP] Removed ZIP file")
                
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def download_county(self, county):
        """Try different URL patterns for a county"""
        county_code = county.replace(" ", "_").replace(".", "")
        
        print(f"\n[COUNTY] {county}")
        
        # Try different URL patterns
        patterns = [
            # Pattern 1: Direct FTP folder structure
            f"https://floridarevenue.com/property/Documents/DataPortal/NAL/2025/{county_code}_NAL_2025.zip",
            f"https://floridarevenue.com/property/Documents/DataPortal/NAL/2025P/{county_code}_NAL_2025P.zip",
            
            # Pattern 2: Alternative paths
            f"https://floridarevenue.com/property/DataPortal/NAL/2025/{county_code}_NAL_2025.zip",
            f"https://floridarevenue.com/DataPortal/NAL/2025/{county_code}_NAL_2025.zip",
            
            # Pattern 3: FTP-style URLs
            f"https://floridarevenue.com/FTP/NAL/2025/{county_code}_NAL_2025.zip",
            f"https://floridarevenue.com/FTP/NAL/2025P/{county_code}_NAL_2025P.zip",
            
            # Pattern 4: Direct file access
            f"https://floridarevenue.com/files/NAL/2025/{county_code}_NAL_2025.zip",
            
            # Pattern 5: SharePoint-style
            f"https://floridarevenue.com/property/Shared%20Documents/DataPortal/NAL/2025/{county_code}_NAL_2025.zip"
        ]
        
        for url in patterns:
            filename = os.path.basename(url)
            if self.try_download_url(url, county, filename):
                self.download_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'county': county,
                    'url': url,
                    'status': 'success'
                })
                return True
        
        print(f"    [NOT FOUND] Could not find NAL file for {county}")
        self.download_log.append({
            'timestamp': datetime.now().isoformat(),
            'county': county,
            'status': 'not_found'
        })
        return False
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("FLORIDA NAL DIRECT DOWNLOADER")
        print("Attempting to download NAL files for all Florida counties")
        print("="*60)
        
        successful = 0
        failed = 0
        
        for county in self.counties:
            if self.download_county(county):
                successful += 1
            else:
                failed += 1
            
            # Small delay between attempts
            time.sleep(1)
        
        # Save log
        log_file = self.base_dir / f"nal_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'total_counties': len(self.counties),
                'successful': successful,
                'failed': failed,
                'download_log': self.download_log
            }, f, indent=2)
        
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE")
        print("="*60)
        print(f"[SUCCESS] Downloaded: {successful} counties")
        print(f"[FAILED] Not found: {failed} counties")
        print(f"[LOG] Log saved to: {log_file}")
        
        if successful == 0:
            print("\n[NOTE] No files were found. The URLs may have changed.")
            print("Please check the Florida Revenue website manually at:")
            print("https://floridarevenue.com/property/Pages/DataPortal.aspx")

if __name__ == "__main__":
    downloader = FloridaNALDownloader()
    downloader.run()