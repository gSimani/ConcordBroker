#!/usr/bin/env python3
"""Find properties with actual sales data in Supabase"""

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

try:
    # Query for properties with sales data
    response = supabase.table('florida_parcels')\
        .select("parcel_id, sale_date, sale_price, sale_qualification, phy_addr1, county, subdivision")\
        .not_.is_('sale_date', None)\
        .not_.is_('sale_price', None)\
        .gt('sale_price', 0)\
        .order('sale_date', desc=True)\
        .limit(20)\
        .execute()

    if response.data and len(response.data) > 0:
        print(f"\n[OK] Found {len(response.data)} properties with sales data:\n")

        # Group by county
        by_county = {}
        for prop in response.data:
            county = prop.get('county', 'Unknown')
            if county not in by_county:
                by_county[county] = []
            by_county[county].append(prop)

        for county, properties in by_county.items():
            print(f"\n{county} COUNTY ({len(properties)} properties):")
            print("-" * 40)
            for prop in properties[:5]:  # Show max 5 per county
                print(f"  Parcel ID: {prop['parcel_id']}")
                print(f"  Sale Date: {prop['sale_date']}")
                print(f"  Sale Price: ${prop['sale_price']:,.0f}")
                print(f"  Type: {prop['sale_qualification'] or 'N/A'}")
                print(f"  Address: {prop['phy_addr1'] or 'N/A'}")
                print(f"  Subdivision: {prop['subdivision'] or 'N/A'}")
                print()

        # Also check for properties in specific subdivisions
        print("\n" + "=" * 60)
        print("CHECKING FOR SUBDIVISION SALES (for comparison feature):")

        # Get unique subdivisions with sales
        subdivisions = {}
        for prop in response.data:
            if prop.get('subdivision'):
                sub = prop['subdivision']
                if sub not in subdivisions:
                    subdivisions[sub] = 0
                subdivisions[sub] += 1

        if subdivisions:
            print(f"\nFound sales in {len(subdivisions)} subdivisions:")
            for sub, count in list(subdivisions.items())[:5]:
                print(f"  - {sub}: {count} sales")

        # Export test parcels
        test_parcels = [prop['parcel_id'] for prop in response.data[:10]]
        print("\n" + "=" * 60)
        print("RECOMMENDED TEST PARCELS (with confirmed sales data):")
        print("Use these in the Playwright test for better results:")
        print()
        for parcel in test_parcels:
            print(f"  '{parcel}',")

    else:
        print("[WARN] No properties found with sales data")

        # Check if there's any data at all
        count_response = supabase.table('florida_parcels')\
            .select("parcel_id", count='exact')\
            .limit(1)\
            .execute()

        print(f"\nTotal records in database: {count_response.count}")

        # Check for any non-null sale_date
        date_check = supabase.table('florida_parcels')\
            .select("parcel_id, sale_date")\
            .not_.is_('sale_date', None)\
            .limit(5)\
            .execute()

        if date_check.data:
            print(f"\nFound {len(date_check.data)} records with sale_date values:")
            for rec in date_check.data:
                print(f"  - {rec['parcel_id']}: {rec['sale_date']}")

except Exception as e:
    print(f"[ERROR] Error querying database: {e}")
    print(f"URL: {url[:30]}...")
    print(f"Key exists: {'Yes' if key else 'No'}")