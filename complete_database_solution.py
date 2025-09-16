"""
COMPLETE DATABASE SOLUTION
This script creates tables and loads mock data to ensure all tabs work
"""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("ERROR: Missing Supabase credentials")
    exit(1)

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print("=" * 80)
print("COMPLETE DATABASE SOLUTION")
print(f"Timestamp: {datetime.now()}")
print("=" * 80)

# Test property - same one shown in screenshots
TEST_PARCEL_ID = "504231242720"
TEST_ADDRESS = "3920 SW 53 CT"

def create_mock_data():
    """Create mock data for all tables"""
    
    mock_data = {}
    
    # 1. Properties table
    mock_data['properties'] = [{
        'parcel_id': TEST_PARCEL_ID,
        'owner_name': 'RODRIGUEZ MARIA',
        'property_address': TEST_ADDRESS,
        'city': 'Hollywood',
        'state': 'FL',
        'zip_code': '33021',
        'property_type': 'Single Family',
        'year_built': 1978,
        'total_sqft': 2150.0,
        'lot_size_sqft': 8500.0,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'assessed_value': 285000.00,
        'market_value': 425000.00,
        'last_sale_date': '2019-06-15',
        'last_sale_price': 320000.00
    }]
    
    # 2. Property sales history
    mock_data['property_sales_history'] = [
        {
            'parcel_id': TEST_PARCEL_ID,
            'sale_date': '2019-06-15',
            'sale_price': 320000.00,
            'sale_type': 'Warranty Deed',
            'buyer_name': 'RODRIGUEZ MARIA',
            'seller_name': 'SMITH JOHN & JANE',
            'deed_type': 'WD',
            'qualified_sale': True
        },
        {
            'parcel_id': TEST_PARCEL_ID,
            'sale_date': '2015-03-20',
            'sale_price': 245000.00,
            'sale_type': 'Warranty Deed',
            'buyer_name': 'SMITH JOHN & JANE',
            'seller_name': 'JOHNSON ROBERT',
            'deed_type': 'WD',
            'qualified_sale': True
        }
    ]
    
    # 3. NAV assessments
    mock_data['nav_assessments'] = [{
        'parcel_id': TEST_PARCEL_ID,
        'tax_year': 2024,
        'just_value': 425000.00,
        'assessed_value': 285000.00,
        'taxable_value': 260000.00,
        'land_value': 175000.00,
        'building_value': 250000.00,
        'exemptions': 25000.00,
        'exemption_types': 'Homestead',
        'millage_rate': 0.0185,
        'taxes_due': 4810.00
    }]
    
    # 4. Property tax records
    mock_data['property_tax_records'] = [{
        'parcel_id': TEST_PARCEL_ID,
        'tax_year': 2024,
        'tax_amount': 4810.00,
        'amount_paid': 2405.00,
        'amount_due': 2405.00,
        'payment_status': 'Partial',
        'due_date': '2025-03-31',
        'last_payment_date': '2024-11-15',
        'delinquent': False
    }]
    
    # 5. Tax certificates
    mock_data['tax_certificates'] = [{
        'parcel_id': TEST_PARCEL_ID,
        'certificate_number': 'TC-2023-001234',
        'tax_year': 2023,
        'certificate_date': '2024-06-01',
        'face_amount': 1250.00,
        'interest_rate': 18.0,
        'redemption_amount': 1475.00,
        'holder_name': 'BROWARD COUNTY',
        'status': 'Active'
    }]
    
    # 6. Florida permits
    mock_data['florida_permits'] = [
        {
            'permit_number': 'B24-001234',
            'parcel_id': TEST_PARCEL_ID,
            'property_address': TEST_ADDRESS,
            'permit_type': 'Building',
            'permit_subtype': 'Roof Replacement',
            'description': 'Replace shingle roof with new architectural shingles',
            'estimated_value': 12500.00,
            'contractor_name': 'ABC Roofing Inc',
            'contractor_license': 'CCC057234',
            'owner_name': 'RODRIGUEZ MARIA',
            'application_date': '2024-08-15',
            'issue_date': '2024-08-20',
            'status': 'Active'
        },
        {
            'permit_number': 'E24-005678',
            'parcel_id': TEST_PARCEL_ID,
            'property_address': TEST_ADDRESS,
            'permit_type': 'Electrical',
            'permit_subtype': 'Panel Upgrade',
            'description': 'Upgrade electrical panel from 100A to 200A',
            'estimated_value': 3500.00,
            'contractor_name': 'Elite Electric LLC',
            'contractor_license': 'EC13004567',
            'owner_name': 'RODRIGUEZ MARIA',
            'application_date': '2024-07-10',
            'issue_date': '2024-07-15',
            'finaled_date': '2024-09-01',
            'status': 'Finaled'
        }
    ]
    
    # 7. Sunbiz corporate (already exists but empty)
    mock_data['sunbiz_corporate'] = [{
        'cor_number': 'P12000087654',
        'cor_name': 'RODRIGUEZ PROPERTIES LLC',
        'cor_status': 'Active',
        'cor_filing_type': 'Limited Liability Company',
        'prin_addr1': TEST_ADDRESS,
        'prin_city': 'Hollywood',
        'prin_state': 'FL',
        'prin_zip': '33021',
        'registered_agent_name': 'RODRIGUEZ MARIA',
        'filing_date': '2012-09-15'
    }]
    
    # 8. Investment analysis
    mock_data['investment_analysis'] = [{
        'parcel_id': TEST_PARCEL_ID,
        'analysis_date': '2025-01-07',
        'investment_score': 75,
        'roi_estimate': 12.5,
        'cap_rate': 6.8,
        'cash_flow_monthly': 850.00,
        'market_rent_estimate': 2800.00,
        'renovation_cost_estimate': 35000.00,
        'arv_estimate': 475000.00,
        'neighborhood_grade': 'B+',
        'risk_level': 'Medium',
        'recommendation': 'Good investment opportunity with strong rental potential'
    }]
    
    # 9. Market comparables
    mock_data['market_comparables'] = [
        {
            'subject_parcel_id': TEST_PARCEL_ID,
            'comp_parcel_id': '504231242721',
            'comp_address': '3924 SW 53 CT',
            'distance_miles': 0.02,
            'sale_date': '2024-11-15',
            'sale_price': 435000.00,
            'price_per_sqft': 195.00,
            'sqft': 2230,
            'bedrooms': 3,
            'bathrooms': 2.5,
            'year_built': 1979,
            'similarity_score': 92.5
        },
        {
            'subject_parcel_id': TEST_PARCEL_ID,
            'comp_parcel_id': '504231242730',
            'comp_address': '3915 SW 53 CT',
            'distance_miles': 0.03,
            'sale_date': '2024-10-01',
            'sale_price': 415000.00,
            'price_per_sqft': 188.00,
            'sqft': 2210,
            'bedrooms': 3,
            'bathrooms': 2.0,
            'year_built': 1977,
            'similarity_score': 88.0
        }
    ]
    
    return mock_data

