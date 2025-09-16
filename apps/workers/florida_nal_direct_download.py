"""
Florida Revenue NAL Direct Downloader
Downloads NAL files directly from Florida Revenue website
"""

import os
import time
import json
import zipfile
import requests
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaNALDirectDownloader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.download_log = []
        
        # Direct download URLs - These are the actual file paths on Florida Revenue
        self.base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P"
        
        # County list with their codes
        self.counties = {
            "ALACHUA": "01", "BAKER": "02", "BAY": "03", "BRADFORD": "04",
            "BREVARD": "05", "BROWARD": "06", "CALHOUN": "07", "CHARLOTTE": "08",
            "CITRUS": "09", "CLAY": "10", "COLLIER": "11", "COLUMBIA": "12",
            "DESOTO": "13", "DIXIE": "14", "DUVAL": "15", "ESCAMBIA": "16",
            "FLAGLER": "17", "FRANKLIN": "18", "GADSDEN": "19", "GILCHRIST": "20",
            "GLADES": "21", "GULF": "22", "HAMILTON": "23", "HARDEE": "24",
            "HENDRY": "25", "HERNANDO": "26", "HIGHLANDS": "27", "HILLSBOROUGH": "28",
            "HOLMES": "29", "INDIAN RIVER": "30", "JACKSON": "31", "JEFFERSON": "32",
            "LAFAYETTE": "33", "LAKE": "34", "LEE": "35", "LEON": "36",
            "LEVY": "37", "LIBERTY": "38", "MADISON": "39", "MANATEE": "40",
            "MARION": "41", "MARTIN": "42", "MIAMI-DADE": "43", "MONROE": "44",
            "NASSAU": "45", "OKALOOSA": "46", "OKEECHOBEE": "47", "ORANGE": "48",
            "OSCEOLA": "49", "PALM BEACH": "50", "PASCO": "51", "PINELLAS": "52",
            "POLK": "53", "PUTNAM": "54", "SANTA ROSA": "55", "SARASOTA": "56",
            "SEMINOLE": "57", "ST. JOHNS": "58", "ST. LUCIE": "59", "SUMTER": "60",
            "SUWANNEE": "61", "TAYLOR": "62", "UNION": "63", "VOLUSIA": "64",
            "WAKULLA": "65", "WALTON": "66", "WASHINGTON": "67"
        }
        
    def get_county_folder(self, county: str) -> Path:
        """Get the NAL folder path for a county"""
        county_folder = self.base_path / county.upper() / "NAL"
        county_folder.mkdir(parents=True, exist_ok=True)
        return county_folder
    
    def download_file(self, url: str, dest_path: Path) -> bool:
        """Download a file from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logger.info(f"Downloading from {url}")
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\rDownloading: {progress:.1f}%", end='')
                
                print()  # New line after progress
                logger.info(f"Successfully downloaded {dest_path.name}")
                return True
            else:
                logger.warning(f"Failed to download (status {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def extract_zip(self, zip_path: Path) -> bool:
        """Extract zip file"""
        try:
            logger.info(f"Extracting {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_path.parent)
            logger.info("Extraction successful")
            # Delete the zip file after extraction
            zip_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return False
    
    def download_county(self, county: str, code: str) -> dict:
        """Download NAL file for a specific county"""
        result = {
            "county": county,
            "code": code,
            "status": "pending",
            "file_path": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get destination folder
            dest_folder = self.get_county_folder(county)
            
            # Check if file already exists
            existing_files = list(dest_folder.glob("NAL25P*.xlsx")) + list(dest_folder.glob("NAL25P*.xls"))
            if existing_files:
                logger.info(f"File already exists for {county}: {existing_files[0].name}")
                result["status"] = "exists"
                result["file_path"] = str(existing_files[0])
                return result
            
            # Try different file naming patterns
            file_patterns = [
                f"NAL25P_{code}.xlsx",
                f"NAL25P_{code}.zip",
                f"NAL25P{code}.xlsx",
                f"NAL25P{code}.zip",
                f"NAL25P_{county.replace(' ', '%20')}.xlsx",
                f"NAL25P_{county.replace(' ', '%20')}.zip"
            ]
            
            for pattern in file_patterns:
                url = f"{self.base_url}/{pattern}"
                
                if pattern.endswith('.zip'):
                    dest_file = dest_folder / pattern
                else:
                    dest_file = dest_folder / pattern
                
                if self.download_file(url, dest_file):
                    # If it's a zip, extract it
                    if pattern.endswith('.zip'):
                        self.extract_zip(dest_file)
                        # Check for extracted Excel file
                        excel_files = list(dest_folder.glob("*.xlsx")) + list(dest_folder.glob("*.xls"))
                        if excel_files:
                            result["file_path"] = str(excel_files[0])
                    else:
                        result["file_path"] = str(dest_file)
                    
                    result["status"] = "success"
                    return result
            
            # If no pattern worked
            result["status"] = "failed"
            result["error"] = "No valid download URL found"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error processing {county}: {e}")
        
        return result
    
    def download_all(self):
        """Download NAL files for all counties"""
        total = len(self.counties)
        logger.info(f"Starting download for {total} counties")
        print("="*60)
        
        success_count = 0
        exists_count = 0
        failed_count = 0
        
        for i, (county, code) in enumerate(self.counties.items(), 1):
            print(f"\n[{i}/{total}] Processing {county} (Code: {code})")
            print("-"*40)
            
            result = self.download_county(county, code)
            self.download_log.append(result)
            
            if result["status"] == "success":
                success_count += 1
                print(f"[SUCCESS] Downloaded successfully")
            elif result["status"] == "exists":
                exists_count += 1
                print(f"[EXISTS] File already exists")
            else:
                failed_count += 1
                print(f"[FAILED] {result.get('error', 'Unknown error')}")
            
            # Small delay between downloads
            if result["status"] == "success":
                time.sleep(2)
        
        # Save log and print summary
        self.save_log()
        self.print_summary(success_count, exists_count, failed_count)
    
    def save_log(self):
        """Save download log to file"""
        log_file = self.base_path / f"nal_direct_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        logger.info(f"Log saved to {log_file}")
    
    def print_summary(self, success: int, exists: int, failed: int):
        """Print download summary"""
        print("\n" + "="*60)
        print("NAL DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Total counties: {len(self.counties)}")
        print(f"[SUCCESS] Downloaded: {success}")
        print(f"[EXISTS] Already existed: {exists}")
        print(f"[FAILED] Failed: {failed}")
        print("="*60)
        
        if failed > 0:
            print("\nFailed counties:")
            for r in self.download_log:
                if r["status"] in ["failed", "error"]:
                    print(f"  - {r['county']}: {r.get('error', 'Unknown error')}")


def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue NAL Direct Downloader")
    print("="*60)
    print(f"Base path: {base_path}")
    print(f"Target: NAL 2025P files")
    print("="*60)
    
    # Check if we have proper access
    test_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/"
    try:
        response = requests.head(test_url, timeout=10)
        if response.status_code == 200:
            print("[OK] Connection to Florida Revenue confirmed")
        else:
            print(f"[WARNING] Florida Revenue returned status {response.status_code}")
            print("  Files may need to be downloaded manually")
    except:
        print("[WARNING] Could not verify connection to Florida Revenue")
    
    print("="*60)
    input("Press Enter to start downloading...")
    
    downloader = FloridaNALDirectDownloader(base_path)
    downloader.download_all()


if __name__ == "__main__":
    main()