"""
Efficiently load all Broward County properties from NAL file
Shows progress and handles errors better
"""

import os
import csv
import json
import requests
import time
import sys
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

def clean_value(value):
    """Clean and convert values for database"""
    if not value or value == '':
        return None
    value = value.strip()
    if value.upper() in ['NULL', 'NONE', 'N/A', '']:
        return None
    return value

def parse_number(value):
    """Parse number from string"""
    if not value or value == '':
        return None
    try:
        cleaned = value.replace(',', '').replace('$', '').strip()
        if '.' in cleaned:
            return float(cleaned)
        return int(cleaned)
    except:
        return None

def parse_year(value):
    """Parse year from string"""
    if not value or value == '':
        return None
    try:
        year = int(value)
        if 1800 <= year <= 2030:
            return year
    except:
        pass
    return None

def process_and_upload_batch(batch_rows, batch_num, total_batches):
    """Process a batch of rows and upload to Supabase"""
    properties = []
    
    for row in batch_rows:
        parcel_id = clean_value(row.get('PARCEL_ID'))
        if not parcel_id:
            continue
        
        property_data = {
            'parcel_id': parcel_id,
            'county': 'BROWARD',
            'year': 2025,
            
            # Essential fields only for speed
            'owner_name': clean_value(row.get('OWN_NAME')),
            'phy_addr1': clean_value(row.get('PHY_ADDR1')),
            'phy_city': clean_value(row.get('PHY_CITY')),
            'phy_zipcd': clean_value(row.get('PHY_ZIPCD')),
            
            'property_use': clean_value(row.get('DOR_UC')),
            'taxable_value': parse_number(row.get('TV_SD')) or parse_number(row.get('TV_NSD')),
            'just_value': parse_number(row.get('JV')),
            'land_value': parse_number(row.get('LND_VAL')),
            
            'year_built': parse_year(row.get('ACT_YR_BLT')),
            'total_living_area': parse_number(row.get('TOT_LVG_AREA')),
            'land_sqft': parse_number(row.get('LND_SQFOOT')),
            
            'sale_price': parse_number(row.get('SALE_PRC1')),
            'sale_year': parse_year(row.get('SALE_YR1')),
            
            'is_redacted': False,
            'data_source': 'NAL_2025',
            'import_date': datetime.now().isoformat()
        }
        
        properties.append(property_data)
    
    if not properties:
        return 0
    
    # Upload batch
    try:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        response = requests.post(
            url,
            json=properties,
            headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"  Batch {batch_num}/{total_batches} uploaded ({len(properties)} properties)")
            return len(properties)
        else:
            print(f"  Batch {batch_num} failed: {response.status_code}")
            return 0
    except Exception as e:
        print(f"  Batch {batch_num} error: {str(e)[:100]}")
        return 0

def main():
    print("EFFICIENT PROPERTY LOADER FOR BROWARD COUNTY")
    print("="*60)
    
    filename = 'NAL16P202501.csv'
    batch_size = 1000  # Process in larger chunks
    
    # Count total rows first
    print("Counting total properties...")
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        total_rows = sum(1 for line in f) - 1  # Subtract header
    
    total_batches = (total_rows // batch_size) + 1
    print(f"Total properties to load: {total_rows:,}")
    print(f"Processing in {total_batches} batches of {batch_size}")
    print()
    
    # Process file in batches
    start_time = time.time()
    total_uploaded = 0
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        batch_rows = []
        batch_num = 0
        
        for i, row in enumerate(reader):
            batch_rows.append(row)
            
            if len(batch_rows) >= batch_size:
                batch_num += 1
                uploaded = process_and_upload_batch(batch_rows, batch_num, total_batches)
                total_uploaded += uploaded
                
                # Show progress
                progress = (batch_num / total_batches) * 100
                elapsed = time.time() - start_time
                rate = total_uploaded / elapsed if elapsed > 0 else 0
                eta = (total_rows - total_uploaded) / rate if rate > 0 else 0
                
                print(f"  Progress: {progress:.1f}% | Uploaded: {total_uploaded:,} | Rate: {rate:.0f}/sec | ETA: {eta/60:.1f} min")
                
                batch_rows = []
                
                # Rate limiting
                time.sleep(0.1)
        
        # Process remaining rows
        if batch_rows:
            batch_num += 1
            uploaded = process_and_upload_batch(batch_rows, batch_num, total_batches)
            total_uploaded += uploaded
    
    # Final summary
    elapsed = time.time() - start_time
    print()
    print("="*60)
    print(f"COMPLETE!")
    print(f"  Total uploaded: {total_uploaded:,} properties")
    print(f"  Time taken: {elapsed/60:.1f} minutes")
    print(f"  Average rate: {total_uploaded/elapsed:.0f} properties/second")
    
    # Verify count
    print("\nVerifying database count...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=parcel_id&limit=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        total_count = response.headers.get('content-range', '').split('/')[-1]
        if total_count != '*':
            print(f"Database now contains: {total_count} properties")

if __name__ == "__main__":
    main()