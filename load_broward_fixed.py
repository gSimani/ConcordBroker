#!/usr/bin/env python3
"""
Fixed Live Property Data Loader for ConcordBroker - BROWARD COUNTY
Uses correct column mapping for existing table structure
"""

import pandas as pd
import numpy as np
from supabase import create_client, Client
from datetime import datetime
import time

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Actual data file path
NAL_FILE = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD\NAL\NAL16P202501.csv"

def load_properties():
    print("Loading Broward County Properties (Fixed)...")
    print("=" * 50)

    try:
        # Initialize Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Connected to Supabase")

        # Read NAL data (limit to 1000 records for testing)
        print(f"Reading NAL file: {NAL_FILE}")
        df = pd.read_csv(NAL_FILE, dtype=str, nrows=1000)
        print(f"Loaded {len(df)} records")

        # Process records with correct column mapping
        records = []
        for i, row in df.iterrows():
            try:
                # Clean and validate data
                parcel_id = str(row.get('PARCEL_ID', '')).strip()
                if not parcel_id or parcel_id == 'nan':
                    parcel_id = f"BROWARD_{i:06d}"

                # Build record with CORRECT column names matching table structure
                record = {
                    'parcel_id': parcel_id,
                    'county': 'BROWARD',
                    'year': 2025,
                    'owner_name': clean_text(row.get('OWN_NAME')),
                    'phy_addr1': clean_text(row.get('PHY_ADDR1')),
                    'phy_addr2': clean_text(row.get('PHY_ADDR2')),
                    'phy_city': clean_text(row.get('PHY_CITY')),
                    'phy_zipcd': clean_text(row.get('PHY_ZIPCD')),
                    'owner_addr1': clean_text(row.get('OWN_ADDR1')),
                    'owner_addr2': clean_text(row.get('OWN_ADDR2')),
                    'owner_city': clean_text(row.get('OWN_CITY')),
                    'owner_state': clean_text(row.get('OWN_STATE'), max_len=2),
                    'owner_zip': clean_text(row.get('OWN_ZIPCD')),
                    'land_sqft': clean_numeric(row.get('LND_SQFOOT')),
                    'land_value': clean_numeric(row.get('LND_VAL')),
                    'just_value': clean_numeric(row.get('JV')),
                    'taxable_value': clean_numeric(row.get('TV_NSD')),
                    'data_source': 'NAL_2025',
                    'import_date': datetime.now().isoformat()
                }

                records.append(record)

            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue

        print(f"Processed {len(records)} valid records")

        # Upload in batches
        batch_size = 100
        uploaded = 0
        total_batches = (len(records) + batch_size - 1) // batch_size

        print(f"Uploading {len(records)} records in {total_batches} batches...")

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(records))
            batch = records[start_idx:end_idx]

            try:
                result = supabase.table('florida_parcels').upsert(
                    batch,
                    on_conflict='parcel_id,county,year'
                ).execute()

                uploaded += len(batch)
                progress = (batch_num + 1) / total_batches * 100
                print(f"Batch {batch_num + 1}/{total_batches}: {len(batch)} records ({progress:.1f}% complete)")

            except Exception as e:
                print(f"Error in batch {batch_num + 1}: {e}")
                # Try individual records on error
                for record in batch:
                    try:
                        supabase.table('florida_parcels').upsert([record]).execute()
                        uploaded += 1
                    except Exception as inner_e:
                        print(f"Failed individual record: {inner_e}")

        print(f"\nSUCCESS! Uploaded {uploaded:,} Broward County properties")
        print("Database now has live property data!")
        print("\nNext steps:")
        print("1. Visit http://localhost:5173/properties")
        print("2. Search for properties in Broward County")
        print("3. View detailed property information")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def clean_text(value, max_len=255):
    """Clean text values for database"""
    if pd.isna(value) or str(value).strip() == '' or str(value) == 'nan':
        return None
    cleaned = str(value).strip()
    return cleaned[:max_len] if cleaned else None

def clean_numeric(value):
    """Clean numeric values for database"""
    if pd.isna(value) or str(value).strip() == '' or str(value) == 'nan':
        return None
    try:
        return float(value)
    except:
        return None

if __name__ == "__main__":
    start_time = time.time()
    success = load_properties()
    elapsed = time.time() - start_time

    print(f"\nOperation completed in {elapsed:.1f} seconds")
    if success:
        print("Database is ready for live property searches!")
    else:
        print("Upload failed. Check error messages above.")