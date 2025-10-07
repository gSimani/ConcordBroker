"""
Process all local NAL (Name, Address, Legal description) files and update Supabase florida_parcels table
This script processes existing NAL CSV files and enhances property data with comprehensive details
"""

import os
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client
import time
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_local_nal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Path to NAL data
NAL_BASE_PATH = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

def test_database_connection():
    """Test database connection"""
    try:
        result = supabase.table('florida_parcels').select('count', count='exact').limit(1).execute()
        logger.info(f"Database connected. Current records: {result.count}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None or value == '':
        return default
    try:
        # Remove dollar signs and commas
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert value to integer"""
    if value is None or value == '':
        return default
    try:
        # Remove dollar signs and commas first
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '')
        # Convert to float first, then to int to handle decimals
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_string(value, max_length=None):
    """Safely convert value to string and truncate if needed"""
    if value is None:
        return ''
    str_value = str(value).strip()
    if max_length and len(str_value) > max_length:
        return str_value[:max_length]
    return str_value

def process_nal_record(row: Dict, county_name: str, county_no: str) -> Optional[Dict]:
    """Process a single NAL record into database format - only existing columns"""
    try:
        # Get parcel ID
        parcel_id = safe_string(row.get('PARCEL_ID', '')).strip()
        if not parcel_id:
            return None

        # Only update fields that exist in the current florida_parcels table
        nal_data = {
            'parcel_id': parcel_id,
            'county': county_name.upper(),
            'year': safe_int(row.get('ASMNT_YR', 2025)),

            # Enhanced value fields from NAL (existing columns)
            'just_value': safe_int(row.get('JV', 0)),
            'assessed_value': safe_int(row.get('AV_SD', 0)) + safe_int(row.get('AV_NSD', 0)),  # Total assessed value
            'taxable_value': safe_int(row.get('TV_SD', 0)) + safe_int(row.get('TV_NSD', 0)),  # Total taxable value
            'land_value': safe_int(row.get('LND_VAL', 0)),
            'building_value': safe_int(row.get('JV', 0)) - safe_int(row.get('LND_VAL', 0)) if safe_int(row.get('JV', 0)) > safe_int(row.get('LND_VAL', 0)) else 0,

            # Property characteristics (existing columns)
            'year_built': safe_int(row.get('ACT_YR_BLT', 0)) or safe_int(row.get('EFF_YR_BLT', 0)),
            'total_living_area': safe_int(row.get('TOT_LVG_AREA', 0)),
            'land_sqft': safe_int(row.get('LND_SQFOOT', 0)),

            # Enhanced owner information from NAL (existing columns)
            'owner_name': safe_string(row.get('OWN_NAME', ''), 255),
            'owner_addr1': safe_string(row.get('OWN_ADDR1', ''), 255),
            'owner_city': safe_string(row.get('OWN_CITY', ''), 100),
            'owner_state': safe_string(row.get('OWN_STATE', ''), 2)[:2],  # Ensure 2 chars max
            'owner_zip': safe_string(row.get('OWN_ZIPCD', ''), 10),

            # Physical address (existing columns)
            'phy_addr1': safe_string(row.get('PHY_ADDR1', ''), 255),
            'phy_city': safe_string(row.get('PHY_CITY', ''), 100),
            'phy_zipcd': safe_string(row.get('PHY_ZIPCD', ''), 10),

            # Update metadata (existing columns)
            'data_source': 'NAL_Enhanced',
            'import_date': datetime.now().isoformat(),
            'update_date': datetime.now().isoformat()
        }

        return nal_data

    except Exception as e:
        logger.error(f"Error processing NAL record: {str(e)}")
        return None

def update_parcels_with_nal(nal_data: List[Dict], batch_size: int = 500):
    """Update florida_parcels records with NAL data using upsert"""
    if not nal_data:
        return 0, 0

    updated = 0
    errors = 0

    try:
        # Process in batches
        for i in range(0, len(nal_data), batch_size):
            batch = nal_data[i:i + batch_size]

            # Update records using upsert
            try:
                response = supabase.table('florida_parcels').upsert(
                    batch,
                    on_conflict='parcel_id,county,year'
                ).execute()
                updated += len(batch)
                logger.info(f"Updated batch of {len(batch)} records")

            except Exception as e:
                logger.error(f"Batch update error: {str(e)}")
                errors += len(batch)

                # Try updating records individually on batch failure
                for record in batch:
                    try:
                        supabase.table('florida_parcels').upsert(
                            record,
                            on_conflict='parcel_id,county,year'
                        ).execute()
                        updated += 1
                        errors -= 1
                    except Exception as ind_error:
                        logger.debug(f"Individual update failed for {record.get('parcel_id')}: {str(ind_error)}")

        return updated, errors

    except Exception as e:
        logger.error(f"Bulk update error: {str(e)}")
        return 0, len(nal_data)

def process_county_nal(county_path: Path) -> Dict:
    """Process all NAL files for a county"""
    county_name = county_path.name
    stats = {
        'county': county_name,
        'files_processed': 0,
        'records_processed': 0,
        'records_updated': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    # Find NAL CSV files
    nal_files = list(county_path.glob("NAL/*.csv"))
    if not nal_files:
        nal_files = list(county_path.glob("NAL/*.txt"))

    if not nal_files:
        logger.warning(f"No NAL files found for {county_name}")
        return stats

    for nal_file in nal_files:
        logger.info(f"Processing {county_name}: {nal_file.name}")

        nal_batch = []

        try:
            # Detect encoding
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(nal_file, 'r', encoding=encoding) as f:
                        # Detect delimiter
                        first_line = f.readline()
                        delimiter = '\t' if '\t' in first_line else ','
                        f.seek(0)

                        reader = csv.DictReader(f, delimiter=delimiter)

                        for row_num, row in enumerate(reader):
                            # Extract county number from CO_NO field
                            county_no = row.get('CO_NO', '').strip()

                            # Process record
                            nal_data = process_nal_record(row, county_name, county_no)
                            if nal_data:
                                nal_batch.append(nal_data)

                            stats['records_processed'] += 1

                            # Update in batches
                            if len(nal_batch) >= 1000:
                                updated, errors = update_parcels_with_nal(nal_batch)
                                stats['records_updated'] += updated
                                stats['errors'] += errors
                                nal_batch = []

                            # Progress logging
                            if row_num > 0 and row_num % 10000 == 0:
                                logger.info(f"{county_name}: Processed {row_num:,} records, updated {stats['records_updated']:,} parcels")

                    break  # Successfully read file
                except UnicodeDecodeError:
                    continue

            # Update remaining records
            if nal_batch:
                updated, errors = update_parcels_with_nal(nal_batch)
                stats['records_updated'] += updated
                stats['errors'] += errors

            stats['files_processed'] += 1

        except Exception as e:
            logger.error(f"Error processing {nal_file}: {str(e)}")
            stats['errors'] += 1

    stats['end_time'] = datetime.now()
    stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()

    logger.info(f"Completed {county_name}: {stats['records_updated']:,} parcels updated from {stats['records_processed']:,} records")

    return stats

def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("PROCESSING LOCAL FLORIDA NAL FILES TO ENHANCE PARCEL DATA")
    logger.info("=" * 80)

    # Test database connection
    if not test_database_connection():
        logger.error("Failed to connect to database")
        return

    # Find all county directories
    county_dirs = [d for d in NAL_BASE_PATH.iterdir() if d.is_dir()]
    logger.info(f"Found {len(county_dirs)} county directories")

    overall_stats = {
        'start_time': datetime.now(),
        'counties_processed': 0,
        'total_records': 0,
        'total_records_updated': 0,
        'total_errors': 0,
        'county_stats': []
    }

    # Process each county
    for county_path in tqdm(county_dirs, desc="Processing counties"):
        logger.info(f"\nProcessing {county_path.name}...")
        stats = process_county_nal(county_path)

        overall_stats['county_stats'].append(stats)
        overall_stats['counties_processed'] += 1
        overall_stats['total_records'] += stats['records_processed']
        overall_stats['total_records_updated'] += stats['records_updated']
        overall_stats['total_errors'] += stats['errors']

    # Calculate final statistics
    overall_stats['end_time'] = datetime.now()
    overall_stats['duration_minutes'] = (overall_stats['end_time'] - overall_stats['start_time']).total_seconds() / 60

    # Log summary
    logger.info("=" * 80)
    logger.info("NAL PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Counties Processed: {overall_stats['counties_processed']}")
    logger.info(f"Total Records Processed: {overall_stats['total_records']:,}")
    logger.info(f"Total Parcels Updated: {overall_stats['total_records_updated']:,}")
    logger.info(f"Total Errors: {overall_stats['total_errors']:,}")
    logger.info(f"Duration: {overall_stats['duration_minutes']:.2f} minutes")
    logger.info("=" * 80)

    # Save summary
    summary_file = Path("local_nal_processing_summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"Florida NAL Processing Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Counties Processed: {overall_stats['counties_processed']}\n")
        f.write(f"Total Records: {overall_stats['total_records']:,}\n")
        f.write(f"Total Parcels Updated: {overall_stats['total_records_updated']:,}\n")
        f.write(f"\nCounty Details:\n")
        for stats in overall_stats['county_stats']:
            if stats['records_updated'] > 0:
                f.write(f"  {stats['county']}: {stats['records_updated']:,} parcels updated from {stats['records_processed']:,} records\n")

    logger.info(f"Summary saved to: {summary_file}")

    return overall_stats

if __name__ == "__main__":
    results = main()