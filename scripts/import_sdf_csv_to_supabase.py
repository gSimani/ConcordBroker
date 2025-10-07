"""
Florida SDF Sales Data Importer (CSV Format)
Parses CSV SDF files from TEMP/DATABASE PROPERTY APP/{COUNTY}/SDF/
and imports sales data into Supabase property_sales_history table

CSV Columns (from sample):
- PARCEL_ID
- SALE_YR, SALE_MO, SALE_PRC
- OR_BOOK, OR_PAGE
- CLERK_NO
- QUAL_CD (Q/U)
- VI_CD
"""

import os
import csv
from pathlib import Path
from datetime import datetime
from supabase import create_client
import time

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Base directory
BASE_DIR = Path("TEMP/DATABASE PROPERTY APP")

# County name mapping (folder name to standard name)
COUNTY_MAPPING = {
    "DADE": "MIAMI-DADE",
    "MIAMI-DADE": "MIAMI-DADE",
    "ST. JOHNS": "ST. JOHNS",
    "ST_JOHNS": "ST. JOHNS",
    "ST. LUCIE": "ST. LUCIE",
    "ST_LUCIE": "ST. LUCIE",
    "INDIAN RIVER": "INDIAN RIVER",
    "INDIAN_RIVER": "INDIAN RIVER",
    "PALM BEACH": "PALM BEACH",
    "PALM_BEACH": "PALM BEACH",
    "SANTA ROSA": "SANTA ROSA",
    "SANTA_ROSA": "SANTA ROSA",
}

def parse_sdf_csv_row(row, county: str):
    """Parse a single CSV row into a sales record dictionary"""

    try:
        parcel_id = str(row.get('PARCEL_ID', '')).strip()

        # Skip if no parcel ID
        if not parcel_id or parcel_id == '0':
            return None

        # Get sale date components
        sale_year = row.get('SALE_YR', '')
        sale_month = row.get('SALE_MO', '')

        if not sale_year or not sale_month:
            return None

        try:
            year = int(sale_year)
            month = int(sale_month)
        except ValueError:
            return None

        # Validate date
        if year < 1900 or year > 2100 or month < 1 or month > 12:
            return None

        # Construct sale date (use day 1)
        sale_date = f"{year:04d}-{month:02d}-01"

        # Get sale price
        sale_price_str = str(row.get('SALE_PRC', '0')).strip()

        try:
            # Sale price appears to be in dollars (not cents) in this CSV format
            sale_price = int(float(sale_price_str))
        except ValueError:
            sale_price = 0

        # Skip invalid sales
        if sale_price <= 0 or sale_price > 99999999900:  # Max ~$1B
            return None

        # Convert to cents for storage
        sale_price_cents = sale_price * 100

        # Get other fields
        or_book = str(row.get('OR_BOOK', '')).strip() or None
        or_page = str(row.get('OR_PAGE', '')).strip() or None
        clerk_no = str(row.get('CLERK_NO', '')).strip() or None
        qual_cd = str(row.get('QUAL_CD', '')).strip() or None
        vi_cd = str(row.get('VI_CD', '')).strip() or None

        # Standardize county name
        county_std = COUNTY_MAPPING.get(county.upper(), county.upper())

        return {
            'parcel_id': parcel_id,
            'county': county_std,
            'sale_date': sale_date,
            'sale_price': sale_price_cents,  # Stored in CENTS
            'sale_year': year,
            'sale_month': month,
            'quality_code': qual_cd if qual_cd in ['Q', 'U', 'q', 'u'] else None,
            'clerk_no': clerk_no,
            'or_book': or_book,
            'or_page': or_page,
            'vi_code': vi_cd,
            'data_source': 'florida_sdf_2025_csv'
        }

    except Exception as e:
        return None

def import_county_sdf(county_dir: Path, county_name: str):
    """Import SDF CSV files for a single county"""

    sdf_dir = county_dir / "SDF"

    if not sdf_dir.exists():
        print(f"  No SDF directory found")
        return 0, 0

    # Find CSV files
    csv_files = list(sdf_dir.glob("*.csv"))

    if not csv_files:
        print(f"  No CSV files found")
        return 0, 0

    csv_file = csv_files[0]
    print(f"  Processing: {csv_file.name} ({csv_file.stat().st_size / (1024 * 1024):.1f} MB)")

    sales_records = []
    parsed_count = 0
    skipped_count = 0

    # Parse CSV file
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, 1):
            record = parse_sdf_csv_row(row, county_name)

            if record:
                sales_records.append(record)
                parsed_count += 1
            else:
                skipped_count += 1

            # Progress indicator
            if row_num % 25000 == 0:
                print(f"    Processed {row_num:,} rows, {parsed_count:,} valid sales...")

    print(f"  Parsed: {parsed_count:,} sales, Skipped: {skipped_count:,} invalid rows")

    if not sales_records:
        print(f"  No valid sales records to import")
        return 0, 0

    # Import to Supabase in batches
    BATCH_SIZE = 1000
    imported = 0
    errors = 0

    print(f"  Importing {len(sales_records):,} sales to Supabase...")

    for i in range(0, len(sales_records), BATCH_SIZE):
        batch = sales_records[i:i + BATCH_SIZE]

        try:
            result = supabase.table('property_sales_history').insert(batch).execute()
            imported += len(batch)

            if (i + BATCH_SIZE) % 10000 == 0:
                print(f"    Imported {imported:,} / {len(sales_records):,} sales...")

        except Exception as e:
            print(f"    Batch import error at row {i}: {str(e)[:200]}")
            errors += len(batch)

        # Rate limiting
        time.sleep(0.05)

    print(f"  Import complete: {imported:,} imported, {errors:,} errors")

    return imported, errors

def main():
    print("=" * 80)
    print("FLORIDA SDF SALES DATA IMPORTER (CSV FORMAT)")
    print("=" * 80)
    print(f"Input directory: {BASE_DIR.absolute()}")
    print()

    # Check if base directory exists
    if not BASE_DIR.exists():
        print(f"ERROR: Base directory not found: {BASE_DIR}")
        return

    # Get list of county directories
    county_dirs = [d for d in BASE_DIR.iterdir() if d.is_dir() and not d.name.startswith('NAL')]

    if not county_dirs:
        print("ERROR: No county directories found")
        return

    print(f"Found {len(county_dirs)} potential county directories")
    print()

    total_imported = 0
    total_errors = 0
    counties_processed = 0
    start_time = time.time()

    for i, county_dir in enumerate(sorted(county_dirs), 1):
        county = county_dir.name

        print(f"\n[{i}/{len(county_dirs)}] {county}")

        imported, errors = import_county_sdf(county_dir, county)

        if imported > 0 or errors > 0:
            counties_processed += 1

        total_imported += imported
        total_errors += errors

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Counties scanned: {len(county_dirs)}")
    print(f"Counties with SDF data: {counties_processed}")
    print(f"Total sales imported: {total_imported:,}")
    print(f"Total errors: {total_errors:,}")
    print(f"Total time: {elapsed / 60:.1f} minutes")
    print("=" * 80)

    # Verify count in database
    print("\nVerifying database count...")
    try:
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
        print(f"Total records in property_sales_history: {result.count:,}")
    except Exception as e:
        print(f"ERROR verifying count: {e}")

if __name__ == "__main__":
    main()
