#!/usr/bin/env python3
"""
Simple NAP Import Status Check
"""

from supabase import create_client, Client

def main():
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    
    supabase = create_client(url, service_key)
    
    print("=== NAP IMPORT STATUS CHECK ===")
    
    try:
        # Total records
        result = supabase.table('florida_parcels').select("*", count="exact").limit(1).execute()
        total_count = result.count if hasattr(result, 'count') else 0
        print(f"Total records: {total_count:,}")
        
        # Records with owner names
        result = supabase.table('florida_parcels').select("*", count="exact").not_.is_('owner_name', 'null').limit(1).execute()
        populated_count = result.count if hasattr(result, 'count') else 0
        print(f"Records with owner names: {populated_count:,}")
        
        # NAP records
        result = supabase.table('florida_parcels').select("*", count="exact").eq('data_source', 'NAP_2025').limit(1).execute()
        nap_count = result.count if hasattr(result, 'count') else 0
        print(f"NAP 2025 records: {nap_count:,}")
        
        # Sample record
        sample = supabase.table('florida_parcels').select("parcel_id,owner_name,phy_addr1,just_value").not_.is_('owner_name', 'null').limit(1).execute()
        if sample.data:
            record = sample.data[0]
            print(f"Sample: {record.get('parcel_id')} | {record.get('owner_name')} | ${record.get('just_value', 0):,.2f}")
        
        print(f"\nImport Progress: {populated_count}/{90508} ({populated_count/90508*100:.1f}%)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()