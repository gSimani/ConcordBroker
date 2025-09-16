"""
Insert complete property data into florida_parcels table with all required fields
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('apps/web/.env')

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print("Inserting complete property data into florida_parcels...")
print("=" * 60)

supabase = create_client(url, key)

# Complete sample properties with county field and all required data
sample_properties = [
    {
        "parcel_id": "504232100010",
        "county": "BROWARD",
        "phy_addr1": "123 OCEAN BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33301",
        "own_name": "OCEANVIEW PROPERTIES LLC",
        "owner_addr1": "123 OCEAN BLVD SUITE 100",
        "owner_city": "FORT LAUDERDALE",
        "owner_state": "FL",
        "owner_zip": "33301",
        "property_use": "011",
        "property_use_desc": "Office Building",
        "just_value": 3200000,
        "assessed_value": 2880000,
        "taxable_value": 2800000,
        "land_value": 1200000,
        "building_value": 2000000,
        "total_living_area": 25000,
        "land_sqft": 35000,
        "land_acres": 0.8,
        "year_built": 2018,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_price": 3100000,
        "sale_date": "2022-06-15",
        "subdivision": "OCEAN PLAZA"
    },
    {
        "parcel_id": "504232100011",
        "county": "BROWARD",
        "phy_addr1": "456 SUNRISE BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33304",
        "own_name": "SMITH JOHN & MARY",
        "owner_addr1": "456 SUNRISE BLVD",
        "owner_city": "FORT LAUDERDALE",
        "owner_state": "FL",
        "owner_zip": "33304",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "just_value": 525000,
        "assessed_value": 472500,
        "taxable_value": 422500,
        "land_value": 225000,
        "building_value": 300000,
        "total_living_area": 2800,
        "land_sqft": 8500,
        "land_acres": 0.2,
        "year_built": 2005,
        "bedrooms": 4,
        "bathrooms": 3,
        "sale_price": 485000,
        "sale_date": "2021-03-20",
        "subdivision": "SUNRISE ESTATES"
    },
    {
        "parcel_id": "504232100012",
        "county": "BROWARD",
        "phy_addr1": "789 LAS OLAS BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33301",
        "own_name": "WILLIAMS ROBERT",
        "owner_addr1": "789 LAS OLAS BLVD UNIT 1501",
        "owner_city": "FORT LAUDERDALE",
        "owner_state": "FL",
        "owner_zip": "33301",
        "property_use": "004",
        "property_use_desc": "Condominium",
        "just_value": 850000,
        "assessed_value": 765000,
        "taxable_value": 715000,
        "land_value": 450000,
        "building_value": 400000,
        "total_living_area": 1500,
        "land_sqft": 0,
        "land_acres": 0,
        "year_built": 2020,
        "bedrooms": 2,
        "bathrooms": 2,
        "sale_price": 825000,
        "sale_date": "2023-01-10",
        "subdivision": "LAS OLAS TOWERS"
    },
    {
        "parcel_id": "504232100013",
        "county": "BROWARD",
        "phy_addr1": "321 ATLANTIC AVE",
        "phy_city": "HOLLYWOOD",
        "phy_state": "FL",
        "phy_zipcd": "33019",
        "own_name": "BEACH HOLDINGS INC",
        "owner_addr1": "321 ATLANTIC AVE",
        "owner_city": "HOLLYWOOD",
        "owner_state": "FL",
        "owner_zip": "33019",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "just_value": 725000,
        "assessed_value": 652500,
        "taxable_value": 602500,
        "land_value": 325000,
        "building_value": 400000,
        "total_living_area": 3200,
        "land_sqft": 10000,
        "land_acres": 0.23,
        "year_built": 1998,
        "bedrooms": 5,
        "bathrooms": 3,
        "sale_price": 695000,
        "sale_date": "2020-07-15",
        "subdivision": "HOLLYWOOD BEACH"
    },
    {
        "parcel_id": "504232100014",
        "county": "BROWARD",
        "phy_addr1": "555 CORAL WAY",
        "phy_city": "CORAL SPRINGS",
        "phy_state": "FL",
        "phy_zipcd": "33065",
        "own_name": "MARTINEZ ROBERTO",
        "owner_addr1": "555 CORAL WAY",
        "owner_city": "CORAL SPRINGS",
        "owner_state": "FL",
        "owner_zip": "33065",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "just_value": 425000,
        "assessed_value": 382500,
        "taxable_value": 332500,
        "land_value": 175000,
        "building_value": 250000,
        "total_living_area": 2400,
        "land_sqft": 7500,
        "land_acres": 0.17,
        "year_built": 2010,
        "bedrooms": 3,
        "bathrooms": 2,
        "sale_price": 395000,
        "sale_date": "2019-11-30",
        "subdivision": "CORAL RIDGE"
    },
    {
        "parcel_id": "504232100015",
        "county": "MIAMI-DADE",
        "phy_addr1": "100 BISCAYNE BLVD",
        "phy_city": "MIAMI",
        "phy_state": "FL",
        "phy_zipcd": "33131",
        "own_name": "BISCAYNE TOWER LLC",
        "owner_addr1": "100 BISCAYNE BLVD FLOOR 50",
        "owner_city": "MIAMI",
        "owner_state": "FL",
        "owner_zip": "33131",
        "property_use": "011",
        "property_use_desc": "Office Building",
        "just_value": 45000000,
        "assessed_value": 40500000,
        "taxable_value": 38000000,
        "land_value": 15000000,
        "building_value": 30000000,
        "total_living_area": 150000,
        "land_sqft": 45000,
        "land_acres": 1.03,
        "year_built": 2019,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_price": 43000000,
        "sale_date": "2021-09-15",
        "subdivision": "BISCAYNE CENTER"
    },
    {
        "parcel_id": "504232100016",
        "county": "BROWARD",
        "phy_addr1": "2500 UNIVERSITY DR",
        "phy_city": "DAVIE",
        "phy_state": "FL",
        "phy_zipcd": "33324",
        "own_name": "UNIVERSITY PLAZA LLC",
        "owner_addr1": "2500 UNIVERSITY DR",
        "owner_city": "DAVIE",
        "owner_state": "FL",
        "owner_zip": "33324",
        "property_use": "011",
        "property_use_desc": "Shopping Center",
        "just_value": 12500000,
        "assessed_value": 11250000,
        "taxable_value": 10500000,
        "land_value": 4500000,
        "building_value": 8000000,
        "total_living_area": 85000,
        "land_sqft": 125000,
        "land_acres": 2.87,
        "year_built": 2005,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_price": 12000000,
        "sale_date": "2022-12-01",
        "subdivision": "UNIVERSITY COMMONS"
    },
    {
        "parcel_id": "504232100017",
        "county": "BROWARD",
        "phy_addr1": "8500 GRIFFIN RD",
        "phy_city": "COOPER CITY",
        "phy_state": "FL",
        "phy_zipcd": "33328",
        "own_name": "GRIFFIN ESTATES HOA",
        "owner_addr1": "8500 GRIFFIN RD",
        "owner_city": "COOPER CITY",
        "owner_state": "FL",
        "owner_zip": "33328",
        "property_use": "001",
        "property_use_desc": "Single Family",
        "just_value": 625000,
        "assessed_value": 562500,
        "taxable_value": 512500,
        "land_value": 275000,
        "building_value": 350000,
        "total_living_area": 2850,
        "land_sqft": 9500,
        "land_acres": 0.22,
        "year_built": 2008,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sale_price": 595000,
        "sale_date": "2020-04-10",
        "subdivision": "GRIFFIN ESTATES"
    }
]

successful = 0
for prop in sample_properties:
    try:
        # Check if property exists
        existing = supabase.table('florida_parcels').select('id').eq('parcel_id', prop['parcel_id']).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table('florida_parcels').update(prop).eq('parcel_id', prop['parcel_id']).execute()
            print(f"Updated: {prop['phy_addr1']}, {prop['phy_city']} - ${prop['just_value']:,.0f}")
            successful += 1
        else:
            # Insert new
            result = supabase.table('florida_parcels').insert(prop).execute()
            print(f"Inserted: {prop['phy_addr1']}, {prop['phy_city']} - ${prop['just_value']:,.0f}")
            successful += 1
            
    except Exception as e:
        error_msg = str(e)
        if 'row-level security' in error_msg.lower():
            print(f"\nRLS is blocking write access to florida_parcels table.")
            print("The API can still read the existing data.")
            break
        else:
            print(f"Error with {prop['parcel_id']}: {error_msg[:100]}")

print("\n" + "=" * 60)
print(f"Successfully loaded {successful} properties")
print("\nThe properties page at http://localhost:5173/properties should now display:")
print("- Property addresses (Site Address)")
print("- Owner names")
print("- Property values (Current Land Value, Just Value, Taxable Value)")
print("- Property types (from DOR use codes)")
print("- Building area (Adj. Bldg. S.F.)")
print("- Year built")
print("- Sales history data")
print("- Homestead exemption status")
print("\nClick on any property to see the full profile with all fields populated!")