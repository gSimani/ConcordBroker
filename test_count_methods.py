"""
Test different count query methods to find which works
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from supabase import create_client

# Use EXACT same connection as property_live_api.py
url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

print(f"Connecting to: {url}")
supabase = create_client(url, key)

print("=" * 80)
print("TESTING COUNT QUERY METHODS")
print("=" * 80)
print()

# Test parameters
min_sqft = 10000
max_sqft = 20000

print(f"Filter: {min_sqft} - {max_sqft} sqft")
print()

# Method 1: head=True (current API method)
print("Method 1: select('*', count='exact', head=True)")
try:
    response = supabase.table('florida_parcels')\
        .select('*', count='exact', head=True)\
        .gte('total_living_area', min_sqft)\
        .lte('total_living_area', max_sqft)\
        .execute()

    print(f"✅ Count: {response.count if hasattr(response, 'count') else 'NO COUNT'}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Method 2: No head parameter (diagnostic script method)
print("Method 2: select('*', count='exact') + limit(1)")
try:
    response = supabase.table('florida_parcels')\
        .select('*', count='exact')\
        .gte('total_living_area', min_sqft)\
        .lte('total_living_area', max_sqft)\
        .limit(1)\
        .execute()

    print(f"✅ Count: {response.count if hasattr(response, 'count') else 'NO COUNT'}")
    print(f"   Data returned: {len(response.data)} records")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Method 3: Minimal select
print("Method 3: select('parcel_id', count='exact') + limit(1)")
try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .gte('total_living_area', min_sqft)\
        .lte('total_living_area', max_sqft)\
        .limit(1)\
        .execute()

    print(f"✅ Count: {response.count if hasattr(response, 'count') else 'NO COUNT'}")
    print(f"   Data returned: {len(response.data)} records")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print("Expected count: 37,726")
print("If Method 1 fails or returns wrong count, we need to switch to Method 2 or 3")
print("=" * 80)
