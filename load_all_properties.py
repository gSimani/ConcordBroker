"""
Load ALL Broward County properties from NAL file (753,243 records)
This is the complete property dataset with all fields
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
    
    # Remove extra spaces
    value = value.strip()
    
    # Handle common null values
    if value.upper() in ['NULL', 'NONE', 'N/A', '']:
        return None
    
    return value

def parse_number(value):
    """Parse number from string"""
    if not value or value == '':
        return None
    try:
        # Remove commas and dollar signs
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
        # Validate reasonable year range
        if 1800 <= year <= 2030:
            return year
    except:
        pass
    return None

def load_nal_file():
    """Load complete NAL file which has all properties"""
    print("LOADING ALL BROWARD COUNTY PROPERTIES")
    print("="*60)
    
    filename = 'NAL16P202501.csv'
    print(f"Reading {filename}...")
    
    properties = []
    duplicates = set()
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = clean_value(row.get('PARCEL_ID'))
            
            if not parcel_id:
                continue
            
            # Skip duplicates
            if parcel_id in duplicates:
                continue
            duplicates.add(parcel_id)
            
            # Map NAL fields to database fields
            property_data = {
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'year': 2025,
                
                # Owner information
                'owner_name': clean_value(row.get('OWN_NAME')),
                'owner_addr1': clean_value(row.get('OWN_ADDR1')),
                'owner_addr2': clean_value(row.get('OWN_ADDR2')),
                'owner_city': clean_value(row.get('OWN_CITY')),
                'owner_state': clean_value(row.get('OWN_STATE')),
                'owner_zip': clean_value(row.get('OWN_ZIPCD')),
                
                # Physical address
                'phy_addr1': clean_value(row.get('PHY_ADDR1')),
                'phy_addr2': clean_value(row.get('PHY_ADDR2')),
                'phy_city': clean_value(row.get('PHY_CITY')),
                'phy_zipcd': clean_value(row.get('PHY_ZIPCD')),
                
                # Property use
                'property_use': clean_value(row.get('DOR_UC')),  # Department of Revenue Use Code
                'pa_uc': clean_value(row.get('PA_UC')),  # Property Appraiser Use Code
                
                # Values
                'just_value': parse_number(row.get('JV')),
                'assessed_value': parse_number(row.get('AV_SD')) or parse_number(row.get('AV_NSD')),
                'taxable_value': parse_number(row.get('TV_SD')) or parse_number(row.get('TV_NSD')),
                'land_value': parse_number(row.get('LND_VAL')),
                
                # Property details
                'year_built': parse_year(row.get('ACT_YR_BLT')),
                'eff_year_built': parse_year(row.get('EFF_YR_BLT')),
                'total_living_area': parse_number(row.get('TOT_LVG_AREA')),
                'land_sqft': parse_number(row.get('LND_SQFOOT')),
                'no_buildings': parse_number(row.get('NO_BULDNG')),
                'no_res_units': parse_number(row.get('NO_RES_UNTS')),
                
                # Legal description
                'legal_desc': clean_value(row.get('S_LEGAL')),
                'subdivision': clean_value(row.get('SUBDIVISION')),
                'census_block': clean_value(row.get('CENSUS_BK')),
                'market_area': clean_value(row.get('MKT_AR')),
                'neighborhood': clean_value(row.get('NBRHD_CD')),
                
                # Sales information
                'sale_price': parse_number(row.get('SALE_PRC1')),
                'sale_year': parse_year(row.get('SALE_YR1')),
                'sale_month': parse_number(row.get('SALE_MO1')),
                'sale_qualification': clean_value(row.get('QUAL_CD1')),
                
                # Construction details
                'construction_type': clean_value(row.get('CONST_CLASS')),
                'improvement_quality': clean_value(row.get('IMP_QUAL')),
                
                # Additional fields
                'group_no': clean_value(row.get('GRP_NO')),
                'district_no': clean_value(row.get('DISTR_CD')),
                'tax_auth_code': clean_value(row.get('TAX_AUTH_CD')),
                
                # Data quality
                'is_redacted': False,
                'data_source': 'NAL_2025',
                'import_date': datetime.now().isoformat()
            }
            
            # Create sale_date if we have year and month
            if property_data['sale_year'] and property_data['sale_month']:
                property_data['sale_date'] = f"{property_data['sale_year']}-{property_data['sale_month']:02d}-01"
            
            properties.append(property_data)
            
            if (i + 1) % 10000 == 0:
                print(f"  Read {i + 1:,} records...")
    
    print(f"Total unique properties: {len(properties):,}")
    return properties

def upload_to_supabase(properties):
    """Upload properties to Supabase in batches"""
    print("\nUploading to Supabase...")
    
    batch_size = 500  # Smaller batches for reliability
    total = len(properties)
    successful = 0
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = properties[i:i+batch_size]
        
        try:
            # Use upsert to handle duplicates
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            
            response = requests.post(
                url,
                json=batch,
                headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
            )
            
            if response.status_code in [200, 201, 204]:
                successful += len(batch)
                print(f"  Uploaded {successful:,}/{total:,} ({(successful/total)*100:.1f}%)")
            else:
                failed += len(batch)
                print(f"  Failed batch {i//batch_size + 1}: {response.status_code}")
                print(f"  Error: {response.text[:200]}")
        
        except Exception as e:
            failed += len(batch)
            print(f"  Exception in batch {i//batch_size + 1}: {str(e)}")
        
        # Rate limiting
        time.sleep(0.1)
    
    print(f"\nUpload complete!")
    print(f"  Successful: {successful:,}")
    print(f"  Failed: {failed:,}")
    
    return successful

def verify_upload():
    """Verify the upload worked"""
    print("\nVerifying upload...")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.head(url, headers=headers)
    
    if response.status_code == 200:
        count = response.headers.get('content-range', '').split('/')[-1]
        print(f"Total properties in database: {count}")
    else:
        print("Could not verify count")

def main():
    start_time = time.time()
    
    # Load all properties from NAL file
    properties = load_nal_file()
    
    if not properties:
        print("No properties found!")
        return
    
    # Upload to Supabase
    successful = upload_to_supabase(properties)
    
    # Verify
    verify_upload()
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed/60:.1f} minutes")
    print("="*60)
    print("COMPLETE! All Broward County properties loaded.")

if __name__ == "__main__":
    main()