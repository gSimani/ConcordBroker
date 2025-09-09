import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(url, key)

# Property to check
parcel_id = "474132080510"
property_address = "10892 NW 72 PL"

print(f"Checking data for property: {property_address}")
print(f"Parcel ID: {parcel_id}")
print("=" * 60)

# Check florida_parcels table
print("\n1. Checking florida_parcels table...")
result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
if result.data and len(result.data) > 0:
    print(f"Found {len(result.data)} record(s)")
    for record in result.data:
        print("\nKey fields:")
        print(f"  - parcel_id: {record.get('parcel_id')}")
        print(f"  - owner_name: {record.get('owner_name')}")
        print(f"  - property_address: {record.get('property_address')}")
        print(f"  - total_living_area: {record.get('total_living_area')}")
        print(f"  - year_built: {record.get('year_built')}")
        print(f"  - land_sqft: {record.get('land_sqft')}")
        print(f"  - sale_price: {record.get('sale_price')}")
        print(f"  - sale_date: {record.get('sale_date')}")
        print(f"  - market_value: {record.get('market_value')}")
        print(f"  - assessed_value: {record.get('assessed_value')}")
        
        # Count how many fields are NULL
        null_count = sum(1 for v in record.values() if v is None)
        total_fields = len(record)
        print(f"\n  Fields with data: {total_fields - null_count}/{total_fields}")
else:
    print("No records found in florida_parcels")

# Check property_sales_history table
print("\n2. Checking property_sales_history table...")
result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).execute()
if result.data and len(result.data) > 0:
    print(f"Found {len(result.data)} sale record(s)")
    for sale in result.data:
        print(f"  - Date: {sale.get('sale_date')}, Price: ${sale.get('sale_price'):,.0f}")
else:
    print("No sales history found")

# Check sdf_sales table (alternative sales source)
print("\n3. Checking sdf_sales table...")
try:
    result = supabase.table('sdf_sales').select('*').eq('parcel_id', parcel_id).execute()
    if result.data and len(result.data) > 0:
        print(f"Found {len(result.data)} SDF sale record(s)")
        for sale in result.data:
            print(f"  - Date: {sale.get('sale_date')}, Price: ${sale.get('sale_price'):,.0f if sale.get('sale_price') else 0}")
    else:
        print("No SDF sales found")
except Exception as e:
    print(f"Error checking sdf_sales: {e}")

# Search by address if parcel_id doesn't work
print("\n4. Searching by address in florida_parcels...")
result = supabase.table('florida_parcels').select('parcel_id, property_address, owner_name, sale_price, total_living_area, year_built').ilike('property_address', f'%{property_address}%').execute()
if result.data and len(result.data) > 0:
    print(f"Found {len(result.data)} record(s) matching address")
    for record in result.data:
        print(f"  - Parcel: {record.get('parcel_id')}")
        print(f"    Address: {record.get('property_address')}")
        print(f"    Owner: {record.get('owner_name')}")
        print(f"    Sale Price: ${record.get('sale_price'):,.0f if record.get('sale_price') else 0}")
        print(f"    Living Area: {record.get('total_living_area')} sq ft")
        print(f"    Year Built: {record.get('year_built')}")
else:
    print("No records found by address search")

print("\n" + "=" * 60)
print("Data check complete")
