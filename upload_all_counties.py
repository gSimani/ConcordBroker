"""
Upload All Property Appraiser Data to Supabase
Processes all 68 Florida counties
"""

import os
import csv
import glob
import json
import time
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

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

def upload_county_data(county_folder: str, status_file: str):
    """Upload data for a single county"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    county_path = os.path.join(base_path, county_folder)
    
    if not os.path.isdir(county_path):
        return 0
    
    # Skip non-county folders
    if county_folder in ['NAL_2025', 'NAL_2025P'] or county_folder.endswith('.json') or county_folder.endswith('.md'):
        return 0
    
    print(f"Processing {county_folder}...")
    
    # Update status file
    with open(status_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Starting {county_folder}\n")
    
    # Get NAL data file - look for NAL*.csv pattern
    nal_path = os.path.join(county_path, 'NAL')
    if not os.path.exists(nal_path):
        print(f"  No NAL folder found for {county_folder}")
        return 0
    
    # Look for NAL*.csv files (e.g., NAL11P202501.csv)
    csv_files = glob.glob(os.path.join(nal_path, 'NAL*.csv'))
    if not csv_files:
        # Try any CSV file
        csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    
    if not csv_files:
        print(f"  No CSV files found for {county_folder}")
        return 0
    
    client = get_supabase_client()
    total_uploaded = 0
    
    for csv_file in csv_files:
        print(f"  Processing {os.path.basename(csv_file)}...")
        
        try:
            # Read CSV in chunks
            chunk_size = 2000  # Smaller chunks for stability
            for chunk_num, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size, 
                                                         low_memory=False, encoding='utf-8', 
                                                         on_bad_lines='skip')):
                
                # Prepare data for upload
                records = []
                for _, row in chunk.iterrows():
                    # Map fields to existing florida_parcels structure - match actual column names
                    record = {
                        'parcel_id': str(row.get('PARCEL_ID', ''))[:100] if pd.notna(row.get('PARCEL_ID')) else None,
                        'county': county_folder,
                        'year': 2025,
                        
                        # Owner information (using 'owner_' prefix as in actual table)
                        'owner_name': str(row.get('OWN_NAME', ''))[:500] if pd.notna(row.get('OWN_NAME')) else None,
                        'owner_addr1': str(row.get('OWN_ADDR1', ''))[:200] if pd.notna(row.get('OWN_ADDR1')) else None,
                        'owner_addr2': str(row.get('OWN_ADDR2', ''))[:200] if pd.notna(row.get('OWN_ADDR2')) else None,
                        'owner_city': str(row.get('OWN_CITY', ''))[:100] if pd.notna(row.get('OWN_CITY')) else None,
                        'owner_state': str(row.get('OWN_STATE', ''))[:50] if pd.notna(row.get('OWN_STATE')) else None,
                        'owner_zip': str(row.get('OWN_ZIPCD', ''))[:20] if pd.notna(row.get('OWN_ZIPCD')) else None,
                        
                        # Property address
                        'phy_addr1': str(row.get('PHY_ADDR1', ''))[:200] if pd.notna(row.get('PHY_ADDR1')) else None,
                        'phy_addr2': str(row.get('PHY_ADDR2', ''))[:200] if pd.notna(row.get('PHY_ADDR2')) else None,
                        'phy_city': str(row.get('PHY_CITY', ''))[:100] if pd.notna(row.get('PHY_CITY')) else None,
                        'phy_zipcd': str(row.get('PHY_ZIPCD', ''))[:20] if pd.notna(row.get('PHY_ZIPCD')) else None,
                        
                        # Values - map to correct column names
                        'just_value': safe_int(row.get('JV')),
                        'taxable_value': safe_int(row.get('TV_SD')),
                        'land_value': safe_int(row.get('LND_VAL')),
                        'land_sqft': safe_int(row.get('LND_SQFOOT')),
                        
                        # Property details
                        'land_use_code': str(row.get('DOR_UC', ''))[:10] if pd.notna(row.get('DOR_UC')) else None,
                        'property_use': str(row.get('DOR_UC', ''))[:10] if pd.notna(row.get('DOR_UC')) else None,
                        
                        # Sales - convert year to proper date format or skip
                        'sale_price': safe_int(row.get('SALE_PRC1')),
                        # Don't include sale_date if we only have year - it expects a timestamp
                        
                        # Legal description
                        'legal_desc': str(row.get('LEGAL1', ''))[:500] if pd.notna(row.get('LEGAL1')) else None,
                    }
                    
                    # Only add if we have a valid parcel_id
                    if record['parcel_id']:
                        records.append(record)
                
                # Upload batch to Supabase
                if records:
                    try:
                        result = client.table('florida_parcels').upsert(
                            records,
                            on_conflict='parcel_id,county,year'
                        ).execute()
                        
                        uploaded = len(records)
                        total_uploaded += uploaded
                        
                        if chunk_num % 10 == 0:  # Print every 10th batch
                            print(f"    Batch {chunk_num + 1}: Uploaded {uploaded} records (Total: {total_uploaded})")
                        
                    except Exception as e:
                        print(f"    Error uploading batch: {str(e)[:100]}")
                        # Continue with next batch instead of stopping
                        continue
                
        except Exception as e:
            print(f"  Error reading file: {str(e)}")
    
    # Update status file with completion
    with open(status_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Completed {county_folder}: {total_uploaded} records\n")
    
    print(f"  Total uploaded for {county_folder}: {total_uploaded}")
    return total_uploaded

def main():
    """Main execution"""
    print("=" * 60)
    print("FLORIDA PROPERTY APPRAISER DATA UPLOAD")
    print("=" * 60)
    
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    status_file = "upload_status.txt"
    
    # Create/clear status file
    with open(status_file, 'w') as f:
        f.write(f"Upload started at {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n")
    
    # Get all county folders
    county_folders = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            if item not in ['NAL_2025', 'NAL_2025P']:
                county_folders.append(item)
    
    county_folders.sort()
    print(f"Found {len(county_folders)} counties to process")
    
    # Process all counties
    total_records = 0
    successful_counties = 0
    failed_counties = []
    
    for i, county in enumerate(county_folders, 1):
        print(f"\n[{i}/{len(county_folders)}] Processing {county}...")
        try:
            records = upload_county_data(county, status_file)
            if records > 0:
                successful_counties += 1
                total_records += records
            time.sleep(0.5)  # Small delay between counties
        except Exception as e:
            print(f"  Failed to process {county}: {str(e)}")
            failed_counties.append(county)
    
    # Final summary
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total records uploaded: {total_records:,}")
    print(f"Counties processed successfully: {successful_counties}/{len(county_folders)}")
    
    if failed_counties:
        print(f"\nFailed counties: {', '.join(failed_counties)}")
    
    # Write final status
    with open(status_file, 'a') as f:
        f.write("=" * 60 + "\n")
        f.write(f"Upload completed at {datetime.now().isoformat()}\n")
        f.write(f"Total records: {total_records}\n")
        f.write(f"Successful counties: {successful_counties}\n")
        if failed_counties:
            f.write(f"Failed counties: {', '.join(failed_counties)}\n")

if __name__ == "__main__":
    main()