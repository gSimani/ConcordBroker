"""
Auto-import Broward SDF to test the full process
"""

import os
import csv
from pathlib import Path
from supabase import create_client
import time

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test with BROWARD
SDF_FILE = Path("TEMP/DATABASE PROPERTY APP/BROWARD/SDF/SDF16P202501.csv")

print("=" * 80)
print("AUTO IMPORT - BROWARD COUNTY SDF")
print("=" * 80)
print(f"File: {SDF_FILE}")
print(f"Size: {SDF_FILE.stat().st_size / (1024 * 1024):.1f} MB")
print()

# Parse CSV into records
print("[1] Parsing CSV...")

sales_records = []

with open(SDF_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        # CRITICAL FIX: Convert scientific notation parcel ID to string
        parcel_id_raw = row.get('PARCEL_ID', '')

        try:
            # If it's scientific notation, convert to integer first then string
            if 'E' in parcel_id_raw or 'e' in parcel_id_raw:
                parcel_id = str(int(float(parcel_id_raw)))
            else:
                parcel_id = str(parcel_id_raw).strip()
        except (ValueError, OverflowError):
            parcel_id = str(parcel_id_raw).strip()

        sale_year = row.get('SALE_YR', '')
        sale_month = row.get('SALE_MO', '')

        if not parcel_id or not sale_year or not sale_month:
            continue

        try:
            year = int(sale_year)
            month = int(sale_month)
            sale_price = int(float(row.get('SALE_PRC', '0')))

            if year < 1900 or month < 1 or month > 12 or sale_price <= 0:
                continue

            sale_date = f"{year:04d}-{month:02d}-01"
            sale_price_cents = sale_price * 100

            # Get OR_BOOK and OR_PAGE (may be empty)
            or_book = str(row.get('OR_BOOK', '')).strip()
            or_page = str(row.get('OR_PAGE', '')).strip()

            # Only set if not empty
            or_book = or_book if or_book and or_book != '' else None
            or_page = or_page if or_page and or_page != '' else None

            record = {
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'sale_date': sale_date,
                'sale_price': sale_price_cents,  # In CENTS
                'sale_year': year,
                'sale_month': month,
                'quality_code': row.get('QUAL_CD', '').strip() or None,
                'clerk_no': row.get('CLERK_NO', '').strip() or None,
                'or_book': or_book,
                'or_page': or_page,
                'vi_code': row.get('VI_CD', '').strip() or None,
                'data_source': 'florida_sdf_broward_2025'
            }

            sales_records.append(record)

        except ValueError:
            continue

print(f"  Parsed {len(sales_records):,} valid sales records")

# Show sample
print(f"\n  Sample records (first 3):")
for i, record in enumerate(sales_records[:3], 1):
    print(f"\n    Record {i}:")
    print(f"      Parcel: {record['parcel_id']}")
    print(f"      Date: {record['sale_date']}")
    print(f"      Price: ${record['sale_price']/100:,.2f}")
    print(f"      OR Book/Page: {record['or_book']}/{record['or_page']}")
    print(f"      Quality: {record['quality_code']}")

# Import in batches
print(f"\n[2] Importing {len(sales_records):,} records to Supabase...")

BATCH_SIZE = 1000
imported = 0
errors = 0

for i in range(0, len(sales_records), BATCH_SIZE):
    batch = sales_records[i:i + BATCH_SIZE]

    try:
        result = supabase.table('property_sales_history').insert(batch).execute()
        imported += len(batch)

        if (i + BATCH_SIZE) % 10000 == 0:
            print(f"    Imported {imported:,} / {len(sales_records):,}...")

    except Exception as e:
        error_msg = str(e)[:300]
        print(f"    Batch error at {i}: {error_msg}")
        errors += len(batch)

    # Rate limiting
    time.sleep(0.05)

print(f"\n  Import complete:")
print(f"    Imported: {imported:,}")
print(f"    Errors: {errors:,}")

# Verify
print(f"\n[3] Verifying import...")

try:
    result = supabase.table('property_sales_history').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()
    print(f"    Total BROWARD sales in database: {result.count:,}")

    # Get a sample
    sample = supabase.table('property_sales_history').select('*').eq('county', 'BROWARD').limit(1).execute()

    if sample.data:
        record = sample.data[0]
        print(f"\n    Sample record from database:")
        print(f"      Parcel: {record.get('parcel_id')}")
        print(f"      Date: {record.get('sale_date')}")
        print(f"      Price: ${record.get('sale_price', 0) / 100:,.2f}")
        print(f"      OR Book/Page: {record.get('or_book')}/{record.get('or_page')}")
        print(f"      Quality: {record.get('quality_code')}")

    print("\n    SUCCESS!")

except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 80)
print("AUTO IMPORT COMPLETE")
print("=" * 80)
