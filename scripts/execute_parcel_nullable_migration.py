"""
Execute migration to make parcel_id nullable
Uses direct PostgREST SQL execution via service role
"""

import os
import sys
import requests
from dotenv import dotenv_values

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment from .env.mcp
env_values = dotenv_values('.env.mcp')

SUPABASE_URL = env_values.get('SUPABASE_URL')
SERVICE_ROLE_KEY = env_values.get('SUPABASE_SERVICE_ROLE_KEY')

print("="*80)
print("EXECUTING MIGRATION: Make parcel_id nullable")
print("="*80)

# Read migration file
migration_path = 'supabase/migrations/20251104_make_parcel_id_nullable.sql'

print(f"\nReading migration: {migration_path}")

with open(migration_path, 'r', encoding='utf-8') as f:
    sql = f.read()

print(f"\nSQL to execute:")
print("-"*80)
print(sql)
print("-"*80)

# Execute via direct PostgreSQL connection through Supabase
# We'll use the REST API to check if we can make this change

headers = {
    'apikey': SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

print(f"\nChecking current table schema...")

# Get current schema info
schema_url = f"{SUPABASE_URL}/rest/v1/tax_deed_bidding_items?limit=0"

try:
    response = requests.get(schema_url, headers=headers)

    if response.status_code == 200:
        print("✅ Table exists and is accessible")

        print(f"\n{'='*80}")
        print("IMPORTANT: Manual execution required")
        print("="*80)
        print("\nPlease execute the following SQL in Supabase SQL Editor:")
        print("\n1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql")
        print("\n2. Copy and paste this SQL:")
        print("-"*80)
        print(sql)
        print("-"*80)

        print("\n3. Click 'Run' to execute")
        print("\n4. Then run: python scripts/upload_tax_deed_fixed_env.py")

        # Save SQL to a file for easy copy-paste
        with open('EXECUTE_THIS_SQL.sql', 'w') as f:
            f.write(sql)

        print(f"\n✅ SQL also saved to: EXECUTE_THIS_SQL.sql (for easy copy-paste)")

    else:
        print(f"❌ Error checking table: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease execute the migration manually in Supabase SQL Editor")
