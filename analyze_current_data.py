#!/usr/bin/env python3
"""
Analyze current data in florida_parcels to determine if NAP import is needed
"""

from supabase import create_client, Client
import csv

def main():
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    
    supabase = create_client(url, service_key)
    
    print("=== CURRENT DATA ANALYSIS ===")
    
    # Get total count
    result = supabase.table('florida_parcels').select("*", count="exact").limit(1).execute()
    total_count = result.count if hasattr(result, 'count') else 0
    print(f"Total records: {total_count:,}")
    
    # Get sample of current data
    sample = supabase.table('florida_parcels').select("*").limit(10).execute()
    
    if sample.data:
        print(f"\n=== SAMPLE CURRENT RECORDS ===")
        for i, record in enumerate(sample.data):
            parcel_id = record.get('parcel_id', 'N/A')
            owner_name = record.get('owner_name', 'N/A')
            phy_addr1 = record.get('phy_addr1', 'N/A')
            phy_city = record.get('phy_city', 'N/A')
            just_value = record.get('just_value', 'N/A')
            assessed_value = record.get('assessed_value', 'N/A')
            data_source = record.get('data_source', 'N/A')
            print(f"{i+1:2d}. {parcel_id} | {owner_name[:30]:<30} | {phy_addr1[:25]:<25} | {phy_city:<15} | JV: {just_value} | AV: {assessed_value} | Source: {data_source}")
    
    # Check NAP file samples to compare
    print(f"\n=== NAP FILE SAMPLE FOR COMPARISON ===")
    nap_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAP16P202501.csv"
    
    try:
        with open(nap_file, 'r', encoding='latin1') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            print("NAP Headers:", headers[:10], "...")
            
            for i, row in enumerate(reader):
                if i >= 5:  # Show first 5 rows
                    break
                    
                acct_id = row[1] if len(row) > 1 else 'N/A'
                own_nam = row[15] if len(row) > 15 else 'N/A'  
                phy_addr = row[27] if len(row) > 27 else 'N/A'
                phy_city = row[28] if len(row) > 28 else 'N/A'
                jv_total = row[8] if len(row) > 8 else 'N/A'
                av_total = row[9] if len(row) > 9 else 'N/A'
                
                print(f"NAP {i+1:2d}. {acct_id} | {own_nam[:30]:<30} | {phy_addr[:25]:<25} | {phy_city:<15} | JV: {jv_total} | AV: {av_total}")
    
    except Exception as e:
        print(f"Error reading NAP file: {e}")
    
    # Check if current data is populated with values
    print(f"\n=== DATA COMPLETENESS ANALYSIS ===")
    
    # Count records with values
    try:
        result = supabase.table('florida_parcels').select("*", count="exact").not_.is_('just_value', 'null').limit(1).execute()
        just_value_count = result.count if hasattr(result, 'count') else 0
        
        result = supabase.table('florida_parcels').select("*", count="exact").not_.is_('assessed_value', 'null').limit(1).execute()
        assessed_value_count = result.count if hasattr(result, 'count') else 0
        
        result = supabase.table('florida_parcels').select("*", count="exact").not_.is_('taxable_value', 'null').limit(1).execute()
        taxable_value_count = result.count if hasattr(result, 'count') else 0
        
        print(f"Records with just_value: {just_value_count:,}")
        print(f"Records with assessed_value: {assessed_value_count:,}")
        print(f"Records with taxable_value: {taxable_value_count:,}")
        
        if total_count > 0:
            print(f"Value completeness: {just_value_count/total_count*100:.1f}%")
        
        # Check data sources
        result = supabase.table('florida_parcels').select("data_source", count="exact").limit(1).execute()
        print(f"Current data source: checking...")
        
        # Get unique data sources
        sources = supabase.table('florida_parcels').select("data_source").limit(10).execute()
        if sources.data:
            unique_sources = set(record.get('data_source') for record in sources.data)
            print(f"Data sources found: {unique_sources}")
            
    except Exception as e:
        print(f"Error in completeness analysis: {e}")
    
    print(f"\n=== RECOMMENDATION ===")
    if just_value_count > 50000:  # If we already have substantial value data
        print("Current database appears to have substantial property value data.")
        print("NAP import may be for enhancement rather than initial population.")
        print("Consider:")
        print("1. Create a separate NAP table for comparison")
        print("2. Update specific fields that are missing")
        print("3. Verify data freshness (NAP 2025 vs current data)")
    else:
        print("Current database lacks value data - NAP import recommended.")
        print("Proceed with NAP data import to populate property values.")

if __name__ == "__main__":
    main()