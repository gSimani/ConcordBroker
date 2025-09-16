"""
Update existing properties with complete valuation data from NAL file
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

def main():
    print("UPDATING PROPERTY VALUES FROM NAL FILE")
    print("=" * 60)
    
    # Track progress
    updated = 0
    failed = 0
    batch = []
    batch_size = 500
    
    print("Reading NAL file for complete data...")
    
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Extract all valuation fields
            update_data = {
                'parcel_id': parcel_id,
                # Valuation fields
                'just_value': int(row.get('JV', 0) or 0) if row.get('JV') else None,
                'assessed_value': int(row.get('AV_SD', 0) or 0) if row.get('AV_SD') else None,
                'taxable_value': int(row.get('TV_SD', 0) or 0) if row.get('TV_SD') else None,
                'land_value': int(row.get('LND_VAL', 0) or 0) if row.get('LND_VAL') else None,
                # Calculate building value (Just Value - Land Value)
                'building_value': (int(row.get('JV', 0) or 0) - int(row.get('LND_VAL', 0) or 0)) if row.get('JV') and row.get('LND_VAL') else None,
                
                # Property details
                'year_built': int(row.get('ACT_YR_BLT', 0) or 0) if row.get('ACT_YR_BLT') else None,
                'total_living_area': int(row.get('TOT_LVG_AREA', 0) or 0) if row.get('TOT_LVG_AREA') else None,
                'land_sqft': int(row.get('LND_SQFOOT', 0) or 0) if row.get('LND_SQFOOT') else None,
                'units': int(row.get('NO_RES_UNTS', 0) or 0) if row.get('NO_RES_UNTS') else None,
                
                # Sales information
                'sale_price': int(row.get('SALE_PRC1', 0) or 0) if row.get('SALE_PRC1') else None,
                'sale_date': f"{row.get('SALE_YR1')}-{row.get('SALE_MO1', '01').zfill(2)}-01" if row.get('SALE_YR1') and int(row.get('SALE_YR1', 0) or 0) > 1900 else None,
                
                # Legal description
                'legal_desc': row.get('S_LEGAL', '').strip() or None,
                
                # Additional owner info
                'owner_addr1': row.get('OWN_ADDR1', '').strip() or None,
                'owner_addr2': row.get('OWN_ADDR2', '').strip() or None,
                'owner_city': row.get('OWN_CITY', '').strip() or None,
                'owner_state': row.get('OWN_STATE', '').strip() or None,
                'owner_zip': row.get('OWN_ZIPCD', '').strip() or None,
            }
            
            # Remove None values and zeros
            update_data = {k: v for k, v in update_data.items() if v is not None and v != 0}
            
            # Must have parcel_id and at least one value field
            if 'parcel_id' in update_data and len(update_data) > 1:
                batch.append(update_data)
            
            # Upload batch when full
            if len(batch) >= batch_size:
                print(f"  Updating batch {updated//batch_size + 1} ({updated} properties)...")
                
                # Use upsert to update existing records
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
                response = requests.patch(
                    url,
                    json=batch,
                    headers={**headers, 'Prefer': 'resolution=merge-duplicates'},
                    params={'parcel_id': f'eq.{batch[0]["parcel_id"]}'}  # Update by parcel_id
                )
                
                # Actually, let's use the upsert endpoint
                response = requests.post(
                    url,
                    json=batch,
                    headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
                )
                
                if response.status_code in [200, 201, 204]:
                    updated += len(batch)
                else:
                    failed += len(batch)
                    if failed <= 5:  # Show first few errors
                        print(f"    Error: {response.status_code}")
                        print(f"    {response.text[:200]}")
                
                batch = []
                time.sleep(0.1)  # Rate limiting
            
            if (i + 1) % 10000 == 0:
                print(f"  Processed {i + 1} records, updated {updated}")
    
    # Upload remaining batch
    if batch:
        print(f"  Updating final batch...")
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        response = requests.post(
            url,
            json=batch,
            headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
        )
        
        if response.status_code in [200, 201, 204]:
            updated += len(batch)
        else:
            failed += len(batch)
    
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE!")
    print(f"Successfully updated: {updated:,} properties")
    print(f"Failed: {failed:,} properties")
    
    # Test the specific property
    print("\n" + "=" * 60)
    print("TESTING PROPERTY 504231242730...")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.504231242730"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            print(f"  Just Value: ${prop.get('just_value', 'N/A')}")
            print(f"  Assessed Value: ${prop.get('assessed_value', 'N/A')}")
            print(f"  Taxable Value: ${prop.get('taxable_value', 'N/A')}")
            print(f"  Land Value: ${prop.get('land_value', 'N/A')}")
            print(f"  Building Value: ${prop.get('building_value', 'N/A')}")
            print(f"  Year Built: {prop.get('year_built', 'N/A')}")
            print(f"  Living Area: {prop.get('total_living_area', 'N/A')} sq ft")

if __name__ == "__main__":
    main()