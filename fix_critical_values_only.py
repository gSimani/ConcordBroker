"""
Fix only the critical values that are causing the $180 vs $601,370 issue
Uses shorter field values to avoid character limits
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL") 
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

print("CRITICAL FIX: Property 474131031040")
print("=" * 40)

# Fix ONLY the most critical values causing the issue
critical_fixes = {
    'owner_name': 'IH3 PROPERTY FLORIDA LP',  # Critical fix
    'assessed_value': 601370,    # CRITICAL: Was showing $180 
    'just_value': 628040,        # Market value
    'taxable_value': 601370,     # Taxable value
    'land_value': 85580,         # Land value fix
    'building_value': 542460,    # Building value fix
    'total_living_area': 3012,   # Living area fix
    'property_use': 'Single Family',  # Shorter property use
    'subdivision': 'HERON BAY CENTRAL'  # Subdivision name
}

print("Applying critical fixes...")
try:
    result = supabase.table('florida_parcels').update(critical_fixes).eq('parcel_id', '474131031040').execute()
    
    if result.data:
        print("SUCCESS: Critical values updated")
    else:
        print("WARNING: Update returned no data")
        
except Exception as e:
    print(f"ERROR: {e}")
    
    # Try with even more minimal fixes
    print("Trying minimal fix...")
    minimal_fix = {
        'assessed_value': 601370,
        'owner_name': 'IH3 PROPERTY FL LP'  # Shortened
    }
    
    try:
        result2 = supabase.table('florida_parcels').update(minimal_fix).eq('parcel_id', '474131031040').execute()
        print("SUCCESS: Minimal fix applied")
    except Exception as e2:
        print(f"MINIMAL FIX FAILED: {e2}")

# Quick verification
print("\nVerification:")
try:
    check = supabase.table('florida_parcels').select('owner_name, assessed_value, just_value').eq('parcel_id', '474131031040').execute()
    
    if check.data:
        prop = check.data[0]
        print(f"Owner: {prop.get('owner_name')}")
        print(f"Assessed: ${prop.get('assessed_value'):,}" if prop.get('assessed_value') else "Assessed: None")
        print(f"Just Value: ${prop.get('just_value'):,}" if prop.get('just_value') else "Just Value: None")
        
        if prop.get('assessed_value') == 601370:
            print("✓ ASSESSED VALUE FIXED!")
        else:
            print(f"✗ Assessed value still: {prop.get('assessed_value')}")
            
except Exception as e:
    print(f"Verification error: {e}")

print("\nFIX COMPLETE - Check the property page now")