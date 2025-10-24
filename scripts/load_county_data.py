"""
Load County Data into Supabase
Loads parsed NAL and SDF data into florida_parcels and property_sales_history tables
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv('.env.mcp')

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE = 1000


def load_nal_data(csv_file: Path, county: str, year: int, dry_run: bool = False):
    """Load NAL (property) data into florida_parcels table"""

    print(f"\n📊 Loading NAL data from: {csv_file.name}")
    print(f"   County: {county}")
    print(f"   Year: {year}")

    if not csv_file.exists():
        print(f"   ❌ File not found: {csv_file}")
        return 0

    records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Transform CSV row to match florida_parcels schema
            record = {
                'parcel_id': row.get('parcel_id'),
                'county': county.upper(),
                'year': year,
                'owner_name': row.get('owner_name'),
                'owner_addr1': row.get('owner_addr1'),
                'owner_addr2': row.get('owner_addr2'),
                'owner_city': row.get('owner_city'),
                'owner_state': row.get('owner_state')[:2] if row.get('owner_state') else None,
                'owner_zip': row.get('owner_zip'),
                'phy_addr1': row.get('phy_addr1'),
                'phy_addr2': row.get('phy_addr2'),
                'city': row.get('city'),
                'zip_code': row.get('zip_code'),
                'dor_uc': row.get('property_use_code'),
                'just_value': float(row['just_value']) if row.get('just_value') else None,
                'assessed_value': float(row['assessed_value']) if row.get('assessed_value') else None,
                'taxable_value': float(row['taxable_value']) if row.get('taxable_value') else None,
                'land_value': float(row['land_value']) if row.get('land_value') else None,
                'building_value': float(row['building_value']) if row.get('building_value') else None,
                'land_sqft': float(row['land_sqft']) if row.get('land_sqft') else None,
                'data_source': 'NAL',
                'last_updated': datetime.now().isoformat(),
            }

            # Skip if missing critical fields
            if not record['parcel_id']:
                continue

            records.append(record)

    print(f"   📋 Read {len(records):,} records from CSV")

    if dry_run:
        print("   🧪 DRY RUN - No database changes")
        if records:
            print("\n   Sample record:")
            for k, v in list(records[0].items())[:10]:
                print(f"      {k}: {v}")
        return len(records)

    # Insert in batches
    inserted = 0
    errors = 0

    print(f"   💾 Inserting into database (batch size: {BATCH_SIZE})...")

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]

        try:
            # Use upsert to handle duplicates
            result = supabase.table('florida_parcels').upsert(
                batch,
                on_conflict='parcel_id,county,year'
            ).execute()

            inserted += len(batch)
            print(f"      Inserted batch {i//BATCH_SIZE + 1}: {len(batch)} records (total: {inserted:,})")

        except Exception as e:
            errors += len(batch)
            print(f"      ❌ Error inserting batch {i//BATCH_SIZE + 1}: {e}")

    print(f"\n   ✅ Loaded {inserted:,} records")
    if errors:
        print(f"   ⚠️  {errors:,} errors")

    return inserted


def load_sdf_data(csv_file: Path, county: str, dry_run: bool = False):
    """Load SDF (sales) data into property_sales_history table"""

    print(f"\n📊 Loading SDF data from: {csv_file.name}")
    print(f"   County: {county}")

    if not csv_file.exists():
        print(f"   ❌ File not found: {csv_file}")
        return 0

    records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Transform CSV row to match property_sales_history schema
            record = {
                'parcel_id': row.get('parcel_id'),
                'county': county.upper(),
                'sale_date': row.get('sale_date'),
                'sale_price': float(row['sale_price']) if row.get('sale_price') else None,
                'buyer_name': row.get('buyer_name'),
                'seller_name': row.get('seller_name'),
                'deed_book': row.get('deed_book'),
                'deed_page': row.get('deed_page'),
                'data_source': 'SDF',
            }

            # Skip if missing critical fields
            if not record['parcel_id'] or not record['sale_date']:
                continue

            records.append(record)

    print(f"   📋 Read {len(records):,} records from CSV")

    if dry_run:
        print("   🧪 DRY RUN - No database changes")
        if records:
            print("\n   Sample record:")
            for k, v in list(records[0].items())[:8]:
                print(f"      {k}: {v}")
        return len(records)

    # Insert in batches
    inserted = 0
    errors = 0

    print(f"   💾 Inserting into database (batch size: {BATCH_SIZE})...")

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]

        try:
            result = supabase.table('property_sales_history').insert(
                batch,
                upsert=True
            ).execute()

            inserted += len(batch)
            print(f"      Inserted batch {i//BATCH_SIZE + 1}: {len(batch)} records (total: {inserted:,})")

        except Exception as e:
            errors += len(batch)
            print(f"      ❌ Error inserting batch {i//BATCH_SIZE + 1}: {e}")

    print(f"\n   ✅ Loaded {inserted:,} records")
    if errors:
        print(f"   ⚠️  {errors:,} errors")

    return inserted


def load_county_data(county: str, download_date: str = None, dry_run: bool = False):
    """Load all parsed data for a county"""

    if download_date is None:
        download_date = str(date.today())

    parsed_dir = Path(__file__).parent.parent / 'data' / 'parsed' / download_date
    county_upper = county.upper()
    year = date.today().year

    print("=" * 80)
    print(f"LOADING {county_upper} DATA INTO SUPABASE")
    print("=" * 80)

    print(f"\n📂 Parsed directory: {parsed_dir}")
    print(f"🗄️  Database: {SUPABASE_URL}")

    if dry_run:
        print(f"🧪 DRY RUN MODE - No database changes")

    if not parsed_dir.exists():
        print(f"\n❌ Parsed directory not found: {parsed_dir}")
        print("   Run parse_county_files.py first")
        return

    total_loaded = 0

    # Load NAL data (properties)
    nal_file = parsed_dir / f"{county_upper}_NAL_parsed.csv"
    if nal_file.exists():
        count = load_nal_data(nal_file, county_upper, year, dry_run)
        total_loaded += count
    else:
        print(f"\n⚠️  NAL file not found: {nal_file.name}")

    # Load SDF data (sales)
    sdf_file = parsed_dir / f"{county_upper}_SDF_parsed.csv"
    if sdf_file.exists():
        count = load_sdf_data(sdf_file, county_upper, dry_run)
        total_loaded += count
    else:
        print(f"\n⚠️  SDF file not found: {sdf_file.name}")

    print("\n" + "=" * 80)
    print("✅ DATA LOAD COMPLETE")
    print("=" * 80)

    print(f"\n📊 Total records loaded: {total_loaded:,}")

    if not dry_run:
        # Verify in database
        print("\n🔍 Verifying data in database...")

        try:
            # Count properties
            parcels_result = supabase.table('florida_parcels')\
                .select('*', count='exact')\
                .eq('county', county_upper)\
                .limit(0)\
                .execute()

            print(f"   florida_parcels: {parcels_result.count:,} records for {county_upper}")

            # Count sales
            sales_result = supabase.table('property_sales_history')\
                .select('*', count='exact')\
                .eq('county', county_upper)\
                .limit(0)\
                .execute()

            print(f"   property_sales_history: {sales_result.count:,} records for {county_upper}")

        except Exception as e:
            print(f"   ⚠️  Verification error: {e}")

    print("\n💡 Next steps:")
    print("   1. Verify data in Supabase dashboard")
    print("   2. Test queries on frontend")
    print("   3. Process additional counties")
    print("   4. Set up daily update schedule")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Load County Data into Supabase')
    parser.add_argument('--county', required=True, help='County name (e.g., BROWARD)')
    parser.add_argument('--date', help='Download date (YYYY-MM-DD), default: today')
    parser.add_argument('--dry-run', action='store_true', help='Preview without loading')

    args = parser.parse_args()

    load_county_data(args.county, args.date, args.dry_run)


if __name__ == '__main__':
    main()
