"""
Optimized Property Appraiser Data Upload to Supabase
Uses REST API performance optimizations and increased batch sizes
"""

import pandas as pd
import os
from pathlib import Path
from supabase import create_client, Client
import time
from typing import List, Dict, Tuple
import json
from datetime import datetime
import traceback
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Optimized upload parameters
BATCH_SIZE = 1000  # Increased from 500
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds with exponential backoff
PROGRESS_FILE = "upload_progress.json"
PARALLEL_WORKERS = 4  # Number of parallel upload threads

# Data source
DATA_DIR = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

# Counties that need upload (missing or partial)
COUNTIES_TO_UPLOAD = {
    'ALACHUA': {'expected': 127419, 'uploaded': 0},
    'BAKER': {'expected': 13228, 'uploaded': 0},
    'BAY': {'expected': 125810, 'uploaded': 0},
    'BRADFORD': {'expected': 14923, 'uploaded': 0},
    'BREVARD': {'expected': 305313, 'uploaded': 0},
    'CALHOUN': {'expected': 8968, 'uploaded': 0},
    'CHARLOTTE': {'expected': 122976, 'uploaded': 0},
    'CITRUS': {'expected': 97531, 'uploaded': 0},
    'CLAY': {'expected': 102371, 'uploaded': 0},
    'COLLIER': {'expected': 196515, 'uploaded': 0},
    'COLUMBIA': {'expected': 37659, 'uploaded': 0},
    'DADE': {'expected': 958552, 'uploaded': 314276},  # Partial
    'DESOTO': {'expected': 15576, 'uploaded': 0},
    'DIXIE': {'expected': 12043, 'uploaded': 0},
    'DUVAL': {'expected': 401513, 'uploaded': 389952},  # Partial
    'HILLSBOROUGH': {'expected': 573444, 'uploaded': 175735},  # Partial
    'LEE': {'expected': 425774, 'uploaded': 0},
    'MARION': {'expected': 204018, 'uploaded': 201518},  # Partial
    'ORANGE': {'expected': 512617, 'uploaded': 0},
    'OSCEOLA': {'expected': 181653, 'uploaded': 0},
    'PALM BEACH': {'expected': 715075, 'uploaded': 0},
    'PASCO': {'expected': 272063, 'uploaded': 0},
    'PINELLAS': {'expected': 562459, 'uploaded': 0},
    'POLK': {'expected': 352732, 'uploaded': 0},
    'SARASOTA': {'expected': 283619, 'uploaded': 0},
    'SEMINOLE': {'expected': 211086, 'uploaded': 0},
    'VOLUSIA': {'expected': 321520, 'uploaded': 0}
}

# Thread-safe progress tracking
progress_lock = threading.Lock()

def load_progress():
    """Load upload progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save upload progress to file (thread-safe)"""
    with progress_lock:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)

def find_county_file(county: str) -> Path:
    """Find the NAL CSV file for a county"""
    # Look for NAL file in county subdirectory
    county_paths = [
        DATA_DIR / county.upper() / "NAL",
        DATA_DIR / county.lower() / "NAL",
        DATA_DIR / county.title() / "NAL",
        DATA_DIR / county / "NAL"
    ]
    
    for county_path in county_paths:
        if county_path.exists():
            # Find the NAL CSV file in the directory
            csv_files = list(county_path.glob("*.csv"))
            if csv_files:
                # Return the first CSV file found (should be NAL file)
                return csv_files[0]
    
    # Fallback: look for direct CSV files
    patterns = [
        f"{county}.csv",
        f"{county.lower()}.csv",
        f"{county.title()}.csv",
        f"{county.upper()}.csv"
    ]
    
    for pattern in patterns:
        file_path = DATA_DIR / pattern
        if file_path.exists():
            return file_path
    
    return None

