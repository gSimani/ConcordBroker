"""
Populate tax deed data with realistic Broward County properties
Based on the actual auction data structure from the website
"""
from datetime import datetime, timedelta
from supabase import create_client, Client
import random

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def generate_broward_address():
    """Generate realistic Broward County addresses"""
    streets = [
        'Ocean Boulevard', 'Las Olas Boulevard', 'Federal Highway', 'Sunrise Boulevard',
        'Commercial Boulevard', 'Atlantic Boulevard', 'Broward Boulevard', 'Griffin Road',
        'Sheridan Street', 'Hollywood Boulevard', 'Pembroke Road', 'Pines Boulevard',
        'University Drive', 'State Road 7', 'Flamingo Road', 'Hiatus Road',
        'Palm Avenue', 'Dixie Highway', 'Andrews Avenue', 'Powerline Road',
        'Nob Hill Road', 'Lyons Road', 'Coral Ridge Drive', 'Bayview Drive',
        'Riverside Drive', 'Victoria Park Road', 'Davie Road', 'Pine Island Road'
    ]
    
    cities = [
        'Fort Lauderdale', 'Hollywood', 'Pompano Beach', 'Coral Springs',
        'Sunrise', 'Plantation', 'Davie', 'Deerfield Beach',
        'Miramar', 'Pembroke Pines', 'Weston', 'Tamarac',
        'Margate', 'Coconut Creek', 'Lauderhill', 'Oakland Park',
        'Hallandale Beach', 'Lighthouse Point', 'Cooper City', 'Dania Beach'
    ]
    
    zip_codes = [
        '33301', '33304', '33305', '33306', '33308', '33309', '33311', '33312',
        '33313', '33314', '33315', '33316', '33317', '33319', '33321', '33322',
        '33323', '33324', '33325', '33326', '33327', '33328', '33330', '33331'
    ]
    
    number = random.randint(100, 9999)
    street = random.choice(streets)
    city = random.choice(cities)
    zip_code = random.choice(zip_codes)
    
    return f"{number} {street}, {city}, FL {zip_code}"

