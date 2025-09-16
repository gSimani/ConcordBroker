"""
Targeted fix for property 474131031040 - only update existing columns with correct values
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("[ERROR] Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(url, key)

def fix_property_data():
    """Fix only the wrong values using existing columns"""
    
    parcel_id = "474131031040"
    
    print(f"[FIXING] Property data for parcel {parcel_id}")
    print("=" * 60)
    
    # TARGETED FIXES - only correct the wrong values
    correct_data = {
        # Fix living area: 3285 -> 3012
        "total_living_area": 3012,
        
        # Fix property values
        "just_value": 628040,  # 580000 -> 628040
        "land_value": 85580,   # 145000 -> 85580  
        "building_value": 542460,  # 435000 -> 542460
        
        # Fix bedrooms/bathrooms
        "bedrooms": 4,  # 5 -> 4
        "bathrooms": 3,  # 3.5 -> 3
        
        # Fix owner name (shortened to fit)
        "owner_name": "IH3 PROPERTY FLORIDA LP",
        
        # Add sale data
        "sale_price": 375000,
        "sale_date": "2013-11-06"
    }
    
    print("[UPDATE] Updating florida_parcels with correct values...")
    print("Corrections:")
    print(f"  Living Area: 3285 -> 3012 sq ft")
    print(f"  Just Value: $580,000 -> $628,040") 
    print(f"  Land Value: $145,000 -> $85,580")
    print(f"  Building Value: $435,000 -> $542,460")
    print(f"  Bedrooms: 5 -> 4")
    print(f"  Bathrooms: 3.5 -> 3")
    print(f"  Sale Price: None -> $375,000")
    
    try:
        result = supabase.table('florida_parcels').update(correct_data).eq('parcel_id', parcel_id).execute()
        print("[SUCCESS] florida_parcels updated successfully")
        
        # Also clear the wrong sales history
        print("[UPDATE] Clearing incorrect sales history...")
        supabase.table('property_sales_history').delete().eq('parcel_id', parcel_id).execute()
        
        # Add correct sales history
        correct_sales = [
            {
                "parcel_id": parcel_id,
                "sale_date": "2013-11-06",
                "sale_price": 375000,
                "deed_type": "Warranty Deed",
                "is_qualified_sale": True
            },
            {
                "parcel_id": parcel_id,
                "sale_date": "2010-09-15", 
                "sale_price": 100,
                "deed_type": "Tax Deed",
                "is_qualified_sale": False
            },
            {
                "parcel_id": parcel_id,
                "sale_date": "2009-07-27",
                "sale_price": 327000,
                "deed_type": "Warranty Deed",
                "is_qualified_sale": True
            },
            {
                "parcel_id": parcel_id,
                "sale_date": "2004-11-16",
                "sale_price": 432000,
                "deed_type": "Warranty Deed",
                "is_qualified_sale": True
            }
        ]
        
        for sale in correct_sales:
            try:
                result = supabase.table('property_sales_history').insert(sale).execute()
            except Exception as e:
                print(f"[WARNING] Could not add sale: {e}")
        
        print(f"[SUCCESS] Added {len(correct_sales)} correct sales records")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error updating property: {e}")
        return False

def verify_fix():
    """Verify the corrections were applied"""
    parcel_id = "474131031040"
    
    print("\n" + "=" * 60)
    print("[VERIFY] Checking corrections...")
    
    try:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
        
        if result.data and len(result.data) > 0:
            data = result.data[0]
            
            # Check all the fixes
            fixes = [
                ("Living Area", data.get('total_living_area'), 3012),
                ("Just Value", data.get('just_value'), 628040),
                ("Land Value", data.get('land_value'), 85580),
                ("Building Value", data.get('building_value'), 542460),
                ("Bedrooms", data.get('bedrooms'), 4),
                ("Bathrooms", data.get('bathrooms'), 3),
                ("Sale Price", data.get('sale_price'), 375000),
            ]
            
            all_correct = True
            for field, actual, expected in fixes:
                if actual == expected:
                    print(f"[OK] {field}: {actual}")
                else:
                    print(f"[STILL WRONG] {field}: {actual} (should be {expected})")
                    all_correct = False
            
            # Check sales history
            sales_result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).execute()
            if sales_result.data:
                most_recent = sales_result.data[0]
                expected_price = 375000
                expected_date = "2013-11-06"
                actual_price = most_recent.get('sale_price')
                actual_date = most_recent.get('sale_date')
                
                if actual_price == expected_price and actual_date == expected_date:
                    print(f"[OK] Sales History: ${actual_price} on {actual_date}")
                else:
                    print(f"[STILL WRONG] Sales: ${actual_price} on {actual_date} (should be ${expected_price} on {expected_date})")
                    all_correct = False
                    
                print(f"[INFO] Total sales records: {len(sales_result.data)}")
            
            if all_correct:
                print("\n[SUCCESS] All values corrected! Property should display correctly now.")
            else:
                print("\n[WARNING] Some values still need correction")
        else:
            print("[ERROR] Property not found")
    except Exception as e:
        print(f"[ERROR] Error verifying: {e}")

if __name__ == "__main__":
    print("[START] Targeted Property Data Fix")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = fix_property_data()
    
    if success:
        verify_fix()
        print("\n[COMPLETE] Property data fix completed!")
        print("[INFO] Refresh http://localhost:5174/properties/parkland/12681-nw-78-mnr to see changes")
    else:
        print("\n[FAILED] Fix encountered errors")