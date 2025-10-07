import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.mcp')

# Use the CORRECT database credentials from property_live_api.py
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

print("Querying actual count from florida_parcels table...")
print(f"Database: {SUPABASE_URL}")
print()

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