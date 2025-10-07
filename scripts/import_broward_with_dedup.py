"""
Import Broward SDF with deduplication
Only imports records that don't already exist (based on parcel_id + sale_date)
"""

import os
import csv
from pathlib import Path
from supabase import create_client
import time

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SDF_FILE = Path("TEMP/DATABASE PROPERTY APP/BROWARD/SDF/SDF16P202501.csv")

print("=" * 80)
print("BROWARD COUNTY SDF IMPORT (WITH DEDUPLICATION)")
print("=" * 80)
print(f"File: {SDF_FILE}")
print(f"Size: {SDF_FILE.stat().st_size / (1024 * 1024):.1f} MB")
print()

# Get existing sales to avoid duplicates
print("[1] Loading existing sales to check for duplicates...")
try:
    # Get all existing Broward sales
    existing = supabase.table('property_sales_history').select('parcel_id, sale_date').eq('county', 'BROWARD').execute()

    existing_keys = set()
    if existing.data:
        existing_keys = {(sale['parcel_id'], sale['sale_date']) for sale in existing.data}
        print(f"  Found {len(existing_keys):,} existing BROWARD sales to skip")
    else:
        print(f"  No existing BROWARD sales found")
except Exception as e:
    print(f"  Warning: Could not load existing sales: {e}")
    print(f"  Proceeding without deduplication")
    existing_keys = set()

# Parse CSV
print(f"\n[2] Parsing CSV...")

sales_records = []
skipped_duplicates = 0
skipped_invalid = 0

with open(SDF_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        # Convert parcel ID from scientific notation
        parcel_id_raw = row.get('PARCEL_ID', '')
        try:
            if 'E' in parcel_id_raw or 'e' in parcel_id_raw:
                parcel_id = str(int(float(parcel_id_raw)))
            else:
                parcel_id = str(parcel_id_raw).strip()
        except (ValueError, OverflowError):
            parcel_id = str(parcel_id_raw).strip()

        sale_year = row.get('SALE_YR', '')
        sale_month = row.get('SALE_MO', '')

        if not parcel_id or not sale_year or not sale_month:
            skipped_invalid += 1
            continue

        try:
            year = int(sale_year)
            month = int(sale_month)
            sale_price = int(float(row.get('SALE_PRC', '0')))

            if year < 1900 or month < 1 or month > 12 or sale_price <= 0:
                skipped_invalid += 1
                continue

            sale_date = f"{year:04d}-{month:02d}-01"

            # Check if duplicate
            if (parcel_id, sale_date) in existing_keys:
                skipped_duplicates += 1
                continue

            # Get OR_BOOK and OR_PAGE
            or_book = str(row.get('OR_BOOK', '')).strip()
            or_page = str(row.get('OR_PAGE', '')).strip()

            # Only set if not empty
            or_book = or_book if or_book and or_book != '' else None
            or_page = or_page if or_page and or_page != '' else None

            # Match the existing table schema exactly
            record = {
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'county_no': '06',  # Broward county code
                'sale_date': sale_date,
                'sale_price': sale_price * 100,  # Convert to cents
                'sale_year': year,
                'sale_month': month,
                'quality_code': row.get('QUAL_CD', '').strip() or None,
                'clerk_no': row.get('CLERK_NO', '').strip() or None,
                'or_book': or_book,
                'or_page': or_page,
                'verification_code': row.get('VI_CD', '').strip() or None,
                'assessment_year': row.get('ASMNT_YR', '').strip() or None,
                'atv_start': row.get('ATV_STRT', '').strip() or None,
                'group_no': row.get('GRP_NO', '').strip() or None,
                'dor_use_code': row.get('DOR_UC', '').strip() or None,
                'neighborhood_code': row.get('NBRHD_CD', '').strip() or None,
                'market_area': row.get('MKT_AR', '').strip() or None,
                'census_block': row.get('CENSUS_BK', '').strip() or None,
                'sale_id_code': row.get('SALE_ID_CD', '').strip() or None,
                'sale_change_code': row.get('SAL_CHG_CD', '').strip() or None,
                'multi_parcel_sale': row.get('MULTI_PAR_SAL', '').strip() or None,
                'rs_id': row.get('RS_ID', '').strip() or None,
                'mp_id': row.get('MP_ID', '').strip() or None,
                'state_parcel_id': row.get('STATE_PARCEL_ID', '').strip() or None,
            }

            sales_records.append(record)

        except ValueError:
            skipped_invalid += 1
            continue

print(f"  Parsed {len(sales_records):,} NEW sales records")
print(f"  Skipped {skipped_duplicates:,} duplicates")
print(f"  Skipped {skipped_invalid:,} invalid records")

if not sales_records:
    print("\n  No new records to import!")
    exit(0)

# Show sample
print(f"\n  Sample records (first 3):")
for i, record in enumerate(sales_records[:3], 1):
    print(f"\n    Record {i}:")
    print(f"      Parcel: {record['parcel_id']}")
    print(f"      Date: {record['sale_date']}")
    print(f"      Price: ${record['sale_price']/100:,.2f}")
    print(f"      County: {record['county']}")
    print(f"      OR Book/Page: {record['or_book']}/{record['or_page']}")

# Import
print(f"\n[3] Importing {len(sales_records):,} records to Supabase...")

BATCH_SIZE = 500  # Smaller batches for stability
imported = 0
errors = 0

for i in range(0, len(sales_records), BATCH_SIZE):
    batch = sales_records[i:i + BATCH_SIZE]

    try:
        result = supabase.table('property_sales_history').insert(batch).execute()
        imported += len(batch)

        if (i + BATCH_SIZE) % 5000 == 0:
            print(f"    Imported {imported:,} / {len(sales_records):,}...")

    except Exception as e:
        error_msg = str(e)[:500]
        print(f"    Batch error at {i}: {error_msg}")
        errors += len(batch)

    time.sleep(0.1)

print(f"\n  Import complete:")
print(f"    Imported: {imported:,}")
print(f"    Errors: {errors:,}")

# Verify
print(f"\n[4] Verifying import...")

try:
    result = supabase.table('property_sales_history').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()
    print(f"    Total BROWARD sales in database: {result.count:,}")

    # Get a sample with county populated
    sample = supabase.table('property_sales_history').select('*').eq('county', 'BROWARD').not_.is_('county', 'null').limit(1).execute()

    if sample.data:
        record = sample.data[0]
        print(f"\n    Sample record with county:")
        print(f"      Parcel: {record.get('parcel_id')}")
        print(f"      County: {record.get('county')}")
        print(f"      Date: {record.get('sale_date')}")
        print(f"      Price: ${record.get('sale_price', 0) / 100:,.2f}")
        print(f"      OR Book/Page: {record.get('or_book')}/{record.get('or_page')}")

        print(f"\n    Test in UI: http://localhost:5178/property/{record.get('parcel_id')}")
        print("\n    SUCCESS!")

except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 80)
print("IMPORT COMPLETE")
print("=" * 80)
