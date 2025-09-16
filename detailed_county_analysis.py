#!/usr/bin/env python3
"""
Detailed Analysis of Florida County Data with Database Comparison
"""

import json
import os

def main():
    """Create detailed analysis report"""

    # Load the inventory data
    with open('county_data_inventory.json', 'r') as f:
        inventory = json.load(f)

    print("DETAILED FLORIDA COUNTY DATA ANALYSIS")
    print("=" * 60)

    # Get current database record counts (simplified - would need actual DB connection)
    # For now, we'll focus on the file inventory analysis

    # Categorize counties
    complete_counties = [c for c in inventory['counties'] if c['completeness_score'] == 100]
    partial_counties = [c for c in inventory['counties'] if 0 < c['completeness_score'] < 100]
    empty_counties = [c for c in inventory['counties'] if c['completeness_score'] == 0]

    print(f"\nDATA COMPLETENESS OVERVIEW:")
    print(f"Complete counties: {len(complete_counties)} (have all 4 data types)")
    print(f"Partial counties: {len(partial_counties)} (missing some data types)")
    print(f"Empty counties: {len(empty_counties)} (no data)")

    # Detailed analysis of problem counties
    print(f"\nPROBLEM COUNTIES ANALYSIS:")
    print("-" * 40)

    for county in partial_counties:
        missing_types = [dt for dt in county['data_types'] if not county['data_types'][dt]['available']]
        available_types = [dt for dt in county['data_types'] if county['data_types'][dt]['available']]

        print(f"\n{county['county']} ({county['completeness_score']}% complete):")
        print(f"  Available: {', '.join(available_types)}")
        print(f"  Missing: {', '.join(missing_types)}")

        # Show file details for available types
        for data_type in available_types:
            files = county['data_types'][data_type]['files']
            size_mb = county['data_types'][data_type]['total_size_mb']
            print(f"     {data_type}: {len(files)} files, {size_mb:.1f} MB")

    for county in empty_counties:
        print(f"\n{county['county']} (No data):")
        print(f"  Issues: {', '.join(county['issues']) if county['issues'] else 'No data files found'}")

    # Analysis of complete counties by size
    print(f"\nCOMPLETE COUNTIES BY SIZE:")
    print("-" * 40)

    complete_by_size = sorted(complete_counties, key=lambda x: x['total_size_mb'], reverse=True)

    print("\nTop 10 Largest:")
    for i, county in enumerate(complete_by_size[:10], 1):
        total_records = sum(county['data_types'][dt]['total_records'] for dt in county['data_types'] if dt != 'NAV')
        print(f"{i:2d}. {county['county']:15s}: {county['total_size_mb']:6.1f} MB, {total_records:7,} records")

    print("\nSmallest 5:")
    for i, county in enumerate(complete_by_size[-5:], len(complete_by_size)-4):
        total_records = sum(county['data_types'][dt]['total_records'] for dt in county['data_types'] if dt != 'NAV')
        print(f"{i:2d}. {county['county']:15s}: {county['total_size_mb']:6.1f} MB, {total_records:7,} records")

    # Data type specific analysis
    print(f"\nDATA TYPE ANALYSIS:")
    print("-" * 40)

    data_types = ['NAL', 'NAP', 'NAV', 'SDF']

    for data_type in data_types:
        counties_with_type = [c for c in inventory['counties'] if c['data_types'][data_type]['available']]
        total_files = sum(len(c['data_types'][data_type]['files']) for c in counties_with_type)
        total_size = sum(c['data_types'][data_type]['total_size_mb'] for c in counties_with_type)

        if data_type == 'NAV':
            print(f"\n{data_type} (Property Values - Fixed-width .txt files):")
            print(f"  Counties: {len(counties_with_type)}/68 ({len(counties_with_type)/68*100:.1f}%)")
            print(f"  Files: {total_files}")
            print(f"  Size: {total_size:.1f} MB")
            print(f"  Note: NAV files are fixed-width .txt format, not CSV")
        else:
            total_records = sum(c['data_types'][data_type]['total_records'] for c in counties_with_type)
            print(f"\n{data_type}:")
            print(f"  Counties: {len(counties_with_type)}/68 ({len(counties_with_type)/68*100:.1f}%)")
            print(f"  Files: {total_files}")
            print(f"  Records: {total_records:,}")
            print(f"  Size: {total_size:.1f} MB")

    # Upload priorities
    print(f"\nUPLOAD PRIORITY RECOMMENDATIONS:")
    print("-" * 40)

    print("\n1. HIGH PRIORITY (Complete data, large counties):")
    high_priority = [c for c in complete_by_size[:10] if c['completeness_score'] == 100]
    for county in high_priority:
        total_records = sum(county['data_types'][dt]['total_records'] for dt in county['data_types'] if dt != 'NAV')
        print(f"   {county['county']:15s}: {total_records:7,} records, {county['total_size_mb']:6.1f} MB")

    print("\n2. MEDIUM PRIORITY (Complete data, medium counties):")
    medium_priority = [c for c in complete_by_size[10:30] if c['completeness_score'] == 100]
    for county in medium_priority[:10]:  # Show first 10
        total_records = sum(county['data_types'][dt]['total_records'] for dt in county['data_types'] if dt != 'NAV')
        print(f"   {county['county']:15s}: {total_records:7,} records, {county['total_size_mb']:6.1f} MB")

    print("\n3. NEEDS ATTENTION (Missing data types):")
    for county in partial_counties:
        missing_types = [dt for dt in county['data_types'] if not county['data_types'][dt]['available']]
        print(f"   {county['county']:15s}: Missing {', '.join(missing_types)}")

    print("\n4. URGENT FIX REQUIRED:")
    for county in empty_counties:
        print(f"   {county['county']:15s}: No data files found")

    # Summary statistics
    print(f"\nFINAL SUMMARY:")
    print("-" * 40)

    total_complete_records = sum(
        sum(c['data_types'][dt]['total_records'] for dt in c['data_types'] if dt != 'NAV')
        for c in complete_counties
    )

    print(f"Ready for upload: {len(complete_counties)} counties")
    print(f"Total records: {total_complete_records:,}")
    print(f"Total size: {sum(c['total_size_mb'] for c in complete_counties):,.1f} MB")
    print(f"Estimated upload time: {total_complete_records / 2000 / 60:.1f} hours (at 2000 records/sec)")

    missing_counties = len(partial_counties) + len(empty_counties)
    print(f"\nRequires attention: {missing_counties} counties")
    print(f"Completion rate: {len(complete_counties)/68*100:.1f}%")

if __name__ == "__main__":
    main()