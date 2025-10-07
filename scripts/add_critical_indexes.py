"""
Add Critical Performance Indexes to Supabase
This will dramatically improve search and query performance
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(__file__).parent.parent / '.env.mcp'
load_dotenv(env_path, override=True)

# Supabase connection
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_KEY:
    print("❌ Error: SUPABASE_SERVICE_ROLE_KEY not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("ADDING CRITICAL PERFORMANCE INDEXES")
print("=" * 80)

# Indexes to create
indexes = [
    {
        'name': 'idx_florida_parcels_parcel_id',
        'table': 'florida_parcels',
        'column': 'parcel_id',
        'description': 'Primary parcel lookup'
    },
    {
        'name': 'idx_florida_parcels_county',
        'table': 'florida_parcels',
        'column': 'county',
        'description': 'County filtering'
    },
    {
        'name': 'idx_florida_parcels_owner_name',
        'table': 'florida_parcels',
        'column': 'owner_name',
        'description': 'Owner search'
    },
    {
        'name': 'idx_florida_parcels_phy_addr1',
        'table': 'florida_parcels',
        'column': 'phy_addr1',
        'description': 'Address search'
    },
    {
        'name': 'idx_florida_parcels_phy_city',
        'table': 'florida_parcels',
        'column': 'phy_city',
        'description': 'City filtering'
    },
    {
        'name': 'idx_florida_parcels_just_value',
        'table': 'florida_parcels',
        'column': 'just_value',
        'description': 'Value filtering'
    },
    {
        'name': 'idx_florida_parcels_dor_uc',
        'table': 'florida_parcels',
        'column': 'dor_uc',
        'description': 'Property type filtering'
    },
]

print("\n📊 Creating indexes on florida_parcels...")
print("This may take several minutes for large tables...")
print()

created = 0
skipped = 0
errors = 0

for idx in indexes:
    try:
        sql = f"""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx['name']}
        ON {idx['table']}({idx['column']});
        """

        print(f"Creating {idx['name']}... ({idx['description']})")

        # Note: Supabase Python client doesn't support raw SQL execution
        # You need to run this via Supabase SQL Editor or use psycopg2
        print(f"  ⚠️  Please run this SQL in Supabase SQL Editor:")
        print(f"  {sql.strip()}")
        print()

    except Exception as e:
        print(f"  ❌ Error: {e}")
        errors += 1

print("\n" + "=" * 80)
print("INDEX CREATION INSTRUCTIONS")
print("=" * 80)
print("""
To add these indexes:

1. Go to Supabase Dashboard: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp
2. Click "SQL Editor" in the left sidebar
3. Copy and paste the SQL from: supabase/migrations/add_critical_indexes.sql
4. Click "Run"

The indexes will be created in the background (CONCURRENTLY means no table locking).

Expected performance improvement:
- Search queries: 10-100x faster
- Property detail pages: 5-20x faster
- Filter operations: 50-200x faster

Total time to create: 5-15 minutes (depends on table size)
""")

print("\n✅ Index SQL file ready at: supabase/migrations/add_critical_indexes.sql")
