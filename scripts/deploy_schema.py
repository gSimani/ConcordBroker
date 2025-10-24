"""
Deploy Database Schema to Supabase
Deploys the daily update schema including all tables, indexes, functions, and RLS policies
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment
load_dotenv('.env.mcp')

# Get database connection string
# Format: postgres://postgres.{project_ref}:{password}@{host}:5432/postgres

SUPABASE_URL = os.getenv('SUPABASE_URL')  # https://xxx.supabase.co
SUPABASE_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'West@Boca613!')

# Extract project ref from SUPABASE_URL to build PostgreSQL host
# Format: https://mogulpssjdlxjvstqfee.supabase.co -> db.mogulpssjdlxjvstqfee.supabase.co
if SUPABASE_URL:
    project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
    SUPABASE_HOST = os.getenv('POSTGRES_HOST', f'db.{project_ref}.supabase.co')
else:
    SUPABASE_HOST = os.getenv('POSTGRES_HOST', 'db.pmispwtdngkcmsrsjwbp.supabase.co')

# URL-encode password to handle special characters like @
encoded_password = quote_plus(SUPABASE_PASSWORD)

# Build connection string
DATABASE_URL = f"postgres://postgres:{encoded_password}@{SUPABASE_HOST}:5432/postgres"

# Schema file
SCHEMA_FILE = Path(__file__).parent.parent / 'supabase' / 'migrations' / 'daily_update_schema.sql'


def deploy_schema():
    """Deploy the database schema"""

    print("=" * 80)
    print("DEPLOYING DAILY UPDATE SCHEMA TO SUPABASE")
    print("=" * 80)

    # Check if schema file exists
    if not SCHEMA_FILE.exists():
        print(f"\n❌ Schema file not found: {SCHEMA_FILE}")
        return False

    print(f"\n📄 Schema file: {SCHEMA_FILE}")
    print(f"🗄️  Database: {SUPABASE_HOST}")

    # Read schema file
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    print(f"\n📊 Schema size: {len(schema_sql)} bytes")

    # Connect to database
    print("\n🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()

        print("✅ Connected successfully")

        # Execute schema
        print("\n🚀 Deploying schema...")
        print("   This may take a minute...")

        try:
            cursor.execute(schema_sql)
            conn.commit()

            print("\n✅ Schema deployed successfully!")

            # Verify tables were created
            print("\n🔍 Verifying tables...")
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()
            print(f"\n📋 Tables created ({len(tables)}):")
            for table in tables:
                print(f"   ✓ {table[0]}")

            # Verify functions
            print("\n🔍 Verifying functions...")
            cursor.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_type = 'FUNCTION'
                ORDER BY routine_name;
            """)

            functions = cursor.fetchall()
            print(f"\n⚙️  Functions created ({len(functions)}):")
            for func in functions:
                print(f"   ✓ {func[0]}")

            # Get row counts
            print("\n📊 Table status:")
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"   {table_name}: {count:,} records")
                except Exception as e:
                    print(f"   {table_name}: Error getting count")

            print("\n" + "=" * 80)
            print("✅ DEPLOYMENT COMPLETE")
            print("=" * 80)

            return True

        except Exception as e:
            conn.rollback()
            print(f"\n❌ Error deploying schema: {e}")
            print("\nRolling back changes...")
            return False

    except Exception as e:
        print(f"\n❌ Database connection error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your database credentials in .env.mcp")
        print("   2. Verify your IP is allowed in Supabase dashboard")
        print("   3. Ensure database is accessible")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("\n🔌 Database connection closed")


def test_connection():
    """Test database connection"""
    print("\n🧪 Testing database connection...")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Get database version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL version: {version.split(',')[0]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    """Main entry point"""

    # Test connection first
    if not test_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)

    # Deploy schema
    success = deploy_schema()

    if success:
        print("\n🎉 Next steps:")
        print("   1. Verify tables in Supabase dashboard")
        print("   2. Test portal access: python scripts/test_portal_access.py")
        print("   3. Download sample county: python scripts/download_county.py --county BROWARD")
        print("   4. Run daily update: python scripts/daily_property_update.py --dry-run")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed - check errors above")
        sys.exit(1)


if __name__ == '__main__':
    main()
