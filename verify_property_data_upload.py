"""
Comprehensive Property Appraiser Data Verification
Compares local TEMP\DATABASE PROPERTY APP files with Supabase database
"""

import os
import glob
from collections import defaultdict
from supabase import create_client, Client`r`nimport os`r`nfrom dotenv import load_dotenv`r`n
load_dotenv('.env.mcp');`r`ndef get_supabase_client() -> Client:
    """Create Supabase client"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
    return create_client(url, key)

load_dotenv('.env.mcp');`r`ndef analyze_local_data():
    """Analyze local Property Appraiser data files"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    counties_data = {}
    all_counties = []
    
    # Get all county folders
    for county_folder in os.listdir(base_path):
        county_path = os.path.join(base_path, county_folder)
        if os.path.isdir(county_path) and not county_folder.startswith('.'):
            if county_folder not in ['NAL_2025', 'NAL_2025P']:  # Skip non-county folders
                all_counties.append(county_folder)
                
                # Check what data types exist for this county
                data_types = {}
                for data_type in ['NAL', 'NAP', 'NAV', 'SDF']:
                    type_path = os.path.join(county_path, data_type)
                    if os.path.exists(type_path):
                        # Count files in each data type folder
                        files = glob.glob(os.path.join(type_path, '*'))
                        data_types[data_type] = len(files)
                
                counties_data[county_folder] = data_types
    
    return all_counties, counties_data

load_dotenv('.env.mcp');`r`ndef check_supabase_data():
    """Check what's in Supabase database"""
    client = get_supabase_client()
    
    # Get unique counties from florida_parcels
    try:
        # Get a sample to see what county field exists
        sample = client.table('florida_parcels').select('*').limit(1).execute()
        
        if sample.data and len(sample.data) > 0:
            # Check available fields
            available_fields = list(sample.data[0].keys())
            county_field = None
            
            # Find county field (could be county, county_name, co_no, etc.)
            for field in ['county', 'county_name', 'co_no', 'county_code']:
                if field in available_fields:
                    county_field = field
                    break
            
            print(f"\nAvailable fields in florida_parcels: {', '.join(available_fields[:10])}...")
            if county_field:
                print(f"Using county field: {county_field}")
            
            # Get county statistics
            # Note: Supabase doesn't support GROUP BY directly, so we'll get a sample
            counties_in_db = set()
            
            # Get records in batches to find unique counties
            offset = 0
            limit = 1000
            while offset < 10000:  # Sample first 10k records
                result = client.table('florida_parcels')\
                    .select(county_field if county_field else '*')\
                    .range(offset, offset + limit - 1)\
                    .execute()
                
                if result.data:
                    for row in result.data:
                        if county_field and row.get(county_field):
                            counties_in_db.add(str(row[county_field]))
                
                if len(result.data) < limit:
                    break
                    
                offset += limit
            
            return counties_in_db, county_field
        else:
            return set(), None
            
    except Exception as e:
        print(f"Error checking Supabase data: {e}")
        return set(), None

load_dotenv('.env.mcp');`r`ndef main():
    """Main verification function"""
    print("=" * 80)
    print("PROPERTY APPRAISER DATA UPLOAD VERIFICATION")
    print("=" * 80)
    
    # Analyze local data
    print("\n1. ANALYZING LOCAL DATA...")
    all_counties, counties_data = analyze_local_data()
    
    print(f"   Found {len(all_counties)} county folders")
    print(f"   Counties: {', '.join(sorted(all_counties)[:10])}...")
    
    # Count total data types
    total_by_type = defaultdict(int)
    for county, types in counties_data.items():
        for data_type, count in types.items():
            total_by_type[data_type] += 1
    
    print("\n   Data type coverage:")
    for data_type in ['NAL', 'NAP', 'NAV', 'SDF']:
        print(f"   - {data_type}: {total_by_type[data_type]} counties")
    
    # Check Supabase
    print("\n2. CHECKING SUPABASE DATABASE...")
    counties_in_db, county_field = check_supabase_data()
    
    if counties_in_db:
        print(f"   Found data from {len(counties_in_db)} unique county codes in database")
        print(f"   County codes in DB: {', '.join(sorted(counties_in_db)[:10])}...")
    
    # Get total count
    client = get_supabase_client()
    try:
        result = client.table('florida_parcels').select('*', count='exact').limit(0).execute()
        total_in_db = result.count if hasattr(result, 'count') else 0
        print(f"   Total records in database: {total_in_db:,}")
    except:
        total_in_db = 0
    
    # Generate comparison report
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    print(f"\nLocal Data:")
    print(f"  - Counties with data folders: {len(all_counties)}")
    print(f"  - Total county folders: {len(all_counties)}")
    
    print(f"\nSupabase Database:")
    print(f"  - Total records: {total_in_db:,}")
    print(f"  - Unique county codes found: {len(counties_in_db)}")
    
    # Create prompts for Supabase
    print("\n" + "=" * 80)
    print("PROMPTS FOR SUPABASE SQL EDITOR")
    print("=" * 80)
    
    print("\n1. Check total records and county distribution:")
    print("```sql")
    print("-- Total records in florida_parcels")
    print("SELECT COUNT(*) as total_records FROM florida_parcels;")
    print("```")
    
    print("\n2. Get county-wise property count:")
    print("```sql")
    print("-- Property count by county (adjust field name if needed)")
    print("SELECT ")
    print("  COALESCE(county, 'Unknown') as county_name,")
    print("  COUNT(*) as property_count")
    print("FROM florida_parcels")
    print("GROUP BY county")
    print("ORDER BY property_count DESC")
    print("LIMIT 20;")
    print("```")
    
    print("\n3. Check data completeness:")
    print("```sql")
    print("-- Check key fields population")
    print("SELECT ")
    print("  COUNT(*) as total,")
    print("  COUNT(parcel_id) as has_parcel_id,")
    print("  COUNT(phy_addr1) as has_address,")
    print("  COUNT(own_name) as has_owner,")
    print("  COUNT(jv) as has_just_value,")
    print("  COUNT(tv_sd) as has_taxable_value")
    print("FROM florida_parcels;")
    print("```")
    
    print("\n4. Check specific counties (example for Broward - code 06):")
    print("```sql")
    print("-- Check Broward County data")
    print("SELECT COUNT(*) as broward_properties")
    print("FROM florida_parcels")
    print("WHERE county = '06' OR county = 'BROWARD' OR county LIKE '%Broward%';")
    print("```")
    
    print("\n5. List all unique counties in database:")
    print("```sql")
    print("-- Get all unique county values")
    print("SELECT DISTINCT county, COUNT(*) as count")
    print("FROM florida_parcels")
    print("GROUP BY county")
    print("ORDER BY county;")
    print("```")
    
    # List counties we expect to see
    print("\n" + "=" * 80)
    print("EXPECTED COUNTIES FROM LOCAL FILES")
    print("=" * 80)
    for i, county in enumerate(sorted(all_counties), 1):
        if i % 5 == 1:
            print()
        print(f"{county:15}", end="")
    print()

if __name__ == "__main__":
    main()
