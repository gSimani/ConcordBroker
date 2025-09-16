"""
Insert sample properties data into the properties table
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

# Import after loading env
from supabase import create_client

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print(f"Connecting to Supabase...")
supabase = create_client(url, key)

# Sample properties that match the 'properties' table schema
sample_properties = [
    {
        "parcel_id": "504232100010",
        "owner_name": "OCEANVIEW PROPERTIES LLC",
        "property_address": "123 OCEAN BLVD",
        "city": "FORT LAUDERDALE",
        "state": "FL",
        "zip_code": "33301",
        "property_type": "Commercial",
        "year_built": 2018,
        "total_sqft": 25000,
        "lot_size_sqft": 35000,
        "bedrooms": 0,
        "bathrooms": 0,
        "assessed_value": 2500000.0,
        "market_value": 3200000.0,
        "last_sale_date": "2022-06-15",
        "last_sale_price": 3100000.0
    },
    {
        "parcel_id": "504232100011",
        "owner_name": "SMITH JOHN & MARY",
        "property_address": "456 SUNRISE BLVD",
        "city": "FORT LAUDERDALE",
        "state": "FL",
        "zip_code": "33304",
        "property_type": "Single Family",
        "year_built": 2005,
        "total_sqft": 2800,
        "lot_size_sqft": 8500,
        "bedrooms": 4,
        "bathrooms": 3,
        "assessed_value": 450000.0,
        "market_value": 525000.0,
        "last_sale_date": "2021-03-20",
        "last_sale_price": 485000.0
    },
    {
        "parcel_id": "504232100012",
        "owner_name": "JOHNSON FAMILY TRUST",
        "property_address": "789 LAS OLAS BLVD",
        "city": "FORT LAUDERDALE",
        "state": "FL",
        "zip_code": "33301",
        "property_type": "Condo",
        "year_built": 2020,
        "total_sqft": 1500,
        "lot_size_sqft": 0,
        "bedrooms": 2,
        "bathrooms": 2,
        "assessed_value": 750000.0,
        "market_value": 850000.0,
        "last_sale_date": "2023-01-10",
        "last_sale_price": 825000.0
    },
    {
        "parcel_id": "504232100013",
        "owner_name": "BEACH HOLDINGS INC",
        "property_address": "321 ATLANTIC AVE",
        "city": "HOLLYWOOD",
        "state": "FL",
        "zip_code": "33019",
        "property_type": "Single Family",
        "year_built": 1998,
        "total_sqft": 3200,
        "lot_size_sqft": 10000,
        "bedrooms": 5,
        "bathrooms": 3,
        "assessed_value": 680000.0,
        "market_value": 725000.0,
        "last_sale_date": "2020-07-15",
        "last_sale_price": 695000.0
    },
    {
        "parcel_id": "504232100014",
        "owner_name": "MARTINEZ ROBERTO",
        "property_address": "555 CORAL WAY",
        "city": "CORAL SPRINGS",
        "state": "FL",
        "zip_code": "33065",
        "property_type": "Single Family",
        "year_built": 2010,
        "total_sqft": 2400,
        "lot_size_sqft": 7500,
        "bedrooms": 3,
        "bathrooms": 2,
        "assessed_value": 385000.0,
        "market_value": 425000.0,
        "last_sale_date": "2019-11-30",
        "last_sale_price": 395000.0
    }
]

print(f"Inserting {len(sample_properties)} sample properties...")

for prop in sample_properties:
    try:
        # Check if property exists
        existing = supabase.table('properties').select('id').eq('parcel_id', prop['parcel_id']).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table('properties').update(prop).eq('parcel_id', prop['parcel_id']).execute()
            print(f"✓ Updated: {prop['property_address']}, {prop['city']}")
        else:
            # Insert new
            result = supabase.table('properties').insert(prop).execute()
            print(f"✓ Inserted: {prop['property_address']}, {prop['city']}")
    except Exception as e:
        print(f"✗ Error with {prop['parcel_id']}: {str(e)[:100]}")

print("\nVerifying data...")

# Query the inserted properties
result = supabase.table('properties').select('*').limit(10).execute()
print(f"\nTotal properties in table: {len(result.data)}")
for prop in result.data:
    print(f"  - {prop.get('property_address')}, {prop.get('city')} (${prop.get('market_value', 0):,.0f})")

print("\nDone! Properties are ready to be displayed.")