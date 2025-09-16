"""
Load sample tax deed data using the correct Supabase instance
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
import random

# Use the same Supabase instance as the frontend
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def create_sample_properties():
    """Create comprehensive sample tax deed properties"""
    properties = []
    
    # Upcoming auctions (Active)
    upcoming_addresses = [
        '1234 Ocean Boulevard, Fort Lauderdale, FL 33301',
        '5678 Sunrise Avenue, Sunrise, FL 33323',
        '910 Commercial Way, Pompano Beach, FL 33062',
        '2345 Palm Street, Coral Springs, FL 33071',
        '6789 Atlantic Drive, Plantation, FL 33324',
        '3456 Beach Road, Deerfield Beach, FL 33441',
        '7890 Main Street, Hollywood, FL 33020'
    ]
    
    for i, address in enumerate(upcoming_addresses):
        prop = {
            'composite_key': f'TD-2025-{i+1:03d}_06421001{i:04d}',
            'auction_id': 'AUCTION-2025-02',
            'tax_deed_number': f'TD-2025-{i+1:03d}',
            'parcel_number': f'06421001{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/06421001{i:04d}',
            'tax_certificate_number': f'TC-2023-{12345+i}',
            'legal_description': f'LOT {i+1} BLOCK {i+2} {["BROWARD ESTATES", "SUNRISE GARDENS", "OCEAN VIEW", "PALM ESTATES"][i % 4]}',
            'situs_address': address,
            'city': address.split(',')[1].strip(),
            'state': 'FL',
            'zip_code': address.split()[-1],
            'homestead': i % 3 == 0,
            'assessed_value': random.randint(250000, 950000),
            'opening_bid': random.randint(75000, 350000),
            'best_bid': random.randint(80000, 380000) if i % 2 == 0 else None,
            'close_time': (datetime.now() + timedelta(days=random.randint(5, 30))).isoformat(),
            'status': 'Active',
            'applicant': f'{["INVESTOR GROUP", "REAL ESTATE HOLDINGS", "PROPERTY INVESTMENTS", "TAX CERTIFICATE HOLDER"][i % 4]} {chr(65+i)} LLC' if i % 2 == 0 else f'{["John", "Jane", "Robert", "Maria"][i % 4]} {["Smith", "Johnson", "Williams", "Brown"][i % 4]}',
            'applicant_companies': [f'{["INVESTOR GROUP", "REAL ESTATE HOLDINGS", "PROPERTY INVESTMENTS"][i % 3]} {chr(65+i)} LLC'] if i % 2 == 0 else [],
            'gis_map_url': f'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=06421001{i:04d}',
            'sunbiz_matched': i % 2 == 0,
            'sunbiz_entity_names': [f'{["INVESTOR GROUP", "REAL ESTATE HOLDINGS", "PROPERTY INVESTMENTS"][i % 3]} {chr(65+i)} LLC'] if i % 2 == 0 else [],
            'sunbiz_entity_ids': [f'L2500004567{i}'] if i % 2 == 0 else [],
            'auction_date': '2025-02-15',
            'auction_description': 'February 2025 Tax Deed Sale'
        }
        properties.append(prop)
    
    # Past auctions (Sold)
    past_addresses = [
        '999 Bayshore Drive, Fort Lauderdale, FL 33304',
        '888 Las Olas Boulevard, Fort Lauderdale, FL 33301',
        '777 Federal Highway, Pompano Beach, FL 33062',
        '666 University Drive, Coral Springs, FL 33071',
        '555 Sawgrass Way, Sunrise, FL 33325'
    ]
    
    for i, address in enumerate(past_addresses):
        prop = {
            'composite_key': f'TD-2024-{i+101:03d}_38421005{i:04d}',
            'auction_id': 'AUCTION-2024-12',
            'tax_deed_number': f'TD-2024-{i+101:03d}',
            'parcel_number': f'38421005{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/38421005{i:04d}',
            'tax_certificate_number': f'TC-2022-{88888+i}',
            'legal_description': f'UNIT {105+i} {["WATERFRONT CONDOS", "BEACH TOWERS", "OCEAN PLAZA", "RIVERSIDE ESTATES"][i % 4]}',
            'situs_address': address,
            'city': address.split(',')[1].strip(),
            'state': 'FL',
            'zip_code': address.split()[-1],
            'homestead': False,
            'assessed_value': random.randint(450000, 1200000),
            'opening_bid': random.randint(175000, 450000),
            'best_bid': random.randint(225000, 550000),
            'winning_bid': random.randint(250000, 600000),
            'winner_name': f'{["PRIME REAL ESTATE HOLDINGS", "COASTAL INVESTMENTS", "BEACH PROPERTIES", "FLORIDA VENTURES"][i % 4]} LLC',
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
    cancelled_addresses = [
        '1001 Industrial Way, Sunrise, FL 33323',
        '2002 Warehouse Boulevard, Pompano Beach, FL 33069',
        '3003 Commerce Park, Fort Lauderdale, FL 33309'
    ]
    
    for i, address in enumerate(cancelled_addresses):
        prop = {
            'composite_key': f'TD-2025-{i+201:03d}_51421009{i:04d}',
            'auction_id': 'AUCTION-2025-01',
            'tax_deed_number': f'TD-2025-{i+201:03d}',
            'parcel_number': f'51421009{i:04d}',
            'parcel_url': f'https://web.bcpa.net/BcpaClient/#/Record/51421009{i:04d}',
            'tax_certificate_number': f'TC-2023-{33333+i}',
            'legal_description': f'{["VACANT LOT", "INDUSTRIAL PARCEL", "COMMERCIAL LOT"][i % 3]} {["SUNRISE INDUSTRIAL", "POMPANO COMMERCE", "FORT LAUDERDALE BUSINESS PARK"][i % 3]}',
            'situs_address': address,
            'city': address.split(',')[1].strip(),
            'state': 'FL',
            'zip_code': address.split()[-1],
            'homestead': False,
            'assessed_value': random.randint(150000, 400000),
            'opening_bid': random.randint(45000, 125000),
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

def main():
    print("Tax Deed Sample Data Loader")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print("=" * 60)
    
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if table exists by trying to query it
        print("\nChecking if table exists...")
        try:
            response = supabase.table('tax_deed_properties_with_contacts').select('id').limit(1).execute()
            print("Table exists!")
        except Exception as e:
            if 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
                print("Table does not exist. Creating it now...")
                # Note: In production, you would run the SQL script to create the table
                print("Please run the create_tax_deed_table.sql script in Supabase SQL editor")
                return
        
        # Clear existing data (optional)
        print("\nClearing existing sample data...")
        supabase.table('tax_deed_properties_with_contacts').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Generate sample data
        properties = create_sample_properties()
        
        print(f"\nInserting {len(properties)} sample properties...")
        print(f"  - Upcoming/Active: {len([p for p in properties if p['status'] == 'Active'])}")
        print(f"  - Past/Sold: {len([p for p in properties if p['status'] == 'Sold'])}")
        print(f"  - Cancelled: {len([p for p in properties if p['status'] == 'Cancelled'])}")
        
        # Insert data in batches
        batch_size = 5
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i+batch_size]
            response = supabase.table('tax_deed_properties_with_contacts').upsert(
                batch,
                on_conflict='composite_key'
            ).execute()
            print(f"  Inserted batch {i//batch_size + 1}/{(len(properties) + batch_size - 1)//batch_size}")
        
        print(f"\nSuccessfully inserted {len(properties)} sample properties!")
        
        # Verify data was inserted
        verify_response = supabase.table('tax_deed_properties_with_contacts').select('status', count='exact').execute()
        if verify_response.data:
            print(f"\nVerified: {len(verify_response.data)} properties in database")
        
        print("\n" + "="*60)
        print("SUCCESS! Sample data loaded.")
        print("\nNext Steps:")
        print("1. Open http://localhost:5173/tax-deed-sales")
        print("2. You should now see the tax deed auction data")
        print("3. Try the following features:")
        print("   - Switch between Upcoming, Past, and Cancelled tabs")
        print("   - Use the search box to find properties")
        print("   - Click on filters (All, Upcoming, Homestead, High Value)")
        print("   - Click on parcel numbers to view property details")
        print("   - Check Sunbiz entity links for company research")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the table exists in Supabase")
        print("2. Verify the API key is correct")
        print("3. Check network connectivity")

if __name__ == "__main__":
    main()