import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

# Check a property that has certificates
test_parcel = '064210010010'  # Property with certificate

print('=' * 80)
print(f'CHECKING PROPERTY WITH TAX CERTIFICATE: {test_parcel}')
print('=' * 80)

# Get certificate details
response = supabase.table('tax_certificates').select('*').eq('parcel_id', test_parcel).execute()

if response.data:
    cert = response.data[0]
    print('\nCertificate Details:')
    for key, value in cert.items():
        print(f'  {key}: {value}')
        
# Get property details
prop_response = supabase.table('florida_parcels').select('*').eq('parcel_id', test_parcel).limit(1).execute()

if prop_response.data:
    prop = prop_response.data[0]
    print('\nProperty Details:')
    print(f'  Address: {prop.get("phy_addr1")}, {prop.get("phy_city")}')
    print(f'  Owner: {prop.get("owner_name")}')
    print(f'  Taxable Value: ${prop.get("taxable_value", 0):,.2f}' if prop.get("taxable_value") else '  Taxable Value: N/A')