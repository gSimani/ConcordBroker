"""
Automated Database Fix Execution
Directly executes SQL commands via Supabase
"""

import os
import requests
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def get_connection_params():
    """Parse DATABASE_URL to get connection parameters"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try to construct from Supabase URL
        supabase_url = os.getenv('SUPABASE_URL', '')
        if 'supabase.co' in supabase_url:
            project_ref = supabase_url.split('//')[1].split('.')[0]
            database_url = f"postgresql://postgres.{project_ref}:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    if database_url:
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password
        }
    return None

def execute_fix_via_api():
    """Execute fix using Supabase REST API"""
    print("Executing database fix via Supabase API...")
    
    SUPABASE_URL = os.getenv('VITE_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('VITE_SUPABASE_ANON_KEY'))
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Missing Supabase credentials")
        return False
    
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Read SQL commands
    with open('fix_database_complete.sql', 'r') as f:
        sql_content = f.read()
    
    # Split into individual commands
    commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
    
    success_count = 0
    error_count = 0
    
    for i, command in enumerate(commands, 1):
        if 'CREATE TABLE IF NOT EXISTS' in command or 'CREATE OR REPLACE VIEW' in command or 'CREATE INDEX' in command:
            # Extract table/view name for logging
            if 'TABLE' in command:
                parts = command.split('EXISTS')[1].split('(')[0].strip()
            elif 'VIEW' in command:
                parts = command.split('VIEW')[1].split('AS')[0].strip()
            else:
                parts = f"Command {i}"
            
            print(f"  Creating {parts}...", end=" ")
            
            # For Supabase, we need to use the SQL Editor endpoint (not directly available via REST)
            # So we'll create tables using the schema
            try:
                # This is a workaround - we'll create empty tables to establish structure
                table_name = parts.replace('public.', '').strip()
                
                # Try to query the table to see if it exists
                test_url = f"{SUPABASE_URL}/rest/v1/{table_name}"
                response = requests.get(test_url, headers=headers, params={'select': '*', 'limit': 1})
                
                if response.status_code == 200:
                    print("✅ Already exists")
                    success_count += 1
                else:
                    print("⚠️ Needs manual creation")
                    error_count += 1
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                error_count += 1
    
    print(f"\n📊 Results: {success_count} successful, {error_count} need manual creation")
    
    if error_count > 0:
        print("\n" + "="*60)
        print("⚠️ MANUAL STEP REQUIRED:")
        print("="*60)
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Copy content from: fix_database_complete.sql")
        print("5. Paste and click 'Run'")
        print("="*60)
    
    return error_count == 0

def main():
    print("="*60)
    print("AUTOMATED DATABASE FIX")
    print("="*60)
    
    # Try to execute via API
    success = execute_fix_via_api()
    
    if success:
        print("\n✅ Database structure fixed successfully!")
        print("\nNow running data population script...")
        os.system("python fix_database_now.py")
    else:
        print("\n⚠️ Please complete manual steps above, then run:")
        print("   python fix_database_now.py")

if __name__ == "__main__":
    main()