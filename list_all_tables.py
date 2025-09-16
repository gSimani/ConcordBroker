"""
List all tables in Supabase to see what's actually available
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/api'))

# Load environment variables
load_dotenv('apps/web/.env')

# Import after loading env
from supabase import create_client

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print(f"Connecting to: {url}")
print("=" * 60)

# Create client
supabase = create_client(url, key)

# List of possible table names to try
possible_tables = [
    'florida_parcels',
    'fl_parcels',
    'parcels',
    'properties',
    'property',
    'latest_parcels',
    'property_sales_history',
    'fl_sdf_sales',
    'nav_assessments',
    'florida_permits',
    'sunbiz_corporate'
]

print("Testing table access:")
for table_name in possible_tables:
    try:
        result = supabase.table(table_name).select('*').limit(1).execute()
        if result.data:
            print(f"✓ {table_name}: EXISTS - {len(result.data)} row(s) retrieved")
            # Show columns
            if result.data[0]:
                columns = list(result.data[0].keys())
                print(f"  Columns: {', '.join(columns[:10])}")
                if len(columns) > 10:
                    print(f"  ... and {len(columns) - 10} more columns")
        else:
            print(f"✓ {table_name}: EXISTS but EMPTY")
    except Exception as e:
        if '42P01' in str(e):
            print(f"✗ {table_name}: DOES NOT EXIST")
        else:
            print(f"? {table_name}: ERROR - {str(e)[:100]}")

print("\n" + "=" * 60)
print("Trying to query 'properties' table directly:")
try:
    result = supabase.table('properties').select('*').limit(5).execute()
    print(f"Found {len(result.data)} properties")
    if result.data:
        for prop in result.data:
            print(f"\n  ID: {prop.get('id')}")
            print(f"  Parcel: {prop.get('parcel_id')}")
            print(f"  Address: {prop.get('phy_addr1')}, {prop.get('phy_city')}")
except Exception as e:
    print(f"Error: {str(e)}")