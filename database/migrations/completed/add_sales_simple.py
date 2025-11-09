"""
Add correct sales history - simple version
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

parcel_id = "474131031040"

# Add the most recent sale (most important)
sale_data = {
    "parcel_id": parcel_id,
    "sale_date": "2013-11-06",
    "sale_price": 375000
}

print("Adding most recent sale...")
try:
    result = supabase.table('property_sales_history').insert(sale_data).execute()
    print(f"SUCCESS: Added ${sale_data['sale_price']} sale on {sale_data['sale_date']}")
except Exception as e:
    print(f"ERROR: {e}")

# Verify
print("\nChecking sales history...")
try:
    result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).execute()
    if result.data:
        print(f"Found {len(result.data)} sales:")
        for sale in result.data:
            print(f"  ${sale.get('sale_price')} on {sale.get('sale_date')}")
    else:
        print("No sales found")
except Exception as e:
    print(f"Error: {e}")