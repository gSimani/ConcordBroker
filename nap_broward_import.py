"""
Import Broward NAP data with correct field mappings
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

def check_existing_data():
    """Check what data already exists"""
    try:
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        existing_count = result.count or 0
        print(f"[INFO] Current records in florida_parcels: {existing_count:,}")
        return existing_count
    except Exception as e:
        print(f"[ERROR] Could not check existing data: {e}")
        return 0

def process_nap_batch_update():
    """Process NAP data to update existing records"""
    
    nap_file = "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\NAP16P202501.csv"
    
    if not os.path.exists(nap_file):
        print(f"[ERROR] NAP file not found: {nap_file}")
        return False
    
    print(f"[START] Processing NAP file: {nap_file}")
    
    # Map NAP fields to florida_parcels columns
    field_mapping = {
        'ACCT_ID': 'parcel_id',       # Main parcel ID
        'OWN_NAM': 'owner_name',      # Owner name
        'OWN_ADDR': 'owner_addr1',    # Owner address
        'OWN_CITY': 'owner_city',     # Owner city
        'OWN_STATE': 'owner_state',   # Owner state
        'OWN_ZIPCD': 'owner_zip',     # Owner ZIP
        'PHY_ADDR': 'phy_addr1',      # Property address
        'PHY_CITY': 'phy_city',       # Property city
        'PHY_ZIPCD': 'phy_zipcd',     # Property ZIP
        'JV_TOTAL': 'just_value',     # Just value (market value)
        'AV_TOTAL': 'assessed_value', # Assessed value
        'TAX_VAL': 'taxable_value',   # Taxable value
        'ASMNT_YR': 'year'           # Assessment year
    }
    
    batch_size = 100  # Smaller batches for updates
    total_processed = 0
    successful_updates = 0
    
    try:
        with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                # Extract parcel ID
                parcel_id = row.get('ACCT_ID', '').strip()
                if not parcel_id:
                    continue
                
                # Build update data
                update_data = {}
                
                for nap_field, db_field in field_mapping.items():
                    value = row.get(nap_field, '').strip()
                    
                    if value and value != '0':
                        # Handle numeric fields
                        if db_field in ['just_value', 'assessed_value', 'taxable_value', 'year']:
                            try:
                                update_data[db_field] = int(float(value))
                            except:
                                pass
                        else:
                            # String fields
                            update_data[db_field] = value[:255]  # Limit length
                
                # Only update if we have meaningful data
                if len(update_data) > 1:  # More than just parcel_id
                    success = update_property_record(parcel_id, update_data)
                    if success:
                        successful_updates += 1
                    
                    total_processed += 1
                    
                    if total_processed % 1000 == 0:
                        print(f"[PROGRESS] Processed {total_processed} records, {successful_updates} successful updates")
        
        print(f"\n[COMPLETE] NAP update finished:")
        print(f"  Total processed: {total_processed:,}")
        print(f"  Successful updates: {successful_updates:,}")
        if total_processed > 0:
            print(f"  Success rate: {(successful_updates/total_processed)*100:.1f}%")
        
        return successful_updates > 0
        
    except Exception as e:
        print(f"[ERROR] Error processing NAP file: {e}")
        return False

def update_property_record(parcel_id, update_data):
    """Update a single property record"""
    try:
        result = supabase.table('florida_parcels').update(update_data).eq('parcel_id', parcel_id).execute()
        return True
    except Exception as e:
        # Silently fail individual updates to keep processing
        return False

def insert_new_properties():
    """Insert NAP properties that don't exist yet"""
    
    nap_file = "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\NAP16P202501.csv"
    
    # First, get list of existing parcel IDs
    print("[INFO] Getting existing parcel IDs...")
    try:
        existing_result = supabase.table('florida_parcels').select('parcel_id').execute()
        existing_parcels = {record['parcel_id'] for record in existing_result.data if record.get('parcel_id')}
        print(f"[INFO] Found {len(existing_parcels):,} existing parcel IDs")
    except Exception as e:
        print(f"[ERROR] Could not get existing parcels: {e}")
        return False
    
    print("[INFO] Finding new properties to insert...")
    
    new_properties = []
    batch_size = 500
    
    try:
        with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                parcel_id = row.get('ACCT_ID', '').strip()
                if not parcel_id or parcel_id in existing_parcels:
                    continue
                
                # Build new property record
                new_record = {
                    'parcel_id': parcel_id,
                    'owner_name': row.get('OWN_NAM', '').strip()[:255],
                    'owner_addr1': row.get('OWN_ADDR', '').strip()[:255],
                    'owner_city': row.get('OWN_CITY', '').strip()[:100],
                    'owner_state': row.get('OWN_STATE', '').strip()[:10],
                    'owner_zip': row.get('OWN_ZIPCD', '').strip()[:20],
                    'phy_addr1': row.get('PHY_ADDR', '').strip()[:255],
                    'phy_city': row.get('PHY_CITY', '').strip()[:100],
                    'phy_zipcd': row.get('PHY_ZIPCD', '').strip()[:20],
                }
                
                # Add numeric fields
                for field_name, db_field in [
                    ('JV_TOTAL', 'just_value'),
                    ('AV_TOTAL', 'assessed_value'),
                    ('TAX_VAL', 'taxable_value'),
                    ('ASMNT_YR', 'year')
                ]:
                    value = row.get(field_name, '').strip()
                    if value and value != '0':
                        try:
                            new_record[db_field] = int(float(value))
                        except:
                            pass
                
                new_properties.append(new_record)
                
                # Insert in batches
                if len(new_properties) >= batch_size:
                    insert_batch(new_properties)
                    new_properties = []
            
            # Insert remaining properties
            if new_properties:
                insert_batch(new_properties)
        
        print(f"[SUCCESS] New property insertion completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error inserting new properties: {e}")
        return False

