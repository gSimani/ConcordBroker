"""
Test loading a small sample of properties first
"""

import os
import csv
import json
import requests
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

def main():
    print("TESTING PROPERTY LOAD WITH SAMPLE DATA")
    print("="*60)
    
    # Read first 100 properties from NAL
    properties = []
    
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if i >= 100:  # Just 100 for testing
                break
            
            parcel_id = clean_value(row.get('PARCEL_ID'))
            if not parcel_id:
                continue
            
            property_data = {
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'year': 2025,
                'owner_name': clean_value(row.get('OWN_NAME')),
                'phy_addr1': clean_value(row.get('PHY_ADDR1')),
                'phy_city': clean_value(row.get('PHY_CITY')),
                'property_use': clean_value(row.get('DOR_UC')),
                'taxable_value': parse_number(row.get('TV_SD')) or parse_number(row.get('TV_NSD')),
                'is_redacted': False,
                'data_source': 'NAL_TEST',
                'import_date': datetime.now().isoformat()
            }
            
            properties.append(property_data)
    
    print(f"Loaded {len(properties)} test properties")
    
    # Show sample
    print("\nSample properties:")
    for p in properties[:5]:
        print(f"  {p['parcel_id']}: {p['phy_addr1']} - {p['phy_city']}")
    
    # Test upload
    print("\nTesting upload...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    response = requests.post(
        url,
        json=properties[:10],  # Just 10 for test
        headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
    )
    
    print(f"Response status: {response.status_code}")
    if response.status_code not in [200, 201, 204]:
        print(f"Error: {response.text[:500]}")
    else:
        print("SUCCESS! Test upload worked.")
        print("\nYou can now run: python load_all_properties.py")
        print("This will load all 753,243 properties.")

if __name__ == "__main__":
    main()