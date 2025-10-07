#!/usr/bin/env python3
"""
Count total records in florida_parcels table to understand the data size.
"""

from supabase import create_client, Client

# Set up Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def main():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase")

        # Get count of total records
        result = supabase.table('florida_parcels').select('id', count='exact').limit(1).execute()
        print(f"Total records in florida_parcels: {result.count:,}")

        # Test a few very high offsets to see if we can find more variety
        test_offsets = [6000000, 7000000, 8000000, 9000000]

        for offset in test_offsets:
            print(f"\nTesting offset {offset:,}...")
            try:
                result = supabase.table('florida_parcels').select('property_use').range(offset, offset + 99).execute()
                if result.data:
                    codes = list(set(row['property_use'] for row in result.data))
                    print(f"  Found codes: {sorted(codes, key=lambda x: int(x) if x.isdigit() else 999)}")
                else:
                    print(f"  No data at offset {offset:,}")
            except Exception as e:
                print(f"  Error at offset {offset:,}: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()