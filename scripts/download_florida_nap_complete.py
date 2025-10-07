"""
Download ALL Florida NAP (Name, Address, Property characteristics) Files from both 2025F and 2025P directories
Downloads final and preliminary property characteristics data from Florida Department of Revenue
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
        logging.FileHandler('florida_nap_complete_download.log'),
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

# Base URLs for Florida DOR data portal
BASE_URL_2025F = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025F"
BASE_URL_2025P = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P"

DOWNLOAD_DIR = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\FLORIDA_NAP_COMPLETE")

def create_download_directory():
    """Create directory structure for downloads"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory ready: {DOWNLOAD_DIR}")

def get_county_code_number(code):
    """Convert county code to proper format for URL"""
    return str(int(code))  # Remove leading zeros

def construct_download_urls(county_code, county_name):
    """Construct the download URLs for a county's NAP files"""
    # Format: NAP{code}F202501.zip for Final files
    # Format: NAP{code}P202501.zip for Preliminary files
    # Example: NAP6F202501.zip for Broward Final (code 06)
    # Example: NAP6P202501.zip for Broward Preliminary (code 06)

    code_num = get_county_code_number(county_code)

    filename_final = f"NAP{code_num}F202501.zip"
    filename_prelim = f"NAP{code_num}P202501.zip"

    url_final = f"{BASE_URL_2025F}/{filename_final}"
    url_prelim = f"{BASE_URL_2025P}/{filename_prelim}"

    return {
        'final': {'url': url_final, 'filename': filename_final},
        'preliminary': {'url': url_prelim, 'filename': filename_prelim}
    }

def download_county_nap(county_code: str, county_name: str, retry_count: int = 3) -> Dict:
    """Download NAP files for a specific county with retry logic"""
    urls = construct_download_urls(county_code, county_name)
    county_dir = DOWNLOAD_DIR / county_name.replace(' ', '_')
    county_dir.mkdir(exist_ok=True)

    results = {'final': None, 'preliminary': None, 'county': county_name}

    for data_type, url_info in urls.items():
        url = url_info['url']
        filename = url_info['filename']
        file_path = county_dir / filename

        # Skip if already downloaded
        if file_path.exists() and file_path.stat().st_size > 1000:
            logger.info(f"Already downloaded: {county_name} {data_type} ({filename})")
            results[data_type] = file_path
            continue

        for attempt in range(retry_count):
            try:
                logger.info(f"Downloading {county_name} {data_type} from {url} (Attempt {attempt + 1}/{retry_count})")

                response = requests.get(url, stream=True, timeout=300)

                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))

                    with open(file_path, 'wb') as f:
                        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"{county_name} {data_type}") as pbar:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))

                    # Verify download
                    if file_path.stat().st_size > 1000:
                        logger.info(f"Successfully downloaded {county_name} {data_type}: {file_path}")
                        results[data_type] = file_path
                        break
                    else:
                        logger.warning(f"Downloaded file too small for {county_name} {data_type}")
                        file_path.unlink(missing_ok=True)
                elif response.status_code == 404:
                    logger.warning(f"File not found (404) for {county_name} {data_type}: {url}")
                    break  # Don't retry 404s
                else:
                    logger.warning(f"HTTP {response.status_code} for {county_name} {data_type}")

            except Exception as e:
                logger.error(f"Error downloading {county_name} {data_type} (Attempt {attempt + 1}): {str(e)}")
                if attempt == retry_count - 1:
                    logger.error(f"Failed to download {county_name} {data_type} after {retry_count} attempts")

            # Delay between retries
            if attempt < retry_count - 1:
                time.sleep(2)

    return results

def extract_nap_file(zip_path: Path, data_type: str) -> bool:
    """Extract NAP file from zip archive"""
    try:
        extract_dir = zip_path.parent / f"NAP_{data_type.upper()}"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            logger.info(f"Extracted {zip_path.name} to {extract_dir}")

        return True

    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {str(e)}")
        return False

