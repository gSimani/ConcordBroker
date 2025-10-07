"""
Test import for a single county (BROWARD) to verify the process works
"""

import os
import csv
from pathlib import Path
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    print(f"SUPABASE_KEY from .env: {os.getenv('SUPABASE_KEY', 'not set')}")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test with BROWARD
SDF_FILE = Path("TEMP/DATABASE PROPERTY APP/BROWARD/SDF/SDF16P202501.csv")

print("=" * 80)
print("TEST IMPORT - BROWARD COUNTY SDF")
print("=" * 80)
print(f"File: {SDF_FILE}")
print(f"Size: {SDF_FILE.stat().st_size / (1024 * 1024):.1f} MB")
print()

# Parse CSV and show sample records
print("[1] Parsing CSV...")

with open(SDF_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    print("  Columns:", list(reader.fieldnames))
    print()

    # Show first 5 records
    print("  First 5 sales records:")
    for i, row in enumerate(reader, 1):
        if i <= 5:
            parcel_id = row.get('PARCEL_ID', '')
            sale_year = row.get('SALE_YR', '')
            sale_month = row.get('SALE_MO', '')
            sale_price = row.get('SALE_PRC', '')
            or_book = row.get('OR_BOOK', '')
            or_page = row.get('OR_PAGE', '')
            qual_cd = row.get('QUAL_CD', '')

            print(f"\n    Record {i}:")
            print(f"      Parcel: {parcel_id}")
            print(f"      Date: {sale_year}/{sale_month}")
            print(f"      Price: ${sale_price}")
            print(f"      OR Book/Page: {or_book}/{or_page}")
            print(f"      Qual: {qual_cd}")
        else:
            break

# Parse into records
print("\n[2] Converting to database format...")

sales_records = []

with open(SDF_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)

    for row in reader:
        parcel_id = str(row.get('PARCEL_ID', '')).strip()
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

            record = {
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'sale_date': sale_date,
                'sale_price': sale_price_cents,  # In CENTS
                'sale_year': year,
                'sale_month': month,
                'quality_code': row.get('QUAL_CD', '').strip() or None,
                'clerk_no': row.get('CLERK_NO', '').strip() or None,
                'or_book': row.get('OR_BOOK', '').strip() or None,
                'or_page': row.get('OR_PAGE', '').strip() or None,
                'vi_code': row.get('VI_CD', '').strip() or None,
                'data_source': 'florida_sdf_broward_test'
            }

            sales_records.append(record)

        except ValueError:
            continue

print(f"  Parsed {len(sales_records):,} valid sales records")

# Show sample records
print(f"\n  Sample database records:")
for i, record in enumerate(sales_records[:3], 1):
    print(f"\n    Record {i}:")
    for key, value in record.items():
        if key == 'sale_price':
            print(f"      {key}: {value:,} cents (${value/100:,.2f})")
        else:
            print(f"      {key}: {value}")

# Ask to import
print(f"\n[3] Ready to import {len(sales_records):,} records to Supabase")
print(f"    This will import to property_sales_history table")

proceed = input("\n  Continue? (yes/no): ").strip().lower()

if proceed not in ['yes', 'y']:
    print("\n  Skipping import")
    exit(0)

# Import in batches
print(f"\n  Importing...")

BATCH_SIZE = 1000
imported = 0
errors = 0

for i in range(0, len(sales_records), BATCH_SIZE):
    batch = sales_records[i:i + BATCH_SIZE]

    try:
        result = supabase.table('property_sales_history').insert(batch).execute()
        imported += len(batch)
        print(f"    Imported {imported:,} / {len(sales_records):,}...")
    except Exception as e:
        print(f"    Batch error at {i}: {str(e)[:200]}")
        errors += len(batch)

print(f"\n  Import complete:")
print(f"    Imported: {imported:,}")
print(f"    Errors: {errors:,}")

# Verify
print(f"\n[4] Verifying import...")

try:
    result = supabase.table('property_sales_history').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()
    print(f"    Total BROWARD sales in database: {result.count:,}")

    # Get a sample
    sample = supabase.table('property_sales_history').select('*').eq('county', 'BROWARD').limit(1).execute()

    if sample.data:
        record = sample.data[0]
        print(f"\n    Sample record:")
        print(f"      Parcel: {record.get('parcel_id')}")
        print(f"      Date: {record.get('sale_date')}")
        print(f"      Price: ${record.get('sale_price', 0) / 100:,.2f}")
        print(f"      OR Book/Page: {record.get('or_book')}/{record.get('or_page')}")

except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
