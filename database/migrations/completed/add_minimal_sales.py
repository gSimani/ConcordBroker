"""
Add minimal sales history with only basic fields
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

def add_minimal_sales():
    """Add sales with minimal fields"""
    
    parcel_id = "474131031040"
    
    # Minimal sales records
    sales = [
        {
            "parcel_id": parcel_id,
            "sale_date": "2013-11-06",
            "sale_price": 375000
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2010-09-15", 
            "sale_price": 100
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2009-07-27",
            "sale_price": 327000
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2004-11-16",
            "sale_price": 432000
        }
    ]
    
    print(f"Adding {len(sales)} minimal sales records...")
    
    for sale in sales:
        try:
            result = supabase.table('property_sales_history').insert(sale).execute()
            print(f"  ✓ Added: ${sale['sale_price']:,} on {sale['sale_date']}")
        except Exception as e:
            print(f"  ✗ Error adding sale {sale['sale_date']}: {e}")
    
    print("\nVerifying sales history...")
    try:
        result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).execute()
        if result.data:
            print(f"SUCCESS: Found {len(result.data)} sales records:")
            for sale in result.data:
                print(f"  ${sale.get('sale_price', 'N/A')} on {sale.get('sale_date', 'N/A')}")
        else:
            print("No sales records found")
    except Exception as e:
        print(f"Error checking sales: {e}")

if __name__ == "__main__":
    add_minimal_sales()