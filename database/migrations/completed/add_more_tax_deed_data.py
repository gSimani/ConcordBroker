"""
Add more tax deed auction data to Supabase
"""
from datetime import datetime, timedelta
from supabase import create_client, Client
import random

# Use the frontend Supabase instance
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def create_properties():
    """Create a variety of tax deed properties"""
    properties = []
    
    # Upcoming/Active properties
    addresses = [
        "1234 Ocean Boulevard, Fort Lauderdale, FL 33301",
        "5678 Sunrise Avenue, Sunrise, FL 33323", 
        "910 Commercial Way, Pompano Beach, FL 33062",
        "2345 Palm Street, Coral Springs, FL 33071",
        "6789 Atlantic Drive, Plantation, FL 33324"
    ]
    
    for i, address in enumerate(addresses):
        prop = {
            'tax_deed_number': f'TD-2025-{i+10:03d}',
            'parcel_id': f'06421001{i+10:04d}',
            'tax_certificate_number': f'TC-2023-{54321+i}',
            'legal_situs_address': address,
            'homestead_exemption': 'Y' if i % 3 == 0 else 'N',
            'assessed_value': float(random.randint(250000, 750000)),
            'soh_value': float(random.randint(200000, 700000)),
            'opening_bid': float(random.randint(50000, 250000)),
            'current_bid': float(random.randint(55000, 280000)) if i % 2 == 0 else None,
            'close_time': (datetime.now() + timedelta(days=random.randint(5, 30))).isoformat(),
            'item_status': 'Active',
            'total_bids': random.randint(0, 15),
            'unique_bidders': random.randint(0, 8),
            'applicant_name': f'{"INVESTOR GROUP " + chr(65+i) + " LLC" if i % 2 == 0 else "John Smith"}',
            'tax_years_included': f'{2020+i%3}-{2022+i%3}',
            'total_taxes_owed': float(random.randint(5000, 25000)),
            'property_appraisal_url': f'https://bcpa.broward.org/property/06421001{i+10:04d}',
            'auction_id': random.randint(1, 3)
        }
        properties.append(prop)
    
    # Past/Sold properties
    sold_addresses = [
        "999 Bayshore Drive, Fort Lauderdale, FL 33304",
        "888 Las Olas Boulevard, Fort Lauderdale, FL 33301",
        "777 Federal Highway, Pompano Beach, FL 33062"
    ]
    
    for i, address in enumerate(sold_addresses):
        prop = {
            'tax_deed_number': f'TD-2024-{i+201:03d}',
            'parcel_id': f'38421005{i+20:04d}',
            'tax_certificate_number': f'TC-2022-{98765+i}',
            'legal_situs_address': address,
            'homestead_exemption': 'N',
            'assessed_value': float(random.randint(450000, 1200000)),
            'soh_value': float(random.randint(400000, 1100000)),
            'opening_bid': float(random.randint(150000, 400000)),
            'winning_bid': float(random.randint(200000, 500000)),
            'winner_name': f'PRIME REAL ESTATE {chr(65+i)} LLC',
            'close_time': (datetime.now() - timedelta(days=random.randint(30, 90))).isoformat(),
            'item_status': 'Sold',
            'total_bids': random.randint(10, 30),
            'unique_bidders': random.randint(5, 15),
            'applicant_name': 'TAX CERTIFICATE HOLDER',
            'tax_years_included': '2019-2021',
            'total_taxes_owed': float(random.randint(15000, 45000)),
            'property_appraisal_url': f'https://bcpa.broward.org/property/38421005{i+20:04d}',
            'auction_id': random.randint(1, 3)
        }
        properties.append(prop)
    
    # Cancelled properties
    cancelled_addresses = [
        "1001 Industrial Way, Sunrise, FL 33323",
        "2002 Warehouse Boulevard, Pompano Beach, FL 33069"
    ]
    
    for i, address in enumerate(cancelled_addresses):
        prop = {
            'tax_deed_number': f'TD-2025-{i+301:03d}',
            'parcel_id': f'51421009{i+30:04d}',
            'tax_certificate_number': f'TC-2023-{33333+i}',
            'legal_situs_address': address,
            'homestead_exemption': 'N',
            'assessed_value': float(random.randint(150000, 400000)),
            'soh_value': float(random.randint(140000, 380000)),
            'opening_bid': float(random.randint(40000, 120000)),
            'close_time': (datetime.now() - timedelta(days=random.randint(5, 20))).isoformat(),
            'item_status': 'Cancelled',
            'total_bids': 0,
            'unique_bidders': 0,
            'applicant_name': 'TAX CERTIFICATE HOLDER',
            'tax_years_included': '2020-2022',
            'total_taxes_owed': float(random.randint(8000, 20000)),
            'property_appraisal_url': f'https://bcpa.broward.org/property/51421009{i+30:04d}',
            'auction_id': random.randint(1, 3)
        }
        properties.append(prop)
    
    return properties

def main():
    print("Adding Tax Deed Auction Data to Supabase")
    print("=" * 60)
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Create properties
        properties = create_properties()
        
        print(f"Adding {len(properties)} properties:")
        print(f"  - Active: {len([p for p in properties if p['item_status'] == 'Active'])}")
        print(f"  - Sold: {len([p for p in properties if p['item_status'] == 'Sold'])}")
        print(f"  - Cancelled: {len([p for p in properties if p['item_status'] == 'Cancelled'])}")
        
        # Insert properties one by one to avoid conflicts
        success_count = 0
        for prop in properties:
            try:
                # Try to insert
                response = supabase.table('tax_deed_bidding_items').insert(prop).execute()
                print(f"  Added: {prop['tax_deed_number']} - {prop['legal_situs_address'][:40]}... ({prop['item_status']})")
                success_count += 1
            except Exception as e:
                # If insert fails, try update
                try:
                    response = supabase.table('tax_deed_bidding_items').upsert(
                        prop,
                        on_conflict='tax_deed_number'
                    ).execute()
                    print(f"  Updated: {prop['tax_deed_number']} ({prop['item_status']})")
                    success_count += 1
                except:
                    print(f"  Failed: {prop['tax_deed_number']} - {str(e)[:50]}")
        
        print(f"\nSuccessfully added/updated {success_count} properties!")
        
        # Verify total count
        count_response = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
        total = len(count_response.data) if count_response.data else 0
        print(f"Total properties now in database: {total}")
        
        print("\n" + "="*60)
        print("SUCCESS! Data has been added to Supabase.")
        print("\nTo see the data on your website:")
        print("1. Open http://localhost:5173/tax-deed-sales")
        print("2. Refresh the page (Ctrl+F5)")
        print("3. You should see:")
        print("   - Upcoming tab: Active properties")
        print("   - Past tab: Sold properties")
        print("   - Cancelled tab: Cancelled properties")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()