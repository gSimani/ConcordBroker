import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

print('=' * 80)
print('SEARCHING FOR MILLAGE RATE AND TAX BILL FIELDS')
print('=' * 80)

# Get ALL columns from florida_parcels
response = supabase.table('florida_parcels').select('*').limit(1).execute()
if response.data:
    all_columns = list(response.data[0].keys())
    
    print(f'\nTotal columns in florida_parcels: {len(all_columns)}')
    print('\nSearching for tax-related fields...')
    print('-' * 40)
    
    # Search for millage/mill rate fields
    print('\n1. MILLAGE/MILL RATE FIELDS:')
    millage_fields = [col for col in all_columns if 'mill' in col.lower() or 'rate' in col.lower()]
    if millage_fields:
        for field in millage_fields:
            value = response.data[0].get(field)
            print(f'  FOUND: {field} = {value}')
    else:
        print('  No millage/rate fields found')
    
    # Search for tax bill/amount fields  
    print('\n2. TAX BILL/AMOUNT FIELDS:')
    tax_bill_fields = [col for col in all_columns if any(term in col.lower() for term in ['tax', 'bill', 'amount', 'due', 'levy', 'payment'])]
    if tax_bill_fields:
        for field in tax_bill_fields:
            value = response.data[0].get(field)
            print(f'  FOUND: {field} = {value}')
    else:
        print('  No tax bill fields found')
    
    # Search for assessment fields
    print('\n3. ASSESSMENT FIELDS:')
    assessment_fields = [col for col in all_columns if 'assess' in col.lower() or 'apprais' in col.lower()]
    if assessment_fields:
        for field in assessment_fields:
            value = response.data[0].get(field)
            print(f'  FOUND: {field} = {value}')
    else:
        print('  No assessment fields found')
        
    # Search for exemption fields
    print('\n4. EXEMPTION FIELDS:')
    exemption_fields = [col for col in all_columns if 'exempt' in col.lower() or 'homestead' in col.lower()]
    if exemption_fields:
        for field in exemption_fields:
            value = response.data[0].get(field)
            print(f'  FOUND: {field} = {value}')
    else:
        print('  No exemption fields found')

# Get a property with known values to test calculations
print('\n' + '=' * 80)
print('TESTING PROPERTY WITH KNOWN VALUES')
print('=' * 80)

test_parcel = '474131031040'
response = supabase.table('florida_parcels').select('*').eq('parcel_id', test_parcel).execute()

if response.data:
    prop = response.data[0]
    print(f'\nProperty: {test_parcel}')
    print(f'Address: {prop.get("phy_addr1")}, {prop.get("phy_city")}')
    print('\nVALUES:')
    
    just_val = prop.get("just_value")
    assessed_val = prop.get("assessed_value")
    taxable_val = prop.get("taxable_value")
    land_val = prop.get("land_value")
    building_val = prop.get("building_value")
    
    if just_val:
        print(f'  Just Value: ${just_val:,}')
    else:
        print('  Just Value: None')
        
    if assessed_val:
        print(f'  Assessed Value: ${assessed_val:,}')
    else:
        print('  Assessed Value: None')
        
    if taxable_val:
        print(f'  Taxable Value: ${taxable_val:,}')
    else:
        print('  Taxable Value: None')
        
    if land_val:
        print(f'  Land Value: ${land_val:,}')
    else:
        print('  Land Value: None')
        
    if building_val:
        print(f'  Building Value: ${building_val:,}')
    else:
        print('  Building Value: None')
    
    # Check for any tax amount fields
    print('\nOTHER TAX-RELATED FIELDS:')
    found_tax_fields = False
    for key, value in prop.items():
        if value and any(term in key.lower() for term in ['tax', 'mill', 'rate', 'levy', 'amount', 'bill']):
            if key not in ['taxable_value']:
                print(f'  {key}: {value}')
                found_tax_fields = True
    
    if not found_tax_fields:
        print('  No additional tax fields found')

# List ALL columns for manual inspection
print('\n' + '=' * 80)
print('ALL COLUMNS IN FLORIDA_PARCELS (for manual inspection):')
print('=' * 80)
if response.data and all_columns:
    # Group columns alphabetically
    all_columns.sort()
    for i in range(0, len(all_columns), 3):
        cols = all_columns[i:i+3]
        line = '  '
        for col in cols:
            line += f'{col:25} | '
        print(line.rstrip(' |'))

# CALCULATE ESTIMATED TAX
print('\n' + '=' * 80)
print('TAX CALCULATION')
print('=' * 80)

if response.data:
    taxable_value = prop.get('taxable_value', 0)
    
    # Broward County 2024 average millage rates
    print('\nUsing Broward County 2024 Average Millage Rates:')
    print('  County: 5.4669 mills')
    print('  School: 6.2430 mills')
    print('  Municipal: ~3.5 mills (varies by city)')
    print('  Special Districts: ~4.5 mills')
    print('  TOTAL: ~19.7099 mills (0.0197099)')
    
    millage_rate = 0.0197099  # Total millage rate for Broward
    
    if taxable_value:
        annual_tax = taxable_value * millage_rate
        print(f'\nCALCULATED ANNUAL TAX:')
        print(f'  Taxable Value: ${taxable_value:,.2f}')
        print(f'  Millage Rate: {millage_rate * 1000:.4f} mills')
        print(f'  Annual Tax: ${annual_tax:,.2f}')
        
        # Monthly payment
        monthly = annual_tax / 12
        print(f'  Monthly: ${monthly:,.2f}')
    else:
        print('\nNo taxable value found - cannot calculate tax')