"""
Download all required Florida Revenue data files
"""

import os
import requests
import zipfile
import time
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL"""
    print(f"Downloading {filename}...")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"  Progress: {percent:.1f}%", end='\r')
        
        print(f"  [OK] Downloaded {filename}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to download {filename}: {e}")
        return False

def extract_zip(zip_file, extract_to='.'):
    """Extract ZIP file"""
    print(f"Extracting {zip_file}...")
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"  [OK] Extracted {zip_file}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to extract {zip_file}: {e}")
        return False

def main():
    print("DOWNLOADING FLORIDA REVENUE DATA FILES")
    print("="*60)
    
    files_to_download = [
        {
            'url': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Broward%2016%20Preliminary%20NAL%202025.zip',
            'filename': 'broward_nal_2025.zip',
            'description': 'NAL - Name/Address with Land data (contains property use codes)'
        },
        {
            'url': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20D/Broward%2016%20NAV%20Detail%202024.zip',
            'filename': 'broward_nav_detail_2024.zip',
            'description': 'NAV Detail - Non-Ad Valorem assessments'
        },
        {
            'url': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20N/Broward%2016%20NAV%20Name%202024.zip',
            'filename': 'broward_nav_name_2024.zip',
            'description': 'NAV Name - Non-Ad Valorem assessment names'
        }
    ]
    
    # Check existing files
    existing = ['NAP16P202501.csv', 'SDF16P202501.csv', 'broward_sdf_2025.zip', 'broward_tpp_2025.zip']
    print("Existing files:")
    for f in existing:
        if os.path.exists(f):
            print(f"  [OK] {f}")
    
    print("\nDownloading missing files...")
    
    for file_info in files_to_download:
        if os.path.exists(file_info['filename']):
            print(f"  [OK] {file_info['filename']} already exists")
            continue
            
        print(f"\n{file_info['description']}")
        success = download_file(file_info['url'], file_info['filename'])
        
        if success and file_info['filename'].endswith('.zip'):
            extract_zip(file_info['filename'])
        
        time.sleep(1)  # Be polite to the server
    
    # Extract existing zips if needed
    print("\nExtracting ZIP files...")
    for zip_file in ['broward_sdf_2025.zip', 'broward_tpp_2025.zip']:
        if os.path.exists(zip_file):
            extract_zip(zip_file)
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    
    # List all CSV files
    print("\nAvailable CSV files:")
    for f in Path('.').glob('*.csv'):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.name} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()