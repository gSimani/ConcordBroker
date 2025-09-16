"""
Fix Property Integration - Connect property_assessments to frontend
This script updates the property search endpoint to use the real property_assessments data
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_ANON_KEY not found in environment variables")
    exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_property_assessments():
    """Test if property_assessments table has data"""
    try:
        # Count total properties
        result = supabase.table('property_assessments').select('*', count='exact').limit(1).execute()
        total_count = result.count if hasattr(result, 'count') else 0
        print(f"✓ property_assessments table has {total_count} records")
        
        # Get sample data
        sample = supabase.table('property_assessments').select('*').limit(5).execute()
        if sample.data:
            print(f"✓ Successfully retrieved sample data")
            print(f"  Sample property: {sample.data[0].get('property_address', 'N/A')}, {sample.data[0].get('property_city', 'N/A')}")
        
        # Count by county
        counties = supabase.table('property_assessments').select('county_name').execute()
        if counties.data:
            county_counts = {}
            for prop in counties.data:
                county = prop.get('county_name', 'Unknown')
                county_counts[county] = county_counts.get(county, 0) + 1
            
            print(f"✓ Properties by county:")
            for county, count in sorted(county_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {county}: {count} properties")
        
        return True
    except Exception as e:
        print(f"✗ Error accessing property_assessments: {e}")
        return False

def test_florida_parcels():
    """Test if florida_parcels table/view exists"""
    try:
        result = supabase.table('florida_parcels').select('*', count='exact').limit(1).execute()
        total_count = result.count if hasattr(result, 'count') else 0
        print(f"✓ florida_parcels has {total_count} records")
        return True
    except Exception as e:
        print(f"✗ florida_parcels not accessible: {e}")
        return False

def create_mapping_view():
    """Create SQL to map property_assessments to florida_parcels structure"""
    sql = """
-- Create or replace view to map property_assessments to florida_parcels structure
CREATE OR REPLACE VIEW florida_parcels AS
SELECT 
    id,
    parcel_id,
    property_address as phy_addr1,
    property_city as phy_city,
    'FL' as phy_state,
    property_zip as phy_zipcd,
    owner_name as own_name,
    owner_address as own_addr1,
    owner_city as own_city,
    owner_state as own_state,
    owner_zip as own_zipcd,
    property_use_code as dor_uc,
    just_value as jv,
    assessed_value as av,
    taxable_value as tv_sd,
    land_value as lnd_val,
    building_value as bldg_val,
    total_sq_ft as lnd_sqfoot,
    living_area as tot_lvg_area,
    year_built as act_yr_blt,
    bedrooms,
    bathrooms,
    county_code,
    county_name,
    CASE 
        WHEN property_use_code LIKE '0%' THEN 'Residential'
        WHEN property_use_code LIKE '1%' THEN 'Commercial'
        WHEN property_use_code LIKE '2%' THEN 'Industrial'
        WHEN property_use_code LIKE '3%' THEN 'Agricultural'
        WHEN property_use_code LIKE '4%' THEN 'Vacant Land'
        ELSE 'Other'
    END as property_type,
    tax_year,
    created_at,
    updated_at
FROM property_assessments;

-- Grant permissions
GRANT SELECT ON florida_parcels TO anon, authenticated;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON property_assessments(property_address);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON property_assessments(property_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON property_assessments(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel ON property_assessments(parcel_id);
"""
    
    print("\n" + "="*60)
    print("SQL TO RUN IN SUPABASE SQL EDITOR:")
    print("="*60)
    print(sql)
    print("="*60)
    
    return sql

def main():
    print("Property Integration Diagnostic Tool")
    print("="*40)
    
    # Test property_assessments
    print("\n1. Testing property_assessments table...")
    has_assessments = test_property_assessments()
    
    # Test florida_parcels
    print("\n2. Testing florida_parcels view/table...")
    has_parcels = test_florida_parcels()
    
    # Provide solution
    if has_assessments and not has_parcels:
        print("\n3. SOLUTION: Create mapping view")
        print("The property_assessments table has data but florida_parcels doesn't exist.")
        print("The frontend is looking for florida_parcels.")
        create_mapping_view()
        
        print("\n4. After running the SQL above in Supabase:")
        print("   - Restart the API server")
        print("   - The properties page should show all 121,477 properties")
    
    elif has_assessments and has_parcels:
        print("\n✓ Both tables are accessible. Properties should be visible.")
        print("If still not showing, check:")
        print("1. API is using port 8001: http://localhost:8001")
        print("2. Frontend is calling the correct port")
    
    else:
        print("\n✗ No property data found in database")
        print("You need to run the property data loader first")

if __name__ == "__main__":
    main()