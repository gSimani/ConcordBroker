import os
from supabase import create_client

SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\nListing all tables in Supabase:\n")
print("=" * 80)

# Use SQL to list tables
try:
    result = supabase.rpc('exec_sql', {
        'query': "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    }).execute()
    print(f"Tables found: {result.data}")
except Exception as e:
    print(f"ERROR with RPC: {e}")
    print("\nTrying direct table access...")
    
    # Try accessing common table names
    tables_to_try = [
        'properties', 'property', 'parcels', 'parcel', 
        'florida_properties', 'fl_parcels', 'nal', 'nap', 'nav',
        'sales', 'sales_history', 'sdf'
    ]
    
    for table in tables_to_try:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            if result.data:
                print(f"\n✓ Table '{table}' exists - Sample fields:")
                if len(result.data) > 0:
                    fields = list(result.data[0].keys())[:10]
                    print(f"  {', '.join(fields)}...")
        except Exception as e:
            if '42P01' not in str(e):
                print(f"\n✗ Table '{table}' error: {e}")

print("\n" + "=" * 80)
