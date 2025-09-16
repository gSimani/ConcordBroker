"""
Populate tax deed data - using only existing columns
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
        'University Drive', 'State Road 7', 'Flamingo Road', 'Hiatus Road'
    ]
    
    cities = [
        'Fort Lauderdale', 'Hollywood', 'Pompano Beach', 'Coral Springs',
        'Sunrise', 'Plantation', 'Davie', 'Deerfield Beach',
        'Miramar', 'Pembroke Pines', 'Weston', 'Tamarac'
    ]
    
    zip_codes = ['33301', '33304', '33305', '33306', '33308', '33309', '33311', '33312']
    
    number = random.randint(100, 9999)
    street = random.choice(streets)
    city = random.choice(cities)
    zip_code = random.choice(zip_codes)
    
    return f"{number} {street}, {city}, FL {zip_code}"

def create_tax_deed_properties():
    """Create realistic tax deed properties"""
    properties = []
    
    # Base tax deed numbers from actual auction data
    base_numbers = [51640, 53487, 53540, 53541, 53542, 53543, 53544, 53546, 53547, 53548,
                   53549, 53550, 53552, 53559, 53563, 53564, 53566, 53575, 53577, 53579]
    
    # Create Active/Upcoming properties (for 9/17/2025 auction)
    for i in range(30):
        if i < len(base_numbers):
            td_number = f"TD-{base_numbers[i]}"
        else:
            td_number = f"TD-{54000 + i}"
        
        # Generate parcel ID
        parcel_id = f"{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(1000,9999):04d}"
        
        # Generate values
        assessed_value = random.randint(50000, 500000)
        opening_bid = random.randint(5000, 150000)
        
        prop = {
            'tax_deed_number': td_number,
            'parcel_id': parcel_id,
            'tax_certificate_number': f"TC-{random.randint(100000, 999999)}",
            'legal_situs_address': generate_broward_address(),
            'homestead_exemption': 'Y' if random.random() < 0.3 else 'N',
            'assessed_value': float(assessed_value),
            'soh_value': float(int(assessed_value * 0.9)),
            'opening_bid': float(opening_bid),
            'item_status': 'Active',
            'applicant_name': 'TAX CERTIFICATE HOLDER',
            'tax_years_included': '2021-2024',
            'total_taxes_owed': float(random.randint(3000, 20000)),
            'property_appraisal_url': f'https://bcpa.broward.org/property/{parcel_id}',
            'auction_id': 1,  # Use a simple valid auction_id
            'close_time': (datetime.now() + timedelta(days=7, hours=11 + (i % 4), minutes=(i % 6) * 10)).isoformat(),
            'total_bids': 0,
            'unique_bidders': 0
        }
        
        # Some should be cancelled
        if random.random() < 0.15:
            prop['item_status'] = 'Cancelled'
            prop['close_time'] = datetime.now().isoformat()  # Cancelled items still need valid timestamp
        
        properties.append(prop)
    
    # Create Sold properties (past auctions)
    sold_count = 50
    for i in range(sold_count):
        td_number = f"TD-{52000 + i}"
        parcel_id = f"{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(1000,9999):04d}"
        
        assessed_value = random.randint(75000, 750000)
        opening_bid = random.randint(10000, 200000)
        winning_bid = opening_bid * random.uniform(1.1, 2.5)
        
        prop = {
            'tax_deed_number': td_number,
            'parcel_id': parcel_id,
            'tax_certificate_number': f"TC-{random.randint(100000, 999999)}",
            'legal_situs_address': generate_broward_address(),
            'homestead_exemption': 'N',
            'assessed_value': float(assessed_value),
            'soh_value': float(int(assessed_value * 0.85)),
            'opening_bid': float(opening_bid),
            'winning_bid': float(winning_bid),
            'current_bid': float(winning_bid),
            'item_status': 'Sold',
            'applicant_name': random.choice([
                f"INVESTMENT GROUP {chr(65+random.randint(0,25))} LLC",
                f"REAL ESTATE HOLDINGS {random.randint(100,999)}",
                f"{random.choice(['John', 'Mary', 'Robert', 'Jennifer'])} {random.choice(['Smith', 'Johnson', 'Williams'])}",
                "PROPERTY ACQUISITION FUND",
                f"SUNSHINE INVESTMENTS {chr(65+random.randint(0,25))}"
            ]),  # Use applicant_name for winner since winner_name column doesn't exist
            'tax_years_included': '2020-2023',
            'total_taxes_owed': float(random.randint(5000, 30000)),
            'property_appraisal_url': f'https://bcpa.broward.org/property/{parcel_id}',
            'auction_id': 1 + (i % 3),  # Use simple valid auction_ids (1, 2, 3)
            'close_time': (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
            'total_bids': random.randint(5, 25),
            'unique_bidders': random.randint(2, 12)
        }
        
        properties.append(prop)
    
    return properties

def main():
    print("Populating Tax Deed Data - Final Version")
    print("="*60)
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check existing data first
        print("Checking existing data...")
        existing = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
        existing_count = len(existing.data) if existing.data else 0
        print(f"Found {existing_count} existing properties")
        
        if existing_count > 70:
            print("Sufficient data already exists. Skipping population.")
            return
        
        # Clear if very little data
        if existing_count < 10:
            print("Clearing sparse existing data...")
            try:
                supabase.table('tax_deed_bidding_items').delete().neq('id', 0).execute()
            except:
                pass
        
        # Create properties
        properties = create_tax_deed_properties()
        
        print(f"\nCreated {len(properties)} properties to insert")
        
        # Count by status
        status_counts = {}
        for prop in properties:
            status = prop['item_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nProperties by status:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        # Insert properties
        print("\nInserting properties...")
        success_count = 0
        failed_count = 0
        
        for i, prop in enumerate(properties):
            try:
                # Remove any fields that might not exist in the table
                safe_prop = {k: v for k, v in prop.items() if k not in ['auction_name']}
                
                response = supabase.table('tax_deed_bidding_items').insert(safe_prop).execute()
                success_count += 1
                
                # Show progress
                if success_count <= 5 or success_count % 10 == 0:
                    print(f"  [{success_count}] Added {prop['tax_deed_number']}: {prop['legal_situs_address'][:40]}...")
                    
            except Exception as e:
                failed_count += 1
                if failed_count <= 3:  # Only show first few errors
                    print(f"  Error: {str(e)[:100]}")
        
        print(f"\nResults:")
        print(f"  Successfully added: {success_count} properties")
        print(f"  Failed: {failed_count} properties")
        
        # Verify final count
        print("\nVerifying database...")
        final = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
        total = len(final.data) if final.data else 0
        print(f"Total properties now in database: {total}")
        
        # Show samples
        if final.data and len(final.data) > 0:
            print("\nSample properties in database:")
            for item in final.data[:5]:
                status = item.get('item_status', 'Unknown')
                bid = item.get('opening_bid', 0)
                address = item.get('legal_situs_address', 'No address')[:50]
                print(f"  - {item['tax_deed_number']}: ${bid:,.2f} ({status})")
                print(f"    {address}...")
        
        print("\n" + "="*60)
        print("COMPLETE!")
        print("\nTo view the tax deed sales:")
        print("1. Go to http://localhost:5173/tax-deed-sales")
        print("2. Refresh the page (Ctrl+F5)")
        print("3. Check the tabs:")
        print(f"   - Upcoming: Active properties")
        print(f"   - Past: Sold properties")
        print(f"   - Cancelled: Cancelled properties")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()