"""
Restore Supabase Database from Backup
Restores data from compressed daily backups
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Backup configuration
BACKUP_BASE_DIR = Path("C:/TEMP/SUPABASE_BACKUPS")

def list_available_backups():
    """List all available backup dates"""
    if not BACKUP_BASE_DIR.exists():
        return []

    backups = []
    for backup_dir in BACKUP_BASE_DIR.iterdir():
        if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
            manifest_file = backup_dir / "backup_manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)

                    date_str = backup_dir.name.replace('backup_', '')
                    backups.append({
                        'date': date_str,
                        'path': backup_dir,
                        'manifest': manifest
                    })
                except Exception as e:
                    logging.warning(f"Could not read manifest for {backup_dir.name}: {e}")

    return sorted(backups, key=lambda x: x['date'], reverse=True)

def restore_table_batch(batch_file, table_name, batch_size=1000):
    """Restore a single batch file to Supabase"""
    try:
        with gzip.open(batch_file, 'rt') as f:
            batch_data = json.load(f)

        records = batch_data['data']
        if not records:
            return 0

        logging.info(f"Restoring {len(records)} records from {batch_file.name}")

        # Insert in smaller chunks to avoid timeouts
        success_count = 0
        for i in range(0, len(records), batch_size):
            chunk = records[i:i+batch_size]

            try:
                response = supabase.table(table_name).insert(chunk).execute()
                success_count += len(chunk)
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                logging.error(f"Error inserting chunk {i}-{i+len(chunk)} for {table_name}: {e}")

        return success_count

    except Exception as e:
        logging.error(f"Error restoring batch {batch_file}: {e}")
        return 0

def clear_table(table_name):
    """Clear all data from a table (WARNING: DESTRUCTIVE)"""
    try:
        # This is a dangerous operation - get confirmation
        response = input(f"WARNING: This will DELETE ALL data in {table_name}. Type 'YES' to confirm: ")
        if response != 'YES':
            print("Operation cancelled.")
            return False

        # For large tables, we need to delete in batches
        batch_size = 1000
        deleted_total = 0

        while True:
            # Get batch of records to delete
            records = supabase.table(table_name).select('id').limit(batch_size).execute()

            if not records.data:
                break

            ids_to_delete = [record['id'] for record in records.data]

            # Delete the batch
            supabase.table(table_name).delete().in_('id', ids_to_delete).execute()
            deleted_total += len(ids_to_delete)

            logging.info(f"Deleted {deleted_total} records from {table_name}")

        logging.info(f"Cleared table {table_name}: {deleted_total} records deleted")
        return True

    except Exception as e:
        logging.error(f"Error clearing table {table_name}: {e}")
        return False

def restore_table(backup_dir, table_name, clear_first=False):
    """Restore entire table from backup"""
    logging.info(f"Starting restore of table: {table_name}")

    # Check metadata
    metadata_file = backup_dir / f"{table_name}_metadata.json"
    if not metadata_file.exists():
        logging.error(f"No metadata found for {table_name}")
        return False

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    logging.info(f"Table {table_name} backup contains {metadata['total_records']:,} records in {metadata['total_batches']} batches")

    # Clear table if requested
    if clear_first:
        if not clear_table(table_name):
            return False

    # Get all batch files
    batch_files = sorted(backup_dir.glob(f"{table_name}_batch_*.json.gz"))

    if len(batch_files) != metadata['total_batches']:
        logging.error(f"Expected {metadata['total_batches']} batch files, found {len(batch_files)}")
        return False

    # Restore all batches
    total_restored = 0
    for batch_file in batch_files:
        restored_count = restore_table_batch(batch_file, table_name)
        total_restored += restored_count

    logging.info(f"Completed restore of {table_name}: {total_restored:,} records restored")
    return total_restored == metadata['total_records']

def main():
    """Main restore process"""
    print("=" * 70)
    print("SUPABASE BACKUP RESTORE")
    print("=" * 70)

    # List available backups
    backups = list_available_backups()

    if not backups:
        print("No backups found!")
        return

    print("\nAvailable backups:")
    for i, backup in enumerate(backups):
        manifest = backup['manifest']
        print(f"{i+1}. {backup['date']} - {manifest['summary']['successful_tables']}/{manifest['summary']['total_tables']} tables ({manifest['summary']['total_size_mb']:.1f} MB)")

    # Select backup
    try:
        choice = int(input(f"\nSelect backup to restore (1-{len(backups)}): "))
        if choice < 1 or choice > len(backups):
            print("Invalid selection")
            return

        selected_backup = backups[choice - 1]
        backup_dir = selected_backup['path']
        manifest = selected_backup['manifest']

    except (ValueError, KeyboardInterrupt):
        print("Operation cancelled")
        return

    print(f"\nSelected backup: {selected_backup['date']}")
    print(f"Backup location: {backup_dir}")

    # Show available tables
    print("\nAvailable tables in backup:")
    table_names = list(manifest['tables'].keys())
    for i, table_name in enumerate(table_names):
        table_info = manifest['tables'][table_name]
        records = table_info.get('total_records', 0)
        size = table_info.get('compressed_size_mb', 0)
        status = "✓" if table_info.get('backup_success') else "✗"
        print(f"{i+1}. {status} {table_name} - {records:,} records ({size:.1f} MB)")

    # Select tables to restore
    print(f"\nSelect tables to restore:")
    print("Enter table numbers separated by commas (e.g., 1,3,5)")
    print("Or 'all' to restore all tables")
    print("Or 'q' to quit")

    selection = input("Selection: ").strip().lower()

    if selection == 'q':
        return

    if selection == 'all':
        tables_to_restore = table_names
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            tables_to_restore = [table_names[i] for i in indices if 0 <= i < len(table_names)]
        except (ValueError, IndexError):
            print("Invalid selection")
            return

    if not tables_to_restore:
        print("No tables selected")
        return

    # Confirm destructive operation
    print(f"\nTables to restore: {', '.join(tables_to_restore)}")
    clear_first = input("Clear existing data before restore? (y/N): ").lower() == 'y'

    if clear_first:
        print("\nWARNING: This will permanently delete existing data!")

    final_confirm = input("Proceed with restore? (y/N): ").lower() == 'y'
    if not final_confirm:
        print("Restore cancelled")
        return

    # Perform restore
    start_time = time.time()
    results = {}

    for table_name in tables_to_restore:
        try:
            success = restore_table(backup_dir, table_name, clear_first)
            results[table_name] = success
        except Exception as e:
            logging.error(f"Failed to restore {table_name}: {e}")
            results[table_name] = False

    # Summary
    elapsed = time.time() - start_time
    successful = sum(1 for success in results.values() if success)
    total = len(results)

    print("\n" + "=" * 70)
    print("RESTORE COMPLETE")
    print("=" * 70)
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Tables restored: {successful}/{total}")

    for table_name, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        table_info = manifest['tables'][table_name]
        records = table_info.get('total_records', 0)
        print(f"  {table_name}: {status} ({records:,} records)")

    if successful == total:
        print("\n*** ALL RESTORES COMPLETED SUCCESSFULLY! ***")
    else:
        print(f"\n*** WARNING: {total - successful} restore(s) failed ***")

    print("Log saved to restore.log")

if __name__ == "__main__":
    main()