"""
Monitor upload progress
"""

import time
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
    return create_client(url, key)

def monitor():
    """Monitor upload progress"""
    client = get_supabase_client()
    
    print("Monitoring upload progress...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    last_count = 0
    
    while True:
        try:
            # Get current count
            result = client.table('florida_parcels').select('*', count='exact').limit(0).execute()
            current_count = result.count if hasattr(result, 'count') else 0
            
            # Calculate new records
            new_records = current_count - last_count
            
            # Display status
            print(f"\rTotal records: {current_count:,} | New: +{new_records:,}", end='', flush=True)
            
            last_count = current_count
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()