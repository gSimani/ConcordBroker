#!/usr/bin/env python3
"""
Quick NAV Import Test
====================

Simple script to import a small batch of NAV data for testing
"""

import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os

def main():
    # Load environment variables
    load_dotenv('apps/web/.env')
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
    
    print(f"Connecting to: {supabase_url}")
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Read first 100 rows from CSV
    print("Reading CSV data...")
    df = pd.read_csv('TEMP/NAP16P202501.csv', nrows=100)
    
    print(f"Loaded {len(df)} records from CSV")
    print("Sample columns:", list(df.columns)[:10])
    
    # Transform to match simple schema
    records = []
    for _, row in df.iterrows():
        record = {
            'parcel_id': str(row.get('ACCT_ID', '')).strip(),
            'tax_year': 2025,  # From ASMNT_YR
            'just_value': float(row.get('JV_TOTAL', 0) or 0),
            'assessed_value': float(row.get('AV_TOTAL', 0) or 0),
            'taxable_value': float(row.get('TAX_VAL', 0) or 0),
            'land_value': 0.0,  # Not available in NAP
            'building_value': 0.0,  # Not available in NAP
        }
        
        if record['parcel_id']:  # Only add if has parcel_id
            records.append(record)
    
    print(f"Prepared {len(records)} valid records")
    
    if records:
        print("Sample record:", records[0])
        
        # Try inserting first 10 records
        test_batch = records[:10]
        try:
            print("Attempting insert...")
            result = supabase.table('nav_assessments').insert(test_batch).execute()
            print("Success! Inserted records:", len(result.data) if result.data else 0)
        except Exception as e:
            print("Error:", e)
            
            # Check current table count
            try:
                count_result = supabase.table('nav_assessments').select('count', count='exact').execute()
                print("Current table count:", count_result.count)
            except Exception as count_e:
                print("Could not get count:", count_e)

if __name__ == "__main__":
    main()