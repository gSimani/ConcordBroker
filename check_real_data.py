#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

# Check current data for property
parcel_id = "1078130000370"

print(f"Checking ACTUAL database data for property: {parcel_id}")
print("=" * 60)

# Get all fields
response = supabase.table('florida_parcels').select("*").eq('parcel_id', parcel_id).execute()

if response.data:
    prop = response.data[0]

    print("\n[Property Values from Database]")
    print(f"Land Value: ${prop.get('land_value', 0):,}")
    print(f"Building Value: ${prop.get('building_value', 0):,}")
    print(f"Just Value: ${prop.get('just_value', 0):,}")
    print(f"Assessed Value: ${prop.get('assessed_value', 0):,}")
    print(f"Taxable Value: ${prop.get('taxable_value', 0):,}")

    print("\n[Land Information]")
    print(f"Land Use: {prop.get('land_use_desc', '')}")
    print(f"Zoning: {prop.get('zoning', '')}")
    print(f"PA Zone: {prop.get('pa_zone', '')}")
    print(f"Land SqFt: {prop.get('land_sqft', 0):,}")

    print("\n[Sales Information in Database]")
    print(f"Sale Date: {prop.get('sale_date', '')}")
    sale_price = prop.get('sale_price', 0)
    if sale_price is None:
        sale_price = 0
    print(f"Sale Price: ${sale_price:,}")
    print(f"Sale Qualification: {prop.get('sale_qualification', '')}")
    print(f"OR Book: {prop.get('or_book', '')}")
    print(f"OR Page: {prop.get('or_page', '')}")

    print("\n[Owner Information]")
    print(f"Owner Name: {prop.get('owner_name', '')}")

    print("\n[Address Information]")
    print(f"Physical Address: {prop.get('phy_addr1', '')} {prop.get('phy_addr2', '')}")
    print(f"City: {prop.get('phy_city', '')}")
    print(f"State: {prop.get('phy_state', '')}")
    print(f"Zip: {prop.get('phy_zipcd', '')}")
else:
    print("Property not found in database")

print("\n" + "=" * 60)
print("COMPARISON WITH PUBLIC RECORDS:")
print("=" * 60)
print("\nPer Public Records (2025):")
print("  Land Value: $41,260")
print("  Building Value: $0")
print("  Market Value: $41,260")
print("  Assessed Value: $27,458")
print("  Land Use: GENERAL")
print("  Muni Zone: B-1")
print("  PA Zone: 6300 - COMMERCIAL - RESTRICTED")
print("  Square Ft: 2,063")
print("  Zoning Code: GP-GOVERNMENT PROPERTY DISTRICT")
print("\nSales History per Public Records:")
print("  06/26/2020: $0 (OR 32000-4868) - CITY OF HOMESTEAD ECO REDING ORD")
print("  03/16/2020: $0 (OR 31872-2543) - CITY OF HOMESTEAD ECO REDING ORD")
print("  02/01/1976: $20,000")