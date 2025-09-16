"""
Debug Supabase connection and table structure
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Anon Key: {SUPABASE_ANON_KEY[:20]}...")

# Headers for API requests
headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

def check_table_structure():
    """Check the table structure"""
    print("\n=== TABLE STRUCTURE DEBUG ===")
    
    # Try to get table info via OpenAPI
    url = f"{SUPABASE_URL}/rest/v1/"
    try:
        response = requests.get(url, headers=headers)
        print(f"API Root Response: {response.status_code}")
        if response.status_code == 200:
            print("API is accessible")
        else:
            print(f"API Error: {response.text}")
    except Exception as e:
        print(f"API Error: {e}")
    
    # Try to select with no filters to see RLS behavior
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*&limit=1"
    try:
        response = requests.get(url, headers=headers)
        print(f"\nTable Query Response: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Data returned: {len(data)} rows")
            if data:
                print("Sample row keys:", list(data[0].keys()))
        
    except Exception as e:
        print(f"Query Error: {e}")

def check_rls_policies():
    """Try to understand RLS policies"""
    print("\n=== RLS POLICY DEBUG ===")
    
    # Try different queries to understand RLS behavior
    test_queries = [
        "?select=count",
        "?select=*&limit=1", 
        "?select=parcel_id&limit=1",
        "?select=*&is_redacted=eq.false&limit=1"
    ]
    
    for query in test_queries:
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels{query}"
        try:
            response = requests.get(url, headers=headers)
            print(f"Query: {query}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")

def test_minimal_insert():
    """Try inserting minimal data"""
    print("\n=== MINIMAL INSERT TEST ===")
    
    # Simplest possible property
    minimal_property = {
        'parcel_id': 'TEST-123',
        'county': 'BROWARD',
        'year': 2025,
        'is_redacted': False
    }
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    try:
        response = requests.post(url, json=[minimal_property], headers=headers)
        print(f"Insert Status: {response.status_code}")
        print(f"Insert Response: {response.text}")
        
        if response.status_code not in [200, 201]:
            print("Insert failed - checking detailed error...")
            
            # Try to understand the specific error
            if "42501" in response.text:
                print("RLS Policy blocking insert")
            elif "23502" in response.text:
                print("NOT NULL constraint violation")
            elif "23505" in response.text:
                print("UNIQUE constraint violation")
            
    except Exception as e:
        print(f"Insert Error: {e}")

def main():
    print("SUPABASE DEBUG SESSION")
    print("=" * 50)
    
    check_table_structure()
    check_rls_policies()
    test_minimal_insert()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check output above for issues.")

if __name__ == "__main__":
    main()