"""
Test that addresses appear before parcel IDs in search results
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

def test_search(query):
    """Test search with prioritized results"""
    print(f"\nTesting search for: '{query}'")
    print("-" * 60)
    
    # First get address matches
    address_url = f"{SUPABASE_URL}/rest/v1/florida_parcels?phy_addr1=ilike.*{query}*&is_redacted=eq.false&limit=5&order=taxable_value.desc"
    address_response = requests.get(address_url, headers=headers)
    
    if address_response.status_code == 200:
        address_results = address_response.json()
        print(f"\nADDRESS MATCHES ({len(address_results)} found):")
        for i, prop in enumerate(address_results, 1):
            print(f"{i}. {prop['phy_addr1']} - {prop['phy_city']}")
            print(f"   Parcel: {prop['parcel_id']}, Value: ${prop.get('taxable_value', 0):,}")
    
    # Then get parcel ID matches
    parcel_url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=ilike.*{query}*&is_redacted=eq.false&limit=5&order=taxable_value.desc"
    parcel_response = requests.get(parcel_url, headers=headers)
    
    if parcel_response.status_code == 200:
        parcel_results = parcel_response.json()
        
        # Filter out any that were already in address results
        address_ids = {r['id'] for r in address_results} if address_results else set()
        unique_parcel_results = [r for r in parcel_results if r['id'] not in address_ids]
        
        if unique_parcel_results:
            print(f"\nPARCEL ID MATCHES ({len(unique_parcel_results)} found):")
            for i, prop in enumerate(unique_parcel_results[:5], 1):
                addr = prop.get('phy_addr1', 'No address')
                city = prop.get('phy_city', 'Unknown')
                print(f"{i}. Parcel {prop['parcel_id']}")
                print(f"   Address: {addr} - {city}")
                print(f"   Value: ${prop.get('taxable_value', 0):,}")
    
    # Show combined order
    print(f"\nCOMBINED RESULTS ORDER (as they should appear):")
    print("=" * 40)
    
    all_results = []
    
    # Add address matches first
    for r in address_results[:10]:
        all_results.append(('ADDRESS', r))
    
    # Add parcel matches if we have room
    remaining = 10 - len(all_results)
    if remaining > 0 and parcel_results:
        unique_parcels = [r for r in parcel_results if r['id'] not in address_ids]
        for r in unique_parcels[:remaining]:
            all_results.append(('PARCEL', r))
    
    for i, (match_type, prop) in enumerate(all_results, 1):
        addr = prop.get('phy_addr1', 'No address')
        print(f"{i:2}. [{match_type:7}] {addr[:40]:<40} (Parcel: {prop['parcel_id']})")

def main():
    print("TESTING SEARCH PRIORITY (ADDRESSES BEFORE PARCELS)")
    print("="*70)
    
    # Test cases
    test_cases = [
        "3930",  # Should show addresses with 3930 first
        "504",   # Another numeric search
        "600",   # Common in parcel IDs
    ]
    
    for query in test_cases:
        test_search(query)
        print("\n" + "="*70)
    
    print("\nSUMMARY:")
    print("- Address matches should always appear FIRST")
    print("- Parcel ID matches should appear AFTER all address matches")
    print("- This ensures users see the most relevant results first")

if __name__ == "__main__":
    main()