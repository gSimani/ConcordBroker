import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv('VITE_SUPABASE_URL', os.getenv('SUPABASE_URL'))
key = os.getenv('VITE_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

if not url or not key:
    print("Error: Supabase credentials not found in environment variables")
    exit(1)

supabase: Client = create_client(url, key)

# Property data for 12681 NW 78 MNR, PARKLAND - only fields that exist
property_data = {
    'parcel_id': '474131031040',
    'phy_addr1': '12681 NW 78 MNR',
    'phy_city': 'PARKLAND',
    'phy_state': 'FL',
    'phy_zipcd': '33076',
    'owner_name': 'INVITATION HOMES',
    'owner_addr1': 'P O BOX 650449',
    'owner_city': 'DALLAS',
    'owner_state': 'TX',
    'owner_zip': '75265',
    'just_value': 580000,
    'taxable_value': 475000,
    'land_value': 145000,
    'building_value': 435000,
    'year_built': 2003,
    'total_living_area': 3285,
    'bedrooms': 5,
    'bathrooms': 3.5,
    'property_use': '001',
    'county': 'BROWARD'
}

print("Updating property data for 12681 NW 78 MNR, PARKLAND")
print("=" * 50)

# Update the florida_parcels table
try:
    # First check if it exists
    existing = supabase.table('florida_parcels').select('parcel_id').eq('parcel_id', property_data['parcel_id']).execute()
    
    if existing.data:
        # Update existing record
        response = supabase.table('florida_parcels').update(property_data).eq('parcel_id', property_data['parcel_id']).execute()
        print(f"Updated florida_parcels record for parcel {property_data['parcel_id']}")
    else:
        # Insert new record
        response = supabase.table('florida_parcels').insert(property_data).execute()
        print(f"Inserted new florida_parcels record for parcel {property_data['parcel_id']}")
        
except Exception as e:
    print(f"Error updating florida_parcels: {e}")

# Add sales history (simplified)
sales_history = [
    {
        'parcel_id': '474131031040',
        'sale_date': '2021-08-15',
        'sale_price': 425000
    },
    {
        'parcel_id': '474131031040',
        'sale_date': '2018-03-20',
        'sale_price': 380000
    },
    {
        'parcel_id': '474131031040',
        'sale_date': '2015-06-10',
        'sale_price': 350000
    }
]

print("\nAdding sales history...")
for sale in sales_history:
    try:
        # Check if sale already exists
        existing = supabase.table('property_sales_history').select('id').eq('parcel_id', sale['parcel_id']).eq('sale_date', sale['sale_date']).execute()
        
        if not existing.data:
            response = supabase.table('property_sales_history').insert(sale).execute()
            print(f"  Added sale from {sale['sale_date']} for ${sale['sale_price']:,}")
        else:
            print(f"  - Sale from {sale['sale_date']} already exists")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 50)
print("Property data loading complete!")
print(f"Property URL: http://localhost:5174/properties/parkland/12681-nw-78-mnr")

# Verify the data
print("\nVerifying loaded data...")
response = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
if response.data:
    prop = response.data[0]
    print(f"  Address: {prop.get('phy_addr1')}, {prop.get('phy_city')}")
    print(f"  Owner: {prop.get('owner_name')}")
    print(f"  Just Value: ${prop.get('just_value'):,}" if prop.get('just_value') else "  Just Value: N/A")
    print(f"  Year Built: {prop.get('year_built')}")
    print(f"  Living Area: {prop.get('total_living_area')} sqft")
    print(f"  Bedrooms: {prop.get('bedrooms')}, Bathrooms: {prop.get('bathrooms')}")