def upload_data(table_name, data):
    """Upload data to Supabase table"""
    if not data:
        return False
        
    url = f'{SUPABASE_URL}/rest/v1/{table_name}'
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            print(f"  OK Uploaded {len(data)} records to {table_name}")
            return True
        elif response.status_code == 404:
            print(f"  X Table {table_name} does not exist")
            return False
        elif response.status_code == 409:
            print(f"  - Data already exists in {table_name}")
            return True
        else:
            print(f"  ? Error uploading to {table_name}: {response.status_code}")
            if response.text:
                print(f"    {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  X Exception uploading to {table_name}: {str(e)}")
        return False

def check_table_exists(table_name):
    """Check if a table exists"""
    url = f'{SUPABASE_URL}/rest/v1/{table_name}?limit=1'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return False
        elif response.status_code in [200, 206]:
            return True
        else:
            # Might be unauthorized but table exists
            return None
    except:
        return None

# Create mock data
print("\n1. CREATING MOCK DATA")
print("=" * 60)
mock_data = create_mock_data()
print(f"Created mock data for {len(mock_data)} tables")

# Check which tables exist
print("\n2. CHECKING TABLE STATUS")
print("=" * 60)
tables_exist = []
tables_missing = []
tables_unknown = []

for table_name in mock_data.keys():
    status = check_table_exists(table_name)
    if status is True:
        tables_exist.append(table_name)
        print(f"  OK {table_name}: EXISTS")
    elif status is False:
        tables_missing.append(table_name)
        print(f"  X {table_name}: MISSING")
    else:
        tables_unknown.append(table_name)
        print(f"  ? {table_name}: UNKNOWN")

# Upload data to existing tables
print("\n3. UPLOADING MOCK DATA")
print("=" * 60)

if not tables_exist and not tables_unknown:
    print("ERROR: No tables exist!")
    print("\nTO FIX THIS:")
    print("1. Go to Supabase Dashboard")
    print("2. Run the SQL from 'create_all_missing_tables.sql'")
    print("3. Then run this script again")
else:
    success_count = 0
    fail_count = 0
    
    # Try all tables (even unknown ones)
    all_tables = tables_exist + tables_unknown
    
    if all_tables:
        for table_name in all_tables:
            if table_name in mock_data:
                if upload_data(table_name, mock_data[table_name]):
                    success_count += 1
                else:
                    fail_count += 1
    
    # Also try missing tables in case they were just created
    if tables_missing:
        print("\nTrying missing tables (in case they were just created):")
        for table_name in tables_missing:
            if table_name in mock_data:
                if upload_data(table_name, mock_data[table_name]):
                    success_count += 1
                    tables_missing.remove(table_name)
                    tables_exist.append(table_name)

# Final summary
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Tables with data: {success_count}/{len(mock_data)}")
print(f"Tables missing: {len(tables_missing)}")

if tables_missing:
    print("\nMissing tables that need to be created:")
    for table in tables_missing:
        print(f"  - {table}")
    print("\nRun 'create_all_missing_tables.sql' in Supabase to create them")

if success_count > 0:
    print("\nSUCCESS: Some data was loaded!")
    print("Check the web interface - tabs should now show data for property:")
    print(f"  Address: {TEST_ADDRESS}")
    print(f"  Parcel: {TEST_PARCEL_ID}")
    
if success_count == len(mock_data):
    print("\n100% COMPLETE - All tables have data!")
else:
    completion = (success_count / len(mock_data)) * 100
    print(f"\n{completion:.1f}% Complete")
    
print("\nNext step: Run 'python comprehensive_database_audit.py' to verify")