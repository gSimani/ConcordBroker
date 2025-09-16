"""
Check total property counts in Supabase
"""

from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Create Supabase client with correct credentials"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
    return create_client(url, key)

def check_property_counts():
    """Check property counts in the database"""
    client = get_supabase_client()
    
    print("=" * 60)
    print("PROPERTY COUNT ANALYSIS")
    print("=" * 60)
    
    # 1. Total visible properties (non-redacted)
    try:
        result = client.table('florida_parcels')\
            .select('*', count='exact')\
            .or_('is_redacted.eq.false,is_redacted.is.null')\
            .limit(0)\
            .execute()
        
        visible_count = result.count if hasattr(result, 'count') else 'N/A'
        print(f"\n1. Total VISIBLE properties (non-redacted): {visible_count:,}")
    except Exception as e:
        print(f"Error checking visible properties: {e}")
        visible_count = 0
    
    # 2. Total raw rows
    try:
        result = client.table('florida_parcels')\
            .select('*', count='exact')\
            .limit(0)\
            .execute()
        
        total_count = result.count if hasattr(result, 'count') else 'N/A'
        print(f"2. Total RAW rows in database: {total_count:,}")
    except Exception as e:
        print(f"Error checking total rows: {e}")
        total_count = 0
    
    # 3. County breakdown (top counties)
    print("\n3. County Breakdown (top 10 counties by property count):")
    try:
        # Get distinct counties with counts
        counties = client.table('florida_parcels')\
            .select('co_no')\
            .or_('is_redacted.eq.false,is_redacted.is.null')\
            .execute()
        
        if counties.data:
            from collections import Counter
            county_counts = Counter(row['co_no'] for row in counties.data if row.get('co_no'))
            
            # Map county codes to names (common Florida counties)
            county_names = {
                '06': 'Broward',
                '11': 'Dade (Miami-Dade)',
                '50': 'Palm Beach',
                '48': 'Orange',
                '29': 'Hillsborough',
                '52': 'Pinellas',
                '16': 'Duval',
                '53': 'Polk',
                '12': 'DeSoto',
                '10': 'Collier'
            }
            
            print(f"{'County':20} {'Code':6} {'Properties':>12}")
            print("-" * 40)
            for county_code, count in county_counts.most_common(10):
                county_name = county_names.get(county_code, f'County {county_code}')
                print(f"{county_name:20} {county_code:6} {count:12,}")
    except Exception as e:
        print(f"Error getting county breakdown: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Properties visible in app: {visible_count:,}")
    print(f"Total database rows: {total_count:,}")
    if isinstance(visible_count, int) and isinstance(total_count, int) and total_count > 0:
        print(f"Visibility rate: {(visible_count/total_count)*100:.1f}%")

if __name__ == "__main__":
    check_property_counts()