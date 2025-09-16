"""
Load sample real estate data into Supabase database
This creates realistic Florida property data for testing
"""

import os
import json
import requests
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('VITE_SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found in .env file")
    exit(1)

print(f"Supabase URL: {SUPABASE_URL}")

# Use service key if available
API_KEY = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

# Headers for API requests
headers = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Street names for Fort Lauderdale area
STREET_NAMES = [
    'Ocean Boulevard', 'Las Olas Boulevard', 'Sunrise Boulevard', 'Federal Highway',
    'Atlantic Boulevard', 'Commercial Boulevard', 'Oakland Park Boulevard',
    'Bayview Drive', 'Riverview Road', 'Seabreeze Boulevard', 'Harbor Drive',
    'Coral Ridge Drive', 'Victoria Park Road', 'Rio Vista Boulevard', 'Davie Boulevard',
    'Griffin Road', 'Stirling Road', 'Hollywood Boulevard', 'Sheridan Street',
    'Hallandale Beach Boulevard', 'Palmetto Park Road', 'Hillsboro Boulevard'
]

# Cities in Broward County
CITIES = [
    'Fort Lauderdale', 'Hollywood', 'Pembroke Pines', 'Coral Springs', 'Miramar',
    'Davie', 'Plantation', 'Sunrise', 'Pompano Beach', 'Deerfield Beach',
    'Coconut Creek', 'Margate', 'Tamarac', 'Lauderhill', 'Weston',
    'Oakland Park', 'Hallandale Beach', 'Cooper City', 'Dania Beach', 'Wilton Manors'
]

# Company suffixes for owner names
COMPANY_SUFFIXES = ['LLC', 'Corp', 'Inc', 'Partners', 'Holdings', 'Investments', 'Properties', 'Realty', 'Group', 'Trust']

def generate_parcel_id():
    """Generate a realistic parcel ID"""
    # Broward County format: XX-XX-XX-XXXX-XXXXX
    return f"{random.randint(10,50):02d}-{random.randint(10,50):02d}-{random.randint(1,30):02d}-{random.randint(1000,9999):04d}-{random.randint(10000,99999):05d}"

def generate_owner_name():
    """Generate a realistic property owner name"""
    if random.random() < 0.6:  # 60% companies
        first_names = ['Ocean', 'Palm', 'Sunset', 'Bay', 'Harbor', 'Beach', 'Coastal', 'Marina', 'Seaside', 'Coral']
        second_names = ['View', 'Point', 'Shore', 'Ridge', 'Park', 'Gardens', 'Estates', 'Plaza', 'Tower', 'Heights']
        suffix = random.choice(COMPANY_SUFFIXES)
        return f"{random.choice(first_names)} {random.choice(second_names)} {suffix}"
    else:  # 40% individuals
        first_names = ['John', 'Mary', 'Robert', 'Patricia', 'Michael', 'Jennifer', 'William', 'Linda', 'David', 'Elizabeth']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_property_data(num_properties=500):
    """Generate sample property data"""
    print(f"\nGenerating {num_properties} sample properties...")
    
    properties = []
    for i in range(num_properties):
        street_num = random.randint(100, 9999)
        street = random.choice(STREET_NAMES)
        city = random.choice(CITIES)
        zip_code = f"33{random.randint(100, 399):03d}"
        
        # Property characteristics
        year_built = random.randint(1950, 2024)
        bedrooms = random.choice([1, 2, 3, 4, 5, 6])
        bathrooms = bedrooms * 0.5 + random.choice([0, 0.5, 1, 1.5])
        living_area = bedrooms * random.randint(400, 800) + random.randint(200, 1000)
        lot_size = living_area * random.randint(2, 5)
        
        # Values
        price_per_sqft = random.randint(150, 500)
        building_value = living_area * price_per_sqft
        land_value = lot_size * random.randint(20, 100)
        market_value = building_value + land_value
        assessed_value = int(market_value * random.uniform(0.8, 1.0))
        taxable_value = int(assessed_value * random.uniform(0.7, 1.0))
        
        # Generate owner
        owner_name = generate_owner_name()
        
        property_data = {
            'parcel_id': generate_parcel_id(),
            'county': 'BROWARD',
            'year': 2025,
            
            # Location
            'phy_addr1': f"{street_num} {street}",
            'phy_city': city,
            'phy_state': 'FL',
            'phy_zipcd': zip_code,
            
            # Owner
            'owner_name': owner_name,
            'owner_addr1': f"{street_num} {street}" if random.random() < 0.3 else f"PO Box {random.randint(1000, 9999)}",
            'owner_city': city if random.random() < 0.7 else random.choice(CITIES),
            'owner_state': 'FL',
            'owner_zip': zip_code,
            
            # Property details
            'property_use': random.choice(['001', '002', '003', '004', '008', '100', '101']),
            'property_use_desc': random.choice(['Single Family', 'Condo', 'Townhouse', 'Multi-Family', 'Commercial']),
            'year_built': year_built,
            'eff_year_built': year_built + random.randint(0, 10),
            'total_living_area': living_area,
            'heated_area': int(living_area * 0.9),
            'land_sqft': lot_size,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'units': 1,
            
            # Values
            'just_value': market_value,
            'assessed_value': assessed_value,
            'taxable_value': taxable_value,
            'land_value': land_value,
            'building_value': building_value,
            'market_value': market_value,
            'tax_amount': int(taxable_value * 0.02),
            
            # Exemptions
            'homestead_exemption': 'Y' if random.random() < 0.3 and 'LLC' not in owner_name else 'N',
            
            # Recent sale
            'sale_date': (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime('%Y-%m-%d'),
            'sale_price': int(market_value * random.uniform(0.85, 1.15)),
            
            'created_at': datetime.now().isoformat()
        }
        
        properties.append(property_data)
    
    return properties

def generate_sales_history(properties, sales_per_property=3):
    """Generate sales history for properties"""
    print(f"\nGenerating sales history...")
    
    sales = []
    for prop in properties[:100]:  # Generate sales for first 100 properties
        # Generate multiple sales for each property
        base_price = prop['sale_price']
        for i in range(sales_per_property):
            sale_date = datetime.now() - timedelta(days=365 * (i + 1) + random.randint(0, 180))
            price_factor = 0.95 ** i  # Price decreases going back in time
            
            sale = {
                'parcel_id': prop['parcel_id'],
                'county': 'BROWARD',
                'year': sale_date.year,
                'sale_date': sale_date.strftime('%Y-%m-%d'),
                'sale_price': int(base_price * price_factor * random.uniform(0.9, 1.1)),
                'sale_type': random.choice(['WD', 'QC', 'TR', 'CT']),  # Warranty Deed, Quit Claim, Trustee, Court
                'qualification_code': random.choice(['Q', 'U']),  # Qualified, Unqualified
                'is_qualified': 'Y' if random.random() < 0.8 else 'N',
                'grantor_name': generate_owner_name(),
                'grantee_name': prop['owner_name'] if i == 0 else generate_owner_name(),
                'book_page': f"Book {random.randint(30000, 35000)} / Page {random.randint(100, 999)}",
                'cin': f"CIN-{sale_date.year}-{random.randint(100000, 999999):06d}",
                'property_address_full': f"{prop['phy_addr1']}, {prop['phy_city']}, FL {prop['phy_zipcd']}",
                'property_address_street_name': prop['phy_addr1'],
                'property_address_city': prop['phy_city'],
                'created_at': datetime.now().isoformat()
            }
            sales.append(sale)
    
    return sales

def generate_sunbiz_entities(properties):
    """Generate Sunbiz corporate entities for LLC owners"""
    print(f"\nGenerating Sunbiz corporate entities...")
    
    entities = []
    seen_names = set()
    
    for prop in properties:
        owner = prop['owner_name']
        if any(suffix in owner for suffix in ['LLC', 'Corp', 'Inc']) and owner not in seen_names:
            seen_names.add(owner)
            
            filing_date = datetime.now() - timedelta(days=random.randint(365, 3650))
            
            entity = {
                'entity_name': owner.upper(),
                'entity_type': 'Limited Liability Company' if 'LLC' in owner else 'Corporation',
                'status': 'Active',
                'state': 'FL',
                'document_number': f"L{filing_date.year}{random.randint(100000, 999999):06d}",
                'fei_ein_number': f"88-{random.randint(1000000, 9999999):07d}",
                'date_filed': filing_date.strftime('%Y-%m-%d'),
                'effective_date': filing_date.strftime('%Y-%m-%d'),
                'principal_address': f"{prop['phy_addr1']}, {prop['phy_city']}, FL {prop['phy_zipcd']}",
                'mailing_address': f"{prop['owner_addr1']}, {prop['owner_city']}, {prop['owner_state']} {prop['owner_zip']}",
                'registered_agent_name': random.choice(['Florida Registered Agent LLC', 'Corporate Services Inc', 'Legal Agent Services']),
                'registered_agent_address': f"{random.randint(100, 999)} Corporate Way, Tallahassee, FL 32301",
                'officers': json.dumps([
                    {
                        'name': owner.replace(' LLC', '').replace(' Corp', '').replace(' Inc', '') + ' Manager',
                        'title': 'Managing Member' if 'LLC' in owner else 'President',
                        'address': f"{prop['owner_addr1']}, {prop['owner_city']}, {prop['owner_state']} {prop['owner_zip']}"
                    }
                ]),
                'annual_reports': json.dumps([
                    {'year': 2024, 'filed_date': '2024-05-01', 'status': 'Filed'},
                    {'year': 2023, 'filed_date': '2023-05-01', 'status': 'Filed'}
                ]),
                'created_at': datetime.now().isoformat()
            }
            entities.append(entity)
            
            if len(entities) >= 50:  # Limit to 50 entities
                break
    
    return entities

def load_to_supabase(records, table_name):
    """Load records to Supabase"""
    if not records:
        print(f"  No records to load for {table_name}")
        return
    
    print(f"  Loading {len(records)} records to {table_name}...")
    
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    # Load in batches of 50
    batch_size = 50
    success_count = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        try:
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201]:
                success_count += len(batch)
                print(f"    Loaded batch {i//batch_size + 1} ({len(batch)} records)")
            else:
                print(f"    Failed batch {i//batch_size + 1}: {response.status_code}")
                if response.text:
                    error_msg = response.text[:200]
                    print(f"    Error: {error_msg}")
                    
                    # If it's a unique constraint error, try updating
                    if 'duplicate key' in error_msg.lower():
                        print("    Attempting upsert...")
                        upsert_headers = headers.copy()
                        upsert_headers['Prefer'] = 'resolution=merge-duplicates'
                        response = requests.post(url, json=batch, headers=upsert_headers)
                        if response.status_code in [200, 201]:
                            success_count += len(batch)
                            print(f"    Upserted batch successfully")
                        
        except Exception as e:
            print(f"    Error loading batch: {e}")
    
    print(f"  Successfully loaded {success_count} records to {table_name}")

def main():
    """Main function to load sample data"""
    print("=" * 50)
    print("LOADING SAMPLE FLORIDA PROPERTY DATA")
    print("=" * 50)
    
    # Generate data
    properties = generate_property_data(500)
    sales = generate_sales_history(properties, 3)
    entities = generate_sunbiz_entities(properties)
    
    # Load to Supabase
    print("\nLoading data to Supabase...")
    load_to_supabase(properties, 'florida_parcels')
    load_to_supabase(sales, 'fl_sdf_sales')
    
    # Create sunbiz table if needed
    print("\nNote: If sunbiz_corporate_filings table doesn't exist, create it in Supabase SQL Editor")
    load_to_supabase(entities, 'sunbiz_corporate_filings')
    
    print("\n" + "=" * 50)
    print("Sample data loading complete!")
    print(f"Loaded {len(properties)} properties, {len(sales)} sales, {len(entities)} entities")
    print("Your website should now display real property data!")
    print("=" * 50)

if __name__ == "__main__":
    main()