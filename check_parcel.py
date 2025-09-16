import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

# Search for the property by address
result = supabase.table('florida_parcels').select('parcel_id, phy_addr1, owner_name, assessed_value').ilike('phy_addr1', '%12681 NW 78%').execute()

if result.data:
    print("Found property:")
    for prop in result.data:
        print(f"  Parcel ID: {prop['parcel_id']}")
        print(f"  Address: {prop['phy_addr1']}")
        print(f"  Owner: {prop['owner_name']}")
        print(f"  Assessed: {prop['assessed_value']}")
else:
    print("Property not found by address")

# Also try the full parcel ID
result2 = supabase.table('florida_parcels').select('parcel_id, phy_addr1').eq('parcel_id', '474131031040').execute()
if result2.data:
    print("\nFound by full parcel ID: 474131031040")
