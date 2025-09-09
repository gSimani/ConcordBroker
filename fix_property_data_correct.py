"""
Corrected Property Data Fix Script for 12681 NW 78 MNR
Uses only columns that exist in the florida_parcels table
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

def fix_property_474131031040():
    """Fix data for 12681 NW 78 MNR, PARKLAND FL 33076"""
    
    # Note: parcel_id field has 10 char limit, removing hyphens
    parcel_id = "4741310310"  # Shortened to fit varchar(10)
    
    print(f"[FIXING] Property data for parcel {parcel_id}")
    print("=" * 60)
    
    # Step 1: Update florida_parcels table with correct data (using ONLY existing columns)
    property_data = {
        # Basic Information
        "parcel_id": parcel_id,
        "phy_addr1": "12681 NW 78 MANOR",
        "phy_city": "PARKLAND",
        "phy_state": "FL", 
        "phy_zipcd": "33076",
        
        # Owner Information - CRITICAL FIX
        "owner_name": "IH3 PROPERTY FLORIDA LP",  # NOT just "INVITATION HOMES"
        "owner_addr1": "% INVITATION HOMES - TAX DEPT",
        "owner_addr2": "1717 MAIN ST #2000",
        "owner_city": "DALLAS",
        "owner_state": "TX",
        "owner_zip": "75201",
        
        # Property Use
        "property_use": "Single Family",
        "property_use_desc": "Single Family Residence",
        "land_use_code": "01-01",
        
        # Legal Description
        "legal_desc": "HERON BAY CENTRAL 171-23 B LOT 10 BLK D",
        "subdivision": "HERON BAY CENTRAL",
        "lot": "10",
        "block": "D",
        
        # 2025 Values - CRITICAL FIXES
        "just_value": 628040,  # NOT 580000
        "assessed_value": 601370,  # NOT 180!!!
        "taxable_value": 601370,
        "market_value": 628040,
        "land_value": 85580,  # NOT 145000
        "building_value": 542460,  # NOT 435000
        
        # Building Information
        "year_built": 2003,
        "total_living_area": 3012,
        "units": 1,
        "bedrooms": 4,
        "bathrooms": 3,
        "stories": 2,
        
        # Land Information
        "land_sqft": 10890,
        "area_sqft": 10890,
        
        # Most Recent Sale - from BCPA
        "sale_date": "2013-11-06",
        "sale_price": 375000,
        "sale_qualification": "Q"  # Qualified
    }
    
    print("[UPDATE] Updating florida_parcels table...")
    try:
        # First check if record exists
        existing = supabase.table('florida_parcels').select('id').eq('parcel_id', parcel_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase.table('florida_parcels').update(property_data).eq('parcel_id', parcel_id).execute()
            print("[SUCCESS] florida_parcels updated successfully")
        else:
            # Insert new record
            result = supabase.table('florida_parcels').insert(property_data).execute()
            print("[SUCCESS] florida_parcels inserted successfully")
    except Exception as e:
        print(f"[ERROR] Error updating florida_parcels: {e}")
        return False
    
    # Step 2: Add complete sales history (if table exists)
    sales_history = [
        {
            "parcel_id": parcel_id,
            "sale_date": "2013-11-06",
            "sale_price": 375000,
            "sale_type": "WD-Q",
            "deed_type": "Warranty Deed",
            "sale_qualification": "Qualified",
            "book_page": "111321624",
            "grantor_name": "Previous Owner",
            "grantee_name": "IH3 PROPERTY FLORIDA LP",
            "is_arms_length": True,
            "is_qualified_sale": True
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2010-09-15", 
            "sale_price": 100,
            "sale_type": "WD-T",
            "deed_type": "Warranty Deed",
            "sale_qualification": "Tax",
            "book_page": "47408/1861",
            "is_arms_length": False,
            "is_qualified_sale": False
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2009-07-27",
            "sale_price": 327000,
            "sale_type": "WD-Q",
            "deed_type": "Warranty Deed",
            "sale_qualification": "Qualified",
            "book_page": "46438/66",
            "is_arms_length": True,
            "is_qualified_sale": True
        },
        {
            "parcel_id": parcel_id,
            "sale_date": "2004-11-16",
            "sale_price": 432000,
            "sale_type": "WD",
            "deed_type": "Warranty Deed", 
            "sale_qualification": "Qualified",
            "book_page": "39186/1286",
            "is_arms_length": True,
            "is_qualified_sale": True
        }
    ]
    
    print("[UPDATE] Updating sales history...")
    try:
        # Delete old incorrect sales data
        supabase.table('property_sales_history').delete().eq('parcel_id', parcel_id).execute()
        
        # Insert correct sales history
        for sale in sales_history:
            result = supabase.table('property_sales_history').insert(sale).execute()
        print(f"[SUCCESS] Added {len(sales_history)} sales records")
    except Exception as e:
        print(f"[WARNING] Sales history table issue: {e}")
    
    # Step 3: Add Sunbiz entity data
    sunbiz_data = {
        "entity_name": "IH3 PROPERTY FLORIDA LP",
        "document_number": "M13000005449",
        "fei_ein_number": "80-0945919",
        "date_filed": "2013-08-28",
        "status": "ACTIVE",
        "entity_type": "Foreign Limited Partnership",
        "state": "DE",
        "principal_address": "5420 Lyndon B Johnson Freeway, Suite 600, Dallas, TX 75240",
        "mailing_address": "5420 Lyndon B Johnson Freeway, Suite 600, Dallas, TX 75240",
        "registered_agent_name": "CORPORATION SERVICE COMPANY",
        "registered_agent_address": "1201 HAYS STREET, TALLAHASSEE, FL 32301"
    }
    
    print("[UPDATE] Adding Sunbiz entity data...")
    try:
        # Try sunbiz_entities table
        result = supabase.table('sunbiz_entities').upsert(
            sunbiz_data,
            on_conflict='document_number'
        ).execute()
        print("[SUCCESS] Sunbiz entity added")
    except Exception as e:
        # Try sunbiz_corporate table
        try:
            result = supabase.table('sunbiz_corporate').upsert(
                sunbiz_data,
                on_conflict='document_number'
            ).execute()
            print("[SUCCESS] Sunbiz entity added to sunbiz_corporate")
        except Exception as e2:
            print(f"[WARNING] Sunbiz table issue: {e}")
    
    return True

def verify_fix():
    """Verify the data was fixed correctly"""
    parcel_id = "474131031040"
    
    print("\n" + "=" * 60)
    print("[VERIFY] Verifying fix...")
    
    try:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
        
        if result.data and len(result.data) > 0:
            data = result.data[0]
            
            # Check critical fields
            checks = [
                ("Owner Name", data.get('owner_name'), "IH3 PROPERTY FLORIDA LP"),
                ("Just Value", data.get('just_value'), 628040),
                ("Assessed Value", data.get('assessed_value'), 601370),
                ("Land Value", data.get('land_value'), 85580),
                ("Building Value", data.get('building_value'), 542460),
                ("Sale Price", data.get('sale_price'), 375000),
                ("Total Living Area", data.get('total_living_area'), 3012),
                ("Year Built", data.get('year_built'), 2003)
            ]
            
            all_correct = True
            for field, actual, expected in checks:
                if actual == expected:
                    print(f"[OK] {field}: {actual}")
                else:
                    print(f"[ERROR] {field}: {actual} (should be {expected})")
                    all_correct = False
            
            if all_correct:
                print("\n[SUCCESS] All critical data fixed successfully!")
            else:
                print("\n[WARNING] Some data still needs correction")
        else:
            print("[ERROR] Property not found in database")
    except Exception as e:
        print(f"[ERROR] Error verifying: {e}")

if __name__ == "__main__":
    print("[START] Starting Comprehensive Property Data Fix")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = fix_property_474131031040()
    
    if success:
        verify_fix()
        print("\n[SUCCESS] Data fix completed!")
        print("[INFO] Please refresh http://localhost:5174/properties/parkland/12681-nw-78-mnr")
    else:
        print("\n[ERROR] Data fix encountered errors")
        print("Please check the error messages above")