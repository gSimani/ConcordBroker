#!/usr/bin/env python3
"""
Load BROWARD County Sample Data to Property Appraiser Tables
This script loads a sample of BROWARD county data for testing
"""

import os
import sys
import csv
import json
from datetime import datetime, date
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import httpx
import time

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

# Load environment variables
load_dotenv('.env.mcp')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing Supabase credentials in .env.mcp")
    sys.exit(1)

print("=" * 80)
print("BROWARD COUNTY DATA LOADER")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Database: {SUPABASE_URL}")
print("=" * 80)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Data paths
DATA_BASE_PATH = r"TEMP\DATABASE PROPERTY APP"
BROWARD_PATH = os.path.join(DATA_BASE_PATH, "BROWARD")

def clean_value(value: Any, data_type: str = 'text') -> Any:
    """Clean and convert values based on type"""
    if value is None or value == '' or value == 'NaN':
        return None

    if data_type == 'integer':
        try:
            return int(float(str(value).replace(',', '')))
        except:
            return None
    elif data_type == 'bigint':
        try:
            return int(float(str(value).replace(',', '')))
        except:
            return None
    elif data_type == 'decimal':
        try:
            return float(str(value).replace(',', ''))
        except:
            return None
    elif data_type == 'date':
        # Handle date conversion
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return None
    elif data_type == 'text':
        # Truncate state codes to 2 chars
        val = str(value).strip()
        if 'state' in data_type.lower() and len(val) > 2:
            # Convert full state names to abbreviations
            state_map = {'FLORIDA': 'FL', 'GEORGIA': 'GA', 'NEW YORK': 'NY'}
            return state_map.get(val.upper(), val[:2].upper())
        return val if val else None

    return value

