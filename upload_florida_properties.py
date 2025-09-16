"""
Upload all Florida property appraiser data to Supabase
Using optimized configuration from documentation
"""

import pandas as pd
from supabase import create_client, Client
from pathlib import Path
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Configuration
DATA_DIR = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Optimized parameters
BATCH_SIZE = 1000          # Records per batch
PARALLEL_WORKERS = 4        # Concurrent upload threads
MAX_RETRIES = 3            # Retry attempts for failed batches
RETRY_DELAY = 2            # Base delay for exponential backoff

def get_supabase_client() -> Client:
    """Create Supabase client with service role"""
    return create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

def find_county_file(county: str) -> Path:
    """Find NAL file for a county"""
    county_paths = [
        DATA_DIR / county.upper() / "NAL",
        DATA_DIR / county.lower() / "NAL",
        DATA_DIR / county.upper() / "nal",
        DATA_DIR / county.lower() / "nal",
    ]
    
    for county_path in county_paths:
        if county_path.exists():
            csv_files = list(county_path.glob("*.csv"))
            if csv_files:
                return csv_files[0]
    return None

def prepare_record(row: pd.Series, county: str) -> dict:
    """Map NAL columns to florida_parcels schema"""
    # Calculate building value if we have both JV and LND_VAL
    building_val = None
    if row.get('JV') and row.get('LND_VAL'):
        try:
            building_val = float(row.get('JV', 0)) - float(row.get('LND_VAL', 0))
        except:
            building_val = None
    
    # Build sale_date timestamp if we have year and month
    sale_date = None
    if row.get('SALE_YR1') and row.get('SALE_MO1'):
        try:
            sale_date = f"{int(row.get('SALE_YR1'))}-{str(row.get('SALE_MO1')).zfill(2)}-01T00:00:00"
        except:
            sale_date = None
    
    record = {
        'parcel_id': str(row.get('PARCEL_ID', '')),
        'county': county.upper(),
        'year': 2025,
        'owner_name': str(row.get('OWN_NAME', '')),
        'owner_addr1': str(row.get('OWN_ADDR1', '')),
        'owner_addr2': str(row.get('OWN_ADDR2', '')),
        'owner_city': str(row.get('OWN_CITY', '')),
        'owner_state': str(row.get('OWN_STATE', ''))[:2],  # Truncate to 2 chars
        'owner_zip': str(row.get('OWN_ZIPCD', '')),
        'phy_addr1': str(row.get('PHY_ADDR1', '')),
        'phy_addr2': str(row.get('PHY_ADDR2', '')),
        'phy_city': str(row.get('PHY_CITY', '')),
        'phy_zipcd': str(row.get('PHY_ZIPCD', '')),
        'legal_desc': str(row.get('S_LEGAL', '')),
        'property_use': str(row.get('PA_UC', '')),
        'just_value': row.get('JV'),
        'land_value': row.get('LND_VAL'),
        'building_value': building_val,
        'assessed_value': row.get('AV_SD'),
        'taxable_value': row.get('TV_SD'),
        'year_built': row.get('ACT_YR_BLT'),
        'total_living_area': row.get('TOT_LVG_AREA'),
        'land_sqft': row.get('LND_SQFOOT'),
        'land_acres': float(row.get('LND_SQFOOT', 0)) / 43560 if row.get('LND_SQFOOT') else None,
        'sale_price': row.get('SALE_PRC1'),
        'sale_date': sale_date,
        'sale_qualification': str(row.get('QUAL_CD1', '')) if row.get('QUAL_CD1') else None,
    }
    
    # Clean numeric fields
    numeric_fields = ['just_value', 'land_value', 'building_value', 'assessed_value', 'taxable_value',
                     'year_built', 'total_living_area', 'land_sqft', 'land_acres', 'sale_price']
    
    for field in numeric_fields:
        if field in record:
            value = record[field]
            if pd.isna(value) or value == '' or value == 'None':
                record[field] = None
            else:
                try:
                    if field == 'year_built':
                        record[field] = int(float(value)) if value else None
                    else:
                        record[field] = float(value) if value else None
                except:
                    record[field] = None
    
    # Clean string fields
    for key, value in record.items():
        if key not in numeric_fields and key != 'sale_date':
            if pd.isna(value) or value == 'nan' or value == '':
                record[key] = ''
        elif key == 'sale_date':
            if pd.isna(value) or value == 'nan' or value == '':
                record[key] = None
    
    return record

