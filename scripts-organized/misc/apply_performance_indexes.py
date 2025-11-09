#!/usr/bin/env python3
"""
Apply Performance Indexes to Supabase Database
Purpose: Fix search timeouts on florida_parcels and other tables
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get direct database connection (not pooled)"""
    # Use non-pooling connection for migrations
    db_url = os.getenv('POSTGRES_URL_NON_POOLING') or os.getenv('DATABASE_URL')

    if not db_url:
        print("❌ Error: POSTGRES_URL_NON_POOLING or DATABASE_URL not found in .env")
        print("   Please add your Supabase connection string to .env file")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)

def run_migration():
    """Run the performance indexes migration"""
    migration_file = Path(__file__).parent / 'supabase' / 'migrations' / 'urgent_performance_indexes.sql'

    if not migration_file.exists():
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)

    print("📋 Reading migration file...")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("🔌 Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🚀 Running index creation...")
        print("   This may take 10-30 minutes depending on table size...")
        print("   You can monitor progress in Supabase Dashboard > Database > Activity\n")

        # Execute the migration
        cursor.execute(sql_content)
        conn.commit()

        print("✅ All indexes created successfully!")
        print("\n📊 Verifying indexes...")

        # Verify indexes
        cursor.execute("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename IN ('florida_parcels', 'florida_entities', 'sunbiz_corporate', 'property_sales_history')
              AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """)

        results = cursor.fetchall()

        if results:
            print(f"\n✅ Found {len(results)} indexes:")
            current_table = None
            for table, index, definition in results:
                if table != current_table:
                    print(f"\n   {table}:")
                    current_table = table
                print(f"     - {index}")
        else:
            print("⚠️  No indexes found (table may not exist yet)")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during migration: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

    print("\n🎉 Migration complete! Search performance should be significantly improved.")

if __name__ == '__main__':
    print("=" * 70)
    print("  URGENT PERFORMANCE INDEXES MIGRATION")
    print("=" * 70)
    print()

    run_migration()
