#!/usr/bin/env python3
"""Simple script to find properties with sales data"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

print("Searching for properties with sales data...")
print("=" * 60)

# Simple query - just get properties and check sales fields in Python
response = supabase.table('florida_parcels')\
    .select("parcel_id, sale_date, sale_price, sale_qualification, phy_addr1, county, subdivision")\
    .limit(1000)\
    .execute()

if response.data:
    # Filter in Python
    properties_with_sales = []
    for prop in response.data:
        if prop.get('sale_date') and prop.get('sale_price') and prop.get('sale_price') > 0:
            properties_with_sales.append(prop)

    if properties_with_sales:
        print(f"\n[OK] Found {len(properties_with_sales)} properties with sales data:\n")

        # Show first 10
        for i, prop in enumerate(properties_with_sales[:10], 1):
            print(f"{i}. Parcel ID: {prop['parcel_id']}")
            print(f"   County: {prop.get('county', 'Unknown')}")
            print(f"   Sale Date: {prop['sale_date']}")
            print(f"   Sale Price: ${prop['sale_price']:,.0f}")
            print(f"   Type: {prop.get('sale_qualification', 'N/A')}")
            print(f"   Address: {prop.get('phy_addr1', 'N/A')}")
            print(f"   Subdivision: {prop.get('subdivision', 'N/A')}")
            print()

        # Export test parcels for Playwright
        print("\n" + "=" * 60)
        print("TEST PARCELS FOR PLAYWRIGHT:")
        print("Copy these into test-sales-history-connection.cjs:")
        print()
        print("const testProperties = [")
        for prop in properties_with_sales[:5]:
            print(f"  '{prop['parcel_id']}',  // ${prop['sale_price']:,.0f} on {prop['sale_date']}")
        print("];")
    else:
        print("[WARN] No properties found with complete sales data")
else:
    print("[ERROR] No data returned from database")