"""
Florida NAV (Non Ad Valorem) Dataset Downloader and Processor
Downloads and processes NAV D and NAV N files from Florida Department of Revenue
Based on navlayout.pdf specifications
"""

import os
import requests
import zipfile
import csv
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nav_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NAVDatasetProcessor:
    """Process Florida NAV (Non Ad Valorem) assessment datasets"""

    def __init__(self, base_dir: str = "TEMP/NAV_DATA"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # County codes (11-77 as per Florida DOR specification)
        self.florida_counties = {
            11: "ALACHUA", 12: "BAKER", 13: "BAY", 14: "BRADFORD", 15: "BREVARD",
            16: "BROWARD", 17: "CALHOUN", 18: "CHARLOTTE", 19: "CITRUS", 20: "CLAY",
            21: "COLLIER", 22: "COLUMBIA", 23: "MIAMI-DADE", 24: "DESOTO", 25: "DIXIE",
            26: "DUVAL", 27: "ESCAMBIA", 28: "FLAGLER", 29: "FRANKLIN", 30: "GADSDEN",
            31: "GILCHRIST", 32: "GLADES", 33: "GULF", 34: "HAMILTON", 35: "HARDEE",
            36: "HENDRY", 37: "HERNANDO", 38: "HIGHLANDS", 39: "HILLSBOROUGH", 40: "HOLMES",
            41: "INDIAN RIVER", 42: "JACKSON", 43: "JEFFERSON", 44: "LAFAYETTE", 45: "LAKE",
            46: "LEE", 47: "LEON", 48: "LEVY", 49: "LIBERTY", 50: "MADISON",
            51: "MANATEE", 52: "MARION", 53: "MARTIN", 54: "MONROE", 55: "NASSAU",
            56: "OKALOOSA", 57: "OKEECHOBEE", 58: "ORANGE", 59: "OSCEOLA", 60: "PALM BEACH",
            61: "PASCO", 62: "PINELLAS", 63: "POLK", 64: "PUTNAM", 65: "ST. JOHNS",
            66: "ST. LUCIE", 67: "SANTA ROSA", 68: "SARASOTA", 69: "SEMINOLE", 70: "SUMTER",
            71: "SUWANNEE", 72: "TAYLOR", 73: "UNION", 74: "VOLUSIA", 75: "WAKULLA",
            76: "WALTON", 77: "WASHINGTON"
        }

        # Base URLs for direct NAV dataset downloads
        self.base_urls = {
            'D': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20D',
            'N': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20N'
        }

    def download_file(self, url: str, local_path: Path) -> bool:
        """Download a file with retry logic"""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(url, stream=True, timeout=300)
                response.raise_for_status()

                # Create directory if it doesn't exist
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Download with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\rProgress: {progress:.1f}%", end='', flush=True)

                print()  # New line after progress
                logger.info(f"Successfully downloaded {local_path.name}")
                return True

            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to download {url} after {max_retries} attempts")
                    return False

        return False

    def discover_nav_files(self, nav_type: str) -> List[str]:
        """Discover available NAV files for a given type (D or N)"""
        discovered_files = []

        # Generate expected file patterns based on county codes
        for county_code, county_name in self.florida_counties.items():
            # File naming pattern: NAV[D|N][county][year][submission].TXT
            # Example: NAVD112401.TXT (NAV D, county 11, year 24, submission 01)
            for submission in ['01', '02', '03']:  # Multiple submissions possible
                filename = f"NAV{nav_type}{county_code:02d}2401.TXT"
                file_url = f"{self.base_urls[nav_type]}/{filename}"
                discovered_files.append((county_code, county_name, filename, file_url))

        return discovered_files

    def validate_nav_record(self, record: List[str], table_type: str) -> bool:
        """Validate NAV record according to specifications"""
        if table_type == 'N':
            # Table N should have 8 fields
            if len(record) != 8:
                return False

            # Field 1: Roll Type should be 'N'
            if record[0] != 'N':
                return False

            # Field 2: County number should be 2 digits (11-77)
            try:
                county = int(record[1])
                if county < 11 or county > 77:
                    return False
            except ValueError:
                return False

            # Field 5: Tax year should be 4 digits
            try:
                year = int(record[4])
                if year < 2020 or year > 2030:  # Reasonable range
                    return False
            except ValueError:
                return False

        elif table_type == 'D':
            # Table D should have 8 fields
            if len(record) != 8:
                return False

            # Field D1: Record Type should be 'D'
            if record[0] != 'D':
                return False

            # Field D2: County number validation
            try:
                county = int(record[1])
                if county < 11 or county > 77:
                    return False
            except ValueError:
                return False

        return True

    def process_nav_file(self, file_path: Path, table_type: str) -> Dict[str, Any]:
        """Process a single NAV file and return statistics"""
        stats = {
            'filename': file_path.name,
            'table_type': table_type,
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'unique_parcels': set(),
            'total_assessments': 0,
            'county_code': None,
            'processing_errors': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                csv_reader = csv.reader(f)

                for line_num, record in enumerate(csv_reader, 1):
                    stats['total_records'] += 1

                    if self.validate_nav_record(record, table_type):
                        stats['valid_records'] += 1

                        # Extract county code
                        if stats['county_code'] is None:
                            stats['county_code'] = int(record[1])

                        # Add parcel to unique set
                        parcel_id = record[2]  # Field 3/D3: PA Parcel Number
                        stats['unique_parcels'].add(parcel_id)

                        # Track assessment amounts
                        if table_type == 'N':
                            try:
                                total_assess = float(record[5])  # Field 6: Total assessments
                                stats['total_assessments'] += total_assess
                            except (ValueError, IndexError):
                                pass
                        elif table_type == 'D':
                            try:
                                assess_amount = float(record[6])  # Field D7: Assessment amount
                                stats['total_assessments'] += assess_amount
                            except (ValueError, IndexError):
                                pass
                    else:
                        stats['invalid_records'] += 1
                        if len(stats['processing_errors']) < 10:  # Limit error collection
                            stats['processing_errors'].append(f"Line {line_num}: Invalid record format")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            stats['processing_errors'].append(f"File processing error: {e}")

        # Convert set to count
        stats['unique_parcels'] = len(stats['unique_parcels'])

        return stats

    def download_and_process_nav_datasets(self):
        """Download and process all available NAV datasets"""
        logger.info("Starting NAV dataset download and processing")

        results = {
            'download_summary': {
                'D': {'attempted': 0, 'successful': 0, 'failed': 0},
                'N': {'attempted': 0, 'successful': 0, 'failed': 0}
            },
            'processing_summary': {
                'D': [],
                'N': []
            },
            'total_statistics': {
                'D': {'records': 0, 'parcels': 0, 'assessments': 0},
                'N': {'records': 0, 'parcels': 0, 'assessments': 0}
            }
        }

        # Process both NAV D and NAV N datasets
        for nav_type in ['D', 'N']:
            logger.info(f"Processing NAV {nav_type} dataset")

            # Create type-specific directory
            type_dir = self.base_dir / f"NAV_{nav_type}"
            type_dir.mkdir(exist_ok=True)

            # Discover files for this type
            discovered_files = self.discover_nav_files(nav_type)

            for county_code, county_name, filename, file_url in discovered_files:
                results['download_summary'][nav_type]['attempted'] += 1

                local_path = type_dir / filename

                # Skip if file already exists and is not empty
                if local_path.exists() and local_path.stat().st_size > 0:
                    logger.info(f"File {filename} already exists, skipping download")
                    download_success = True
                else:
                    download_success = self.download_file(file_url, local_path)

                if download_success and local_path.exists():
                    results['download_summary'][nav_type]['successful'] += 1

                    # Process the file
                    logger.info(f"Processing {filename}")
                    stats = self.process_nav_file(local_path, nav_type)
                    stats['county_name'] = county_name
                    results['processing_summary'][nav_type].append(stats)

                    # Update totals
                    results['total_statistics'][nav_type]['records'] += stats['valid_records']
                    results['total_statistics'][nav_type]['parcels'] += stats['unique_parcels']
                    results['total_statistics'][nav_type]['assessments'] += stats['total_assessments']

                else:
                    results['download_summary'][nav_type]['failed'] += 1
                    logger.warning(f"Failed to download or process {filename}")

                # Small delay between downloads to be respectful
                time.sleep(1)

        # Generate summary report
        self.generate_summary_report(results)

        return results

    def generate_summary_report(self, results: Dict[str, Any]):
        """Generate a comprehensive summary report"""
        report_path = self.base_dir / "NAV_Processing_Report.txt"

        with open(report_path, 'w') as f:
            f.write("Florida NAV Dataset Processing Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Download summary
            f.write("DOWNLOAD SUMMARY\n")
            f.write("-" * 20 + "\n")
            for nav_type in ['D', 'N']:
                summary = results['download_summary'][nav_type]
                f.write(f"NAV {nav_type} Files:\n")
                f.write(f"  Attempted: {summary['attempted']}\n")
                f.write(f"  Successful: {summary['successful']}\n")
                f.write(f"  Failed: {summary['failed']}\n")
                f.write(f"  Success Rate: {(summary['successful']/summary['attempted']*100):.1f}%\n\n")

            # Processing statistics
            f.write("PROCESSING STATISTICS\n")
            f.write("-" * 25 + "\n")
            for nav_type in ['D', 'N']:
                totals = results['total_statistics'][nav_type]
                f.write(f"NAV {nav_type} Dataset Totals:\n")
                f.write(f"  Total Valid Records: {totals['records']:,}\n")
                f.write(f"  Unique Parcels: {totals['parcels']:,}\n")
                f.write(f"  Total Assessment Value: ${totals['assessments']:,.2f}\n\n")

            # Detailed file statistics
            f.write("DETAILED FILE STATISTICS\n")
            f.write("-" * 30 + "\n")
            for nav_type in ['D', 'N']:
                f.write(f"\nNAV {nav_type} Files:\n")
                for stats in results['processing_summary'][nav_type]:
                    if stats['valid_records'] > 0:  # Only show files with data
                        f.write(f"  {stats['filename']} ({stats['county_name']}):\n")
                        f.write(f"    Valid Records: {stats['valid_records']:,}\n")
                        f.write(f"    Unique Parcels: {stats['unique_parcels']:,}\n")
                        f.write(f"    Assessment Total: ${stats['total_assessments']:,.2f}\n")
                        if stats['processing_errors']:
                            f.write(f"    Errors: {len(stats['processing_errors'])}\n")
                        f.write("\n")

        logger.info(f"Summary report saved to {report_path}")

def main():
    """Main execution function"""
    logger.info("Starting Florida NAV Dataset Download and Processing")

    # Initialize processor
    processor = NAVDatasetProcessor()

    # Download and process all datasets
    results = processor.download_and_process_nav_datasets()

    # Print final summary
    print("\n" + "="*60)
    print("FLORIDA NAV DATASET PROCESSING COMPLETE")
    print("="*60)

    for nav_type in ['D', 'N']:
        totals = results['total_statistics'][nav_type]
        download_stats = results['download_summary'][nav_type]

        print(f"\nNAV {nav_type} Dataset:")
        print(f"  Files Downloaded: {download_stats['successful']}/{download_stats['attempted']}")
        print(f"  Total Records: {totals['records']:,}")
        print(f"  Unique Parcels: {totals['parcels']:,}")
        print(f"  Total Assessments: ${totals['assessments']:,.2f}")

    print(f"\nDetailed report saved to: TEMP/NAV_DATA/NAV_Processing_Report.txt")
    print(f"Log file saved to: nav_download.log")

if __name__ == "__main__":
    main()