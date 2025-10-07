"""
Download ALL Florida Sales Data Files (SDF) from 2025F (Final) directory
Downloads final 2025 tax roll data from Florida Department of Revenue
"""

import os
import time
import requests
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_sdf_2025f_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# All 67 Florida Counties with their county codes
FLORIDA_COUNTIES = {
    '01': 'ALACHUA',
    '02': 'BAKER',
    '03': 'BAY',
    '04': 'BRADFORD',
    '05': 'BREVARD',
    '06': 'BROWARD',
    '07': 'CALHOUN',
    '08': 'CHARLOTTE',
    '09': 'CITRUS',
    '10': 'CLAY',
    '11': 'COLLIER',
    '12': 'COLUMBIA',
    '13': 'MIAMI-DADE',
    '14': 'DESOTO',
    '15': 'DIXIE',
    '16': 'DUVAL',
    '17': 'ESCAMBIA',
    '18': 'FLAGLER',
    '19': 'FRANKLIN',
    '20': 'GADSDEN',
    '21': 'GILCHRIST',
    '22': 'GLADES',
    '23': 'GULF',
    '24': 'HAMILTON',
    '25': 'HARDEE',
    '26': 'HENDRY',
    '27': 'HERNANDO',
    '28': 'HIGHLANDS',
    '29': 'HILLSBOROUGH',
    '30': 'HOLMES',
    '31': 'INDIAN RIVER',
    '32': 'JACKSON',
    '33': 'JEFFERSON',
    '34': 'LAFAYETTE',
    '35': 'LAKE',
    '36': 'LEE',
    '37': 'LEON',
    '38': 'LEVY',
    '39': 'LIBERTY',
    '40': 'MADISON',
    '41': 'MANATEE',
    '42': 'MARION',
    '43': 'MARTIN',
    '44': 'MONROE',
    '45': 'NASSAU',
    '46': 'OKALOOSA',
    '47': 'OKEECHOBEE',
    '48': 'ORANGE',
    '49': 'OSCEOLA',
    '50': 'PALM BEACH',
    '51': 'PASCO',
    '52': 'PINELLAS',
    '53': 'POLK',
    '54': 'PUTNAM',
    '55': 'SANTA ROSA',
    '56': 'SARASOTA',
    '57': 'SEMINOLE',
    '58': 'ST. JOHNS',
    '59': 'ST. LUCIE',
    '60': 'SUMTER',
    '61': 'SUWANNEE',
    '62': 'TAYLOR',
    '63': 'UNION',
    '64': 'VOLUSIA',
    '65': 'WAKULLA',
    '66': 'WALTON',
    '67': 'WASHINGTON'
}

# Base URL for Florida DOR data portal - 2025F Final data
BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025F"
DOWNLOAD_DIR = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\FLORIDA_SDF_2025F")

def create_download_directory():
    """Create directory structure for downloads"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory ready: {DOWNLOAD_DIR}")

def get_county_code_number(code):
    """Convert county code to proper format for URL"""
    return str(int(code))  # Remove leading zeros

def construct_download_url(county_code, county_name):
    """Construct the download URL for a county's SDF file"""
    # Format: SDF{code}F202501.zip for Final files
    # Example: SDF6F202501.zip for Broward (code 06)
    code_num = get_county_code_number(county_code)
    filename = f"SDF{code_num}F202501.zip"
    url = f"{BASE_URL}/{filename}"
    return url, filename

def download_county_sdf(county_code: str, county_name: str, retry_count: int = 3) -> Optional[Path]:
    """Download SDF file for a specific county with retry logic"""
    url, filename = construct_download_url(county_code, county_name)
    file_path = DOWNLOAD_DIR / county_name.replace(' ', '_') / filename
    file_path.parent.mkdir(exist_ok=True)

    # Skip if already downloaded
    if file_path.exists() and file_path.stat().st_size > 1000:
        logger.info(f"Already downloaded: {county_name} ({filename})")
        return file_path

    for attempt in range(retry_count):
        try:
            logger.info(f"Downloading {county_name} from {url} (Attempt {attempt + 1}/{retry_count})")

            response = requests.get(url, stream=True, timeout=300)

            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))

                with open(file_path, 'wb') as f:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=county_name) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))

                # Verify download
                if file_path.stat().st_size > 1000:
                    logger.info(f"Successfully downloaded {county_name}: {file_path}")
                    return file_path
                else:
                    logger.warning(f"Downloaded file too small for {county_name}")
                    file_path.unlink(missing_ok=True)
            else:
                logger.warning(f"HTTP {response.status_code} for {county_name}")

        except Exception as e:
            logger.error(f"Error downloading {county_name} (Attempt {attempt + 1}): {str(e)}")
            if attempt == retry_count - 1:
                logger.error(f"Failed to download {county_name} after {retry_count} attempts")

        # Delay between retries
        if attempt < retry_count - 1:
            time.sleep(2)

    return None

