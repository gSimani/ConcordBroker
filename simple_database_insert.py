"""
Simple direct database insertion for ConcordBroker
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found")
    exit(1)

print(f"Connecting to Supabase: {SUPABASE_URL}")

# Headers for API requests
headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def insert_properties():
    """Insert Florida properties directly"""
    print("\nInserting Florida properties...")
    
    properties = [
        {
            'parcel_id': '10-42-35-4500-1200',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '3930 Bayview Drive',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33308',
            'owner_name': 'Bayview Estates LLC',
            'property_use': '001',
            'year_built': 2021,
            'total_living_area': 3100,
            'land_sqft': 7500,
            'bedrooms': 4,
            'bathrooms': 3,
            'just_value': 695000,
            'assessed_value': 625500,
            'taxable_value': 556000,
            'land_value': 265000,
            'building_value': 430000,
            'sale_date': '2024-04-10',
            'sale_price': 665000
        },
        {
            'parcel_id': '10-42-28-5800-0420',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '1234 Ocean Boulevard',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33301',
            'owner_name': 'Ocean Properties LLC',
            'property_use': '001',
            'year_built': 2018,
            'total_living_area': 3200,
            'land_sqft': 8500,
            'bedrooms': 4,
            'bathrooms': 3,
            'just_value': 1250000,
            'assessed_value': 1125000,
            'taxable_value': 1000000,
            'land_value': 450000,
            'building_value': 800000,
            'sale_date': '2023-08-15',
            'sale_price': 1175000
        },
        {
            'parcel_id': '10-42-30-1200-0100',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '567 Las Olas Boulevard',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33301',
            'owner_name': 'Las Olas Investments LLC',
            'property_use': '001',
            'year_built': 2019,
            'total_living_area': 2950,
            'land_sqft': 6800,
            'bedrooms': 3,
            'bathrooms': 3,
            'just_value': 875000,
            'assessed_value': 787500,
            'taxable_value': 700000,
            'land_value': 280000,
            'building_value': 595000,
            'sale_date': '2023-11-10',
            'sale_price': 825000
        }
    ]
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    try:
        # Try to insert data
        response = requests.post(url, json=properties, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            print(f"Successfully inserted {len(properties)} properties")
            return True
        elif response.status_code == 401:
            print("Authentication error - checking RLS policies...")
            return False
        elif "42501" in response.text:
            print("Row Level Security (RLS) is blocking insertion")
            print("Need to disable RLS or grant proper permissions")
            return False
        else:
            print(f"Failed to insert properties: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error inserting properties: {e}")
        return False

def verify_data():
    """Verify data was inserted"""
    print("\nVerifying data in database...")
    
    # Check properties
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*"
    headers_count = headers.copy()
    headers_count['Prefer'] = 'count=exact'
    
    try:
        response = requests.get(url, headers=headers_count)
        print(f"Verification response: {response.status_code}")
        
        if response.status_code == 200:
            count = response.headers.get('content-range', '').split('/')[-1]
            properties = response.json()
            print(f"Properties in database: {count}")
            
            if properties:
                print("Sample properties found:")
                for prop in properties[:3]:
                    addr = prop.get('phy_addr1', 'N/A')
                    city = prop.get('phy_city', 'N/A') 
                    parcel = prop.get('parcel_id', 'N/A')
                    print(f"  - {addr}, {city} (Parcel: {parcel})")
            
            return int(count) if count.isdigit() else 0
        else:
            print(f"Failed to verify properties: {response.status_code}")
            print(f"Error: {response.text}")
            return 0
    except Exception as e:
        print(f"Error verifying data: {e}")
        return 0

def check_tables():
    """Check what tables exist"""
    print("\nChecking available tables...")
    
    # Try to list tables
    tables_to_check = ['florida_parcels', 'fl_sdf_sales', 'sunbiz_corporate_filings']
    
    for table in tables_to_check:
        url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(f"  Table '{table}': EXISTS and accessible")
            elif response.status_code == 401:
                print(f"  Table '{table}': EXISTS but not accessible (RLS/auth)")
            elif response.status_code == 404:
                print(f"  Table '{table}': NOT FOUND")
            else:
                print(f"  Table '{table}': Status {response.status_code}")
        except Exception as e:
            print(f"  Table '{table}': Error - {e}")

def main():
    """Main function"""
    print("CONCORDBROKER DATABASE POPULATION")
    print("=" * 50)
    
    # Check tables first
    check_tables()
    
    # Try to insert data
    success = insert_properties()
    
    # Verify results
    property_count = verify_data()
    
    print("\n" + "=" * 50)
    if property_count > 0:
        print("DATABASE POPULATED SUCCESSFULLY!")
        print(f"Found {property_count} properties in database")
        print("\nYour website should now show properties at:")
        print("   http://localhost:5174/properties")
        print("\nTry searching for:")
        print("   - 3930 (should find '3930 Bayview Drive')")
        print("   - Ocean Boulevard")
        print("   - Fort Lauderdale")
    else:
        print("NO PROPERTIES FOUND IN DATABASE")
        if not success:
            print("Database insertion failed - likely due to:")
            print("1. Row Level Security (RLS) policies")
            print("2. Missing table columns")
            print("3. Authentication issues")
            print("\nPlease run the populate_database.sql script")
            print("manually in your Supabase SQL Editor")
    print("=" * 50)

if __name__ == "__main__":
    main()