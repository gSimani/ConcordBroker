"""
Create sales history tables directly via Supabase API
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

print("CHECKING SALES HISTORY TABLES")
print("=" * 60)

# Check if the main table exists
url = f"{SUPABASE_URL}/rest/v1/property_sales_history?limit=1"
response = requests.get(url, headers=headers)

if response.status_code == 404:
    print("Sales history tables don't exist yet.")
    print("\nTo create them:")
    print("1. Go to your Supabase dashboard")
    print("2. Click on 'SQL Editor' in the left sidebar")
    print("3. Copy and paste the contents of 'create_complete_sales_tables.sql'")
    print("4. Click 'Run' button")
    print("\nThe SQL file creates:")
    print("  - property_sales_history table (for all sales)")
    print("  - property_ownership_history table (for tracking owners)")
    print("  - buyer_activity table (for tracking buyers)")
    print("  - address_parcel_match table (for address matching)")
    print("  - Two views for easy querying")
    
    print("\nAfter creating tables, run 'python load_complete_sales_history.py'")
elif response.status_code == 200:
    print("Sales history tables already exist!")
    
    # Check how many records we have
    url = f"{SUPABASE_URL}/rest/v1/property_sales_history?select=count"
    headers_count = {**headers, 'Prefer': 'count=exact,head=true'}
    response = requests.get(url, headers=headers_count)
    
    if 'content-range' in response.headers:
        count = response.headers['content-range'].split('/')[1]
        print(f"Current sales records: {count}")
        
        if count == "0":
            print("\nNo sales data loaded yet.")
            print("Run 'python load_complete_sales_history.py' to load sales data")
        else:
            print("\nSales data already loaded!")
            
            # Get a sample
            url = f"{SUPABASE_URL}/rest/v1/property_sales_history?limit=5&order=sale_date.desc"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                sales = response.json()
                print("\nRecent sales:")
                for sale in sales:
                    print(f"  {sale.get('parcel_id')}: ${sale.get('sale_price', 0):,} on {sale.get('sale_date')}")
else:
    print(f"Unexpected response: {response.status_code}")
    print(response.text[:500])