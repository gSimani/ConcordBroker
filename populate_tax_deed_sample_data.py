"""
Populate sample Tax Deed data to Supabase for testing
"""
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    exit(1)

client: Client = create_client(supabase_url, supabase_key)

# Sample data for testing
def create_sample_auctions():
    """Create sample auction data"""
    now = datetime.now(timezone.utc)
    
    auctions = [
        {
            'auction_id': '110',
            'description': '9/17/2025 Tax Deed Sale',
            'auction_date': (now + timedelta(days=7)).isoformat(),
            'total_items': 46,
            'available_items': 42,
            'advertised_items': 46,
            'canceled_items': 4,
            'status': 'Upcoming',
            'auction_url': 'https://broward.deedauction.net/auction/110',
            'last_updated': now.isoformat(),
            'metadata': {
                'scraper_version': '2.0',
                'extraction_timestamp': now.isoformat(),
                'property_count': 46
            }
        },
        {
            'auction_id': '111',
            'description': '10/15/2025 Tax Deed Sale',
            'auction_date': (now + timedelta(days=35)).isoformat(),
            'total_items': 63,
            'available_items': 60,
            'advertised_items': 63,
            'canceled_items': 3,
            'status': 'Upcoming',
            'auction_url': 'https://broward.deedauction.net/auction/111',
            'last_updated': now.isoformat(),
            'metadata': {
                'scraper_version': '2.0',
                'extraction_timestamp': now.isoformat(),
                'property_count': 63
            }
        }
    ]
    
    return auctions

def create_sample_properties(auction_id: str, count: int):
    """Create sample property data"""
    now = datetime.now(timezone.utc)
    properties = []
    
    # Sample addresses in Broward County
    streets = ['Ocean Blvd', 'Las Olas Blvd', 'Sunrise Blvd', 'Commercial Blvd', 
               'Atlantic Blvd', 'Griffin Rd', 'Sheridan St', 'Hollywood Blvd',
               'Pembroke Rd', 'Stirling Rd', 'Davie Blvd', 'Broward Blvd']
    
    cities = ['Fort Lauderdale', 'Hollywood', 'Pembroke Pines', 'Miramar', 
              'Coral Springs', 'Pompano Beach', 'Davie', 'Plantation', 
              'Sunrise', 'Tamarac', 'Margate', 'Coconut Creek']
    
    companies = ['SUNSHINE INVESTMENTS LLC', 'FLORIDA REAL ESTATE HOLDINGS INC',
                 'BEACH PROPERTIES TRUST', 'COASTAL VENTURES LP',
                 'PALM TREE INVESTMENTS LLC', 'BROWARD HOLDINGS CORP',
                 'ATLANTIC REALTY GROUP INC', 'SUNRISE PROPERTIES LLC']
    
    for i in range(count):
        prop_id = f"{auction_id}_{i+1}"
        parcel = f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        street_num = random.randint(100, 9999)
        street = random.choice(streets)
        city = random.choice(cities)
        zip_code = f"33{random.randint(300,399)}"
        
        opening_bid = random.randint(5000, 500000)
        assessed_value = opening_bid * random.uniform(1.5, 3.0)
        
        # Some properties have best bids
        best_bid = None
        if random.random() > 0.7:
            best_bid = opening_bid + random.randint(100, 10000)
            
        # Random company assignment
        applicant_company = random.choice(companies) if random.random() > 0.3 else "INDIVIDUAL INVESTOR"
        
        property_data = {
            'composite_key': prop_id,
            'auction_id': auction_id,
            'item_id': str(i+1),
            'tax_deed_number': f"2025-{random.randint(1000,9999)}",
            'parcel_number': parcel,
            'parcel_url': f"https://bcpa.net/RecInfo.asp?URL_Folio={parcel.replace('-', '')}",
            'tax_certificate_number': f"2023-{random.randint(10000,99999)}",
            'legal_description': f"LOT {random.randint(1,50)} BLOCK {random.randint(1,20)} OF SUBDIVISION PLAT",
            'situs_address': f"{street_num} {street}",
            'city': city,
            'state': 'FL',
            'zip_code': zip_code,
            'homestead': random.random() > 0.8,
            'assessed_value': assessed_value,
            'soh_value': assessed_value * 0.5 if random.random() > 0.7 else None,
            'applicant': applicant_company,
            'applicant_companies': [applicant_company] if 'LLC' in applicant_company or 'INC' in applicant_company else [],
            'gis_map_url': f"https://gis.broward.org/maps/?parcel={parcel}",
            'opening_bid': opening_bid,
            'best_bid': best_bid,
            'close_time': (now + timedelta(days=7, hours=11)).isoformat() if auction_id == '110' else (now + timedelta(days=35, hours=11)).isoformat(),
            'status': random.choice(['Upcoming', 'Upcoming', 'Upcoming', 'Active', 'Canceled']),
            'sunbiz_matched': 'LLC' in applicant_company or 'INC' in applicant_company,
            'sunbiz_entity_names': [applicant_company] if ('LLC' in applicant_company or 'INC' in applicant_company) else [],
            'sunbiz_entity_ids': [f"L{random.randint(10000000000,99999999999)}"] if ('LLC' in applicant_company or 'INC' in applicant_company) else [],
            'sunbiz_data': {
                'matched': 'LLC' in applicant_company or 'INC' in applicant_company,
                'entities': [],
                'search_terms': [applicant_company] if applicant_company != "INDIVIDUAL INVESTOR" else []
            },
            'extracted_at': now.isoformat(),
            'metadata': {
                'has_parcel_link': True,
                'has_gis_map': True,
                'company_count': 1 if applicant_company != "INDIVIDUAL INVESTOR" else 0,
                'sunbiz_match_count': 1 if ('LLC' in applicant_company or 'INC' in applicant_company) else 0
            }
        }
        
        properties.append(property_data)
        
    return properties

