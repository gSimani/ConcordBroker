import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv('VITE_SUPABASE_URL', os.getenv('SUPABASE_URL'))
key = os.getenv('VITE_SUPABASE_ANON_KEY', os.getenv('SUPABASE_ANON_KEY'))

if not url or not key:
    print("Error: Supabase credentials not found in environment variables")
    exit(1)

supabase: Client = create_client(url, key)

# Search for the property
search_address = "12681-nw-78-mnr"
search_address_clean = search_address.replace('-', ' ')
search_parcel = "12681 nw 78"

print(f"Searching for property: {search_address}")
print("=" * 50)

# Try florida_parcels table
print("\n1. Checking florida_parcels table...")
response = supabase.table('florida_parcels').select('*').ilike('phy_addr1', f'%{search_address_clean}%').limit(5).execute()
if response.data:
    print(f"Found {len(response.data)} results in florida_parcels")
    for prop in response.data:
        print(f"  - Parcel: {prop.get('parcel_id')}")
        print(f"    Address: {prop.get('phy_addr1')}, {prop.get('phy_city')}, FL {prop.get('phy_zipcd')}")
        print(f"    Owner: {prop.get('owner_name')}")
        print(f"    Just Value: ${prop.get('just_value')}")
        print(f"    Year Built: {prop.get('year_built')}")
        print(f"    Living Area: {prop.get('total_living_area')} sqft")
        print(f"    Bedrooms: {prop.get('bedrooms')}, Bathrooms: {prop.get('bathrooms')}")
else:
    print("  No results found")

# Try by parcel ID pattern
print("\n2. Checking by parcel ID pattern...")
response = supabase.table('florida_parcels').select('*').ilike('parcel_id', f'%{search_parcel}%').limit(5).execute()
if response.data:
    print(f"Found {len(response.data)} results by parcel ID")
    for prop in response.data:
        print(f"  - Parcel: {prop.get('parcel_id')}")
        print(f"    Address: {prop.get('phy_addr1')}, {prop.get('phy_city')}, FL {prop.get('phy_zipcd')}")
        print(f"    Owner: {prop.get('owner_name')}")
else:
    print("  No results found")

# Check properties table
print("\n3. Checking properties table...")
response = supabase.table('properties').select('*').ilike('property_address', f'%{search_address_clean}%').limit(5).execute()
if response.data:
    print(f"Found {len(response.data)} results in properties table")
    for prop in response.data:
        print(f"  - Property: {prop.get('property_address')}, {prop.get('city')}")
        print(f"    Owner: {prop.get('owner_name')}")
else:
    print("  No results found")

# Search for Parkland properties to get correct format
print("\n4. Sample Parkland properties (to find correct format)...")
response = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city').eq('phy_city', 'PARKLAND').limit(10).execute()
if response.data:
    print(f"Found {len(response.data)} Parkland properties:")
    for prop in response.data:
        print(f"  - {prop.get('parcel_id')}: {prop.get('phy_addr1')}")
else:
    print("  No Parkland properties found")

# Try exact address search
exact_address = "12681 NW 78 MNR"
print(f"\n5. Trying exact address: {exact_address}")
response = supabase.table('florida_parcels').select('*').eq('phy_addr1', exact_address).limit(1).execute()
if response.data:
    print("Found exact match!")
    prop = response.data[0]
    print(json.dumps({
        'parcel_id': prop.get('parcel_id'),
        'address': prop.get('phy_addr1'),
        'city': prop.get('phy_city'),
        'owner': prop.get('owner_name'),
        'just_value': prop.get('just_value'),
        'taxable_value': prop.get('taxable_value'),
        'year_built': prop.get('year_built'),
        'living_area': prop.get('total_living_area'),
        'bedrooms': prop.get('bedrooms'),
        'bathrooms': prop.get('bathrooms')
    }, indent=2))
else:
    print("  No exact match found")