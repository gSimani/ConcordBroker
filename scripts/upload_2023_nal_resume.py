#!/usr/bin/env python3
"""
Resume 2023 NAL upload for incomplete counties
Improved version with retry logic, better error handling, and resume capability
"""
import os
import glob
import pandas as pd
from supabase import create_client
import sys
import time
import random

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0')
ROOT = r"C:\Users\gsima\Documents\MyProject\ConcordBroker"
BASE_PATH = os.path.join(ROOT, 'TEMP', 'DATABASE PROPERTY APP')
YEAR = 2023
RUN_ID = '2023-full-load-v3'

# Adaptive batch sizes
NORMAL_BATCH_SIZE = 1500
LARGE_COUNTY_BATCH_SIZE = 750  # Smaller batches for large counties
LARGE_COUNTIES = {'ORANGE', 'DADE', 'BROWARD', 'PALM BEACH', 'HILLSBOROUGH',
                  'PINELLAS', 'DUVAL', 'LEE', 'POLK', 'PASCO'}

# Retry configuration
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 2  # seconds

print("=" * 80)
print(f"2023 NAL DATA UPLOAD - RESUME MODE")
print("=" * 80)
print(f"Base path: {BASE_PATH}")
print(f"Normal batch size: {NORMAL_BATCH_SIZE}")
print(f"Large county batch size: {LARGE_COUNTY_BATCH_SIZE}")
print(f"Run ID: {RUN_ID}")
print("=" * 80)

