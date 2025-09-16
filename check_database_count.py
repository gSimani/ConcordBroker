"""
Check property counts in Supabase database
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import requests

# Load environment variables
load_dotenv()

print("=" * 60)
print("CHECKING DATABASE PROPERTY COUNTS")
print("=" * 60)

# Get credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')

print(f"\nConnecting to Supabase: {url}")

# Create client
supabase = create_client(url, key)

# List of tables to check
tables_to_check = [
    'florida_parcels',
    'fl_properties', 
    'properties',
    'fl_parcel',
    'parcels',
    'property_data'
]

print("\nChecking tables for property data:")
print("-" * 40)

for table_name in tables_to_check:
    try:
        # Try to count records using a simple query
        response = supabase.table(table_name).select('id').limit(1).execute()
        
        # If successful, try to get count
        try:
            # Try to get actual count
            count_response = supabase.table(table_name).select('*', count='exact', head=True).execute()
            count = count_response.count
            print(f"✓ {table_name}: {count:,} records" if count else f"✓ {table_name}: 0 records")
        except:
            # If count fails, at least we know table exists
            print(f"✓ {table_name}: Table exists (count unavailable)")
            
    except Exception as e:
        error_msg = str(e)
        if "relation" in error_msg and "does not exist" in error_msg:
            print(f"✗ {table_name}: Table does not exist")
        else:
            print(f"? {table_name}: Error - {error_msg[:50]}")

# Try direct API call
print("\n" + "-" * 40)
print("Checking via direct API call:")

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Range': '0-0'
}

# Try florida_parcels
api_url = f"{url}/rest/v1/florida_parcels"
try:
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        # Get content-range header for count
        content_range = response.headers.get('content-range', '')
        if content_range:
            # Format: "0-0/total"
            parts = content_range.split('/')
            if len(parts) == 2:
                total = parts[1]
                print(f"✓ florida_parcels: {total} total records (via API)")
        else:
            # Try to get from response
            data = response.json()
            if isinstance(data, list):
                print(f"✓ florida_parcels: Retrieved {len(data)} records (total unknown)")
    else:
        print(f"✗ API call failed: {response.status_code}")
except Exception as e:
    print(f"✗ API error: {e}")

print("\n" + "=" * 60)