def upload_batch_with_retry(client: Client, records: list, batch_num: int) -> dict:
    """Upload a batch with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            # Use optimal headers for performance
            headers = {
                'Prefer': 'return=minimal,resolution=merge-duplicates,count=none',
                'Content-Type': 'application/json'
            }
            
            # Set headers on client
            client.headers.update(headers)
            
            result = client.table('florida_parcels').upsert(
                records,
                on_conflict='parcel_id,county,year'
            ).execute()
            
            return {'batch': batch_num, 'success': True, 'records': len(records)}
            
        except Exception as e:
            error_str = str(e)
            
            if '429' in error_str:  # Rate limited
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
            elif '57014' in error_str:  # Timeout
                delay = RETRY_DELAY * (attempt + 1)
                time.sleep(delay)
            else:
                # For other errors, log and continue
                if attempt == MAX_RETRIES - 1:
                    return {'batch': batch_num, 'success': False, 'records': 0, 'error': error_str}
                time.sleep(RETRY_DELAY)
    
    return {'batch': batch_num, 'success': False, 'records': 0, 'error': 'Max retries exceeded'}

def process_county(county: str, client: Client) -> dict:
    """Process a single county"""
    print(f"[{county}] Starting...")
    
    # Find CSV file
    csv_path = find_county_file(county)
    if not csv_path:
        print(f"[{county}] No NAL file found")
        return {'county': county, 'total': 0, 'uploaded': 0, 'failed': 0}
    
    print(f"[{county}] Reading {csv_path.name}...")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path, low_memory=False, encoding='utf-8', on_bad_lines='skip')
        total_records = len(df)
        print(f"[{county}] Found {total_records:,} records")
        
        # Prepare all records
        all_records = []
        for _, row in df.iterrows():
            record = prepare_record(row, county)
            all_records.append(record)
        
        # Split into batches
        batches = [all_records[i:i+BATCH_SIZE] for i in range(0, len(all_records), BATCH_SIZE)]
        total_batches = len(batches)
        
        print(f"[{county}] Uploading {total_batches} batches...")
        
        # Upload batches with ThreadPoolExecutor
        uploaded = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = {
                executor.submit(upload_batch_with_retry, client, batch, i): i 
                for i, batch in enumerate(batches)
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    uploaded += result['records']
                else:
                    failed += len(batches[result['batch']])
                
                # Progress update
                if (uploaded + failed) % 10000 == 0:
                    print(f"[{county}] Progress: {uploaded:,}/{total_records:,} uploaded")
        
        print(f"[{county}] Complete: {uploaded:,} uploaded, {failed:,} failed")
        return {'county': county, 'total': total_records, 'uploaded': uploaded, 'failed': failed}
        
    except Exception as e:
        print(f"[{county}] Error: {e}")
        return {'county': county, 'total': 0, 'uploaded': 0, 'failed': 0, 'error': str(e)}

def main():
    """Main upload process"""
    print("=" * 70)
    print("FLORIDA PROPERTY APPRAISER DATA UPLOAD")
    print("=" * 70)
    print(f"Data directory: {DATA_DIR}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Parallel workers: {PARALLEL_WORKERS}")
    print()
    
    # Get list of counties
    counties = []
    for county_dir in DATA_DIR.iterdir():
        if county_dir.is_dir() and not county_dir.name.startswith('.'):
            counties.append(county_dir.name)
    
    counties.sort()
    print(f"Found {len(counties)} counties to process")
    
    # Initialize client
    client = get_supabase_client()
    
    # Check current count
    try:
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        current_count = result.count if hasattr(result, 'count') else 0
        print(f"Current database records: {current_count:,}")
    except:
        current_count = 0
        print("Could not get current count")
    
    print()
    print("Starting upload process...")
    print("-" * 70)
    
    # Process each county
    results = []
    start_time = time.time()
    
    for county in counties:
        county_result = process_county(county, client)
        results.append(county_result)
        
        # Save progress
        with open('upload_progress.json', 'w') as f:
            json.dump(results, f, indent=2)
    
    # Summary
    elapsed = time.time() - start_time
    total_uploaded = sum(r['uploaded'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_records = sum(r['total'] for r in results)
    
    print()
    print("=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)
    print(f"Total records: {total_records:,}")
    print(f"Uploaded: {total_uploaded:,}")
    print(f"Failed: {total_failed:,}")
    print(f"Success rate: {(total_uploaded/total_records*100):.1f}%")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Speed: {total_uploaded/elapsed:.0f} records/second")
    
    # Check final count
    try:
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        final_count = result.count if hasattr(result, 'count') else 0
        print(f"Final database records: {final_count:,}")
        print(f"Records added: {final_count - current_count:,}")
    except:
        print("Could not get final count")
    
    # Save final report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_counties': len(counties),
        'total_records': total_records,
        'uploaded': total_uploaded,
        'failed': total_failed,
        'elapsed_minutes': elapsed/60,
        'records_per_second': total_uploaded/elapsed if elapsed > 0 else 0,
        'results': results
    }
    
    with open('upload_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to upload_report.json")

if __name__ == "__main__":
    main()