def prepare_record(row: pd.Series, county: str) -> Dict:
    """Prepare a record for upload - maps NAL columns to florida_parcels schema"""
    # Map NAL columns to our schema
    record = {
        'parcel_id': row.get('PARCEL_ID', row.get('parcel_id', '')),
        'county': county.upper(),
        'year': 2025,  # ASMNT_YR shows 2025
        'owner_name': row.get('OWN_NAME', row.get('owner_name', '')),
        'owner_address': f"{row.get('OWN_ADDR1', '')} {row.get('OWN_ADDR2', '')}".strip(),
        'owner_city': row.get('OWN_CITY', row.get('owner_city', '')),
        'owner_state': row.get('OWN_STATE', row.get('owner_state', '')),
        'owner_zip': str(row.get('OWN_ZIPCD', row.get('owner_zip', ''))),
        'property_address': f"{row.get('PHY_ADDR1', '')} {row.get('PHY_ADDR2', '')}".strip(),
        'property_city': row.get('PHY_CITY', row.get('property_city', '')),
        'property_zip': str(row.get('PHY_ZIPCD', row.get('property_zip', ''))),
        'legal_description': row.get('S_LEGAL', row.get('legal_description', '')),
        'property_use_code': row.get('PA_UC', row.get('property_use_code', '')),
        'subdivision': row.get('NBRHD_CD', row.get('subdivision', '')),
        'tax_district': row.get('DISTR_CD', row.get('tax_district', '')),
        'neighborhood': row.get('NBRHD_CD', row.get('neighborhood', '')),
        'dor_code': row.get('DOR_UC', row.get('dor_code', '')),
        'census_block': row.get('CENSUS_BK', row.get('census_block', '')),
        'market_area': row.get('MKT_AR', row.get('market_area', '')),
        
        # Values
        'total_value': row.get('JV', row.get('total_value')),
        'land_value': row.get('LND_VAL', row.get('land_value')),
        'building_value': row.get('JV', 0) - row.get('LND_VAL', 0) if row.get('JV') and row.get('LND_VAL') else None,
        'assessed_value': row.get('AV_SD', row.get('assessed_value')),
        'exemption_value': row.get('AV_HMSTD', row.get('exemption_value', 0)),
        'taxable_value': row.get('TV_SD', row.get('taxable_value')),
        
        # Building info
        'year_built': row.get('ACT_YR_BLT', row.get('year_built')),
        'effective_year_built': row.get('EFF_YR_BLT', row.get('effective_year_built')),
        'living_area': row.get('TOT_LVG_AREA', row.get('living_area')),
        'total_area': row.get('LND_SQFOOT', row.get('total_area')),
        'building_class': row.get('CONST_CLASS', row.get('building_class', '')),
        'quality': row.get('IMP_QUAL', row.get('quality', '')),
        'condition': row.get('IMP_QUAL', row.get('condition', '')),
        'num_buildings': row.get('NO_BULDNG', row.get('num_buildings')),
        'num_units': row.get('NO_RES_UNTS', row.get('num_units')),
        
        # Sale info
        'sale_price': row.get('SALE_PRC1', row.get('sale_price')),
        'sale_date': f"{row.get('SALE_YR1', '')}-{str(row.get('SALE_MO1', '')).zfill(2)}-01" if row.get('SALE_YR1') and row.get('SALE_MO1') else None,
        'sale_year': row.get('SALE_YR1', row.get('sale_year')),
        'sale_month': row.get('SALE_MO1', row.get('sale_month')),
        'sale_qualification': row.get('QUAL_CD1', row.get('sale_qualification', '')),
        'sale_instrument': row.get('VI_CD1', row.get('sale_instrument', '')),
        'or_book': str(row.get('OR_BOOK1', row.get('or_book', ''))),
        'or_page': str(row.get('OR_PAGE1', row.get('or_page', ''))),
        
        # Exemptions
        'homestead_exemption': row.get('JV_HMSTD', 0) > 0 if row.get('JV_HMSTD') else False,
        'senior_exemption': row.get('EXMPT_03', 0) > 0 if row.get('EXMPT_03') else False,
        'veteran_exemption': row.get('EXMPT_02', 0) > 0 if row.get('EXMPT_02') else False,
        'widow_exemption': row.get('EXMPT_04', 0) > 0 if row.get('EXMPT_04') else False,
        'disability_exemption': row.get('EXMPT_05', 0) > 0 if row.get('EXMPT_05') else False,
        'agricultural_classification': row.get('EXMPT_07', 0) > 0 if row.get('EXMPT_07') else False,
        
        # Land info
        'land_square_footage': row.get('LND_SQFOOT', row.get('land_square_footage')),
        'land_acres': row.get('LND_SQFOOT', 0) / 43560 if row.get('LND_SQFOOT') else None,
        
        # GIS info
        'township': row.get('TWN', row.get('township', '')),
        'range': row.get('RNG', row.get('range', '')),
        'section': row.get('SEC', row.get('section', '')),
        
        # Metadata
        'alt_key': row.get('ALT_KEY', row.get('alt_key', '')),
        'state_parcel_id': row.get('STATE_PAR_ID', row.get('state_parcel_id', '')),
        'last_updated': datetime.now().isoformat()
    }
    
    # Clean numeric fields
    numeric_fields = [
        'total_value', 'land_value', 'building_value',
        'assessed_value', 'exemption_value', 'taxable_value',
        'sale_price', 'living_area', 'total_area', 'land_square_footage',
        'land_acres', 'year_built', 'effective_year_built',
        'num_buildings', 'num_units', 'sale_year', 'sale_month'
    ]
    
    for field in numeric_fields:
        if field in record:
            value = record[field]
            if pd.isna(value) or value == '' or value == 'None':
                record[field] = None
            else:
                try:
                    record[field] = float(value) if field not in ['year_built', 'effective_year_built', 'num_buildings', 'num_units', 'sale_year', 'sale_month'] else int(float(value))
                except:
                    record[field] = None
    
    # Clean string fields - remove None and NaN
    for key, value in record.items():
        if pd.isna(value) or value == 'None':
            record[key] = None if key in numeric_fields else ''
    
    return record

