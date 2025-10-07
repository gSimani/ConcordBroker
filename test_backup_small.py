"""
Test Backup System with Small Dataset
Tests the backup system with a limited number of records
"""

import os
import json
import gzip
from datetime import datetime
from pathlib import Path
import logging
from supabase import create_client
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BACKUP_BASE_DIR = Path("C:/TEMP/SUPABASE_BACKUPS")
TEST_LIMIT = 1000  # Only backup first 1000 records for testing

def test_backup():
    """Test backup with limited records"""

    print("=" * 60)
    print("TESTING BACKUP SYSTEM - LIMITED RECORDS")
    print("=" * 60)

    # Create test backup directory
    date_str = datetime.now().strftime('%Y-%m-%d-TEST')
    backup_dir = BACKUP_BASE_DIR / f"backup_{date_str}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"Test backup directory: {backup_dir}")

    start_time = time.time()

    # Test backup of florida_parcels (limited records)
    print(f"\nBacking up first {TEST_LIMIT} florida_parcels records...")

    # Get records
    response = supabase.table('florida_parcels').select('*').limit(TEST_LIMIT).execute()

    if not response.data:
        print("No data retrieved!")
        return False

    records_count = len(response.data)
    print(f"Retrieved {records_count} records")

    # Create compressed backup file
    backup_file = backup_dir / "florida_parcels_test.json.gz"

    with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
        json.dump({
            'table': 'florida_parcels',
            'test_backup': True,
            'record_count': records_count,
            'timestamp': datetime.now().isoformat(),
            'data': response.data
        }, f, indent=2, default=str)

    # Get file size
    file_size_mb = backup_file.stat().st_size / 1024 / 1024

    print(f"Backup file created: {backup_file}")
    print(f"Compressed size: {file_size_mb:.2f} MB")

    # Test verification - read back the file
    print("\nTesting backup verification...")

    try:
        with gzip.open(backup_file, 'rt') as f:
            restored_data = json.load(f)

        if len(restored_data['data']) == records_count:
            print("[PASS] Backup verification successful")
        else:
            print(f"[FAIL] Record count mismatch: expected {records_count}, got {len(restored_data['data'])}")
            return False

    except Exception as e:
        print(f"[FAIL] Backup verification failed: {e}")
        return False

    # Test other tables with very small datasets
    test_tables = ['counties']  # This should be a small table

    for table_name in test_tables:
        print(f"\nTesting backup of {table_name}...")

        try:
            response = supabase.table(table_name).select('*').execute()

            if response.data:
                table_file = backup_dir / f"{table_name}_test.json.gz"

                with gzip.open(table_file, 'wt') as f:
                    json.dump({
                        'table': table_name,
                        'test_backup': True,
                        'record_count': len(response.data),
                        'timestamp': datetime.now().isoformat(),
                        'data': response.data
                    }, f, indent=2, default=str)

                table_size_mb = table_file.stat().st_size / 1024 / 1024
                print(f"  {table_name}: {len(response.data)} records ({table_size_mb:.2f} MB)")
            else:
                print(f"  {table_name}: No data found")

        except Exception as e:
            print(f"  {table_name}: Error - {e}")

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("TEST BACKUP COMPLETE")
    print("=" * 60)
    print(f"Time elapsed: {elapsed:.1f} seconds")
    print(f"Test directory: {backup_dir}")

    # List all created files
    backup_files = list(backup_dir.glob("*.gz"))
    total_size = sum(f.stat().st_size for f in backup_files) / 1024 / 1024

    print(f"Files created: {len(backup_files)}")
    print(f"Total size: {total_size:.2f} MB")

    for f in backup_files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  - {f.name} ({size_mb:.2f} MB)")

    print("\n[SUCCESS] Backup system test completed!")
    return True

if __name__ == "__main__":
    test_backup()