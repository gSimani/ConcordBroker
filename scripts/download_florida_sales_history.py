"""
Download and Import Complete Florida Sales History from SDF Files
This script downloads Sales Data Files (SDF) for all 67 Florida counties
and imports them into the property_sales_history table.
"""

import os
import csv
import time
import requests
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from supabase import create_client, Client
from tqdm import tqdm
import psycopg2
from io import StringIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_sales_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Florida counties list (all 67 counties)
FLORIDA_COUNTIES = [
    'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
    'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE',
    'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES',
    'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
    'HOLMES', 'INDIAN_RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE',
    'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN', 'MIAMI_DADE',
    'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM_BEACH',
    'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA_ROSA', 'SARASOTA', 'SEMINOLE',
    'ST_JOHNS', 'ST_LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
    'WAKULLA', 'WALTON', 'WASHINGTON'
]

# Base URL for Florida DOR data portal
BASE_URL = "https://floridarevenue.com/property/dataportal/api/download"
DOWNLOAD_DIR = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/SDF_DATA")

def create_download_directory():
    """Create directory structure for downloads"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Download directory created: {DOWNLOAD_DIR}")

def download_county_sdf(county: str) -> Optional[Path]:
    """Download SDF file for a specific county"""
    try:
        # Format county name for URL (replace underscore with space)
        county_formatted = county.replace('_', '%20')

        # Construct download URL
        # Note: This is a placeholder URL - actual URL pattern may differ
        url = f"{BASE_URL}/{county_formatted}/SDF/2025"

        # Download file
        logger.info(f"Downloading SDF data for {county}...")
        response = requests.get(url, stream=True, timeout=300)

        if response.status_code == 200:
            file_path = DOWNLOAD_DIR / f"{county}_SDF.zip"

            # Write file with progress bar
            total_size = int(response.headers.get('content-length', 0))
            with open(file_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=county) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))

            logger.info(f"Downloaded {county} SDF file: {file_path}")
            return file_path
        else:
            logger.warning(f"Failed to download {county}: HTTP {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error downloading {county}: {str(e)}")
        return None

def extract_sdf_file(zip_path: Path) -> Optional[Path]:
    """Extract SDF CSV from zip file"""
    try:
        extract_dir = zip_path.parent / zip_path.stem
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find the SDF CSV file
        csv_files = list(extract_dir.glob("*SDF*.csv")) or list(extract_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Extracted SDF file: {csv_files[0]}")
            return csv_files[0]
        else:
            logger.error(f"No CSV file found in {zip_path}")
            return None

    except Exception as e:
        logger.error(f"Error extracting {zip_path}: {str(e)}")
        return None

def parse_sale_date(year, month, day=1):
    """Parse sale date from year/month/day components"""
    try:
        if year and month:
            year = int(year)
            month = int(month)
            day = int(day) if day else 1

            # Validate values
            if 1900 <= year <= 2025 and 1 <= month <= 12:
                return f"{year:04d}-{month:02d}-{day:02d}"
    except:
        pass
    return None

def parse_quality_code(code):
    """Parse Florida quality code to determine if sale is qualified"""
    qualified_codes = ['01', '02', '03', '04']  # Arms length sales
    return str(code).zfill(2) in qualified_codes if code else False

def process_sdf_record(row: Dict, county: str) -> Optional[Dict]:
    """Process a single SDF record into database format"""
    try:
        # Parse sale price
        sale_price = float(row.get('SALE_PRC1', 0) or 0)

        # Skip if no valid sale price
        if sale_price <= 0:
            return None

        # Parse sale date
        sale_date = parse_sale_date(
            row.get('SALE_YR1'),
            row.get('SALE_MO1'),
            row.get('SALE_DAY1', 1)
        )

        # Skip if no valid sale date
        if not sale_date:
            return None

        # Determine if qualified sale
        quality_code = row.get('VI_CD1', '')
        qualified = parse_quality_code(quality_code)

        return {
            'parcel_id': row.get('PARCEL_ID', '').strip(),
            'county': county.upper(),
            'sale_date': sale_date,
            'sale_year': int(row.get('SALE_YR1', 0) or 0),
            'sale_month': int(row.get('SALE_MO1', 0) or 0),
            'sale_day': int(row.get('SALE_DAY1', 1) or 1),
            'sale_price': sale_price,
            'grantor': row.get('GRANTOR1', '').strip()[:255],
            'grantee': row.get('GRANTEE1', '').strip()[:255],
            'instrument_type': row.get('INST_TYP1', '').strip()[:50],
            'instrument_number': row.get('INST_NUM1', '').strip()[:50],
            'or_book': row.get('OR_BOOK1', '').strip()[:20],
            'or_page': row.get('OR_PAGE1', '').strip()[:20],
            'clerk_no': row.get('CLERK_NO1', '').strip()[:50],
            'sale_qualification': row.get('QUAL1', '').strip()[:50],
            'quality_code': quality_code[:10],
            'vi_code': row.get('VI_CD1', '').strip()[:10],
            'reason': row.get('REASON1', '').strip()[:255],
            'vacant_improved': row.get('VAC_IMP1', '').strip()[:20],
            'property_use': row.get('USE_CD1', '').strip()[:50],
            'qualified_sale': qualified,
            'arms_length': qualified,
            'multi_parcel': row.get('MULTI_PAR1', '') == 'Y',
            'foreclosure': quality_code in ['15', '16'],
            'rea_sale': quality_code == '08',
            'short_sale': quality_code == '09',
            'distressed_sale': quality_code in ['08', '09', '15', '16'],
            'data_source': 'SDF',
            'import_date': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing SDF record: {str(e)}")
        return None

def batch_insert_sales(sales_data: List[Dict], batch_size: int = 1000):
    """Batch insert sales data into Supabase"""
    total_records = len(sales_data)
    inserted = 0
    errors = 0

    logger.info(f"Inserting {total_records} sales records...")

    for i in range(0, total_records, batch_size):
        batch = sales_data[i:i + batch_size]

        try:
            # Insert batch using upsert to handle duplicates
            response = supabase.table('property_sales_history').upsert(
                batch,
                on_conflict='parcel_id,sale_date,sale_price,or_book,or_page'
            ).execute()

            inserted += len(batch)
            logger.info(f"Inserted {inserted}/{total_records} records")

        except Exception as e:
            logger.error(f"Batch insert error: {str(e)}")
            errors += len(batch)

            # Try inserting records individually on batch failure
            for record in batch:
                try:
                    supabase.table('property_sales_history').upsert(record).execute()
                    inserted += 1
                    errors -= 1
                except:
                    pass

    logger.info(f"Insertion complete: {inserted} successful, {errors} errors")
    return inserted, errors

def process_county_sdf(county: str) -> Dict:
    """Complete process for a single county"""
    stats = {
        'county': county,
        'status': 'pending',
        'records_processed': 0,
        'records_inserted': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    try:
        # Download SDF file
        zip_path = download_county_sdf(county)
        if not zip_path:
            stats['status'] = 'download_failed'
            return stats

        # Extract CSV
        csv_path = extract_sdf_file(zip_path)
        if not csv_path:
            stats['status'] = 'extraction_failed'
            return stats

        # Process CSV file
        logger.info(f"Processing {county} SDF data...")
        sales_data = []

        # Read CSV with proper encoding
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)

            for row in reader:
                record = process_sdf_record(row, county)
                if record:
                    sales_data.append(record)
                stats['records_processed'] += 1

                # Insert in batches
                if len(sales_data) >= 5000:
                    inserted, errors = batch_insert_sales(sales_data)
                    stats['records_inserted'] += inserted
                    stats['errors'] += errors
                    sales_data = []

        # Insert remaining records
        if sales_data:
            inserted, errors = batch_insert_sales(sales_data)
            stats['records_inserted'] += inserted
            stats['errors'] += errors

        stats['status'] = 'completed'
        stats['end_time'] = datetime.now()
        stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()

        logger.info(f"Completed {county}: {stats['records_inserted']} records inserted")

        # Clean up files
        try:
            os.remove(zip_path)
            os.remove(csv_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Error processing {county}: {str(e)}")
        stats['status'] = 'error'
        stats['error_message'] = str(e)

    return stats

def main():
    """Main function to orchestrate the download and import process"""
    logger.info("=" * 80)
    logger.info("FLORIDA SALES HISTORY IMPORT - STARTING")
    logger.info("=" * 80)

    # Create download directory
    create_download_directory()

    # Create table in Supabase (execute SQL)
    logger.info("Creating property_sales_history table...")

    # Track overall statistics
    overall_stats = {
        'start_time': datetime.now(),
        'counties_processed': 0,
        'counties_failed': 0,
        'total_records': 0,
        'total_errors': 0,
        'county_stats': []
    }

    # Process counties with concurrent downloads (limited concurrency)
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all counties for processing
        future_to_county = {
            executor.submit(process_county_sdf, county): county
            for county in FLORIDA_COUNTIES[:5]  # Start with first 5 counties as test
        }

        # Process completed counties
        for future in as_completed(future_to_county):
            county = future_to_county[future]
            try:
                stats = future.result()
                overall_stats['county_stats'].append(stats)

                if stats['status'] == 'completed':
                    overall_stats['counties_processed'] += 1
                    overall_stats['total_records'] += stats['records_inserted']
                    overall_stats['total_errors'] += stats['errors']
                else:
                    overall_stats['counties_failed'] += 1

                # Log progress
                progress = (overall_stats['counties_processed'] + overall_stats['counties_failed']) / len(FLORIDA_COUNTIES)
                logger.info(f"Overall progress: {progress:.1%} complete")

            except Exception as e:
                logger.error(f"Failed to process {county}: {str(e)}")
                overall_stats['counties_failed'] += 1

    # Calculate final statistics
    overall_stats['end_time'] = datetime.now()
    overall_stats['duration_hours'] = (overall_stats['end_time'] - overall_stats['start_time']).total_seconds() / 3600

    # Log summary
    logger.info("=" * 80)
    logger.info("FLORIDA SALES HISTORY IMPORT - COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Counties Processed: {overall_stats['counties_processed']}/{len(FLORIDA_COUNTIES)}")
    logger.info(f"Counties Failed: {overall_stats['counties_failed']}")
    logger.info(f"Total Records Imported: {overall_stats['total_records']:,}")
    logger.info(f"Total Errors: {overall_stats['total_errors']:,}")
    logger.info(f"Duration: {overall_stats['duration_hours']:.2f} hours")
    logger.info("=" * 80)

    # Save statistics to file
    import json
    with open('florida_sales_import_stats.json', 'w') as f:
        json.dump(overall_stats, f, indent=2, default=str)

    return overall_stats

if __name__ == "__main__":
    main()