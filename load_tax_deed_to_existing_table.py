"""
Load tax deed data to the existing tax_deed_auctions table
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
import random

# Use the frontend Supabase instance
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def check_existing_table():
    """Check what tax deed related tables exist"""
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Try different table names
    tables_to_try = [
        'tax_deed_auctions',
        'tax_deed_properties',
        'tax_deed_bidding_items',
        'tax_certificates'
    ]
    
    existing_tables = []
    for table in tables_to_try:
        try:
            response = supabase.table(table).select('*').limit(1).execute()
            existing_tables.append(table)
            print(f"Found table: {table}")
            
            # Get column info if possible
            if response.data and len(response.data) > 0:
                print(f"  Columns: {', '.join(response.data[0].keys())[:100]}...")
        except Exception as e:
            if 'Could not find the table' not in str(e):
                print(f"Table {table}: {str(e)[:50]}")
    
    return existing_tables

def create_auction_data():
    """Create sample auction data"""
    auctions = []
    
    # Create a few auction events
    auction_dates = [
        ('2025-02-15', 'February 2025 Tax Deed Sale', 'upcoming'),
        ('2024-12-15', 'December 2024 Tax Deed Sale', 'past'),
        ('2025-01-15', 'January 2025 Tax Deed Sale', 'cancelled')
    ]
    
    for i, (date, description, status) in enumerate(auction_dates):
        auction = {
            'auction_id': f'AUCTION-{date[:7]}',
            'auction_date': date,
            'description': description,
            'status': status,
            'location': 'Broward County Courthouse',
            'created_at': datetime.now().isoformat()
        }
        auctions.append(auction)
    
    return auctions

def create_bidding_items():
    """Create sample bidding items (properties)"""
    items = []
    
    # Upcoming properties
    for i in range(5):
        item = {
            'item_id': f'TD-2025-{i+1:03d}',
            'auction_id': 'AUCTION-2025-02',
            'parcel_id': f'06421001{i:04d}',
            'tax_deed_number': f'TD-2025-{i+1:03d}',
            'legal_description': f'LOT {i+1} BLOCK {i+2} BROWARD ESTATES',
            'property_address': f'{100+i*10} Main Street, Fort Lauderdale, FL 33301',
            'opening_bid': random.randint(75000, 350000),
            'current_bid': random.randint(80000, 380000) if i % 2 == 0 else None,
            'item_status': 'Active',
            'homestead': i % 3 == 0,
            'assessed_value': random.randint(250000, 950000),
            'applicant_name': f'INVESTOR GROUP {chr(65+i)} LLC' if i % 2 == 0 else f'John Doe {i+1}',
            'created_at': datetime.now().isoformat()
        }
        items.append(item)
    
    # Past/Sold properties
    for i in range(3):
        item = {
            'item_id': f'TD-2024-{i+101:03d}',
            'auction_id': 'AUCTION-2024-12',
            'parcel_id': f'38421005{i:04d}',
            'tax_deed_number': f'TD-2024-{i+101:03d}',
            'legal_description': f'UNIT {105+i} WATERFRONT CONDOS',
            'property_address': f'{999+i*2} Bayshore Drive, Fort Lauderdale, FL 33304',
            'opening_bid': random.randint(175000, 450000),
            'winning_bid': random.randint(250000, 600000),
            'winner_name': f'COASTAL INVESTMENTS {chr(65+i)} LLC',
            'item_status': 'Sold',
            'homestead': False,
            'assessed_value': random.randint(450000, 1200000),
            'applicant_name': f'TAX CERTIFICATE HOLDER',
            'created_at': datetime.now().isoformat()
        }
        items.append(item)
    
    # Cancelled properties
    for i in range(2):
        item = {
            'item_id': f'TD-2025-{i+201:03d}',
            'auction_id': 'AUCTION-2025-01',
            'parcel_id': f'51421009{i:04d}',
            'tax_deed_number': f'TD-2025-{i+201:03d}',
            'legal_description': 'VACANT LOT SUNRISE INDUSTRIAL',
            'property_address': f'{1001+i*10} Industrial Way, Sunrise, FL 33323',
            'opening_bid': random.randint(45000, 125000),
            'item_status': 'Cancelled',
            'homestead': False,
            'assessed_value': random.randint(150000, 400000),
            'applicant_name': 'TAX CERTIFICATE HOLDER',
            'created_at': datetime.now().isoformat()
        }
        items.append(item)
    
    return items

def main():
    print("Tax Deed Data Loader - Using Existing Tables")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print("=" * 60)
    
    try:
        # Check what tables exist
        print("\nChecking existing tables...")
        existing_tables = check_existing_table()
        
        if not existing_tables:
            print("\nNo tax deed related tables found!")
            return
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Load data based on available tables
        if 'tax_deed_auctions' in existing_tables:
            print("\nLoading auction data...")
            auctions = create_auction_data()
            
            # Clear existing sample data
            try:
                supabase.table('tax_deed_auctions').delete().neq('auction_id', '').execute()
            except:
                pass
            
            # Insert new data
            for auction in auctions:
                try:
                    response = supabase.table('tax_deed_auctions').upsert(
                        auction,
                        on_conflict='auction_id'
                    ).execute()
                    print(f"  Inserted auction: {auction['description']}")
                except Exception as e:
                    print(f"  Failed: {e}")
        
        if 'tax_deed_bidding_items' in existing_tables:
            print("\nLoading property/bidding items...")
            items = create_bidding_items()
            
            # Clear existing sample data
            try:
                supabase.table('tax_deed_bidding_items').delete().neq('item_id', '').execute()
            except:
                pass
            
            # Insert new data
            for item in items:
                try:
                    response = supabase.table('tax_deed_bidding_items').upsert(
                        item,
                        on_conflict='item_id'
                    ).execute()
                    print(f"  Inserted: {item['tax_deed_number']} - {item['item_status']}")
                except Exception as e:
                    # Try without on_conflict
                    try:
                        response = supabase.table('tax_deed_bidding_items').insert(item).execute()
                        print(f"  Inserted: {item['tax_deed_number']} - {item['item_status']}")
                    except:
                        print(f"  Failed {item['tax_deed_number']}: {str(e)[:50]}")
        
        print("\n" + "="*60)
        print("Data loading complete!")
        print("\nNext Steps:")
        print("1. Open http://localhost:5173/tax-deed-sales")
        print("2. The page should now display the loaded data")
        print("3. Check the browser console for any errors")
        print("\nNote: The component may need to be updated to use")
        print("the correct table names (tax_deed_bidding_items)")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()