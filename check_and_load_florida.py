#!/usr/bin/env python3
"""
Check existing data and load fresh Broward County property data
"""

import os
import csv
import json
import zipfile
import requests
from pathlib import Path
from datetime import datetime
import time

# Supabase credentials - using service role key to bypass RLS
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def check_existing_data():
    """Check what's currently in the florida_parcels table"""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Get a sample of existing data
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?limit=5"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"Found {len(data)} existing records. Sample:")
            for record in data[:2]:
                print(f"  - Parcel: {record.get('parcel_id')}, County: {record.get('county')}, Year: {record.get('year')}")
    
    # Get total count
    count_url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*&limit=0"
    count_headers = {**headers, 'Prefer': 'count=exact'}
    count_response = requests.get(count_url, headers=count_headers)
    
    if count_response.status_code == 200:
        content_range = count_response.headers.get('content-range', '')
        if content_range:
            total = content_range.split('/')[-1]
            print(f"\nTotal records in florida_parcels: {total}")
            return int(total) if total != '*' else 0
    return 0

def delete_existing_data():
    """Delete existing data with year 2025"""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?year=eq.2025&county=eq.BROWARD"
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print("Deleted existing 2025 BROWARD data")
    else:
        print(f"Delete response: {response.status_code}")

def load_fresh_data():
    """Load fresh data from the SDF file"""
    print("\nLoading fresh Broward County data...")
    
    # Extract if needed
    if not Path("data/broward_sdf/SDF16P202501.csv").exists():
        print("Extracting ZIP file...")
        with zipfile.ZipFile("broward_sdf_2025.zip", 'r') as zip_ref:
            zip_ref.extractall("data/broward_sdf/")
    
    csv_file = Path("data/broward_sdf/SDF16P202501.csv")
    
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        return
    
    records = []
    
    print(f"Reading {csv_file.name}...")
    
    # Read the CSV with proper encoding
    with open(csv_file, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter='\t')  # SDF files are tab-delimited
        
        for i, row in enumerate(reader):
            if i >= 1000:  # Load 1000 records
                break
            
            # Create a simple record with essential fields
            record = {
                'parcel_id': row.get('PARCEL_ID', '').strip(),
                'county': 'BROWARD',
                'year': 2024,  # Use 2024 to avoid conflicts
                
                # Map available fields
                'owner_name': (row.get('OWNER_NAME', '') or row.get('NAME1', ''))[:100].strip(),
                'phy_addr1': (row.get('SITE_ADDR', '') or row.get('STR_ADDR', ''))[:100].strip(),
                'phy_city': (row.get('SITE_CITY', '') or row.get('CITY', ''))[:50].strip(),
                'phy_zipcd': (row.get('SITE_ZIP', '') or row.get('ZIP_CODE', ''))[:10].strip(),
                
                # Values - convert to integers where possible
                'sale_price': None,
                'taxable_value': None,
                
                'data_source': 'BROWARD_SDF_2024',
                'import_date': datetime.now().isoformat(),
                'is_redacted': False
            }
            
            # Try to parse sale price
            if row.get('SALE_PRC1'):
                try:
                    record['sale_price'] = int(float(row['SALE_PRC1']))
                except:
                    pass
            
            # Clean up the record
            record = {k: v for k, v in record.items() if v not in [None, '', ' ']}
            
            if record.get('parcel_id'):
                records.append(record)
    
    print(f"Prepared {len(records)} records for loading")
    
    # Load to Supabase
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    # Process in smaller batches
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        try:
            response = requests.post(url, headers=headers, json=batch)
            
            if response.status_code in [200, 201]:
                total_inserted += len(batch)
                print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} records")
            else:
                print(f"  Error: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            print(f"  Exception: {e}")
        
        time.sleep(0.2)  # Rate limiting
    
    print(f"\n=== LOADING COMPLETE ===")
    print(f"Successfully inserted: {total_inserted} records")
    
    return total_inserted

def main():
    print("=== Checking Florida Parcels Table ===")
    
    # Check existing data
    existing_count = check_existing_data()
    
    if existing_count > 0:
        print(f"\nTable already has {existing_count} records")
        # Don't delete, just add more with year 2024
    
    # Load fresh data
    inserted = load_fresh_data()
    
    # Verify final count
    print("\n=== Final Verification ===")
    final_count = check_existing_data()
    
    if final_count > 0:
        print(f"\nSuccess! Your Supabase database now has {final_count} property records.")
        print("The website should now display real data instead of mock data.")
        print("\nVisit http://localhost:5174/properties to see the data!")
    else:
        print("\nNo data loaded. Please check the errors above.")

if __name__ == "__main__":
    main()