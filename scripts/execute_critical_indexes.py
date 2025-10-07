"""
Execute Critical Database Indexes
Runs the SQL directly via psycopg2 to add performance indexes
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load environment
env_path = Path(__file__).parent.parent / '.env.mcp'
load_dotenv(env_path, override=True)

# Get connection string from Supabase URL
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL not found")
    sys.exit(1)

# Parse Supabase URL to get connection details
# Format: https://PROJECT_ID.supabase.co
project_id = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

# Construct PostgreSQL connection string
# Supabase uses port 6543 for direct PostgreSQL connections
conn_string = f"postgresql://postgres.{project_id}:{SUPABASE_SERVICE_ROLE_KEY}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

print("=" * 80)
print("EXECUTING CRITICAL PERFORMANCE INDEXES")
print("=" * 80)

# Read SQL file
sql_file = Path(__file__).parent.parent / 'supabase' / 'migrations' / 'add_critical_indexes.sql'
if not sql_file.exists():
    print(f"❌ Error: SQL file not found at {sql_file}")
    sys.exit(1)

with open(sql_file, 'r') as f:
    sql_content = f.read()

print(f"\nRead {len(sql_content)} characters from SQL file")
print(f"Connecting to Supabase...")

try:
    # Connect to database
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True  # CONCURRENTLY requires autocommit
    cursor = conn.cursor()

    print("Connected successfully")
    print("\nExecuting index creation SQL...")
    print("This may take 5-15 minutes for large tables...\n")

    # Execute the SQL
    cursor.execute(sql_content)

    print("\nIndex creation completed successfully!")

    # Get index info
    cursor.execute("""
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename IN ('florida_parcels', 'florida_entities')
        AND schemaname = 'public'
        ORDER BY tablename, indexname;
    """)

    indexes = cursor.fetchall()

    print(f"\nTotal indexes on florida_parcels and florida_entities: {len(indexes)}")
    print("\nIndexes created:")
    for idx in indexes:
        print(f"  - {idx[2]} on {idx[1]}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("SUCCESS - INDEXES ADDED")
    print("=" * 80)
    print("""
Expected performance improvements:
- Property search: 10-100x faster
- Property detail pages: 5-20x faster
- Filter operations: 50-200x faster
- Owner/address searches: 20-50x faster
""")

except Exception as e:
    print(f"\n❌ Error executing indexes: {e}")
    print("\nFallback: Please run the SQL manually in Supabase SQL Editor:")
    print(f"1. Go to: https://supabase.com/dashboard/project/{project_id}")
    print("2. Click 'SQL Editor'")
    print(f"3. Open file: {sql_file}")
    print("4. Click 'Run'")
    sys.exit(1)
