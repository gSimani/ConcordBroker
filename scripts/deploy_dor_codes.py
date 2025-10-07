"""
Deploy DOR Use Codes to Supabase
This script deploys the Florida Department of Revenue land use codes to your Supabase database
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Create and return a Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_role_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
        sys.exit(1)

    return create_client(url, service_role_key)

def read_sql_file(filepath: str) -> str:
    """Read SQL file content"""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ Error: SQL file not found: {filepath}")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql(client: Client, sql: str, description: str) -> bool:
    """Execute SQL statement"""
    try:
        print(f"🔄 Executing: {description}...")

        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            if statement:
                # Skip comments
                if statement.startswith('--'):
                    continue

                # Execute via Supabase RPC (if you have an execute_sql function)
                # Otherwise, you'll need to run these in the Supabase SQL editor
                print(f"   Statement {i}/{len(statements)}...")

        print(f"✅ Success: {description}")
        return True

    except Exception as e:
        print(f"❌ Error in {description}: {str(e)}")
        return False

def check_table_exists(client: Client) -> bool:
    """Check if DOR use codes table already exists"""
    try:
        result = client.table('dor_use_codes').select('code').limit(1).execute()
        return True
    except:
        return False

def verify_deployment(client: Client) -> bool:
    """Verify that DOR codes were deployed successfully"""
    try:
        # Check if table exists and has data
        result = client.table('dor_use_codes').select('code', count='exact').execute()
        count = len(result.data) if result.data else 0

        if count == 100:
            print(f"✅ Verification successful: {count} DOR codes loaded")

            # Show category breakdown
            categories = {}
            for row in result.data:
                cat = row.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1

            print("\n📊 Category Breakdown:")
            for cat, cnt in sorted(categories.items()):
                print(f"   - {cat}: {cnt} codes")

            return True
        else:
            print(f"⚠️ Warning: Expected 100 codes, found {count}")
            return False

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         DOR Use Codes Deployment to Supabase                  ║
║                                                                ║
║  This will deploy all 100 Florida Department of Revenue       ║
║  land use codes to your Supabase database.                   ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Get Supabase client
    print("🔗 Connecting to Supabase...")
    client = get_supabase_client()
    print("✅ Connected to Supabase")

    # Check if table already exists
    if check_table_exists(client):
        response = input("\n⚠️ DOR use codes table already exists. Recreate? (y/n): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return

    # SQL file paths
    base_path = Path(__file__).parent.parent / 'supabase'
    schema_file = base_path / 'dor_use_codes_schema.sql'
    data_file = base_path / 'dor_use_codes_data.sql'
    relationships_file = base_path / 'dor_use_codes_relationships.sql'

    print(f"\n📁 SQL Files Location: {base_path}")

    # Note: Supabase Python client doesn't support raw SQL execution
    # You need to either:
    # 1. Run these in Supabase SQL editor manually
    # 2. Create an RPC function to execute SQL
    # 3. Use psycopg2 to connect directly to the database

    print("""
╔════════════════════════════════════════════════════════════════╗
║                    MANUAL DEPLOYMENT REQUIRED                  ║
╠════════════════════════════════════════════════════════════════╣
║  The Supabase Python client doesn't support raw SQL execution ║
║  Please run the following SQL files in your Supabase SQL      ║
║  editor in this order:                                        ║
║                                                                ║
║  1. dor_use_codes_schema.sql     - Creates table structure    ║
║  2. dor_use_codes_data.sql       - Inserts all 100 codes     ║
║  3. dor_use_codes_relationships.sql - Adds relationships      ║
║                                                                ║
║  Location: supabase/ folder in project root                   ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Generate combined SQL file for easy copy-paste
    combined_file = base_path / 'dor_use_codes_complete.sql'

    print("\n📝 Generating combined SQL file for easy deployment...")

    try:
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write("-- Combined DOR Use Codes Deployment\n")
            f.write("-- Run this entire file in Supabase SQL editor\n\n")
            f.write("-- Step 1: Schema\n")
            f.write(read_sql_file(str(schema_file)))
            f.write("\n\n-- Step 2: Data\n")
            f.write(read_sql_file(str(data_file)))
            f.write("\n\n-- Step 3: Relationships\n")
            f.write(read_sql_file(str(relationships_file)))

        print(f"✅ Combined SQL file created: {combined_file}")
        print("\n📋 Copy the contents of 'dor_use_codes_complete.sql' and paste")
        print("   into your Supabase SQL editor, then click 'Run'")

    except Exception as e:
        print(f"❌ Error creating combined file: {str(e)}")

    # Provide test queries
    print("""
╔════════════════════════════════════════════════════════════════╗
║                      TEST QUERIES                              ║
╠════════════════════════════════════════════════════════════════╣
║  After deployment, test with these queries:                   ║
║                                                                ║
║  -- Count all codes                                           ║
║  SELECT COUNT(*) FROM dor_use_codes;                         ║
║                                                                ║
║  -- View categories                                           ║
║  SELECT category, COUNT(*) as count                          ║
║  FROM dor_use_codes                                          ║
║  GROUP BY category                                           ║
║  ORDER BY count DESC;                                        ║
║                                                                ║
║  -- Get residential codes                                     ║
║  SELECT * FROM v_dor_residential_codes;                      ║
║                                                                ║
║  -- Test property integration (if florida_parcels exists)    ║
║  SELECT * FROM v_properties_with_dor LIMIT 10;              ║
╚════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()