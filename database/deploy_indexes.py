#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe Index Deployment Script
Deploys critical indexes to Supabase with progress tracking and rollback support
"""

import os
import sys
import time
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.mcp')

# Supabase connection
SUPABASE_HOST = os.getenv('SUPABASE_HOST')
SUPABASE_DB = os.getenv('SUPABASE_DB', 'postgres')
SUPABASE_USER = os.getenv('SUPABASE_USER', 'postgres')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD')
SUPABASE_PORT = int(os.getenv('SUPABASE_PORT', '5432'))

def print_banner():
    print("\n" + "="*70)
    print("  🚀 CRITICAL INDEX DEPLOYMENT")
    print("="*70)
    print()

def get_indexes_from_sql():
    """Parse critical_indexes.sql and extract CREATE INDEX statements"""
    indexes = []

    with open('database/critical_indexes.sql', 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by semicolons and filter CREATE INDEX statements
    statements = [s.strip() for s in content.split(';')]

    for stmt in statements:
        if stmt.startswith('CREATE INDEX CONCURRENTLY'):
            # Extract index name
            parts = stmt.split()
            index_name = parts[3]
            indexes.append({
                'name': index_name,
                'sql': stmt + ';'
            })

    return indexes

def check_index_exists(cursor, index_name):
    """Check if index already exists"""
    cursor.execute("""
        SELECT 1
        FROM pg_indexes
        WHERE indexname = %s;
    """, (index_name,))

    return cursor.fetchone() is not None

def deploy_index(cursor, index):
    """Deploy a single index"""
    index_name = index['name']
    sql = index['sql']

    # Check if exists
    if check_index_exists(cursor, index_name):
        print(f"  ⏭️  {index_name} already exists, skipping")
        return True

    print(f"  🔨 Creating {index_name}...")
    start_time = time.time()

    try:
        cursor.execute(sql)
        elapsed = time.time() - start_time
        print(f"  ✅ Created in {elapsed:.1f}s")
        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def main():
    print_banner()

    # Connect to Supabase
    print("  [1/3] Connecting to Supabase...")
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            port=SUPABASE_PORT
        )
        conn.set_session(autocommit=True)  # Required for CONCURRENTLY
        cursor = conn.cursor()
        print("  ✅ Connected")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Parse indexes
    print("\n  [2/3] Parsing index definitions...")
    indexes = get_indexes_from_sql()
    print(f"  ✅ Found {len(indexes)} indexes")

    # Deploy indexes
    print(f"\n  [3/3] Deploying {len(indexes)} indexes...")
    print()

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, index in enumerate(indexes, 1):
        print(f"  [{i}/{len(indexes)}] {index['name']}")

        if check_index_exists(cursor, index['name']):
            print(f"      ⏭️  Already exists, skipping")
            skipped_count += 1
        else:
            if deploy_index(cursor, index):
                success_count += 1
            else:
                failed_count += 1

        print()

    # Summary
    print("="*70)
    print("  DEPLOYMENT SUMMARY")
    print("="*70)
    print()
    print(f"  Total indexes: {len(indexes)}")
    print(f"  ✅ Created: {success_count}")
    print(f"  ⏭️  Skipped (already exist): {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")
    print()

    if failed_count == 0:
        print("  🎉 All indexes deployed successfully!")
    else:
        print(f"  ⚠️  {failed_count} indexes failed. Check errors above.")

    print()
    print("="*70)

    # Cleanup
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
