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

parcel_id = "474131031040"
print(f"Checking all tables for parcel: {parcel_id}")
print("=" * 50)

# Check florida_parcels
print("\n1. florida_parcels table:")
response = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).limit(1).execute()
if response.data:
    prop = response.data[0]
    print(f"  Found record with {len(prop)} fields")
    print(f"  Key fields:")
    for key in ['owner_name', 'phy_addr1', 'phy_city', 'just_value', 'taxable_value', 
                'year_built', 'total_living_area', 'bedrooms', 'bathrooms', 'land_value', 
                'building_value', 'lot_size', 'property_use']:
        print(f"    {key}: {prop.get(key)}")
else:
    print("  Not found")

# Check nav_parcel_assessments
print("\n2. nav_parcel_assessments table:")
response = supabase.table('nav_parcel_assessments').select('*').eq('parcel_id', parcel_id).limit(1).execute()
if response.data:
    prop = response.data[0]
    print(f"  Found record with {len(prop)} fields")
    for key in prop:
        if prop[key] is not None and prop[key] != '' and prop[key] != 0:
            print(f"    {key}: {prop[key]}")
else:
    print("  Not found")

# Check fl_nav_parcel_summary
print("\n3. fl_nav_parcel_summary table:")
response = supabase.table('fl_nav_parcel_summary').select('*').eq('parcel_id', parcel_id).limit(1).execute()
if response.data:
    prop = response.data[0]
    print(f"  Found record with {len(prop)} fields")
    for key in prop:
        if prop[key] is not None and prop[key] != '' and prop[key] != 0:
            print(f"    {key}: {prop[key]}")
else:
    print("  Not found")

# Check property_sales_history
print("\n4. property_sales_history table:")
response = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).limit(5).execute()
if response.data:
    print(f"  Found {len(response.data)} sales records")
    for sale in response.data:
        print(f"    Sale Date: {sale.get('sale_date')}, Price: ${sale.get('sale_price')}")
else:
    print("  Not found")

# Check fl_sdf_sales
print("\n5. fl_sdf_sales table:")
response = supabase.table('fl_sdf_sales').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).limit(5).execute()
if response.data:
    print(f"  Found {len(response.data)} sales records")
    for sale in response.data:
        print(f"    Sale Date: {sale.get('sale_date')}, Price: ${sale.get('sale_price')}")
else:
    print("  Not found")

# Check tax_certificates
print("\n6. tax_certificates table:")
response = supabase.table('tax_certificates').select('*').eq('parcel_id', parcel_id).limit(5).execute()
if response.data:
    print(f"  Found {len(response.data)} tax certificate records")
    for cert in response.data:
        print(f"    Certificate: {cert.get('certificate_number')}, Year: {cert.get('tax_year')}")
else:
    print("  Not found")

# Check a similar property with complete data
print("\n\n7. Checking a property with complete data for reference...")
response = supabase.table('florida_parcels').select('*').eq('phy_city', 'PARKLAND').not_.is_('year_built', 'null').not_.is_('bedrooms', 'null').limit(1).execute()
if response.data:
    prop = response.data[0]
    print(f"  Example complete property: {prop.get('parcel_id')}")
    print(f"  Address: {prop.get('phy_addr1')}")
    print(f"  Owner: {prop.get('owner_name')}")
    print(f"  Year Built: {prop.get('year_built')}")
    print(f"  Living Area: {prop.get('total_living_area')}")
    print(f"  Bedrooms: {prop.get('bedrooms')}, Bathrooms: {prop.get('bathrooms')}")
    print(f"  Just Value: ${prop.get('just_value')}")
    print(f"  Taxable Value: ${prop.get('taxable_value')}")
else:
    print("  No complete properties found")