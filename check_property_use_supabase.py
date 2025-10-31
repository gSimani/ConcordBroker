#!/usr/bin/env python3
"""
Check property_use values and counts in florida_parcels table
"""
import os
from supabase import create_client, Client

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("=" * 80)
print("PROPERTY_USE VALUES AND COUNTS IN FLORIDA_PARCELS")
print("=" * 80)

# Query property_use distribution
try:
    # Get total count first
    total_result = supabase.table('florida_parcels').select('id', count='exact').limit(1).execute()
    total_count = total_result.count if total_result.count else 0
    print(f"\nTOTAL PROPERTIES IN DATABASE: {total_count:,}\n")

    # Get property_use distribution (top 30 values)
    print("TOP 30 PROPERTY_USE VALUES:\n")
    print(f"{'property_use':<15} {'Count':>12} {'Percentage':>12}")
    print("-" * 42)

    # Query distinct property_use values with counts
    # Note: Supabase doesn't support GROUP BY directly, so we'll query all and count in Python
    # This is a workaround - for large datasets, use RPC or raw SQL

    # Get sample of distinct property_use values
    result = supabase.table('florida_parcels')\
        .select('property_use')\
        .not_.is_('property_use', 'null')\
        .limit(10000)\
        .execute()

    if result.data:
        # Count occurrences
        use_counts = {}
        for row in result.data:
            use = row.get('property_use', 'NULL')
            use_counts[use] = use_counts.get(use, 0) + 1

        # Sort by count
        sorted_uses = sorted(use_counts.items(), key=lambda x: x[1], reverse=True)

        for use_code, count in sorted_uses[:30]:
            percentage = (count / len(result.data)) * 100
            print(f"{str(use_code):<15} {count:>12,} {percentage:>11.2f}%")

    print("\n" + "=" * 80)
    print("TESTING FILTER QUERIES")
    print("=" * 80)

    # Test residential filter (codes 01-09)
    residential_codes = ['01', '02', '03', '04', '05', '06', '07', '08', '09',
                        '1', '2', '3', '4', '5', '6', '7', '8', '9']
    print(f"\nRESIDENTIAL FILTER TEST (codes: {', '.join(residential_codes[:5])}...)")

    res_result = supabase.table('florida_parcels')\
        .select('id', count='exact')\
        .in_('property_use', residential_codes)\
        .limit(1)\
        .execute()

    res_count = res_result.count if res_result.count else 0
    print(f"   Count: {res_count:,} properties")
    print(f"   Percentage: {(res_count/total_count)*100:.2f}%")

    # Test commercial filter (codes 10-39)
    commercial_codes = [str(i) for i in range(10, 40)]  # 10-39
    commercial_codes.extend([f"0{i}" for i in range(10, 40)])  # 010-039
    print(f"\nCOMMERCIAL FILTER TEST (codes: 10-39)")

    com_result = supabase.table('florida_parcels')\
        .select('id', count='exact')\
        .in_('property_use', commercial_codes)\
        .limit(1)\
        .execute()

    com_count = com_result.count if com_result.count else 0
    print(f"   Count: {com_count:,} properties")
    print(f"   Percentage: {(com_count/total_count)*100:.2f}%")

    # Test industrial filter (codes 40-49)
    industrial_codes = [str(i) for i in range(40, 50)]  # 40-49
    industrial_codes.extend([f"0{i}" for i in range(40, 50)])  # 040-049
    print(f"\nINDUSTRIAL FILTER TEST (codes: 40-49)")

    ind_result = supabase.table('florida_parcels')\
        .select('id', count='exact')\
        .in_('property_use', industrial_codes)\
        .limit(1)\
        .execute()

    ind_count = ind_result.count if ind_result.count else 0
    print(f"   Count: {ind_count:,} properties")
    print(f"   Percentage: {(ind_count/total_count)*100:.2f}%")

    print("\n" + "=" * 80)
    print("✅ QUERY COMPLETE")
    print("=" * 80)

except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
