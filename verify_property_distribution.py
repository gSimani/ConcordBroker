"""
Verify the full distribution of property use codes in the database
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
    'Content-Type': 'application/json'
}

def get_category_name(code):
    """Get category name for property use code"""
    if not code:
        return 'No Code'
    
    try:
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
    except:
        return 'Invalid'

def main():
    print("VERIFYING PROPERTY USE CODE DISTRIBUTION")
    print("="*60)
    
    # Get all properties with their use codes
    print("Fetching all properties...")
    
    all_properties = []
    offset = 0
    limit = 1000
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=property_use&limit={limit}&offset={offset}"
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
    
    print(f"Total properties: {len(all_properties)}")
    
    # Count by category
    categories = {}
    code_details = {}
    
    for prop in all_properties:
        code = prop.get('property_use', '')
        category = get_category_name(code)
        
        categories[category] = categories.get(category, 0) + 1
        
        if code:
            code_details[code] = code_details.get(code, 0) + 1
    
    # Show distribution
    print("\n" + "="*60)
    print("PROPERTY DISTRIBUTION BY CATEGORY:")
    print("="*60)
    
    total = len(all_properties)
    for category in ['Residential', 'Commercial', 'Industrial', 'Agricultural', 
                     'Institutional', 'Government', 'Miscellaneous', 'No Code', 'Unknown', 'Invalid']:
        if category in categories:
            count = categories[category]
            percent = (count / total) * 100
            print(f"{category:15} : {count:8,} ({percent:5.2f}%)")
    
    # Show top codes
    print("\n" + "="*60)
    print("TOP 10 PROPERTY USE CODES:")
    print("="*60)
    
    sorted_codes = sorted(code_details.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for code, count in sorted_codes:
        category = get_category_name(code)
        percent = (count / total) * 100
        print(f"Code {code:3} ({category:12}) : {count:8,} ({percent:5.2f}%)")
    
    # Check filter values
    print("\n" + "="*60)
    print("FILTER BUTTON COUNTS:")
    print("="*60)
    
    # Count for each filter button
    residential_codes = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '000']
    commercial_codes = [f'{i:03d}' for i in range(10, 40)]
    industrial_codes = [f'{i:03d}' for i in range(40, 50)]
    
    residential_count = sum(code_details.get(code, 0) for code in residential_codes)
    commercial_count = sum(code_details.get(code, 0) for code in commercial_codes)
    industrial_count = sum(code_details.get(code, 0) for code in industrial_codes)
    
    print(f"Residential (001): {residential_count:,} properties")
    print(f"Commercial (200) : {commercial_count:,} properties")
    print(f"Industrial (400) : {industrial_count:,} properties")
    
    print("\n" + "="*60)
    print("VERIFICATION COMPLETE!")

if __name__ == "__main__":
    main()