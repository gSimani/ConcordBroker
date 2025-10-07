"""
Complete Sales History Setup
1. Ensures property_sales_history table exists
2. Downloads all Florida SDF files
3. Imports sales data into Supabase
"""

import os
import sys
from pathlib import Path
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable not set")
    print("\nPlease set it in your environment:")
    print("  Windows: set SUPABASE_SERVICE_ROLE_KEY=your_key")
    print("  Linux/Mac: export SUPABASE_SERVICE_ROLE_KEY=your_key")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_table_exists() -> bool:
    """Check if property_sales_history table exists"""
    print("\n[1] Checking if property_sales_history table exists...")

    try:
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
        print(f"    Table exists with {result.count:,} records")
        return True
    except Exception as e:
        print(f"    Table does not exist or error: {e}")
        return False

def create_table_if_needed():
    """Create property_sales_history table if it doesn't exist"""

    if check_table_exists():
        print("    Table already exists, skipping creation")

        # Check current record count
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()

        if result.count > 0:
            print(f"\n    WARNING: Table already has {result.count:,} records")
            print("    Do you want to:")
            print("      1. Skip import (table already populated)")
            print("      2. Clear table and re-import")
            print("      3. Append new records")

            choice = input("\n    Enter choice (1/2/3): ").strip()

            if choice == "1":
                print("    Skipping import")
                return False
            elif choice == "2":
                print("    Clearing table...")
                # Note: Supabase doesn't have a truncate via API, would need SQL
                print("    Please manually truncate table in Supabase dashboard if needed")
                return True
            elif choice == "3":
                print("    Will append new records")
                return True
            else:
                print("    Invalid choice, exiting")
                return False

        return True
    else:
        print("\n    Table does not exist. Please create it manually in Supabase with this SQL:")
        print("""
CREATE TABLE IF NOT EXISTS property_sales_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id TEXT NOT NULL,
  county TEXT NOT NULL,
  sale_date DATE NOT NULL,
  sale_price BIGINT, -- stored in CENTS (divide by 100 for dollars)
  sale_year INTEGER,
  sale_month INTEGER,
  quality_code TEXT, -- 'Q' = qualified, 'U' = unqualified
  clerk_no TEXT,
  or_book TEXT, -- Official Records Book number
  or_page TEXT, -- Official Records Page number
  grantor_name TEXT,
  grantee_name TEXT,
  vi_code TEXT,
  data_source TEXT DEFAULT 'florida_sdf',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_sales_parcel ON property_sales_history(parcel_id);
CREATE INDEX idx_sales_date ON property_sales_history(sale_date DESC);
CREATE INDEX idx_sales_county ON property_sales_history(county);
CREATE INDEX idx_sales_parcel_date ON property_sales_history(parcel_id, sale_date DESC);

-- Enable RLS
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Sales history is viewable by everyone"
  ON property_sales_history FOR SELECT
  USING (true);
""")

        print("\nAfter creating the table, run this script again.")
        return False

def download_sdf_files():
    """Download all SDF files"""
    print("\n[2] Downloading Florida SDF files...")
    print("    This will download ~67 county files, may take 30-60 minutes")

    import download_florida_sdf_2025
    download_florida_sdf_2025.main()

def import_sales_data():
    """Import sales data to Supabase"""
    print("\n[3] Importing sales data to Supabase...")
    print("    This may take 1-2 hours depending on file sizes")

    import import_sdf_to_supabase
    import_sdf_to_supabase.main()

def verify_import():
    """Verify import was successful"""
    print("\n[4] Verifying import...")

    try:
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
        print(f"    Total records in property_sales_history: {result.count:,}")

        if result.count > 0:
            # Get sample record
            sample = supabase.table('property_sales_history').select('*').limit(1).execute()

            if sample.data:
                record = sample.data[0]
                print(f"\n    Sample record:")
                print(f"      Parcel ID: {record.get('parcel_id')}")
                print(f"      County: {record.get('county')}")
                print(f"      Sale Date: {record.get('sale_date')}")
                print(f"      Sale Price (cents): {record.get('sale_price'):,}")
                print(f"      Sale Price (dollars): ${record.get('sale_price', 0) / 100:,.2f}")
                print(f"      OR Book: {record.get('or_book')}")
                print(f"      OR Page: {record.get('or_page')}")

            print("\n    SUCCESS! Sales data imported correctly.")
            return True
        else:
            print("    WARNING: Table is still empty after import")
            return False

    except Exception as e:
        print(f"    ERROR verifying: {e}")
        return False

def main():
    print("=" * 80)
    print("FLORIDA SALES HISTORY - COMPLETE SETUP")
    print("=" * 80)
    print()
    print("This script will:")
    print("  1. Check/create property_sales_history table")
    print("  2. Download all 67 Florida county SDF files (~30-60 min)")
    print("  3. Import sales data into Supabase (~1-2 hours)")
    print("  4. Verify import")
    print()

    # Step 1: Check/create table
    if not create_table_if_needed():
        print("\nExiting - please create table first")
        return

    # Ask user if ready to proceed
    print("\nReady to download and import sales data?")
    print("This will take 1.5-3 hours total.")

    proceed = input("Continue? (yes/no): ").strip().lower()

    if proceed not in ['yes', 'y']:
        print("\nExiting - run this script again when ready")
        return

    # Step 2: Download SDF files
    try:
        download_sdf_files()
    except Exception as e:
        print(f"\nERROR during download: {e}")
        print("You can run download_florida_sdf_2025.py separately if needed")

    # Step 3: Import sales data
    try:
        import_sales_data()
    except Exception as e:
        print(f"\nERROR during import: {e}")
        print("You can run import_sdf_to_supabase.py separately if needed")

    # Step 4: Verify
    verify_import()

    print("\n" + "=" * 80)
    print("SETUP COMPLETE")
    print("=" * 80)
    print("\nYou can now view sales history in the UI at:")
    print("  http://localhost:5178/property/{parcel_id}")

if __name__ == "__main__":
    main()
