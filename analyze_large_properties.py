"""
Analyze NAL files for large properties (7,500+ sqft) and compare with Supabase data
"""
import csv
import os
from collections import defaultdict
from pathlib import Path
import json

# Define the base directory
BASE_DIR = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

# Size ranges for analysis
SIZE_RANGES = [
    (7500, 10000, "7,500-10,000 sqft"),
    (10000, 15000, "10,000-15,000 sqft"),
    (15000, 20000, "15,000-20,000 sqft"),
    (20000, 30000, "20,000-30,000 sqft"),
    (30000, 50000, "30,000-50,000 sqft"),
    (50000, float('inf'), "50,000+ sqft")
]

# NAL file column positions (0-indexed)
# Based on Florida DOR NAL format specification
COLUMNS = {
    'PARCEL_ID': 1,      # Column 2 (1-indexed) = 1 (0-indexed)
    'COUNTY': 0,         # Column 1 (1-indexed) = 0 (0-indexed)
    'TOT_LVG_AREA': 49,  # Column 50 (1-indexed) = 49 (0-indexed)
    'DOR_UC': 7,         # Column 8 (1-indexed) = 7 (0-indexed) - DOR Use Code
    'OWN_NAME': 66       # Column 67 (1-indexed) = 66 (0-indexed) - Owner name
}

def extract_county_from_path(file_path):
    """Extract county name from file path"""
    parts = file_path.split(os.sep)
    for i, part in enumerate(parts):
        if part == 'DATABASE PROPERTY APP' and i + 1 < len(parts):
            return parts[i + 1]
    return 'UNKNOWN'

def parse_float(value):
    """Safely parse float value"""
    if not value or value.strip() == '':
        return None
    try:
        return float(value.strip())
    except (ValueError, AttributeError):
        return None

def analyze_nal_file(file_path):
    """Analyze a single NAL file for large properties"""
    print(f"\nAnalyzing: {file_path}")

    county = extract_county_from_path(file_path)
    stats = {
        'county': county,
        'total_records': 0,
        'records_with_living_area': 0,
        'large_properties': defaultdict(int),
        'samples': defaultdict(list)
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)

            # Skip header if present
            try:
                first_row = next(reader)
                # Check if first row looks like data (parcel ID typically starts with digits)
                if not first_row[0].strip()[0].isdigit():
                    pass  # Was a header, continue
                else:
                    # Was data, need to process it
                    stats['total_records'] += 1
                    process_row(first_row, stats)
            except StopIteration:
                return stats

            # Process remaining rows
            for row_num, row in enumerate(reader, start=2):
                stats['total_records'] += 1

                if len(row) <= max(COLUMNS.values()):
                    continue

                process_row(row, stats)

                # Progress indicator
                if stats['total_records'] % 10000 == 0:
                    print(f"  Processed {stats['total_records']:,} records...")

    except Exception as e:
        print(f"  Error reading file: {e}")

    print(f"  Completed: {stats['total_records']:,} total records")
    print(f"  Records with living area: {stats['records_with_living_area']:,}")

    return stats

def process_row(row, stats):
    """Process a single row from NAL file"""
    try:
        living_area = parse_float(row[COLUMNS['TOT_LVG_AREA']])

        if living_area is not None and living_area > 0:
            stats['records_with_living_area'] += 1

            # Check if it's a large property (7,500+ sqft)
            if living_area >= 7500:
                # Categorize into size ranges
                for min_size, max_size, range_label in SIZE_RANGES:
                    if min_size <= living_area < max_size:
                        stats['large_properties'][range_label] += 1

                        # Store sample (limit to 5 per range)
                        if len(stats['samples'][range_label]) < 5:
                            stats['samples'][range_label].append({
                                'parcel_id': row[COLUMNS['PARCEL_ID']].strip(),
                                'living_area': living_area,
                                'dor_uc': row[COLUMNS['DOR_UC']].strip() if len(row) > COLUMNS['DOR_UC'] else '',
                                'owner_name': row[COLUMNS['OWN_NAME']].strip() if len(row) > COLUMNS['OWN_NAME'] else ''
                            })
                        break
    except (IndexError, ValueError) as e:
        pass  # Skip malformed rows

