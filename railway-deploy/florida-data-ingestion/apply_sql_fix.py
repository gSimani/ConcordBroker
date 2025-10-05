"""
Apply SQL fixes directly to Supabase database
Uses psycopg2 to execute SQL that Supabase REST API doesn't support
"""
import psycopg2
import os

# Supabase connection details
# Format: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SUPABASE_DB_URL = "postgresql://postgres.pmispwtdngkcmsrsjwbp:[YOUR_DB_PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

print("=== Applying SQL Fixes to Supabase ===\n")

# Read SQL fix
with open('FIX_UPSERT_FUNCTION.sql', 'r') as f:
    sql = f.read()

# Split into individual statements (removing comments and test queries)
statements = []
current_statement = []

for line in sql.split('\n'):
    # Skip comments
    if line.strip().startswith('--'):
        continue

    # Skip test queries at the end
    if 'SELECT * FROM upsert_nal_to_core' in line or '\\df' in line:
        continue

    current_statement.append(line)

    # Check if statement is complete
    if line.strip().endswith(';'):
        stmt = '\n'.join(current_statement).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
        current_statement = []

print(f"Found {len(statements)} SQL statements to execute\n")

# Connect and execute
try:
    print("Connecting to Supabase database...")
    print(f"NOTE: You need to set the database password in this script")
    print(f"Get it from: Supabase Dashboard > Settings > Database > Connection String")
    print(f"\nIf you don't have direct database access, run this in Supabase SQL Editor instead.\n")

    # Uncomment this when you have the password
    # conn = psycopg2.connect(SUPABASE_DB_URL)
    # cur = conn.cursor()
    #
    # for i, stmt in enumerate(statements, 1):
    #     print(f"Executing statement {i}/{len(statements)}...")
    #     cur.execute(stmt)
    #     conn.commit()
    #     print(f"  ✓ Success")
    #
    # cur.close()
    # conn.close()
    # print("\n✅ All SQL fixes applied successfully!")

    print("ALTERNATIVE: Copy and paste FIX_UPSERT_FUNCTION.sql into Supabase SQL Editor")
    print("URL: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql")

except Exception as e:
    print(f"❌ Error: {e}")
