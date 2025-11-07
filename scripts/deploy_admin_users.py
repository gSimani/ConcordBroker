"""
Deploy Admin Users Table to Supabase
Creates the admin_users table for managing administrative access
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment
load_dotenv('.env.mcp')

# Get database connection parameters
SUPABASE_HOST = os.getenv('SUPABASE_HOST', 'aws-1-us-east-1.pooler.supabase.com')
SUPABASE_USER = os.getenv('SUPABASE_USER', 'postgres.pmispwtdngkcmsrsjwbp')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD', 'West@Boca613!')
SUPABASE_DB = os.getenv('SUPABASE_DB', 'postgres')
SUPABASE_PORT = os.getenv('SUPABASE_PORT', '5432')

# URL-encode password to handle special characters
encoded_password = quote_plus(SUPABASE_PASSWORD)

# Build connection string
DATABASE_URL = f"postgres://{SUPABASE_USER}:{encoded_password}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB}"

# Migration file
MIGRATION_FILE = Path(__file__).parent.parent / 'supabase' / 'migrations' / '20251106_create_admin_users.sql'


def deploy_migration():
    """Deploy the admin_users migration"""

    print("=" * 80)
    print("DEPLOYING ADMIN USERS TABLE TO SUPABASE")
    print("=" * 80)

    # Check if migration file exists
    if not MIGRATION_FILE.exists():
        print(f"\n[ERROR] Migration file not found: {MIGRATION_FILE}")
        return False

    print(f"\n[FILE] Migration file: {MIGRATION_FILE}")
    print(f"[DB] Database: {SUPABASE_HOST}")

    # Read migration file
    with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    print(f"\n[INFO] Migration size: {len(migration_sql)} bytes")

    # Connect to database
    print("\n[INFO] Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()

        print("[SUCCESS] Connected successfully")

        # Execute migration
        print("\n[INFO] Deploying migration...")

        try:
            cursor.execute(migration_sql)
            conn.commit()

            print("\n[SUCCESS] Migration deployed successfully!")

            # Verify table was created
            print("\n[INFO] Verifying admin_users table...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'admin_users'
                ORDER BY ordinal_position;
            """)

            columns = cursor.fetchall()
            if columns:
                print(f"\n[TABLE] admin_users table columns ({len(columns)}):")
                for col in columns:
                    nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                    print(f"   [OK] {col[0]:<20} {col[1]:<20} {nullable}")
            else:
                print("\n[ERROR] admin_users table not found!")
                return False

            # Check RLS policies
            print("\n[INFO] Verifying RLS policies...")
            cursor.execute("""
                SELECT policyname, permissive
                FROM pg_policies
                WHERE tablename = 'admin_users';
            """)

            policies = cursor.fetchall()
            if policies:
                print(f"\n[SECURITY] RLS policies ({len(policies)}):")
                for policy in policies:
                    perm = "PERMISSIVE" if policy[1] == 'PERMISSIVE' else "RESTRICTIVE"
                    print(f"   [OK] {policy[0]} ({perm})")

            # Check indexes
            print("\n[INFO] Verifying indexes...")
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'admin_users'
                AND schemaname = 'public';
            """)

            indexes = cursor.fetchall()
            if indexes:
                print(f"\n[INDEX] Indexes ({len(indexes)}):")
                for idx in indexes:
                    print(f"   [OK] {idx[0]}")

            cursor.close()
            conn.close()

            print("\n" + "=" * 80)
            print("[SUCCESS] DEPLOYMENT COMPLETE!")
            print("=" * 80)
            print("\nYou can now:")
            print("  1. Navigate to /admin/users in your web app")
            print("  2. Create the first admin user (no login required)")
            print("  3. Log in and manage additional users")
            print("\n")

            return True

        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR] Error executing migration: {e}")
            return False

    except Exception as e:
        print(f"\n[ERROR] Error connecting to database: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that SUPABASE_URL and POSTGRES_PASSWORD are set in .env.mcp")
        print(f"  2. Verify database is accessible at: {SUPABASE_HOST}")
        print("  3. Check that the PostgreSQL connection is allowed in Supabase settings")
        return False


if __name__ == '__main__':
    success = deploy_migration()
    sys.exit(0 if success else 1)