def extract_sdf_file(zip_path: Path) -> bool:
    """Extract SDF file from zip archive"""
    try:
        extract_dir = zip_path.parent / "SDF"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            logger.info(f"Extracted {zip_path.name} to {extract_dir}")

        return True

    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {str(e)}")
        return False

def download_all_counties(max_workers: int = 3, start_from: str = None):
    """Download SDF files for all Florida counties"""
    logger.info("=" * 80)
    logger.info("DOWNLOADING ALL FLORIDA SDF FILES - 2025F (FINAL)")
    logger.info(f"Total counties: {len(FLORIDA_COUNTIES)}")
    logger.info("=" * 80)

    create_download_directory()

    results = {
        'successful': [],
        'failed': [],
        'stats': {}
    }

    # Filter counties if starting from a specific one
    counties_to_download = FLORIDA_COUNTIES.copy()
    if start_from:
        found = False
        filtered_counties = {}
        for code, name in FLORIDA_COUNTIES.items():
            if name == start_from or found:
                filtered_counties[code] = name
                found = True
        counties_to_download = filtered_counties

    # Download with limited concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_county = {
            executor.submit(download_county_sdf, code, name): (code, name)
            for code, name in counties_to_download.items()
        }

        for future in as_completed(future_to_county):
            code, name = future_to_county[future]
            try:
                file_path = future.result()
                if file_path:
                    results['successful'].append(name)

                    # Extract the zip file
                    if extract_sdf_file(file_path):
                        logger.info(f"{name}: Successfully extracted SDF data")

                else:
                    results['failed'].append(name)

            except Exception as e:
                logger.error(f"Exception processing {name}: {str(e)}")
                results['failed'].append(name)

            # Progress update
            total_processed = len(results['successful']) + len(results['failed'])
            logger.info(f"Progress: {total_processed}/{len(counties_to_download)} counties processed")

            # Brief delay to avoid overwhelming server
            time.sleep(0.5)

    return results

def main():
    """Main execution function"""
    start_time = datetime.now()

    logger.info("Starting Florida SDF 2025F (Final) download process...")
    logger.info(f"Target directory: {DOWNLOAD_DIR}")

    # Download all counties
    results = download_all_counties(max_workers=2)  # Use 2 workers to be gentle on server

    # Summary statistics
    duration = (datetime.now() - start_time).total_seconds() / 60

    logger.info("=" * 80)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Successful downloads: {len(results['successful'])}")
    logger.info(f"Failed downloads: {len(results['failed'])}")
    logger.info(f"Total duration: {duration:.2f} minutes")

    if results['failed']:
        logger.info("\nFailed counties:")
        for county in results['failed']:
            logger.info(f"  - {county}")

    # Save summary to file
    summary_file = DOWNLOAD_DIR / "download_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Florida SDF 2025F Download Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Successful: {len(results['successful'])} counties\n")
        f.write(f"Failed: {len(results['failed'])} counties\n")
        f.write(f"Duration: {duration:.2f} minutes\n")

        if results['successful']:
            f.write(f"\nSuccessfully downloaded:\n")
            for county in sorted(results['successful']):
                f.write(f"  - {county}\n")

        if results['failed']:
            f.write(f"\nFailed to download:\n")
            for county in sorted(results['failed']):
                f.write(f"  - {county}\n")

    logger.info(f"\nSummary saved to: {summary_file}")

    return results

if __name__ == "__main__":
    results = main()