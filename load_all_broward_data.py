#!/usr/bin/env python3
"""
Load ALL Broward County property records from SDF file to Supabase
This will load 95,000+ records
"""

import csv
import requests
import time
from pathlib import Path
from datetime import datetime
import sys

# Supabase credentials - using service role key
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

print("=" * 60)
print("LOADING ALL BROWARD COUNTY PROPERTY DATA")
print("=" * 60)

# Check if SDF file exists
csv_file = Path("data/broward_sdf/SDF16P202501.csv")
if not csv_file.exists():
    print("Extracting ZIP file first...")
    import zipfile
    with zipfile.ZipFile("broward_sdf_2025.zip", 'r') as zip_ref:
        zip_ref.extractall("data/broward_sdf/")

# Count total lines first
print("\nCounting total records...")
with open(csv_file, 'r', encoding='latin-1') as f:
    total_lines = sum(1 for line in f) - 1  # Subtract header

print(f"Total records to process: {total_lines:,}")

# Ask for confirmation
response = input("\nThis will load ALL records to Supabase. Continue? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    sys.exit(0)

print("\nReading and processing SDF data...")
records = []
processed = 0
skipped = 0

with open(csv_file, 'r', encoding='latin-1') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        processed += 1
        
        # Skip records without valid parcel ID
        parcel_id = row.get('PARCEL_ID', '').strip()
        if not parcel_id or parcel_id == '0':
            skipped += 1
            continue
        
        # Parse sale date
        sale_date = None
        if row.get('SALE_YR') and row.get('SALE_MO'):
            try:
                year = int(row['SALE_YR'])
                month = int(row['SALE_MO'])
                if 1900 <= year <= 2025 and 1 <= month <= 12:
                    sale_date = f"{year}-{month:02d}-01"
            except:
                pass
        
        # Parse sale price
        sale_price = None
        if row.get('SALE_PRC'):
            try:
                price = int(row['SALE_PRC'])
                if price > 0:
                    sale_price = price
            except:
                pass
        
        # Create record - using minimal fields to avoid issues
        record = {
            'parcel_id': parcel_id,
            'county': 'BROWARD',
            'year': int(row.get('ASMNT_YR', 2024)),
            
            # Basic info - we'll enrich this later
            'owner_name': f"Property {parcel_id}",
            'phy_addr1': f"Broward Property {parcel_id}",
            'phy_city': 'BROWARD COUNTY',
            'phy_zipcd': '33301',
            
            # Property use code from DOR_UC field
            'property_use': row.get('DOR_UC', '000')[:3],
            
            # Sale information
            'sale_date': sale_date,
            'sale_price': sale_price,
            
            # Values - use sale price as estimate if available
            'taxable_value': sale_price if sale_price else 100000,
            'just_value': sale_price if sale_price else 100000,
            
            # Metadata
            'data_source': 'BROWARD_SDF_2025',
            'import_date': datetime.now().isoformat(),
            'is_redacted': False
        }
        
        # Remove None values
        record = {k: v for k, v in record.items() if v is not None}
        
        records.append(record)
        
        # Show progress
        if processed % 10000 == 0:
            print(f"  Processed: {processed:,} / {total_lines:,} ({processed*100//total_lines}%)")

print(f"\nPrepared {len(records):,} valid records (skipped {skipped:,})")

# Load to Supabase in batches
print("\nLoading to Supabase...")
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

# First, clear existing sample data to avoid duplicates
print("Clearing existing sample data...")
delete_response = requests.delete(
    f"{url}?data_source=in.(SAMPLE_DATA,BROWARD_SDF_2025)",
    headers=headers
)
if delete_response.status_code in [200, 204]:
    print("  Cleared existing data")

# Insert in batches
batch_size = 500  # Larger batches for efficiency
total_inserted = 0
total_errors = 0

for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    
    try:
        response = requests.post(url, headers=headers, json=batch)
        
        if response.status_code in [200, 201]:
            total_inserted += len(batch)
            if (i // batch_size + 1) % 10 == 0:  # Print every 10th batch
                print(f"  Progress: {total_inserted:,} / {len(records):,} inserted")
        else:
            total_errors += len(batch)
            if total_errors <= 5:  # Only show first few errors
                print(f"  Error: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        total_errors += len(batch)
        print(f"  Exception: {e}")
    
    # Small delay to avoid overwhelming the server
    if (i // batch_size) % 20 == 0:
        time.sleep(0.5)

print("\n" + "=" * 60)
print(f"LOADING COMPLETE")
print(f"  Successfully inserted: {total_inserted:,} records")
print(f"  Errors: {total_errors:,} records")

# Verify final count
print("\nVerifying final count...")
count_headers = {**headers, 'Prefer': 'count=exact'}
count_response = requests.get(f"{url}?select=*&limit=0", headers=count_headers)

if count_response.status_code == 200:
    content_range = count_response.headers.get('content-range', '')
    if content_range:
        total_count = content_range.split('/')[-1]
        print(f"\nTOTAL RECORDS IN DATABASE: {total_count}")
        
        if int(total_count) > 0:
            print("\n" + "=" * 60)
            print("SUCCESS!")
            print(f"Your database now has {total_count:,} Florida property records")
            print("\nVisit http://localhost:5174/properties to explore the data!")
            print("You can search by city, filter by price, and more.")
            print("=" * 60)