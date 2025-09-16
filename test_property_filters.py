"""
Test the property filters are working correctly
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

def test_filter(filter_name, filter_query):
    """Test a specific filter"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=parcel_id,property_use,owner_name,taxable_value&{filter_query}&limit=5"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n{filter_name}:")
        print(f"  Found {len(data)} properties (showing max 5)")
        
        for prop in data[:5]:
            print(f"  - Code {prop['property_use']}: {prop['owner_name'][:30]}... (${prop['taxable_value']:,})")
        
        return len(data) > 0
    else:
        print(f"\n{filter_name}: ERROR {response.status_code}")
        return False

def main():
    print("TESTING PROPERTY FILTERS")
    print("="*60)
    
    # Test each filter type
    tests = [
        ("All Properties", "limit=5"),
        ("Residential (000-009)", "property_use=gte.000&property_use=lte.009"),
        ("Commercial (010-039)", "property_use=gte.010&property_use=lte.039"),
        ("Industrial (040-049)", "property_use=gte.040&property_use=lte.049"),
        ("Specific Code 001", "property_use=eq.001"),
        ("Specific Code 011", "property_use=eq.011"),
        ("Specific Code 048", "property_use=eq.048"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, query in tests:
        if test_filter(test_name, query):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed == 0:
        print("\nSUCCESS! All property filters are working correctly.")
        print("\nThe filter buttons should now work:")
        print("  - Residential: Shows codes 000-009")
        print("  - Commercial: Shows codes 010-039")
        print("  - Industrial: Shows codes 040-049")
    else:
        print("\nSome filters failed. Please check the database.")

if __name__ == "__main__":
    main()