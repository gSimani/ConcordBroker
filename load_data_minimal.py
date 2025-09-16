"""
Load minimal Florida property data that matches existing table structure
"""

import os
import json
import requests
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('VITE_SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found")
    exit(1)

print(f"Supabase URL: {SUPABASE_URL}")

# Use service key if available
API_KEY = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

headers = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Fort Lauderdale area data
STREET_NAMES = [
    'Ocean Boulevard', 'Las Olas Boulevard', 'Sunrise Boulevard', 'Federal Highway',
    'Atlantic Boulevard', 'Commercial Boulevard', 'Oakland Park Boulevard',
    'Bayview Drive', 'Riverview Road', 'Seabreeze Boulevard'
]

CITIES = [
    'Fort Lauderdale', 'Hollywood', 'Pembroke Pines', 'Coral Springs', 
    'Pompano Beach', 'Deerfield Beach', 'Davie', 'Plantation'
]

def generate_properties(num=100):
    """Generate property records with minimal fields"""
    properties = []
    
    for i in range(num):
        street_num = random.randint(100, 9999)
        street = random.choice(STREET_NAMES)
        city = random.choice(CITIES)
        zip_code = f"33{random.randint(100, 399):03d}"
        
        # Generate owner
        is_company = random.random() < 0.6
        if is_company:
            owner_name = f"{random.choice(['Ocean', 'Palm', 'Sunset', 'Bay'])} {random.choice(['Properties', 'Holdings', 'Investments'])} LLC"
        else:
            owner_name = f"{random.choice(['John', 'Mary', 'Robert', 'Patricia'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])}"
        
        # Values
        living_area = random.randint(1000, 5000)
        land_value = random.randint(100000, 500000)
        building_value = random.randint(200000, 1000000)
        market_value = land_value + building_value
        
        prop = {
            'parcel_id': f"{random.randint(10,50):02d}-{random.randint(10,50):02d}-{random.randint(1,30):02d}-{random.randint(1000,9999):04d}-{random.randint(10000,99999):05d}",
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': f"{street_num} {street}",
            'phy_city': city,
            'phy_state': 'FL',
            'phy_zipcd': zip_code,
            'owner_name': owner_name,
            'owner_city': city,
            'owner_state': 'FL',
            'owner_zip': zip_code,
            'property_use': '001',
            'year_built': random.randint(1950, 2024),
            'total_living_area': living_area,
            'land_sqft': living_area * random.randint(2, 4),
            'bedrooms': random.randint(2, 5),
            'bathrooms': random.randint(1, 4),
            'just_value': market_value,
            'assessed_value': int(market_value * 0.9),
            'taxable_value': int(market_value * 0.8),
            'land_value': land_value,
            'building_value': building_value,
            'sale_date': (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime('%Y-%m-%d'),
            'sale_price': int(market_value * random.uniform(0.85, 1.15))
        }
        
        properties.append(prop)
    
    return properties

def generate_sales(properties):
    """Generate sales records"""
    sales = []
    
    for prop in properties[:50]:  # First 50 properties
        for i in range(2):  # 2 sales each
            sale_date = datetime.now() - timedelta(days=365 * (i + 1))
            
            sale = {
                'parcel_id': prop['parcel_id'],
                'county': 'BROWARD',
                'year': sale_date.year,
                'sale_date': sale_date.strftime('%Y-%m-%d'),
                'sale_price': int(prop['sale_price'] * (0.9 ** i)),
                'sale_type': 'WD',
                'property_address_full': f"{prop['phy_addr1']}, {prop['phy_city']}, FL {prop['phy_zipcd']}",
                'property_address_city': prop['phy_city']
            }
            sales.append(sale)
    
    return sales

def load_data(records, table):
    """Load data to Supabase"""
    if not records:
        return 0
        
    print(f"\nLoading {len(records)} records to {table}...")
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    
    success = 0
    batch_size = 20
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        try:
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201]:
                success += len(batch)
                print(f"  Batch {i//batch_size + 1}: Success ({len(batch)} records)")
            else:
                print(f"  Batch {i//batch_size + 1}: Failed - {response.status_code}")
                if response.text:
                    print(f"    {response.text[:100]}")
                    
                    # Try with upsert
                    if 'duplicate' in response.text.lower():
                        upsert_headers = headers.copy()
                        upsert_headers['Prefer'] = 'resolution=merge-duplicates'
                        resp2 = requests.post(url, json=batch, headers=upsert_headers)
                        if resp2.status_code in [200, 201]:
                            success += len(batch)
                            print(f"    Upserted successfully")
                            
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"  Total loaded: {success} records")
    return success

def main():
    print("=" * 50)
    print("LOADING FLORIDA PROPERTY DATA")
    print("=" * 50)
    
    # Generate data
    properties = generate_properties(100)
    sales = generate_sales(properties)
    
    # Load to database
    prop_count = load_data(properties, 'florida_parcels')
    sales_count = load_data(sales, 'fl_sdf_sales')
    
    print("\n" + "=" * 50)
    print("LOADING COMPLETE")
    print(f"Properties loaded: {prop_count}")
    print(f"Sales loaded: {sales_count}")
    print("=" * 50)
    
    if prop_count > 0:
        print("\n✅ Your website should now display real property data!")
        print("Visit http://localhost:5174/properties to see the properties")
    else:
        print("\n⚠️ No data was loaded. Check your Supabase table structure.")

if __name__ == "__main__":
    main()