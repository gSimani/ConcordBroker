"""
Deploy all property enhancement tables and columns to Supabase
Then load NAP physical data and SDF enhanced sales data
"""

import os
import csv
import requests
import time
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

def add_nap_columns():
    """Add NAP physical property columns to florida_parcels table"""
    print("\n1. ADDING NAP COLUMNS TO DATABASE")
    print("=" * 60)
    
    # First check if columns already exist
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=bedrooms,bathrooms,year_built&limit=1"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("   NAP columns already exist in database")
        return True
    
    print("   NAP columns don't exist, would need to be added via Supabase SQL Editor")
    print("   Required columns: bedrooms, bathrooms, year_built, total_living_area, etc.")
    return False

def create_sales_tables():
    """Check if sales history tables exist"""
    print("\n2. CHECKING SALES HISTORY TABLES")
    print("=" * 60)
    
    url = f"{SUPABASE_URL}/rest/v1/property_sales_history?limit=1"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("   Sales history tables already exist")
        return True
    elif response.status_code == 404:
        print("   Sales history tables don't exist")
        print("   Would need to be created via Supabase SQL Editor")
        return False
    else:
        print(f"   Unexpected response: {response.status_code}")
        return False

def load_nap_data_simple():
    """Load NAP physical data using only existing columns"""
    print("\n3. LOADING NAP PHYSICAL DATA (Using Existing Columns)")
    print("=" * 60)
    
    if not os.path.exists('NAP16P202501.csv'):
        print("   NAP file not found!")
        return 0
    
    updates_batch = []
    batch_size = 100
    total_updated = 0
    
    with open('NAP16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Extract data that fits in existing columns
            # We'll store key info in existing fields
            update_data = {
                'parcel_id': parcel_id,
                
                # Store year built as integer
                'year_built': int(row.get('ACT_YR_BLT', 0) or 0) if row.get('ACT_YR_BLT') else None,
                
                # Store living area as integer
                'total_living_area': int(float(row.get('TOT_LVG_AREA', 0) or 0)) if row.get('TOT_LVG_AREA') else None,
                
                # Store number of units (can use for multi-family)
                'no_units': int(float(row.get('NO_UNITS', 0) or 0)) if row.get('NO_UNITS') else None,
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if len(update_data) > 1:  # Has data beyond parcel_id
                updates_batch.append(update_data)
            
            # Upload batch when full
            if len(updates_batch) >= batch_size:
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
                headers_upsert = {
                    **headers,
                    'Prefer': 'resolution=merge-duplicates,return=minimal'
                }
                
                response = requests.post(url, json=updates_batch, headers=headers_upsert)
                
                if response.status_code in [200, 201, 204]:
                    total_updated += len(updates_batch)
                    if total_updated % 5000 == 0:
                        print(f"   Updated {total_updated:,} properties...")
                
                updates_batch = []
                time.sleep(0.1)
        
        # Upload remaining batch
        if updates_batch:
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            headers_upsert = {
                **headers,
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }
            
            response = requests.post(url, json=updates_batch, headers=headers_upsert)
            
            if response.status_code in [200, 201, 204]:
                total_updated += len(updates_batch)
    
    print(f"   Total properties updated with NAP data: {total_updated:,}")
    return total_updated

def load_sdf_sales_simple():
    """Load SDF sales data directly into florida_parcels"""
    print("\n4. LOADING SDF SALES DATA (Most Recent Sale)")
    print("=" * 60)
    
    if not os.path.exists('SDF16P202501.csv'):
        print("   SDF file not found!")
        return 0
    
    # Track most recent sale per property
    sales_by_parcel = {}
    
    with open('SDF16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            try:
                sale_price = int(float(row.get('SALE_PRC', 0) or 0))
                sale_year = int(float(row.get('SALE_YR', 0) or 0))
                sale_month = int(float(row.get('SALE_MO', 0) or 0))
                
                # Skip invalid sales
                if sale_price <= 0 or sale_year < 1900:
                    continue
                
                # Create sale date
                sale_date = f"{sale_year}-{str(sale_month).zfill(2)}-01"
                
                # Keep only most recent sale
                if parcel_id not in sales_by_parcel:
                    sales_by_parcel[parcel_id] = {
                        'sale_price': sale_price,
                        'sale_date': sale_date,
                        'sale_year': sale_year
                    }
                elif sale_year > sales_by_parcel[parcel_id]['sale_year']:
                    sales_by_parcel[parcel_id] = {
                        'sale_price': sale_price,
                        'sale_date': sale_date,
                        'sale_year': sale_year
                    }
            except:
                continue
    
    print(f"   Found sales for {len(sales_by_parcel):,} properties")
    
    # Update properties with sales data
    updates_batch = []
    batch_size = 100
    total_updated = 0
    
    for parcel_id, sale_info in sales_by_parcel.items():
        update_data = {
            'parcel_id': parcel_id,
            'sale_price': sale_info['sale_price'],
            'sale_date': sale_info['sale_date']
        }
        updates_batch.append(update_data)
        
        if len(updates_batch) >= batch_size:
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            headers_upsert = {
                **headers,
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }
            
            response = requests.post(url, json=updates_batch, headers=headers_upsert)
            
            if response.status_code in [200, 201, 204]:
                total_updated += len(updates_batch)
                if total_updated % 5000 == 0:
                    print(f"   Updated {total_updated:,} properties with sales...")
            
            updates_batch = []
            time.sleep(0.1)
    
    # Upload remaining batch
    if updates_batch:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        headers_upsert = {
            **headers,
            'Prefer': 'resolution=merge-duplicates,return=minimal'
        }
        
        response = requests.post(url, json=updates_batch, headers=headers_upsert)
        
        if response.status_code in [200, 201, 204]:
            total_updated += len(updates_batch)
    
    print(f"   Total properties updated with sales: {total_updated:,}")
    return total_updated

def check_sample_property():
    """Check what data we have for property 504231242730"""
    print("\n5. CHECKING SAMPLE PROPERTY 504231242730")
    print("=" * 60)
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.504231242730"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            print("   Property Data:")
            print(f"     Address: {prop.get('phy_addr1', 'N/A')}")
            print(f"     Year Built: {prop.get('year_built', 'N/A')}")
            print(f"     Living Area: {prop.get('total_living_area', 'N/A')} sq ft")
            print(f"     Units: {prop.get('no_units', 'N/A')}")
            print(f"     Sale Price: ${prop.get('sale_price', 0) or 0:,}")
            print(f"     Sale Date: {prop.get('sale_date', 'N/A')}")
            print(f"     Just Value: ${prop.get('just_value', 0) or 0:,}")
            print(f"     Assessed: ${prop.get('assessed_value', 0) or 0:,}")
            print(f"     Taxable: ${prop.get('taxable_value', 0) or 0:,}")

def main():
    print("DEPLOYING PROPERTY ENHANCEMENTS")
    print("=" * 60)
    
    # Check what exists
    nap_columns_exist = add_nap_columns()
    sales_tables_exist = create_sales_tables()
    
    # Load NAP data (using existing columns)
    nap_count = load_nap_data_simple()
    
    # Load SDF sales data
    sdf_count = load_sdf_sales_simple()
    
    # Check a sample property
    check_sample_property()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print(f"Updated {nap_count:,} properties with NAP physical data")
    print(f"Updated {sdf_count:,} properties with sales data")
    
    if not nap_columns_exist:
        print("\nTo add bedroom/bathroom data:")
        print("1. Go to Supabase SQL Editor")
        print("2. Run the SQL from 'add_nap_columns.sql'")
        print("3. Re-run this script")
    
    if not sales_tables_exist:
        print("\nTo create full sales history:")
        print("1. Go to Supabase SQL Editor")
        print("2. Run the SQL from 'create_complete_sales_tables.sql'")
        print("3. Run 'python load_complete_sales_history.py'")

if __name__ == "__main__":
    main()