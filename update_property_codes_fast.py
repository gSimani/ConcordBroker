"""
Fast update of property_use codes from NAL file using bulk updates
"""

import os
import csv
import json
import requests
from dotenv import load_dotenv
from collections import Counter

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

def get_use_category(code):
    """Get category for property use code"""
    if not code:
        return 'Unknown'
    
    # Ensure 3-digit format
    code = code.zfill(3)
    code_num = int(code)
    
    if 0 <= code_num <= 9:
        return 'Residential'
    elif 10 <= code_num <= 39:
        return 'Commercial'
    elif 40 <= code_num <= 49:
        return 'Industrial'
    elif 50 <= code_num <= 69:
        return 'Agricultural'
    elif 70 <= code_num <= 79:
        return 'Institutional'
    elif 80 <= code_num <= 89:
        return 'Government'
    elif 90 <= code_num <= 99:
        return 'Miscellaneous'
    else:
        return 'Unknown'

def main():
    print("FAST UPDATE OF PROPERTY USE CODES")
    print("="*60)
    
    # Read NAL file and create lookup
    print("Reading NAL file...")
    property_codes = {}
    
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            dor_uc = row.get('DOR_UC', '').strip()
            
            if parcel_id and dor_uc:
                # Store with 3-digit padding
                property_codes[parcel_id] = dor_uc.zfill(3)
            
            if (i + 1) % 50000 == 0:
                print(f"  Read {i + 1} records...")
    
    print(f"Found {len(property_codes)} properties with use codes")
    
    # Show distribution
    code_categories = Counter()
    for code in property_codes.values():
        code_categories[get_use_category(code)] += 1
    
    print("\nProperty use distribution:")
    for category, count in code_categories.most_common():
        print(f"  {category}: {count:,}")
    
    # Get all properties from database  
    print("\nFetching properties from database...")
    all_properties = []
    offset = 0
    limit = 1000
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=id,parcel_id&limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch properties: {response.status_code}")
            break
            
        batch = response.json()
        if not batch:
            break
            
        all_properties.extend(batch)
        offset += limit
        
        if len(all_properties) % 10000 == 0:
            print(f"  Fetched {len(all_properties)} properties...")
    
    print(f"Found {len(all_properties)} properties in database")
    
    # Prepare updates
    print("\nPreparing updates...")
    updates_by_code = {}
    
    for prop in all_properties:
        parcel_id = prop['parcel_id']
        if parcel_id in property_codes:
            use_code = property_codes[parcel_id]
            
            if use_code not in updates_by_code:
                updates_by_code[use_code] = []
            updates_by_code[use_code].append(prop['id'])
    
    # Perform bulk updates by code
    print(f"\nUpdating {sum(len(ids) for ids in updates_by_code.values())} properties...")
    
    for code, ids in updates_by_code.items():
        # Update in chunks of 500
        for i in range(0, len(ids), 500):
            chunk_ids = ids[i:i+500]
            
            # Build filter
            id_filter = f"id=in.({','.join(map(str, chunk_ids))})"
            
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels?{id_filter}"
            data = {'property_use': code}
            
            response = requests.patch(url, json=data, headers=headers)
            
            if response.status_code != 204:
                print(f"  Warning: Failed to update code {code}: {response.status_code}")
        
        print(f"  Updated {len(ids)} properties with code {code} ({get_use_category(code)})")
    
    print("\n" + "="*60)
    print("Update complete!")
    
    # Verify the update
    print("\nVerifying update...")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=property_use&property_use=not.is.null&limit=10"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        sample = response.json()
        print(f"Sample of updated properties:")
        for prop in sample[:5]:
            code = prop['property_use']
            print(f"  Code: {code} ({get_use_category(code)})")

if __name__ == "__main__":
    main()