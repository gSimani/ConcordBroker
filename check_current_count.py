"""
Check current property count in database
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
    print("CHECKING CURRENT DATABASE COUNT")
    print("="*60)
    
    # Get count
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.head(url, headers=headers)
    
    if response.status_code == 200:
        count_str = response.headers.get('content-range', '').split('/')[-1]
        if count_str.isdigit():
            count = int(count_str)
            print(f"Current properties in database: {count:,}")
            print(f"Target: 753,243 properties")
            progress = (count / 753243) * 100
            print(f"Progress: {progress:.1f}%")
        else:
            print(f"Count value: {count_str}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    main()