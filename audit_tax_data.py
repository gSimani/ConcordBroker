import os
from supabase import create_client
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

print('=' * 80)
print('DETAILED TAX DATA FIELD MAPPING')
print('=' * 80)

# Test parcel ID
test_parcel = '474131031040'

print(f'\nAnalyzing data for parcel: {test_parcel}')
print('-' * 40)

# 1. Get property tax assessment data from florida_parcels
print('\n1. PROPERTY TAX ASSESSMENT DATA (florida_parcels):')
try:
    response = supabase.table('florida_parcels').select('*').eq('parcel_id', test_parcel).execute()
    if response.data:
        prop = response.data[0]
        tax_data = {
            'Annual Tax Amount': None,  # Need to calculate or find
            'Total Amount Due': None,   # Need to find
            'Just Value': prop.get('just_value'),
            'Assessed Value': prop.get('assessed_value'),
            'Taxable Value': prop.get('taxable_value'),
            'Land Value': prop.get('land_value'),
            'Building Value': prop.get('building_value'),
            'Homestead Exemption': prop.get('homestead_exemption'),
            'Millage Rate': None,  # Need to find
            'Tax Status': None,  # Need to determine
        }
        
        for field, value in tax_data.items():
            status = 'FOUND' if value is not None else 'MISSING'
            print(f'  [{status}] {field}: {value}')
    else:
        print('  Property not found')
except Exception as e:
    print(f'  Error: {e}')

# 2. Get tax certificate data
print('\n2. TAX CERTIFICATE DATA:')
try:
    response = supabase.table('tax_certificates').select('*').eq('parcel_id', test_parcel).execute()
    if response.data:
        print(f'  Found {len(response.data)} certificates for this property')
        for i, cert in enumerate(response.data, 1):
            print(f'\n  Certificate #{i}:')
            cert_fields = {
                'Certificate Number': cert.get('certificate_number'),
                'Tax Year': cert.get('tax_year'),
                'Face Amount': cert.get('face_amount'),
                'Redemption Amount': cert.get('redemption_amount'),
                'Interest Rate': cert.get('interest_rate'),
                'Buyer Name': cert.get('buyer_name'),
                'Issued Date': cert.get('issued_date'),
                'Expiration Date': cert.get('expiration_date'),
                'Status': cert.get('status'),
                'Winning Bid %': cert.get('winning_bid_percentage'),
            }
            for field, value in cert_fields.items():
                print(f'    - {field}: {value}')
    else:
        print('  No certificates found for this property')
        # Check if any certificates exist at all
        all_certs = supabase.table('tax_certificates').select('parcel_id').limit(10).execute()
        if all_certs.data:
            parcels_with_certs = [c['parcel_id'] for c in all_certs.data]
            print(f'  Sample parcels with certificates: {parcels_with_certs[:5]}')
except Exception as e:
    print(f'  Error: {e}')

# 3. Check tax deed auction data
print('\n3. TAX DEED AUCTION DATA:')
try:
    response = supabase.table('tax_deed_auctions').select('*').limit(5).execute()
    if response.data:
        print(f'  Found {len(response.data)} auctions in database')
        print('  Auction fields:', list(response.data[0].keys()))
        
        # Check for property-specific auction
        prop_auction = supabase.table('tax_deed_auctions').select('*').eq('parcel_id', test_parcel).execute()
        if prop_auction.data:
            print(f'  Found auction for test property:')
            auction = prop_auction.data[0]
            for key, value in auction.items():
                print(f'    - {key}: {value}')
        else:
            print('  No auction found for test property')
    else:
        print('  No auctions found in database')
except Exception as e:
    if 'does not exist' in str(e):
        print('  tax_deed_auctions table does not exist')
    else:
        print(f'  Error: {e}')

# 4. Check property_sales_history for additional data
print('\n4. PROPERTY SALES HISTORY (for context):')
try:
    response = supabase.table('property_sales_history').select('*').eq('parcel_id', test_parcel).order('sale_date', desc=True).limit(3).execute()
    if response.data:
        print(f'  Found {len(response.data)} recent sales')
        for sale in response.data:
            sale_price = sale.get('sale_price')
            if sale_price:
                print(f'    - {sale.get("sale_date")}: ${sale_price:,}')
            else:
                print(f'    - {sale.get("sale_date")}: N/A')
    else:
        print('  No sales history found')
except Exception as e:
    print(f'  Error: {e}')

print('\n' + '=' * 80)
print('UI FIELD MAPPING SUMMARY')
print('=' * 80)

ui_fields = {
    'TAX ASSESSMENT SECTION': {
        'Total Amount Due': 'MISSING - Need calculation or separate tax bill table',
        'Annual Tax Amount': 'MISSING - Need tax bill data or calculation',
        'Tax Certificates Count': 'AVAILABLE - Count from tax_certificates table',
        'Property Values': 'AVAILABLE - just_value, assessed_value, taxable_value',
    },
    'TAX CERTIFICATE DETAILS': {
        'Certificate Number': 'AVAILABLE - tax_certificates.certificate_number',
        'Real Estate Account': 'AVAILABLE - tax_certificates.real_estate_account or parcel_id',
        'Tax Year': 'AVAILABLE - tax_certificates.tax_year',
        'Face Amount': 'AVAILABLE - tax_certificates.face_amount',
        'Redemption Amount': 'AVAILABLE - tax_certificates.redemption_amount',
        'Certificate Buyer': 'AVAILABLE - tax_certificates.buyer_name',
        'Interest Rate': 'AVAILABLE - tax_certificates.interest_rate',
        'Winning Bid %': 'AVAILABLE - tax_certificates.winning_bid_percentage',
        'Issued Date': 'AVAILABLE - tax_certificates.issued_date',
        'Expiration Date': 'AVAILABLE - tax_certificates.expiration_date',
        'Status': 'AVAILABLE - tax_certificates.status',
        'Advertised Number': 'AVAILABLE - tax_certificates.advertised_number',
    },
    'SUNBIZ INTEGRATION': {
        'Entity Matches': 'PARTIAL - buyer_name exists, need Sunbiz lookup',
        'Officer/Director Info': 'MISSING - Need Sunbiz API integration',
        'Entity Links': 'MISSING - Need to generate from buyer names',
    },
    'MISSING CRITICAL DATA': {
        'Annual Tax Bill Amount': 'Need separate tax_bills table or calculation',
        'Current Tax Status': 'Need to determine from payment records',
        'Tax Delinquent Flag': 'Need logic based on certificates/payments',
        'Millage Rate': 'Need county tax rate data',
        'Total Outstanding Amount': 'Need calculation from certificates + interest',
    }
}

for section, fields in ui_fields.items():
    print(f'\n{section}:')
    for field, status in fields.items():
        print(f'  - {field}: {status}')

print('\n' + '=' * 80)
print('RECOMMENDATIONS')
print('=' * 80)

print("""
1. IMMEDIATE ACTIONS:
   - Update UI to pull real tax certificate data from tax_certificates table
   - Calculate Annual Tax Amount using: taxable_value * millage_rate / 1000
   - Sum face_amount from all active certificates for Total Amount Due

2. DATA TO ADD:
   - Create tax_bills table for annual tax amounts
   - Add millage_rate to florida_parcels or create tax_rates table
   - Add tax_status field to indicate delinquent/current status

3. UI COMPONENT UPDATES NEEDED:
   - TaxAssessmentTab: Connect to florida_parcels for values
   - TaxCertificateTab: Connect to tax_certificates table
   - Add logic to calculate totals and interest accrual
   - Implement Sunbiz entity lookup for certificate buyers
""")