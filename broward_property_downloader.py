"""
Broward County Property Appraiser Data Downloader
Downloads property data directly from Broward County
"""

import os
import requests
import zipfile
import csv
from pathlib import Path
from datetime import datetime
import json

class BrowardPropertyDownloader:
    def __init__(self):
        self.base_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.broward_dir = self.base_dir / "BROWARD"
        self.session = requests.Session()
        
        # Create directory
        self.broward_dir.mkdir(parents=True, exist_ok=True)
        
        # Broward County download URLs (public data)
        self.data_urls = {
            'property_data': 'https://bcpa.net/RecordSearch/downloads/dailydata/NAL.txt',
            'sales_data': 'https://bcpa.net/RecordSearch/downloads/dailydata/SAL.txt',
            'tangible_property': 'https://bcpa.net/RecordSearch/downloads/dailydata/TPP.txt',
            'full_dataset': 'https://gis.broward.org/GISData/PropertyAppraiser/PropertyData.zip'
        }
        
        print(f"[DIR] Download directory: {self.broward_dir}")
        
    def download_file(self, url, filename, description):
        """Download a file with progress tracking"""
        try:
            print(f"\n[DOWNLOAD] {description}")
            print(f"    URL: {url}")
            
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            file_path = self.broward_dir / filename
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"    Progress: {progress:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='\r')
            
            print(f"\n    [OK] Downloaded {filename} ({downloaded:,} bytes)")
            
            # If it's a ZIP file, extract it
            if filename.endswith('.zip'):
                print(f"    [EXTRACT] Extracting {filename}...")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(self.broward_dir)
                    extracted_files = zip_ref.namelist()
                    print(f"    [EXTRACTED] {len(extracted_files)} files")
                
                # Remove ZIP after extraction
                file_path.unlink()
                print(f"    [CLEANUP] Removed ZIP file")
            
            return True
            
        except Exception as e:
            print(f"    [ERROR] Failed to download: {e}")
            return False
    
    def parse_nal_sample(self):
        """Parse a sample of the NAL (Name, Address, Legal) file"""
        nal_file = self.broward_dir / "NAL.txt"
        
        if not nal_file.exists():
            print("[WARNING] NAL.txt not found")
            return
        
        print("\n[PARSE] Analyzing NAL.txt structure...")
        
        try:
            with open(nal_file, 'r', encoding='latin-1') as f:
                # Read first 5 lines to understand structure
                print("\n    Sample records:")
                for i in range(5):
                    line = f.readline()
                    if not line:
                        break
                    
                    # NAL format is typically fixed-width
                    # Common fields: Parcel ID, Owner Name, Mailing Address, Property Address
                    print(f"    Record {i+1} (first 200 chars): {line[:200]}")
                
                # Count total records
                f.seek(0)
                total_lines = sum(1 for _ in f)
                print(f"\n    Total records in NAL.txt: {total_lines:,}")
                
        except Exception as e:
            print(f"    [ERROR] Failed to parse NAL.txt: {e}")
    
    def download_alternative_sources(self):
        """Try alternative Broward County data sources"""
        
        alternative_urls = [
            {
                'url': 'https://www.broward.org/OpenData/Documents/PropertyData.csv',
                'filename': 'PropertyData.csv',
                'description': 'Broward Open Data Property File'
            },
            {
                'url': 'https://bcpagis.broward.org/arcgis/rest/services/PublicAccess/MapServer/0/query?where=1%3D1&outFields=*&f=json&resultRecordCount=10',
                'filename': 'sample_properties.json',
                'description': 'Sample Property Data from GIS Service'
            }
        ]
        
        print("\n[ALTERNATIVE] Trying alternative data sources...")
        
        for source in alternative_urls:
            self.download_file(source['url'], source['filename'], source['description'])
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("BROWARD COUNTY PROPERTY APPRAISER DATA DOWNLOADER")
        print("="*60)
        
        success_count = 0
        
        # Try each data source
        for key, url in self.data_urls.items():
            filename = os.path.basename(url)
            description = key.replace('_', ' ').title()
            
            if self.download_file(url, filename, description):
                success_count += 1
        
        # Parse NAL file if downloaded
        if (self.broward_dir / "NAL.txt").exists():
            self.parse_nal_sample()
        
        # Try alternative sources
        self.download_alternative_sources()
        
        # Summary
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        print(f"[SUCCESS] Downloaded {success_count}/{len(self.data_urls)} primary files")
        print(f"[LOCATION] Data saved to: {self.broward_dir}")
        
        # List all downloaded files
        print("\n[FILES] Downloaded files:")
        for file_path in self.broward_dir.iterdir():
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"    - {file_path.name} ({size/1024/1024:.2f} MB)")
        
        return success_count > 0

if __name__ == "__main__":
    downloader = BrowardPropertyDownloader()
    downloader.run()