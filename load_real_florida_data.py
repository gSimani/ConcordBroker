"""
Load REAL Florida Data into Supabase - Production Ready
"""

import os
import csv
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("ERROR: Supabase credentials not found")
    exit(1)

print(f"Connecting to Supabase: {SUPABASE_URL}")

# Headers for API requests
headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def load_nap_data(filename='NAP16P202501.csv', max_records=1000):
    """Load NAP (Name/Address/Parcel) data into florida_parcels table"""
    print(f"\nLoading NAP data from {filename}...")
    
    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found!")
        return False
    
    properties = []
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if i >= max_records:
                    break
                
                # Map NAP fields to florida_parcels table
                property_data = {
                    'parcel_id': row.get('PARCEL_ID', '').strip(),
                    'county': 'BROWARD',
                    'year': 2025,
                    'phy_addr1': row.get('PHY_ADDR1', '').strip(),
                    'phy_city': row.get('PHY_CITY', '').strip(),
                    'phy_state': 'FL',
                    'phy_zipcd': row.get('PHY_ZIPCD', '').strip(),
                    'owner_name': row.get('OWNER_NAME', '').strip(),
                    'owner_addr1': row.get('OWN_ADDR1', '').strip(),
                    'owner_city': row.get('OWN_CITY', '').strip(),
                    'owner_state': row.get('OWN_STATE', '').strip(),
                    'owner_zip': row.get('OWN_ZIPCD', '').strip(),
                    'property_use': row.get('DOR_UC', '').strip(),
                    'just_value': int(row.get('JV', 0) or 0),
                    'assessed_value': int(row.get('AV', 0) or 0),
                    'taxable_value': int(row.get('TV', 0) or 0),
                    'is_redacted': False,
                    'data_source': 'NAP16P202501'
                }
                
                # Only add if has valid parcel_id and address
                if property_data['parcel_id'] and property_data['phy_addr1']:
                    properties.append(property_data)
                
                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1} records...")
        
        print(f"Prepared {len(properties)} valid properties for insertion")
        
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return False
    
    # Insert in batches
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(properties), batch_size):
        batch = properties[i:i + batch_size]
        
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        
        try:
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201]:
                total_inserted += len(batch)
                print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} properties")
            elif "42501" in response.text:
                print("RLS Policy blocking insertion - need to disable RLS first")
                return False
            else:
                print(f"  Failed batch {i//batch_size + 1}: {response.status_code}")
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Batch error: {e}")
    
    print(f"\nTotal properties inserted: {total_inserted}")
    return total_inserted > 0

def load_sdf_data(filename='SDF16P202501.csv', max_records=1000):
    """Load SDF (Sales Data File) into fl_sdf_sales table"""
    print(f"\nLoading SDF data from {filename}...")
    
    if not os.path.exists(filename):
        print(f"ERROR: {filename} not found!")
        return False
    
    sales = []
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if i >= max_records:
                    break
                
                # Map SDF fields to fl_sdf_sales table
                sale_data = {
                    'parcel_id': row.get('PARCEL_ID', '').strip(),
                    'county': 'BROWARD',
                    'year': 2025,
                    'sale_date': row.get('SALE_DATE', '').strip() or None,
                    'sale_price': int(row.get('SALE_PRICE', 0) or 0),
                    'sale_type': row.get('SALE_TYPE', '').strip(),
                    'book_page': row.get('BOOK_PAGE', '').strip(),
                    'property_address_full': row.get('PHY_ADDR1', '').strip(),
                    'data_source': 'SDF16P202501'
                }
                
                # Only add if has valid parcel_id and sale info
                if sale_data['parcel_id'] and sale_data['sale_price'] > 0:
                    sales.append(sale_data)
                
                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1} records...")
        
        print(f"Prepared {len(sales)} valid sales for insertion")
        
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return False
    
    # Insert sales in batches
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(sales), batch_size):
        batch = sales[i:i + batch_size]
        
        url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales"
        
        try:
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201]:
                total_inserted += len(batch)
                print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} sales")
            else:
                print(f"  Failed batch {i//batch_size + 1}: {response.status_code}")
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Batch error: {e}")
    
    print(f"\nTotal sales inserted: {total_inserted}")
    return total_inserted > 0

def disable_rls():
    """Disable RLS via SQL (needs to be run in Supabase dashboard)"""
    print("\n" + "="*60)
    print("IMPORTANT: RLS IS BLOCKING DATA INSERTION")
    print("="*60)
    print("\nYou need to run this SQL in Supabase SQL Editor first:")
    print("\n--- COPY THIS SQL ---")
    print("ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;")
    print("ALTER TABLE fl_sdf_sales DISABLE ROW LEVEL SECURITY;")
    print("--- END SQL ---")
    print("\nThen run this script again.")
    print("="*60)

def verify_data():
    """Verify data was loaded"""
    print("\nVerifying loaded data...")
    
    # Check florida_parcels
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        count = data[0]['count'] if data else 0
        print(f"  florida_parcels: {count} records")
    
    # Check fl_sdf_sales
    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales?select=count"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        count = data[0]['count'] if data else 0
        print(f"  fl_sdf_sales: {count} records")

def main():
    print("LOADING REAL FLORIDA DATA FOR PRODUCTION")
    print("="*60)
    
    # Try to load NAP data
    nap_success = load_nap_data(max_records=500)  # Start with 500 records
    
    if not nap_success:
        disable_rls()
        return
    
    # Load SDF sales data
    sdf_success = load_sdf_data(max_records=500)
    
    # Verify results
    verify_data()
    
    print("\n" + "="*60)
    if nap_success:
        print("SUCCESS! Real Florida data loaded!")
        print("\nYour website should now show real properties at:")
        print("  http://localhost:5174/properties")
        print("\nTry searching for real addresses from Broward County!")
    else:
        print("Data loading incomplete - check errors above")
    print("="*60)

if __name__ == "__main__":
    main()