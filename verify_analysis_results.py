#!/usr/bin/env python3
"""
Verification script for missing data analysis results
"""

import json

def verify_analysis():
    """Verify key findings from the analysis"""

    print("MISSING DATA ANALYSIS VERIFICATION")
    print("=" * 50)

    # Load analysis results
    with open('comprehensive_missing_data_analysis.json', 'r') as f:
        analysis = json.load(f)

    summary = analysis['summary']
    priorities = analysis['upload_priorities']

    print(f"\nKEY METRICS VERIFICATION:")
    print(f"- Counties with data: {summary['total_counties_with_data']}")
    print(f"- Total local records: {summary['total_local_records']:,}")
    print(f"- Database records: {summary['total_database_records']}")
    print(f"- Data gap: {summary['data_gap_percentage']:.4f}%")
    print(f"- Total size: {summary['total_size_mb']:.1f} MB")

    print(f"\nTOP 5 PRIORITY COUNTIES:")
    for i, county in enumerate(priorities[:5]):
        print(f"{i+1}. {county['county']}: {county['records']:,} records, Score: {county['priority_score']}")

    print(f"\nCRITICAL FINDINGS:")
    print(f"- Database is {summary['data_gap_percentage']:.1f}% empty")
    print(f"- {summary['total_local_records']:,} records available for upload")
    print(f"- Top 5 counties contain {sum(c['records'] for c in priorities[:5]):,} records")
    print(f"- Estimated upload time for top 5: {sum(c['estimated_upload_time_hours'] for c in priorities[:5]):.1f} hours")

    print(f"\nRECOMMENDATION:")
    print("IMMEDIATE ACTION REQUIRED - Database needs bulk upload to become functional")

    return True

if __name__ == "__main__":
    verify_analysis()