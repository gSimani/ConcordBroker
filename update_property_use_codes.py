"""
Update property_use codes from NAL file which contains DOR_UC (Department of Revenue Use Codes)
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
    'Content-Type': 'application/json'
}

def read_nal_file(filename='NAL16P202501.csv'):
    """Read NAL file and extract property use codes"""
    print(f"Reading NAL file: {filename}")
    
    property_codes = {}
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                parcel_id = row.get('PARCEL_ID', '').strip()
                dor_uc = row.get('DOR_UC', '').strip()
                
                if parcel_id and dor_uc:
                    # Store the DOR_UC code as-is (3-digit format)
                    property_codes[parcel_id] = dor_uc
                
                if (i + 1) % 10000 == 0:
                    print(f"  Read {i + 1} records...")
        
        print(f"Found {len(property_codes)} properties with use codes")
        
        # Show distribution of codes
        from collections import Counter
        code_counts = Counter(property_codes.values())
        print("\nTop property use codes:")
        for code, count in code_counts.most_common(10):
            print(f"  {code}: {count} properties ({get_use_description(code)})")
        
        return property_codes
        
    except FileNotFoundError:
        print(f"NAL file not found: {filename}")
        return None

def get_use_description(code):
    """Get description for property use code"""
    # DOR codes are 3-digit, map the most common ones
    use_descriptions = {
        # Residential (000-099)
        '000': 'Vacant Residential',
        '001': 'Single Family',
        '002': 'Mobile Home',
        '003': 'Multi-Family (10+ units)',
        '004': 'Condominium',
        '005': 'Cooperative',
        '006': 'Retirement Home',
        '007': 'Multi-Family (< 10 units)',
        '008': 'Multi-Family (2-9 units)',
        '009': 'Undefined Residential',
        
        # Commercial (010-039)
        '010': 'Vacant Commercial',
        '011': 'Stores',
        '012': 'Mixed Use (Store/Office)',
        '013': 'Department Store',
        '014': 'Supermarket',
        '015': 'Regional Shopping',
        '016': 'Community Shopping',
        '017': 'Office Building',
        '018': 'Professional Building',
        '019': 'Airport',
        '020': 'Golf Course',
        '021': 'Restaurant',
        '022': 'Service Station',
        '023': 'Auto Sales/Service',
        '024': 'Repair Shop',
        '025': 'Parking Lot',
        '026': 'Wholesale',
        '027': 'Hotel/Motel',
        '028': 'Mobile Home Park',
        '029': 'Finance/Insurance',
        '030': 'Hospital',
        '031': 'Medical Building',
        '032': 'Veterinary',
        '033': 'Kennel',
        '034': 'Bowling Alley',
        '035': 'Bar/Lounge',
        '036': 'Theater',
        '037': 'Amusement Park',
        '038': 'Night Club',
        '039': 'Bank',
        
        # Industrial (040-049)
        '040': 'Vacant Industrial',
        '041': 'Light Manufacturing',
        '042': 'Heavy Manufacturing',
        '043': 'Lumber Yard',
        '044': 'Packing Plant',
        '045': 'Cannery',
        '046': 'Food Processing',
        '047': 'Mineral Processing',
        '048': 'Warehouse',
        '049': 'Open Storage',
        
        # Agricultural (050-069)
        '050': 'Improved Agricultural',
        '051': 'Cropland',
        '052': 'Timber Land',
        '053': 'Livestock',
        '054': 'Orchard/Grove',
        '055': 'Poultry/Fish/Bee',
        '056': 'Dairy',
        
        # Institutional (070-079)
        '070': 'Institutional',
        '071': 'Church',
        '072': 'Private School',
        '073': 'Hospital (Institutional)',
        '074': 'Charitable',
        '075': 'Orphanage',
        '076': 'Mortuary/Cemetery',
        '077': 'Club/Lodge',
        '078': 'Union Hall',
        
        # Government (080-089)
        '080': 'Government',
        '081': 'Military',
        '082': 'Forest/Parks',
        '083': 'Public School',
        '084': 'College',
        '085': 'Hospital (Government)',
        '086': 'County',
        '087': 'State',
        '088': 'Federal',
        '089': 'Municipal',
        
        # Miscellaneous (090-099)
        '090': 'Leasehold',
        '091': 'Utility',
        '092': 'Mining',
        '093': 'Petroleum/Gas',
        '094': 'Subsurface Rights',
        '095': 'Right of Way',
        '096': 'Submerged Land',
        '097': 'Severed Mineral Rights'
    }
    
    # DOR codes are already in 3-digit format
    # Just ensure it's padded to 3 digits
    code = code.zfill(3)
    
    return use_descriptions.get(code, 'Unknown')

def update_database_codes(property_codes):
    """Update property_use codes in database"""
    print("\nUpdating database with property use codes...")
    
    # Get all properties from database
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=id,parcel_id&limit=10000"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch properties: {response.status_code}")
        return
    
    db_properties = response.json()
    print(f"Found {len(db_properties)} properties in database")
    
    # Update in batches
    updates = []
    for prop in db_properties:
        parcel_id = prop['parcel_id']
        if parcel_id in property_codes:
            use_code = property_codes[parcel_id]
            # DOR codes are already in 3-digit format, just ensure padding
            use_code = use_code.zfill(3)
            
            updates.append({
                'id': prop['id'],
                'property_use': use_code
            })
    
    print(f"Updating {len(updates)} properties with use codes...")
    
    # Update in batches
    batch_size = 100
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        
        for update in batch:
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels?id=eq.{update['id']}"
            data = {'property_use': update['property_use']}
            
            response = requests.patch(url, json=data, headers=headers)
            
        print(f"  Updated batch {i//batch_size + 1}")
        time.sleep(0.1)  # Rate limiting
    
    print(f"Updated {len(updates)} properties with use codes")
    
    # Verify the update
    verify_codes()

def verify_codes():
    """Verify property codes in database"""
    print("\nVerifying property use codes...")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=property_use&limit=1000"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        properties = response.json()
        
        # Count by category
        categories = {
            'Residential': 0,
            'Commercial': 0,
            'Industrial': 0,
            'Agricultural': 0,
            'Institutional': 0,
            'Government': 0,
            'Miscellaneous': 0,
            'Unknown': 0
        }
        
        for prop in properties:
            code = prop.get('property_use', '')
            if code:
                if code.startswith('00') or code == '001':
                    categories['Residential'] += 1
                elif code.startswith('01') or code.startswith('02') or code.startswith('03'):
                    categories['Commercial'] += 1
                elif code.startswith('04'):
                    categories['Industrial'] += 1
                elif code.startswith('05') or code.startswith('06'):
                    categories['Agricultural'] += 1
                elif code.startswith('07'):
                    categories['Institutional'] += 1
                elif code.startswith('08'):
                    categories['Government'] += 1
                elif code.startswith('09'):
                    categories['Miscellaneous'] += 1
                else:
                    categories['Unknown'] += 1
        
        print("\nProperty categories in database:")
        for category, count in categories.items():
            if count > 0:
                print(f"  {category}: {count}")

def main():
    print("UPDATING PROPERTY USE CODES FROM NAL FILE")
    print("="*60)
    
    # Read NAL file
    property_codes = read_nal_file()
    
    if property_codes:
        # Update database
        update_database_codes(property_codes)
        
        print("\n" + "="*60)
        print("Property use codes updated successfully!")
        print("The filter buttons should now work correctly:")
        print("  - Residential: Shows single family, condos, etc.")
        print("  - Commercial: Shows stores, offices, hotels, etc.")
        print("  - Industrial: Shows warehouses, manufacturing, etc.")
    else:
        print("\nNAL file not found. Please ensure it's downloaded first.")

if __name__ == "__main__":
    main()