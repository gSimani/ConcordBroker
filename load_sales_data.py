"""
Load sales data from SDF file into fl_sdf_sales table
"""

import os
import csv
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def create_sales_table():
    """Create the sales table if it doesn't exist"""
    print("Note: Run this SQL in Supabase to create the sales table:")
    print("""
CREATE TABLE IF NOT EXISTS fl_sdf_sales (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    sale_date DATE,
    sale_price INTEGER,
    sale_year INTEGER,
    sale_month INTEGER,
    qual_code VARCHAR(10),
    vi_code VARCHAR(10),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    clerk_no VARCHAR(20),
    multi_parcel_sale BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sdf_sales_parcel ON fl_sdf_sales(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sdf_sales_date ON fl_sdf_sales(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sdf_sales_price ON fl_sdf_sales(sale_price);
    """)

def load_sales():
    print("LOADING SALES DATA FROM SDF FILE")
    print("=" * 60)
    
    sales_batch = []
    batch_size = 500
    total_loaded = 0
    
    with open('SDF16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Parse sale data
            try:
                sale_price = int(float(row.get('SALE_PRC', 0) or 0))
                sale_year = int(float(row.get('SALE_YR', 0) or 0))
                sale_month = int(float(row.get('SALE_MO', 0) or 0))
                
                # Skip invalid sales
                if sale_price <= 0 or sale_year < 1900:
                    continue
                
                # Create sale date
                sale_date = f"{sale_year}-{str(sale_month).zfill(2)}-01"
                
                sale_data = {
                    'parcel_id': parcel_id,
                    'sale_date': sale_date,
                    'sale_price': sale_price,
                    'sale_year': sale_year,
                    'sale_month': sale_month,
                    'qual_code': row.get('QUAL_CD', '').strip() or None,
                    'vi_code': row.get('VI_CD', '').strip() or None,
                    'or_book': row.get('OR_BOOK', '').strip() or None,
                    'or_page': row.get('OR_PAGE', '').strip() or None,
                    'clerk_no': row.get('CLERK_NO', '').strip() or None,
                    'multi_parcel_sale': row.get('MULTI_PAR_SAL', '') == 'Y'
                }
                
                # Remove None values
                sale_data = {k: v for k, v in sale_data.items() if v is not None}
                
                sales_batch.append(sale_data)
                
                # Upload batch when full
                if len(sales_batch) >= batch_size:
                    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales"
                    response = requests.post(url, json=sales_batch, headers=headers)
                    
                    if response.status_code in [200, 201, 204]:
                        total_loaded += len(sales_batch)
                        print(f"  Loaded {total_loaded} sales...")
                    else:
                        print(f"  Error: {response.status_code}")
                        if response.status_code == 404:
                            print("  Table fl_sdf_sales doesn't exist. Create it first!")
                            return
                        elif total_loaded == 0:
                            print(f"  {response.text[:200]}")
                    
                    sales_batch = []
                    time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                if i < 5:  # Show first few errors
                    print(f"  Error parsing row {i}: {e}")
                continue
        
        # Upload remaining batch
        if sales_batch:
            url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales"
            response = requests.post(url, json=sales_batch, headers=headers)
            
            if response.status_code in [200, 201, 204]:
                total_loaded += len(sales_batch)
    
    print(f"\nComplete! Loaded {total_loaded:,} sales records")
    
    # Check if our property has sales now
    print("\nChecking for sales of property 504231242730...")
    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales?parcel_id=eq.504231242730"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"  Found {len(data)} sales for this property!")
            for sale in data:
                print(f"    ${sale.get('sale_price', 0):,} on {sale.get('sale_date')}")
        else:
            print("  No sales found for this property (it may not have sold recently)")

if __name__ == "__main__":
    create_sales_table()
    print("\nPress Enter to load sales data, or Ctrl+C to cancel...")
    input()
    load_sales()