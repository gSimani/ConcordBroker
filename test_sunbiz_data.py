#!/usr/bin/env python3
"""
Test Sunbiz data availability in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in environment")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_sunbiz_data():
    """Test if Sunbiz tables exist and have data"""
    
    owner_name = "SIMANI,GUY & SARAH"
    property_address = "3930 SW 53 CT"
    
    print(f"Testing Sunbiz data for owner: {owner_name}")
    print(f"   Property address: {property_address}")
    print("-" * 50)
    
    # Test 1: Check if sunbiz_corporate table exists and has data
    try:
        result = supabase.table('sunbiz_corporate').select('*').limit(5).execute()
        print(f"OK: sunbiz_corporate table exists")
        print(f"   Sample records: {len(result.data)} found")
        
        # Search for this specific owner
        search_result = supabase.table('sunbiz_corporate').select('*').ilike('entity_name', f'%SIMANI%').execute()
        print(f"   Records matching 'SIMANI': {len(search_result.data)}")
        
        if search_result.data:
            for record in search_result.data[:2]:
                print(f"     - {record.get('entity_name', 'N/A')} ({record.get('status', 'N/A')})")
    except Exception as e:
        print(f"ERROR: sunbiz_corporate table error: {str(e)}")
    
    print()
    
    # Test 2: Check if sunbiz_fictitious table exists
    try:
        result = supabase.table('sunbiz_fictitious').select('*').limit(5).execute()
        print(f"OK: sunbiz_fictitious table exists")
        print(f"   Sample records: {len(result.data)} found")
    except Exception as e:
        print(f"ERROR: sunbiz_fictitious table error: {str(e)}")
    
    print()
    
    # Test 3: Check if sunbiz_corporate_events table exists
    try:
        result = supabase.table('sunbiz_corporate_events').select('*').limit(5).execute()
        print(f"OK: sunbiz_corporate_events table exists")
        print(f"   Sample records: {len(result.data)} found")
    except Exception as e:
        print(f"ERROR: sunbiz_corporate_events table error: {str(e)}")
    
    print()
    print("=" * 50)
    print(" Summary:")
    print("-" * 50)
    
    # Test if we can find any companies at the property address
    try:
        address_search = supabase.table('sunbiz_corporate').select('*').or_(
            f"prin_addr1.ilike.%3930%,mail_addr1.ilike.%3930%"
        ).limit(5).execute()
        
        print(f"Companies at address containing '3930': {len(address_search.data)}")
        if address_search.data:
            for record in address_search.data:
                print(f"  - {record.get('entity_name', 'N/A')}")
                print(f"    Principal: {record.get('prin_addr1', 'N/A')}")
                print(f"    Mailing: {record.get('mail_addr1', 'N/A')}")
    except Exception as e:
        print(f"Address search error: {str(e)}")
    
    print()
    print(" Recommendations:")
    if len(search_result.data if 'search_result' in locals() else []) == 0:
        print("  - No Sunbiz data found for this owner")
        print("  - The component should show mock/demo data")
        print("  - Consider loading Sunbiz data from Florida's database")
    else:
        print("  - Sunbiz data exists for this owner")
        print("  - Check if the component is properly displaying it")

if __name__ == "__main__":
    test_sunbiz_data()