def download_all_counties(max_workers: int = 3, start_from: str = None):
    """Download NAP files for all Florida counties"""
    logger.info("==" * 40)
    logger.info("DOWNLOADING ALL FLORIDA NAP FILES - 2025F (FINAL) AND 2025P (PRELIMINARY)")
    logger.info(f"Total counties: {len(FLORIDA_COUNTIES)}")
    logger.info("==" * 40)

    create_download_directory()

    results = {
        'successful_final': [],
        'successful_preliminary': [],
        'failed_final': [],
        'failed_preliminary': [],
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
            executor.submit(download_county_nap, code, name): (code, name)
            for code, name in counties_to_download.items()
        }

        for future in as_completed(future_to_county):
            code, name = future_to_county[future]
            try:
                county_results = future.result()

                # Process final file results
                if county_results['final']:
                    results['successful_final'].append(name)
                    # Extract the zip file
                    if extract_nap_file(county_results['final'], 'final'):
                        logger.info(f"{name}: Successfully extracted NAP Final data")
                else:
                    results['failed_final'].append(name)

                # Process preliminary file results
                if county_results['preliminary']:
                    results['successful_preliminary'].append(name)
                    # Extract the zip file
                    if extract_nap_file(county_results['preliminary'], 'preliminary'):
                        logger.info(f"{name}: Successfully extracted NAP Preliminary data")
                else:
                    results['failed_preliminary'].append(name)

                results['stats'][name] = county_results

            except Exception as e:
                logger.error(f"Exception processing {name}: {str(e)}")
                results['failed_final'].append(name)
                results['failed_preliminary'].append(name)

            # Progress update
            total_processed = len(set(results['successful_final'] + results['failed_final']))
            logger.info(f"Progress: {total_processed}/{len(counties_to_download)} counties processed")

            # Brief delay to avoid overwhelming server
            time.sleep(0.5)

    return results

def main():
    """Main execution function"""
    start_time = datetime.now()

    logger.info("Starting Florida NAP Complete download process...")
    logger.info(f"Target directory: {DOWNLOAD_DIR}")

    # Download all counties
    results = download_all_counties(max_workers=2)  # Use 2 workers to be gentle on server

    # Summary statistics
    duration = (datetime.now() - start_time).total_seconds() / 60

    logger.info("==" * 40)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("==" * 40)
    logger.info(f"Final files - Successful: {len(results['successful_final'])}, Failed: {len(results['failed_final'])}")
    logger.info(f"Preliminary files - Successful: {len(results['successful_preliminary'])}, Failed: {len(results['failed_preliminary'])}")
    logger.info(f"Total duration: {duration:.2f} minutes")

    if results['failed_final']:
        logger.info("\nFailed Final downloads:")
        for county in results['failed_final']:
            logger.info(f"  - {county}")

    if results['failed_preliminary']:
        logger.info("\nFailed Preliminary downloads:")
        for county in results['failed_preliminary']:
            logger.info(f"  - {county}")

    # Save summary to file
    summary_file = DOWNLOAD_DIR / "download_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Florida NAP Complete Download Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Final files - Successful: {len(results['successful_final'])}, Failed: {len(results['failed_final'])}\n")
        f.write(f"Preliminary files - Successful: {len(results['successful_preliminary'])}, Failed: {len(results['failed_preliminary'])}\n")
        f.write(f"Duration: {duration:.2f} minutes\n")

        if results['successful_final']:
            f.write(f"\nSuccessfully downloaded Final:\n")
            for county in sorted(results['successful_final']):
                f.write(f"  - {county}\n")

        if results['successful_preliminary']:
            f.write(f"\nSuccessfully downloaded Preliminary:\n")
            for county in sorted(results['successful_preliminary']):
                f.write(f"  - {county}\n")

        if results['failed_final']:
            f.write(f"\nFailed to download Final:\n")
            for county in sorted(results['failed_final']):
                f.write(f"  - {county}\n")

        if results['failed_preliminary']:
            f.write(f"\nFailed to download Preliminary:\n")
            for county in sorted(results['failed_preliminary']):
                f.write(f"  - {county}\n")

    logger.info(f"\nSummary saved to: {summary_file}")

    return results

if __name__ == "__main__":
    results = main()