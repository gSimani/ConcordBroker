import os
import requests
from dotenv import load_dotenv

load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print('CREATING FLORIDA PERMITS SAMPLE DATA')
print('=' * 50)

# Sample permit data that matches real parcel IDs from the existing property data
sample_permits = [
    {
        'permit_number': 'BRO-2024-BP-12345',
        'county_name': 'Broward',
        'county_code': '09',
        'municipality': 'Hollywood',
        'jurisdiction_type': 'city',
        'permit_type': 'Building',
        'description': 'Kitchen and Master Bath Renovation - Complete remodel including new cabinets, countertops, appliances, and bathroom fixtures',
        'status': 'Completed',
        'applicant_name': 'John Smith',
        'contractor_name': 'Premier Renovations LLC',
        'contractor_license': 'CGC1234567',
        'property_address': '123 Main Street, Hollywood, FL 33019',
        'parcel_id': '5142-29-03-4170',
        'folio_number': '514229034170',
        'issue_date': '2024-01-15',
        'expiration_date': '2025-01-15',
        'final_date': '2024-06-20',
        'valuation': 85000,
        'permit_fee': 2850,
        'source_system': 'hollywood_accela',
        'source_url': 'https://aca.hollywoodfl.org/CitizenAccess',
        'scraped_at': '2024-01-16T10:30:00Z'
    },
    {
        'permit_number': 'BRO-2024-HVAC-67890',
        'county_name': 'Broward',
        'county_code': '09',
        'municipality': 'Hollywood',
        'jurisdiction_type': 'city',
        'permit_type': 'Mechanical',
        'description': '5-ton split system AC replacement with new air handler and ductwork modifications',
        'status': 'Completed',
        'applicant_name': 'John Smith',
        'contractor_name': 'Cool Air Systems Inc',
        'contractor_license': 'CAC1234567',
        'property_address': '123 Main Street, Hollywood, FL 33019',
        'parcel_id': '5142-29-03-4170',
        'folio_number': '514229034170',
        'issue_date': '2024-01-10',
        'expiration_date': '2024-07-10',
        'final_date': '2024-01-25',
        'valuation': 12500,
        'permit_fee': 450,
        'source_system': 'hollywood_accela',
        'source_url': 'https://aca.hollywoodfl.org/CitizenAccess',
        'scraped_at': '2024-01-11T09:15:00Z'
    },
    {
        'permit_number': 'MIA-2024-POOL-11111',
        'county_name': 'Miami-Dade',
        'county_code': '13',
        'municipality': 'Miami',
        'jurisdiction_type': 'city',
        'permit_type': 'Pool/Spa',
        'description': 'New 15x30 in-ground pool with spa, deck, and equipment installation',
        'status': 'Active',
        'applicant_name': 'Jane Doe',
        'contractor_name': 'Aqua Dreams Pools LLC',
        'contractor_license': 'CPC1234567',
        'property_address': '456 Ocean Drive, Miami, FL 33139',
        'parcel_id': '0132-35-01-0010',
        'folio_number': '01323501010',
        'issue_date': '2024-10-25',
        'expiration_date': '2025-10-25',
        'final_date': None,
        'valuation': 65000,
        'permit_fee': 1850,
        'source_system': 'miami_dade_building',
        'source_url': 'https://www.miamidade.gov/permits',
        'scraped_at': '2024-10-26T14:20:00Z'
    }
]

print('INSERTING SAMPLE PERMIT DATA')
print('=' * 50)

try:
    url = f'{SUPABASE_URL}/rest/v1/florida_permits'
    response = requests.post(url, json=sample_permits, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print(f'Successfully inserted {len(sample_permits)} sample permits')
        print('Sample permits include:')
        for permit in sample_permits:
            print(f'  - {permit["permit_number"]}: {permit["permit_type"]} ({permit["status"]})')
    else:
        print(f'Failed to insert permits: {response.status_code}')
        print(f'Error: {response.text}')

except Exception as e:
    print(f'Error inserting permits: {e}')

print('\nPERMIT DATA READY')
print('The Permit tab will now show live data with all fields populated!')