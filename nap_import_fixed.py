"""
Fixed NAP Import - Works after unique constraint is added
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

def import_nap_data():
    """Import NAP data with proper upsert after constraint fix"""
    
    nap_file = "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\NAP16P202501.csv"
    
    if not os.path.exists(nap_file):
        print(f"[ERROR] NAP file not found: {nap_file}")
        return False
    
    print("=" * 60)
    print("NAP DATA IMPORT - FIXED VERSION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Map NAP columns to database fields
    field_mapping = {
        'ACCT_ID': 'parcel_id',
        'OWN_NAM': 'owner_name',
        'OWN_ADDR': 'owner_addr1',
        'OWN_CITY': 'owner_city',
        'OWN_STATE': 'owner_state',
        'OWN_ZIPCD': 'owner_zip',
        'PHY_ADDR': 'phy_addr1',
        'PHY_CITY': 'phy_city',
        'PHY_ZIPCD': 'phy_zipcd',
        'JV_TOTAL': 'just_value',
        'AV_TOTAL': 'assessed_value',
        'TAX_VAL': 'taxable_value',
        'ASMNT_YR': 'year'
    }
    
    batch_size = 500
    batch = []
    total_processed = 0
    successful_imports = 0
    
    print(f"[START] Processing NAP file...")
    print(f"[INFO] Batch size: {batch_size}")
    
    try:
        with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                # Build record
                record = {}
                
                for nap_field, db_field in field_mapping.items():
                    value = row.get(nap_field, '').strip()
                    
                    if value:
                        # Handle numeric fields
                        if db_field in ['just_value', 'assessed_value', 'taxable_value', 'year']:
                            try:
                                record[db_field] = int(float(value))
                            except:
                                pass
                        else:
                            # String fields - limit length
                            if db_field == 'owner_name':
                                record[db_field] = value[:255]
                            elif db_field in ['owner_addr1', 'phy_addr1']:
                                record[db_field] = value[:255]
                            elif db_field in ['owner_city', 'phy_city']:
                                record[db_field] = value[:100]
                            elif db_field in ['owner_state']:
                                record[db_field] = value[:10]
                            elif db_field in ['owner_zip', 'phy_zipcd']:
                                record[db_field] = value[:20]
                            else:
                                record[db_field] = value
                
                # Only process records with parcel_id
                if record.get('parcel_id'):
                    batch.append(record)
                
                # Process batch when full
                if len(batch) >= batch_size:
                    success_count = upsert_batch(batch, total_processed // batch_size + 1)
                    successful_imports += success_count
                    total_processed += len(batch)
                    batch = []
                    
                    if total_processed % 5000 == 0:
                        rate = successful_imports / (total_processed / 1000) if total_processed > 0 else 0
                        print(f"[PROGRESS] {total_processed:,} processed | {successful_imports:,} imported | {rate:.1f} per 1000")
            
            # Process final batch
            if batch:
                success_count = upsert_batch(batch, total_processed // batch_size + 1)
                successful_imports += success_count
                total_processed += len(batch)
        
        print(f"\n[COMPLETE] NAP Import Results:")
        print(f"  Total processed: {total_processed:,}")
        print(f"  Successfully imported: {successful_imports:,}")
        if total_processed > 0:
            print(f"  Success rate: {(successful_imports/total_processed)*100:.1f}%")
        
        return successful_imports > 0
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

def upsert_batch(batch, batch_num):
    """Upsert a batch of records using the unique constraint"""
    try:
        # Use upsert with on_conflict for parcel_id
        result = supabase.table('florida_parcels').upsert(
            batch,
            on_conflict='parcel_id'
        ).execute()
        print(f"  Batch {batch_num}: SUCCESS ({len(batch)} records)")
        return len(batch)
    except Exception as e:
        print(f"  Batch {batch_num}: FAILED - {str(e)[:100]}")
        return 0

def verify_import():
    """Verify import results"""
    print(f"\n[VERIFY] Checking import results...")
    
    try:
        # Total count
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        total = result.count or 0
        print(f"  Total properties: {total:,}")
        
        # Properties with values
        value_result = supabase.table('florida_parcels').select('id', count='exact').gt('just_value', 0).execute()
        with_values = value_result.count or 0
        print(f"  With NAP values: {with_values:,} ({(with_values/total*100):.1f}%)")
        
        # Sample check
        sample = supabase.table('florida_parcels').select(
            'parcel_id, owner_name, phy_addr1, just_value'
        ).gt('just_value', 0).limit(3).execute()
        
        if sample.data:
            print(f"\n  Sample imported properties:")
            for prop in sample.data:
                parcel = prop.get('parcel_id', 'N/A')
                owner = prop.get('owner_name', 'N/A')[:30]
                addr = prop.get('phy_addr1', 'N/A')[:40]
                value = prop.get('just_value', 0)
                print(f"    {parcel}: ${value:,} - {owner} at {addr}")
    
    except Exception as e:
        print(f"  Verification error: {e}")

if __name__ == "__main__":
    # Check if constraint exists first
    print("[CHECK] Verifying database is ready...")
    try:
        # Try a test upsert
        test_record = {'parcel_id': 'TEST123', 'owner_name': 'Test'}
        result = supabase.table('florida_parcels').upsert(
            test_record,
            on_conflict='parcel_id'
        ).execute()
        # Clean up test
        supabase.table('florida_parcels').delete().eq('parcel_id', 'TEST123').execute()
        print("[OK] Database has unique constraint - ready for import!")
    except Exception as e:
        if 'no unique or exclusion constraint' in str(e):
            print("[ERROR] Unique constraint missing!")
            print("\nPlease run this SQL in Supabase first:")
            print("ALTER TABLE florida_parcels ADD CONSTRAINT florida_parcels_parcel_id_unique UNIQUE (parcel_id);")
            sys.exit(1)
    
    # Run import
    success = import_nap_data()
    
    if success:
        verify_import()
        print("\n[SUCCESS] NAP data import completed successfully!")
    else:
        print("\n[FAILED] NAP import encountered errors")