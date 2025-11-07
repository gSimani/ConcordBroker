#!/usr/bin/env python3
"""
Upload 2023 NAL data for all Florida counties
Based on working upload_alachua_fixed.py implementation
"""
import os
import glob
import pandas as pd
from supabase import create_client
from datetime import datetime
import sys

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
ROOT = r"C:\Users\gsima\Documents\MyProject\ConcordBroker"
BASE_PATH = os.path.join(ROOT, 'TEMP', 'DATABASE PROPERTY APP')
BATCH_SIZE = 1500  # Optimized for 4-core CPU
YEAR = 2023
RUN_ID = '2023-full-load-v3'

print("=" * 70)
print(f"2023 NAL DATA UPLOAD - ALL COUNTIES")
print("=" * 70)
print(f"Base path: {BASE_PATH}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Run ID: {RUN_ID}")
print("=" * 70)

# Create Supabase client
if not SUPABASE_KEY:
    print("[ERROR] SUPABASE_SERVICE_ROLE_KEY not set in environment")
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

# Get all county folders
county_folders = []
if os.path.exists(BASE_PATH):
    for item in os.listdir(BASE_PATH):
        county_path = os.path.join(BASE_PATH, item)
        if os.path.isdir(county_path):
            nal_path = os.path.join(county_path, 'NAL')
            if os.path.exists(nal_path):
                county_folders.append((item, nal_path))

if not county_folders:
    print(f"[ERROR] No county folders found in {BASE_PATH}")
    sys.exit(1)

county_folders.sort()  # Process alphabetically
total_counties = len(county_folders)

print(f"\nFound {total_counties} counties with NAL data")
print("-" * 70)

# Process each county
grand_total_uploaded = 0
counties_processed = 0

for county_index, (county_name, nal_path) in enumerate(county_folders, start=1):
    print(f"\n[{county_index}/{total_counties}] Processing {county_name}")
    print("-" * 70)

    # Get all CSV files in county folder
    csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    if not csv_files:
        print(f"  [WARNING] No CSV files found for {county_name}, skipping")
        continue

    # Sort files to prioritize Final > Supplemental > Preliminary
    # Files are named like: NAL_2023_01Alachua_P.csv, NAL_2023_01Alachua_S.csv, NAL_2023_01Alachua_F.csv
    # We want to process in order: P, S, F (Final overwrites earlier data due to upsert)
    csv_files.sort()

    print(f"  Found {len(csv_files)} CSV file(s)")

    county_uploaded = 0

    for file_index, csv_file in enumerate(csv_files, start=1):
        file_name = os.path.basename(csv_file)
        print(f"  [{file_index}/{len(csv_files)}] Processing: {file_name}")

        log_progress(
            phase_index=county_index,
            phase_total=total_counties,
            county=county_name,
            done=file_index - 1,
            total=len(csv_files),
            current=f"start:{file_name}"
        )

        try:
            chunk_iter = pd.read_csv(
                csv_file,
                chunksize=BATCH_SIZE,
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

                    # Truncate owner_state to 2 characters (FL not FLORIDA)
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

                try:
                    # Upsert with conflict resolution on (parcel_id, county, year)
                    client.table('florida_parcels').upsert(
                        records,
                        on_conflict='parcel_id,county,year'
                    ).execute()

                    file_uploaded += len(records)
                    county_uploaded += len(records)
                    grand_total_uploaded += len(records)

                    if chunk_num % 10 == 0:
                        print(f"    Chunk {chunk_num}: +{len(records)} rows (file: {file_uploaded:,}, county: {county_uploaded:,}, total: {grand_total_uploaded:,})")

                except Exception as e:
                    print(f"    [ERROR] Batch upload failed: {str(e)[:200]}")
                    # Continue with next batch instead of stopping

            print(f"    Completed {file_name}: {file_uploaded:,} rows")

            log_progress(
                phase_index=county_index,
                phase_total=total_counties,
                county=county_name,
                done=file_index,
                total=len(csv_files),
                current=f"ingested:{file_name}"
            )

        except Exception as e:
            print(f"    [ERROR] File processing failed: {str(e)[:200]}")
            continue

    print(f"  {county_name} complete: {county_uploaded:,} rows")
    counties_processed += 1

print("\n" + "=" * 70)
print("UPLOAD COMPLETE")
print("=" * 70)
print(f"Counties processed: {counties_processed}/{total_counties}")
print(f"Total rows uploaded: {grand_total_uploaded:,}")
print("=" * 70)
