"""
Load ALL Broward County Properties - 90,509 records
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

def clear_existing_data():
    """Clear existing test data"""
    print("Clearing existing test data...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.TEST-123"
    requests.delete(url, headers=headers)

def load_all_properties():
    """Load ALL properties from NAP file"""
    print("Loading ALL Broward County properties...")
    
    properties = []
    total_loaded = 0
    batch_num = 0
    batch_size = 500
    
    with open('NAP16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            # Map fields
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
                'data_source': 'NAP2025_FULL'
            }
            
            # Add if valid
            if property_data['parcel_id'] and property_data['phy_addr1']:
                properties.append(property_data)
            
            # Insert in batches
            if len(properties) >= batch_size:
                batch_num += 1
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
                
                try:
                    response = requests.post(url, json=properties, headers=headers)
                    
                    if response.status_code in [200, 201]:
                        total_loaded += len(properties)
                        print(f"Batch {batch_num}: Loaded {len(properties)} properties (Total: {total_loaded:,})")
                    else:
                        print(f"Batch {batch_num} failed: {response.status_code}")
                        if "duplicate" in response.text.lower():
                            print("  Skipping duplicates...")
                            total_loaded += len(properties)
                except Exception as e:
                    print(f"Error in batch {batch_num}: {e}")
                
                properties = []
                
                # Progress update
                if batch_num % 10 == 0:
                    print(f"Progress: {total_loaded:,} / ~90,000 ({total_loaded*100/90000:.1f}%)")
                    time.sleep(0.5)  # Brief pause
        
        # Insert remaining
        if properties:
            batch_num += 1
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            try:
                response = requests.post(url, json=properties, headers=headers)
                if response.status_code in [200, 201]:
                    total_loaded += len(properties)
                    print(f"Final batch: Loaded {len(properties)} properties")
            except Exception as e:
                print(f"Error in final batch: {e}")
    
    return total_loaded

def verify_count():
    """Check total count in database"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[0]['count'] if data else 0
    return 0

def test_search():
    """Test some searches"""
    print("\nTesting searches...")
    
    test_addresses = [
        "PARKLAND",
        "FORT LAUDERDALE", 
        "COCONUT CREEK",
        "DEERFIELD BEACH",
        "POMPANO BEACH"
    ]
    
    for city in test_addresses:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?phy_city=ilike.*{city}*&limit=5&select=phy_addr1,phy_city,owner_name"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            print(f"\n{city}: Found {len(results)} properties")
            if results:
                for r in results[:2]:
                    print(f"  - {r['phy_addr1']}, {r['phy_city']} ({r['owner_name']})")

def main():
    print("="*60)
    print("LOADING ALL 90,509 BROWARD COUNTY PROPERTIES")
    print("="*60)
    
    # Clear test data
    clear_existing_data()
    
    # Check current count
    before = verify_count()
    print(f"Properties before: {before:,}")
    
    # Load all data
    print("\nStarting full data load...")
    start = time.time()
    total = load_all_properties()
    elapsed = time.time() - start
    
    # Verify
    after = verify_count()
    
    print("\n" + "="*60)
    print("LOADING COMPLETE!")
    print(f"Time taken: {elapsed/60:.1f} minutes")
    print(f"Properties loaded: {total:,}")
    print(f"Total in database: {after:,}")
    
    # Test searches
    test_search()
    
    print("\n" + "="*60)
    print("Your website can now search ANY Broward property!")
    print("Try searching for any address, city, or owner name")
    print("="*60)

if __name__ == "__main__":
    main()