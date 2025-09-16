"""
Load REAL Florida Data - Fixed field mappings
"""

import os
import csv
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

print(f"Connecting to Supabase: {SUPABASE_URL}")

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def load_nap_data(filename='NAP16P202501.csv', max_records=500):
    """Load NAP data with correct field mappings"""
    print(f"\nLoading NAP data from {filename}...")
    
    properties = []
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if i >= max_records:
                break
            
            # Map NAP fields correctly
            property_data = {
                'parcel_id': row.get('ACCT_ID', '').strip().replace('"', ''),
                'county': 'BROWARD',
                'year': 2025,
                'phy_addr1': row.get('PHY_ADDR', '').strip().replace('"', ''),
                'phy_city': row.get('PHY_CITY', '').strip().replace('"', ''),
                'phy_state': 'FL',
                'phy_zipcd': row.get('PHY_ZIPCD', '').strip().replace('"', ''),
                'owner_name': row.get('OWN_NAM', '').strip().replace('"', ''),
                'owner_addr1': row.get('OWN_ADDR', '').strip().replace('"', ''),
                'owner_city': row.get('OWN_CITY', '').strip().replace('"', ''),
                'owner_state': row.get('OWN_STATE', '').strip().replace('"', ''),
                'owner_zip': row.get('OWN_ZIPCD', '').strip().replace('"', ''),
                'just_value': int(row.get('JV_TOTAL', 0) or 0),
                'assessed_value': int(row.get('AV_TOTAL', 0) or 0),
                'taxable_value': int(row.get('TAX_VAL', 0) or 0),
                'is_redacted': False,
                'data_source': 'NAP2025'
            }
            
            # Only add if has valid data
            if property_data['parcel_id'] and property_data['phy_addr1']:
                properties.append(property_data)
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1} records...")
    
    print(f"Prepared {len(properties)} properties")
    
    # Show sample
    if properties:
        print("\nSample property:")
        sample = properties[0]
        print(f"  Parcel: {sample['parcel_id']}")
        print(f"  Address: {sample['phy_addr1']}, {sample['phy_city']}")
        print(f"  Owner: {sample['owner_name']}")
        print(f"  Value: ${sample['taxable_value']:,}")
    
    return properties

def insert_to_supabase(properties):
    """Insert properties to Supabase"""
    print(f"\nInserting {len(properties)} properties to Supabase...")
    
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(properties), batch_size):
        batch = properties[i:i + batch_size]
        
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        
        response = requests.post(url, json=batch, headers=headers)
        
        if response.status_code in [200, 201]:
            total_inserted += len(batch)
            print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} properties")
        elif "42501" in response.text:
            print("\nRLS BLOCKING! Run this SQL in Supabase first:")
            print("\nALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY;")
            print("CREATE POLICY \"Allow all\" ON florida_parcels FOR ALL USING (true);")
            print("ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;")
            return False
        else:
            print(f"  Failed: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    
    print(f"\nTotal inserted: {total_inserted}")
    return total_inserted > 0

def main():
    print("LOADING REAL FLORIDA DATA")
    print("="*60)
    
    # Load and parse NAP data
    properties = load_nap_data(max_records=100)  # Start with 100
    
    if properties:
        # Try to insert
        success = insert_to_supabase(properties)
        
        if success:
            print("\n" + "="*60)
            print("SUCCESS! Real data loaded!")
            print("Check http://localhost:5174/properties")
        else:
            print("\nFailed - see errors above")
    else:
        print("No valid properties found in NAP file")

if __name__ == "__main__":
    main()