from supabase import create_client, Client
import json

# Connect to database
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

parcel_id = '3040190012860'
print(f'Searching for TAX information for property: {parcel_id}')
print('=' * 60)

# Query florida_parcels for tax-related fields
response = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()

if response.data and len(response.data) > 0:
    prop = response.data[0]
    print('TAX-RELATED FIELDS IN DATABASE:')
    print()

    # Show ALL fields that might contain tax data
    tax_fields = {}
    for key, value in prop.items():
        if value is not None and value != '' and value != 0:
            # Look for tax-related field names
            key_lower = key.lower()
            if any(term in key_lower for term in ['tax', 'millage', 'levy', 'assessment', 'exemption', 'homestead', 'value']):
                tax_fields[key] = value

    if tax_fields:
        print('Tax-related fields found:')
        for field, value in sorted(tax_fields.items()):
            print(f'  {field}: {value}')
    else:
        print('No tax-specific fields found with data')

    print()
    print('Key Assessment Values for Tax Calculation:')
    print(f'  taxable_value: {prop.get("taxable_value", "N/A")}')
    print(f'  assessed_value: {prop.get("assessed_value", "N/A")}')
    print(f'  just_value: {prop.get("just_value", "N/A")}')
    print(f'  land_value: {prop.get("land_value", "N/A")}')
    print(f'  building_value: {prop.get("building_value", "N/A")}')
    print()

    # Calculate estimated tax based on Miami-Dade millage rates
    taxable_value = float(prop.get('taxable_value', 0))
    if taxable_value > 0:
        print('TAX CALCULATION (Miami-Dade County):')
        print(f'  Taxable Value: ${taxable_value:,.2f}')
        print()

        # Miami-Dade typical millage rate is around 20-22 mills (0.020 to 0.022)
        # This varies by location and includes county, school, city, etc.
        avg_millage = 0.021  # 21 mills typical for Miami-Dade
        estimated_tax = taxable_value * avg_millage

        print(f'  Estimated Annual Tax (at 21 mills): ${estimated_tax:,.2f}')
        print(f'  Calculation: ${taxable_value:,.2f} x 0.021 = ${estimated_tax:,.2f}')
        print()
        print('  Note: Actual tax depends on specific millage rates for:')
        print('    - County Operating')
        print('    - School District')
        print('    - City/Municipality')
        print('    - Special Districts')
        print('    - Non-ad valorem assessments')

        # We'll use this estimated tax amount for the API
        print()
        print('RECOMMENDATION:')
        print(f'  Add tax_amount field to API response: ${estimated_tax:,.2f}')
        print(f'  This is calculated as: taxable_value x 0.021 (avg Miami-Dade millage)')

    print()
    print('ALL DATABASE FIELDS (for reference):')
    for key, value in prop.items():
        if value is not None and value != '' and value != 0 and value != '0':
            print(f'  {key}: {value}')

# Also check if there's a separate tax table
print()
print('Checking for additional tax-related tables...')

# List all tables to see what's available
try:
    # Check common tax table names
    tax_tables = ['property_taxes', 'tax_bills', 'tax_assessments', 'property_tax_bills',
                  'miami_dade_taxes', 'county_taxes', 'tax_records']

    for table_name in tax_tables:
        try:
            test_response = supabase.table(table_name).select('*').eq('parcel_id', parcel_id).limit(1).execute()
            if test_response.data:
                print(f'  Found table: {table_name} with data for this parcel')
                for record in test_response.data:
                    print(f'    Sample record: {json.dumps(record, indent=2)}')
        except:
            pass  # Table doesn't exist

except Exception as e:
    print(f'Error checking tables: {e}')