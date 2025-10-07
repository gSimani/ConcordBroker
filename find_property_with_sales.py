import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("\n=== Finding properties WITH sales data ===\n")

# Check property_sales_history
print("[1] Checking property_sales_history:")
try:
    result = supabase.table('property_sales_history').select('parcel_id, sale_date, sale_price, or_book, or_page').limit(5).execute()

    if result.data:
        print(f"   FOUND {len(result.data)} sample sales records:\n")
        for sale in result.data:
            price_cents = sale.get('sale_price', 0)
            price_dollars = price_cents / 100 if price_cents else 0
            print(f"      Parcel: {sale.get('parcel_id')}")
            print(f"      Date: {sale.get('sale_date')}")
            print(f"      Price: ${price_dollars:,.2f}")
            print(f"      Book: {sale.get('or_book')}, Page: {sale.get('or_page')}")
            print()
    else:
        print("   NO sales found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check florida_parcels
print("\n[2] Checking florida_parcels with sale data:")
try:
    result = supabase.table('florida_parcels').select('parcel_id, sale_date, sale_price, sale_qualification').neq('sale_price', None).limit(5).execute()

    if result.data:
        print(f"   FOUND {len(result.data)} parcels with sales:\n")
        for parcel in result.data:
            print(f"      Parcel: {parcel.get('parcel_id')}")
            print(f"      Date: {parcel.get('sale_date')}")
            print(f"      Price: ${parcel.get('sale_price'):,.2f}" if parcel.get('sale_price') else "      Price: None")
            print(f"      Qualification: {parcel.get('sale_qualification')}")
            print()
    else:
        print("   NO parcels with sales found")
except Exception as e:
    print(f"   ERROR: {e}")

print("=" * 60 + "\n")
