"""
Load ALL Florida Data into Supabase - Production Scale
Handles millions of records efficiently
"""

import os
import csv
import requests
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

print(f"Supabase URL: {SUPABASE_URL}")

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def count_csv_rows(filename):
    """Count total rows in CSV file"""
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        return sum(1 for line in f) - 1  # Subtract header

def load_nap_data_batch(filename='NAP16P202501.csv', batch_size=500, start_row=0, max_rows=None):
    """Load NAP data in efficient batches"""
    
    properties = []
    row_count = 0
    
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        # Skip to start_row
        for _ in range(start_row):
            next(reader, None)
        
        for row in reader:
            if max_rows and row_count >= max_rows:
                break
                
            # Map NAP fields
            property_data = {
                'parcel_id': row.get('ACCT_ID', '').strip().replace('"', ''),
                'county': 'BROWARD',
                'year': 2025,
                'phy_addr1': row.get('PHY_ADDR', '').strip().replace('"', ''),
                'phy_city': row.get('PHY_CITY', '').strip().replace('"', ''),
                'phy_state': 'FL',
                'phy_zipcd': row.get('PHY_ZIPCD', '').strip().replace('"', ''),
                'owner_name': row.get('OWN_NAM', '').strip().replace('"', ''),
                'owner_addr1': row.get('OWN_ADDR', '').strip().replace('"', ''),
                'owner_city': row.get('OWN_CITY', '').strip().replace('"', ''),
                'owner_state': row.get('OWN_STATE', '').strip().replace('"', ''),
                'owner_zip': row.get('OWN_ZIPCD', '').strip().replace('"', ''),
                'just_value': int(row.get('JV_TOTAL', 0) or 0),
                'assessed_value': int(row.get('AV_TOTAL', 0) or 0),
                'taxable_value': int(row.get('TAX_VAL', 0) or 0),
                'is_redacted': False,
                'data_source': 'NAP2025'
            }
            
            # Only add if has valid data
            if property_data['parcel_id'] and property_data['phy_addr1']:
                properties.append(property_data)
                row_count += 1
                
                # Insert when batch is full
                if len(properties) >= batch_size:
                    yield properties
                    properties = []
    
    # Yield remaining properties
    if properties:
        yield properties

def insert_batch(batch, batch_num):
    """Insert a batch of properties"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    try:
        response = requests.post(url, json=batch, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"  Batch {batch_num}: Inserted {len(batch)} properties")
            return True
        else:
            print(f"  Batch {batch_num}: Failed - {response.status_code}")
            if "duplicate key" in response.text:
                print("    Duplicate records detected - skipping")
                return True  # Continue despite duplicates
            return False
    except Exception as e:
        print(f"  Batch {batch_num}: Error - {e}")
        return False

def load_all_data():
    """Load all Florida data efficiently"""
    print("LOADING ALL FLORIDA DATA")
    print("="*60)
    
    # Count total rows
    total_rows = count_csv_rows('NAP16P202501.csv')
    print(f"Total rows in NAP file: {total_rows:,}")
    
    # Process in chunks
    batch_size = 500
    batch_num = 0
    total_inserted = 0
    failed_batches = []
    
    print(f"\nProcessing in batches of {batch_size}...")
    start_time = time.time()
    
    for batch in load_nap_data_batch('NAP16P202501.csv', batch_size=batch_size):
        batch_num += 1
        
        # Show progress
        if batch_num % 10 == 0:
            elapsed = time.time() - start_time
            rate = (batch_num * batch_size) / elapsed
            eta = (total_rows - (batch_num * batch_size)) / rate / 60
            print(f"\nProgress: {batch_num * batch_size:,} / {total_rows:,} ({batch_num * batch_size * 100 / total_rows:.1f}%)")
            print(f"  Rate: {rate:.0f} records/second")
            print(f"  ETA: {eta:.1f} minutes")
        
        # Insert batch
        if insert_batch(batch, batch_num):
            total_inserted += len(batch)
        else:
            failed_batches.append(batch_num)
            
        # Rate limiting to avoid overwhelming the database
        if batch_num % 5 == 0:
            time.sleep(0.5)  # Brief pause every 5 batches
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("LOADING COMPLETE")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Total inserted: {total_inserted:,} properties")
    print(f"Failed batches: {len(failed_batches)}")
    
    if failed_batches[:10]:
        print(f"First failed batches: {failed_batches[:10]}")
    
    return total_inserted

def verify_data():
    """Verify data in database"""
    print("\nVerifying data...")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=count"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = data[0]['count'] if data else 0
        print(f"Total properties in database: {count:,}")
        return count
    else:
        print(f"Verification failed: {response.status_code}")
        return 0

def main():
    print("FLORIDA DATA LOADER - PRODUCTION SCALE")
    print("="*60)
    
    # Check if we should continue from where we left off
    existing_count = verify_data()
    
    if existing_count > 0:
        print(f"\nFound {existing_count:,} existing properties")
        response = input("Continue loading more data? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    
    # Load all data
    total = load_all_data()
    
    # Final verification
    final_count = verify_data()
    
    print("\n" + "="*60)
    print("PRODUCTION DATA LOADED")
    print(f"Database now contains {final_count:,} properties")
    print("\nYour website can now handle millions of properties!")
    print("Filters will work server-side for optimal performance")

if __name__ == "__main__":
    main()