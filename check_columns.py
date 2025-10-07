#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

# Get one property to see all columns
response = supabase.table('florida_parcels')\
    .select("*")\
    .limit(1)\
    .execute()

if response.data:
    columns = list(response.data[0].keys())
    print("Available columns in florida_parcels table:")
    print("=" * 60)
    
    # Look for sales-related columns
    sales_cols = []
    book_cols = []
    doc_cols = []
    
    for col in sorted(columns):
        if 'sale' in col.lower():
            sales_cols.append(col)
        if 'book' in col.lower() or 'page' in col.lower():
            book_cols.append(col)
        if 'doc' in col.lower() or 'cin' in col.lower() or 'or_' in col.lower():
            doc_cols.append(col)
    
    print("\nSales-related columns:")
    for col in sales_cols:
        print(f"  - {col}")
    
    print("\nBook/Page columns:")
    for col in book_cols:
        print(f"  - {col}")
    
    print("\nDocument/CIN columns:")
    for col in doc_cols:
        print(f"  - {col}")

# Now find a property with actual sales data
print("\n" + "=" * 60)
print("Finding properties with actual sales data...")

sales_props = supabase.table('florida_parcels')\
    .select("parcel_id, county, sale_date, sale_price, sale_qualification")\
    .gt('sale_price', 1000)\
    .limit(5)\
    .execute()

if sales_props.data:
    print("\nProperties with sales data:")
    for prop in sales_props.data:
        if prop.get('sale_date'):
            print(f"  {prop['parcel_id']} - ${prop.get('sale_price', 0):,.0f} on {prop.get('sale_date')}")
