import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.mcp')

# Use the CORRECT database credentials from property_live_api.py
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "REDACTED"

print("Querying actual count from florida_parcels table...")
print(f"Database: {SUPABASE_URL}")
print()

# Override from environment if available
env_url = os.getenv('SUPABASE_URL')
env_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
if env_url:
    SUPABASE_URL = env_url
if env_key:
    SUPABASE_KEY = env_key

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # Get exact count - just need to select with count and limit 0 for performance
    result = supabase.table('florida_parcels').select('parcel_id', count='exact').limit(0).execute()
    actual_count = result.count if hasattr(result, 'count') else 0

    print("="*50)
    print("ACTUAL DATABASE COUNT")
    print("="*50)
    print(f"Total properties in florida_parcels: {actual_count:,}")

    if actual_count > 9000000:
        print("Status: FULL 9.1M DATASET CONFIRMED!")
    elif actual_count > 6000000:
        print("Status: Partial dataset (6.4M)")
    else:
        print(f"Status: Limited dataset")
    print("="*50)

except Exception as e:
    print(f"Error: {e}")

