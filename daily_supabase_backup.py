"""
Daily Supabase Database Backup System
Creates compressed backups of all tables with rotation and verification
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase import create_client
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Backup configuration
BACKUP_BASE_DIR = Path("C:/TEMP/SUPABASE_BACKUPS")
RETENTION_DAYS = 30  # Keep backups for 30 days
BATCH_SIZE = 10000  # Records per batch for large tables

# Tables to backup (verified existing tables)
TABLES_TO_BACKUP = [
    'florida_parcels'
]

# Priority tables (backed up first)
PRIORITY_TABLES = ['florida_parcels']

def create_backup_directory(date_str):
    """Create backup directory for the given date"""
    backup_dir = BACKUP_BASE_DIR / f"backup_{date_str}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def get_table_count(table_name):
    """Get total record count for a table"""
    try:
        response = supabase.table(table_name).select('id', count='exact', head=True).execute()
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        logging.warning(f"Could not get count for {table_name}: {e}")
        return 0

def backup_table_batch(table_name, offset, limit, backup_dir):
    """Backup a batch of records from a table"""
    try:
        response = supabase.table(table_name).select('*').range(offset, offset + limit - 1).execute()

        if response.data:
            batch_file = backup_dir / f"{table_name}_batch_{offset//limit + 1}.json"

            # Write compressed JSON
            with gzip.open(f"{batch_file}.gz", 'wt', encoding='utf-8') as f:
                json.dump({
                    'table': table_name,
                    'batch_info': {
                        'offset': offset,
                        'limit': limit,
                        'record_count': len(response.data),
                        'timestamp': datetime.now().isoformat()
                    },
                    'data': response.data
                }, f, indent=2, default=str)

            return len(response.data)
        return 0

    except Exception as e:
        logging.error(f"Error backing up {table_name} batch {offset}-{offset+limit}: {e}")
        return 0

def backup_table(table_name, backup_dir):
    """Backup entire table using batched approach"""
    logging.info(f"Starting backup of table: {table_name}")

    # Get total count
    total_count = get_table_count(table_name)
    if total_count == 0:
        logging.info(f"Table {table_name} is empty, skipping")
        return True

    logging.info(f"Table {table_name} has {total_count:,} records")

    # Create table metadata
    metadata = {
        'table_name': table_name,
        'total_records': total_count,
        'backup_timestamp': datetime.now().isoformat(),
        'batch_size': BATCH_SIZE,
        'total_batches': (total_count + BATCH_SIZE - 1) // BATCH_SIZE
    }

    # Save metadata
    with open(backup_dir / f"{table_name}_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    # Backup in batches
    total_backed_up = 0
    batch_num = 0

    for offset in range(0, total_count, BATCH_SIZE):
        batch_num += 1
        batch_count = backup_table_batch(table_name, offset, BATCH_SIZE, backup_dir)
        total_backed_up += batch_count

        if batch_num % 10 == 0:
            logging.info(f"  {table_name}: {total_backed_up:,}/{total_count:,} records ({(total_backed_up/total_count)*100:.1f}%)")

        # Rate limiting for large tables
        if total_count > 100000:
            time.sleep(0.1)

    logging.info(f"Completed backup of {table_name}: {total_backed_up:,} records in {batch_num} batches")
    return total_backed_up == total_count

def create_backup_manifest(backup_dir, table_results):
    """Create a manifest file with backup summary"""

    manifest = {
        'backup_timestamp': datetime.now().isoformat(),
        'backup_version': '1.0',
        'supabase_url': SUPABASE_URL,
        'tables': {},
        'summary': {
            'total_tables': len(table_results),
            'successful_tables': sum(1 for success in table_results.values() if success),
            'failed_tables': sum(1 for success in table_results.values() if not success),
            'total_files': 0,
            'total_size_mb': 0
        }
    }

    # Calculate sizes and file counts
    for table_name in table_results.keys():
        metadata_file = backup_dir / f"{table_name}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                manifest['tables'][table_name] = metadata

        # Count compressed batch files
        batch_files = list(backup_dir.glob(f"{table_name}_batch_*.json.gz"))
        table_size = sum(f.stat().st_size for f in batch_files) / 1024 / 1024

        manifest['tables'][table_name] = {
            **manifest['tables'].get(table_name, {}),
            'batch_files': len(batch_files),
            'compressed_size_mb': round(table_size, 2),
            'backup_success': table_results[table_name]
        }

        manifest['summary']['total_files'] += len(batch_files)
        manifest['summary']['total_size_mb'] += table_size

    manifest['summary']['total_size_mb'] = round(manifest['summary']['total_size_mb'], 2)

    # Save manifest
    with open(backup_dir / "backup_manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest

def cleanup_old_backups():
    """Remove backups older than retention period"""
    if not BACKUP_BASE_DIR.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    logging.info(f"Cleaning up backups older than {cutoff_date.strftime('%Y-%m-%d')}")

    deleted_count = 0
    for backup_dir in BACKUP_BASE_DIR.iterdir():
        if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
            try:
                date_str = backup_dir.name.replace('backup_', '')
                backup_date = datetime.strptime(date_str, '%Y-%m-%d')

                if backup_date < cutoff_date:
                    shutil.rmtree(backup_dir)
                    deleted_count += 1
                    logging.info(f"Deleted old backup: {backup_dir.name}")
            except ValueError:
                logging.warning(f"Could not parse backup date from: {backup_dir.name}")

    logging.info(f"Cleaned up {deleted_count} old backups")

def verify_backup(backup_dir, table_name):
    """Verify backup integrity by checking files and metadata"""
    try:
        metadata_file = backup_dir / f"{table_name}_metadata.json"
        if not metadata_file.exists():
            return False, "Missing metadata file"

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        expected_batches = metadata['total_batches']
        actual_batches = len(list(backup_dir.glob(f"{table_name}_batch_*.json.gz")))

        if actual_batches != expected_batches:
            return False, f"Expected {expected_batches} batches, found {actual_batches}"

        # Verify at least one batch file can be read
        first_batch = backup_dir / f"{table_name}_batch_1.json.gz"
        if first_batch.exists():
            with gzip.open(first_batch, 'rt') as f:
                test_data = json.load(f)
                if 'data' not in test_data:
                    return False, "Invalid batch file format"

        return True, "Backup verified successfully"

    except Exception as e:
        return False, f"Verification error: {e}"

def main():
    """Main backup process"""
    start_time = time.time()
    date_str = datetime.now().strftime('%Y-%m-%d')

    print("=" * 70)
    print("SUPABASE DAILY BACKUP")
    print("=" * 70)
    print(f"Backup Date: {date_str}")
    print(f"Tables to backup: {len(TABLES_TO_BACKUP)}")
    print()

    # Create backup directory
    backup_dir = create_backup_directory(date_str)
    logging.info(f"Created backup directory: {backup_dir}")

    # Backup all tables
    table_results = {}

    # Backup priority tables first
    for table_name in PRIORITY_TABLES:
        if table_name in TABLES_TO_BACKUP:
            try:
                success = backup_table(table_name, backup_dir)
                table_results[table_name] = success

                # Verify backup
                verified, msg = verify_backup(backup_dir, table_name)
                logging.info(f"Backup verification for {table_name}: {msg}")

            except Exception as e:
                logging.error(f"Failed to backup {table_name}: {e}")
                table_results[table_name] = False

    # Backup remaining tables
    remaining_tables = [t for t in TABLES_TO_BACKUP if t not in PRIORITY_TABLES]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        for table_name in remaining_tables:
            future = executor.submit(backup_table, table_name, backup_dir)
            futures[future] = table_name

        for future in as_completed(futures):
            table_name = futures[future]
            try:
                success = future.result()
                table_results[table_name] = success

                # Verify backup
                verified, msg = verify_backup(backup_dir, table_name)
                logging.info(f"Backup verification for {table_name}: {msg}")

            except Exception as e:
                logging.error(f"Failed to backup {table_name}: {e}")
                table_results[table_name] = False

    # Create backup manifest
    manifest = create_backup_manifest(backup_dir, table_results)

    # Cleanup old backups
    cleanup_old_backups()

    # Final summary
    elapsed = time.time() - start_time
    successful = sum(1 for success in table_results.values() if success)
    total = len(table_results)

    print("\n" + "=" * 70)
    print("BACKUP COMPLETE")
    print("=" * 70)
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Tables processed: {successful}/{total}")
    print(f"Total files created: {manifest['summary']['total_files']}")
    print(f"Total compressed size: {manifest['summary']['total_size_mb']:.1f} MB")
    print(f"Backup location: {backup_dir}")

    # Log results
    for table_name, success in table_results.items():
        status = "SUCCESS" if success else "FAILED"
        table_info = manifest['tables'].get(table_name, {})
        records = table_info.get('total_records', 0)
        size = table_info.get('compressed_size_mb', 0)
        print(f"  {table_name}: {status} ({records:,} records, {size:.1f} MB)")

    if successful == total:
        print("\n*** ALL BACKUPS COMPLETED SUCCESSFULLY! ***")
    else:
        print(f"\n*** WARNING: {total - successful} backup(s) failed ***")

    print(f"\nBackup retention: {RETENTION_DAYS} days")
    print("Log saved to backup.log")

if __name__ == "__main__":
    main()