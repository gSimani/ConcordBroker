"""
Check the actual schema of florida_parcels table
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

def main():
    print("CHECKING DATABASE SCHEMA")
    print("="*60)
    
    # Get one record to see the structure
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?limit=1"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            print("Available columns in florida_parcels table:")
            print()
            for key in sorted(data[0].keys()):
                value = data[0][key]
                value_type = type(value).__name__ if value is not None else "null"
                print(f"  {key}: {value_type}")
        else:
            print("No data found in table")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()