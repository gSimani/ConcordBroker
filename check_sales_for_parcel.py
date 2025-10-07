import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_ANON_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

parcel_id = '402101327008'

print(f"\n=== Checking Sales Data for Parcel: {parcel_id} ===\n")

# Check property_sales_history
print("[1] Checking property_sales_history table:")
try:
    result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).execute()

    if result.data:
        print(f"   FOUND {len(result.data)} sales records")
        for i, sale in enumerate(result.data, 1):
            price_cents = sale.get('sale_price', 0)
            price_dollars = price_cents / 100 if price_cents else 0
            print(f"\n   Sale {i}:")
            print(f"      Date: {sale.get('sale_date')}")
            print(f"      Price (cents): {price_cents}")
            print(f"      Price (dollars): ${price_dollars:,.2f}")
            print(f"      OR Book: {sale.get('or_book')}")
            print(f"      OR Page: {sale.get('or_page')}")
            print(f"      Quality Code: {sale.get('quality_code')}")
            print(f"      Clerk No: {sale.get('clerk_no')}")
    else:
        print(f"   NO sales found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check florida_parcels
print("\n[2] Checking florida_parcels table:")
try:
    result = supabase.table('florida_parcels').select('parcel_id, sale_prc1, sale_yr1, sale_mo1, sale_prc2, sale_yr2, sale_mo2, sale_prc3, sale_yr3, sale_mo3').eq('parcel_id', parcel_id).execute()

    if result.data and len(result.data) > 0:
        parcel = result.data[0]
        print(f"   FOUND parcel record")
        for i in range(1, 4):
            price = parcel.get(f'sale_prc{i}')
            year = parcel.get(f'sale_yr{i}')
            month = parcel.get(f'sale_mo{i}')
            if price:
                print(f"\n   Sale {i}:")
                print(f"      Price: ${price:,.2f}")
                print(f"      Year: {year}")
                print(f"      Month: {month}")
    else:
        print(f"   NO parcel found")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
print("\nDone!\n")
