"""
Check if tax deed data exists in Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

print("Checking Tax Deed Data in Supabase")
print("=" * 60)
print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY[:50]}..." if SUPABASE_KEY else "KEY: None")
print("=" * 60)

try:
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check if table exists and get data
    response = supabase.table('tax_deed_properties_with_contacts').select('*').execute()
    
    if response.data:
        print(f"\nFound {len(response.data)} properties in database:")
        
        # Count by status
        status_counts = {}
        for prop in response.data:
            status = prop.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nProperties by status:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        # Show first 3 properties
        print("\nFirst 3 properties:")
        for i, prop in enumerate(response.data[:3], 1):
            print(f"\n{i}. {prop.get('tax_deed_number', 'N/A')}")
            print(f"   Address: {prop.get('situs_address', 'N/A')}")
            print(f"   Status: {prop.get('status', 'N/A')}")
            print(f"   Opening Bid: ${prop.get('opening_bid', 0):,.0f}")
    else:
        print("\nNo data found in tax_deed_properties_with_contacts table")
        print("\nTrying to insert sample data...")
        
        # Insert one test property
        test_property = {
            'composite_key': 'TD-TEST-001_123456789',
            'tax_deed_number': 'TD-TEST-001',
            'parcel_number': '123456789',
            'situs_address': '123 Test Street, Fort Lauderdale, FL 33301',
            'city': 'Fort Lauderdale',
            'state': 'FL',
            'zip_code': '33301',
            'opening_bid': 150000,
            'status': 'Active',
            'applicant': 'Test Applicant LLC',
            'homestead': False,
            'auction_date': '2025-02-15',
            'auction_description': 'February 2025 Tax Deed Sale'
        }
        
        insert_response = supabase.table('tax_deed_properties_with_contacts').upsert(
            test_property,
            on_conflict='composite_key'
        ).execute()
        
        if insert_response.data:
            print("Successfully inserted test property!")
        else:
            print("Failed to insert test property")
            
except Exception as e:
    print(f"\nError: {e}")
    print("\nPossible issues:")
    print("1. Table 'tax_deed_properties_with_contacts' might not exist")
    print("2. Invalid API credentials")
    print("3. Network/connection issues")
    
    # Try to determine the specific issue
    if 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
        print("\n=> Table does not exist. Create it using the SQL script.")
    elif 'Invalid API key' in str(e):
        print("\n=> API key is invalid. Check your .env file.")
    elif '401' in str(e):
        print("\n=> Authentication failed. Check Supabase credentials.")