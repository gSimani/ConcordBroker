import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('.env.mcp')

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print('Error: Missing Supabase credentials')
    exit(1)

print(f'Connecting to: {url}')

# Use the REST API directly to get tables
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

# Try to list tables by making requests to common table names
possible_tables = [
    'florida_parcels', 'properties', 'property_appraiser', 'property_data',
    'parcels', 'real_estate', 'tax_deed', 'sales', 'owners', 'assessments',
    'florida_properties', 'broward_properties', 'property_records',
    'property_info', 'property_details', 'property_listings'
]

print('\n' + '='*60)
print('Checking for existing tables...')
print('='*60)

existing_tables = []

for table_name in possible_tables:
    try:
        # Try to query each table with limit=1
        table_url = f'{url}/rest/v1/{table_name}?limit=1'
        resp = requests.get(table_url, headers=headers)

        if resp.status_code == 200:
            print(f'[FOUND] {table_name}')
            existing_tables.append(table_name)

            # Get count
            count_url = f'{url}/rest/v1/{table_name}?select=*&limit=1'
            count_headers = headers.copy()
            count_headers['Prefer'] = 'count=exact'
            count_resp = requests.head(count_url, headers=count_headers)

            if 'content-range' in count_resp.headers:
                content_range = count_resp.headers['content-range']
                # Parse the count from content-range header
                if '/' in content_range:
                    count = content_range.split('/')[-1]
                    if count != '*':
                        print(f'  Records: {count}')
        elif resp.status_code == 404:
            # Table doesn't exist - skip quietly
            pass
        else:
            print(f'[ERROR] {table_name}: Status {resp.status_code}')

    except Exception as e:
        print(f'[ERROR] {table_name}: {str(e)[:50]}')

# Save results
results = {
    'tables_checked': possible_tables,
    'tables_found': existing_tables,
    'database_url': url
}

with open('database_tables_found.json', 'w') as f:
    json.dump(results, f, indent=2)

print('\n' + '='*60)
print(f'SUMMARY: Found {len(existing_tables)} tables')
print('='*60)

if not existing_tables:
    print('\nNo standard property tables found.')
    print('The database appears to be empty or using different table names.')
    print('\nPossible reasons:')
    print('1. Tables have not been created yet')
    print('2. Using a different schema (not public)')
    print('3. Different naming convention')
    print('4. RLS policies blocking access')
