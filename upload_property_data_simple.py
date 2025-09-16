"""
Simple Property Appraiser Data Upload Script
Works with existing florida_parcels table structure
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

def upload_county_data(county_folder: str):
    """Upload data for a single county"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    county_path = os.path.join(base_path, county_folder)
    
    if not os.path.isdir(county_path):
        return 0
    
    # Skip non-county folders
    if county_folder in ['NAL_2025', 'NAL_2025P'] or county_folder.endswith('.json') or county_folder.endswith('.md'):
        return 0
    
    print(f"\nProcessing {county_folder}...")
    
    # Get NAL data file
    nal_path = os.path.join(county_path, 'NAL')
    if not os.path.exists(nal_path):
        print(f"  No NAL folder found for {county_folder}")
        return 0
    
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
            chunk_size = 5000
            for chunk_num, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size, 
                                                         low_memory=False, encoding='utf-8', 
                                                         on_bad_lines='skip')):
                
                # Prepare data for upload
                records = []
                for _, row in chunk.iterrows():
                    # Map fields to existing florida_parcels structure
                    record = {
                        'parcel_id': str(row.get('PARCEL_ID', '')),
                        'county': county_folder,
                        'year': 2025,
                        
                        # Owner information
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
                        
                        # Values
                        'jv': safe_int(row.get('JV')),
                        'tv_sd': safe_int(row.get('TV_SD')),
                        'lnd_val': safe_int(row.get('LND_VAL')),
                        'lnd_sqfoot': safe_int(row.get('LND_SQFOOT')),
                        
                        # Property details
                        'dor_uc': str(row.get('DOR_UC', ''))[:10] if pd.notna(row.get('DOR_UC')) else None,
                        'act_yr_blt': safe_int(row.get('ACT_YR_BLT')),
                        'tot_lvg_area': safe_int(row.get('TOT_LVG_AREA')),
                        
                        # Sales
                        'sale_prc1': safe_int(row.get('SALE_PRC1')),
                        'sale_yr1': str(row.get('SALE_YR1', ''))[:4] if pd.notna(row.get('SALE_YR1')) else None,
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
                        print(f"    Batch {chunk_num + 1}: Uploaded {uploaded} records")
                        
                    except Exception as e:
                        print(f"    Error uploading batch: {str(e)[:100]}")
                        # Try individual uploads for debugging
                        for record in records[:5]:
                            try:
                                client.table('florida_parcels').upsert(record).execute()
                                total_uploaded += 1
                            except Exception as e2:
                                print(f"      Individual upload error: {str(e2)[:50]}")
                                break
                
        except Exception as e:
            print(f"  Error reading file: {str(e)}")
    
    print(f"  Total uploaded for {county_folder}: {total_uploaded}")
    return total_uploaded

def safe_int(value):
    """Safely convert to integer"""
    if pd.isna(value) or value == '' or value is None:
        return None
    try:
        return int(float(str(value).replace(',', '')))
    except:
        return None

def main():
    """Main execution"""
    print("=" * 60)
    print("PROPERTY APPRAISER DATA UPLOAD")
    print("=" * 60)
    
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    # Get all county folders
    county_folders = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            if item not in ['NAL_2025', 'NAL_2025P']:
                county_folders.append(item)
    
    county_folders.sort()
    print(f"Found {len(county_folders)} counties to process")
    
    # Test with first few counties
    test_counties = county_folders[:3]  # Start with 3 counties
    print(f"\nTesting with: {', '.join(test_counties)}")
    
    total_records = 0
    for county in test_counties:
        records = upload_county_data(county)
        total_records += records
        time.sleep(1)  # Small delay between counties
    
    print("\n" + "=" * 60)
    print(f"Upload complete: {total_records} total records")
    print("=" * 60)

if __name__ == "__main__":
    main()