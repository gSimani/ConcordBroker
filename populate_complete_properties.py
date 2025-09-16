"""
Populate florida_parcels table with complete sample data for testing
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/api'))
from supabase_client import get_supabase_client

# Load environment variables
load_dotenv('apps/web/.env')

supabase = get_supabase_client()

# Sample properties with complete data
sample_properties = [
    {
        "parcel_id": "494222110010",
        "phy_addr1": "1200 BRICKELL AVE",
        "phy_city": "MIAMI",
        "phy_state": "FL",
        "phy_zipcd": "33131",
        "owner_name": "BRICKELL TOWER LLC",
        "owner_addr1": "1200 BRICKELL AVE",
        "owner_city": "MIAMI",
        "owner_state": "FL", 
        "owner_zip": "33131",
        "property_use": "011",
        "property_use_desc": "Office Building",
        "year_built": 2018,
        "total_living_area": 450000,
        "bedrooms": 0,
        "bathrooms": 0,
        "land_sqft": 85000,
        "land_acres": 1.95,
        "just_value": 125000000,
        "assessed_value": 118750000,
        "taxable_value": 112500000,
        "land_value": 45000000,
        "building_value": 80000000,
        "sale_date": "2019-06-15",
        "sale_price": 130000000,
        "county": "BROWARD",
        "subdivision": "BRICKELL CENTER"
    },
    {
        "parcel_id": "504232100050",
        "phy_addr1": "3930 N OCEAN DR",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33308",
        "owner_name": "OCEAN TOWERS CONDO ASSOC",
        "owner_addr1": "3930 N OCEAN DR",
        "owner_city": "FORT LAUDERDALE",
        "owner_state": "FL",
        "owner_zip": "33308",
        "property_use": "004",
        "property_use_desc": "Condominium",
        "year_built": 1985,
        "total_living_area": 2400,
        "bedrooms": 3,
        "bathrooms": 3,
        "land_sqft": 0,
        "land_acres": 0,
        "just_value": 1850000,
        "assessed_value": 1665000,
        "taxable_value": 1572500,
        "land_value": 650000,
        "building_value": 1200000,
        "sale_date": "2022-03-20",
        "sale_price": 1950000,
        "county": "BROWARD",
        "subdivision": "OCEAN TOWERS"
    },
    {
        "parcel_id": "514245330040",
        "phy_addr1": "789 SUNSET BLVD",
        "phy_city": "HOLLYWOOD",
        "phy_state": "FL",
        "phy_zipcd": "33019",
        "owner_name": "JOHNSON FAMILY TRUST",
        "owner_addr1": "789 SUNSET BLVD",
        "owner_city": "HOLLYWOOD",
        "owner_state": "FL",
        "owner_zip": "33019",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "year_built": 1998,
        "total_living_area": 3200,
        "bedrooms": 4,
        "bathrooms": 3,
        "land_sqft": 12500,
        "land_acres": 0.29,
        "just_value": 785000,
        "assessed_value": 706500,
        "taxable_value": 667000,
        "land_value": 385000,
        "building_value": 400000,
        "sale_date": "2020-08-10",
        "sale_price": 810000,
        "county": "BROWARD",
        "subdivision": "HOLLYWOOD HILLS"
    },
    {
        "parcel_id": "524257250080",
        "phy_addr1": "2500 UNIVERSITY DR",
        "phy_city": "DAVIE",
        "phy_state": "FL",
        "phy_zipcd": "33324",
        "owner_name": "UNIVERSITY PLAZA LLC",
        "owner_addr1": "100 CORPORATE BLVD",
        "owner_city": "MIAMI",
        "owner_state": "FL",
        "owner_zip": "33126",
        "property_use": "011",
        "property_use_desc": "Shopping Center",
        "year_built": 2005,
        "total_living_area": 125000,
        "bedrooms": 0,
        "bathrooms": 0,
        "land_sqft": 435600,
        "land_acres": 10.0,
        "just_value": 28500000,
        "assessed_value": 25650000,
        "taxable_value": 24200000,
        "land_value": 8500000,
        "building_value": 20000000,
        "sale_date": "2021-12-01",
        "sale_price": 29750000,
        "county": "BROWARD",
        "subdivision": "UNIVERSITY COMMONS"
    },
    {
        "parcel_id": "534268140120",
        "phy_addr1": "456 CORAL SPRINGS DR",
        "phy_city": "CORAL SPRINGS",
        "phy_state": "FL",
        "phy_zipcd": "33065",
        "owner_name": "MARTINEZ ROBERTO & MARIA",
        "owner_addr1": "456 CORAL SPRINGS DR",
        "owner_city": "CORAL SPRINGS",
        "owner_state": "FL",
        "owner_zip": "33065",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "year_built": 2003,
        "total_living_area": 2850,
        "bedrooms": 4,
        "bathrooms": 2,
        "land_sqft": 9800,
        "land_acres": 0.22,
        "just_value": 565000,
        "assessed_value": 508500,
        "taxable_value": 480000,
        "land_value": 265000,
        "building_value": 300000,
        "sale_date": "2019-04-15",
        "sale_price": 575000,
        "county": "BROWARD",
        "subdivision": "CORAL RIDGE"
    },
    {
        "parcel_id": "544279350150",
        "phy_addr1": "100 LAS OLAS BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33301",
        "owner_name": "LAS OLAS TOWER LP",
        "owner_addr1": "100 LAS OLAS BLVD",
        "owner_city": "FORT LAUDERDALE",
        "owner_state": "FL",
        "owner_zip": "33301",
        "property_use": "039",
        "property_use_desc": "Hotel/Motel",
        "year_built": 2016,
        "total_living_area": 380000,
        "bedrooms": 0,
        "bathrooms": 0,
        "land_sqft": 65340,
        "land_acres": 1.5,
        "just_value": 95000000,
        "assessed_value": 85500000,
        "taxable_value": 80750000,
        "land_value": 35000000,
        "building_value": 60000000,
        "sale_date": "2018-09-30",
        "sale_price": 98000000,
        "county": "BROWARD",
        "subdivision": "LAS OLAS CENTER"
    },
    {
        "parcel_id": "554280460180",
        "phy_addr1": "8500 GRIFFIN RD",
        "phy_city": "COOPER CITY",
        "phy_state": "FL",
        "phy_zipcd": "33328",
        "owner_name": "SMITH JOHN & SUSAN",
        "owner_addr1": "8500 GRIFFIN RD",
        "owner_city": "COOPER CITY",
        "owner_state": "FL",
        "owner_zip": "33328",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "year_built": 2008,
        "total_living_area": 3450,
        "bedrooms": 5,
        "bathrooms": 3,
        "land_sqft": 14500,
        "land_acres": 0.33,
        "just_value": 925000,
        "assessed_value": 832500,
        "taxable_value": 786000,
        "land_value": 425000,
        "building_value": 500000,
        "sale_date": "2021-07-20",
        "sale_price": 950000,
        "county": "BROWARD",
        "subdivision": "GRIFFIN ESTATES"
    },
    {
        "parcel_id": "564291570210",
        "phy_addr1": "1850 SAWGRASS MILLS CIR",
        "phy_city": "SUNRISE",
        "phy_state": "FL",
        "phy_zipcd": "33323",
        "owner_name": "SAWGRASS RETAIL LLC",
        "owner_addr1": "1850 SAWGRASS MILLS CIR",
        "owner_city": "SUNRISE",
        "owner_state": "FL",
        "owner_zip": "33323",
        "property_use": "011",
        "property_use_desc": "Regional Mall",
        "year_built": 1990,
        "total_living_area": 2350000,
        "bedrooms": 0,
        "bathrooms": 0,
        "land_sqft": 3920400,
        "land_acres": 90.0,
        "just_value": 485000000,
        "assessed_value": 436500000,
        "taxable_value": 412000000,
        "land_value": 185000000,
        "building_value": 300000000,
        "sale_date": "2017-05-10",
        "sale_price": 490000000,
        "county": "BROWARD",
        "subdivision": "SAWGRASS MILLS"
    }
]

print("Inserting sample properties with complete data...")

try:
    # First, check if we have the right columns
    result = supabase.table('florida_parcels').select('*').limit(1).execute()
    if result.data:
        print(f"Existing columns: {list(result.data[0].keys())}")
    
    # Insert each property
    for prop in sample_properties:
        try:
            # Try to update if exists, otherwise insert
            existing = supabase.table('florida_parcels').select('id').eq('parcel_id', prop['parcel_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('florida_parcels').update(prop).eq('parcel_id', prop['parcel_id']).execute()
                print(f"Updated: {prop['phy_addr1']}, {prop['phy_city']}")
            else:
                # Insert new
                result = supabase.table('florida_parcels').insert(prop).execute()
                print(f"Inserted: {prop['phy_addr1']}, {prop['phy_city']}")
                
        except Exception as e:
            print(f"Error with property {prop['parcel_id']}: {str(e)}")
            
    print("\nVerifying data...")
    
    # Query the properties we just inserted
    for prop in sample_properties[:3]:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', prop['parcel_id']).execute()
        if result.data:
            data = result.data[0]
            print(f"\n{data.get('phy_addr1')}, {data.get('phy_city')}")
            print(f"  Just Value: ${data.get('just_value', 0):,.0f}")
            print(f"  Building Area: {data.get('total_living_area', 0):,} sqft")
            print(f"  Land: {data.get('land_sqft', 0):,} sqft")
            print(f"  Year Built: {data.get('year_built', 'N/A')}")
    
    print("\nSample data loaded successfully!")
    print("You can now search for properties in cities like:")
    print("- FORT LAUDERDALE")
    print("- MIAMI")
    print("- HOLLYWOOD") 
    print("- DAVIE")
    print("- CORAL SPRINGS")
    print("- COOPER CITY")
    print("- SUNRISE")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()