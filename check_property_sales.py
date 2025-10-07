#!/usr/bin/env python3
"""Check if property has sales data and what format it's in"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

# Check the specific property
parcel_id = "1078130000370"

print(f"Checking sales data for property: {parcel_id}")
print("=" * 60)

# Get all data for this property
response = supabase.table('florida_parcels')\
    .select("*")\
    .eq('parcel_id', parcel_id)\
    .execute()

if response.data:
    prop = response.data[0]
    print("\n[Property Found]")
    print(f"County: {prop.get('county')}")
    print(f"Address: {prop.get('phy_addr1')}")

    # Check all sale-related fields
    print("\n[Sales Fields in Database]")
    sale_fields = [
        'sale_date', 'sale_price', 'sale_qualification',
        'sale_date1', 'sale_price1', 'sale_qual1',
        'sale_date2', 'sale_price2', 'sale_qual2',
        'sale_yr1', 'sale_mo1', 'sale_day1',
        'book', 'page', 'cin', 'or_book', 'or_page',
        'doc_no', 'doc_type', 'sale_code'
    ]

    for field in sale_fields:
        if field in prop and prop[field]:
            print(f"  {field}: {prop[field]}")

    # Also check for sales_history array or related data
    if 'sales_history' in prop:
        print(f"\n[Sales History Array]")
        print(f"  sales_history: {prop['sales_history']}")

# Now check if there's a separate sales table
print("\n" + "=" * 60)
print("Checking for separate sales tables...")

try:
    # Try florida_sales table
    sales_response = supabase.table('florida_sales')\
        .select("*")\
        .eq('parcel_id', parcel_id)\
        .limit(5)\
        .execute()

    if sales_response.data:
        print("\n[florida_sales table]")
        for sale in sales_response.data:
            print(f"  Date: {sale.get('sale_date')}, Price: {sale.get('sale_price')}")
except:
    print("No florida_sales table found")

try:
    # Try sales_history table
    history_response = supabase.table('sales_history')\
        .select("*")\
        .eq('parcel_id', parcel_id)\
        .limit(5)\
        .execute()

    if history_response.data:
        print("\n[sales_history table]")
        for sale in history_response.data:
            print(f"  Date: {sale.get('sale_date')}, Price: {sale.get('sale_price')}")
except:
    print("No sales_history table found")

# Check for any property with sales in the same format
print("\n" + "=" * 60)
print("Finding ANY property with sales data for reference...")

any_sales = supabase.table('florida_parcels')\
    .select("parcel_id, county, sale_date, sale_price, sale_qualification, book, page, or_book, or_page, doc_no")\
    .neq('sale_price', None)\
    .gt('sale_price', 1000)\
    .limit(5)\
    .execute()

if any_sales.data:
    print("\n[Properties WITH Sales Data]")
    for prop in any_sales.data:
        print(f"\nParcel: {prop['parcel_id']} ({prop['county']} County)")
        print(f"  Sale Date: {prop.get('sale_date')}")
        print(f"  Sale Price: ${prop.get('sale_price'):,.0f}")
        print(f"  Book/Page: {prop.get('book')}/{prop.get('page')}")
        print(f"  OR Book/Page: {prop.get('or_book')}/{prop.get('or_page')}")
        print(f"  Doc No: {prop.get('doc_no')}")
