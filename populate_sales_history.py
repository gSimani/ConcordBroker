"""
Populate Sales History Data in Supabase
Creates sample sales data for testing property pages
"""

from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print('Missing Supabase credentials')
    exit(1)

supabase = create_client(url, key)

# Sample property with known parcel_id from the URL
parcel_id = '474131031040'

# Create sales_history table if it doesn't exist
create_table_sql = """
CREATE TABLE IF NOT EXISTS sales_history (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    sale_price DECIMAL(12,2) NOT NULL,
    sale_year INTEGER,
    sale_month INTEGER,
    sale_type VARCHAR(50),
    document_type VARCHAR(100),
    grantor_name VARCHAR(200),
    grantee_name VARCHAR(200),
    book VARCHAR(20),
    page VARCHAR(20),
    sale_reason VARCHAR(200),
    vi_code VARCHAR(20),
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    is_cash_sale BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_history_parcel ON sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_history_date ON sales_history(sale_date);
"""

# Sample sales data for the property
sales_records = [
    {
        'parcel_id': parcel_id,
        'sale_date': '2023-08-15',
        'sale_price': 485000,
        'sale_year': 2023,
        'sale_month': 8,
        'sale_type': 'qualified',
        'document_type': 'Warranty Deed',
        'grantor_name': 'JOHNSON FAMILY TRUST',
        'grantee_name': 'MARTINEZ, CARLOS & MARIA',
        'book': '2023',
        'page': '45678',
        'sale_reason': 'Arms Length Sale',
        'vi_code': 'Q',
        'is_distressed': False,
        'is_bank_sale': False,
        'is_cash_sale': True
    },
    {
        'parcel_id': parcel_id,
        'sale_date': '2019-03-20',
        'sale_price': 395000,
        'sale_year': 2019,
        'sale_month': 3,
        'sale_type': 'qualified',
        'document_type': 'Warranty Deed',
        'grantor_name': 'SMITH, ROBERT & LINDA',
        'grantee_name': 'JOHNSON FAMILY TRUST',
        'book': '2019',
        'page': '12345',
        'sale_reason': 'Arms Length Sale',
        'vi_code': 'Q',
        'is_distressed': False,
        'is_bank_sale': False,
        'is_cash_sale': False
    },
    {
        'parcel_id': parcel_id,
        'sale_date': '2015-11-10',
        'sale_price': 320000,
        'sale_year': 2015,
        'sale_month': 11,
        'sale_type': 'qualified',
        'document_type': 'Special Warranty Deed',
        'grantor_name': 'FIRST NATIONAL BANK',
        'grantee_name': 'SMITH, ROBERT & LINDA',
        'book': '2015',
        'page': '98765',
        'sale_reason': 'Foreclosure Sale',
        'vi_code': 'Q',
        'is_distressed': True,
        'is_bank_sale': True,
        'is_cash_sale': False
    },
    {
        'parcel_id': parcel_id,
        'sale_date': '2008-06-25',
        'sale_price': 425000,
        'sale_year': 2008,
        'sale_month': 6,
        'sale_type': 'qualified',
        'document_type': 'Warranty Deed',
        'grantor_name': 'DEVELOPER CORP LLC',
        'grantee_name': 'WILLIAMS, JAMES',
        'book': '2008',
        'page': '54321',
        'sale_reason': 'New Construction Sale',
        'vi_code': 'Q',
        'is_distressed': False,
        'is_bank_sale': False,
        'is_cash_sale': False
    },
    {
        'parcel_id': parcel_id,
        'sale_date': '2005-01-15',
        'sale_price': 185000,
        'sale_year': 2005,
        'sale_month': 1,
        'sale_type': 'qualified',
        'document_type': 'Warranty Deed',
        'grantor_name': 'LAND DEVELOPMENT INC',
        'grantee_name': 'DEVELOPER CORP LLC',
        'book': '2005',
        'page': '11111',
        'sale_reason': 'Vacant Land Sale',
        'vi_code': 'Q',
        'is_distressed': False,
        'is_bank_sale': False,
        'is_cash_sale': False
    }
]

print(f"Populating sales history for property {parcel_id}")
print("=" * 60)

try:
    # Insert sales records
    for i, record in enumerate(sales_records, 1):
        response = supabase.table('sales_history').upsert(record).execute()
        print(f"[{i}/{len(sales_records)}] Added sale from {record['sale_date']}: ${record['sale_price']:,}")

    print("\n✓ Sales history populated successfully!")
    print(f"Total records added: {len(sales_records)}")

    # Verify the data
    print("\nVerifying data...")
    verify_response = supabase.table('sales_history').select('*').eq('parcel_id', parcel_id).execute()

    if verify_response.data:
        print(f"✓ Found {len(verify_response.data)} sales records in database")
        print("\nSales Summary:")
        for sale in sorted(verify_response.data, key=lambda x: x['sale_date'], reverse=True):
            print(f"  - {sale['sale_date']}: ${sale['sale_price']:,.0f} ({sale['grantee_name']})")
    else:
        print("✗ No records found in verification")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTrying to create table first...")

    # Try to create the table
    try:
        # Note: Direct SQL execution might not work, using table operations instead
        # First, try to insert a dummy record to auto-create the table
        dummy_record = {
            'parcel_id': 'TEST',
            'sale_date': '2024-01-01',
            'sale_price': 1,
            'sale_year': 2024,
            'sale_month': 1
        }

        supabase.table('sales_history').insert(dummy_record).execute()
        supabase.table('sales_history').delete().eq('parcel_id', 'TEST').execute()

        print("✓ Table created, retrying insertion...")

        # Retry insertion
        for i, record in enumerate(sales_records, 1):
            response = supabase.table('sales_history').upsert(record).execute()
            print(f"[{i}/{len(sales_records)}] Added sale from {record['sale_date']}: ${record['sale_price']:,}")

        print("\n✓ Sales history populated successfully on second attempt!")

    except Exception as e2:
        print(f"✗ Failed to create table: {e2}")
        print("\nPlease create the sales_history table manually in Supabase with the following columns:")
        print("  - parcel_id (text)")
        print("  - sale_date (date)")
        print("  - sale_price (numeric)")
        print("  - sale_year (int)")
        print("  - sale_month (int)")
        print("  - sale_type (text)")
        print("  - document_type (text)")
        print("  - grantor_name (text)")
        print("  - grantee_name (text)")
        print("  - book (text)")
        print("  - page (text)")
        print("  - sale_reason (text)")
        print("  - vi_code (text)")
        print("  - is_distressed (bool)")
        print("  - is_bank_sale (bool)")
        print("  - is_cash_sale (bool)")

print("\n" + "=" * 60)
print("Visit http://localhost:5173/property/474131031040 to see the sales history!")
print("The Sales History tab should now show real data instead of 'No Sales History Available'")