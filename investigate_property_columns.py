#!/usr/bin/env python3
"""
CRITICAL INVESTIGATION: Find which column has property classification data
"""
import os
from supabase import create_client, Client
from collections import Counter

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("=" * 80)
print("INVESTIGATING PROPERTY CLASSIFICATION COLUMNS")
print("=" * 80)

# Step 1: Get sample records with ALL columns
print("\n[STEP 1] Getting 1000 sample records with all columns...")

sample = supabase.table('florida_parcels').select('*').limit(1000).execute()

if sample.data and len(sample.data) > 0:
    all_columns = list(sample.data[0].keys())
    print(f"\nTotal columns in table: {len(all_columns)}")

    # Find columns related to property classification
    print("\n[STEP 2] Identifying potential property classification columns...")
    classification_columns = [col for col in all_columns if any(x in col.lower() for x in
        ['use', 'type', 'class', 'category', 'dor', 'uc', 'code'])]

    print(f"\nFound {len(classification_columns)} potential columns:")
    for col in classification_columns:
        print(f"  - {col}")

    # Check each column for data
    print("\n[STEP 3] Analyzing data in each classification column...")
    print("-" * 80)

    for col in classification_columns:
        values = [row.get(col) for row in sample.data]
        non_null = [v for v in values if v is not None and str(v).strip() != '']

        if len(non_null) > 0:
            unique_values = set(non_null)
            value_counts = Counter(non_null)

            print(f"\n[*] Column: {col}")
            print(f"   Non-NULL records: {len(non_null)}/{len(values)} ({len(non_null)/len(values)*100:.1f}%)")
            print(f"   Unique values: {len(unique_values)}")

            if len(unique_values) <= 50:
                print(f"   Top values:")
                for val, count in value_counts.most_common(15):
                    print(f"      {str(val):<20} {count:>4} records")
            else:
                print(f"   Sample values: {list(unique_values)[:10]}")
        else:
            print(f"\n[X] Column: {col}")
            print(f"   ALL NULL or empty")

    # Step 4: Check the most promising column in detail
    print("\n" + "=" * 80)
    print("[STEP 4] Detailed analysis of most promising column")
    print("=" * 80)

    # The DOR uses 'dor_uc' column (DOR Use Code)
    if 'dor_uc' in all_columns:
        print("\n[!] Analyzing 'dor_uc' column (DOR Use Code) - THIS IS LIKELY THE CORRECT COLUMN")

        # Get larger sample of dor_uc values
        dor_sample = supabase.table('florida_parcels').select('dor_uc').limit(10000).execute()

        if dor_sample.data:
            dor_values = [row.get('dor_uc') for row in dor_sample.data if row.get('dor_uc')]
            dor_counter = Counter(dor_values)

            print(f"\nSample size: 10,000 properties")
            print(f"Non-NULL dor_uc: {len(dor_values)} ({len(dor_values)/10000*100:.1f}%)")
            print(f"Unique codes: {len(dor_counter)}")

            print(f"\n{'DOR Code':<15} {'Count':>10} {'Description':<40}")
            print("-" * 70)

            for code, count in dor_counter.most_common(30):
                desc = get_dor_description(code)
                print(f"{str(code):<15} {count:>10,}  {desc:<40}")

        # Now count actual database distribution
        print("\n[STEP 5] Counting properties by DOR code ranges in dor_uc column...")
        print("-" * 80)

        total_result = supabase.table('florida_parcels').select('id', count='exact').limit(1).execute()
        total = total_result.count if total_result.count else 0

        print(f"\nTotal properties: {total:,}")
        print("\nCounting by category (using dor_uc column)...\n")

        categories = {
            'Residential (01-09)': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
            'Commercial (10-39)': [str(i) for i in range(10, 40)],
            'Industrial (40-49)': [str(i) for i in range(40, 50)],
            'Agricultural (51-69)': [str(i) for i in range(51, 70)],
            'Institutional (71-79)': [str(i) for i in range(71, 80)],
            'Government (81-89)': [str(i) for i in range(81, 90)],
            'Vacant (00, 90-99)': ['0', '00'] + [str(i) for i in range(90, 100)],
        }

        total_accounted = 0
        results = {}

        for category, codes in categories.items():
            try:
                result = supabase.table('florida_parcels')\
                    .select('id', count='exact')\
                    .in_('dor_uc', codes)\
                    .limit(1)\
                    .execute()

                count = result.count if result.count else 0
                pct = (count / total * 100) if total > 0 else 0
                results[category] = count
                total_accounted += count

                print(f"{category:<30} {count:>12,} ({pct:>6.2f}%)")

            except Exception as e:
                print(f"{category:<30} ERROR: {str(e)[:40]}")

        unaccounted = total - total_accounted
        unaccounted_pct = (unaccounted / total * 100) if total > 0 else 0

        print("\n" + "=" * 80)
        print(f"Total properties:        {total:>12,}")
        print(f"Accounted for:           {total_accounted:>12,} ({(total_accounted/total*100):>6.2f}%)")
        print(f"UNACCOUNTED:             {unaccounted:>12,} ({unaccounted_pct:>6.2f}%)")
        print("=" * 80)

        if unaccounted > 100000:
            print(f"\n[!] Still {unaccounted:,} unaccounted - checking for NULL values...")

            # Check NULL count
            null_result = supabase.table('florida_parcels')\
                .select('id', count='exact')\
                .is_('dor_uc', 'null')\
                .limit(1)\
                .execute()

            null_count = null_result.count if null_result.count else 0
            print(f"   NULL dor_uc values: {null_count:,} ({null_count/total*100:.2f}%)")

        # Save findings
        with open('CORRECT_PROPERTY_COLUMN_FOUND.txt', 'w') as f:
            f.write("CRITICAL FINDING: CORRECT PROPERTY CLASSIFICATION COLUMN\n")
            f.write("=" * 80 + "\n\n")
            f.write("The correct column is: dor_uc (NOT property_use)\n\n")
            f.write("API BUG: The API was querying the wrong column!\n\n")
            f.write(f"Total properties: {total:,}\n\n")
            f.write("Accurate counts by category:\n")
            for category, count in results.items():
                pct = (count / total * 100) if total > 0 else 0
                f.write(f"  {category:<30} {count:>12,} ({pct:>6.2f}%)\n")
            f.write(f"\nUnaccounted: {unaccounted:,} ({unaccounted_pct:.2f}%)\n")
            f.write(f"NULL values: {null_count:,} ({null_count/total*100:.2f}%)\n")

        print("\n[OK] Findings saved to: CORRECT_PROPERTY_COLUMN_FOUND.txt")

def get_dor_description(code):
    """Get description of DOR code"""
    descriptions = {
        '0': 'Vacant Land',
        '00': 'Vacant Land',
        '01': 'Single Family',
        '1': 'Single Family',
        '02': 'Mobile Home',
        '2': 'Mobile Home',
        '03': 'Multi-Family',
        '3': 'Multi-Family',
        '04': 'Condominium',
        '4': 'Condominium',
    }

    try:
        code_num = int(str(code).lstrip('0')) if code and str(code).strip() and str(code) != '0' else 0
        if code_num in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            return 'Residential'
        elif 10 <= code_num <= 39:
            return 'Commercial'
        elif 40 <= code_num <= 49:
            return 'Industrial'
        elif 51 <= code_num <= 69:
            return 'Agricultural'
        elif 71 <= code_num <= 79:
            return 'Institutional'
        elif 81 <= code_num <= 89:
            return 'Government'
        elif code_num == 0 or 90 <= code_num <= 99:
            return 'Vacant Land'
    except:
        pass

    return descriptions.get(str(code), 'Unknown')

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
