import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

# Get one record to see what columns exist
result = supabase.table('florida_parcels').select('*').limit(1).execute()

if result.data and len(result.data) > 0:
    columns = list(result.data[0].keys())
    print("Available columns in florida_parcels table:")
    print("=" * 60)
    for col in sorted(columns):
        print(f"  - {col}")
    print(f"\nTotal columns: {len(columns)}")
else:
    print("No data found in florida_parcels table")
