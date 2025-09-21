"""
Test Supabase directly to find the issue
"""

from supabase import create_client

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing Supabase query directly...")

# Test 1: Basic query with pagination
print("\n1. Basic query with limit 10:")
query = supabase.table('florida_parcels').select('*').range(0, 9)
result = query.execute()
print(f"   Returned: {len(result.data)} properties")

# Test 2: Count total without any filters
print("\n2. Count total properties:")
count_result = supabase.table('florida_parcels').select('*', count='exact', head=True).execute()
print(f"   Total: {count_result.count:,} properties")

# Test 3: Query with pagination like the API does
print("\n3. Query like the API (offset 0, limit 100):")
offset = 0
limit = 100
query = supabase.table('florida_parcels').select('*').range(offset, offset + limit - 1)
result = query.execute()
print(f"   Returned: {len(result.data)} properties")

# Test 4: What the API is actually building
print("\n4. Exact API query simulation:")
query = supabase.table('florida_parcels').select('*')
# Don't filter addresses - the API removed this
# Apply pagination
query = query.range(0, 99)  # First 100
result = query.execute()
print(f"   Returned: {len(result.data)} properties")

# Show first property
if result.data:
    first = result.data[0]
    print(f"\n   First property:")
    print(f"     Parcel ID: {first.get('parcel_id')}")
    print(f"     Address: {first.get('phy_addr1')}")
    print(f"     City: {first.get('phy_city')}")

print("\n" + "="*60)
print("SUMMARY:")
print(f"Database has {count_result.count:,} total properties")
print("API should be returning this count when no filters are applied")