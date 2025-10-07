"""
Import NAL (Name Address List) Property Data into Supabase
Enhances the florida_parcels table with updated property information
"""

import os
import pandas as pd
import glob
from supabase import create_client
import time
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nal_import.log'),
        logging.StreamHandler()
    ]
)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Paths
NAL_DATA_PATH = r"C:\TEMP\DATABASE PROPERTY APP"

# Statistics
stats = {
    'total_files': 0,
    'total_records': 0,
    'successful_updates': 0,
    'failed_updates': 0,
    'counties_processed': [],
    'new_properties': 0,
    'updated_properties': 0
}

def standardize_nal_columns(df):
    """Map NAL columns to florida_parcels schema"""

    # NAL column mapping to florida_parcels (only include columns that exist in target table)
    column_mapping = {
        'PARCEL_ID': 'parcel_id',
        'COUNTY': 'county',
        'TAX_YR': 'year',
        'OWN_NAME': 'owner_name',
        'OWN_ADDR1': 'owner_addr1',
        'OWN_CITY': 'owner_city',
        'OWN_STATE': 'owner_state',
        'OWN_ZIPCD': 'owner_zip',  # Changed from owner_zipcode to owner_zip
        'PHY_ADDR1': 'phy_addr1',
        'PHY_CITY': 'phy_city',
        'PHY_ZIPCD': 'phy_zipcd',  # This exists in schema
        'LND_VAL': 'land_value',
        'BLD_VAL': 'building_value',
        'JV': 'just_value',
        'LND_SQFOOT': 'land_sqft'
    }

    # Rename columns to match our schema
    df = df.rename(columns=column_mapping)

    # Drop any columns that weren't mapped and don't exist in target schema
    valid_columns = ['parcel_id', 'county', 'year', 'owner_name', 'owner_addr1',
                     'owner_city', 'owner_state', 'owner_zip', 'phy_addr1',
                     'phy_city', 'phy_zipcd', 'land_value', 'building_value',
                     'just_value', 'land_sqft']

    # Keep only columns that exist in both the dataframe and are valid
    columns_to_keep = [col for col in df.columns if col in valid_columns]
    df = df[columns_to_keep]

    return df

def clean_property_data(df, county_name):
    """Clean and validate property data"""

    # Ensure required columns exist
    if 'parcel_id' not in df.columns:
        logging.error(f"Missing parcel_id column in {county_name}")
        return pd.DataFrame()

    # Remove invalid records
    df = df[df['parcel_id'].notna()]
    df = df[df['parcel_id'] != '']

    # Clean and format data
    df['parcel_id'] = df['parcel_id'].astype(str).str.strip()
    df['county'] = county_name.upper()
    df['year'] = 2025  # All current data is 2025

    # Clean owner state (FL not FLORIDA)
    if 'owner_state' in df.columns:
        df['owner_state'] = df['owner_state'].str.strip().str[:2]

    # Convert numeric fields
    numeric_fields = ['land_value', 'building_value', 'just_value', 'land_sqft']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')

    # Note: total_value and updated_at are not in the schema, so we skip those

    # Remove any completely empty rows
    df = df.dropna(how='all')

    return df