def main():
    """Main function to populate sample data"""
    print("[INFO] Starting Tax Deed sample data population...")
    
    try:
        # Create auctions
        auctions = create_sample_auctions()
        
        for auction in auctions:
            # Insert auction
            result = client.table('tax_deed_auctions').upsert(
                auction,
                on_conflict='auction_id'
            ).execute()
            
            print(f"[OK] Created auction: {auction['description']}")
            
            # Create properties for this auction
            num_properties = 20 if auction['auction_id'] == '110' else 25
            properties = create_sample_properties(auction['auction_id'], num_properties)
            
            # Insert properties in batches
            batch_size = 10
            for i in range(0, len(properties), batch_size):
                batch = properties[i:i+batch_size]
                result = client.table('tax_deed_properties').upsert(
                    batch,
                    on_conflict='composite_key'
                ).execute()
                
            print(f"[OK] Created {len(properties)} properties for auction {auction['auction_id']}")
            
            # Create sample contacts for some properties
            for prop in properties[:5]:  # First 5 properties get contact records
                contact_data = {
                    'property_id': prop['composite_key'],  # Using composite_key as ID for simplicity
                    'composite_key': prop['composite_key'],
                    'contact_status': random.choice(['Not Contacted', 'Contacted', 'Follow Up', 'Not Interested']),
                    'owner_name': prop['applicant'],
                    'phone': f"954-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    'email': f"investor{random.randint(1,100)}@example.com" if random.random() > 0.5 else None,
                    'notes': f"Tax Deed #{prop['tax_deed_number']}\nOpening Bid: ${prop['opening_bid']:,.2f}\nHomestead: {'Yes' if prop['homestead'] else 'No'}",
                    'last_contact_date': (datetime.now(timezone.utc) - timedelta(days=random.randint(1,30))).isoformat() if random.random() > 0.5 else None
                }
                
                # Check if contact exists first
                existing = client.table('tax_deed_contacts').select('id').eq(
                    'composite_key', prop['composite_key']
                ).execute()
                
                if not existing.data:
                    client.table('tax_deed_contacts').insert(contact_data).execute()
                    
        # Create some sample alerts
        alerts = [
            {
                'alert_type': 'HIGH_VALUE_PROPERTY',
                'priority': 'HIGH',
                'title': 'High Value Property: $450,000',
                'details': '1234 Ocean Blvd, Fort Lauderdale\nTax Deed: 2025-5678',
                'auction_id': '110',
                'created_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'alert_type': 'HOMESTEAD_PROPERTY',
                'priority': 'MEDIUM',
                'title': 'Homestead Property Available',
                'details': '5678 Las Olas Blvd, Fort Lauderdale\nOpening Bid: $125,000',
                'auction_id': '110',
                'created_at': datetime.now(timezone.utc).isoformat()
            },
            {
                'alert_type': 'NEW_AUCTION',
                'priority': 'LOW',
                'title': 'New Auction Added: 10/15/2025',
                'details': '63 properties available for bidding',
                'auction_id': '111',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        client.table('tax_deed_alerts').upsert(alerts).execute()
        print(f"[OK] Created {len(alerts)} sample alerts")
        
        print("\n" + "="*60)
        print("[SUCCESS] Sample Tax Deed data populated successfully!")
        print("="*60)
        print("\nSummary:")
        print(f"- Created {len(auctions)} auctions")
        print(f"- Created {20 + 25} total properties")
        print(f"- Created sample contacts and alerts")
        print("\nYou can now test the Tax Deed Sales page at:")
        print("http://localhost:5173/tax-deed-sales")
        
    except Exception as e:
        print(f"[ERROR] Failed to populate data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()