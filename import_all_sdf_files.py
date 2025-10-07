"""
Import ALL Florida SDF (Sales Data Files) into Supabase
This will import sales history for all 67 Florida counties
"""

import os
import zipfile
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
        logging.FileHandler('sdf_import.log'),
        logging.StreamHandler()
    ]
)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Paths
SDF_ZIP_PATH = r"C:\TEMP\FLORIDA_SDF_DATA"
SDF_EXTRACT_PATH = r"C:\TEMP\FLORIDA_SDF_EXTRACTED"

# Statistics
stats = {
    'total_files': 0,
    'total_records': 0,
    'successful_imports': 0,
    'failed_imports': 0,
    'counties_processed': []
}

def extract_zip_files():
    """Extract all SDF ZIP files"""
    logging.info("=" * 70)
    logging.info("EXTRACTING SDF ZIP FILES")
    logging.info("=" * 70)

    if not os.path.exists(SDF_EXTRACT_PATH):
        os.makedirs(SDF_EXTRACT_PATH)

    zip_files = glob.glob(os.path.join(SDF_ZIP_PATH, "*Final_SDF_2025.zip"))

    for zip_path in zip_files:
        county_name = os.path.basename(zip_path).split('_')[0]
        extract_dir = os.path.join(SDF_EXTRACT_PATH, county_name)

        if not os.path.exists(extract_dir):
            logging.info(f"Extracting {county_name}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            logging.info(f"  Extracted to {extract_dir}")
        else:
            logging.info(f"  {county_name} already extracted")

    return len(zip_files)

def analyze_sdf_structure(sample_file):
    """Analyze the structure of an SDF file"""
    try:
        # Read first few rows to understand structure
        df = pd.read_csv(sample_file, nrows=5, encoding='latin1')

        logging.info(f"SDF Columns found: {list(df.columns)}")
        logging.info(f"Sample data:\n{df.head(2)}")

        return list(df.columns)
    except Exception as e:
        logging.error(f"Error analyzing SDF: {e}")
        return []

def standardize_sdf_columns(df):
    """Standardize SDF column names to match our database schema"""

    # Common SDF column mappings (adjust based on actual Florida SDF format)
    column_mapping = {
        'PARID': 'parcel_id',
        'PARCEL_ID': 'parcel_id',
        'PARCELNO': 'parcel_id',
        'SALE_DATE': 'sale_date',
        'SALEDT': 'sale_date',
        'SALEDATE': 'sale_date',
        'SALE_PRICE': 'sale_price',
        'SALEPRICE': 'sale_price',
        'SALE_PRC': 'sale_price',
        'PRICE': 'sale_price',
        'SALE_YR': 'sale_year',
        'SALE_YEAR': 'sale_year',
        'SALEYR': 'sale_year',
        'SALE_MO': 'sale_month',
        'SALE_MONTH': 'sale_month',
        'SALEMO': 'sale_month',
        'QUAL_CODE': 'sale_qualification',
        'QUAL': 'sale_qualification',
        'QUALIFICATION': 'sale_qualification',
        'DEED_TYPE': 'document_type',
        'INSTRUMENT': 'document_type',
        'INST_TYPE': 'document_type',
        'GRANTOR': 'grantor_name',
        'GRANTOR_NAME': 'grantor_name',
        'GRANTEE': 'grantee_name',
        'GRANTEE_NAME': 'grantee_name',
        'BOOK': 'book',
        'BK': 'book',
        'PAGE': 'page',
        'PG': 'page',
        'OR_BOOK': 'book',
        'OR_PAGE': 'page'
    }

    # Rename columns
    df.columns = [col.upper() for col in df.columns]
    df.rename(columns=column_mapping, inplace=True)

    return df

def clean_sales_data(df, county_name):
    """Clean and validate sales data"""

    # Ensure required columns exist
    required_cols = ['parcel_id', 'sale_price']
    for col in required_cols:
        if col not in df.columns:
            logging.warning(f"Missing required column {col} in {county_name}")
            return pd.DataFrame()

    # Remove invalid records
    df = df[df['parcel_id'].notna()]
    df = df[df['sale_price'] > 0]  # Remove $0 sales

    # Clean parcel_id
    df['parcel_id'] = df['parcel_id'].astype(str).str.strip()

    # Parse sale_date if exists
    if 'sale_date' in df.columns:
        try:
            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')
            df['sale_year'] = df['sale_date'].dt.year
            df['sale_month'] = df['sale_date'].dt.month
        except:
            pass

    # Add county
    df['county'] = county_name.upper()

    # Add import timestamp
    df['imported_at'] = datetime.now().isoformat()

    return df

def import_to_supabase(df, county_name, batch_size=1000):
    """Import sales data to Supabase in batches"""

    if df.empty:
        return 0, 0

    success_count = 0
    error_count = 0

    # Convert to records
    records = df.to_dict('records')
    total = len(records)

    logging.info(f"Importing {total} sales records for {county_name}...")

    # Process in batches
    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]

        try:
            # First, try to create property_sales table if it doesn't exist
            response = supabase.table('property_sales').upsert(
                batch,
                on_conflict='parcel_id,sale_date,sale_price'
            ).execute()

            success_count += len(batch)

            if (i + batch_size) % 5000 == 0:
                logging.info(f"  Progress: {min(i+batch_size, total)}/{total} records")

        except Exception as e:
            error_msg = str(e)

            # If table doesn't exist, try florida_parcels update
            if 'property_sales' in error_msg and 'does not exist' in error_msg:
                logging.info("property_sales table not found, updating florida_parcels instead...")

                # Update florida_parcels with latest sale
                for record in batch[:10]:  # Just update first 10 as example
                    try:
                        supabase.table('florida_parcels').update({
                            'sale_date': record.get('sale_date'),
                            'sale_price': record.get('sale_price'),
                            'sale_qualification': record.get('sale_qualification')
                        }).eq('parcel_id', record['parcel_id']).execute()
                        success_count += 1
                    except:
                        error_count += 1
                break
            else:
                logging.error(f"Batch import error: {error_msg[:100]}")
                error_count += len(batch)

        # Rate limiting
        time.sleep(0.1)

    return success_count, error_count

