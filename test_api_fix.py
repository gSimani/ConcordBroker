"""
Test the API fix for building sqft filters
"""
import requests
import json
import sys

# Fix unicode encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("TESTING API FIX - Building SqFt Filter")
print("=" * 80)
print()

# Test the API endpoint
url = "http://localhost:8000/api/properties/search"
params = {
    "minBuildingSqFt": 10000,
    "maxBuildingSqFt": 20000,
    "limit": 10
}

print(f"Testing: {url}")
print(f"Params: {params}")
print()

try:
    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()

        print("✅ API Response Received")
        print()
        print(f"Success: {data.get('success')}")
        print(f"Total Count: {data.get('total', 0):,}")
        print(f"Properties Returned: {len(data.get('data', []))}")
        print()

        if data.get('total', 0) > 10000:
            print("🎉 FIX VERIFIED! Count is correct (37,726 expected)")
        elif data.get('total', 0) == 0:
            print("⚠️  Total is 0 - Fix may not be active or count query issue")
        elif data.get('total', 0) < 100:
            print(f"❌ Total is {data.get('total', 0)} - Still showing wrong count")
        else:
            print(f"✓ Total is {data.get('total', 0):,} - Looks reasonable")

        # Show sample properties
        if data.get('data'):
            print()
            print("Sample Properties:")
            print("-" * 80)
            for i, prop in enumerate(data['data'][:5], 1):
                sqft = prop.get('buildingSqFt') or prop.get('tot_lvg_area', 0)
                parcel = prop.get('parcel_id', 'N/A')
                county = prop.get('county', 'N/A')
                print(f"  {i}. {parcel:<20} {county:<15} {sqft:>8,} sqft")

    else:
        print(f"❌ API Error: Status {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 80)