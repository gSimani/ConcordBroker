"""
Deploy the Sunbiz officer contacts table to Supabase (safe, env-driven).

Requires:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY (preferred) or SUPABASE_ANON_KEY
- SUPABASE_ENABLE_SQL=true (only if you have a vetted execute_sql RPC)
"""
import os
import sys
from pathlib import Path
from supabase import create_client


def deploy_contacts_table():
    print("=" * 60)
    print("DEPLOYING SUNBIZ OFFICER CONTACTS TABLE")
    print("=" * 60)

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        return False

    if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
        print("Direct SQL execution is disabled.")
        print("Recommended: run the SQL file via Supabase dashboard or psql with admin credentials.")
        return False

    supabase = create_client(supabase_url, supabase_key)
    sql_file = Path("create_sunbiz_officer_contacts_table.sql")
    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        return False

    sql_content = sql_file.read_text(encoding='utf-8')
    print(f"Loaded SQL from {sql_file}")
    print(f"SQL length: {len(sql_content)} characters")

    try:
        print("\nExecuting table creation via RPC 'execute_sql'...")
        supabase.rpc('execute_sql', {'sql_query': sql_content}).execute()
        print("Table creation executed successfully")

        print("\nVerifying table creation...")
        supabase.table('sunbiz_officer_contacts').select('*').limit(0).execute()
        print("Table verification successful")
        return True
    except Exception as e:
        print(f"Error creating table: {e}")
        return False


if __name__ == "__main__":
    ok = deploy_contacts_table()
    sys.exit(0 if ok else 1)

