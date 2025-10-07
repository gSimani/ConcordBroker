"""
Find sample parcels with sales data
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Getting sample sales records from property_sales_history...\n")

result = supabase.table('property_sales_history').select('*').limit(5).execute()

if result.data:
    print(f"Found {len(result.data)} sample sales:\n")

    for i, sale in enumerate(result.data, 1):
        price_cents = sale.get('sale_price', 0)
        price_dollars = price_cents / 100 if price_cents else 0

        print(f"Sale {i}:")
        print(f"  Parcel ID: {sale.get('parcel_id')}")
        print(f"  County: {sale.get('county')}")
        print(f"  Date: {sale.get('sale_date')}")
        print(f"  Price: ${price_dollars:,.2f}")
        print(f"  OR Book/Page: {sale.get('or_book')}/{sale.get('or_page')}")
        print(f"  Quality: {sale.get('quality_code')}")
        print()

    # Use first parcel for testing
    test_parcel = result.data[0]['parcel_id']
    print(f"Test this parcel in UI: http://localhost:5178/property/{test_parcel}")

else:
    print("No sales found!")
