"""
Monitor Florida Property Appraiser Upload Progress
Shows real-time status of county data uploads using the monitoring view
"""

import time
from datetime import datetime
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def monitor_progress():
    """Monitor upload progress using the monitoring view"""
    client = get_supabase_client()
    
    print("=" * 80)
    print("FLORIDA PROPERTY APPRAISER UPLOAD MONITOR")
    print("=" * 80)
    print(f"Started monitoring at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    while True:
        try:
            # Query the monitoring view
            result = client.table('florida_parcels_ingest_status').select('*').execute()
            
            if result.data:
                # Calculate totals
                total_counties = len(result.data)
                total_records = sum(row['total_rows'] for row in result.data)
                
                # Clear screen (works on Windows)
                print("\033[2J\033[H", end="")
                
                # Display header
                print("=" * 80)
                print("FLORIDA PROPERTY APPRAISER UPLOAD MONITOR")
                print("=" * 80)
                print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Total Counties: {total_counties} | Total Records: {total_records:,}")
                print("-" * 80)
                print(f"{'County':<20} {'Records':<15} {'Has Values':<15} {'Has Owner':<15}")
                print("-" * 80)
                
                # Display county data (top 20)
                for row in sorted(result.data, key=lambda x: x['total_rows'], reverse=True)[:20]:
                    county = row.get('county', 'Unknown')
                    total = row.get('total_rows', 0)
                    has_values = row.get('has_values', 0)
                    has_owner = row.get('has_owner', 0)
                    
                    print(f"{county:<20} {total:<15,} {has_values:<15,} {has_owner:<15,}")
                
                if len(result.data) > 20:
                    print(f"\n... and {len(result.data) - 20} more counties")
                
                print("-" * 80)
                print("Press Ctrl+C to stop monitoring")
                
            else:
                print("No data found in monitoring view yet...")
            
            # Wait 5 seconds before next update
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_progress()