def create_tax_deed_properties():
    """Create realistic tax deed properties based on actual auction data"""
    properties = []
    
    # Generate properties for different auctions
    auctions = [
        {'date': '9/17/2025', 'count': 46, 'status': 'Active', 'days_away': 7},
        {'date': '10/15/2025', 'count': 63, 'status': 'Active', 'days_away': 35},
        {'date': '8/20/2025', 'count': 31, 'status': 'Sold', 'days_away': -21},
        {'date': '7/23/2025', 'count': 42, 'status': 'Sold', 'days_away': -49},
        {'date': '6/25/2025', 'count': 38, 'status': 'Sold', 'days_away': -77},
        {'date': '5/21/2025', 'count': 45, 'status': 'Sold', 'days_away': -112},
        {'date': '4/16/2025', 'count': 51, 'status': 'Sold', 'days_away': -147},
    ]
    
    # Base tax deed numbers from actual data
    base_numbers = [51640, 53487, 53540, 53541, 53542, 53543, 53544, 53546, 53547, 53548,
                   53549, 53550, 53552, 53559, 53563, 53564, 53566, 53575, 53577, 53579,
                   53580, 53581, 53583, 53588, 53589, 53590, 53591, 53592, 53593, 53597]
    
    property_id = 1
    
    for auction in auctions:
        # Calculate how many properties to create for this auction
        # Create a subset to avoid too much data
        num_properties = min(auction['count'], 15)  # Limit to 15 per auction
        
        for i in range(num_properties):
            # Generate tax deed number
            if property_id <= len(base_numbers):
                td_number = f"TD-{base_numbers[property_id-1]}"
            else:
                td_number = f"TD-{54000 + property_id}"
            
            # Generate parcel ID (Broward format)
            parcel_id = f"{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(1000,9999):04d}"
            
            # Generate property values
            assessed_value = random.randint(50000, 500000)
            soh_value = int(assessed_value * random.uniform(0.8, 1.2))
            
            # Calculate opening bid (typically includes back taxes, fees, etc.)
            tax_years = random.randint(2, 5)
            annual_tax = assessed_value * 0.02  # Approx 2% property tax
            opening_bid = annual_tax * tax_years + random.randint(1000, 5000)  # Plus fees
            
            # Create property record
            prop = {
                'tax_deed_number': td_number,
                'parcel_id': parcel_id,
                'tax_certificate_number': f"TC-{random.randint(100000, 999999)}",
                'legal_situs_address': generate_broward_address(),
                'homestead_exemption': 'Y' if random.random() < 0.3 else 'N',
                'assessed_value': float(assessed_value),
                'soh_value': float(soh_value),
                'opening_bid': float(opening_bid),
                'item_status': auction['status'],
                'auction_name': f"{auction['date']} Tax Deed Sale",
                'applicant_name': 'TAX CERTIFICATE HOLDER',
                'tax_years_included': f"{2025-tax_years}-2024",
                'total_taxes_owed': float(annual_tax * tax_years),
                'property_appraisal_url': f'https://bcpa.broward.org/property/{parcel_id}',
                'auction_id': 110 - auctions.index(auction),  # Auction IDs from actual site
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Set close time based on auction date
            if auction['status'] == 'Active':
                # Future auction
                close_date = datetime.now() + timedelta(days=auction['days_away'])
                # Auctions typically run from 9 AM to 3 PM
                hour = 11 + (i % 6)  # Spread throughout the day
                minute = random.choice([0, 1, 2, 3, 4, 5]) * 10
                prop['close_time'] = f"{hour:02d}:{minute:02d} AM" if hour < 12 else f"{hour-12:02d}:{minute:02d} PM"
                prop['current_bid'] = None
                prop['total_bids'] = 0
                prop['unique_bidders'] = 0
                
                # Some properties might be cancelled
                if random.random() < 0.2:  # 20% cancelled
                    prop['item_status'] = 'Cancelled'
                    prop['close_time'] = '-'
                    
            else:
                # Past auction (sold)
                close_date = datetime.now() + timedelta(days=auction['days_away'])
                prop['close_time'] = close_date.isoformat()
                
                # Add winning bid information
                winning_bid = opening_bid * random.uniform(1.1, 2.5)
                prop['winning_bid'] = float(winning_bid)
                prop['current_bid'] = float(winning_bid)
                
                # Generate winner name
                winner_types = [
                    f"{random.choice(['PRIME', 'ELITE', 'PREMIER', 'CAPITAL', 'VENTURE'])} REAL ESTATE {chr(65+random.randint(0,25))} LLC",
                    f"{random.choice(['SUNSHINE', 'ATLANTIC', 'COASTAL', 'PALM', 'TROPICAL'])} INVESTMENTS GROUP",
                    f"{random.choice(['John', 'Mary', 'Robert', 'Jennifer', 'Michael', 'Patricia'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'])}",
                    f"{chr(65+random.randint(0,25))}{''.join([chr(65+random.randint(0,25)) for _ in range(2)])} HOLDINGS LLC",
                    "PROPERTY ACQUISITION FUND"
                ]
                prop['winner_name'] = random.choice(winner_types)
                
                # Bidding activity
                prop['total_bids'] = random.randint(5, 30)
                prop['unique_bidders'] = random.randint(2, min(15, prop['total_bids']))
            
            properties.append(prop)
            property_id += 1
    
    return properties

def main():
    print("Populating Tax Deed Auction Data")
    print("="*60)
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Create properties
        properties = create_tax_deed_properties()
        
        print(f"Created {len(properties)} properties")
        
        # Count by status
        status_counts = {}
        for prop in properties:
            status = prop['item_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nProperties by status:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        # Clear existing data first (optional)
        print("\nClearing existing data...")
        try:
            # Delete all existing records
            supabase.table('tax_deed_bidding_items').delete().neq('id', 0).execute()
        except:
            pass  # Table might be empty
        
        # Insert properties
        print("\nInserting properties...")
        success_count = 0
        
        for i, prop in enumerate(properties):
            try:
                response = supabase.table('tax_deed_bidding_items').insert(prop).execute()
                success_count += 1
                if i < 5 or i % 10 == 0:  # Show first 5 and every 10th
                    print(f"  Added {prop['tax_deed_number']}: {prop['legal_situs_address'][:50]}... ({prop['item_status']})")
            except Exception as e:
                print(f"  Error adding {prop['tax_deed_number']}: {str(e)[:50]}")
        
        print(f"\nSuccessfully added {success_count} properties!")
        
        # Verify data
        print("\nVerifying data in database...")
        response = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
        total = len(response.data) if response.data else 0
        print(f"Total properties in database: {total}")
        
        # Show sample data
        if response.data:
            print("\nSample properties:")
            for item in response.data[:3]:
                print(f"  - {item['tax_deed_number']}: {item['legal_situs_address'][:40]}...")
                print(f"    Status: {item['item_status']}, Opening Bid: ${item['opening_bid']:,.2f}")
        
        print("\n" + "="*60)
        print("SUCCESS! Tax deed data has been populated.")
        print("\nTo view the data on your website:")
        print("1. Open http://localhost:5173/tax-deed-sales")
        print("2. Refresh the page (Ctrl+F5)")
        print("3. You should see:")
        print(f"   - Upcoming tab: {status_counts.get('Active', 0)} active properties")
        print(f"   - Past tab: {status_counts.get('Sold', 0)} sold properties")
        print(f"   - Cancelled tab: {status_counts.get('Cancelled', 0)} cancelled properties")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()