if not SUPABASE_KEY:
    print("[ERROR] SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_int(v):
    try:
        return int(float(str(v).replace(',', ''))) if (v is not None and str(v) != '' and str(v).lower() != 'nan') else None
    except:
        return None

def safe_float(v):
    try:
        return float(str(v).replace(',', '')) if (v is not None and str(v) != '' and str(v).lower() != 'nan') else None
    except:
        return None

def build_sale_date(yr, mo):
    y = safe_int(yr)
    m = safe_int(mo)
    if not y or not m:
        return None
    return f"{y}-{str(m).zfill(2)}-01T00:00:00"

def log_progress(phase_index, phase_total, county, done, total, current):
    """Write progress to ingestion_progress table"""
    try:
        progress_record = {
            'run_id': RUN_ID,
            'phase_index': phase_index,
            'phase_total': phase_total,
            'county': county,
            'years': {'start': YEAR, 'end': YEAR},
            'done': done,
            'total': total,
            'percent': int((done / total * 100) if total > 0 else 0),
            'current': current
        }
        client.table('ingestion_progress').insert(progress_record).execute()
    except Exception as e:
        print(f"  [WARNING] Progress logging failed: {e}")

def upload_batch_with_retry(records, max_retries=MAX_RETRIES):
    """Upload batch with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            client.table('florida_parcels').upsert(
                records,
                on_conflict='parcel_id,county,year'
            ).execute()
            return True, None
        except Exception as e:
            error_str = str(e)

            # Check if it's a retryable error
            if '429' in error_str or '57014' in error_str or 'timeout' in error_str.lower():
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (INITIAL_RETRY_DELAY ** attempt) + random.uniform(0, 1)
                    print(f"      [RETRY {attempt + 1}/{max_retries}] Rate limited/timeout, retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    return False, f"Max retries exceeded: {error_str[:200]}"
            else:
                # Non-retryable error
                return False, error_str[:200]

    return False, "Unknown error"

def get_completed_counties():
    """Get list of counties that have already been successfully uploaded"""
    try:
        # Get all progress entries with "ingested:" status
        result = client.table('ingestion_progress').select('county, current').eq('run_id', RUN_ID).execute()

        completed = set()
        for entry in result.data:
            if entry.get('current', '').startswith('ingested:'):
                completed.add(entry['county'])

        return completed
    except Exception as e:
        print(f"[WARNING] Could not fetch completed counties: {e}")
        return set()

# Get list of completed counties
completed_counties = get_completed_counties()
print(f"\nFound {len(completed_counties)} already completed counties:")
for county in sorted(completed_counties):
    print(f"  [OK] {county}")
print()

# Get all county folders
county_folders = []
if os.path.exists(BASE_PATH):
    for item in os.listdir(BASE_PATH):
        county_path = os.path.join(BASE_PATH, item)
        if os.path.isdir(county_path):
            nal_path = os.path.join(county_path, 'NAL')
            if os.path.exists(nal_path):
                # Skip if already completed
                if item in completed_counties:
                    continue
                county_folders.append((item, nal_path))

if not county_folders:
    print("[INFO] No remaining counties to process - upload is complete!")
    sys.exit(0)

county_folders.sort()
total_counties = len(county_folders)
total_counties_all = total_counties + len(completed_counties)

print(f"Remaining counties to process: {total_counties}")
print("-" * 80)

# Process each county
grand_total_uploaded = 0
counties_processed = 0
counties_failed = []

for county_index, (county_name, nal_path) in enumerate(county_folders, start=1):
    # Determine batch size based on county
    batch_size = LARGE_COUNTY_BATCH_SIZE if county_name in LARGE_COUNTIES else NORMAL_BATCH_SIZE

    print(f"\n[{county_index}/{total_counties}] Processing {county_name} (batch size: {batch_size})")
    print("-" * 80)

    # Get all CSV files
    csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    if not csv_files:
        print(f"  [WARNING] No CSV files found for {county_name}, skipping")
        continue

    csv_files.sort()
    print(f"  Found {len(csv_files)} CSV file(s)")

    county_uploaded = 0
    county_errors = []

    for file_index, csv_file in enumerate(csv_files, start=1):
        file_name = os.path.basename(csv_file)
        print(f"  [{file_index}/{len(csv_files)}] Processing: {file_name}")

        log_progress(
            phase_index=len(completed_counties) + county_index,
            phase_total=total_counties_all,
            county=county_name,
            done=file_index - 1,
            total=len(csv_files),
            current=f"start:{file_name}"
        )

        try:
            chunk_iter = pd.read_csv(
                csv_file,
                chunksize=batch_size,
                low_memory=False,
                encoding='utf-8',
                on_bad_lines='skip'
            )

            file_uploaded = 0

            for chunk_num, chunk in enumerate(chunk_iter, start=1):
                records = []
                for _, row in chunk.iterrows():
                    parcel_id = str(row.get('PARCEL_ID', '')).strip()
                    if not parcel_id:
                        continue

                    jv = safe_float(row.get('JV'))
                    land_val = safe_float(row.get('LND_VAL'))
                    building_val = (jv - land_val) if (jv is not None and land_val is not None) else None

                    owner_state = str(row.get('OWN_STATE'))[:2] if pd.notna(row.get('OWN_STATE')) else None

                    rec = {
                        'parcel_id': parcel_id,
                        'county': county_name,
                        'year': YEAR,
                        'owner_name': (str(row.get('OWN_NAME'))[:255] if pd.notna(row.get('OWN_NAME')) else None),
                        'owner_addr1': (str(row.get('OWN_ADDR1'))[:255] if pd.notna(row.get('OWN_ADDR1')) else None),
                        'owner_addr2': (str(row.get('OWN_ADDR2'))[:255] if pd.notna(row.get('OWN_ADDR2')) else None),
                        'owner_city': (str(row.get('OWN_CITY'))[:100] if pd.notna(row.get('OWN_CITY')) else None),
                        'owner_state': owner_state,
                        'owner_zip': (str(row.get('OWN_ZIPCD'))[:10] if pd.notna(row.get('OWN_ZIPCD')) else None),
                        'phy_addr1': (str(row.get('PHY_ADDR1'))[:255] if pd.notna(row.get('PHY_ADDR1')) else None),
                        'phy_addr2': (str(row.get('PHY_ADDR2'))[:255] if pd.notna(row.get('PHY_ADDR2')) else None),
                        'phy_city': (str(row.get('PHY_CITY'))[:100] if pd.notna(row.get('PHY_CITY')) else None),
                        'phy_state': 'FL',
                        'phy_zipcd': (str(row.get('PHY_ZIPCD'))[:10] if pd.notna(row.get('PHY_ZIPCD')) else None),
                        'property_use': (str(row.get('DOR_UC'))[:10] if pd.notna(row.get('DOR_UC')) else None),
                        'year_built': safe_int(row.get('ACT_YR_BLT')),
                        'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
                        'land_sqft': safe_int(row.get('LND_SQFOOT')),
                        'just_value': jv,
                        'assessed_value': safe_float(row.get('AV_SD')),
                        'taxable_value': safe_float(row.get('TV_SD')),
                        'land_value': land_val,
                        'building_value': building_val,
                        'sale_price': safe_float(row.get('SALE_PRC1')),
                        'sale_date': build_sale_date(row.get('SALE_YR1'), row.get('SALE_MO1')),
                    }
                    records.append(rec)

                if not records:
                    continue

                # Upload with retry logic
                success, error = upload_batch_with_retry(records)

                if success:
                    file_uploaded += len(records)
                    county_uploaded += len(records)
                    grand_total_uploaded += len(records)

                    if chunk_num % 10 == 0:
                        print(f"    Chunk {chunk_num}: +{len(records)} rows (file: {file_uploaded:,}, county: {county_uploaded:,}, total: {grand_total_uploaded:,})")
                else:
                    error_msg = f"Chunk {chunk_num} failed after retries: {error}"
                    print(f"    [ERROR] {error_msg}")
                    county_errors.append(error_msg)

            print(f"    Completed {file_name}: {file_uploaded:,} rows")

            log_progress(
                phase_index=len(completed_counties) + county_index,
                phase_total=total_counties_all,
                county=county_name,
                done=file_index,
                total=len(csv_files),
                current=f"ingested:{file_name}"
            )

        except Exception as e:
            error_msg = f"File {file_name} processing failed: {str(e)[:200]}"
            print(f"    [ERROR] {error_msg}")
            county_errors.append(error_msg)
            continue

    if county_errors:
        print(f"\n  [WARNING] {county_name} completed with {len(county_errors)} errors")
        counties_failed.append((county_name, county_errors))
    else:
        print(f"\n  [SUCCESS] {county_name} complete: {county_uploaded:,} rows")

    counties_processed += 1

print("\n" + "=" * 80)
print("UPLOAD COMPLETE")
print("=" * 80)
print(f"Counties already completed: {len(completed_counties)}")
print(f"Counties newly processed: {counties_processed}/{total_counties}")
print(f"Total rows uploaded this run: {grand_total_uploaded:,}")

if counties_failed:
    print(f"\n[WARNING] {len(counties_failed)} counties had errors:")
    for county, errors in counties_failed:
        print(f"  [!] {county}: {len(errors)} errors")
        for error in errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
else:
    print("\n[SUCCESS] All counties processed without errors!")

print("=" * 80)
