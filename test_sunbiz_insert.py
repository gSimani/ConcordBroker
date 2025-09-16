#!/usr/bin/env python3
"""
Test inserting single Sunbiz record to identify the field causing issues
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
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print('TESTING SUNBIZ INSERT')
print('=' * 60)

# Minimal test record with shortened values
test_record = {
    'doc_number': 'L10123456',  # 9 chars
    'entity_name': 'SIMANI LLC',  # Short name
    'status': 'ACTIVE',
    'filing_date': '2010-06-15',
    'state_country': 'FL',  # 2 chars
    'prin_addr1': '3930 SW 53 CT',
    'prin_city': 'HOLLYWOOD',
    'prin_state': 'FL',
    'prin_zip': '33314',  # 5 chars
    'mail_addr1': '3930 SW 53 CT',
    'mail_city': 'HOLLYWOOD', 
    'mail_state': 'FL',
    'mail_zip': '33314',
    'ein': '27-1234567',  # 10 chars
    'registered_agent': 'GUY SIMANI',  # Short name
    'file_type': 'LLC',  # 3 chars
    'subtype': 'LLC'  # 3 chars
}

# Try inserting test record
try:
    url = f'{SUPABASE_URL}/rest/v1/sunbiz_corporate'
    
    # First check if RLS is blocking us - try a simple select
    print("Testing table access...")
    check_response = requests.get(url + '?limit=1', headers=headers)
    if check_response.status_code == 401:
        print("X Row Level Security is blocking access")
        print("  Need to disable RLS or use service role key")
    else:
        print("OK Table is accessible")
    
    print("\nInserting test record...")
    print(f"  doc_number length: {len(test_record['doc_number'])}")
    print(f"  entity_name length: {len(test_record['entity_name'])}")
    print(f"  state_country length: {len(test_record.get('state_country', ''))}")
    print(f"  ein length: {len(test_record.get('ein', ''))}")
    print(f"  registered_agent length: {len(test_record.get('registered_agent', ''))}")
    
    response = requests.post(url, json=[test_record], headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print('OK Successfully inserted test record!')
    else:
        print(f'X Failed to insert: {response.status_code}')
        error_detail = response.json() if response.text else response.text
        
        # Parse error to find which field is too long
        if 'value too long' in str(error_detail):
            print('ERROR: Field value too long')
            print(f'Full error: {error_detail}')
            
            # Check which field might be the issue
            print('\nChecking field lengths:')
            for key, value in test_record.items():
                if value:
                    print(f'  {key}: {len(str(value))} chars - "{value}"')
        else:
            print(f'Error details: {error_detail}')
            
except Exception as e:
    print(f'Exception: {e}')

print('\n' + '=' * 60)
print('TEST COMPLETE')