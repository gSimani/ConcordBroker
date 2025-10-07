"""
Check actual schema of property_sales_history table
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Checking property_sales_history table schema...\n")

# Try to get one record to see all columns
try:
    result = supabase.table('property_sales_history').select('*').limit(1).execute()

    if result.data and len(result.data) > 0:
        print("Table has data. Columns:")
        for col in sorted(result.data[0].keys()):
            print(f"  - {col}")
    else:
        print("Table is empty. Trying to insert a test record to see required fields...")

        # Try inserting a minimal record to see what's required
        test_record = {
            'parcel_id': 'TEST123',
            'county': 'TEST',
            'sale_date': '2024-01-01',
            'sale_price': 100000,
            'data_source': 'test'
        }

        try:
            result = supabase.table('property_sales_history').insert(test_record).execute()
            print("\nTest insert succeeded! Required fields are minimal.")
            print("Inserted record:", result.data)

            # Delete test record
            supabase.table('property_sales_history').delete().eq('parcel_id', 'TEST123').execute()
            print("Test record deleted")

        except Exception as e:
            print(f"\nTest insert failed: {e}")
            print("\nThis tells us what fields are required or have constraints")

except Exception as e:
    print(f"Error: {e}")
