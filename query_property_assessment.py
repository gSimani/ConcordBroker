from supabase import create_client, Client
import json

# Connect to database
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Query for the specific property
parcel_id = '3040190012860'
print(f'Searching for property: {parcel_id}')
print('=' * 60)

# First, get ALL fields for this property to see what data we have
response = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()

if response.data and len(response.data) > 0:
    prop = response.data[0]
    print('PROPERTY FOUND!')
    print()

    # Display key assessment fields
    print('=== PROPERTY ASSESSMENT VALUES ===')
    print(f'Parcel ID: {prop.get("parcel_id", "N/A")}')
    print(f'County: {prop.get("county", "N/A")}')
    print()

    print('Site Address:')
    print(f'  Physical Address 1: {prop.get("phy_addr1", "N/A")}')
    print(f'  Physical Address 2: {prop.get("phy_addr2", "N/A")}')
    print(f'  City: {prop.get("phy_city", "N/A")}')
    print(f'  Zip: {prop.get("phy_zipcd", "N/A")}')
    print()

    print('Owner Information:')
    print(f'  Owner Name: {prop.get("owner_name", "N/A")}')
    print(f'  Owner Address 1: {prop.get("owner_addr1", "N/A")}')
    print(f'  Owner City: {prop.get("owner_city", "N/A")}')
    print(f'  Owner State: {prop.get("owner_state", "N/A")}')
    print()

    print('Property Use:')
    print(f'  Property Use Code: {prop.get("property_use", "N/A")}')
    print(f'  Land Use Code: {prop.get("land_use_code", "N/A")}')
    print(f'  DOR Use Code: {prop.get("dor_uc", "N/A")}')
    print()

    print('Assessment Values:')
    print(f'  Land Value: ${prop.get("land_value", "N/A")}')
    print(f'  Building Value: ${prop.get("building_value", "N/A")}')
    print(f'  Just/Market Value: ${prop.get("just_value", "N/A")}')
    print(f'  Assessed Value: ${prop.get("assessed_value", "N/A")}')
    print(f'  Taxable Value: ${prop.get("taxable_value", "N/A")}')
    print()

    print('Tax Information:')
    print(f'  Property Tax: ${prop.get("property_tax", "N/A")}')
    print(f'  Tax Year: {prop.get("tax_year", "N/A")}')
    print(f'  Millage Rate: {prop.get("millage_rate", "N/A")}')
    print()

    print('Property Details:')
    print(f'  Year Built: {prop.get("year_built", "N/A")}')
    print(f'  Living Area: {prop.get("total_living_area", "N/A")} sq ft')
    print(f'  Land Sq Ft: {prop.get("land_sqft", "N/A")}')
    print(f'  Bedrooms: {prop.get("bedrooms", "N/A")}')
    print(f'  Bathrooms: {prop.get("bathrooms", "N/A")}')
    print()

    # Show all available fields for debugging
    print('=== ALL AVAILABLE FIELDS ===')
    for key, value in prop.items():
        if value is not None and value != '' and value != 0:
            print(f'  {key}: {value}')

else:
    print(f'Property {parcel_id} not found in database')