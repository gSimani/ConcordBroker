"""
DEPLOY MISSING TABLES TO SUPABASE
This script reads the SQL schema and executes it in Supabase
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Use service key if available, otherwise use anon key
API_KEY = SUPABASE_SERVICE_KEY if SUPABASE_SERVICE_KEY else SUPABASE_ANON_KEY

if not SUPABASE_URL or not API_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

print("=" * 80)
print("DEPLOYING MISSING TABLES TO SUPABASE")
print(f"Timestamp: {datetime.now()}")
print("=" * 80)

# Read the SQL schema file
schema_file = 'create_all_missing_tables.sql'
if not os.path.exists(schema_file):
    print(f"ERROR: Schema file '{schema_file}' not found!")
    exit(1)

with open(schema_file, 'r') as f:
    sql_content = f.read()

# Split SQL into individual statements
# Remove comments and empty lines
sql_statements = []
current_statement = []

for line in sql_content.split('\n'):
    # Skip comment lines
    if line.strip().startswith('--') or not line.strip():
        continue
    
    current_statement.append(line)
    
    # If line ends with semicolon, we have a complete statement
    if line.strip().endswith(';'):
        statement = '\n'.join(current_statement).strip()
        if statement:
            sql_statements.append(statement)
        current_statement = []

print(f"\nFound {len(sql_statements)} SQL statements to execute")

# Execute SQL via Supabase REST API
# Note: Direct SQL execution requires using the Supabase Dashboard or CLI
# We'll create tables using the REST API instead

headers = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

print("\nIMPORTANT: Direct SQL execution via API is limited.")
print("For best results, please:")
print("1. Go to your Supabase Dashboard")
print("2. Navigate to SQL Editor")
print("3. Copy and paste the contents of 'create_all_missing_tables.sql'")
print("4. Click 'Run' to execute all statements")
print("\nAlternatively, you can use the Supabase CLI:")
print("supabase db push create_all_missing_tables.sql")

# Check if some critical tables exist
print("\n" + "=" * 60)
print("CHECKING CRITICAL TABLES STATUS")
print("=" * 60)

critical_tables = [
    'properties',
    'broward_parcels',
    'property_sales_history',
    'florida_permits',
    'property_tax_records',
    'foreclosure_cases',
    'tax_deed_sales',
    'tax_liens',
    'investment_analysis'
]

tables_exist = []
tables_missing = []

for table in critical_tables:
    url = f'{SUPABASE_URL}/rest/v1/{table}?select=count'
    response = requests.head(url, headers=headers)
    
    if response.status_code == 404:
        tables_missing.append(table)
        print(f"X {table}: NOT FOUND")
    elif response.status_code in [200, 206]:
        tables_exist.append(table)
        print(f"OK {table}: EXISTS")
    else:
        print(f"? {table}: Unknown status ({response.status_code})")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Tables that exist: {len(tables_exist)}/{len(critical_tables)}")
print(f"Tables missing: {len(tables_missing)}/{len(critical_tables)}")

if tables_missing:
    print("\nMissing tables:")
    for table in tables_missing:
        print(f"  - {table}")
    
    print("\nACTION REQUIRED:")
    print("Please run the SQL schema in Supabase to create these tables.")
    print("\nFile to run: create_all_missing_tables.sql")
else:
    print("\nAll critical tables exist! You can now load data.")

# Save instructions for manual execution
instructions_file = 'DEPLOY_INSTRUCTIONS.txt'
with open(instructions_file, 'w') as f:
    f.write("SUPABASE TABLE DEPLOYMENT INSTRUCTIONS\n")
    f.write("=" * 60 + "\n\n")
    f.write("To create the missing tables:\n\n")
    f.write("OPTION 1: Supabase Dashboard (Recommended)\n")
    f.write("-" * 40 + "\n")
    f.write("1. Go to your Supabase project dashboard\n")
    f.write("2. Click on 'SQL Editor' in the left sidebar\n")
    f.write("3. Click 'New Query'\n")
    f.write("4. Copy the entire contents of 'create_all_missing_tables.sql'\n")
    f.write("5. Paste into the SQL editor\n")
    f.write("6. Click 'Run' button\n")
    f.write("7. Wait for all tables to be created\n\n")
    
    f.write("OPTION 2: Supabase CLI\n")
    f.write("-" * 40 + "\n")
    f.write("1. Install Supabase CLI if not already installed\n")
    f.write("2. Run: supabase link --project-ref <your-project-ref>\n")
    f.write("3. Run: supabase db push create_all_missing_tables.sql\n\n")
    
    f.write("AFTER DEPLOYMENT:\n")
    f.write("-" * 40 + "\n")
    f.write("1. Run: python comprehensive_database_audit.py\n")
    f.write("   To verify all tables were created\n")
    f.write("2. Run the data loading scripts to populate tables\n")
    f.write("3. Check the web interface to confirm tabs show real data\n")

print(f"\nInstructions saved to: {instructions_file}")
print("\nPlease follow the instructions to complete table deployment.")