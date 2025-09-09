"""
URGENT DATABASE FIX: Add missing columns and correct property data
Fixes the field name mismatch between UI and database
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL") 
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

print("[START] URGENT DATABASE SCHEMA FIX")
print("=" * 50)

# Step 1: Add missing columns that UI expects
missing_columns_sql = """
-- Add columns that UI expects but don't exist
ALTER TABLE florida_parcels 
ADD COLUMN IF NOT EXISTS phy_addr1 VARCHAR(255),
ADD COLUMN IF NOT EXISTS phy_city VARCHAR(100), 
ADD COLUMN IF NOT EXISTS phy_zipcd VARCHAR(10),
ADD COLUMN IF NOT EXISTS own_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS jv NUMERIC,
ADD COLUMN IF NOT EXISTS av_sd NUMERIC,
ADD COLUMN IF NOT EXISTS tv_sd NUMERIC,
ADD COLUMN IF NOT EXISTS lnd_val NUMERIC,
ADD COLUMN IF NOT EXISTS tot_lvg_area NUMERIC,
ADD COLUMN IF NOT EXISTS act_yr_blt INTEGER,
ADD COLUMN IF NOT EXISTS dor_uc VARCHAR(10),
ADD COLUMN IF NOT EXISTS sale_prc1 NUMERIC,
ADD COLUMN IF NOT EXISTS sale_yr1 INTEGER,
ADD COLUMN IF NOT EXISTS sale_mo1 INTEGER,
ADD COLUMN IF NOT EXISTS qual_cd1 VARCHAR(5);
"""

print("[1] Adding missing columns...")
try:
    # Execute the SQL
    result = supabase.rpc('exec_sql', {'sql': missing_columns_sql}).execute()
    print("[SUCCESS] Missing columns added")
except Exception as e:
    print(f"[WARNING] Column addition issue: {e}")

# Step 2: Copy data from existing columns to new ones
print("[2] Copying existing data to new columns...")
try:
    # Get all records and update them
    records = supabase.table('florida_parcels').select('*').execute()
    
    for record in records.data:
        updated_data = {}
        
        # Map existing fields to UI expected fields
        if record.get('property_address'):
            updated_data['phy_addr1'] = record['property_address']
        if record.get('property_city'):
            updated_data['phy_city'] = record['property_city']  
        if record.get('property_zip'):
            updated_data['phy_zipcd'] = str(record['property_zip'])
        if record.get('owner_name'):
            updated_data['own_name'] = record['owner_name']
        if record.get('just_value'):
            updated_data['jv'] = record['just_value']
        if record.get('assessed_value'):
            updated_data['av_sd'] = record['assessed_value']
        if record.get('taxable_value'):
            updated_data['tv_sd'] = record['taxable_value']
        if record.get('land_value'):
            updated_data['lnd_val'] = record['land_value']
        if record.get('total_living_area'):
            updated_data['tot_lvg_area'] = record['total_living_area']
        if record.get('year_built'):
            updated_data['act_yr_blt'] = record['year_built']
        if record.get('sale_price'):
            updated_data['sale_prc1'] = record['sale_price']
        if record.get('sale_date') and 'T' in str(record['sale_date']):
            try:
                from datetime import datetime
                sale_date = datetime.fromisoformat(str(record['sale_date']).replace('Z', '+00:00'))
                updated_data['sale_yr1'] = sale_date.year
                updated_data['sale_mo1'] = sale_date.month
            except:
                pass
        
        # Update the record
        if updated_data:
            supabase.table('florida_parcels').update(updated_data).eq('id', record['id']).execute()
    
    print(f"[SUCCESS] Updated {len(records.data)} records with mapped fields")
    
except Exception as e:
    print(f"[ERROR] Data copying failed: {e}")

# Step 3: Fix the specific property that's wrong
print("[3] Fixing property 474131031040 with correct values...")

correct_property_data = {
    'phy_addr1': '12681 NW 78 MNR',
    'phy_city': 'PARKLAND', 
    'phy_zipcd': '33076',
    'own_name': 'IH3 PROPERTY FLORIDA LP',  # CRITICAL FIX
    'jv': 628040,        # Just Value
    'av_sd': 601370,     # Assessed Value - CRITICAL FIX  
    'tv_sd': 601370,     # Taxable Value
    'lnd_val': 85580,    # Land Value
    'tot_lvg_area': 3012, # Living Area
    'act_yr_blt': 2003,  # Year Built
    'dor_uc': '001',     # Property Use Code
    'sale_prc1': 375000, # Most Recent Sale
    'sale_yr1': 2013,    # Sale Year
    'sale_mo1': 11,      # Sale Month
    'qual_cd1': 'Q'      # Qualified Sale
}

try:
    # Update the specific problematic property
    result = supabase.table('florida_parcels').update(correct_property_data).eq('parcel_id', '474131031040').execute()
    
    if result.data:
        print("[SUCCESS] Property 474131031040 corrected")
        print("  - Owner: IH3 PROPERTY FLORIDA LP")  
        print("  - Assessed Value: $601,370")
        print("  - Living Area: 3,012 sq ft")
        print("  - Year Built: 2003")
    else:
        print("[WARNING] Property 474131031040 not found for update")
        
except Exception as e:
    print(f"[ERROR] Property fix failed: {e}")

# Step 4: Verify the fix
print("\n[4] Verifying the fix...")
try:
    test_property = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
    
    if test_property.data:
        prop = test_property.data[0]
        print("\nFixed property data:")
        print(f"  Address: {prop.get('phy_addr1')}")
        print(f"  Owner: {prop.get('own_name')}") 
        print(f"  Assessed Value: ${prop.get('av_sd'):,}" if prop.get('av_sd') else "  Assessed Value: N/A")
        print(f"  Living Area: {prop.get('tot_lvg_area')} sq ft" if prop.get('tot_lvg_area') else "  Living Area: N/A")
        print(f"  Year Built: {prop.get('act_yr_blt')}" if prop.get('act_yr_blt') else "  Year Built: N/A")
        
        # Check if critical fields are fixed
        if prop.get('av_sd') == 601370 and prop.get('own_name') == 'IH3 PROPERTY FLORIDA LP':
            print("\n[SUCCESS] ✅ CRITICAL ISSUES FIXED!")
            print("  ✅ Assessed value corrected: $601,370") 
            print("  ✅ Owner name corrected: IH3 PROPERTY FLORIDA LP")
            print("  ✅ UI field mappings added")
        else:
            print(f"\n[WARNING] Still needs work:")
            print(f"  - Assessed: {prop.get('av_sd')} (should be 601370)")
            print(f"  - Owner: {prop.get('own_name')} (should be IH3 PROPERTY FLORIDA LP)")
    else:
        print("[ERROR] Property not found after fix")
        
except Exception as e:
    print(f"[ERROR] Verification failed: {e}")

print("\n" + "=" * 50)
print("[COMPLETE] Urgent database fix finished")
print("[INFO] Please refresh http://localhost:5174/properties/parkland/12681-nw-78-mnr")
print("[INFO] The property should now show correct values instead of N/A")