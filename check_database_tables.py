import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
url = os.getenv('VITE_SUPABASE_URL')
# We need service key to bypass RLS
service_key = os.getenv('VITE_SUPABASE_SERVICE_KEY')
anon_key = os.getenv('VITE_SUPABASE_ANON_KEY')

if not url:
    print("Error: VITE_SUPABASE_URL not found in environment")
    exit(1)

# Try service key first, fall back to anon key
key = service_key or anon_key
if not key:
    print("Error: No Supabase key found in environment")
    exit(1)

print(f"Connecting to Supabase at: {url}")
print(f"Using {'service' if service_key else 'anon'} key")

# Create Supabase client
supabase: Client = create_client(url, key)

# Check what tables exist
try:
    # List all tables we expect
    expected_tables = [
        'florida_parcels',
        'fl_properties', 
        'fl_sdf_sales',
        'fl_nav_assessment_detail',
        'fl_tpp_accounts',
        'sunbiz_corporate_filings'
    ]
    
    print("\nChecking database tables:")
    print("-" * 50)
    
    for table in expected_tables:
        try:
            # Try to count records in each table
            result = supabase.table(table).select('*', count='exact').limit(1).execute()
            count = result.count if hasattr(result, 'count') else len(result.data)
            print(f"✓ {table}: {count} records")
        except Exception as e:
            print(f"✗ {table}: Not found or error - {str(e)[:50]}")
    
    print("\n" + "-" * 50)
    print("\nNeed to create tables and load real data!")
    
except Exception as e:
    print(f"Error checking tables: {e}")