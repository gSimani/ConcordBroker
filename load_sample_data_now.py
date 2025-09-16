#!/usr/bin/env python3
"""Load sample data into Supabase for testing autocomplete"""

from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

# Create Supabase client
print(f"Connecting to Supabase...")
supabase = create_client(supabase_url, supabase_key)

# Sample data with the address you're looking for
sample_properties = [
    {
        'parcel_id': '064210010010',
        'phy_addr1': '3930 SW 53 CT',
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'JOHN DOE',
        'taxable_value': 450000,
        'year_built': 1985,
        'total_living_area': 2200,
        'bedrooms': 3,
        'bathrooms': 2,
        'sale_date': '2020-05-15',
        'sale_price': 425000,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010011',
        'phy_addr1': '3931 SW 53 CT',
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'JANE SMITH',
        'taxable_value': 475000,
        'year_built': 1986,
        'total_living_area': 2350,
        'bedrooms': 4,
        'bathrooms': 2.5,
        'sale_date': '2019-08-20',
        'sale_price': 440000,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010012',
        'phy_addr1': '3932 SW 53 CT',
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'ROBERT JOHNSON',
        'taxable_value': 430000,
        'year_built': 1985,
        'total_living_area': 2100,
        'bedrooms': 3,
        'bathrooms': 2,
        'sale_date': '2021-03-10',
        'sale_price': 415000,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010013',
        'phy_addr1': '3933 SW 53 CT',
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'MARY WILLIAMS',
        'taxable_value': 490000,
        'year_built': 1987,
        'total_living_area': 2400,
        'bedrooms': 4,
        'bathrooms': 3,
        'sale_date': '2022-01-25',
        'sale_price': 480000,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010014',
        'phy_addr1': '3940 SW 53 CT',
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'DAVID BROWN',
        'taxable_value': 460000,
        'year_built': 1986,
        'total_living_area': 2250,
        'bedrooms': 3,
        'bathrooms': 2.5,
        'sale_date': '2021-11-15',
        'sale_price': 455000,
        'is_redacted': False
    },
    # Add some variations to test address matching
    {
        'parcel_id': '064210010015',
        'phy_addr1': '3930 SW 53RD CT',  # Different format
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'TEST OWNER 1',
        'taxable_value': 400000,
        'year_built': 1985,
        'total_living_area': 2000,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010016',
        'phy_addr1': '3930 SW 53RD COURT',  # Full word
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'TEST OWNER 2',
        'taxable_value': 410000,
        'year_built': 1985,
        'total_living_area': 2050,
        'is_redacted': False
    },
    {
        'parcel_id': '064210010017',
        'phy_addr1': '3930 SOUTHWEST 53 COURT',  # Spelled out
        'phy_city': 'DAVIE',
        'phy_zipcd': '33314',
        'owner_name': 'TEST OWNER 3',
        'taxable_value': 420000,
        'year_built': 1985,
        'total_living_area': 2100,
        'is_redacted': False
    }
]

try:
    # Insert data into florida_parcels table
    print("Inserting sample properties...")
    result = supabase.table('florida_parcels').upsert(
        sample_properties,
        on_conflict='parcel_id'
    ).execute()
    
    print(f"✓ Inserted {len(sample_properties)} sample properties")
    
    # Verify data was inserted
    check = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city').limit(5).execute()
    print(f"\n✓ Verified {len(check.data)} properties in database:")
    for prop in check.data:
        print(f"  - {prop['parcel_id']}: {prop['phy_addr1']}, {prop['phy_city']}")
    
    # Test search for the specific address
    print("\nTesting search for '3930 SW 53'...")
    search_result = supabase.table('florida_parcels').select('*').ilike('phy_addr1', '%3930 SW 53%').execute()
    print(f"✓ Found {len(search_result.data)} matching properties")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nThe florida_parcels table might not exist.")
    print("Please create it first by running the SQL schema in Supabase dashboard.")

print("\nDone!")