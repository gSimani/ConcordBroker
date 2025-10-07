"""
Fix property_sales_history table schema by adding missing county column
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("FIXING PROPERTY_SALES_HISTORY TABLE SCHEMA")
print("=" * 80)
print()

# Check current schema
print("[1] Checking current table structure...")

try:
    # Get one record to see columns
    result = supabase.table('property_sales_history').select('*').limit(1).execute()

    if result.data and len(result.data) > 0:
        columns = list(result.data[0].keys())
        print(f"  Current columns: {', '.join(columns)}")

        if 'county' in columns:
            print("\n  ✓ 'county' column already exists!")
            print("  No schema fix needed.")
            exit(0)
        else:
            print(f"\n  ✗ 'county' column is missing")
            print(f"  Found 'county_no' instead" if 'county_no' in columns else "")
    else:
        print("  Table is empty, checking if it exists...")
        # Try to query to see if table exists
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
        print(f"  Table exists with {result.count} records")

except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

print("\n[2] Adding 'county' column...")
print("  NOTE: This requires direct SQL execution via Supabase Dashboard")
print()
print("  Please run this SQL in Supabase SQL Editor:")
print()
print("  " + "-" * 76)
print("  ALTER TABLE property_sales_history ADD COLUMN IF NOT EXISTS county TEXT;")
print("  CREATE INDEX IF NOT EXISTS idx_sales_county ON property_sales_history(county);")
print("  " + "-" * 76)
print()
print("  After running the SQL, run the import script:")
print("  python scripts/import_broward_sdf_auto.py")
print()
print("=" * 80)
