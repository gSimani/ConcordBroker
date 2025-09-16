"""
Test searching for properties with address containing '3930'
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

def search_properties(query):
    """Search for properties matching the query"""
    # Search in address field
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?phy_addr1=ilike.*{query}*&limit=10&select=parcel_id,phy_addr1,phy_city,owner_name,taxable_value"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []

def main():
    print("SEARCHING FOR PROPERTIES WITH '3930' IN ADDRESS")
    print("="*60)
    
    # Search for '3930'
    results = search_properties('3930')
    
    if results:
        print(f"Found {len(results)} properties with '3930' in address:\n")
        for prop in results:
            print(f"Parcel ID: {prop['parcel_id']}")
            print(f"Address:   {prop['phy_addr1']}")
            print(f"City:      {prop['phy_city']}")
            print(f"Owner:     {prop['owner_name'][:50]}..." if len(prop['owner_name']) > 50 else f"Owner:     {prop['owner_name']}")
            print(f"Value:     ${prop['taxable_value']:,}")
            print("-" * 40)
    else:
        print("No properties found with '3930' in address")
        
    # Also try searching by parcel ID
    print("\n" + "="*60)
    print("SEARCHING FOR PARCEL IDS CONTAINING '3930'")
    print("="*60)
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=ilike.*3930*&limit=10&select=parcel_id,phy_addr1,phy_city,owner_name,taxable_value"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"Found {len(results)} properties with '3930' in parcel ID:\n")
            for prop in results:
                print(f"Parcel ID: {prop['parcel_id']}")
                print(f"Address:   {prop['phy_addr1'] or 'N/A'}")
                print(f"City:      {prop['phy_city'] or 'N/A'}")
                print(f"Owner:     {prop['owner_name'][:50]}..." if prop['owner_name'] and len(prop['owner_name']) > 50 else f"Owner:     {prop['owner_name'] or 'N/A'}")
                print(f"Value:     ${prop['taxable_value']:,}" if prop['taxable_value'] else "Value:     N/A")
                print("-" * 40)
        else:
            print("No properties found with '3930' in parcel ID")
    
    # Check total count of properties with addresses
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count&phy_addr1=not.is.null"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        count_with_address = len(response.json())
        print(f"Properties with addresses: {count_with_address}")
    
    # Get a sample of addresses
    print("\nSample addresses in database:")
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=phy_addr1&phy_addr1=not.is.null&limit=10"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        samples = response.json()
        for i, prop in enumerate(samples, 1):
            print(f"  {i}. {prop['phy_addr1']}")

if __name__ == "__main__":
    main()