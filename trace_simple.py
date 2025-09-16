"""
Simple trace script to find exact database values vs official values
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

print("TRACING DATA FOR 474131031040")
print("=" * 60)

# Official values from BCPA
official = {
    "owner_name": "IH3 PROPERTY FLORIDA LP",
    "total_living_area": 3012,  # NOT 3285
    "just_value": 628040,
    "assessed_value": 601370,
    "land_value": 85580,
    "building_value": 542460,
    "sale_price": 375000,  # NOT 425000
    "year_built": 2003,
    "bedrooms": 4,
    "bathrooms": 3
}

print("OFFICIAL VALUES:")
for k, v in official.items():
    print(f"  {k}: {v}")

print("\nCHECKING DATABASE...")

try:
    result = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
    
    if result.data and len(result.data) > 0:
        db_record = result.data[0]
        print("\nDATABASE VALUES:")
        
        for field, expected in official.items():
            actual = db_record.get(field)
            status = "OK" if actual == expected else "WRONG"
            print(f"  {field}: {actual} (expected: {expected}) [{status}]")
            
    else:
        print("Property not found!")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("SALES HISTORY CHECK...")

try:
    tables = ['property_sales_history', 'fl_sdf_sales', 'sdf_sales']
    
    for table in tables:
        try:
            sales = supabase.table(table).select('*').eq('parcel_id', '474131031040').execute()
            if sales.data:
                print(f"\n{table}: {len(sales.data)} records")
                for sale in sales.data[:3]:
                    price = sale.get('sale_price', 'N/A')
                    date = sale.get('sale_date', 'N/A')
                    print(f"  ${price} on {date}")
            else:
                print(f"{table}: No data")
        except:
            print(f"{table}: Table doesn't exist")
            
except Exception as e:
    print(f"Sales error: {e}")