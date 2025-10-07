import os
from supabase import create_client

# Load environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

parcel_id = '402101327008'

print(f"\nChecking sales data for parcel: {parcel_id}\n")
print("=" * 80)

# Check 1: property_sales_history
print("\n[1] Checking property_sales_history table:")
try:
    result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).execute()
    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for sale in result.data:
            print(f"      - {sale.get('sale_date')}: ${sale.get('sale_price')} (Book {sale.get('book')}, Page {sale.get('page')})")
    else:
        print(f"   NO records found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 2: florida_sdf_sales
print("\n[2] Checking florida_sdf_sales table:")
try:
    result = supabase.table('florida_sdf_sales').select('*').eq('parcel_id', parcel_id).execute()
    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for sale in result.data:
            print(f"      - {sale.get('sale_date')}: ${sale.get('sale_price')}")
    else:
        print(f"   NO records found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 3: sdf_sales
print("\n[3] Checking sdf_sales table:")
try:
    result = supabase.table('sdf_sales').select('*').eq('parcel_id', parcel_id).execute()
    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for sale in result.data:
            print(f"      - {sale.get('sale_date')}: ${sale.get('sale_price')} (Book {sale.get('book')}, Page {sale.get('page')})")
    else:
        print(f"   NO records found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 4: florida_parcels (built-in sales data)
print("\n[4] Checking florida_parcels table (built-in sales):")
try:
    result = supabase.table('florida_parcels').select('parcel_id, sale_date, sale_price, sale_qualification, book, page').eq('parcel_id', parcel_id).not_('sale_date', 'is', None).execute()
    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for sale in result.data:
            print(f"      - {sale.get('sale_date')}: ${sale.get('sale_price')} (Book {sale.get('book')}, Page {sale.get('page')})")
    else:
        print(f"   NO records found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 5: comprehensive_sales_data view
print("\n[5] Checking comprehensive_sales_data view:")
try:
    result = supabase.table('comprehensive_sales_data').select('*').eq('parcel_id', parcel_id).execute()
    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for sale in result.data:
            print(f"      - {sale.get('sale_date')}: ${sale.get('sale_price')} (Book {sale.get('book')}, Page {sale.get('page')})")
    else:
        print(f"   NO records found")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 80)
print("\nCheck complete!\n")
