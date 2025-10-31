"""
Test script for PostgreSQL bulk loader
Verifies connection and demonstrates usage patterns
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded environment from {env_file}")
else:
    print(f"[WARN] .env file not found at {env_file}")
    print("   Set DATABASE_URL environment variable manually")

# Now import the loader
from postgres_bulk_loader import PostgreSQLBulkLoader, BulkUploadStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_1_connection():
    """Test 1: Basic database connectivity"""
    print("\n" + "="*60)
    print("TEST 1: Database Connectivity")
    print("="*60)

    loader = PostgreSQLBulkLoader(verbose=True)

    if loader.connect():
        print("[OK] Connection successful")
        print(f"  Host: {loader.host}")
        print(f"  Port: {loader.port}")

        # Get some stats
        cursor = loader.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_tables
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"  Tables in database: {table_count}")

        cursor.close()
        loader.disconnect()
        return True
    else:
        print("[FAIL] Connection failed")
        return False


def test_2_table_check():
    """Test 2: Check if florida_parcels table exists"""
    print("\n" + "="*60)
    print("TEST 2: Florida Parcels Table Check")
    print("="*60)

    loader = PostgreSQLBulkLoader(verbose=True)

    if not loader.connect():
        print("[FAIL] Cannot connect to database")
        return False

    try:
        cursor = loader.conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'florida_parcels'
            )
        """)
        exists = cursor.fetchone()[0]

        if exists:
            print("[OK] florida_parcels table exists")

            # Get table stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    pg_size_pretty(pg_total_relation_size('florida_parcels')) as size
                FROM florida_parcels
            """)
            total_records, table_size = cursor.fetchone()
            print(f"  Total records: {total_records:,}")
            print(f"  Table size: {table_size}")

            # Show columns
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'florida_parcels'
                ORDER BY ordinal_position
                LIMIT 10
            """)
            print("  Columns (first 10):")
            for col_name, data_type in cursor.fetchall():
                print(f"    - {col_name}: {data_type}")

            return True
        else:
            print("[FAIL] florida_parcels table does not exist")
            print("  Run: python scripts/deploy_schema.py")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        cursor.close()
        loader.disconnect()


def test_3_performance_estimate():
    """Test 3: Estimate performance for bulk operations"""
    print("\n" + "="*60)
    print("TEST 3: Performance Estimates")
    print("="*60)

    loader = PostgreSQLBulkLoader(verbose=False)

    if not loader.connect():
        print("[FAIL] Cannot connect to database")
        return False

    try:
        cursor = loader.conn.cursor()

        # Get record count
        cursor.execute("""
            SELECT COUNT(*) FROM florida_parcels
        """)
        total_records = cursor.fetchone()[0]

        if total_records > 0:
            print(f"[OK] Database has {total_records:,} records")

            # Estimate speeds
            copy_speed = 3000  # records/sec for COPY
            upsert_speed = 1500  # records/sec for UPSERT
            batch_speed = 800  # records/sec for batch

            copy_time = total_records / copy_speed / 60
            upsert_time = total_records / upsert_speed / 60
            batch_time = total_records / batch_speed / 60

            print(f"\nEstimated bulk operation times for {total_records:,} records:")
            print(f"  COPY method:   {copy_time:.1f} minutes ({copy_speed:,} rec/sec)")
            print(f"  UPSERT method: {upsert_time:.1f} minutes ({upsert_speed:,} rec/sec)")
            print(f"  Batch method:  {batch_time:.1f} minutes ({batch_speed:,} rec/sec)")
        else:
            print("[OK] Database is empty (no records to estimate)")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        cursor.close()
        loader.disconnect()


def test_4_example_usage():
    """Test 4: Show example usage patterns"""
    print("\n" + "="*60)
    print("TEST 4: Example Usage Patterns")
    print("="*60)

    examples = """
EXAMPLE 1: Fastest COPY import
==============================
from postgres_bulk_loader import PostgreSQLBulkLoader

loader = PostgreSQLBulkLoader()
loader.connect()

stats = loader.bulk_copy_from_csv(
    csv_file_path="florida_properties.csv",
    table_name="florida_parcels",
    columns=['parcel_id', 'county', 'owner_name', 'just_value']
)

print(stats)
loader.disconnect()


EXAMPLE 2: Safe UPSERT (insert or update)
==========================================
stats = loader.bulk_upsert_from_csv(
    csv_file_path="florida_updates.csv",
    table_name="florida_parcels",
    columns=['parcel_id', 'county', 'property_use', 'just_value'],
    unique_keys=['parcel_id', 'county']
)


EXAMPLE 3: Batch updates with validation
========================================
records = [
    {'parcel_id': 'ABC123', 'county': 'BROWARD', 'property_use': 'RES'},
    {'parcel_id': 'XYZ789', 'county': 'MIAMI', 'property_use': 'COM'}
]

stats = loader.batch_update_from_list(
    table_name="florida_parcels",
    records=records,
    unique_keys=['parcel_id', 'county']
)


PERFORMANCE COMPARISON
======================
             Speed           Time (9.7M records)
REST API     100-200/sec     13-26 hours
COPY         2000-4000/sec   40-80 minutes
UPSERT       1000-2000/sec   80min - 2.5 hours
Batch        500-1000/sec    2.5-5 hours

WHY SO FAST?
============
- COPY uses binary protocol (no SQL parsing)
- Direct PostgreSQL driver (no HTTP overhead)
- Connection pooling (reuse connections)
- Batch commits (reduce transaction overhead)
- No JWT validation per request
- No rate limiting (429 errors)
    """
    print(examples)
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PostgreSQL Bulk Loader - Verification Suite")
    print("="*60)

    tests = [
        ("Connection", test_1_connection),
        ("Table Check", test_2_table_check),
        ("Performance", test_3_performance_estimate),
        ("Examples", test_4_example_usage),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            results.append((test_name, status))
        except Exception as e:
            print(f"[ERROR] Test crashed: {e}")
            results.append((test_name, "ERROR"))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, status in results:
        symbol = "[OK]" if status == "PASS" else "[FAIL]"
        print(f"{symbol} {test_name:20} {status}")

    all_passed = all(status == "PASS" for _, status in results)
    print("\n" + ("[OK] All tests passed!" if all_passed else "[FAIL] Some tests failed"))

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