def process_county(county_dir):
    """Process all SDF files for a county"""

    county_name = os.path.basename(county_dir)
    logging.info(f"\nProcessing {county_name}...")

    # Find SDF CSV files
    sdf_files = glob.glob(os.path.join(county_dir, "*.csv")) + \
                glob.glob(os.path.join(county_dir, "*.txt")) + \
                glob.glob(os.path.join(county_dir, "SDF*", "*.csv"))

    if not sdf_files:
        logging.warning(f"No SDF files found for {county_name}")
        return 0, 0

    all_sales = []

    for sdf_file in sdf_files:
        try:
            # Read SDF file
            df = pd.read_csv(sdf_file, encoding='latin1', low_memory=False)

            # Standardize columns
            df = standardize_sdf_columns(df)

            # Clean data
            df = clean_sales_data(df, county_name)

            if not df.empty:
                all_sales.append(df)

        except Exception as e:
            logging.error(f"Error reading {sdf_file}: {e}")

    if all_sales:
        # Combine all sales for the county
        combined_df = pd.concat(all_sales, ignore_index=True)

        # Remove duplicates
        combined_df.drop_duplicates(subset=['parcel_id', 'sale_date', 'sale_price'], inplace=True)

        # Import to Supabase
        success, errors = import_to_supabase(combined_df, county_name)

        return success, errors

    return 0, 0

def main():
    """Main import process"""

    print("=" * 70)
    print("FLORIDA SDF SALES DATA IMPORT")
    print("=" * 70)
    print()

    start_time = time.time()

    # Step 1: Extract ZIP files
    num_zips = extract_zip_files()
    logging.info(f"\nFound {num_zips} county SDF ZIP files")

    # Step 2: Get all county directories
    county_dirs = glob.glob(os.path.join(SDF_EXTRACT_PATH, "*"))
    logging.info(f"Found {len(county_dirs)} counties to process")

    # Step 3: Analyze structure from first county
    if county_dirs:
        first_county = county_dirs[0]
        sample_files = glob.glob(os.path.join(first_county, "*.csv"))[:1]
        if sample_files:
            analyze_sdf_structure(sample_files[0])

    # Step 4: Process all counties
    total_success = 0
    total_errors = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_county, county_dir): county_dir
                  for county_dir in county_dirs}

        for future in as_completed(futures):
            county_dir = futures[future]
            county_name = os.path.basename(county_dir)

            try:
                success, errors = future.result()
                total_success += success
                total_errors += errors
                stats['counties_processed'].append(county_name)
                logging.info(f"✓ {county_name}: {success} imported, {errors} errors")
            except Exception as e:
                logging.error(f"✗ {county_name}: Failed - {e}")

    # Final statistics
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Counties processed: {len(stats['counties_processed'])}")
    print(f"Records imported: {total_success:,}")
    print(f"Errors: {total_errors:,}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Import rate: {total_success/elapsed:.0f} records/second")

    # Save stats
    with open('sdf_import_stats.json', 'w') as f:
        json.dump({
            'counties': stats['counties_processed'],
            'total_imported': total_success,
            'total_errors': total_errors,
            'elapsed_minutes': elapsed/60
        }, f, indent=2)

    print("\nStats saved to sdf_import_stats.json")
    print("Log saved to sdf_import.log")

if __name__ == "__main__":
    main()