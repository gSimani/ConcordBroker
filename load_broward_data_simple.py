#!/usr/bin/env python3
"""
Simple Property Data Loader for ConcordBroker
Loads Broward County property data to Supabase for immediate frontend use
"""

import pandas as pd
import numpy as np
from supabase import create_client, Client
import json
import os
from datetime import datetime
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Data paths
BROWARD_DATA_PATH = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD"

def load_sample_data():
    """Load a sample of Broward County data for immediate testing"""
    print("ConcordBroker Live Property Data Loader")
    print("=" * 50)

    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("Supabase connection established")

        # Check for NAL file
        nal_file = Path(BROWARD_DATA_PATH) / "NAL2025.csv"
        print(f"Looking for NAL file: {nal_file}")

        if not nal_file.exists():
            print(f"NAL file not found. Checking directory contents...")
            if Path(BROWARD_DATA_PATH).exists():
                files = list(Path(BROWARD_DATA_PATH).glob("*.csv"))
                print(f"Found CSV files: {[f.name for f in files]}")
                if files:
                    nal_file = files[0]  # Use first CSV file found
                    print(f"Using file: {nal_file}")
                else:
                    print("No CSV files found in directory")
                    return False
            else:
                print(f"Directory does not exist: {BROWARD_DATA_PATH}")
                return False

        # Read CSV file (limit to first 1000 records for testing)
        print("Reading CSV file...")
        df = pd.read_csv(nal_file, dtype=str, nrows=1000)
        print(f"Loaded {len(df)} records")
        print(f"Columns available: {list(df.columns)}")

        # Process records
        records = []
        for i, row in df.iterrows():
            try:
                record = {
                    'parcel_id': str(row.get('PARCEL_ID', '')).strip() if pd.notna(row.get('PARCEL_ID')) else f"TEST_{i}",
                    'county': 'BROWARD',
                    'year': 2025,
                    'owner_name': str(row.get('OWN_NAME', '')).strip()[:255] if pd.notna(row.get('OWN_NAME')) else None,
                    'phy_addr1': str(row.get('PHY_ADDR1', '')).strip()[:255] if pd.notna(row.get('PHY_ADDR1')) else None,
                    'property_city': str(row.get('PHY_CITY', '')).strip()[:100] if pd.notna(row.get('PHY_CITY')) else None,
                    'property_zip': str(row.get('PHY_ZIPCD', '')).strip()[:10] if pd.notna(row.get('PHY_ZIPCD')) else None,
                    'created_at': datetime.now().isoformat()
                }

                # Only add records with valid parcel_id
                if record['parcel_id'] and record['parcel_id'] != 'nan':
                    records.append(record)

            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue

        print(f"Processed {len(records)} valid records")

        if not records:
            print("No valid records to upload")
            return False

        # Upload to Supabase in small batches
        batch_size = 100
        uploaded = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                result = supabase.table('florida_parcels').upsert(batch).execute()
                uploaded += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records (Total: {uploaded})")
                time.sleep(0.5)  # Small delay between batches

            except Exception as e:
                print(f"Error uploading batch: {e}")
                # Try individual records if batch fails
                for record in batch:
                    try:
                        supabase.table('florida_parcels').upsert([record]).execute()
                        uploaded += 1
                    except Exception as inner_e:
                        print(f"Failed to upload record {record.get('parcel_id')}: {inner_e}")

        print(f"\nSUCCESS! Uploaded {uploaded} property records")
        print("Visit http://localhost:5173/properties to see the live data")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    load_sample_data()