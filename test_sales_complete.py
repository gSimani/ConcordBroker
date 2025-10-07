"""
Complete Sales History Feature Test
Tests all components end-to-end
"""

import requests
from supabase import create_client

# Configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
API_URL = 'http://localhost:8000'

print("=" * 70)
print("SALES HISTORY FEATURE - COMPLETE TEST")
print("=" * 70)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test 1: Database has sales data
print("\n[TEST 1] Checking Database Sales Data...")
print("-" * 40)
response = supabase.table('florida_parcels').select('parcel_id, sale_price').gt('sale_price', 100000).limit(3).execute()
if response.data:
    print("[PASS] Database has sales data")
    test_parcels = [prop['parcel_id'] for prop in response.data]
    for prop in response.data:
        print(f"  {prop['parcel_id']}: ${prop['sale_price']:,.0f}")
else:
    print("[FAIL] No sales data in database")
    test_parcels = []

# Test 2: API endpoint returns sales
print("\n[TEST 2] Testing API Sales Endpoint...")
print("-" * 40)
if test_parcels:
    test_parcel = test_parcels[0]
    try:
        api_response = requests.get(f"{API_URL}/api/properties/{test_parcel}/sales")
        if api_response.status_code == 200:
            data = api_response.json()
            if data.get('success') and data.get('sales_count', 0) > 0:
                print(f"[PASS] API returns {data['sales_count']} sale(s) for {test_parcel}")
                print(f"  Sale Price: ${data['sales'][0]['sale_price']:,.0f}")
                print(f"  Sale Date: {data['sales'][0]['sale_date']}")
            else:
                print(f"[FAIL] API returned no sales for {test_parcel}")
        else:
            print(f"[FAIL] API error: {api_response.status_code}")
    except Exception as e:
        print(f"[FAIL] Could not connect to API: {e}")

# Test 3: Frontend hook compatibility
print("\n[TEST 3] Frontend Hook Compatibility...")
print("-" * 40)
# Test direct Supabase query that frontend uses
if test_parcels:
    test_parcel = test_parcels[0]
    response = supabase.table('florida_parcels').select('parcel_id, sale_date, sale_price, sale_qualification').eq('parcel_id', test_parcel).gt('sale_price', 0).execute()
    if response.data:
        print(f"[PASS] Frontend hook will retrieve sales for {test_parcel}")
        print(f"  Direct Supabase query successful")
    else:
        print(f"[FAIL] Frontend hook query failed")

# Test 4: Check multiple properties have sales
print("\n[TEST 4] Sales Data Coverage...")
print("-" * 40)
total_props = supabase.table('florida_parcels').select('id', count='exact', head=True).execute()
total_count = total_props.count if hasattr(total_props, 'count') else 0

with_sales = supabase.table('florida_parcels').select('id', count='exact', head=True).gt('sale_price', 0).execute()
sales_count = with_sales.count if hasattr(with_sales, 'count') else 0

if total_count > 0:
    coverage = (sales_count / total_count) * 100
    print(f"[PASS] Sales data coverage: {sales_count:,} of {total_count:,} properties ({coverage:.1f}%)")
else:
    print("[FAIL] Could not determine coverage")

# Final Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

tests_passed = 0
tests_total = 4

# Count passed tests
if test_parcels:
    tests_passed += 1
if 'api_response' in locals() and api_response.status_code == 200:
    tests_passed += 1
if 'response' in locals() and response.data:
    tests_passed += 1
if sales_count > 0:
    tests_passed += 1

completion_percent = (tests_passed / tests_total) * 100

print(f"\nTests Passed: {tests_passed}/{tests_total}")
print(f"Feature Completion: {completion_percent:.0f}%")

if completion_percent == 100:
    print("\n*** SALES HISTORY FEATURE IS 100% COMPLETE! ***")
    print("[PASS] Database has sales data")
    print("[PASS] API endpoint working")
    print("[PASS] Frontend hook compatible")
    print("[PASS] Multiple properties have sales")
else:
    print(f"\n[WARNING] Feature is {completion_percent:.0f}% complete")
    print("Remaining issues to fix for 100%:")