def main():
    """Main analysis function"""
    print("=" * 80)
    print("LARGE PROPERTY ANALYSIS - NAL SOURCE FILES")
    print("=" * 80)

    # Find all NAL files
    nal_files = []
    for county_dir in os.listdir(BASE_DIR):
        county_path = os.path.join(BASE_DIR, county_dir)
        if os.path.isdir(county_path):
            nal_dir = os.path.join(county_path, 'NAL')
            if os.path.isdir(nal_dir):
                for file in os.listdir(nal_dir):
                    if file.startswith('NAL') and file.endswith('.csv'):
                        nal_files.append(os.path.join(nal_dir, file))

    nal_files.sort()
    print(f"\nFound {len(nal_files)} NAL files to analyze\n")

    # Analyze all files
    all_stats = []
    total_counts = defaultdict(int)
    all_samples = defaultdict(list)

    for file_path in nal_files:
        stats = analyze_nal_file(file_path)
        all_stats.append(stats)

        # Aggregate counts
        for range_label, count in stats['large_properties'].items():
            total_counts[range_label] += count

        # Aggregate samples
        for range_label, samples in stats['samples'].items():
            if len(all_samples[range_label]) < 10:  # Keep top 10 samples per range
                all_samples[range_label].extend(samples[:10 - len(all_samples[range_label])])

    # Generate report
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)

    total_large_properties = sum(total_counts.values())
    print(f"\nTotal Large Properties (7,500+ sqft): {total_large_properties:,}")
    print("\nBreakdown by Size Range:")
    print("-" * 80)

    for min_size, max_size, range_label in SIZE_RANGES:
        count = total_counts[range_label]
        percentage = (count / total_large_properties * 100) if total_large_properties > 0 else 0
        print(f"  {range_label:20s}: {count:8,} properties ({percentage:5.1f}%)")

    # Show samples
    print("\n" + "=" * 80)
    print("SAMPLE PROPERTIES FROM EACH RANGE")
    print("=" * 80)

    for min_size, max_size, range_label in SIZE_RANGES:
        if range_label in all_samples and all_samples[range_label]:
            print(f"\n{range_label}:")
            print("-" * 80)
            for i, sample in enumerate(all_samples[range_label][:5], 1):
                print(f"\n  {i}. Parcel ID: {sample['parcel_id']}")
                print(f"     Living Area: {sample['living_area']:,.0f} sqft")
                print(f"     DOR Use Code: {sample['dor_uc']}")
                print(f"     Owner: {sample['owner_name'][:50]}")

    # County breakdown
    print("\n" + "=" * 80)
    print("BREAKDOWN BY COUNTY (Top 20 counties)")
    print("=" * 80)

    county_totals = []
    for stats in all_stats:
        total = sum(stats['large_properties'].values())
        if total > 0:
            county_totals.append((stats['county'], total))

    county_totals.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'County':20s} {'Large Properties':>20s}")
    print("-" * 42)
    for county, count in county_totals[:20]:
        print(f"{county:20s} {count:20,}")

    # Save detailed results to JSON
    output_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\nal_large_properties_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_large_properties': total_large_properties,
                'size_range_counts': dict(total_counts),
                'total_files_analyzed': len(nal_files)
            },
            'county_breakdown': [{'county': c, 'count': cnt} for c, cnt in county_totals],
            'samples': {k: v for k, v in all_samples.items()}
        }, f, indent=2)

    print(f"\n\nDetailed results saved to: {output_file}")

    # Now check Supabase data
    print("\n" + "=" * 80)
    print("COMPARISON WITH SUPABASE DATABASE")
    print("=" * 80)
    print("\nNOTE: Run the following SQL query in Supabase to compare:")
    print("""
    SELECT
        CASE
            WHEN total_living_area >= 7500 AND total_living_area < 10000 THEN '7,500-10,000 sqft'
            WHEN total_living_area >= 10000 AND total_living_area < 15000 THEN '10,000-15,000 sqft'
            WHEN total_living_area >= 15000 AND total_living_area < 20000 THEN '15,000-20,000 sqft'
            WHEN total_living_area >= 20000 AND total_living_area < 30000 THEN '20,000-30,000 sqft'
            WHEN total_living_area >= 30000 AND total_living_area < 50000 THEN '30,000-50,000 sqft'
            WHEN total_living_area >= 50000 THEN '50,000+ sqft'
        END as size_range,
        COUNT(*) as count
    FROM florida_parcels
    WHERE total_living_area >= 7500
    GROUP BY size_range
    ORDER BY MIN(total_living_area);
    """)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()