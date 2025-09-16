import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

# Query for the specific property the user is viewing
parcel_id = '474135040890'  # The property from the UI

print('=' * 80)
print(f'TAX CERTIFICATE DATA FOR PARCEL: {parcel_id}')
print('=' * 80)

# Get tax certificates for this property
try:
    response = supabase.table('tax_certificates').select('*').eq('parcel_id', parcel_id).execute()
    
    if response.data:
        print(f'\nFound {len(response.data)} tax certificate(s) for this property')
        
        for i, cert in enumerate(response.data, 1):
            print(f'\n--- Certificate #{i} ---')
            print(f'Certificate Number: {cert.get("certificate_number")}')
            print(f'Tax Year: {cert.get("tax_year")}')
            print(f'Face Amount: ${cert.get("face_amount", 0):,.2f}')
            print(f'Redemption Amount: ${cert.get("redemption_amount", 0):,.2f}')
            print(f'Interest Rate: {cert.get("interest_rate")}%')
            print(f'Buyer Name: {cert.get("buyer_name")}')
            print(f'Issued Date: {cert.get("issued_date")}')
            print(f'Expiration Date: {cert.get("expiration_date")}')
            print(f'Status: {cert.get("status")}')
            print(f'Winning Bid %: {cert.get("winning_bid_percentage")}')
            
        # Export to JSON for UI integration
        with open('tax_certificate_data.json', 'w') as f:
            json.dump(response.data, f, indent=2, default=str)
        print('\nData exported to tax_certificate_data.json')
            
    else:
        print('\nNo tax certificates found for this property')
        
        # Check if there are ANY certificates in the database
        print('\nChecking for any tax certificates in database...')
        all_certs = supabase.table('tax_certificates').select('parcel_id, certificate_number, face_amount').limit(5).execute()
        
        if all_certs.data:
            print(f'Found {len(all_certs.data)} certificates in database:')
            for cert in all_certs.data:
                print(f'  - Parcel: {cert["parcel_id"]}, Cert: {cert["certificate_number"]}, Amount: ${cert.get("face_amount", 0):,.2f}')
        else:
            print('No tax certificates found in the entire database')
            
except Exception as e:
    print(f'Error querying tax certificates: {e}')

# Also check florida_parcels for tax values
print('\n' + '=' * 80)
print('PROPERTY TAX VALUES')
print('=' * 80)

try:
    response = supabase.table('florida_parcels').select('just_value, assessed_value, taxable_value, land_value, building_value').eq('parcel_id', parcel_id).execute()
    
    if response.data:
        prop = response.data[0]
        print(f'\nProperty values for {parcel_id}:')
        just_val = prop.get("just_value", 0) or 0
        assessed_val = prop.get("assessed_value", 0) or 0
        taxable_val = prop.get("taxable_value", 0) or 0
        land_val = prop.get("land_value", 0) or 0
        building_val = prop.get("building_value", 0) or 0
        
        print(f'Just Value: ${just_val:,.2f}')
        print(f'Assessed Value: ${assessed_val:,.2f}')
        print(f'Taxable Value: ${taxable_val:,.2f}')
        print(f'Land Value: ${land_val:,.2f}')
        print(f'Building Value: ${building_val:,.2f}')
        
        # Calculate annual tax
        taxable_value = prop.get("taxable_value", 0)
        if taxable_value:
            millage_rate = 0.0197099  # Broward County average
            annual_tax = taxable_value * millage_rate
            print(f'\nCalculated Annual Tax: ${annual_tax:,.2f}')
            print(f'(Using Broward County avg millage rate: {millage_rate * 1000:.4f} mills)')
            
except Exception as e:
    print(f'Error querying property values: {e}')