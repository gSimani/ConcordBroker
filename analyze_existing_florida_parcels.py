#!/usr/bin/env python3
"""
Analyze existing florida_parcels table structure to understand data format
"""

from supabase import create_client, Client

def main():
    # Use explicit credentials
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    
    supabase: Client = create_client(url, service_key)
    
    print("=== EXISTING FLORIDA_PARCELS TABLE ANALYSIS ===")
    
    try:
        # Get sample records to see structure
        result = supabase.table('florida_parcels').select("*").limit(5).execute()
        
        if result.data:
            print(f"\nSample records found: {len(result.data)}")
            
            # Show column structure from first record
            first_record = result.data[0]
            print(f"\n=== COLUMN STRUCTURE ===")
            print(f"Total columns: {len(first_record.keys())}")
            
            columns = list(first_record.keys())
            for i, col in enumerate(columns):
                value = first_record.get(col, '')
                value_type = type(value).__name__
                value_preview = str(value)[:50] if value else "NULL"
                print(f"{i+1:2d}. {col:<25} {value_type:<10} {value_preview}")
            
            print(f"\n=== SAMPLE RECORDS ===")
            for i, record in enumerate(result.data):
                print(f"\nRecord {i+1}:")
                # Show key fields
                key_fields = ['acct_id', 'phy_addr', 'own_nam', 'phy_city', 'phy_zipcd']
                for field in key_fields:
                    if field in record:
                        print(f"  {field}: {record.get(field, 'N/A')}")
        
        else:
            print("No records found in florida_parcels table")
            
    except Exception as e:
        print(f"Error analyzing table: {e}")
        
    # Check total count again
    try:
        count_result = supabase.table('florida_parcels').select("*", count="exact").limit(1).execute()
        total_count = count_result.count if hasattr(count_result, 'count') else "Unknown"
        print(f"\n=== RECORD COUNT ===")
        print(f"Total records in florida_parcels: {total_count}")
    except Exception as e:
        print(f"Error getting count: {e}")

if __name__ == "__main__":
    main()