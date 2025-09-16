"""
Test Sunbiz Integration with Supabase

This script tests the Sunbiz data integration to ensure data is properly
flowing from Supabase to the frontend Sunbiz tab.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_ANON_KEY", "")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

def test_sunbiz_data_for_property():
    """Test fetching Sunbiz data for a specific property"""
    
    # Test property information (from property 064210010010)
    test_cases = [
        {
            "owner_name": "LAUDERDALE BY THE SEA LLC",
            "address": "4445 EL MAR DR",
            "city": "LAUDERDALE BY THE SEA"
        },
        {
            "owner_name": "LAUDERDALE",  # Partial match
            "address": "4445",  # Partial address
            "city": "LAUDERDALE"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test['owner_name']}")
        print(f"{'='*60}")
        
        # Search for corporate entities by owner name
        print(f"\n1. Searching corporate entities by owner name: '{test['owner_name']}'")
        corporate_by_name = supabase.table('sunbiz_corporate').select('*').or_(
            f"entity_name.ilike.%{test['owner_name']}%,registered_agent.ilike.%{test['owner_name']}%"
        ).eq('status', 'ACTIVE').order('filing_date', desc=True).limit(10).execute()
        
        print(f"   Found {len(corporate_by_name.data)} corporate entities by name")
        for entity in corporate_by_name.data[:3]:  # Show first 3
            print(f"   - {entity.get('entity_name')} ({entity.get('doc_number')})")
        
        # Search by address
        print(f"\n2. Searching corporate entities by address: '{test['address']}'")
        corporate_by_address = supabase.table('sunbiz_corporate').select('*').or_(
            f"prin_addr1.ilike.%{test['address']}%,mail_addr1.ilike.%{test['address']}%"
        ).limit(10).execute()
        
        print(f"   Found {len(corporate_by_address.data)} corporate entities by address")
        for entity in corporate_by_address.data[:3]:
            print(f"   - {entity.get('entity_name')} at {entity.get('prin_addr1')}")
        
        # Search fictitious names
        print(f"\n3. Searching fictitious names (DBAs) by owner: '{test['owner_name']}'")
        fictitious = supabase.table('sunbiz_fictitious').select('*').or_(
            f"owner_name.ilike.%{test['owner_name']}%,name.ilike.%{test['owner_name']}%"
        ).order('filed_date', desc=True).limit(10).execute()
        
        print(f"   Found {len(fictitious.data)} fictitious names")
        for dba in fictitious.data[:3]:
            print(f"   - {dba.get('name')} owned by {dba.get('owner_name')}")
        
        # Get events for first corporate entity if found
        if corporate_by_name.data:
            doc_number = corporate_by_name.data[0].get('doc_number')
            print(f"\n4. Fetching events for document {doc_number}")
            events = supabase.table('sunbiz_corporate_events').select('*').eq(
                'doc_number', doc_number
            ).order('event_date', desc=True).execute()
            
            print(f"   Found {len(events.data)} events")
            for event in events.data[:3]:
                print(f"   - {event.get('event_type')} on {event.get('event_date')}")

def test_sunbiz_tables_structure():
    """Test that Sunbiz tables exist and have the expected structure"""
    
    print("\n" + "="*60)
    print("Testing Sunbiz Table Structure")
    print("="*60)
    
    tables = [
        'sunbiz_corporate',
        'sunbiz_corporate_events', 
        'sunbiz_fictitious',
        'sunbiz_partnerships',
        'sunbiz_liens'
    ]
    
    for table in tables:
        try:
            # Try to fetch one record to verify table exists and is accessible
            result = supabase.table(table).select('*').limit(1).execute()
            print(f"✓ {table}: Accessible (has {len(result.data)} test record)")
            
            if result.data:
                # Show available columns
                columns = list(result.data[0].keys())
                print(f"  Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
        except Exception as e:
            print(f"✗ {table}: Error - {str(e)}")

def test_sample_sunbiz_data():
    """Show sample data from Sunbiz tables"""
    
    print("\n" + "="*60)
    print("Sample Sunbiz Data")
    print("="*60)
    
    # Get sample active corporations
    print("\n1. Sample Active Corporations:")
    active_corps = supabase.table('sunbiz_corporate').select('*').eq(
        'status', 'ACTIVE'
    ).limit(5).execute()
    
    for corp in active_corps.data:
        print(f"   - {corp.get('entity_name')}")
        print(f"     Doc: {corp.get('doc_number')}, Filed: {corp.get('filing_date')}")
        print(f"     Address: {corp.get('prin_addr1')}, {corp.get('prin_city')}")
    
    # Get sample fictitious names
    print("\n2. Sample Fictitious Names (DBAs):")
    dbas = supabase.table('sunbiz_fictitious').select('*').limit(5).execute()
    
    for dba in dbas.data:
        print(f"   - {dba.get('name')}")
        print(f"     Owner: {dba.get('owner_name')}")
        print(f"     County: {dba.get('county')}, Filed: {dba.get('filed_date')}")

if __name__ == "__main__":
    print("Testing Sunbiz Integration with Supabase")
    print("="*60)
    
    # Test table structure
    test_sunbiz_tables_structure()
    
    # Test sample data
    test_sample_sunbiz_data()
    
    # Test specific property data
    test_sunbiz_data_for_property()
    
    print("\n" + "="*60)
    print("Sunbiz Integration Test Complete")
    print("="*60)
    print("\nTo view the Sunbiz tab in the browser:")
    print("1. Navigate to http://localhost:5173/property/064210010010")
    print("2. Click on the 'Sunbiz Info' tab")
    print("3. Check browser console for debug logs")