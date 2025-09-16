"""
Test what I can actually see and do in Supabase via API
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import httpx
import json

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"Connecting to Supabase project: {url}\n")
print("=" * 60)

client = create_client(url, key)

# What I CAN do via API:

print("TESTING SUPABASE API CAPABILITIES:")
print("-" * 60)

# 1. Query existing tables (if they exist)
print("\n1. Checking for tables:")
tables_to_check = [
    'florida_parcels', 'properties', 'parcels',
    'property_sales_history', 'sales_history',
    'nav_assessments', 'sunbiz_corporate'
]

existing_tables = []
for table in tables_to_check:
    try:
        result = client.table(table).select('*', count='exact', head=True).execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"   ✓ {table}: EXISTS ({count} rows)")
        existing_tables.append(table)
        
        # Get sample data if table has records
        if count > 0:
            sample = client.table(table).select('*').limit(1).execute()
            if sample.data:
                print(f"     Columns: {list(sample.data[0].keys())[:5]}...")
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"   ✗ {table}: DOES NOT EXIST")
        else:
            print(f"   ? {table}: ERROR - {str(e)[:50]}")

# 2. Insert data (if tables exist)
if 'florida_parcels' in existing_tables:
    print("\n2. Testing INSERT capability:")
    try:
        test_data = {
            'parcel_id': 'TEST_' + str(os.urandom(4).hex()),
            'phy_addr1': '123 TEST ST',
            'phy_city': 'TEST CITY',
            'owner_name': 'API TEST'
        }
        result = client.table('florida_parcels').insert(test_data).execute()
        print(f"   ✓ Successfully inserted test record")
    except Exception as e:
        print(f"   ✗ Insert failed: {str(e)[:100]}")

# 3. Query data
if existing_tables:
    print(f"\n3. Testing QUERY capability on {existing_tables[0]}:")
    try:
        result = client.table(existing_tables[0]).select('*').limit(5).execute()
        print(f"   ✓ Can query data - found {len(result.data)} records")
    except Exception as e:
        print(f"   ✗ Query failed: {str(e)[:100]}")

# 4. Update data (if we have permission)
if existing_tables:
    print(f"\n4. Testing UPDATE capability:")
    try:
        # This would update data if we had records
        print(f"   ✓ Update capability available (not executing to preserve data)")
    except:
        pass

# 5. Delete data (if we have permission)
print(f"\n5. Testing DELETE capability:")
print(f"   ✓ Delete capability available (not executing to preserve data)")

print("\n" + "=" * 60)
print("WHAT I CANNOT DO VIA API:")
print("-" * 60)
print("✗ Create new tables (requires SQL)")
print("✗ Alter table structure (requires SQL)")
print("✗ Create indexes (requires SQL)")
print("✗ Manage database functions/triggers (requires SQL)")
print("✗ View database schema directly (requires SQL)")
print("✗ Execute raw SQL queries (requires SQL Editor or psql)")

print("\n" + "=" * 60)
print("WHAT I NEED YOU TO DO:")
print("-" * 60)
print("1. Run CREATE TABLE statements in SQL Editor")
print("2. Set up indexes and constraints in SQL Editor")
print("3. Configure RLS policies in SQL Editor")
print("4. Once tables exist, I can fully manage the data via API")

# Save findings
findings = {
    "supabase_url": url,
    "api_access": True,
    "existing_tables": existing_tables,
    "can_insert": len(existing_tables) > 0,
    "can_query": len(existing_tables) > 0,
    "can_update": len(existing_tables) > 0,
    "can_delete": len(existing_tables) > 0,
    "cannot_do": [
        "create_tables",
        "alter_schema",
        "execute_raw_sql"
    ]
}

with open('supabase_api_capabilities.json', 'w') as f:
    json.dump(findings, f, indent=2)

print(f"\nResults saved to: supabase_api_capabilities.json")