def create_optimized_client() -> Client:
    """Create Supabase client with optimized headers"""
    client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
    
    # Add performance headers to client session if possible
    # These headers optimize REST API performance
    if hasattr(client, 'headers'):
        client.headers.update({
            'Prefer': 'return=minimal,resolution=merge-duplicates,count=none',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    return client

def upload_batch_with_retry(client: Client, records: List[Dict], county: str, batch_num: int) -> Tuple[bool, int]:
    """Upload a batch with retry logic and exponential backoff"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  [{county}] Batch {batch_num}: Uploading {len(records)} records (attempt {attempt + 1})")
            
            # Use upsert with optimized headers
            result = client.table('florida_parcels').upsert(
                records,
                on_conflict='parcel_id,county,year',
                returning='minimal',  # Don't return full records
                count='none'  # Don't count results
            ).execute()
            
            print(f"  [{county}] Batch {batch_num}: SUCCESS")
            return True, len(records)
            
        except Exception as e:
            error_str = str(e)
            
            # Check for rate limiting
            if '429' in error_str:
                # Rate limited - use exponential backoff with jitter
                delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                print(f"  [{county}] Batch {batch_num}: Rate limited, waiting {delay:.1f}s...")
                time.sleep(delay)
                continue
                
            # Check for timeout errors
            elif '57014' in error_str or 'timeout' in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)
                    print(f"  [{county}] Batch {batch_num}: Timeout, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"  [{county}] Batch {batch_num}: FAILED after {MAX_RETRIES} attempts")
                    return False, 0
            else:
                # Non-recoverable error
                print(f"  [{county}] Batch {batch_num}: Error: {error_str[:100]}")
                return False, 0
    
    return False, 0

def upload_county_parallel(county: str, progress: Dict) -> Dict:
    """Upload data for a single county (called by parallel workers)"""
    print(f"\n{'='*60}")
    print(f"Processing {county}")
    print(f"{'='*60}")
    
    # Check if already completed
    county_progress = progress.get(county, {})
    if county_progress.get('status') == 'completed':
        print(f"[COMPLETED] {county} already completed")
        return {'county': county, 'uploaded': county_progress.get('uploaded', 0), 'status': 'completed'}
    
    # Find county file
    file_path = find_county_file(county)
    if not file_path:
        print(f"[ERROR] No file found for {county}")
        return {'county': county, 'uploaded': 0, 'status': 'file_not_found'}
    
    print(f"Reading from: {file_path}")
    
    try:
        # Create optimized client for this thread
        client = create_optimized_client()
        
        # Load data
        df = pd.read_csv(file_path, low_memory=False)
        total_records = len(df)
        print(f"Found {total_records:,} records")
        
        # Skip records that may already be uploaded (for partial counties)
        start_index = county_progress.get('last_index', 0)
        if start_index > 0:
            print(f"Resuming from index {start_index:,}")
            df = df.iloc[start_index:]
        
        # Process in batches
        uploaded_count = county_progress.get('uploaded', 0)
        failed_batches = []
        
        for batch_num, i in enumerate(range(0, len(df), BATCH_SIZE), 1):
            batch_df = df.iloc[i:i+BATCH_SIZE]
            records = [prepare_record(row, county) for _, row in batch_df.iterrows()]
            
            success, count = upload_batch_with_retry(client, records, county, batch_num)
            
            if success:
                uploaded_count += count
                # Update progress
                progress[county] = {
                    'uploaded': uploaded_count,
                    'last_index': start_index + i + len(batch_df),
                    'status': 'in_progress',
                    'timestamp': datetime.now().isoformat()
                }
                save_progress(progress)
            else:
                failed_batches.append(batch_num)
        
        # Mark as completed
        status = 'completed' if not failed_batches else 'partial'
        progress[county] = {
            'uploaded': uploaded_count,
            'total': total_records,
            'status': status,
            'failed_batches': failed_batches,
            'timestamp': datetime.now().isoformat()
        }
        save_progress(progress)
        
        print(f"\n{county} Summary:")
        print(f"  Uploaded: {uploaded_count:,} / {total_records:,}")
        if failed_batches:
            print(f"  Failed batches: {failed_batches}")
        
        return {'county': county, 'uploaded': uploaded_count, 'status': status, 'total': total_records}
        
    except Exception as e:
        print(f"[ERROR] Error processing {county}: {e}")
        traceback.print_exc()
        return {'county': county, 'uploaded': 0, 'status': 'error', 'error': str(e)}

def main():
    """Main upload process with parallel processing"""
    print("="*70)
    print("OPTIMIZED PROPERTY APPRAISER DATA UPLOAD")
    print("="*70)
    print(f"\nTarget: Upload remaining 6.2M records")
    print(f"Batch size: {BATCH_SIZE} records")
    print(f"Parallel workers: {PARALLEL_WORKERS}")
    print(f"Counties to process: {len(COUNTIES_TO_UPLOAD)}")
    
    # Test connection
    print("\nTesting Supabase connection...")
    client = create_optimized_client()
    
    try:
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            print(f"Connected! Current records: {result.count:,}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Load progress
    progress = load_progress()
    
    # Process counties in parallel
    total_uploaded = 0
    failed_counties = []
    results = []
    
    print(f"\nStarting parallel upload with {PARALLEL_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        # Submit all counties to the thread pool
        futures = {
            executor.submit(upload_county_parallel, county, progress): county 
            for county in COUNTIES_TO_UPLOAD.keys()
        }
        
        # Process completed uploads
        for future in as_completed(futures):
            county = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] in ['completed', 'partial']:
                    total_uploaded += result.get('uploaded', 0)
                    print(f"[DONE] {county}: {result.get('uploaded', 0):,} records")
                else:
                    failed_counties.append(county)
                    print(f"[FAILED] {county}: {result.get('status')}")
                    
            except Exception as e:
                print(f"[ERROR] {county}: {e}")
                failed_counties.append(county)
    
    # Final summary
    print("\n" + "="*70)
    print("UPLOAD COMPLETE")
    print("="*70)
    print(f"Total records uploaded: {total_uploaded:,}")
    print(f"Counties processed: {len(COUNTIES_TO_UPLOAD) - len(failed_counties)}")
    if failed_counties:
        print(f"Failed counties: {failed_counties}")
    
    # Verify final count
    print("\nVerifying final database count...")
    result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
    if hasattr(result, 'count'):
        print(f"Total records in database: {result.count:,}")
        print(f"  Expected: 9,758,470")
        print(f"  Completion: {(result.count / 9758470 * 100):.2f}%")
    
    print("\nIMPORTANT: Remember to run restore_timeouts.sql after upload completes!")

if __name__ == "__main__":
    main()