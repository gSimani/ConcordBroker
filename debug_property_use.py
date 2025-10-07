#!/usr/bin/env python3
"""
Debug script to understand the property_use data structure.
"""

import os
import json
from supabase import create_client, Client

# Set up Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def main():
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase")

        # Try different approaches to get variety
        print("Trying different sampling methods...")

        # Method 1: Get from different offsets
        offsets = [0, 100000, 200000, 300000, 500000, 1000000]
        all_codes = {}

        for offset in offsets:
            print(f"Sampling from offset {offset}...")
            result = supabase.table('florida_parcels').select('property_use').range(offset, offset + 999).execute()

            if result.data:
                for row in result.data:
                    prop_use = row['property_use']
                    if prop_use not in all_codes:
                        all_codes[prop_use] = 0
                    all_codes[prop_use] += 1
                print(f"  Found codes: {list(set(row['property_use'] for row in result.data))}")
            else:
                print(f"  No data at offset {offset}")

        print(f"\nCombined results from all offsets:")
        print(f"Total distinct codes found: {len(all_codes)}")
        for code in sorted(all_codes.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            print(f"  Code '{code}': {all_codes[code]:,} properties")


    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()