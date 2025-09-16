import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

# Test the updated query logic
address_or_parcel_id = "12681-nw-78-mnr"
city = "parkland"

print(f"Testing property data fetch for: {address_or_parcel_id}, {city}")
print("=" * 50)

# Simulate the improved logic
address_variations = [
    address_or_parcel_id,
    address_or_parcel_id.replace('-', ' ').upper(),
    address_or_parcel_id.lower().replace('-', ' '),
    address_or_parcel_id.lower().replace('-', ' ').replace(' ', ' ').strip()
]

print("Address variations to test:")
for i, addr in enumerate(address_variations, 1):
    print(f"  {i}. '{addr}'")

print("\nTesting each variation:")

for i, addr in enumerate(address_variations, 1):
    try:
        response = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city, owner_name').ilike('phy_addr1', f'%{addr}%').limit(5).execute()
        
        if response.data:
            print(f"  SUCCESS Variation {i} ('{addr}') found {len(response.data)} results:")
            for prop in response.data:
                print(f"    - {prop.get('parcel_id')}: {prop.get('phy_addr1')}")
        else:
            print(f"  NO RESULTS Variation {i} ('{addr}') found no results")
    except Exception as e:
        print(f"  ERROR Variation {i} error: {e}")

# Test the exact match we expect
print(f"\nTesting exact match for '12681 NW 78 MNR':")
response = supabase.table('florida_parcels').select('*').eq('phy_addr1', '12681 NW 78 MNR').execute()

if response.data:
    prop = response.data[0]
    print(f"SUCCESS Exact match found!")
    print(f"  Parcel ID: {prop.get('parcel_id')}")
    print(f"  Address: {prop.get('phy_addr1')}")
    print(f"  Owner: {prop.get('owner_name')}")
    print(f"  Just Value: ${prop.get('just_value'):,}" if prop.get('just_value') else "  Just Value: N/A")
else:
    print("ERROR No exact match found")