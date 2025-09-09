"""
IMMEDIATE FIX: Update existing property data with correct values
Uses existing columns in the florida_parcels table
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL") 
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

print("[START] IMMEDIATE DATA CORRECTION")
print("=" * 50)

# Fix property 474131031040 with correct official values
print("[1] Fixing property 474131031040 with official BCPA values...")

correct_data = {
    # Use existing column names from the audit
    'owner_name': 'IH3 PROPERTY FLORIDA LP',  # NOT "INVITATION HOMES"
    'assessed_value': 601370,    # NOT 180 !!!
    'just_value': 628040,        # Market value from BCPA
    'taxable_value': 601370,     # Taxable value 
    'land_value': 85580,         # NOT 145000
    'building_value': 542460,    # Calculated: 628040 - 85580
    'market_value': 628040,      # Just value
    'total_living_area': 3012,   # From BCPA
    'year_built': 2003,          # From BCPA
    'sale_price': 375000,        # Most recent sale
    'sale_date': '2013-11-06',   # Sale date
    'sale_qualification': 'Q',    # Qualified sale
    
    # Property details
    'property_use': 'Single Family',
    'property_use_desc': 'Single Family Residence', 
    'bedrooms': 4,
    'bathrooms': 3,
    'stories': 2,
    'land_sqft': 10890,
    'area_sqft': 10890,
    
    # Legal description
    'legal_desc': 'HERON BAY CENTRAL 171-23 B LOT 10 BLK D',
    'subdivision': 'HERON BAY CENTRAL',
    'lot': '10',
    'block': 'D'
}

try:
    result = supabase.table('florida_parcels').update(correct_data).eq('parcel_id', '474131031040').execute()
    
    if result.data and len(result.data) > 0:
        print("[SUCCESS] Property 474131031040 updated with correct values!")
        print("  ✅ Owner: IH3 PROPERTY FLORIDA LP")
        print("  ✅ Assessed Value: $601,370 (was $180)")
        print("  ✅ Just Value: $628,040")
        print("  ✅ Land Value: $85,580 (was $145,000)")
        print("  ✅ Building Value: $542,460")
        print("  ✅ Living Area: 3,012 sq ft")
        print("  ✅ Year Built: 2003")
    else:
        print("[WARNING] Property 474131031040 update may have failed")
        
except Exception as e:
    print(f"[ERROR] Update failed: {e}")

# Verify the changes
print("\n[2] Verifying the corrections...")
try:
    check = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
    
    if check.data and len(check.data) > 0:
        prop = check.data[0]
        
        print("\nVerification results:")
        print(f"  Owner: {prop.get('owner_name')}")
        print(f"  Assessed: ${prop.get('assessed_value'):,}" if prop.get('assessed_value') else "  Assessed: None")
        print(f"  Just Value: ${prop.get('just_value'):,}" if prop.get('just_value') else "  Just Value: None")
        print(f"  Land: ${prop.get('land_value'):,}" if prop.get('land_value') else "  Land: None")
        print(f"  Building: ${prop.get('building_value'):,}" if prop.get('building_value') else "  Building: None")
        print(f"  Living Area: {prop.get('total_living_area')} sq ft" if prop.get('total_living_area') else "  Living Area: None")
        print(f"  Year Built: {prop.get('year_built')}" if prop.get('year_built') else "  Year Built: None")
        
        # Check if the critical errors are fixed
        fixes_applied = 0
        if prop.get('owner_name') == 'IH3 PROPERTY FLORIDA LP':
            print("  ✅ Owner name FIXED")
            fixes_applied += 1
        else:
            print(f"  ❌ Owner still wrong: {prop.get('owner_name')}")
            
        if prop.get('assessed_value') == 601370:
            print("  ✅ Assessed value FIXED ($601,370)")
            fixes_applied += 1
        else:
            print(f"  ❌ Assessed value still wrong: {prop.get('assessed_value')}")
            
        if prop.get('total_living_area') == 3012:
            print("  ✅ Living area FIXED (3,012 sq ft)")
            fixes_applied += 1
        else:
            print(f"  ❌ Living area still wrong: {prop.get('total_living_area')}")
        
        print(f"\n[SUMMARY] {fixes_applied}/3 critical fixes applied")
        
        if fixes_applied == 3:
            print("\n🎉 SUCCESS! All critical data corrections applied!")
            print("The property page should now show correct values.")
        else:
            print(f"\n⚠️  {3-fixes_applied} issues remain - may need manual Supabase column updates")
    else:
        print("[ERROR] Could not verify - property not found")
        
except Exception as e:
    print(f"[ERROR] Verification failed: {e}")

print("\n" + "=" * 50)
print("[COMPLETE] Immediate data correction finished")
print("\n[NEXT STEP] Refresh: http://localhost:5174/properties/parkland/12681-nw-78-mnr")
print("[EXPECTED] Should now show:")
print("  - Owner: IH3 PROPERTY FLORIDA LP")
print("  - Assessed Value: $601,370") 
print("  - Living Area: 3,012 sq ft")
print("  - Year Built: 2003")
print("  - NO MORE N/A VALUES")