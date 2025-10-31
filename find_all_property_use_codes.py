#!/usr/bin/env python3
"""
Find ALL property_use codes in florida_parcels table
Identify the missing 6.4M properties
"""
import os
from supabase import create_client, Client
from collections import Counter

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("=" * 80)
print("FINDING ALL PROPERTY_USE CODES IN DATABASE")
print("=" * 80)

# Get total
total_result = supabase.table('florida_parcels').select('id', count='exact').limit(1).execute()
total_count = total_result.count if total_result.count else 0
print(f"\nTotal properties in database: {total_count:,}\n")

# Sample 100,000 properties to find ALL unique property_use values
print("Sampling 100,000 properties to find all property_use codes...")
print("(This represents 1% of database and should capture all codes)\n")

sample_result = supabase.table('florida_parcels')\
    .select('property_use')\
    .not_.is_('property_use', 'null')\
    .limit(100000)\
    .execute()

if sample_result.data:
    # Count all unique codes
    use_counter = Counter()
    null_count = 0

    for row in sample_result.data:
        use_code = row.get('property_use')
        if use_code:
            use_counter[use_code] += 1
        else:
            null_count += 1

    print(f"Found {len(use_counter)} unique property_use codes in sample")
    print(f"NULL/empty values: {null_count}\n")

    print("=" * 80)
    print("ALL PROPERTY_USE CODES (sorted by frequency)")
    print("=" * 80)
    print(f"\n{'Code':<15} {'Count':>10} {'% of Sample':>12} {'Category':<30}")
    print("-" * 80)

    # Categorize each code
    def categorize_code(code):
        """Determine category from DOR code"""
        try:
            # Handle string codes
            code_str = str(code).strip()

            # Check text codes first
            if code_str.upper() in ['SFR', 'SFRES', 'RES', 'RESIDENTIAL', 'MFR', 'CONDO']:
                return 'Residential'
            if code_str.upper() in ['COM', 'COMM', 'COMMERCIAL']:
                return 'Commercial'
            if code_str.upper() in ['IND', 'INDUSTRIAL']:
                return 'Industrial'
            if code_str.upper() in ['AGR', 'AG', 'AGRICULTURAL', 'FARM']:
                return 'Agricultural'
            if code_str.upper() in ['VAC', 'VACANT', 'LAND']:
                return 'Vacant Land'
            if code_str.upper() in ['GOV', 'GOVT', 'GOVERNMENT']:
                return 'Government'
            if code_str.upper() in ['INST', 'INSTITUTIONAL', 'CHURCH', 'SCHOOL']:
                return 'Institutional'

            # Try numeric
            code_num = int(code_str.lstrip('0')) if code_str and code_str != '0' else 0

            if code_num in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                return 'Residential'
            elif 10 <= code_num <= 39:
                return 'Commercial'
            elif 40 <= code_num <= 49:
                return 'Industrial'
            elif 51 <= code_num <= 69:
                return 'Agricultural'
            elif 71 <= code_num <= 79:
                return 'Institutional/Conservation'
            elif 81 <= code_num <= 89:
                return 'Government'
            elif code_num == 0 or 90 <= code_num <= 99:
                return 'Vacant Land'
            else:
                return '*** UNKNOWN ***'

        except:
            return '*** INVALID ***'

    # Sort by frequency
    total_sample = len(sample_result.data)
    category_totals = Counter()

    for code, count in use_counter.most_common():
        pct = (count / total_sample) * 100
        category = categorize_code(code)
        category_totals[category] += count
        print(f"{str(code):<15} {count:>10,} {pct:>11.2f}%  {category:<30}")

    # Summary by category
    print("\n" + "=" * 80)
    print("SUMMARY BY CATEGORY (from sample)")
    print("=" * 80)
    print(f"\n{'Category':<30} {'Sample Count':>15} {'% of Sample':>12} {'Est. Total':>15}")
    print("-" * 80)

    for category, count in category_totals.most_common():
        pct = (count / total_sample) * 100
        estimated_total = int((count / total_sample) * total_count)
        print(f"{category:<30} {count:>15,} {pct:>11.2f}%  {estimated_total:>15,}")

    # Now do actual counts for each category
    print("\n" + "=" * 80)
    print("ACTUAL DATABASE COUNTS (querying entire database)")
    print("=" * 80)
    print("\nThis will take a few minutes...\n")

    # Build comprehensive code lists based on what we found
    all_codes_by_category = {}

    for code in use_counter.keys():
        category = categorize_code(code)
        if category not in all_codes_by_category:
            all_codes_by_category[category] = []
        all_codes_by_category[category].append(str(code))

    # Query actual counts
    actual_counts = {}
    total_accounted = 0

    for category, codes in sorted(all_codes_by_category.items()):
        try:
            print(f"Counting {category} ({len(codes)} codes)...")
            result = supabase.table('florida_parcels')\
                .select('id', count='exact')\
                .in_('property_use', codes)\
                .limit(1)\
                .execute()

            count = result.count if result.count else 0
            pct = (count / total_count * 100) if total_count > 0 else 0
            actual_counts[category] = count
            total_accounted += count

            print(f"  {category:<30} {count:>12,} ({pct:>6.2f}%)")

        except Exception as e:
            print(f"  {category:<30} ERROR: {str(e)[:50]}")

    # Find unaccounted
    print("\n" + "=" * 80)
    print("FINAL ACCOUNTING")
    print("=" * 80)

    unaccounted = total_count - total_accounted
    unaccounted_pct = (unaccounted / total_count * 100) if total_count > 0 else 0

    print(f"\nTotal properties:        {total_count:>12,} (100.00%)")
    print(f"Accounted for:           {total_accounted:>12,} ({(total_accounted/total_count*100):>6.2f}%)")
    print(f"UNACCOUNTED:             {unaccounted:>12,} ({unaccounted_pct:>6.2f}%)")

    if unaccounted > 1000:
        print(f"\n*** WARNING: {unaccounted:,} properties still unaccounted! ***")
        print("These may be NULL property_use values or codes not captured in sample.")

    # Save results
    with open('property_use_complete_analysis.txt', 'w') as f:
        f.write("COMPLETE PROPERTY_USE ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total properties: {total_count:,}\n\n")

        f.write("ALL CODES FOUND:\n")
        for code in sorted(use_counter.keys(), key=lambda x: use_counter[x], reverse=True):
            cat = categorize_code(code)
            f.write(f"  {code:<15} -> {cat}\n")

        f.write("\n\nACTUAL COUNTS:\n")
        for category, count in sorted(actual_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_count * 100) if total_count > 0 else 0
            f.write(f"  {category:<30} {count:>12,} ({pct:>6.2f}%)\n")

        f.write(f"\n\nUNACCOUNTED: {unaccounted:,} ({unaccounted_pct:.2f}%)\n")

    print("\nFull analysis saved to: property_use_complete_analysis.txt")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
