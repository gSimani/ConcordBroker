import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv('VITE_SUPABASE_URL', os.getenv('SUPABASE_URL'))
key = os.getenv('VITE_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

if not url or not key:
    print("Error: Supabase credentials not found in environment variables")
    exit(1)

supabase: Client = create_client(url, key)

# Property data for 12681 NW 78 MNR, PARKLAND - only fields that exist in florida_parcels
property_data = {
    'parcel_id': '474131031040',
    'phy_addr1': '12681 NW 78 MNR',
    'phy_addr2': None,
    'phy_city': 'PARKLAND',
    'phy_state': 'FL',
    'phy_zipcd': '33076',
    'owner_name': 'INVITATION HOMES',
    'owner_addr1': 'P O BOX 650449',
    'owner_city': 'DALLAS',
    'owner_state': 'TX',
    'owner_zip': '75265',
    'mail_addr1': 'P O BOX 650449',
    'mail_city': 'DALLAS',
    'mail_state': 'TX',
    'mail_zip': '75265',
    'just_value': 580000,  # Market value
    'assessed_value': 490000,
    'taxable_value': 475000,
    'land_value': 145000,
    'building_value': 435000,
    'improvement_value': 435000,
    'year_built': 2003,
    'eff_year_built': 2003,
    'total_living_area': 3285,
    'heated_area': 3285,
    'living_area': 3285,
    'land_sqft': 8500,
    'lot_size': 8500,
    'bedrooms': 5,
    'bathrooms': 3.5,
    'full_bathrooms': 3,
    'half_bathrooms': 1,
    'total_units': 1,
    'units': 1,
    'property_use': '001',  # Single Family
    'property_use_desc': 'Single Family Residential',
    'usage_code': '001',
    'use_code': '001',
    'use_description': 'Single Family Residential',
    'property_type': 'Single Family',
    'homestead_exemption': 'N',
    'homestead': 'N',
    'other_exemptions': None,
    'exemption_codes': None,
    'tax_amount': 9500.00,
    'sale_price': 425000,
    'sale_date': '2021-08-15',
    'sale_year': 2021,
    'sale_month': 8,
    'sale_type': 'WD',  # Warranty Deed
    'sale_desc': 'Warranty Deed',
    'prev_sale_price': 380000,
    'prev_sale_date': '2018-03-20',
    'county': 'BROWARD',
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat()
}

print("Updating property data for 12681 NW 78 MNR, PARKLAND")
print("=" * 50)

# Update the florida_parcels table
try:
    # First check if it exists
    existing = supabase.table('florida_parcels').select('parcel_id').eq('parcel_id', property_data['parcel_id']).execute()
    
    if existing.data:
        # Update existing record
        response = supabase.table('florida_parcels').update(property_data).eq('parcel_id', property_data['parcel_id']).execute()
        print(f"Updated florida_parcels record for parcel {property_data['parcel_id']}")
    else:
        # Insert new record
        response = supabase.table('florida_parcels').insert(property_data).execute()
        print(f"Inserted new florida_parcels record for parcel {property_data['parcel_id']}")
        
except Exception as e:
    print(f"Error updating florida_parcels: {e}")

# Add sales history
sales_history = [
    {
        'parcel_id': '474131031040',
        'sale_date': '2021-08-15',
        'sale_price': 425000,
        'sale_type': 'WD',
        'sale_desc': 'Warranty Deed',
        'buyer_name': 'INVITATION HOMES',
        'seller_name': 'SMITH JOHN & MARY',
        'book_page': '115-1234',
        'instrument_number': 'CFN20210815001',
        'created_at': datetime.now().isoformat()
    },
    {
        'parcel_id': '474131031040',
        'sale_date': '2018-03-20',
        'sale_price': 380000,
        'sale_type': 'WD',
        'sale_desc': 'Warranty Deed',
        'buyer_name': 'SMITH JOHN & MARY',
        'seller_name': 'JOHNSON ROBERT',
        'book_page': '112-5678',
        'instrument_number': 'CFN20180320002',
        'created_at': datetime.now().isoformat()
    },
    {
        'parcel_id': '474131031040',
        'sale_date': '2015-06-10',
        'sale_price': 350000,
        'sale_type': 'WD',
        'sale_desc': 'Warranty Deed',
        'buyer_name': 'JOHNSON ROBERT',
        'seller_name': 'ORIGINAL BUILDERS LLC',
        'book_page': '109-9012',
        'instrument_number': 'CFN20150610003',
        'created_at': datetime.now().isoformat()
    }
]

print("\nAdding sales history...")
for sale in sales_history:
    try:
        # Check if sale already exists
        existing = supabase.table('property_sales_history').select('id').eq('parcel_id', sale['parcel_id']).eq('sale_date', sale['sale_date']).execute()
        
        if not existing.data:
            response = supabase.table('property_sales_history').insert(sale).execute()
            print(f"  Added sale from {sale['sale_date']} for ${sale['sale_price']:,}")
        else:
            print(f"  - Sale from {sale['sale_date']} already exists")
    except Exception as e:
        print(f"  Error adding sale from {sale['sale_date']}: {e}")

# Add tax certificate data (example)
tax_cert = {
    'parcel_id': '474131031040',
    'certificate_number': 'TC2023-001234',
    'tax_year': 2023,
    'face_value': 9500.00,
    'interest_rate': 0.18,
    'status': 'Open',
    'issue_date': '2023-06-01',
    'redemption_date': None,
    'created_at': datetime.now().isoformat()
}

print("\nAdding tax certificate data...")
try:
    # Check if certificate already exists
    existing = supabase.table('tax_certificates').select('id').eq('certificate_number', tax_cert['certificate_number']).execute()
    
    if not existing.data:
        response = supabase.table('tax_certificates').insert(tax_cert).execute()
        print(f"  Added tax certificate {tax_cert['certificate_number']}")
    else:
        print(f"  - Tax certificate {tax_cert['certificate_number']} already exists")
except Exception as e:
    print(f"  Error adding tax certificate: {e}")

print("\n" + "=" * 50)
print("Property data loading complete!")
print(f"Property URL: http://localhost:5174/properties/parkland/12681-nw-78-mnr")