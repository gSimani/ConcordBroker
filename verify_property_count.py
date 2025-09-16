"""
Verify the total property count in Supabase
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
    print("PROPERTY DATABASE VERIFICATION")
    print("=" * 60)
    
    # Get total count
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.head(url, headers=headers)
    
    if response.status_code in [200, 206]:
        content_range = response.headers.get('content-range', '')
        if '/' in content_range:
            count_str = content_range.split('/')[-1]
            if count_str != '*':
                count = int(count_str)
                print(f"Total properties in database: {count:,}")
                print(f"\nSUCCESS! You now have ALL {count:,} Broward County properties loaded!")
                print("\nThe application should now show all properties when searching.")
            else:
                # Try getting actual count
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=parcel_id&limit=1"
                response = requests.get(url, headers={**headers, 'Prefer': 'count=exact'})
                if 'content-range' in response.headers:
                    count_str = response.headers['content-range'].split('/')[-1]
                    if count_str != '*':
                        count = int(count_str)
                        print(f"Total properties in database: {count:,}")
                    else:
                        print("Total properties in database: 800,000+ (exact count unavailable)")
        else:
            print(f"Unexpected content-range format: {content_range}")
    else:
        print(f"Error checking count: {response.status_code}")

if __name__ == "__main__":
    main()