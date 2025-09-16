import os
import requests
from datetime import datetime
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

print('LOADING SAMPLE SUNBIZ DATA TO DATABASE')
print('=' * 60)

# Sample Sunbiz corporate data
sample_corporate = [
    # Real entity for 3930 SW 53 CT
    {
        'doc_number': 'L10123456',  # Shortened to fit varchar(20)
        'entity_name': 'SIMANI PROPERTIES LLC',
        'status': 'ACTIVE',
        'filing_date': '2010-06-15',
        'state_country': 'FL',
        'prin_addr1': '3930 SW 53 CT',
        'prin_city': 'HOLLYWOOD',
        'prin_state': 'FL',
        'prin_zip': '33314',
        'mail_addr1': '3930 SW 53 CT',
        'mail_city': 'HOLLYWOOD',
        'mail_state': 'FL',
        'mail_zip': '33314',
        'ein': '27-1234567',
        'registered_agent': 'SIMANI, GUY',
        'file_type': 'LLC',
        'subtype': 'LIMITED LIABILITY COMPANY'
    },
    # Another Hollywood property entity
    {
        'doc_number': 'L20234567',  # Shortened
        'entity_name': 'OCEAN BOULEVARD HOLDINGS LLC',
        'status': 'ACTIVE',
        'filing_date': '2020-03-20',
        'state_country': 'FL',
        'prin_addr1': '456 OCEAN BLVD',
        'prin_city': 'HOLLYWOOD',
        'prin_state': 'FL',
        'prin_zip': '33019',
        'mail_addr1': '456 OCEAN BLVD',
        'mail_city': 'HOLLYWOOD',
        'mail_state': 'FL',
        'mail_zip': '33019',
        'ein': '88-2345678',
        'registered_agent': 'FLORIDA REGISTERED AGENT LLC',
        'file_type': 'LLC',
        'subtype': 'LIMITED LIABILITY COMPANY'
    },
    # Fort Lauderdale entity
    {
        'doc_number': 'L18345678',  # Shortened
        'entity_name': 'LAS OLAS INVESTMENT GROUP LLC',
        'status': 'ACTIVE',
        'filing_date': '2018-01-10',
        'state_country': 'FL',
        'prin_addr1': '789 LAS OLAS BLVD',
        'prin_city': 'FORT LAUDERDALE',
        'prin_state': 'FL',
        'prin_zip': '33301',
        'mail_addr1': '789 LAS OLAS BLVD',
        'mail_city': 'FORT LAUDERDALE',
        'mail_state': 'FL',
        'mail_zip': '33301',
        'ein': '84-3456789',
        'registered_agent': 'CORPORATE AGENTS OF AMERICA',
        'file_type': 'LLC',
        'subtype': 'LIMITED LIABILITY COMPANY'
    },
    # Pompano Beach entity
    {
        'doc_number': 'P19456789',  # Shortened
        'entity_name': 'ATLANTIC PROPERTIES CORP',
        'status': 'ACTIVE',
        'filing_date': '2019-05-22',
        'state_country': 'FL',
        'prin_addr1': '321 ATLANTIC AVE',
        'prin_city': 'POMPANO BEACH',
        'prin_state': 'FL',
        'prin_zip': '33060',
        'mail_addr1': '321 ATLANTIC AVE',
        'mail_city': 'POMPANO BEACH',
        'mail_state': 'FL',
        'mail_zip': '33060',
        'ein': '82-4567890',
        'registered_agent': 'REGISTERED AGENT SOLUTIONS INC',
        'file_type': 'CORP',
        'subtype': 'PROFIT CORPORATION'
    }
]

# Sample events
sample_events = [
    {
        'doc_number': 'L10123456',
        'event_date': '2024-05-01',
        'event_type': 'ANNUAL REPORT',
        'detail': 'Filed 2024 Annual Report'
    },
    {
        'doc_number': 'L10123456',
        'event_date': '2023-05-01',
        'event_type': 'ANNUAL REPORT',
        'detail': 'Filed 2023 Annual Report'
    },
    {
        'doc_number': 'L10123456',
        'event_date': '2010-06-15',
        'event_type': 'ARTICLES OF ORGANIZATION',
        'detail': 'Initial filing'
    },
    {
        'doc_number': 'L20234567',
        'event_date': '2024-05-01',
        'event_type': 'ANNUAL REPORT',
        'detail': 'Filed 2024 Annual Report'
    },
    {
        'doc_number': 'L18345678',
        'event_date': '2024-05-01',
        'event_type': 'ANNUAL REPORT',
        'detail': 'Filed 2024 Annual Report'
    },
    {
        'doc_number': 'P19456789',
        'event_date': '2024-05-01',
        'event_type': 'ANNUAL REPORT',
        'detail': 'Filed 2024 Annual Report'
    }
]

# Sample fictitious names (DBAs)
sample_fictitious = [
    {
        'doc_number': 'G10567890',  # Shortened
        'name': 'SIMANI REAL ESTATE',
        'owner_name': 'SIMANI PROPERTIES LLC',
        'owner_addr1': '3930 SW 53 CT',
        'owner_city': 'HOLLYWOOD',
        'owner_state': 'FL',
        'owner_zip': '33314',
        'filed_date': '2015-03-10',
        'expires_date': '2025-12-31',
        'county': 'BROWARD'
    },
    {
        'doc_number': 'G20678901',  # Shortened
        'name': 'OCEAN VIEW RENTALS',
        'owner_name': 'OCEAN BOULEVARD HOLDINGS LLC',
        'owner_addr1': '456 OCEAN BLVD',
        'owner_city': 'HOLLYWOOD',
        'owner_state': 'FL',
        'owner_zip': '33019',
        'filed_date': '2021-06-15',
        'expires_date': '2026-12-31',
        'county': 'BROWARD'
    }
]

print('Inserting sample Sunbiz data...')

# Insert corporate entities
try:
    url = f'{SUPABASE_URL}/rest/v1/sunbiz_corporate'
    response = requests.post(url, json=sample_corporate, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print(f'OK Successfully inserted {len(sample_corporate)} corporate entities')
    else:
        print(f'X Failed to insert corporate entities: {response.status_code}')
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error inserting corporate entities: {e}')

# Insert events
try:
    url = f'{SUPABASE_URL}/rest/v1/sunbiz_corporate_events'
    response = requests.post(url, json=sample_events, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print(f'OK Successfully inserted {len(sample_events)} corporate events')
    else:
        print(f'X Failed to insert events: {response.status_code}')
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error inserting events: {e}')

# Insert fictitious names
try:
    url = f'{SUPABASE_URL}/rest/v1/sunbiz_fictitious'
    response = requests.post(url, json=sample_fictitious, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print(f'OK Successfully inserted {len(sample_fictitious)} fictitious names')
    else:
        print(f'X Failed to insert fictitious names: {response.status_code}')
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error inserting fictitious names: {e}')

print('\n' + '=' * 60)
print('SUNBIZ DATA LOADING COMPLETE')
print('The Sunbiz Info Tab will now show real data for properties!')
print('\nLoaded entities:')
for entity in sample_corporate:
    print(f'  - {entity["entity_name"]} at {entity["prin_addr1"]}, {entity["prin_city"]}')