
import psycopg2
import json
from supabase import create_client, Client

# Load Supabase config
import os
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check florida_parcels table
        result = supabase.table('florida_parcels').select('county', count='exact').execute()
        print(f"Database record count: {result.count if hasattr(result, 'count') else 'Unknown'}")
        
        # Get county breakdown
        counties_in_db = supabase.table('florida_parcels').select('county').execute()
        if counties_in_db.data:
            unique_counties = set(record['county'] for record in counties_in_db.data)
            print(f"Counties in database: {len(unique_counties)}")
            print(f"Counties: {sorted(unique_counties)}")
    except Exception as e:
        print(f"Database check failed: {e}")
else:
    print("Supabase credentials not available for database comparison")
