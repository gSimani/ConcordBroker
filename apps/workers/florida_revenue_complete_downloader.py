"""
Florida Revenue Complete Data Downloader
Downloads NAL, NAP, and SDF files for all Florida counties
"""

import os
import time
import json
import zipfile
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaRevenueDownloader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Data types to download
        self.data_types = ['NAL', 'NAP', 'SDF']
        
        # Base URLs for each data type
        self.base_urls = {
            'NAL': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/',
            'NAP': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P/',
            'SDF': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P/'
        }
        
        # Florida counties
        self.counties = [
            "Alachua", "Baker", "Bay", "Bradford", "Brevard", "Broward",
            "Calhoun", "Charlotte", "Citrus", "Clay", "Collier", "Columbia",
            "DeSoto", "Dixie", "Duval", "Escambia", "Flagler", "Franklin",
            "Gadsden", "Gilchrist", "Glades", "Gulf", "Hamilton", "Hardee",
            "Hendry", "Hernando", "Highlands", "Hillsborough", "Holmes",
            "Indian River", "Jackson", "Jefferson", "Lafayette", "Lake",
            "Lee", "Leon", "Levy", "Liberty", "Madison", "Manatee", "Marion",
            "Martin", "Miami-Dade", "Monroe", "Nassau", "Okaloosa", "Okeechobee",
            "Orange", "Osceola", "Palm Beach", "Pasco", "Pinellas", "Polk",
            "Putnam", "St. Johns", "St. Lucie", "Santa Rosa", "Sarasota", 
            "Seminole", "Sumter", "Suwannee", "Taylor", "Union", "Volusia",
            "Wakulla", "Walton", "Washington"
        ]
        
        self.download_log = []
    
    def get_county_folder(self, county: str, data_type: str) -> Path:
        """Get the folder path for a county and data type"""
        # Normalize county name for folder (remove spaces, dots)
        folder_name = county.upper().replace(" ", "_").replace(".", "")
        # Handle special cases
        if folder_name == "DESOTO":
            folder_name = "DESOTO"
        elif folder_name == "MIAMI-DADE":
            folder_name = "MIAMI-DADE"
        elif folder_name == "ST_JOHNS":
            folder_name = "ST. JOHNS"
        elif folder_name == "ST_LUCIE":
            folder_name = "ST. LUCIE"
        elif folder_name == "SANTA_ROSA":
            folder_name = "SANTA ROSA"
        elif folder_name == "INDIAN_RIVER":
            folder_name = "INDIAN RIVER"
        elif folder_name == "PALM_BEACH":
            folder_name = "PALM BEACH"
        
        county_folder = self.base_path / folder_name / data_type
        county_folder.mkdir(parents=True, exist_ok=True)
        return county_folder
    
    def build_file_url(self, county: str, data_type: str) -> list:
        """Build possible download URLs for a county file"""
        base_url = self.base_urls[data_type]
        
        # Try different naming patterns Florida Revenue might use
        patterns = [
            f"{county}%2011%20Preliminary%20{data_type}%202025.zip",
            f"{county}%2012%20Preliminary%20{data_type}%202025.zip",
            f"{county}%20Preliminary%20{data_type}%202025.zip",
            f"{county}%20{data_type}%202025.zip",
            f"{county}%20{data_type}%2025P.zip",
            f"{county}_{data_type}_2025.zip",
            f"{county}_{data_type}_2025P.zip"
        ]
        
        # Handle special county names
        if county == "DeSoto":
            patterns.append(f"Desoto%2011%20Preliminary%20{data_type}%202025.zip")
            patterns.append(f"DESOTO%2011%20Preliminary%20{data_type}%202025.zip")
        elif county == "Miami-Dade":
            patterns.append(f"Miami%20Dade%2011%20Preliminary%20{data_type}%202025.zip")
            patterns.append(f"MiamiDade%2011%20Preliminary%20{data_type}%202025.zip")
        elif "St." in county or "St " in county:
            alt_name = county.replace("St.", "Saint").replace("St ", "Saint ")
            patterns.append(f"{alt_name}%2011%20Preliminary%20{data_type}%202025.zip")
        
        return [base_url + pattern for pattern in patterns]
    
    def download_file(self, url: str, dest_path: Path) -> bool:
        """Download a file from URL"""
        try:
            logger.info(f"Trying URL: {unquote(url)}")
            response = self.session.get(url, stream=True, timeout=30)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and downloaded % (1024 * 1024) == 0:  # Progress every MB
                                progress = (downloaded / total_size) * 100
                                print(f"\r  Downloading: {progress:.1f}%", end='')
                
                print()  # New line after progress
                logger.info(f"Successfully downloaded {dest_path.name}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.debug(f"Download failed: {e}")
            return False
    
    def extract_zip(self, zip_path: Path) -> bool:
        """Extract zip file and delete it"""
        try:
            logger.info(f"Extracting {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(zip_path.parent)
            
            # Delete the zip file after extraction
            zip_path.unlink()
            logger.info("Extraction complete, zip file removed")
            return True
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return False
    
    def download_county_data(self, county: str, data_type: str) -> dict:
        """Download data file for a specific county and type"""
        result = {
            "county": county,
            "data_type": data_type,
            "status": "pending",
            "file_path": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get destination folder
            dest_folder = self.get_county_folder(county, data_type)
            
            # Check if file already exists
            existing_files = list(dest_folder.glob("*.xlsx")) + list(dest_folder.glob("*.xls"))
            if existing_files:
                logger.info(f"File already exists for {county}/{data_type}: {existing_files[0].name}")
                result["status"] = "exists"
                result["file_path"] = str(existing_files[0])
                return result
            
            # Try different URL patterns
            urls = self.build_file_url(county, data_type)
            
            for url in urls:
                zip_path = dest_folder / f"{county}_{data_type}_2025.zip"
                
                if self.download_file(url, zip_path):
                    # Extract the zip file
                    if self.extract_zip(zip_path):
                        # Check for extracted Excel file
                        excel_files = list(dest_folder.glob("*.xlsx")) + list(dest_folder.glob("*.xls"))
                        if excel_files:
                            result["status"] = "success"
                            result["file_path"] = str(excel_files[0])
                            return result
                    else:
                        result["status"] = "extraction_failed"
                        return result
            
            # If no pattern worked
            result["status"] = "failed"
            result["error"] = "No valid download URL found"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error processing {county}/{data_type}: {e}")
        
        return result
    
    def download_all(self):
        """Download all data types for all counties"""
        total_files = len(self.counties) * len(self.data_types)
        logger.info(f"Starting download for {total_files} files ({len(self.counties)} counties x {len(self.data_types)} data types)")
        
        for data_type in self.data_types:
            print(f"\n{'='*60}")
            print(f"Downloading {data_type} files")
            print(f"{'='*60}")
            
            success_count = 0
            exists_count = 0
            failed_count = 0
            
            for i, county in enumerate(self.counties, 1):
                print(f"\n[{i}/{len(self.counties)}] {county} - {data_type}")
                print("-"*40)
                
                result = self.download_county_data(county, data_type)
                self.download_log.append(result)
                
                if result["status"] == "success":
                    success_count += 1
                    print(f"[SUCCESS] Downloaded and extracted")
                elif result["status"] == "exists":
                    exists_count += 1
                    print(f"[EXISTS] File already present")
                else:
                    failed_count += 1
                    print(f"[FAILED] {result.get('error', 'Download failed')}")
                
                # Small delay between downloads
                if result["status"] == "success":
                    time.sleep(1)
            
            print(f"\n{data_type} Summary:")
            print(f"  Downloaded: {success_count}")
            print(f"  Already existed: {exists_count}")
            print(f"  Failed: {failed_count}")
        
        # Save log and print final summary
        self.save_log()
        self.print_final_summary()
    
    def save_log(self):
        """Save download log to file"""
        log_file = self.base_path / f"florida_revenue_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        logger.info(f"Log saved to {log_file}")
    
    def print_final_summary(self):
        """Print final download summary"""
        print("\n" + "="*60)
        print("FINAL DOWNLOAD SUMMARY")
        print("="*60)
        
        for data_type in self.data_types:
            type_results = [r for r in self.download_log if r["data_type"] == data_type]
            success = sum(1 for r in type_results if r["status"] == "success")
            exists = sum(1 for r in type_results if r["status"] == "exists")
            failed = sum(1 for r in type_results if r["status"] in ["failed", "error", "extraction_failed"])
            
            print(f"\n{data_type}:")
            print(f"  Total counties: {len(self.counties)}")
            print(f"  [SUCCESS] Downloaded: {success}")
            print(f"  [EXISTS] Already had: {exists}")
            print(f"  [FAILED] Failed: {failed}")
            
            if failed > 0:
                print(f"\n  Failed counties for {data_type}:")
                for r in type_results:
                    if r["status"] in ["failed", "error", "extraction_failed"]:
                        print(f"    - {r['county']}: {r.get('error', r['status'])}")
        
        print("="*60)


def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue Complete Data Downloader")
    print("="*60)
    print(f"Base path: {base_path}")
    print(f"Data types: NAL, NAP, SDF")
    print(f"Year: 2025P")
    print("="*60)
    
    downloader = FloridaRevenueDownloader(base_path)
    downloader.download_all()


if __name__ == "__main__":
    main()