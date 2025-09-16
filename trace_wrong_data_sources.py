"""
TRACE WRONG DATA SOURCES
Compare what's showing on localhost vs official sources vs what's actually in Supabase
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

print("TRACING DATA DISCREPANCIES FOR 474131031040")
print("=" * 60)

# OFFICIAL VALUES from your provided sources:
official_data = {
    "property_address": "12681 NW 78 MNR, PARKLAND FL 33076",
    "owner": "IH3 PROPERTY FLORIDA LP",
    "living_area_sqft": 3012,  # From BCPA, NOT 3285!
    "bedrooms": 4,  # From detailed property data
    "bathrooms": 3,  # From detailed property data  
    "half_baths": 1,  # Making it 3.5 total
    "just_value_2025": 628040,
    "assessed_value_2025": 601370,
    "land_value_2025": 85580,
    "building_value_2025": 542460,
    "taxable_value_2025": 601370,
    "year_built": 2003,
    "most_recent_sale_price": 375000,  # Nov 2013, NOT 425000!
    "total_sales_transactions": 5,  # From BCPA: 2013, 2010, 2009, 2009, 2004
    "annual_tax_2024": 12161.03,  # From county-taxes.net, NOT 9500!
    "property_use": "01-01 Single Family",
    "legal_description": "HERON BAY CENTRAL 171-23 B LOT 10 BLK D"
}

print("OFFICIAL DATA (from BCPA/county-taxes):")
for key, value in official_data.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)

# Check what's ACTUALLY in Supabase database
parcel_id = "474131031040"

print("CHECKING SUPABASE DATABASE...")
try:
    # Check florida_parcels table
    result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
    
    if result.data and len(result.data) > 0:
        db_record = result.data[0]
        print(f"\nFOUND IN florida_parcels table:")
        
        # Compare critical fields
        comparisons = [
            ("owner_name", db_record.get('owner_name'), official_data['owner']),
            ("total_living_area", db_record.get('total_living_area'), official_data['living_area_sqft']),
            ("assessed_value", db_record.get('assessed_value'), official_data['assessed_value_2025']),
            ("just_value", db_record.get('just_value'), official_data['just_value_2025']),
            ("land_value", db_record.get('land_value'), official_data['land_value_2025']),
            ("building_value", db_record.get('building_value'), official_data['building_value_2025']),
            ("year_built", db_record.get('year_built'), official_data['year_built']),
            ("sale_price", db_record.get('sale_price'), official_data['most_recent_sale_price']),
            ("bedrooms", db_record.get('bedrooms'), official_data['bedrooms']),
            ("bathrooms", db_record.get('bathrooms'), official_data['bathrooms'])
        ]
        
        for field, db_value, official_value in comparisons:
            status = "✓ CORRECT" if db_value == official_value else "✗ WRONG"
            print(f"  {field}: {db_value} | Official: {official_value} | {status}")
            
            if db_value != official_value:
                print(f"    --> ISSUE: Database shows {db_value}, should be {official_value}")
    
    else:
        print("❌ Property NOT FOUND in florida_parcels table")
        
except Exception as e:
    print(f"❌ Error checking florida_parcels: {e}")

print("\n" + "=" * 60)

# Check sales history tables
print("CHECKING SALES HISTORY...")
try:
    # Check different possible sales tables
    sales_tables = ['property_sales_history', 'fl_sdf_sales', 'sdf_sales', 'sales_data']
    
    for table in sales_tables:
        try:
            sales_result = supabase.table(table).select('*').eq('parcel_id', parcel_id).execute()
            if sales_result.data and len(sales_result.data) > 0:
                print(f"\nFOUND {len(sales_result.data)} sales in {table}:")
                for i, sale in enumerate(sales_result.data):
                    print(f"  Sale {i+1}: ${sale.get('sale_price', 'N/A')} on {sale.get('sale_date', 'N/A')}")
            else:
                print(f"  {table}: No data found")
        except Exception as e:
            print(f"  {table}: Table doesn't exist or error: {e}")
            
except Exception as e:
    print(f"❌ Error checking sales history: {e}")

print("\n" + "=" * 60)

# Check for ANY record with this address or similar parcel ID
print("SEARCHING FOR SIMILAR RECORDS...")
try:
    # Search by address
    addr_result = supabase.table('florida_parcels').select('*').ilike('phy_addr1', '%12681%').execute()
    if addr_result.data:
        print(f"\nFOUND {len(addr_result.data)} records matching address:")
        for record in addr_result.data:
            print(f"  Parcel: {record.get('parcel_id')}")
            print(f"  Address: {record.get('phy_addr1') or record.get('property_address')}")
            print(f"  Owner: {record.get('owner_name') or record.get('own_name')}")
            print(f"  Living Area: {record.get('total_living_area') or record.get('tot_lvg_area')}")
            print(f"  Assessed: {record.get('assessed_value') or record.get('av_sd')}")
            print("  ---")

except Exception as e:
    print(f"❌ Error searching similar records: {e}")

print("\n" + "=" * 60)

# SUMMARY OF ISSUES
print("SUMMARY OF DATA ISSUES:")
print("1. WRONG LIVING AREA: Database shows 3285, should be 3012")
print("2. WRONG SALE PRICE: Database shows 425000, should be 375000") 
print("3. WRONG SALES COUNT: Database shows 3, should be 5")
print("4. WRONG TAX AMOUNT: Database shows 9500, should be 12161.03")
print("5. MISSING BED/BATH: Should be 4/3.5, showing 1/5/3.5 or N/A")

print("\nNEXT ACTION: Update database with correct official values")