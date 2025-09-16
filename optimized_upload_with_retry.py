"""
Optimized Florida Property Upload Script with Retry Logic
Handles statement timeouts gracefully and retries failed batches
"""

import os
import csv
import glob
import time
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import traceback
from typing import List, Dict, Tuple

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Optimized settings
BATCH_SIZE = 500  # Smaller batches to avoid timeouts
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT_CODES = ['57014', '57P01', '57P03']  # Statement timeout codes

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_int(value):
    """Safely convert to integer"""
    if pd.isna(value) or value == '' or value is None:
        return None
    try:
        return int(float(str(value).replace(',', '')))
    except:
        return None

def safe_str(value, max_length=None):
    """Safely convert to string with optional max length"""
    if pd.isna(value) or value is None:
        return None
    result = str(value).strip()
    if max_length and len(result) > max_length:
        result = result[:max_length]
    return result if result else None

def get_counties_status() -> Dict[str, int]:
    """Get current count for each county in database"""
    client = get_supabase_client()
    status = {}
    
    print("Checking current database status...")
    
    # Counties to check
    all_counties = [
        'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD',
        'CALHOUN', 'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA',
        'DADE', 'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER',
        'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON',
        'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
        'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE',
        'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE',
        'MARION', 'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA',
        'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS',
        'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS',
        'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
        'WAKULLA', 'WALTON', 'WASHINGTON'
    ]
    
    for county in all_counties:
        try:
            result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
            if hasattr(result, 'count'):
                status[county] = result.count
        except:
            status[county] = 0
    
    return status

