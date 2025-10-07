"""
Check for sales-related tables and data in Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("CHECKING SUPABASE FOR SALES DATA")
print("=" * 80)
print()

# Tables to check for sales data
sales_tables = [
    'comprehensive_sales_data',
    'sdf_sales',
    'sales_history',
    'florida_parcels',
    'property_sales',
    'sales_data',
    'sales_transactions'
]

print("1. CHECKING FOR SALES TABLES:")
print("-" * 40)

for table in sales_tables:
    try:
        # Try to query each table for count
        response = supabase.table(table).select('*', count='exact', head=True).execute()
        count = response.count if hasattr(response, 'count') else 0
        print(f"✓ {table}: {count:,} records")
    except Exception as e:
        error_msg = str(e)
        if 'relation' in error_msg and 'does not exist' in error_msg:
            print(f"✗ {table}: Table does not exist")
        else:
            print(f"? {table}: Error - {error_msg[:50]}")

print()
print("2. CHECKING FLORIDA_PARCELS FOR SALES COLUMNS:")
print("-" * 40)

try:
    # Check if florida_parcels has sales data columns
    response = supabase.table('florida_parcels').select('parcel_id, sale_date, sale_price, sale_year, sale_qualification').limit(1).execute()

    if response.data:
        sample = response.data[0]
        print("Sales columns found in florida_parcels:")
        for col in ['sale_date', 'sale_price', 'sale_year', 'sale_qualification']:
            if col in sample:
                print(f"  - {col}: {sample[col]}")

        # Count properties with sale data
        with_sales = supabase.table('florida_parcels').select('id', count='exact', head=True).not_('sale_price', 'is', None).execute()
        sales_count = with_sales.count if hasattr(with_sales, 'count') else 0
        print(f"\nProperties with sale_price data: {sales_count:,}")

except Exception as e:
    print(f"Error checking florida_parcels: {e}")

print()
print("3. SAMPLE PARCEL WITH SALES DATA:")
print("-" * 40)

try:
    # Find a property with actual sales data
    response = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city, sale_price, sale_year, sale_date').gt('sale_price', 100000).limit(5).execute()

    if response.data:
        print("Found properties with sales data:")
        for prop in response.data:
            print(f"\nParcel: {prop['parcel_id']}")
            print(f"Address: {prop['phy_addr1']}, {prop['phy_city']}")
            print(f"Sale Price: ${prop['sale_price']:,.0f}" if prop['sale_price'] else "N/A")
            print(f"Sale Year: {prop['sale_year']}" if prop['sale_year'] else "N/A")
            print(f"Sale Date: {prop['sale_date']}" if prop.get('sale_date') else "N/A")
    else:
        print("No properties found with sales data > $100,000")

except Exception as e:
    print(f"Error finding sample properties: {e}")

print()
print("4. RECOMMENDATIONS:")
print("-" * 40)
print("""
Based on the findings above, here's what needs to be done:

1. If no dedicated sales tables exist, we need to:
   - Create a 'property_sales' table with proper schema
   - Import SDF (Sales Data File) from Florida Revenue

2. If florida_parcels has sales columns but limited data:
   - Import comprehensive sales history from SDF files
   - Create a view to combine sales data

3. Required table structure for property_sales:
   CREATE TABLE property_sales (
     id SERIAL PRIMARY KEY,
     parcel_id VARCHAR(50) NOT NULL,
     sale_date DATE,
     sale_price NUMERIC(12,2),
     sale_year INTEGER,
     sale_month INTEGER,
     qualified_sale BOOLEAN,
     document_type VARCHAR(100),
     grantor_name VARCHAR(255),
     grantee_name VARCHAR(255),
     book VARCHAR(50),
     page VARCHAR(50),
     vi_code VARCHAR(10),
     created_at TIMESTAMP DEFAULT NOW()
   );

4. Create index for performance:
   CREATE INDEX idx_property_sales_parcel ON property_sales(parcel_id);
   CREATE INDEX idx_property_sales_date ON property_sales(sale_date DESC);
""")