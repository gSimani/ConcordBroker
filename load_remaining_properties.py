"""
Load ONLY the properties we don't have yet
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

def get_existing_parcels():
    """Get list of parcel IDs we already have"""
    print("Fetching existing parcel IDs...")
    existing = set()
    offset = 0
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=parcel_id&limit=1000&offset={offset}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching existing: {response.status_code}")
            break
            
        data = response.json()
        if not data:
            break
            
        for row in data:
            existing.add(row['parcel_id'])
        
        offset += 1000
        if len(existing) % 10000 == 0:
            print(f"  Fetched {len(existing)} existing IDs...")
    
    print(f"Found {len(existing)} existing properties")
    return existing

def main():
    print("LOADING REMAINING PROPERTIES")
    print("="*60)
    
    # Get existing parcel IDs
    existing_parcels = get_existing_parcels()
    
    # Read NAL file and find new properties
    print("\nReading NAL file for new properties...")
    new_properties = []
    skipped = 0
    
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Skip if we already have this property
            if parcel_id in existing_parcels:
                skipped += 1
                continue
            
            # Add new property (minimal fields for speed)
            new_properties.append({
                'parcel_id': parcel_id,
                'county': 'BROWARD',
                'year': 2025,
                'owner_name': row.get('OWN_NAME', '').strip() or None,
                'phy_addr1': row.get('PHY_ADDR1', '').strip() or None,
                'phy_city': row.get('PHY_CITY', '').strip() or None,
                'phy_zipcd': row.get('PHY_ZIPCD', '').strip() or None,
                'property_use': row.get('DOR_UC', '').strip() or None,
                'is_redacted': False,
                'data_source': 'NAL_2025'
            })
            
            if len(new_properties) % 10000 == 0:
                print(f"  Found {len(new_properties)} new properties (skipped {skipped} existing)...")
    
    print(f"\nTotal new properties to add: {len(new_properties)}")
    print(f"Skipped existing: {skipped}")
    
    if not new_properties:
        print("No new properties to add!")
        return
    
    # Upload in batches
    print("\nUploading new properties...")
    batch_size = 500
    uploaded = 0
    
    for i in range(0, len(new_properties), batch_size):
        batch = new_properties[i:i+batch_size]
        
        # Remove None values
        batch = [{k: v for k, v in prop.items() if v is not None} for prop in batch]
        
        try:
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201, 204]:
                uploaded += len(batch)
                print(f"  Uploaded {uploaded}/{len(new_properties)} ({(uploaded/len(new_properties)*100):.1f}%)")
            else:
                print(f"  Batch failed: {response.status_code}")
                if i == 0:  # Show error for first batch
                    print(f"  Error: {response.text[:300]}")
        except Exception as e:
            print(f"  Exception: {str(e)[:100]}")
        
        time.sleep(0.1)  # Rate limiting
    
    print(f"\nComplete! Added {uploaded} new properties")
    print(f"Total should now be: {len(existing_parcels) + uploaded}")

if __name__ == "__main__":
    main()