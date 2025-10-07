"""
Check if parcel 402101327008 has sales data
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

parcel_id = '402101327008'

print(f"\nChecking sales for parcel {parcel_id}...\n")

# Check property_sales_history
result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).execute()

if result.data:
    print(f"Found {len(result.data)} sales records:")
    for i, sale in enumerate(result.data, 1):
        price = sale.get('sale_price', 0) / 100
        print(f"  {i}. Date: {sale.get('sale_date')}, Price: ${price:,.2f}, County: {sale.get('county')}")
else:
    print(f"NO sales found for parcel {parcel_id}")
    print("\nThis property genuinely has no sales history in the database.")
    print("The 'No Sales History Available' message is CORRECT for this parcel.")

# Check florida_parcels
print(f"\nChecking florida_parcels table...")
result2 = supabase.table('florida_parcels').select('parcel_id, sale_date, sale_price, county').eq('parcel_id', parcel_id).execute()

if result2.data:
    parcel = result2.data[0]
    print(f"  County: {parcel.get('county')}")
    print(f"  Sale Date: {parcel.get('sale_date')}")
    print(f"  Sale Price: {parcel.get('sale_price')}")
else:
    print("  No parcel data found")

print("\n" + "=" * 60)
print("Try this property instead (has sales): http://localhost:5178/property/474128000000")
print("=" * 60 + "\n")
