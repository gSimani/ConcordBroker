"""
Categorize remaining properties without use codes using intelligent rules
"""

import os
import requests
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

def categorize_by_owner(owner_name):
    """Categorize based on owner name patterns"""
    if not owner_name:
        return None
    
    owner_upper = owner_name.upper()
    
    # Government
    if any(word in owner_upper for word in ['COUNTY', 'CITY OF', 'STATE OF', 'SCHOOL', 'DISTRICT', 'GOVERNMENT', 'MUNICIPAL']):
        return '080'  # Government
    
    # Utility
    if any(word in owner_upper for word in ['POWER', 'ELECTRIC', 'UTILITY', 'WATER', 'GAS', 'FLORIDA POWER']):
        return '091'  # Utility
    
    # Commercial
    if any(word in owner_upper for word in ['LLC', 'CORP', 'INC', 'COMPANY', 'ASSOCIATES', 'PARTNERS', 'PROPERTIES', 
                                             'INVESTMENT', 'HOTEL', 'RETAIL', 'OFFICE', 'PLAZA', 'CENTER', 'MALL',
                                             'BANK', 'FINANCIAL', 'INSURANCE']):
        return '011'  # Commercial/Stores
    
    # Industrial
    if any(word in owner_upper for word in ['INDUSTRIAL', 'WAREHOUSE', 'DISTRIBUTION', 'MANUFACTURING', 'LOGISTICS']):
        return '048'  # Warehouse
    
    # Institutional
    if any(word in owner_upper for word in ['CHURCH', 'TEMPLE', 'MOSQUE', 'SYNAGOGUE', 'HOSPITAL', 'MEDICAL',
                                             'CHARITABLE', 'FOUNDATION', 'TRUST']):
        return '071'  # Church/Institutional
    
    # Default to residential for individual names
    if ' ' in owner_name and not any(char in owner_name for char in ['&', 'LLC', 'CORP']):
        return '001'  # Single Family
    
    return None

def categorize_by_value(taxable_value, total_living_area):
    """Categorize based on property characteristics"""
    if taxable_value and taxable_value > 0:
        # Small residential properties
        if taxable_value < 500000 and (not total_living_area or total_living_area < 5000):
            return '001'  # Single Family
        
        # Large commercial properties
        if taxable_value > 5000000:
            return '011'  # Commercial
    
    return None

def main():
    print("CATEGORIZING REMAINING PROPERTIES")
    print("="*60)
    
    # Get properties without use codes
    print("Fetching properties without use codes...")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=id,parcel_id,owner_name,taxable_value,total_living_area&property_use=is.null&limit=1000"
    
    all_properties = []
    offset = 0
    
    while True:
        batch_url = f"{url}&offset={offset}"
        response = requests.get(batch_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch properties: {response.status_code}")
            break
            
        batch = response.json()
        if not batch:
            break
            
        all_properties.extend(batch)
        offset += len(batch)
        
        print(f"  Fetched {len(all_properties)} properties...")
        
        if len(batch) < 1000:
            break
    
    print(f"Found {len(all_properties)} properties without use codes")
    
    if not all_properties:
        print("No properties need categorization!")
        return
    
    # Categorize properties
    print("\nCategorizing properties...")
    updates_by_code = {}
    uncategorized = []
    
    for prop in all_properties:
        # Try owner-based categorization first
        use_code = categorize_by_owner(prop.get('owner_name'))
        
        # If no match, try value-based
        if not use_code:
            use_code = categorize_by_value(
                prop.get('taxable_value'),
                prop.get('total_living_area')
            )
        
        # Default to residential if still no match
        if not use_code:
            use_code = '001'  # Default to single family
        
        if use_code:
            if use_code not in updates_by_code:
                updates_by_code[use_code] = []
            updates_by_code[use_code].append(prop['id'])
        else:
            uncategorized.append(prop['id'])
    
    # Perform updates
    print(f"\nUpdating {sum(len(ids) for ids in updates_by_code.values())} properties...")
    
    for code, ids in updates_by_code.items():
        # Update in chunks
        for i in range(0, len(ids), 500):
            chunk_ids = ids[i:i+500]
            
            id_filter = f"id=in.({','.join(map(str, chunk_ids))})"
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels?{id_filter}"
            data = {'property_use': code}
            
            response = requests.patch(url, json=data, headers=headers)
            
            if response.status_code != 204:
                print(f"  Warning: Failed to update code {code}: {response.status_code}")
        
        print(f"  Updated {len(ids)} properties with code {code}")
    
    if uncategorized:
        print(f"\n{len(uncategorized)} properties could not be categorized")
    
    # Verify final distribution
    print("\n" + "="*60)
    print("FINAL VERIFICATION")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=property_use"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        properties = response.json()
        
        categories = {
            'Residential': 0,
            'Commercial': 0,
            'Industrial': 0,
            'Agricultural': 0,
            'Institutional': 0,
            'Government': 0,
            'Miscellaneous': 0,
            'No Code': 0
        }
        
        for prop in properties:
            code = prop.get('property_use', '')
            if not code:
                categories['No Code'] += 1
            else:
                code_num = int(code) if code.isdigit() else -1
                
                if 0 <= code_num <= 9:
                    categories['Residential'] += 1
                elif 10 <= code_num <= 39:
                    categories['Commercial'] += 1
                elif 40 <= code_num <= 49:
                    categories['Industrial'] += 1
                elif 50 <= code_num <= 69:
                    categories['Agricultural'] += 1
                elif 70 <= code_num <= 79:
                    categories['Institutional'] += 1
                elif 80 <= code_num <= 89:
                    categories['Government'] += 1
                elif 90 <= code_num <= 99:
                    categories['Miscellaneous'] += 1
        
        print("\nFinal property distribution:")
        total = sum(categories.values())
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                percent = (count / total) * 100
                print(f"  {category}: {count:,} ({percent:.1f}%)")

if __name__ == "__main__":
    main()