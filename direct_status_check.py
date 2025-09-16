"""
Direct status check - queries the florida_parcels table directly
"""

from datetime import datetime
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_status():
    """Check current upload status directly from florida_parcels table"""
    client = get_supabase_client()
    
    print("=" * 80)
    print("FLORIDA PROPERTY APPRAISER UPLOAD STATUS (DIRECT QUERY)")
    print("=" * 80)
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    try:
        # Get unique counties and their counts
        # Using raw SQL through RPC or getting all data and processing locally
        # Since we don't have an RPC, let's get a sample to see what counties we have
        
        # Get distinct counties (limited query)
        result = client.table('florida_parcels').select('county').limit(10000).execute()
        
        if result.data:
            # Count by county
            county_counts = {}
            for row in result.data:
                county = row.get('county')
                if county:
                    county_counts[county] = county_counts.get(county, 0) + 1
            
            print(f"Sample of counties found (from first 10,000 records):")
            for county, count in sorted(county_counts.items()):
                print(f"  {county}: {count} records")
            
            print("\n" + "-" * 80)
            print("NOTE: This is a limited sample. Full counts require the monitoring view.")
            
            # Try to get total count
            try:
                # Get count for each county one by one (for top counties)
                print("\nGetting exact counts for uploaded counties...")
                for county in sorted(county_counts.keys())[:5]:  # Just check first 5
                    count_result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
                    if hasattr(count_result, 'count'):
                        print(f"  {county}: {count_result.count:,} total records")
            except:
                pass
            
        else:
            print("No data found in florida_parcels table")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()