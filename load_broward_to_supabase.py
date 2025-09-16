#!/usr/bin/env python3
"""
Load Broward County property data into Supabase florida_parcels table
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

def extract_zip_files():
    """Extract the Broward County ZIP files"""
    print("Extracting ZIP files...")
    
    # Extract SDF (Sales Data File)
    if Path("broward_sdf_2025.zip").exists():
        with zipfile.ZipFile("broward_sdf_2025.zip", 'r') as zip_ref:
            zip_ref.extractall("data/broward_sdf/")
        print("  - Extracted broward_sdf_2025.zip")
    
    # Extract TPP (Tangible Personal Property)
    if Path("broward_tpp_2025.zip").exists():
        with zipfile.ZipFile("broward_tpp_2025.zip", 'r') as zip_ref:
            zip_ref.extractall("data/broward_tpp/")
        print("  - Extracted broward_tpp_2025.zip")

def find_csv_files():
    """Find all extracted CSV files"""
    csv_files = []
    
    # Check SDF directory
    sdf_path = Path("data/broward_sdf")
    if sdf_path.exists():
        csv_files.extend(list(sdf_path.glob("*.csv")))
        csv_files.extend(list(sdf_path.glob("*.txt")))
    
    # Check TPP directory
    tpp_path = Path("data/broward_tpp")
    if tpp_path.exists():
        csv_files.extend(list(tpp_path.glob("*.csv")))
        csv_files.extend(list(tpp_path.glob("*.txt")))
    
    return csv_files

def parse_sdf_record(row):
    """Parse a record from SDF (Sales Data File) to florida_parcels format"""
    # Map SDF fields to florida_parcels table columns
    # SDF has fields like: PARCEL_ID, SALE_DATE, SALE_PRICE, etc.
    
    parcel = {
        'parcel_id': row.get('PARCEL_ID', '').strip(),
        'county': 'BROWARD',
        'year': 2025,
        
        # Owner information
        'owner_name': row.get('OWNER_NAME', '').strip()[:100] if row.get('OWNER_NAME') else None,
        'owner_addr1': row.get('OWNER_ADDR1', '').strip()[:100] if row.get('OWNER_ADDR1') else None,
        'owner_city': row.get('OWNER_CITY', '').strip()[:50] if row.get('OWNER_CITY') else None,
        'owner_state': row.get('OWNER_STATE', '').strip()[:2] if row.get('OWNER_STATE') else None,
        'owner_zip': row.get('OWNER_ZIP', '').strip()[:10] if row.get('OWNER_ZIP') else None,
        
        # Physical address
        'phy_addr1': row.get('SITE_ADDR', '').strip()[:100] if row.get('SITE_ADDR') else None,
        'phy_city': row.get('SITE_CITY', '').strip()[:50] if row.get('SITE_CITY') else None,
        'phy_zipcd': row.get('SITE_ZIP', '').strip()[:10] if row.get('SITE_ZIP') else None,
        
        # Property details
        'property_use': row.get('USE_CODE', '').strip()[:10] if row.get('USE_CODE') else None,
        'land_use_code': row.get('LAND_USE', '').strip()[:10] if row.get('LAND_USE') else None,
        
        # Values
        'sale_date': row.get('SALE_DATE', '').strip()[:10] if row.get('SALE_DATE') else None,
        'sale_price': int(float(row.get('SALE_PRICE', 0))) if row.get('SALE_PRICE') else None,
        
        # Metadata
        'data_source': 'BROWARD_SDF_2025',
        'import_date': datetime.now().isoformat(),
        'is_redacted': False
    }
    
    # Remove None values
    return {k: v for k, v in parcel.items() if v is not None}

def load_to_supabase(records, batch_size=100):
    """Load records to Supabase florida_parcels table"""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=minimal'  # Use upsert to handle duplicates
    }
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    
    total_inserted = 0
    total_errors = 0
    
    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        try:
            # Use upsert (POST with merge-duplicates)
            response = requests.post(url, headers=headers, json=batch)
            
            if response.status_code in [200, 201]:
                total_inserted += len(batch)
                print(f"  Upserted batch {i//batch_size + 1}: {len(batch)} records")
            else:
                print(f"  Error upserting batch: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                total_errors += len(batch)
                
        except Exception as e:
            print(f"  Exception upserting batch: {e}")
            total_errors += len(batch)
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    return total_inserted, total_errors

def load_sample_data():
    """Load a sample of Broward County data"""
    print("\nLoading Broward County property data to Supabase...")
    
    # Extract ZIP files
    extract_zip_files()
    
    # Find CSV files
    csv_files = find_csv_files()
    print(f"\nFound {len(csv_files)} data files")
    
    if not csv_files:
        print("No data files found. Please ensure ZIP files are in the current directory.")
        return
    
    all_records = []
    
    # Process each CSV file
    for csv_file in csv_files[:1]:  # Start with just the first file
        print(f"\nProcessing: {csv_file.name}")
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(csv_file, 'r', encoding=encoding) as f:
                    # Detect delimiter
                    sample = f.read(1024)
                    f.seek(0)
                    
                    delimiter = '\t' if '\t' in sample else ','
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    # Process records
                    record_count = 0
                    for row in reader:
                        if record_count >= 500:  # Limit to 500 records for testing
                            break
                        
                        # Parse based on file type
                        if 'sdf' in str(csv_file).lower() or 'sale' in str(csv_file).lower():
                            record = parse_sdf_record(row)
                        else:
                            # For TPP or other files, create basic record
                            record = {
                                'parcel_id': row.get('PARCEL_ID', row.get('FOLIO', f"TEMP_{record_count}")).strip(),
                                'county': 'BROWARD',
                                'year': 2025,
                                'owner_name': row.get('OWNER_NAME', row.get('NAME', 'Unknown')).strip()[:100],
                                'data_source': csv_file.name,
                                'import_date': datetime.now().isoformat(),
                                'is_redacted': False
                            }
                        
                        if record.get('parcel_id'):
                            all_records.append(record)
                            record_count += 1
                    
                    print(f"  - Parsed {record_count} records from {csv_file.name}")
                    break  # Successfully read the file
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  - Error reading {csv_file.name}: {e}")
                break
    
    if all_records:
        print(f"\nTotal records to load: {len(all_records)}")
        
        # Load to Supabase
        inserted, errors = load_to_supabase(all_records)
        
        print(f"\n=== LOADING COMPLETE ===")
        print(f"Successfully inserted: {inserted} records")
        print(f"Errors: {errors} records")
        
        # Verify the data
        verify_url = f"{SUPABASE_URL}/rest/v1/florida_parcels?select=*&limit=0"
        headers = {
            'apikey': SUPABASE_KEY,
            'Prefer': 'count=exact'
        }
        
        response = requests.get(verify_url, headers=headers)
        if response.status_code == 200:
            content_range = response.headers.get('content-range', '')
            if content_range:
                total = content_range.split('/')[-1]
                print(f"\nTotal records now in florida_parcels: {total}")
    else:
        print("\nNo records found to load")

if __name__ == "__main__":
    load_sample_data()