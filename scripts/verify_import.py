"""
Verify Broward County sales import
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.vSW_L6wL_lW15KPqIJFT3bY-KhNABd3d7qs8m-6hQ7g')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get total count
result = supabase.table('property_sales_history').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()

print(f"Total BROWARD sales: {result.count:,}")

# Get sample record
sample = supabase.table('property_sales_history').select('*').eq('county', 'BROWARD').limit(1).execute()

if sample.data:
    rec = sample.data[0]
    price = rec.get('sale_price', 0) / 100
    print(f"\nSample record:")
    print(f"  Parcel: {rec.get('parcel_id')}")
    print(f"  Date: {rec.get('sale_date')}")
    print(f"  Price: ${price:,.2f}")
    print(f"  County: {rec.get('county')}")
    print(f"  OR Book/Page: {rec.get('or_book')}/{rec.get('or_page')}")
    print(f"\nTest in UI: http://localhost:5178/property/{rec.get('parcel_id')}")
