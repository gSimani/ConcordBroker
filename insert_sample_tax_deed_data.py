"""
Insert sample tax deed data for testing
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
import random

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

def create_sample_data():
    """Create sample tax deed properties"""
    
    properties = []
    
    # Upcoming auctions
    for i in range(5):
        prop = {
            'composite_key': f'TD-2025-{i+1:03d}_06421001{i:04d}',
            'auction_id': 'AUCTION-2025-02',
            'tax_deed_number': f'TD-2025-{i+1:03d}',
            'parcel_number': f'06421001{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/06421001{i:04d}',
            'tax_certificate_number': f'TC-2023-{12345+i}',
            'legal_description': f'LOT {i+1} BLOCK {i+2} BROWARD ESTATES',
            'situs_address': f'{100+i*10} Main Street',
            'city': 'Fort Lauderdale',
            'state': 'FL',
            'zip_code': '33301',
            'homestead': i % 3 == 0,  # Every third property is homestead
            'assessed_value': random.randint(200000, 800000),
            'opening_bid': random.randint(50000, 300000),
            'best_bid': random.randint(60000, 320000) if i % 2 == 0 else None,
            'close_time': (datetime.now() + timedelta(days=random.randint(5, 30))).isoformat(),
            'status': 'Active',
            'applicant': f'INVESTOR GROUP {chr(65+i)} LLC' if i % 2 == 0 else f'John Doe {i+1}',
            'applicant_companies': [f'INVESTOR GROUP {chr(65+i)} LLC'] if i % 2 == 0 else [],
            'gis_map_url': f'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=06421001{i:04d}',
            'sunbiz_matched': i % 2 == 0,
            'sunbiz_entity_names': [f'INVESTOR GROUP {chr(65+i)} LLC'] if i % 2 == 0 else [],
            'sunbiz_entity_ids': [f'L2400004567{i}'] if i % 2 == 0 else [],
            'auction_date': '2025-02-15',
            'auction_description': 'February 2025 Tax Deed Sale'
        }
        properties.append(prop)
    
    # Past auctions (sold)
    for i in range(3):
        prop = {
            'composite_key': f'TD-2024-{i+101:03d}_38421005{i:04d}',
            'auction_id': 'AUCTION-2024-12',
            'tax_deed_number': f'TD-2024-{i+101:03d}',
            'parcel_number': f'38421005{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/38421005{i:04d}',
            'tax_certificate_number': f'TC-2022-{88888+i}',
            'legal_description': f'UNIT {105+i} WATERFRONT CONDOS',
            'situs_address': f'{999+i*2} Bayshore Drive',
            'city': 'Fort Lauderdale',
            'state': 'FL',
            'zip_code': '33304',
            'homestead': False,
            'assessed_value': random.randint(400000, 900000),
            'opening_bid': random.randint(150000, 400000),
            'best_bid': random.randint(200000, 450000),
            'close_time': (datetime.now() - timedelta(days=random.randint(30, 90))).isoformat(),
            'status': 'Sold',
            'applicant': f'COASTAL INVESTMENTS {chr(65+i)} LLC',
            'applicant_companies': [f'COASTAL INVESTMENTS {chr(65+i)} LLC'],
            'gis_map_url': f'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=38421005{i:04d}',
            'sunbiz_matched': True,
            'sunbiz_entity_names': [f'COASTAL INVESTMENTS {chr(65+i)} LLC'],
            'sunbiz_entity_ids': [f'L2400004567{i+10}'],
            'auction_date': '2024-12-15',
            'auction_description': 'December 2024 Tax Deed Sale'
        }
        properties.append(prop)
    
    # Cancelled auctions
    for i in range(2):
        prop = {
            'composite_key': f'TD-2025-{i+201:03d}_51421009{i:04d}',
            'auction_id': 'AUCTION-2025-01',
            'tax_deed_number': f'TD-2025-{i+201:03d}',
            'parcel_number': f'51421009{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/51421009{i:04d}',
            'tax_certificate_number': f'TC-2023-{33333+i}',
            'legal_description': f'VACANT LOT SUNRISE INDUSTRIAL',
            'situs_address': f'{1001+i*10} Industrial Way',
            'city': 'Sunrise',
            'state': 'FL',
            'zip_code': '33323',
            'homestead': False,
            'assessed_value': random.randint(100000, 300000),
            'opening_bid': random.randint(30000, 100000),
            'best_bid': None,
            'close_time': (datetime.now() - timedelta(days=random.randint(5, 20))).isoformat(),
            'status': 'Cancelled',
            'applicant': 'TAX CERTIFICATE HOLDER',
            'applicant_companies': [],
            'gis_map_url': f'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=51421009{i:04d}',
            'sunbiz_matched': False,
            'sunbiz_entity_names': [],
            'sunbiz_entity_ids': [],
            'auction_date': '2025-01-15',
            'auction_description': 'January 2025 Tax Deed Sale'
        }
        properties.append(prop)
    
    return properties

def insert_to_supabase():
    """Insert sample data to Supabase"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Generate sample data
        properties = create_sample_data()
        
        print(f"Inserting {len(properties)} sample properties...")
        print(f"  - Upcoming: {len([p for p in properties if p['status'] == 'Active'])}")
        print(f"  - Past/Sold: {len([p for p in properties if p['status'] == 'Sold'])}")
        print(f"  - Cancelled: {len([p for p in properties if p['status'] == 'Cancelled'])}")
        
        # Insert data using upsert
        response = supabase.table('tax_deed_properties_with_contacts').upsert(
            properties,
            on_conflict='composite_key'
        ).execute()
        
        print(f"\nSuccessfully inserted {len(properties)} sample properties!")
        print("\nSample properties added:")
        for prop in properties[:3]:
            print(f"  - {prop['tax_deed_number']}: {prop['situs_address']} ({prop['status']})")
        
        return True
        
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False

if __name__ == "__main__":
    print("Tax Deed Sample Data Loader")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print("=" * 60)
    
    if insert_to_supabase():
        print("\n" + "="*60)
        print("Next Steps:")
        print("1. Open http://localhost:5173/tax-deed-sales")
        print("2. You should now see the sample tax deed data")
        print("3. Try switching between Upcoming, Past, and Cancelled tabs")
        print("="*60)
    else:
        print("\nFailed to insert sample data. Please check the error above.")