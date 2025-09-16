#!/usr/bin/env python3
"""
Generate final comprehensive report with database comparison
"""

import json
import os

def create_final_report():
    """Create final comprehensive report"""

    # Load inventory
    with open('county_data_inventory.json', 'r') as f:
        inventory = json.load(f)

    # Create comprehensive report
    report = {
        "report_generated": inventory['generated_at'],
        "summary": {
            "total_counties_in_florida": 67,  # Actual Florida counties
            "counties_with_data": len([c for c in inventory['counties'] if c['completeness_score'] > 0]),
            "complete_counties": len([c for c in inventory['counties'] if c['completeness_score'] == 100]),
            "partial_counties": len([c for c in inventory['counties'] if 0 < c['completeness_score'] < 100]),
            "empty_counties": len([c for c in inventory['counties'] if c['completeness_score'] == 0]),
            "total_files": inventory['summary']['total_files'],
            "total_size_gb": round(inventory['summary']['total_size_mb'] / 1024, 2),
            "estimated_total_records": inventory['summary']['total_records']
        },
        "data_types": {
            "NAL": {
                "description": "Names and Addresses - Main property records",
                "format": "CSV",
                "counties_available": len([c for c in inventory['counties'] if c['data_types']['NAL']['available']]),
                "total_records": sum(c['data_types']['NAL']['total_records'] for c in inventory['counties']),
                "total_size_mb": sum(c['data_types']['NAL']['total_size_mb'] for c in inventory['counties'])
            },
            "NAP": {
                "description": "Property Characteristics - Building details, land use",
                "format": "CSV",
                "counties_available": len([c for c in inventory['counties'] if c['data_types']['NAP']['available']]),
                "total_records": sum(c['data_types']['NAP']['total_records'] for c in inventory['counties']),
                "total_size_mb": sum(c['data_types']['NAP']['total_size_mb'] for c in inventory['counties'])
            },
            "NAV": {
                "description": "Property Values and Assessments",
                "format": "Fixed-width TXT",
                "counties_available": len([c for c in inventory['counties'] if c['data_types']['NAV']['available']]),
                "total_records": "Unknown (fixed-width format)",
                "total_size_mb": sum(c['data_types']['NAV']['total_size_mb'] for c in inventory['counties'])
            },
            "SDF": {
                "description": "Sales Data - Property transactions",
                "format": "CSV",
                "counties_available": len([c for c in inventory['counties'] if c['data_types']['SDF']['available']]),
                "total_records": sum(c['data_types']['SDF']['total_records'] for c in inventory['counties']),
                "total_size_mb": sum(c['data_types']['SDF']['total_size_mb'] for c in inventory['counties'])
            }
        },
        "priority_upload_counties": [],
        "problem_counties": [],
        "upload_estimates": {}
    }

    # Complete counties sorted by size
    complete_counties = [c for c in inventory['counties'] if c['completeness_score'] == 100]
    complete_counties.sort(key=lambda x: x['total_size_mb'], reverse=True)

    for county in complete_counties:
        total_records = sum(county['data_types'][dt]['total_records'] for dt in county['data_types'] if dt != 'NAV')
        report['priority_upload_counties'].append({
            "county": county['county'],
            "records": total_records,
            "size_mb": county['total_size_mb'],
            "completeness": county['completeness_score'],
            "priority": "HIGH" if county['total_size_mb'] > 200 else "MEDIUM" if county['total_size_mb'] > 50 else "LOW"
        })

    # Problem counties
    problem_counties = [c for c in inventory['counties'] if c['completeness_score'] < 100]

    for county in problem_counties:
        missing_types = [dt for dt in county['data_types'] if not county['data_types'][dt]['available']]
        available_types = [dt for dt in county['data_types'] if county['data_types'][dt]['available']]

        report['problem_counties'].append({
            "county": county['county'],
            "completeness": county['completeness_score'],
            "available_data_types": available_types,
            "missing_data_types": missing_types,
            "size_mb": county['total_size_mb'],
            "action_required": "Download missing data" if missing_types else "Investigate directory"
        })

    # Upload estimates
    total_records_ready = sum(c['records'] for c in report['priority_upload_counties'])

    report['upload_estimates'] = {
        "total_records_ready": total_records_ready,
        "estimated_time_hours_2k_per_sec": round(total_records_ready / 2000 / 3600, 1),
        "estimated_time_hours_4k_per_sec": round(total_records_ready / 4000 / 3600, 1),
        "counties_ready": len(report['priority_upload_counties']),
        "counties_needing_attention": len(report['problem_counties'])
    }

    return report

def main():
    """Generate and save final report"""

    print("Generating final comprehensive county data report...")

    report = create_final_report()

    # Save report
    with open('county_data_final_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("\nFINAL FLORIDA COUNTY DATA REPORT")
    print("=" * 50)

    print(f"\nOVERALL STATUS:")
    print(f"Counties with data: {report['summary']['counties_with_data']}/67")
    print(f"Complete datasets: {report['summary']['complete_counties']}")
    print(f"Partial datasets: {report['summary']['partial_counties']}")
    print(f"Empty counties: {report['summary']['empty_counties']}")
    print(f"Total data size: {report['summary']['total_size_gb']} GB")
    print(f"Estimated records: {report['summary']['estimated_total_records']:,}")

    print(f"\nDATA TYPE COVERAGE:")
    for data_type, info in report['data_types'].items():
        print(f"{data_type}: {info['counties_available']}/67 counties ({info['counties_available']/67*100:.1f}%)")

    print(f"\nUPLOAD READINESS:")
    print(f"Ready for upload: {report['upload_estimates']['counties_ready']} counties")
    print(f"Records ready: {report['upload_estimates']['total_records_ready']:,}")
    print(f"Upload time estimate: {report['upload_estimates']['estimated_time_hours_2k_per_sec']}-{report['upload_estimates']['estimated_time_hours_4k_per_sec']} hours")

    print(f"\nTOP 10 PRIORITY COUNTIES:")
    for i, county in enumerate(report['priority_upload_counties'][:10], 1):
        print(f"{i:2d}. {county['county']:15s}: {county['records']:7,} records ({county['priority']})")

    print(f"\nPROBLEM COUNTIES ({len(report['problem_counties'])}):")
    for county in report['problem_counties']:
        if county['completeness'] == 0:
            print(f"EMPTY {county['county']:15s}: No data")
        else:
            print(f"PARTIAL {county['county']:15s}: Missing {', '.join(county['missing_data_types'])}")

    print(f"\nNext Steps:")
    print(f"1. Start uploading {report['summary']['complete_counties']} complete counties")
    print(f"2. Download missing data for {report['summary']['partial_counties']} partial counties")
    print(f"3. Investigate {report['summary']['empty_counties']} empty counties")
    print(f"4. Total completion rate: {report['summary']['complete_counties']/67*100:.1f}%")

    print(f"\nReport saved to: county_data_final_report.json")

if __name__ == "__main__":
    main()