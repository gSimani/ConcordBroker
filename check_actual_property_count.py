import os
import requests
from dotenv import load_dotenv

load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

print('CHECKING ACTUAL PROPERTY COUNTS IN DATABASE')
print('=' * 60)

# Check florida_parcels table with a simpler approach
url = f'{SUPABASE_URL}/rest/v1/florida_parcels?select=*&limit=1'
headers['Prefer'] = 'count=exact,head=true'
response = requests.get(url, headers=headers)

if response.status_code in [200, 206]:
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        count = content_range.split('/')[-1]
        if count == '*':
            # Try a different approach
            url = f'{SUPABASE_URL}/rest/v1/florida_parcels?select=count(*)'
            del headers['Prefer']
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    count = data[0].get('count', 'unknown')
        print(f'florida_parcels table: {count} records')
    else:
        print(f'florida_parcels table: unable to get count')
else:
    print(f'Error checking florida_parcels: {response.status_code}')

# Check properties table  
url = f'{SUPABASE_URL}/rest/v1/properties?select=*&limit=1'
headers['Prefer'] = 'count=exact,head=true'
response = requests.get(url, headers=headers)

if response.status_code in [200, 206]:
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        count = content_range.split('/')[-1]
        if count == '*':
            # Try a different approach
            url = f'{SUPABASE_URL}/rest/v1/properties?select=count(*)'
            del headers['Prefer']
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    count = data[0].get('count', 'unknown')
        print(f'properties table: {count} records')
    else:
        print(f'properties table: unable to get count')
else:
    print(f'Error checking properties: {response.status_code}')

# Check broward_parcels table (if it exists)
url = f'{SUPABASE_URL}/rest/v1/broward_parcels?select=*&limit=1'
headers['Prefer'] = 'count=exact,head=true'
response = requests.get(url, headers=headers)

if response.status_code in [200, 206]:
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        count = content_range.split('/')[-1]
        print(f'broward_parcels table: {count} records')
    else:
        print(f'broward_parcels table: unable to get count')
elif response.status_code == 404:
    print(f'broward_parcels table: does not exist')
else:
    print(f'Error checking broward_parcels: {response.status_code}')

print('\n' + '=' * 60)
print('These are the actual counts in the database.')
print('The UI should be updated to reflect the correct count.')