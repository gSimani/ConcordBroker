"""
Check exact columns in florida_parcels table
"""

from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    return create_client(url, key)

def check_columns():
    """Check existing columns in florida_parcels"""
    client = get_supabase_client()
    
    print("Checking florida_parcels table structure...")
    print("=" * 60)
    
    # Get one record to see the columns
    try:
        result = client.table('florida_parcels').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            columns = list(result.data[0].keys())
            print(f"Found {len(columns)} columns in florida_parcels:")
            print("-" * 60)
            for col in sorted(columns):
                value = result.data[0][col]
                if value is not None:
                    print(f"  {col}: {type(value).__name__} (sample: {str(value)[:50]})")
                else:
                    print(f"  {col}: null")
        else:
            print("No data found in table, trying to get schema...")
            # Try an insert with empty data to trigger an error that shows columns
            try:
                client.table('florida_parcels').insert({}).execute()
            except Exception as e:
                print(f"Schema error: {str(e)}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()