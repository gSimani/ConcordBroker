#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("Testing Available Tables")
print("=" * 40)

try:
    supabase: Client = create_client(url, key)
    print("[OK] Connected to Supabase")

    # Try some common tables
    test_tables = [
        'properties',
        'tax_deed_sales',
        'florida_parcels',
        'sunbiz_corporations',
        'users',
        'test'
    ]

    for table_name in test_tables:
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            count = len(result.data)
            print(f"[OK] {table_name}: {count} record(s)")
        except Exception as e:
            error_msg = str(e)
            if 'does not exist' in error_msg:
                print(f"[NO] {table_name}: Table doesn't exist")
            else:
                print(f"[ERR] {table_name}: {error_msg}")

except Exception as e:
    print(f"[ERROR] Failed to connect: {e}")