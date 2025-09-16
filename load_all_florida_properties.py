"""
Load ALL Broward County properties with correct schema mapping
"""

import os
import csv
import json
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

def process_batch(rows, batch_num):
    """Process a batch of rows and upload"""
    properties = []
    
    for row in rows:
        parcel_id = clean_value(row.get('PARCEL_ID'))
        if not parcel_id:
            continue
        
        # Map to EXACT column names from schema
        property_data = {
            # Required fields
            'parcel_id': parcel_id,
            'county': 'BROWARD',
            'year': 2025,
            
            # Owner info - these columns exist
            'owner_name': clean_value(row.get('OWN_NAME')),
            'owner_addr1': clean_value(row.get('OWN_ADDR1')),
            'owner_addr2': clean_value(row.get('OWN_ADDR2')),
            'owner_city': clean_value(row.get('OWN_CITY')),
            'owner_state': clean_value(row.get('OWN_STATE')),
            'owner_zip': clean_value(row.get('OWN_ZIPCD')),
            
            # Physical address - these columns exist
            'phy_addr1': clean_value(row.get('PHY_ADDR1')),
            'phy_addr2': clean_value(row.get('PHY_ADDR2')),
            'phy_city': clean_value(row.get('PHY_CITY')),
            'phy_state': 'FL',
            'phy_zipcd': clean_value(row.get('PHY_ZIPCD')),
            
            # Values - these columns exist
            'just_value': parse_number(row.get('JV')),
            'assessed_value': parse_number(row.get('AV_SD')) or parse_number(row.get('AV_NSD')),
            'taxable_value': parse_number(row.get('TV_SD')) or parse_number(row.get('TV_NSD')),
            'land_value': parse_number(row.get('LND_VAL')),
            
            # Property details - these columns exist
            'property_use': clean_value(row.get('DOR_UC')),
            'year_built': parse_year(row.get('ACT_YR_BLT')),
            'total_living_area': parse_number(row.get('TOT_LVG_AREA')),
            'land_sqft': parse_number(row.get('LND_SQFOOT')),
            
            # Legal - these columns exist
            'legal_desc': clean_value(row.get('S_LEGAL')),
            'subdivision': clean_value(row.get('SUBDIVISION')),
            
            # Sales - these columns exist
            'sale_price': parse_number(row.get('SALE_PRC1')),
            'sale_qualification': clean_value(row.get('QUAL_CD1')),
            
            # Data quality - these columns exist
            'is_redacted': False,
            'data_source': 'NAL_2025',
            'import_date': datetime.now().isoformat()
        }
        
        # Create sale_date if we have year and month
        sale_year = parse_year(row.get('SALE_YR1'))
        sale_month = parse_number(row.get('SALE_MO1'))
        if sale_year and sale_month:
            property_data['sale_date'] = f"{sale_year}-{sale_month:02d}-01"
        
        # Remove None values to avoid schema mismatch
        property_data = {k: v for k, v in property_data.items() if v is not None}
        
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
            print(f"  Batch {batch_num}: Uploaded {len(properties)} properties")
            return len(properties)
        else:
            print(f"  Batch {batch_num} failed: {response.status_code}")
            # Show first error for debugging
            if batch_num == 1:
                print(f"  Error: {response.text[:500]}")
            return 0
    except Exception as e:
        print(f"  Batch {batch_num} exception: {str(e)[:100]}")
        return 0

def main():
    print("LOADING ALL BROWARD COUNTY PROPERTIES")
    print("="*60)
    
    filename = 'NAL16P202501.csv'
    batch_size = 500
    
    print(f"Processing {filename} in batches of {batch_size}")
    print("This will take approximately 20-30 minutes")
    print()
    
    start_time = time.time()
    total_uploaded = 0
    batch_num = 0
    batch_rows = []
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            batch_rows.append(row)
            
            if len(batch_rows) >= batch_size:
                batch_num += 1
                uploaded = process_batch(batch_rows, batch_num)
                total_uploaded += uploaded
                
                # Progress update every 10 batches
                if batch_num % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = total_uploaded / elapsed if elapsed > 0 else 0
                    print(f"  Progress: {total_uploaded:,} properties uploaded ({rate:.0f}/sec)")
                
                batch_rows = []
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.05)
        
        # Process remaining rows
        if batch_rows:
            batch_num += 1
            uploaded = process_batch(batch_rows, batch_num)
            total_uploaded += uploaded
    
    # Summary
    elapsed = time.time() - start_time
    print()
    print("="*60)
    print(f"COMPLETE!")
    print(f"  Total uploaded: {total_uploaded:,} properties")
    print(f"  Time taken: {elapsed/60:.1f} minutes")
    print(f"  Average rate: {total_uploaded/elapsed:.0f} properties/second")
    
    # Verify final count
    print("\nVerifying database count...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=parcel_id&limit=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        total_count = response.headers.get('content-range', '').split('/')[-1]
        if total_count != '*':
            print(f"Database now contains: {total_count} properties")

if __name__ == "__main__":
    main()