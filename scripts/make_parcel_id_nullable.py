"""
Make parcel_id nullable in tax_deed_bidding_items table
This allows past auction summaries without individual parcel IDs
"""

import os
import sys
from dotenv import dotenv_values
from supabase import create_client, Client

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment from .env.mcp
env_values = dotenv_values('.env.mcp')

SUPABASE_URL = env_values.get('SUPABASE_URL')
SERVICE_ROLE_KEY = env_values.get('SUPABASE_SERVICE_ROLE_KEY')

print("="*80)
print("MAKING PARCEL_ID NULLABLE IN TAX_DEED_BIDDING_ITEMS")
print("="*80)

print(f"\nSUPABASE_URL: {SUPABASE_URL}")
print(f"Using SERVICE_ROLE_KEY (first 30 chars): {SERVICE_ROLE_KEY[:30]}...")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

# Execute ALTER TABLE statement
sql = """
ALTER TABLE tax_deed_bidding_items
ALTER COLUMN parcel_id DROP NOT NULL;
"""

print(f"\nExecuting SQL:")
print(sql)

try:
    # Execute via RPC (if available) or direct SQL
    result = supabase.rpc('execute_sql', {'query': sql}).execute()

    print("\n✅ SUCCESS! parcel_id is now nullable")

except Exception as e:
    print(f"\n⚠️  Note: {e}")
    print("\nTrying alternative approach via PostgREST...")

    # Try to verify the change by checking column info
    try:
        # Query information_schema to verify
        verify_sql = """
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'tax_deed_bidding_items'
        AND column_name = 'parcel_id';
        """

        print(f"\nVerification query:")
        print(verify_sql)
        print("\nPlease execute the ALTER TABLE statement manually in Supabase SQL Editor:")
        print(sql)

    except Exception as e2:
        print(f"\nVerification error: {e2}")

print("\n" + "="*80)
print("NEXT STEP: Upload BROWARD data")
print("="*80)
print("Run: python scripts/upload_tax_deed_fixed_env.py")