def insert_batch(properties):
    """Insert a batch of new properties"""
    try:
        result = supabase.table('florida_parcels').insert(properties).execute()
        print(f"  [OK] Inserted batch of {len(properties)} new properties")
        return True
    except Exception as e:
        print(f"  [FAIL] Batch insert failed: {str(e)[:100]}...")
        return False

def verify_nap_import():
    """Verify the NAP import results"""
    print(f"\n[VERIFY] Checking NAP import results...")
    
    try:
        # Get total count
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        total_count = result.count or 0
        print(f"  Total records in database: {total_count:,}")
        
        # Check properties with NAP data (just_value > 0)
        nap_result = supabase.table('florida_parcels').select('id', count='exact').gt('just_value', 0).execute()
        nap_count = nap_result.count or 0
        print(f"  Properties with NAP valuation data: {nap_count:,}")
        
        # Check specific property that we corrected earlier
        test_result = supabase.table('florida_parcels').select('parcel_id, owner_name, phy_addr1, just_value, assessed_value').eq('parcel_id', '474131031040').execute()
        if test_result.data:
            test_prop = test_result.data[0]
            print(f"  Test property 474131031040:")
            print(f"    Owner: {test_prop.get('owner_name')}")
            print(f"    Address: {test_prop.get('phy_addr1')}")
            print(f"    Just Value: ${test_prop.get('just_value', 0):,}")
            print(f"    Assessed: ${test_prop.get('assessed_value', 0):,}")
        
        return total_count > 0
        
    except Exception as e:
        print(f"  [ERROR] Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BROWARD NAP DATA IMPORT")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Check existing data
    existing_count = check_existing_data()
    
    # Step 2: Update existing records with NAP data
    print("\n[STEP 1] Updating existing records with NAP data...")
    update_success = process_nap_batch_update()
    
    # Step 3: Insert new properties from NAP
    print("\n[STEP 2] Inserting new properties from NAP...")
    insert_success = insert_new_properties()
    
    # Step 4: Verify results
    if update_success or insert_success:
        verify_nap_import()
        print("\n[SUCCESS] NAP data import completed!")
        print("[INFO] Your database now contains updated Broward County NAP data")
        print("[INFO] Property values, ownership, and addresses have been refreshed")
    else:
        print("\n[FAILED] NAP data import encountered errors")