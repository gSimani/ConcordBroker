"""
Download ALL Florida Sales Data Files (SDF) from Florida Department of Revenue
Downloads directly from the official data portal without row limitations
"""

import os
import time
import requests
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from typing import List, Dict, Optional
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_sdf_download.log'),
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

# Base URL for Florida DOR data portal - 2025 Preliminary data
BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P"
DOWNLOAD_DIR = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\FLORIDA_SDF_2025")

def create_download_directory():
    """Create directory structure for downloads"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory ready: {DOWNLOAD_DIR}")

def get_county_code_number(code):
    """Convert county code to proper format for URL"""
    return str(int(code))  # Remove leading zeros

def construct_download_url(county_code, county_name):
    """Construct the download URL for a county's SDF file"""
    # Format: SDF{code}P202501.zip
    # Example: SDF6P202501.zip for Broward (code 06)
    code_num = get_county_code_number(county_code)
    filename = f"SDF{code_num}P202501.zip"
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

    return None

def extract_and_preview_sdf(zip_path: Path) -> Dict:
    """Extract SDF file and preview its contents"""
    try:
        extract_dir = zip_path.parent / zip_path.stem
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find CSV/TXT files
        data_files = list(extract_dir.glob("*.csv")) + list(extract_dir.glob("*.txt"))

        if not data_files:
            logger.error(f"No data files found in {zip_path}")
            return {"status": "error", "message": "No data files found"}

        data_file = data_files[0]
        logger.info(f"Found data file: {data_file}")

        # Read first few rows to preview
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(data_file, nrows=5, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            # Get file stats
            total_rows = sum(1 for _ in open(data_file, 'r', encoding=encoding)) - 1  # Subtract header

            return {
                "status": "success",
                "file": str(data_file),
                "columns": list(df.columns),
                "sample_rows": df.to_dict('records'),
                "total_rows": total_rows,
                "file_size_mb": data_file.stat().st_size / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"Error reading data file: {str(e)}")
            return {"status": "error", "message": str(e)}

    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {str(e)}")
        return {"status": "error", "message": str(e)}

def download_all_counties(max_workers: int = 3):
    """Download SDF files for all Florida counties"""
    logger.info("=" * 80)
    logger.info("DOWNLOADING ALL FLORIDA SDF FILES")
    logger.info(f"Total counties: {len(FLORIDA_COUNTIES)}")
    logger.info("=" * 80)

    create_download_directory()

    results = {
        'successful': [],
        'failed': [],
        'stats': {}
    }

    # Download with limited concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_county = {
            executor.submit(download_county_sdf, code, name): (code, name)
            for code, name in FLORIDA_COUNTIES.items()
        }

        for future in as_completed(future_to_county):
            code, name = future_to_county[future]
            try:
                file_path = future.result()
                if file_path:
                    results['successful'].append(name)

                    # Preview the data
                    preview = extract_and_preview_sdf(file_path)
                    results['stats'][name] = preview

                    if preview['status'] == 'success':
                        logger.info(f"{name}: {preview['total_rows']:,} records, {preview['file_size_mb']:.1f} MB")
                else:
                    results['failed'].append(name)

            except Exception as e:
                logger.error(f"Exception processing {name}: {str(e)}")
                results['failed'].append(name)

            # Progress update
            total_processed = len(results['successful']) + len(results['failed'])
            logger.info(f"Progress: {total_processed}/{len(FLORIDA_COUNTIES)} counties processed")

    return results

def main():
    """Main execution function"""
    start_time = datetime.now()

    logger.info("Starting Florida SDF download process...")
    logger.info(f"Target directory: {DOWNLOAD_DIR}")

    # Download all counties
    results = download_all_counties(max_workers=3)

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

    # Calculate total records
    total_records = 0
    total_size_mb = 0
    for county, stats in results['stats'].items():
        if stats['status'] == 'success':
            total_records += stats['total_rows']
            total_size_mb += stats['file_size_mb']

    logger.info(f"\nTotal sales records: {total_records:,}")
    logger.info(f"Total data size: {total_size_mb:.1f} MB")

    # Save summary to file
    summary_file = DOWNLOAD_DIR / "download_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Florida SDF Download Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Successful: {len(results['successful'])} counties\n")
        f.write(f"Failed: {len(results['failed'])} counties\n")
        f.write(f"Total Records: {total_records:,}\n")
        f.write(f"Total Size: {total_size_mb:.1f} MB\n")
        f.write(f"\nCounty Details:\n")
        for county, stats in results['stats'].items():
            if stats['status'] == 'success':
                f.write(f"  {county}: {stats['total_rows']:,} records\n")

    logger.info(f"\nSummary saved to: {summary_file}")

    return results

if __name__ == "__main__":
    results = main()