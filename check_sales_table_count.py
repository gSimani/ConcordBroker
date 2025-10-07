import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("\n=== Checking Table Counts ===\n")

# Count property_sales_history
print("[1] property_sales_history:")
try:
    result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
    print(f"   Total records: {result.count}")
except Exception as e:
    print(f"   ERROR: {e}")

# Count florida_parcels total
print("\n[2] florida_parcels total:")
try:
    result = supabase.table('florida_parcels').select('*', count='exact').limit(0).execute()
    print(f"   Total records: {result.count:,}")
except Exception as e:
    print(f"   ERROR: {e}")

# Count florida_parcels with sale_price not null
print("\n[3] florida_parcels with sale_price:")
try:
    result = supabase.table('florida_parcels').select('*', count='exact').not_.is_('sale_price', 'null').limit(0).execute()
    print(f"   Records with sale_price: {result.count:,}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60 + "\n")
