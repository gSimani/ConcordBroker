"""
Verify Property Appraiser Upload Status in Supabase
"""

from supabase import create_client, Client
from datetime import datetime

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    return create_client(url, key)

def run_verification():
    """Run verification queries"""
    client = get_supabase_client()
    
    print("=" * 60)
    print("FLORIDA PARCELS UPLOAD VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Total rows and latest insert
    print("1. TOTAL ROWS AND LATEST INSERT:")
    print("-" * 40)
    try:
        result = client.table('florida_parcels').select('*', count='exact').limit(0).execute()
        total_count = result.count if hasattr(result, 'count') else 0
        print(f"   Total rows: {total_count:,}")
        
        # Get latest record
        latest = client.table('florida_parcels').select('import_date').order('import_date', desc=True).limit(1).execute()
        if latest.data:
            print(f"   Last insert: {latest.data[0].get('import_date', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 2. Broward county count
    print("2. BROWARD COUNTY COUNT:")
    print("-" * 40)
    try:
        result = client.table('florida_parcels').select('*', count='exact').eq('county', 'BROWARD').limit(0).execute()
        broward_count = result.count if hasattr(result, 'count') else 0
        print(f"   Broward records: {broward_count:,}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 3. Check column structure
    print("3. COLUMN STRUCTURE CHECK:")
    print("-" * 40)
    try:
        # Get a sample record to see columns
        sample = client.table('florida_parcels').select('*').limit(1).execute()
        if sample.data:
            columns = list(sample.data[0].keys())
            
            # Check for remapped columns
            important_cols = ['owner_name', 'owner_addr1', 'owner_addr2', 'owner_city', 
                            'owner_state', 'owner_zip', 'land_use_code', 'property_use',
                            'just_value', 'taxable_value', 'land_value', 'land_sqft',
                            'sale_price', 'sale_date', 'legal_desc']
            
            print("   Remapped columns present:")
            for col in important_cols:
                if col in columns:
                    print(f"   ✓ {col}")
                else:
                    print(f"   ✗ {col} (missing)")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 4. Counties with data
    print("4. TOP COUNTIES BY RECORD COUNT:")
    print("-" * 40)
    try:
        # Get unique counties
        counties = client.table('florida_parcels').select('county').execute()
        county_counts = {}
        
        if counties.data:
            unique_counties = set(row['county'] for row in counties.data if row.get('county'))
            
            # Count records for each county (limited sampling)
            for county in list(unique_counties)[:10]:  # Check first 10 counties
                result = client.table('florida_parcels').select('*', count='exact').eq('county', county).limit(0).execute()
                count = result.count if hasattr(result, 'count') else 0
                if count > 0:
                    county_counts[county] = count
            
            # Sort and display
            sorted_counties = sorted(county_counts.items(), key=lambda x: x[1], reverse=True)
            for county, count in sorted_counties[:5]:
                print(f"   {county}: {count:,} records")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 5. Recent inserts
    print("5. RECENT INSERT ACTIVITY (Last 10 records):")
    print("-" * 40)
    try:
        recent = client.table('florida_parcels').select(
            'parcel_id,county,owner_name,phy_addr1,import_date'
        ).order('import_date', desc=True).limit(10).execute()
        
        if recent.data:
            for row in recent.data[:5]:
                print(f"   {row.get('county', 'N/A')}: {row.get('parcel_id', 'N/A')} - {row.get('owner_name', 'N/A')[:30]}")
                print(f"      Address: {row.get('phy_addr1', 'N/A')[:40]}")
                print(f"      Import: {row.get('import_date', 'N/A')}")
        else:
            print("   No recent records found")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 6. Data quality check
    print("6. DATA QUALITY CHECK:")
    print("-" * 40)
    try:
        # Check for nulls in critical fields
        sample = client.table('florida_parcels').select(
            'parcel_id,county,owner_name,phy_addr1,just_value,land_value'
        ).limit(100).execute()
        
        if sample.data:
            null_counts = {
                'parcel_id': 0,
                'county': 0,
                'owner_name': 0,
                'phy_addr1': 0,
                'just_value': 0,
                'land_value': 0
            }
            
            for row in sample.data:
                for field in null_counts:
                    if not row.get(field):
                        null_counts[field] += 1
            
            print(f"   Sample of {len(sample.data)} records:")
            for field, count in null_counts.items():
                fill_rate = ((len(sample.data) - count) / len(sample.data)) * 100
                print(f"   {field}: {fill_rate:.1f}% filled")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 60)
    print("RECOMMENDATIONS:")
    print("-" * 40)
    print("1. If upload is slow, increase batch size to 5000")
    print("2. Consider adding sale_year column for year-only data")
    print("3. Add indexes after bulk load completes for better performance")
    print("4. Monitor import_date to track upload progress")

if __name__ == "__main__":
    run_verification()