"""
Check properties table structure
"""
import os
import sys
from dotenv import load_dotenv
import json

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/api'))

# Load environment variables
load_dotenv('apps/web/.env')

# Import after loading env
from supabase import create_client

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print(f"Checking 'properties' table structure...")
print("=" * 60)

# Create client
supabase = create_client(url, key)

try:
    # Get sample data from properties table
    result = supabase.table('properties').select('*').limit(5).execute()
    
    if result.data:
        print(f"Found {len(result.data)} records in 'properties' table")
        
        # Show first record's structure
        first_record = result.data[0]
        print("\nTable columns and sample values:")
        print("-" * 40)
        for key, value in first_record.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        # Show all records
        print("\n" + "=" * 60)
        print("All records:")
        for i, record in enumerate(result.data, 1):
            print(f"\nRecord {i}:")
            print(f"  ID: {record.get('id')}")
            print(f"  Parcel ID: {record.get('parcel_id')}")
            print(f"  Address: {record.get('phy_addr1')}")
            print(f"  City: {record.get('phy_city')}")
            print(f"  Owner: {record.get('own_name')}")
            print(f"  Just Value: {record.get('jv')}")
            print(f"  DOR Code: {record.get('dor_uc')}")
    else:
        print("No data found in 'properties' table")
        
except Exception as e:
    print(f"Error accessing 'properties' table: {str(e)}")

# Now try to insert sample data
print("\n" + "=" * 60)
print("Inserting sample property data...")

sample_properties = [
    {
        "parcel_id": "504232100001",
        "phy_addr1": "123 OCEAN BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_zipcd": "33301",
        "own_name": "SMITH JOHN",
        "dor_uc": "001",
        "jv": 750000,
        "tv_sd": 650000,
        "lnd_val": 350000,
        "tot_lvg_area": 2500,
        "lnd_sqfoot": 8500,
        "act_yr_blt": 2005,
        "sale_prc1": 725000,
        "sale_yr1": "2022"
    },
    {
        "parcel_id": "504232100002",
        "phy_addr1": "456 SUNRISE BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_zipcd": "33304",
        "own_name": "JOHNSON MARY",
        "dor_uc": "001",
        "jv": 450000,
        "tv_sd": 400000,
        "lnd_val": 200000,
        "tot_lvg_area": 1800,
        "lnd_sqfoot": 6000,
        "act_yr_blt": 1998,
        "sale_prc1": 425000,
        "sale_yr1": "2021"
    },
    {
        "parcel_id": "504232100003",
        "phy_addr1": "789 LAS OLAS BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_zipcd": "33301",
        "own_name": "WILLIAMS ROBERT",
        "dor_uc": "011",
        "jv": 2500000,
        "tv_sd": 2200000,
        "lnd_val": 1000000,
        "tot_lvg_area": 15000,
        "lnd_sqfoot": 25000,
        "act_yr_blt": 2010,
        "sale_prc1": 2400000,
        "sale_yr1": "2023"
    }
]

for prop in sample_properties:
    try:
        # Check if property exists
        existing = supabase.table('properties').select('id').eq('parcel_id', prop['parcel_id']).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table('properties').update(prop).eq('parcel_id', prop['parcel_id']).execute()
            print(f"Updated: {prop['phy_addr1']}, {prop['phy_city']}")
        else:
            # Insert new
            result = supabase.table('properties').insert(prop).execute()
            print(f"Inserted: {prop['phy_addr1']}, {prop['phy_city']}")
    except Exception as e:
        print(f"Error with property {prop['parcel_id']}: {str(e)[:100]}")

print("\nDone!")