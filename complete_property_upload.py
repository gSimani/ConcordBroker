"""
Complete Property Appraiser Data Upload to Supabase
Uploads remaining 6.2M records using chunked REST API with retry logic
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

# Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Upload parameters
BATCH_SIZE = 500  # Small batches to avoid timeouts
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
PROGRESS_FILE = "upload_progress.json"

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

def load_progress():
    """Load upload progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save upload progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def find_county_file(county: str) -> Path:
    """Find the CSV file for a county"""
    # Try different naming patterns
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
    
    # Try to find any file containing the county name
    for file in DATA_DIR.glob("*.csv"):
        if county.lower() in file.name.lower():
            return file
    
    return None

def prepare_record(row: pd.Series, county: str) -> Dict:
    """Prepare a record for upload"""
    record = row.to_dict()
    
    # Ensure required fields
    record['county'] = county.upper()
    record['year'] = 2024
    
    # Clean numeric fields
    numeric_fields = [
        'total_value', 'land_value', 'building_value',
        'assessed_value', 'exemption_value', 'taxable_value',
        'sale_price', 'living_area', 'total_area',
        'year_built', 'bedrooms', 'bathrooms'
    ]
    
    for field in numeric_fields:
        if field in record:
            value = record[field]
            if pd.isna(value) or value == '' or value == 'None':
                record[field] = None
            else:
                try:
                    record[field] = float(value)
                except:
                    record[field] = None
    
    # Clean date fields
    date_fields = ['sale_date', 'last_updated']
    for field in date_fields:
        if field in record and pd.isna(record[field]):
            record[field] = None
    
    return record

def upload_batch_with_retry(client: Client, records: List[Dict], county: str, batch_num: int) -> Tuple[bool, int]:
    """Upload a batch with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  Batch {batch_num}: Uploading {len(records)} records (attempt {attempt + 1})")
            
            # Upload using upsert to handle duplicates
            result = client.table('florida_parcels').upsert(
                records,
                on_conflict='parcel_id,county,year'
            ).execute()
            
            print(f"  Batch {batch_num}: SUCCESS - {len(records)} records uploaded")
            return True, len(records)
            
        except Exception as e:
            error_str = str(e)
            print(f"  Batch {batch_num}: ERROR - {error_str[:100]}")
            
            # Check for timeout errors
            if '57014' in error_str or 'timeout' in error_str.lower():
                if attempt < MAX_RETRIES - 1:
                    print(f"  Batch {batch_num}: Timeout error, retrying in {RETRY_DELAY * (attempt + 1)} seconds...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print(f"  Batch {batch_num}: FAILED after {MAX_RETRIES} attempts")
                    return False, 0
            else:
                # Non-timeout error, don't retry
                print(f"  Batch {batch_num}: Non-recoverable error: {error_str[:200]}")
                return False, 0
    
    return False, 0

def upload_county(client: Client, county: str, progress: Dict) -> Dict:
    """Upload data for a single county"""
    print(f"\n{'='*60}")
    print(f"Processing {county}")
    print(f"{'='*60}")
    
    # Check if already completed
    county_progress = progress.get(county, {})
    if county_progress.get('status') == 'completed':
        print(f"[COMPLETED] {county} already completed")
        return {'uploaded': county_progress.get('uploaded', 0), 'status': 'completed'}
    
    # Find county file
    file_path = find_county_file(county)
    if not file_path:
        print(f"[ERROR] No file found for {county}")
        return {'uploaded': 0, 'status': 'file_not_found'}
    
    print(f"Reading from: {file_path}")
    
    try:
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
                print(f"  Warning: Batch {batch_num} failed")
        
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
        
        return progress[county]
        
    except Exception as e:
        print(f"[ERROR] Error processing {county}: {e}")
        traceback.print_exc()
        return {'uploaded': 0, 'status': 'error', 'error': str(e)}

def main():
    """Main upload process"""
    print("="*70)
    print("PROPERTY APPRAISER DATA UPLOAD")
    print("="*70)
    print(f"\nTarget: Upload remaining 6.2M records")
    print(f"Batch size: {BATCH_SIZE} records")
    print(f"Max retries: {MAX_RETRIES}")
    print(f"Counties to process: {len(COUNTIES_TO_UPLOAD)}")
    
    # Initialize Supabase client
    print("\nConnecting to Supabase...")
    client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
    
    # Test connection
    try:
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            print(f"Connected! Current records: {result.count:,}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    # Load progress
    progress = load_progress()
    
    # Process each county
    total_uploaded = 0
    failed_counties = []
    
    for county, info in COUNTIES_TO_UPLOAD.items():
        result = upload_county(client, county, progress)
        
        if result['status'] in ['completed', 'partial']:
            total_uploaded += result.get('uploaded', 0)
        else:
            failed_counties.append(county)
        
        # Small delay between counties
        time.sleep(1)
    
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

if __name__ == "__main__":
    main()