def upload_batch_with_retry(client, records: List[Dict], county: str, batch_num: int) -> Tuple[bool, int]:
    """Upload a batch with retry logic"""
    
    for attempt in range(MAX_RETRIES):
        try:
            # Try to upload
            result = client.table('florida_parcels').upsert(
                records,
                on_conflict='parcel_id,county,year'
            ).execute()
            
            # Success
            return True, len(records)
            
        except Exception as e:
            error_str = str(e)
            error_code = None
            
            # Extract error code if present
            if 'code' in error_str:
                for code in TIMEOUT_CODES:
                    if code in error_str:
                        error_code = code
                        break
            
            # Check if it's a timeout error
            if error_code in TIMEOUT_CODES or 'timeout' in error_str.lower():
                print(f"    Batch {batch_num} attempt {attempt + 1}/{MAX_RETRIES}: Timeout error, retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                continue
            else:
                # Non-timeout error, don't retry
                print(f"    Batch {batch_num}: Non-timeout error: {error_str[:100]}")
                return False, 0
    
    # All retries failed
    print(f"    Batch {batch_num}: Failed after {MAX_RETRIES} attempts")
    return False, 0

def upload_county_optimized(county_folder: str, current_count: int, expected_count: int):
    """Upload county data with optimized batch size and retry logic"""
    
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    county_path = os.path.join(base_path, county_folder)
    
    # Skip if already complete
    if current_count >= expected_count * 0.95:  # 95% threshold
        print(f"  {county_folder}: Already complete ({current_count:,}/{expected_count:,})")
        return 0
    
    # Check for NAL folder
    nal_path = os.path.join(county_path, 'NAL')
    if not os.path.exists(nal_path):
        return 0
    
    # Find CSV files
    csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    if not csv_files:
        return 0
    
    client = get_supabase_client()
    total_uploaded = 0
    total_failed = 0
    
    for csv_file in csv_files:
        print(f"  Processing {os.path.basename(csv_file)}...")
        
        try:
            # Count total rows first
            with open(csv_file, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for line in f) - 1
            
            if total_rows == 0:
                continue
                
            print(f"    Total rows: {total_rows:,} | Current in DB: {current_count:,}")
            
            # Process in smaller chunks
            batch_num = 0
            for chunk in pd.read_csv(csv_file, chunksize=BATCH_SIZE, low_memory=False, encoding='utf-8', on_bad_lines='skip'):
                
                # Prepare records
                records = []
                for _, row in chunk.iterrows():
                    record = {
                        'parcel_id': safe_str(row.get('PARCEL_ID'), 100),
                        'county': county_folder.upper(),
                        'year': 2025,
                        'owner_name': safe_str(row.get('OWN_NAME'), 500),
                        'owner_addr1': safe_str(row.get('OWN_ADDR1'), 200),
                        'owner_addr2': safe_str(row.get('OWN_ADDR2'), 200),
                        'owner_city': safe_str(row.get('OWN_CITY'), 100),
                        'owner_state': safe_str(row.get('OWN_STATE'), 2),
                        'owner_zip': safe_str(row.get('OWN_ZIPCD'), 20),
                        'phy_addr1': safe_str(row.get('PHY_ADDR1'), 200),
                        'phy_addr2': safe_str(row.get('PHY_ADDR2'), 200),
                        'phy_city': safe_str(row.get('PHY_CITY'), 100),
                        'phy_state': safe_str(row.get('PHY_STATE'), 2),
                        'phy_zipcd': safe_str(row.get('PHY_ZIPCD'), 20),
                        'just_value': safe_int(row.get('JV')),
                        'taxable_value': safe_int(row.get('TV_SD')),
                        'land_value': safe_int(row.get('LND_VAL')),
                        'land_sqft': safe_int(row.get('LND_SQFOOT')),
                        'building_value': safe_int(row.get('BLD_VAL')),
                        'land_use_code': safe_str(row.get('DOR_UC'), 10),
                        'property_use': safe_str(row.get('DOR_UC'), 10),
                        'property_use_desc': safe_str(row.get('PA_UC_DESC'), 200),
                        'sale_price': safe_int(row.get('SALE_PRC1')),
                        'sale_year': safe_int(row.get('SALE_YR1')),
                        'legal_desc': safe_str(row.get('LEGAL1'), 500),
                        'year_built': safe_int(row.get('ACT_YR_BLT')),
                        'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
                        'bedrooms': safe_int(row.get('NO_BDRMS')),
                        'bathrooms': safe_int(row.get('NO_BATHS')),
                        'data_source': 'NAL_2025',
                        'import_date': datetime.now().isoformat(),
                    }
                    
                    if record['parcel_id']:
                        records.append(record)
                
                if records:
                    batch_num += 1
                    success, count = upload_batch_with_retry(client, records, county_folder, batch_num)
                    
                    if success:
                        total_uploaded += count
                        if batch_num % 10 == 0:  # Progress every 10 batches
                            print(f"    Progress: {total_uploaded:,} uploaded")
                    else:
                        total_failed += len(records)
                
                # Small delay between batches
                time.sleep(0.1)
                
        except Exception as e:
            print(f"  Error processing file: {e}")
            traceback.print_exc()
    
    print(f"  {county_folder} complete: {total_uploaded:,} uploaded, {total_failed:,} failed")
    return total_uploaded

def main():
    """Main execution"""
    print("=" * 80)
    print("OPTIMIZED FLORIDA PROPERTY UPLOAD WITH RETRY LOGIC")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get current status
    print("\nGetting current database status...")
    county_status = get_counties_status()
    
    # Expected counts
    expected_counts = {
        'BROWARD': 753242, 'DADE': 933276, 'PALM BEACH': 616436,
        'HILLSBOROUGH': 524735, 'ORANGE': 445018, 'PINELLAS': 444821,
        'LEE': 389491, 'POLK': 309595, 'DUVAL': 305928,
        'BREVARD': 283107, 'VOLUSIA': 258456, 'SEMINOLE': 192525,
        'PASCO': 181865, 'COLLIER': 167456, 'SARASOTA': 167214,
        'MANATEE': 156303, 'MARION': 155808, 'OSCEOLA': 136648,
        'LAKE': 135299, 'ST. LUCIE': 134308, 'ESCAMBIA': 123158,
        'LEON': 91766, 'ST. JOHNS': 108775, 'CLAY': 84090,
        'SANTA ROSA': 84548, 'HERNANDO': 84403, 'OKALOOSA': 83351,
        'CHARLOTTE': 82328, 'INDIAN RIVER': 81696
    }
    
    # Prioritize missing/incomplete counties
    counties_to_process = []
    
    # First: Counties with 0 records
    for county, expected in expected_counts.items():
        current = county_status.get(county, 0)
        if current == 0 and expected > 0:
            counties_to_process.append((county, current, expected, 'MISSING'))
    
    # Second: Counties less than 50% complete
    for county, expected in expected_counts.items():
        current = county_status.get(county, 0)
        if 0 < current < expected * 0.5:
            counties_to_process.append((county, current, expected, 'INCOMPLETE'))
    
    # Sort by priority
    counties_to_process.sort(key=lambda x: x[2], reverse=True)  # Largest first
    
    print(f"\nFound {len(counties_to_process)} counties needing upload:")
    for county, current, expected, status in counties_to_process[:10]:
        print(f"  {county}: {current:,}/{expected:,} ({current/expected*100:.1f}%) - {status}")
    
    if not counties_to_process:
        print("\nAll counties appear complete!")
        return
    
    # Process counties
    print("\n" + "=" * 80)
    print("STARTING OPTIMIZED UPLOAD")
    print("=" * 80)
    
    total_new_records = 0
    
    for i, (county, current, expected, status) in enumerate(counties_to_process, 1):
        print(f"\n[{i}/{len(counties_to_process)}] Processing {county} ({status})...")
        
        try:
            uploaded = upload_county_optimized(county, current, expected)
            total_new_records += uploaded
            
            # Check if we should continue
            if i % 5 == 0:  # Every 5 counties
                print(f"\nTotal new records so far: {total_new_records:,}")
                print("Continue? (y/n): ", end='')
                # Auto-continue for automation
                print("y (auto-continue)")
                
        except KeyboardInterrupt:
            print("\n\nUpload interrupted by user")
            break
        except Exception as e:
            print(f"  Failed to process {county}: {e}")
            traceback.print_exc()
    
    # Final summary
    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"Total new records uploaded: {total_new_records:,}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()