def load_nal_data(limit: int = 100) -> int:
    """Load NAL (Names/Addresses/Legal) data into florida_parcels"""
    print("\n1. LOADING NAL DATA TO florida_parcels")
    print("-" * 40)

    # Try different possible file names
    possible_files = [
        os.path.join(BROWARD_PATH, "NAL", "NAL16P202501.csv"),
        os.path.join(BROWARD_PATH, "NAL", "broward_nal_2025.csv"),
        os.path.join(BROWARD_PATH, "NAL", "NAL.csv")
    ]

    nal_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            nal_file = file_path
            print(f"  [INFO] Found NAL file: {nal_file}")
            break

    # Check if file exists
    if not os.path.exists(nal_file):
        print(f"  [WARNING] NAL file not found: {nal_file}")
        print(f"  [INFO] Creating sample data instead...")
        return create_sample_florida_parcels(limit)

    try:
        records = []
        with open(nal_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                if i >= limit:
                    break

                # Map NAL fields to florida_parcels columns
                record = {
                    'parcel_id': clean_value(row.get('PARCEL_ID'), 'text'),
                    'county': 'BROWARD',
                    'year': 2025,

                    # Physical address
                    'phy_addr1': clean_value(row.get('PHY_ADDR1'), 'text'),
                    'phy_addr2': clean_value(row.get('PHY_ADDR2'), 'text'),
                    'phy_city': clean_value(row.get('PHY_CITY'), 'text'),
                    'phy_zipcd': clean_value(row.get('PHY_ZIPCD'), 'text'),

                    # Owner information
                    'owner_name': clean_value(row.get('OWN_NAME'), 'text'),
                    'owner_addr1': clean_value(row.get('OWN_ADDR1'), 'text'),
                    'owner_addr2': clean_value(row.get('OWN_ADDR2'), 'text'),
                    'owner_city': clean_value(row.get('OWN_CITY'), 'text'),
                    'owner_state': clean_value(row.get('OWN_STATE'), 'text'),
                    'owner_zip': clean_value(row.get('OWN_ZIPCD'), 'text'),

                    # Values
                    'just_value': clean_value(row.get('JV'), 'bigint'),
                    'land_value': clean_value(row.get('LND_VAL'), 'bigint'),
                    'taxable_value': clean_value(row.get('TV_SD'), 'bigint'),

                    # Land info
                    'land_sqft': clean_value(row.get('LND_SQFOOT'), 'bigint'),

                    # Building info
                    'year_built': clean_value(row.get('ACT_YR_BLT'), 'integer'),
                    'total_living_area': clean_value(row.get('TOT_LVG_AREA'), 'integer'),

                    # Sale info
                    'sale_price': clean_value(row.get('SALE_PRC1'), 'bigint'),
                    'sale_yr1': clean_value(row.get('SALE_YR1'), 'integer'),
                    'sale_mo1': clean_value(row.get('SALE_MO1'), 'integer'),

                    # Property use
                    'property_use': clean_value(row.get('DOR_UC'), 'text')
                }

                # Build sale_date from year and month
                if record['sale_yr1'] and record['sale_mo1']:
                    try:
                        record['sale_date'] = f"{record['sale_yr1']}-{record['sale_mo1']:02d}-01"
                    except:
                        record['sale_date'] = None

                # Calculate building_value
                if record['just_value'] and record['land_value']:
                    record['building_value'] = record['just_value'] - record['land_value']

                # Only add if parcel_id exists
                if record['parcel_id']:
                    records.append(record)

        print(f"  [INFO] Loaded {len(records)} records from NAL file")

        # Insert into database
        if records:
            # Insert in batches
            batch_size = 50
            total_inserted = 0

            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                try:
                    response = supabase.table('florida_parcels').upsert(
                        batch,
                        on_conflict='parcel_id'
                    ).execute()
                    total_inserted += len(batch)
                    print(f"  [OK] Inserted batch {i//batch_size + 1}: {len(batch)} records")
                except Exception as e:
                    print(f"  [ERROR] Failed to insert batch: {str(e)[:100]}")

            print(f"  [SUCCESS] Total records inserted: {total_inserted}")
            return total_inserted

    except Exception as e:
        print(f"  [ERROR] Failed to load NAL data: {e}")
        return 0

def create_sample_florida_parcels(count: int = 100) -> int:
    """Create sample florida_parcels data if NAL file not available"""
    print("\n  Creating sample florida_parcels data...")

    sample_records = []
    for i in range(count):
        record = {
            'parcel_id': f'06-42-{str(i+1).zfill(6)}',
            'county': 'BROWARD',
            'year': 2025,
            'owner_name': f'Property Owner {i+1}',
            'phy_addr1': f'{100+i} Main Street',
            'phy_city': 'Fort Lauderdale',
            'phy_zipcd': f'333{str(i % 100).zfill(2)}',
            'owner_addr1': f'{100+i} Main Street',
            'owner_city': 'Fort Lauderdale',
            'owner_state': 'FL',
            'owner_zip': f'333{str(i % 100).zfill(2)}',
            'just_value': 200000 + (i * 1000),
            'land_value': 80000 + (i * 500),
            'building_value': 120000 + (i * 500),
            'taxable_value': 180000 + (i * 900),
            'land_sqft': 5000 + (i * 10),
            'year_built': 1990 + (i % 30),
            'total_living_area': 1500 + (i * 10),
            'sale_price': 195000 + (i * 1000),
            'sale_date': f'202{3 + (i % 2)}-0{1 + (i % 9)}-15',
            'property_use': ['0100', '0200', '0300'][i % 3]
        }
        sample_records.append(record)

    try:
        # Insert in batches
        batch_size = 50
        total_inserted = 0

        for i in range(0, len(sample_records), batch_size):
            batch = sample_records[i:i+batch_size]
            response = supabase.table('florida_parcels').upsert(
                batch,
                on_conflict='parcel_id'
            ).execute()
            total_inserted += len(batch)
            print(f"  [OK] Inserted batch: {len(batch)} records")

        print(f"  [SUCCESS] Created {total_inserted} sample records")
        return total_inserted

    except Exception as e:
        print(f"  [ERROR] Failed to create sample data: {e}")
        return 0

def verify_data_loaded() -> Dict:
    """Verify that data was loaded successfully"""
    print("\n2. VERIFYING DATA LOAD")
    print("-" * 40)

    verification = {}

    # Check florida_parcels
    try:
        response = supabase.table('florida_parcels').select('count', count='exact').execute()
        count = response.count if hasattr(response, 'count') else len(response.data)
        verification['florida_parcels'] = count
        print(f"  florida_parcels: {count} records")

        # Get sample record
        sample = supabase.table('florida_parcels').select('*').limit(1).execute()
        if sample.data:
            print(f"  Sample parcel_id: {sample.data[0].get('parcel_id')}")
            print(f"  Sample address: {sample.data[0].get('phy_addr1')}")

    except Exception as e:
        verification['florida_parcels'] = 0
        print(f"  [ERROR] Could not verify florida_parcels: {e}")

    return verification

def main():
    """Main loading process"""

    # Step 1: Load NAL data
    records_loaded = load_nal_data(limit=100)

    # Step 2: Verify data
    if records_loaded > 0:
        verification = verify_data_loaded()

        # Summary
        print("\n" + "=" * 80)
        print("LOAD SUMMARY")
        print("=" * 80)
        print(f"Records loaded: {records_loaded}")
        print(f"Records verified: {verification.get('florida_parcels', 0)}")

        if verification.get('florida_parcels', 0) > 0:
            print("\n[SUCCESS] Data loaded successfully!")
            print("\nNext steps:")
            print("1. Test frontend: npm run dev")
            print("2. Load more data: python property_appraiser_fast_loader.py")
            print("3. Monitor: Check Supabase Dashboard")
        else:
            print("\n[WARNING] Data loaded but verification failed")

    else:
        print("\n[ERROR] No data was loaded")
        print("\nTroubleshooting:")
        print("1. Check if tables exist in Supabase")
        print("2. Verify NAL file exists at:", os.path.join(BROWARD_PATH, "NAL"))
        print("3. Check Supabase credentials in .env.mcp")

if __name__ == "__main__":
    main()