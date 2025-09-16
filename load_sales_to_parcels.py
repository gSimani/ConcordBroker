"""
Load sales data directly into florida_parcels table
This updates the existing sale_price and sale_date fields
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

def load_sales_to_parcels():
    """Load most recent sale for each property into florida_parcels table"""
    print("LOADING SALES DATA INTO FLORIDA_PARCELS")
    print("=" * 60)
    print("This will update the sale_price and sale_date fields")
    print("with the most recent sale for each property\n")
    
    # Track sales by parcel to get most recent
    sales_by_parcel = {}
    
    # First, load all sales from SDF file
    print("1. Reading SDF sales file...")
    if not os.path.exists('SDF16P202501.csv'):
        print("   SDF file not found!")
        return
    
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
                
                # Store sale if it's newer than existing
                if parcel_id not in sales_by_parcel:
                    sales_by_parcel[parcel_id] = {
                        'sale_price': sale_price,
                        'sale_date': sale_date,
                        'sale_year': sale_year
                    }
                else:
                    # Keep the most recent sale
                    if sale_year > sales_by_parcel[parcel_id]['sale_year']:
                        sales_by_parcel[parcel_id] = {
                            'sale_price': sale_price,
                            'sale_date': sale_date,
                            'sale_year': sale_year
                        }
                    elif sale_year == sales_by_parcel[parcel_id]['sale_year'] and sale_price > sales_by_parcel[parcel_id]['sale_price']:
                        # Same year but higher price (probably more accurate)
                        sales_by_parcel[parcel_id] = {
                            'sale_price': sale_price,
                            'sale_date': sale_date,
                            'sale_year': sale_year
                        }
            except:
                continue
    
    print(f"   Found sales for {len(sales_by_parcel):,} properties")
    
    # Also check NAL file for additional sales
    print("\n2. Reading NAL file for additional sales...")
    if os.path.exists('NAL16P202501.csv'):
        with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                parcel_id = row.get('PARCEL_ID', '').strip()
                
                if not parcel_id:
                    continue
                
                # Check SALE_PRC1
                if row.get('SALE_PRC1') and row['SALE_PRC1'].strip():
                    try:
                        price = int(float(row['SALE_PRC1']))
                        year = int(float(row.get('SALE_YR1', 0) or 0))
                        
                        if price > 0 and year > 1900:
                            month = row.get('SALE_MO1', '01').strip() or '01'
                            sale_date = f"{year}-{month.zfill(2)}-01"
                            
                            # Update if newer or doesn't exist
                            if parcel_id not in sales_by_parcel or year > sales_by_parcel[parcel_id]['sale_year']:
                                sales_by_parcel[parcel_id] = {
                                    'sale_price': price,
                                    'sale_date': sale_date,
                                    'sale_year': year
                                }
                    except:
                        pass
                
                # Check SALE_PRC2 (usually older)
                if row.get('SALE_PRC2') and row['SALE_PRC2'].strip():
                    try:
                        price = int(float(row['SALE_PRC2']))
                        year = int(float(row.get('SALE_YR2', 0) or 0))
                        
                        if price > 0 and year > 1900:
                            month = row.get('SALE_MO2', '01').strip() or '01'
                            sale_date = f"{year}-{month.zfill(2)}-01"
                            
                            # Only update if we don't have any sale yet
                            if parcel_id not in sales_by_parcel:
                                sales_by_parcel[parcel_id] = {
                                    'sale_price': price,
                                    'sale_date': sale_date,
                                    'sale_year': year
                                }
                    except:
                        pass
    
    print(f"   Total properties with sales: {len(sales_by_parcel):,}")
    
    # Now update the florida_parcels table
    print("\n3. Updating florida_parcels table with sales data...")
    
    update_batch = []
    batch_size = 100
    total_updated = 0
    
    for parcel_id, sale_info in sales_by_parcel.items():
        update_data = {
            'parcel_id': parcel_id,
            'sale_price': sale_info['sale_price'],
            'sale_date': sale_info['sale_date']
        }
        update_batch.append(update_data)
        
        if len(update_batch) >= batch_size:
            # Update using upsert
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            headers_upsert = {
                **headers,
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }
            
            response = requests.post(url, json=update_batch, headers=headers_upsert)
            
            if response.status_code in [200, 201, 204]:
                total_updated += len(update_batch)
                if total_updated % 5000 == 0:
                    print(f"   Updated {total_updated:,} properties...")
            else:
                print(f"   Error updating batch: {response.status_code}")
            
            update_batch = []
            time.sleep(0.1)
    
    # Update remaining batch
    if update_batch:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        headers_upsert = {
            **headers,
            'Prefer': 'resolution=merge-duplicates,return=minimal'
        }
        
        response = requests.post(url, json=update_batch, headers=headers_upsert)
        
        if response.status_code in [200, 201, 204]:
            total_updated += len(update_batch)
    
    print(f"\n   Total properties updated with sales: {total_updated:,}")
    
    # Check a specific property
    print("\n4. Checking property 504231242730...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.504231242730"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            if prop.get('sale_price'):
                print(f"   Sale Price: ${prop['sale_price']:,}")
                print(f"   Sale Date: {prop.get('sale_date', 'N/A')}")
            else:
                print("   No sale data for this property")
    
    print("\n" + "=" * 60)
    print("SALES LOADING COMPLETE!")
    print("Properties now have their most recent sale information")
    print("Check http://localhost:5174/property/504231242730 to see sales data")

if __name__ == "__main__":
    load_sales_to_parcels()