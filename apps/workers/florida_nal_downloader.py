"""
Florida Revenue NAL Data Downloader
Downloads NAL (Non Ad Valorem) data files for all Florida counties
"""

import os
import time
import json
import zipfile
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaNALDownloader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P"
        self.download_log = []
        
        # Florida counties list
        self.counties = [
            "ALACHUA", "BAKER", "BAY", "BRADFORD", "BREVARD", "BROWARD",
            "CALHOUN", "CHARLOTTE", "CITRUS", "CLAY", "COLLIER", "COLUMBIA",
            "DESOTO", "DIXIE", "DUVAL", "ESCAMBIA", "FLAGLER", "FRANKLIN",
            "GADSDEN", "GILCHRIST", "GLADES", "GULF", "HAMILTON", "HARDEE",
            "HENDRY", "HERNANDO", "HIGHLANDS", "HILLSBOROUGH", "HOLMES",
            "INDIAN RIVER", "JACKSON", "JEFFERSON", "LAFAYETTE", "LAKE",
            "LEE", "LEON", "LEVY", "LIBERTY", "MADISON", "MANATEE", "MARION",
            "MARTIN", "MIAMI-DADE", "MONROE", "NASSAU", "OKALOOSA", "OKEECHOBEE",
            "ORANGE", "OSCEOLA", "PALM BEACH", "PASCO", "PINELLAS", "POLK",
            "PUTNAM", "SANTA ROSA", "SARASOTA", "SEMINOLE", "ST. JOHNS",
            "ST. LUCIE", "SUMTER", "SUWANNEE", "TAYLOR", "UNION", "VOLUSIA",
            "WAKULLA", "WALTON", "WASHINGTON"
        ]
        
    def get_county_folder(self, county: str) -> Path:
        """Get the NAL folder path for a county"""
        county_folder = self.base_path / county.upper() / "NAL"
        county_folder.mkdir(parents=True, exist_ok=True)
        return county_folder
    
    def build_file_url(self, county: str) -> str:
        """Build the download URL for a county's NAL file"""
        # Format: NAL25P_XX.xlsx where XX is county code
        # Using the pattern from Florida Revenue website
        county_codes = {
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
        
        county_code = county_codes.get(county.upper())
        if not county_code:
            return None
            
        # Try both .xlsx and .zip extensions
        filename = f"NAL25P_{county_code}"
        return f"{self.base_url}/{filename}.xlsx"
    
    def download_file(self, url: str, dest_path: Path) -> bool:
        """Download a file from URL to destination path"""
        try:
            logger.info(f"Downloading from {url}")
            response = requests.get(url, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Successfully downloaded to {dest_path}")
                return True
            else:
                # Try with .zip extension
                zip_url = url.replace('.xlsx', '.zip')
                logger.info(f"Trying .zip extension: {zip_url}")
                response = requests.get(zip_url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    with open(dest_path.with_suffix('.zip'), 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"Successfully downloaded zip to {dest_path.with_suffix('.zip')}")
                    return True
                    
                logger.warning(f"Failed to download (status {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def extract_if_zip(self, file_path: Path) -> bool:
        """Extract zip file if needed"""
        zip_path = file_path.with_suffix('.zip')
        if zip_path.exists():
            try:
                logger.info(f"Extracting {zip_path}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(file_path.parent)
                logger.info(f"Extracted successfully")
                # Remove zip file after extraction
                zip_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                return False
        return True
    
    def download_county(self, county: str) -> Dict:
        """Download NAL file for a specific county"""
        result = {
            "county": county,
            "status": "pending",
            "file_path": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get destination folder
            dest_folder = self.get_county_folder(county)
            
            # Build download URL
            url = self.build_file_url(county)
            if not url:
                result["status"] = "failed"
                result["error"] = "County code not found"
                return result
            
            # Download file
            dest_file = dest_folder / f"NAL25P_{county}.xlsx"
            
            # Check if file already exists
            if dest_file.exists():
                logger.info(f"File already exists for {county}, skipping")
                result["status"] = "exists"
                result["file_path"] = str(dest_file)
                return result
            
            if self.download_file(url, dest_file):
                # Extract if it's a zip
                self.extract_if_zip(dest_file)
                
                # Check if file exists after download/extraction
                if dest_file.exists() or list(dest_folder.glob("*.xlsx")):
                    result["status"] = "success"
                    result["file_path"] = str(dest_file)
                else:
                    result["status"] = "failed"
                    result["error"] = "File not found after download"
            else:
                result["status"] = "failed"
                result["error"] = "Download failed"
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Error processing {county}: {e}")
        
        return result
    
    def download_all(self):
        """Download NAL files for all counties"""
        logger.info(f"Starting download for {len(self.counties)} counties")
        
        for i, county in enumerate(self.counties, 1):
            logger.info(f"Processing {i}/{len(self.counties)}: {county}")
            result = self.download_county(county)
            self.download_log.append(result)
            
            # Small delay to avoid overwhelming the server
            if result["status"] == "success":
                time.sleep(2)
        
        # Save download log
        self.save_log()
        self.print_summary()
    
    def save_log(self):
        """Save download log to file"""
        log_file = self.base_path / f"nal_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        logger.info(f"Log saved to {log_file}")
    
    def print_summary(self):
        """Print download summary"""
        success = sum(1 for r in self.download_log if r["status"] == "success")
        exists = sum(1 for r in self.download_log if r["status"] == "exists")
        failed = sum(1 for r in self.download_log if r["status"] == "failed")
        
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        print(f"Total counties: {len(self.counties)}")
        print(f"Successfully downloaded: {success}")
        print(f"Already existed: {exists}")
        print(f"Failed: {failed}")
        print("="*60)
        
        if failed > 0:
            print("\nFailed counties:")
            for r in self.download_log:
                if r["status"] == "failed":
                    print(f"  - {r['county']}: {r['error']}")


def main():
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Florida Revenue NAL Data Downloader")
    print("="*60)
    print(f"Base path: {base_path}")
    print(f"Target: NAL 2025P files")
    print("="*60)
    
    downloader = FloridaNALDownloader(base_path)
    downloader.download_all()


if __name__ == "__main__":
    main()