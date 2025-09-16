"""
Florida Property Appraiser Database Downloader
Downloads NAL files from floridarevenue.com and extracts them
Target: NAL/2025P county ZIP files
Destination: C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP
"""

import os
import requests
import zipfile
import time
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import shutil

class FloridaPropertyDownloader:
    def __init__(self):
        self.base_url = "https://floridarevenue.com/property/dataportal/"
        self.target_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.nal_dir = self.target_dir / "NAL_2025P"
        self.session = requests.Session()
        self.download_log = []
        
        # Create directories
        self.nal_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[DIR] Download directory: {self.nal_dir}")
        print(f"[URL] Source: {self.base_url}")
        
    def get_nal_files(self):
        """Navigate to NAL section and get 2025P files"""
        print("\n[SEARCH] Accessing NAL section...")
        
        # The NAL 2025P files URL pattern
        nal_2025p_url = "https://floridarevenue.com/property/dataportal/FTP%20Folders/NAL/2025P/"
        
        try:
            response = self.session.get(nal_2025p_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all ZIP file links
            zip_files = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.zip'):
                    file_name = os.path.basename(href)
                    full_url = urljoin(nal_2025p_url, href)
                    zip_files.append({
                        'name': file_name,
                        'url': full_url,
                        'county': file_name.replace('_NAL_2025P.zip', '').replace('_', ' ')
                    })
            
            print(f"[FOUND] {len(zip_files)} NAL county files")
            return zip_files
            
        except Exception as e:
            print(f"[ERROR] Error accessing NAL files: {e}")
            return []
    
    def download_and_extract(self, file_info):
        """Download a ZIP file and extract it"""
        file_name = file_info['name']
        url = file_info['url']
        county = file_info['county']
        
        # Create county-specific folder
        county_dir = self.nal_dir / county
        county_dir.mkdir(exist_ok=True)
        
        # Download path
        zip_path = self.nal_dir / file_name
        
        try:
            # Download with progress
            print(f"\n[DOWNLOAD] Downloading {county} data...")
            print(f"   URL: {url}")
            
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
                            print(f"   Progress: {progress:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='\r')
            
            print(f"\n[OK] Downloaded {file_name} ({downloaded:,} bytes)")
            
            # Extract files
            print(f"[EXTRACT] Extracting to {county_dir}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of files in ZIP
                file_list = zip_ref.namelist()
                print(f"   Files in archive: {len(file_list)}")
                
                # Extract all files
                zip_ref.extractall(county_dir)
                
                # Log extracted files
                extracted_files = []
                for file in file_list:
                    extracted_path = county_dir / file
                    if extracted_path.exists():
                        file_size = extracted_path.stat().st_size
                        extracted_files.append({
                            'name': file,
                            'size': file_size,
                            'path': str(extracted_path)
                        })
                        print(f"   > {file} ({file_size:,} bytes)")
            
            # Delete ZIP file after extraction
            zip_path.unlink()
            print(f"[CLEANUP] Removed ZIP file (keeping extracted data only)")
            
            # Log success
            self.download_log.append({
                'timestamp': datetime.now().isoformat(),
                'county': county,
                'zip_file': file_name,
                'url': url,
                'status': 'success',
                'extracted_files': extracted_files,
                'total_files': len(extracted_files)
            })
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error processing {county}: {e}")
            
            # Clean up partial download
            if zip_path.exists():
                zip_path.unlink()
            
            # Log failure
            self.download_log.append({
                'timestamp': datetime.now().isoformat(),
                'county': county,
                'zip_file': file_name,
                'url': url,
                'status': 'failed',
                'error': str(e)
            })
            
            return False
    
    def save_process_log(self):
        """Save the download process log"""
        log_file = self.target_dir / f"nal_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'start_time': self.download_log[0]['timestamp'] if self.download_log else None,
            'end_time': datetime.now().isoformat(),
            'total_counties': len(self.download_log),
            'successful': sum(1 for log in self.download_log if log['status'] == 'success'),
            'failed': sum(1 for log in self.download_log if log['status'] == 'failed'),
            'download_details': self.download_log
        }
        
        with open(log_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n[LOG] Process log saved to: {log_file}")
        return summary
    
    def run(self):
        """Main execution"""
        print("=" * 60)
        print("FLORIDA PROPERTY APPRAISER DATABASE DOWNLOADER")
        print("NAL (Name, Address, Legal) Files - 2025P")
        print("=" * 60)
        
        # Get list of NAL files
        nal_files = self.get_nal_files()
        
        if not nal_files:
            print("[ERROR] No NAL files found")
            return
        
        print(f"\n[LIST] Counties to download:")
        for i, file_info in enumerate(nal_files, 1):
            print(f"   {i}. {file_info['county']}")
        
        # Download and extract each file
        print(f"\n[START] Starting download of {len(nal_files)} county files...")
        
        successful = 0
        failed = 0
        
        for i, file_info in enumerate(nal_files, 1):
            print(f"\n[{i}/{len(nal_files)}] Processing {file_info['county']}...")
            
            if self.download_and_extract(file_info):
                successful += 1
            else:
                failed += 1
            
            # Small delay between downloads
            if i < len(nal_files):
                time.sleep(2)
        
        # Save process log
        summary = self.save_process_log()
        
        # Print summary
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        print(f"[SUCCESS] Downloaded: {successful} counties")
        if failed > 0:
            print(f"[FAILED] Failed: {failed} counties")
        print(f"[LOCATION] Data location: {self.nal_dir}")
        
        # List all extracted files
        print(f"\n[SUMMARY] Extracted Data Summary:")
        total_size = 0
        total_files = 0
        
        for county_dir in self.nal_dir.iterdir():
            if county_dir.is_dir():
                county_files = list(county_dir.glob('*'))
                county_size = sum(f.stat().st_size for f in county_files if f.is_file())
                total_size += county_size
                total_files += len(county_files)
                print(f"   {county_dir.name}: {len(county_files)} files, {county_size/1024/1024:.2f} MB")
        
        print(f"\n[TOTAL] {total_files} files, {total_size/1024/1024:.2f} MB")
        
        return summary

if __name__ == "__main__":
    downloader = FloridaPropertyDownloader()
    downloader.run()