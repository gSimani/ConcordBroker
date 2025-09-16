"""
Simple NAP data insert that works with existing table structure
"""

import os
import csv
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not url or not key:
    print("[ERROR] Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(url, key)

def clear_existing_data():
    """Clear existing data from florida_parcels"""
    print("[CLEAR] Removing existing data from florida_parcels...")
    try:
        # Get count first
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        existing_count = result.count or 0
        print(f"[INFO] Found {existing_count} existing records")
        
        if existing_count > 0:
            # Clear the table
            result = supabase.table('florida_parcels').delete().neq('id', 'none').execute()
            print(f"[SUCCESS] Cleared existing data")
        else:
            print(f"[INFO] No existing data to clear")
    except Exception as e:
        print(f"[WARNING] Could not clear existing data: {e}")

def insert_nap_data():
    """Insert NAP data into florida_parcels"""
    
    nap_file = "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\NAP16P202501.csv"
    
    if not os.path.exists(nap_file):
        print(f"[ERROR] NAP file not found: {nap_file}")
        return False
    
    print(f"[START] Processing NAP file: {nap_file}")
    
    # Define field mapping from NAP to florida_parcels
    field_mapping = {
        'PARCEL_ID': 'parcel_id',
        'OWN_NAME': 'owner_name', 
        'OWN_ADDR1': 'owner_addr1',
        'OWN_CITY': 'owner_city',
        'OWN_STATE': 'owner_state',
        'OWN_ZIP': 'owner_zip',
        'PHY_ADDR1': 'phy_addr1',
        'PHY_CITY': 'phy_city',
        'PHY_ZIPCD': 'phy_zipcd',
        'JV': 'just_value',
        'AV_SD': 'assessed_value',
        'TV_SD': 'taxable_value',
        'LV_SD': 'land_value',
        'BV_SD': 'building_value',
        'YR_BLT': 'year_built',
        'TOT_LVG_AREA': 'total_living_area',
        'NO_BULDNG': 'buildings',
        'NO_RES_UNTS': 'units'
    }
    
    batch_size = 500
    batch = []
    total_processed = 0
    successful_inserts = 0
    
    try:
        with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                # Convert NAP row to florida_parcels record
                record = {}
                
                for nap_field, db_field in field_mapping.items():
                    value = row.get(nap_field, '').strip()
                    
                    if value:
                        # Convert numeric fields
                        if db_field in ['just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value']:
                            try:
                                record[db_field] = int(float(value))
                            except:
                                pass
                        elif db_field in ['year_built', 'total_living_area', 'buildings', 'units']:
                            try:
                                record[db_field] = int(float(value))
                            except:
                                pass
                        else:
                            record[db_field] = value
                
                # Only add records with parcel_id
                if record.get('parcel_id'):
                    batch.append(record)
                
                # Process batch
                if len(batch) >= batch_size:
                    success = insert_batch(batch, len(batch))
                    if success:
                        successful_inserts += len(batch)
                    total_processed += len(batch)
                    batch = []
                    
                    if total_processed % 5000 == 0:
                        print(f"[PROGRESS] Processed {total_processed} records, {successful_inserts} successful")
            
            # Process remaining records
            if batch:
                success = insert_batch(batch, len(batch))
                if success:
                    successful_inserts += len(batch)
                total_processed += len(batch)
        
        print(f"\n[COMPLETE] Import finished:")
        print(f"  Total processed: {total_processed}")
        print(f"  Successful inserts: {successful_inserts}")
        print(f"  Success rate: {(successful_inserts/total_processed)*100:.1f}%")
        
        return successful_inserts > 0
        
    except Exception as e:
        print(f"[ERROR] Error processing NAP file: {e}")
        return False

def insert_batch(batch, batch_num):
    """Insert a batch of records"""
    try:
        result = supabase.table('florida_parcels').insert(batch).execute()
        print(f"  [OK] Batch {batch_num}: {len(batch)} records inserted")
        return True
    except Exception as e:
        print(f"  [FAIL] Batch {batch_num} failed: {e}")
        return False

def verify_import():
    """Verify the import was successful"""
    print(f"\n[VERIFY] Checking import results...")
    
    try:
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        total_count = result.count or 0
        print(f"  Total records in database: {total_count}")
        
        # Check a few sample records
        sample = supabase.table('florida_parcels').select('parcel_id, owner_name, phy_addr1, just_value').limit(3).execute()
        if sample.data:
            print(f"  Sample records:")
            for record in sample.data:
                parcel = record.get('parcel_id', 'N/A')
                owner = record.get('owner_name', 'N/A')
                addr = record.get('phy_addr1', 'N/A')
                value = record.get('just_value', 0)
                print(f"    {parcel}: {owner} at {addr} (${value:,})")
        
        return total_count > 0
        
    except Exception as e:
        print(f"  [ERROR] Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("NAP DATA IMPORT - SIMPLE INSERT")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Clear existing data
    clear_existing_data()
    
    # Step 2: Insert NAP data
    success = insert_nap_data()
    
    # Step 3: Verify import
    if success:
        verify_import()
        print("\n[SUCCESS] NAP data import completed!")
        print("[INFO] Your database now contains official Broward County NAP data")
    else:
        print("\n[FAILED] NAP data import encountered errors")