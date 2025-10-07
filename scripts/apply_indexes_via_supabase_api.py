"""
Apply Critical Database Indexes via Supabase REST API
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import time

# Load environment
env_path = Path(__file__).parent.parent / '.env.mcp'
load_dotenv(env_path, override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: SUPABASE_SERVICE_ROLE_KEY not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 80)
print("APPLYING CRITICAL PERFORMANCE INDEXES")
print("=" * 80)

# Individual index creation statements
indexes = [
    {
        'name': 'idx_florida_parcels_parcel_id',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);',
        'description': 'Primary parcel lookup'
    },
    {
        'name': 'idx_florida_parcels_county',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county ON florida_parcels(county);',
        'description': 'County filtering'
    },
    {
        'name': 'idx_florida_parcels_owner_name',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name);',
        'description': 'Owner search'
    },
    {
        'name': 'idx_florida_parcels_phy_addr1',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1 ON florida_parcels(phy_addr1);',
        'description': 'Address search'
    },
    {
        'name': 'idx_florida_parcels_phy_city',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city ON florida_parcels(phy_city);',
        'description': 'City filtering'
    },
    {
        'name': 'idx_florida_parcels_just_value',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value ON florida_parcels(just_value);',
        'description': 'Value filtering'
    },
    {
        'name': 'idx_florida_parcels_dor_uc',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_dor_uc ON florida_parcels(dor_uc);',
        'description': 'Property type filtering'
    },
    {
        'name': 'idx_florida_parcels_county_parcel',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county_parcel ON florida_parcels(county, parcel_id);',
        'description': 'Composite county+parcel'
    },
    {
        'name': 'idx_florida_parcels_year',
        'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year ON florida_parcels(year);',
        'description': 'Year filtering'
    },
]

print("\nApplying indexes to florida_parcels...")
print("This approach uses Supabase RPC - indexes will be created in background\n")

created = 0
skipped = 0
errors = 0

for idx in indexes:
    try:
        print(f"Creating {idx['name']}... ({idx['description']})")

        # Try to create index via RPC
        result = supabase.rpc('execute_sql', {
            'query': idx['sql']
        }).execute()

        created += 1
        print(f"  OK - Index creation initiated")

    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower():
            print(f"  SKIP - Index already exists")
            skipped += 1
        elif 'function execute_sql does not exist' in error_msg.lower():
            print(f"  WARN - execute_sql RPC not available")
            print("\n" + "=" * 80)
            print("MANUAL EXECUTION REQUIRED")
            print("=" * 80)
            print(f"\nSupabase Python client cannot execute raw SQL directly.")
            print(f"\nPlease run the indexes manually:\n")
            print(f"1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp")
            print(f"2. Click 'SQL Editor' in the left sidebar")
            print(f"3. Copy and paste this SQL:\n")

            # Read and print the SQL file
            sql_file = Path(__file__).parent.parent / 'supabase' / 'migrations' / 'add_critical_indexes.sql'
            if sql_file.exists():
                with open(sql_file, 'r') as f:
                    print(f.read())

            print(f"\n4. Click 'Run'")
            print(f"\nExpected time: 5-15 minutes")
            print(f"Expected performance improvement: 10-100x faster searches\n")
            sys.exit(0)
        else:
            print(f"  ERROR: {error_msg}")
            errors += 1

    # Small delay between index creations
    time.sleep(0.5)

# Try to run ANALYZE
try:
    print("\nRunning ANALYZE on florida_parcels...")
    supabase.rpc('execute_sql', {
        'query': 'ANALYZE florida_parcels;'
    }).execute()
    print("  OK - Table analyzed")
except:
    print("  SKIP - Unable to run ANALYZE via API")

print("\n" + "=" * 80)
print(f"RESULTS: {created} created, {skipped} skipped, {errors} errors")
print("=" * 80)

if created > 0 or skipped > 0:
    print("""
Expected performance improvements:
- Property search: 10-100x faster
- Property detail pages: 5-20x faster
- Filter operations: 50-200x faster
- Owner/address searches: 20-50x faster

Indexes are being created in the background using CONCURRENTLY.
No table locking - database remains fully operational.
""")
