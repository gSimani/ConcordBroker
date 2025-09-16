"""
Run the database population script directly via Python
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
    'Prefer': 'return=minimal'
}

def insert_properties():
    """Insert Florida properties directly"""
    print("\nInserting Florida properties...")
    
    properties = [
        {
            'parcel_id': '10-42-28-5800-0420',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '1234 Ocean Boulevard',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33301',
            'owner_name': 'Ocean Properties LLC',
            'owner_addr1': '1234 Ocean Boulevard',
            'owner_city': 'Fort Lauderdale',
            'owner_state': 'FL',
            'owner_zip': '33301',
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
            'owner_addr1': '567 Las Olas Boulevard',
            'owner_city': 'Fort Lauderdale',
            'owner_state': 'FL',
            'owner_zip': '33301',
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
        },
        {
            'parcel_id': '10-42-35-4500-1200',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '3930 Bayview Drive',
            'phy_city': 'Fort Lauderdale',
            'phy_state': 'FL',
            'phy_zipcd': '33308',
            'owner_name': 'Bayview Estates LLC',
            'owner_addr1': '3930 Bayview Drive',
            'owner_city': 'Fort Lauderdale',
            'owner_state': 'FL',
            'owner_zip': '33308',
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
            'parcel_id': '15-50-22-4100-0500',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '789 Hollywood Boulevard',
            'phy_city': 'Hollywood',
            'phy_state': 'FL',
            'phy_zipcd': '33019',
            'owner_name': 'Patricia Johnson',
            'owner_addr1': '789 Hollywood Boulevard',
            'owner_city': 'Hollywood',
            'owner_state': 'FL',
            'owner_zip': '33019',
            'property_use': '001',
            'year_built': 2010,
            'total_living_area': 1850,
            'land_sqft': 4800,
            'bedrooms': 2,
            'bathrooms': 2,
            'just_value': 385000,
            'assessed_value': 346500,
            'taxable_value': 308000,
            'land_value': 140000,
            'building_value': 245000,
            'sale_date': '2024-02-28',
            'sale_price': 370000
        },
        {
            'parcel_id': '20-55-18-3600-0600',
            'county': 'BROWARD',
            'year': 2025,
            'phy_addr1': '1456 Atlantic Boulevard',
            'phy_city': 'Pompano Beach',
            'phy_state': 'FL',
            'phy_zipcd': '33062',
            'owner_name': 'Michael Davis',
            'owner_addr1': '1456 Atlantic Boulevard',
            'owner_city': 'Pompano Beach',
            'owner_state': 'FL',
            'owner_zip': '33062',
            'property_use': '001',
            'year_built': 2015,
            'total_living_area': 1650,
            'land_sqft': 4200,
            'bedrooms': 2,
            'bathrooms': 1,
            'just_value': 295000,
            'assessed_value': 265500,
            'taxable_value': 236000,
            'land_value': 110000,
            'building_value': 185000,
            'sale_date': '2023-09-20',
            'sale_price': 285000
        }
    ]
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    try:
        response = requests.post(url, json=properties, headers=headers)
        if response.status_code in [200, 201]:
            print(f"Successfully inserted {len(properties)} properties")
            return True
        else:
            print(f"Failed to insert properties: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error inserting properties: {e}")
        return False

def insert_sales():
    """Insert sales history"""
    print("\nInserting sales history...")
    
    sales = [
        {
            'parcel_id': '10-42-28-5800-0420',
            'county': 'BROWARD',
            'year': 2023,
            'sale_date': '2023-08-15',
            'sale_price': 1175000,
            'sale_type': 'WD',
            'property_address_full': '1234 Ocean Boulevard, Fort Lauderdale, FL 33301',
            'property_address_city': 'Fort Lauderdale'
        },
        {
            'parcel_id': '10-42-30-1200-0100',
            'county': 'BROWARD',
            'year': 2023,
            'sale_date': '2023-11-10',
            'sale_price': 825000,
            'sale_type': 'WD',
            'property_address_full': '567 Las Olas Boulevard, Fort Lauderdale, FL 33301',
            'property_address_city': 'Fort Lauderdale'
        },
        {
            'parcel_id': '10-42-35-4500-1200',
            'county': 'BROWARD',
            'year': 2024,
            'sale_date': '2024-04-10',
            'sale_price': 665000,
            'sale_type': 'WD',
            'property_address_full': '3930 Bayview Drive, Fort Lauderdale, FL 33308',
            'property_address_city': 'Fort Lauderdale'
        }
    ]
    
    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales"
    
    try:
        response = requests.post(url, json=sales, headers=headers)
        if response.status_code in [200, 201]:
            print(f"Successfully inserted {len(sales)} sales records")
            return True
        else:
            print(f"Failed to insert sales: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error inserting sales: {e}")
        return False

def verify_data():
    """Verify data was inserted"""
    print("\nVerifying data insertion...")
    
    # Check properties
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*"
    headers_count = headers.copy()
    headers_count['Prefer'] = 'count=exact'
    
    try:
        response = requests.get(url, headers=headers_count)
        if response.status_code == 200:
            count = response.headers.get('content-range', '').split('/')[-1]
            properties = response.json()
            print(f"Properties in database: {count}")
            
            if properties:
                print("   Sample properties:")
                for prop in properties[:3]:
                    print(f"   - {prop.get('phy_addr1', 'N/A')}, {prop.get('phy_city', 'N/A')}")
            
            return int(count) if count.isdigit() else 0
        else:
            print(f"Failed to verify properties: {response.status_code}")
            return 0
    except Exception as e:
        print(f"Error verifying data: {e}")
        return 0

def main():
    """Main function"""
    print("POPULATING CONCORDBROKER DATABASE")
    print("=" * 50)
    
    # Insert data
    properties_success = insert_properties()
    sales_success = insert_sales()
    
    # Verify
    property_count = verify_data()
    
    print("\n" + "=" * 50)
    if property_count > 0:
        print("DATABASE POPULATED SUCCESSFULLY!")
        print(f"{property_count} properties available")
        print("\nYour website should now display properties at:")
        print("   http://localhost:5174/properties")
        print("\nTry searching for:")
        print("   - 3930 (should suggest '3930 Bayview Drive')")
        print("   - Ocean Boulevard")
        print("   - Fort Lauderdale")
    else:
        print("DATABASE POPULATION FAILED")
        print("Please run the SQL script manually in Supabase dashboard")
        print("File: populate_database.sql")
    print("=" * 50)

if __name__ == "__main__":
    main()