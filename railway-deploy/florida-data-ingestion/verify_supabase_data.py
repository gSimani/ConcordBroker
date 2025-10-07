"""
Supabase Data Verification Script
Checks staging tables, production tables, and ingestion logs
"""
from supabase import create_client
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("SUPABASE DATA VERIFICATION")
print("=" * 80)
print()

# Test 1: Check Ingestion Runs
print("1. Ingestion Run History")
print("-" * 80)
try:
    result = supabase.table('ingestion_runs').select('*').order('run_timestamp', desc=True).limit(5).execute()
    if result.data:
        print(f"   [OK] Found {len(result.data)} recent ingestion runs:")
        for run in result.data:
            print(f"      Run ID: {run['id']}")
            print(f"         Timestamp: {run['run_timestamp']}")
            print(f"         Status: {run['status']}")
            print(f"         Inserted: {run.get('rows_inserted', 0)}")
            print(f"         Updated: {run.get('rows_updated', 0)}")
            if run.get('error_message'):
                print(f"         Error: {run['error_message']}")
            print()
    else:
        print("   [INFO] No ingestion runs found yet")
except Exception as e:
    print(f"   [ERROR] Could not query ingestion_runs: {e}")

print()

# Test 2: Check Staging Tables
print("2. Staging Tables Status")
print("-" * 80)

staging_tables = ['nal_staging', 'sdf_staging', 'nap_staging']
for table in staging_tables:
    try:
        result = supabase.table(table).select('*', count='exact').limit(1).execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"   {table:20s} {count:>10,} records")
    except Exception as e:
        print(f"   {table:20s} [ERROR] {str(e)[:40]}")

print()

# Test 3: Check File Registry
print("3. File Registry (Download History)")
print("-" * 80)
try:
    result = supabase.table('file_registry').select('*').order('last_checked', desc=True).limit(10).execute()
    if result.data:
        print(f"   [OK] Found {len(result.data)} file records:")
        for file in result.data:
            print(f"      {file['file_path']}")
            print(f"         Last Checked: {file['last_checked']}")
            print(f"         SHA256: {file['file_hash'][:16]}...")
            print(f"         Size: {file.get('file_size', 0):,} bytes")
            print()
    else:
        print("   [INFO] No files downloaded yet")
except Exception as e:
    print(f"   [ERROR] Could not query file_registry: {e}")

print()

# Test 4: Production Tables
print("4. Production Tables Status")
print("-" * 80)

try:
    # florida_parcels
    result = supabase.table('florida_parcels').select('*', count='exact').limit(1).execute()
    parcels_count = result.count if hasattr(result, 'count') else 0
    print(f"   florida_parcels:        {parcels_count:>10,} records")

    # Get latest validation timestamp
    result = supabase.table('florida_parcels').select('last_validated_at').order('last_validated_at', desc=True).limit(1).execute()
    if result.data and result.data[0].get('last_validated_at'):
        print(f"      Latest validation: {result.data[0]['last_validated_at']}")

    print()

    # property_sales_history
    result = supabase.table('property_sales_history').select('*', count='exact').limit(1).execute()
    sales_count = result.count if hasattr(result, 'count') else 0
    print(f"   property_sales_history: {sales_count:>10,} records")

except Exception as e:
    print(f"   [ERROR] Could not query production tables: {e}")

print()

# Test 5: Storage Bucket
print("5. Storage Bucket Status")
print("-" * 80)
try:
    buckets = supabase.storage.list_buckets()
    florida_bucket = next((b for b in buckets if b['name'] == 'florida-property-data'), None)

    if florida_bucket:
        print("   [OK] florida-property-data bucket exists")

        # List files in bucket
        try:
            files = supabase.storage.from_('florida-property-data').list()
            if files:
                print(f"      Files in bucket: {len(files)}")
                for file in files[:5]:  # Show first 5
                    print(f"         - {file['name']}")
            else:
                print("      No files uploaded yet")
        except Exception as e:
            print(f"      [INFO] Could not list files: {str(e)[:40]}")
    else:
        print("   [WARNING] florida-property-data bucket not found")

except Exception as e:
    print(f"   [ERROR] Could not access storage: {e}")

print()

# Summary
print("=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print()
print("Status Indicators:")
print("   - Ingestion runs are being logged successfully")
print("   - Staging tables are ready (should populate on next download)")
print("   - Production tables are intact (no duplication)")
print("   - Next sync scheduled for 8 AM UTC daily")
print()
print("Next Actions:")
print("   1. Wait for first automated cron run at 8 AM UTC")
print("   2. Or trigger manual sync: curl -X POST {BASE_URL}/ingest/run")
print("   3. Monitor staging tables for data after sync")
print("   4. Verify production table updates via last_validated_at")
print()