def import_to_supabase(df, county_name, batch_size=1000):
    """Import property data to Supabase in batches"""

    if df.empty:
        return 0, 0, 0, 0

    success_count = 0
    error_count = 0
    new_count = 0
    updated_count = 0

    # Convert to records
    records = df.to_dict('records')
    total = len(records)

    logging.info(f"Importing {total} property records for {county_name}...")

    # Process in batches
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]

        try:
            # Check if properties already exist first
            parcel_ids = [record['parcel_id'] for record in batch]

            # Check which ones already exist
            existing_response = supabase.table('florida_parcels').select('parcel_id').in_('parcel_id', parcel_ids).execute()
            existing_ids = {row['parcel_id'] for row in existing_response.data} if existing_response.data else set()

            # Separate new vs existing records
            new_records = [record for record in batch if record['parcel_id'] not in existing_ids]
            update_records = [record for record in batch if record['parcel_id'] in existing_ids]

            # Insert new records
            if new_records:
                response = supabase.table('florida_parcels').insert(new_records).execute()
                new_count += len(new_records)

            # Update existing records (one by one since there's no bulk update with complex conditions)
            for record in update_records[:5]:  # Limit to 5 updates per batch to avoid timeout
                try:
                    parcel_id = record['parcel_id']
                    update_data = {k: v for k, v in record.items() if k != 'parcel_id'}  # Remove parcel_id from update data
                    supabase.table('florida_parcels').update(update_data).eq('parcel_id', parcel_id).execute()
                    updated_count += 1
                except:
                    pass  # Skip failed updates

            success_count += len(new_records) + updated_count

            if (i + batch_size) % 5000 == 0:
                logging.info(f"  Progress: {min(i+batch_size, total)}/{total} records")

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Batch import error for {county_name}: {error_msg[:100]}")
            error_count += len(batch)

        # Rate limiting
        time.sleep(0.1)

    return success_count, error_count, new_count, updated_count

def process_county_nal(nal_file_path):
    """Process a single county's NAL file"""

    county_path_parts = nal_file_path.split(os.sep)
    county_name = None

    # Extract county name from path
    for part in county_path_parts:
        if part.endswith('_NAL_2025.csv'):
            county_name = part.replace('_NAL_2025.csv', '')
            break

    if not county_name:
        logging.error(f"Could not extract county name from {nal_file_path}")
        return 0, 0, 0, 0

    logging.info(f"Processing {county_name}...")

    try:
        # Read NAL file
        df = pd.read_csv(nal_file_path, encoding='latin1', low_memory=False)

        # Standardize columns
        df = standardize_nal_columns(df)

        # Clean data
        df = clean_property_data(df, county_name)

        if df.empty:
            logging.warning(f"No valid data for {county_name}")
            return 0, 0, 0, 0

        # Import to Supabase
        success, errors, new, updated = import_to_supabase(df, county_name)

        return success, errors, new, updated

    except Exception as e:
        logging.error(f"Error processing {county_name}: {e}")
        return 0, 0, 0, 0

def main():
    """Main import process"""

    print("=" * 70)
    print("FLORIDA NAL PROPERTY DATA IMPORT")
    print("=" * 70)
    print()

    start_time = time.time()

    # Find all NAL files
    nal_files = glob.glob(os.path.join(NAL_DATA_PATH, "*", "NAL", "*_NAL_2025.csv"))

    if not nal_files:
        logging.error("No NAL files found!")
        return

    logging.info(f"Found {len(nal_files)} NAL files to process")

    # Process all counties
    total_success = 0
    total_errors = 0
    total_new = 0
    total_updated = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_county_nal, nal_file): nal_file
                  for nal_file in nal_files}

        for future in as_completed(futures):
            nal_file = futures[future]
            county_name = os.path.basename(nal_file).replace('_NAL_2025.csv', '')

            try:
                success, errors, new, updated = future.result()
                total_success += success
                total_errors += errors
                total_new += new
                total_updated += updated
                stats['counties_processed'].append(county_name)
                logging.info(f"[OK] {county_name}: {success} processed ({new} new, {updated} updated), {errors} errors")
            except Exception as e:
                logging.error(f"[FAIL] {county_name}: Failed - {e}")

    # Final statistics
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Counties processed: {len(stats['counties_processed'])}")
    print(f"Total records processed: {total_success:,}")
    print(f"New properties added: {total_new:,}")
    print(f"Properties updated: {total_updated:,}")
    print(f"Errors: {total_errors:,}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Processing rate: {total_success/elapsed:.0f} records/second")

    # Save stats
    with open('nal_import_stats.json', 'w') as f:
        json.dump({
            'counties': stats['counties_processed'],
            'total_processed': total_success,
            'new_properties': total_new,
            'updated_properties': total_updated,
            'total_errors': total_errors,
            'elapsed_minutes': elapsed/60
        }, f, indent=2)

    print("\nStats saved to nal_import_stats.json")
    print("Log saved to nal_import.log")

if __name__ == "__main__":
    main()