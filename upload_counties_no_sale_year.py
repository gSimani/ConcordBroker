"""
Fixed Property Appraiser Upload Script - Without sale_year
- Truncates state fields to 2 characters to fix varchar(2) errors
- Excludes sale_year field until PostgREST cache refreshes
- Better error handling and progress monitoring
"""

import os
import csv
import glob
import json
import time
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import traceback

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

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

def get_uploaded_counties():
    """Get list of counties already uploaded"""
    client = get_supabase_client()
    try:
        # Get unique counties in database
        result = client.table('florida_parcels').select('county').execute()
        if result.data:
            counties = set(row['county'] for row in result.data if row.get('county'))
            return counties
    except Exception as e:
        print(f"Error getting uploaded counties: {e}")
    return set()

def upload_county_data(county_folder: str, progress_file: str):
    """Upload data for a single county with fixed state field truncation"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    county_path = os.path.join(base_path, county_folder)
    
    if not os.path.isdir(county_path):
        return 0, "Directory not found"
    
    # Skip non-county folders
    if county_folder in ['NAL_2025', 'NAL_2025P'] or county_folder.endswith('.json') or county_folder.endswith('.md'):
        return 0, "Not a county folder"
    
    print(f"Processing {county_folder}...")
    
    # Update progress file
    with open(progress_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Starting {county_folder}\n")
    
    # Get NAL data file
    nal_path = os.path.join(county_path, 'NAL')
    if not os.path.exists(nal_path):
        print(f"  No NAL folder found for {county_folder}")
        return 0, "No NAL folder"
    
    # Look for CSV files
    csv_files = glob.glob(os.path.join(nal_path, 'NAL*.csv'))
    if not csv_files:
        csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    
    if not csv_files:
        print(f"  No CSV files found for {county_folder}")
        return 0, "No CSV files"
    
    client = get_supabase_client()
    total_uploaded = 0
    errors = []
    
    for csv_file in csv_files:
        print(f"  Processing {os.path.basename(csv_file)}...")
        
        try:
            # Read CSV in larger chunks for speed
            chunk_size = 5000  # Increased from 2000
            total_rows = 0
            
            # First, count total rows for progress
            with open(csv_file, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for line in f) - 1  # Subtract header
            
            print(f"    Total rows to process: {total_rows:,}")
            
            # Process chunks
            for chunk_num, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size, 
                                                         low_memory=False, encoding='utf-8', 
                                                         on_bad_lines='skip')):
                
                # Prepare data for upload
                records = []
                for _, row in chunk.iterrows():
                    try:
                        # Map fields to existing florida_parcels structure
                        # FIX: Truncate state fields to 2 characters
                        # EXCLUDE sale_year until cache refreshes
                        record = {
                            'parcel_id': safe_str(row.get('PARCEL_ID'), 100),
                            'county': county_folder.upper(),
                            'year': 2025,
                            
                            # Owner information
                            'owner_name': safe_str(row.get('OWN_NAME'), 500),
                            'owner_addr1': safe_str(row.get('OWN_ADDR1'), 200),
                            'owner_addr2': safe_str(row.get('OWN_ADDR2'), 200),
                            'owner_city': safe_str(row.get('OWN_CITY'), 100),
                            'owner_state': safe_str(row.get('OWN_STATE'), 2),  # FIX: Truncate to 2 chars
                            'owner_zip': safe_str(row.get('OWN_ZIPCD'), 20),
                            
                            # Property address
                            'phy_addr1': safe_str(row.get('PHY_ADDR1'), 200),
                            'phy_addr2': safe_str(row.get('PHY_ADDR2'), 200),
                            'phy_city': safe_str(row.get('PHY_CITY'), 100),
                            'phy_state': safe_str(row.get('PHY_STATE'), 2),  # FIX: Truncate to 2 chars
                            'phy_zipcd': safe_str(row.get('PHY_ZIPCD'), 20),
                            
                            # Values
                            'just_value': safe_int(row.get('JV')),
                            'taxable_value': safe_int(row.get('TV_SD')),
                            'land_value': safe_int(row.get('LND_VAL')),
                            'land_sqft': safe_int(row.get('LND_SQFOOT')),
                            'building_value': safe_int(row.get('BLD_VAL')),
                            
                            # Property details
                            'land_use_code': safe_str(row.get('DOR_UC'), 10),
                            'property_use': safe_str(row.get('DOR_UC'), 10),
                            'property_use_desc': safe_str(row.get('PA_UC_DESC'), 200),
                            
                            # Sales - only price for now, no sale_year
                            'sale_price': safe_int(row.get('SALE_PRC1')),
                            # 'sale_year': safe_int(row.get('SALE_YR1')),  # EXCLUDED TEMPORARILY
                            
                            # Legal description
                            'legal_desc': safe_str(row.get('LEGAL1'), 500),
                            
                            # Additional fields
                            'year_built': safe_int(row.get('ACT_YR_BLT')),
                            'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
                            'bedrooms': safe_int(row.get('NO_BDRMS')),
                            'bathrooms': safe_int(row.get('NO_BATHS')),
                            
                            # Data tracking
                            'data_source': 'NAL_2025',
                            'import_date': datetime.now().isoformat(),
                        }
                        
                        # Only add if we have a valid parcel_id
                        if record['parcel_id']:
                            records.append(record)
                    except Exception as e:
                        # Log individual record errors but continue
                        errors.append(f"Record error: {str(e)[:100]}")
                        continue
                
                # Upload batch to Supabase
                if records:
                    try:
                        # Use upsert to handle duplicates
                        result = client.table('florida_parcels').upsert(
                            records,
                            on_conflict='parcel_id,county,year'
                        ).execute()
                        
                        uploaded = len(records)
                        total_uploaded += uploaded
                        
                        # Progress update
                        progress = ((chunk_num + 1) * chunk_size / total_rows) * 100
                        print(f"    Progress: {progress:.1f}% - Uploaded {total_uploaded:,} records")
                        
                    except Exception as e:
                        error_msg = f"Batch upload error: {str(e)[:200]}"
                        print(f"    {error_msg}")
                        errors.append(error_msg)
                        # Continue with next batch instead of failing
                        continue
                
        except Exception as e:
            error_msg = f"File processing error: {str(e)}"
            print(f"  {error_msg}")
            errors.append(error_msg)
            traceback.print_exc()
    
    # Update progress file with completion
    with open(progress_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Completed {county_folder}: {total_uploaded} records\n")
        if errors:
            f.write(f"  Errors: {len(errors)}\n")
    
    print(f"  Total uploaded for {county_folder}: {total_uploaded:,}")
    return total_uploaded, errors

def main():
    """Main execution"""
    print("=" * 60)
    print("FLORIDA PROPERTY APPRAISER DATA UPLOAD (NO SALE_YEAR)")
    print("=" * 60)
    
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    progress_file = "upload_progress_no_sale_year.txt"
    
    # Get already uploaded counties
    print("Checking already uploaded counties...")
    uploaded = get_uploaded_counties()
    print(f"Found {len(uploaded)} counties already uploaded: {', '.join(sorted(uploaded))}")
    
    # Create/append to progress file
    with open(progress_file, 'a') as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"Upload resumed at {datetime.now().isoformat()}\n")
        f.write(f"Skipping already uploaded: {', '.join(sorted(uploaded))}\n")
        f.write("=" * 60 + "\n")
    
    # Get all county folders
    county_folders = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            if item not in ['NAL_2025', 'NAL_2025P'] and item.upper() not in uploaded:
                county_folders.append(item)
    
    county_folders.sort()
    print(f"Found {len(county_folders)} counties to process")
    
    if not county_folders:
        print("All counties already uploaded!")
        return
    
    # Process remaining counties
    total_records = 0
    successful_counties = 0
    failed_counties = []
    all_errors = []
    
    for i, county in enumerate(county_folders, 1):
        print(f"\n[{i}/{len(county_folders)}] Processing {county}...")
        try:
            records, errors = upload_county_data(county, progress_file)
            if records > 0:
                successful_counties += 1
                total_records += records
            if errors:
                all_errors.extend(errors)
            time.sleep(1)  # Small delay between counties
        except Exception as e:
            print(f"  Failed to process {county}: {str(e)}")
            failed_counties.append(county)
            traceback.print_exc()
    
    # Final summary
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total new records uploaded: {total_records:,}")
    print(f"Counties processed successfully: {successful_counties}/{len(county_folders)}")
    
    if failed_counties:
        print(f"\nFailed counties: {', '.join(failed_counties)}")
    
    # Write final status
    with open(progress_file, 'a') as f:
        f.write("=" * 60 + "\n")
        f.write(f"Upload completed at {datetime.now().isoformat()}\n")
        f.write(f"Total new records: {total_records}\n")
        f.write(f"Successful counties: {successful_counties}\n")
        if failed_counties:
            f.write(f"Failed counties: {', '.join(failed_counties)}\n")

if __name__ == "__main__":
    main()