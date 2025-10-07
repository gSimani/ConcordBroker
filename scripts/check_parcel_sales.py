"""
Check if specific parcel has sales data
"""
import os
from supabase import create_client

SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

parcel = '474128000000'
result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel).execute()

print(f"\nChecking parcel {parcel}:")
print(f"Found {len(result.data)} sales records\n")

if result.data:
    for i, sale in enumerate(result.data[:5], 1):
        price = sale.get('sale_price', 0) / 100
        print(f"{i}. {sale.get('sale_date')} - ${price:,.2f} - {sale.get('quality_code')}")
        print(f"   OR Book/Page: {sale.get('or_book')}/{sale.get('or_page')}")
        print(f"   County: {sale.get('county')}")
        print()
else:
    print("NO SALES DATA - this is the problem!")
    print("\nTrying to count total Broward sales...")
    count_result = supabase.table('property_sales_history').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()
    print(f"Total BROWARD sales in DB: {count_result.count}")
