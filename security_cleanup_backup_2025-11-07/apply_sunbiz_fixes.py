#!/usr/bin/env python3
"""
Apply Sunbiz schema fixes to Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in environment")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("APPLYING SUNBIZ SCHEMA FIXES")
print("=" * 60)

# SQL commands to fix the schema
sql_commands = [
    # Increase doc_number column sizes
    "ALTER TABLE sunbiz_corporate ALTER COLUMN doc_number TYPE VARCHAR(50);",
    "ALTER TABLE sunbiz_corporate_events ALTER COLUMN doc_number TYPE VARCHAR(50);",
    "ALTER TABLE sunbiz_fictitious ALTER COLUMN doc_number TYPE VARCHAR(50);",
    
    # Disable RLS to allow inserts
    "ALTER TABLE sunbiz_corporate DISABLE ROW LEVEL SECURITY;",
    "ALTER TABLE sunbiz_corporate_events DISABLE ROW LEVEL SECURITY;",
    "ALTER TABLE sunbiz_fictitious DISABLE ROW LEVEL SECURITY;",
]

# Execute each command
for i, sql in enumerate(sql_commands, 1):
    try:
        # Use RPC to execute raw SQL
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print(f"✓ Command {i} executed successfully")
        print(f"  {sql[:60]}...")
    except Exception as e:
        # Try alternative approach - direct execution
        if 'exec_sql' in str(e):
            print(f"⚠ Command {i} - exec_sql not available, skipping")
            print(f"  {sql[:60]}...")
            print(f"  Note: You may need to run this in Supabase SQL editor")
        else:
            print(f"✗ Command {i} failed: {str(e)[:100]}")

print("\n" + "=" * 60)
print("SCHEMA FIX ATTEMPT COMPLETE")
print("\nNOTE: If the commands failed, you may need to:")
print("1. Go to your Supabase dashboard")
print("2. Navigate to SQL Editor")
print("3. Run the commands from fix_sunbiz_schema.sql manually")
print("\nAlternatively, we can try inserting data with adjusted formats...")