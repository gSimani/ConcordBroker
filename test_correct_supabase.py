"""
Test with the correct Supabase URL from .env.mcp
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# Load environment variables from .env.mcp
load_dotenv(Path('.env.mcp'))

def main():
    # Use the correct URL from .env.mcp
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    print("Testing with CORRECT Supabase URL:")
    print(f"URL: {url}")
    print(f"Anon Key: {'Set' if anon_key else 'Not set'}")
    print(f"Service Key: {'Set' if service_key else 'Not set'}")
    print()

    # Test with service key
    if service_key:
        print("Testing with Service Role Key:")
        try:
            supabase = create_client(url, service_key)

            # List all tables in public schema
            response = supabase.rpc('get_schema_tables').execute()
            print(f"Available tables: {response.data}")

        except Exception as e:
            print(f"Service key test failed: {e}")

            # Try basic info query
            try:
                # Try to get table info from information_schema
                response = supabase.rpc('get_table_info', {}).execute()
                print("Table info retrieved successfully")
            except Exception as e2:
                print(f"Table info failed: {e2}")

                # Try simplest possible query
                try:
                    response = supabase.table('information_schema').select("*").limit(1).execute()
                    print("Information schema accessible")
                except Exception as e3:
                    print(f"Information schema failed: {e3}")

    # Test with anon key
    if anon_key:
        print("\nTesting with Anonymous Key:")
        try:
            supabase = create_client(url, anon_key)

            # Try a simple query
            response = supabase.table('florida_parcels').select("*").limit(1).execute()
            print(f"SUCCESS: Found {len(response.data)} records")

        except Exception as e:
            print(f"Anon key test failed: {e}")

if __name__ == "__main__":
    main()