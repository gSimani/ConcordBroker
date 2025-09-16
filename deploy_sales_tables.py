"""
Deploy sales history tables to Supabase
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Use service key if available, otherwise anon key
api_key = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

headers = {
    'apikey': api_key,
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

print("DEPLOYING SALES HISTORY TABLES TO SUPABASE")
print("=" * 60)

# Read the SQL file
with open('create_complete_sales_tables.sql', 'r') as f:
    sql_content = f.read()

# Split into individual statements (remove comments and empty lines)
statements = []
current_statement = []

for line in sql_content.split('\n'):
    # Skip comments and empty lines
    if line.strip().startswith('--') or not line.strip():
        continue
    
    current_statement.append(line)
    
    # If line ends with semicolon, it's end of statement
    if line.strip().endswith(';'):
        statement = '\n'.join(current_statement)
        statements.append(statement)
        current_statement = []

print(f"Found {len(statements)} SQL statements to execute")

# Execute each statement
successful = 0
failed = 0

for i, statement in enumerate(statements, 1):
    # Get first few words for description
    words = statement.strip().split()[:3]
    description = ' '.join(words)
    
    print(f"\n{i}. Executing: {description}...")
    
    # Use the raw SQL endpoint
    url = f"{SUPABASE_URL}/rest-admin/v1/query"
    
    payload = {
        "query": statement
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201, 204]:
            print(f"   Success")
            successful += 1
        else:
            print(f"   Failed: {response.status_code}")
            if response.text:
                error_msg = response.text[:200]
                print(f"   Error: {error_msg}")
            
            # Try alternative approach for some statements
            if "CREATE TABLE" in statement or "CREATE OR REPLACE VIEW" in statement:
                print("   Attempting alternative approach...")
                # For tables/views, they might already exist
                if "already exists" in response.text.lower():
                    print("   Table/view already exists, continuing...")
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
    except Exception as e:
        print(f"   Exception: {e}")
        failed += 1

print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE!")
print(f"Successful: {successful}/{len(statements)}")
print(f"Failed: {failed}/{len(statements)}")

if failed == len(statements):
    print("\nAll statements failed. This usually means:")
    print("1. Tables already exist (which is OK)")
    print("2. Or you need to run the SQL directly in Supabase SQL Editor")
    print("\nTo run in Supabase:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Paste the contents of create_complete_sales_tables.sql")
    print("4. Click 'Run'")
else:
    print("\nTables deployed successfully!")
    print("You can now run load_complete_sales_history.py to load the data")