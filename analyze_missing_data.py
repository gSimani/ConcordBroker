#!/usr/bin/env python3
"""
Comprehensive Missing Data Analysis
Compares Supabase database with local county data inventory
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def analyze_missing_data():
    """Analyze missing data gaps between database and local files"""

    print("="*80)
    print("COMPREHENSIVE MISSING DATA ANALYSIS")
    print("="*80)

    # Read county inventory
    with open('county_data_inventory.json', 'r') as f:
        inventory = json.load(f)

    # Read database audit
    with open('database_audit_results.json', 'r') as f:
        db_audit = json.load(f)

    # Initialize analysis structures
    analysis = {
        'summary': {
            'total_counties_with_data': 0,
            'total_local_records': 0,
            'total_database_records': 0,
            'data_gap_percentage': 0,
            'counties_analysis': {}
        },
        'county_details': {},
        'upload_priorities': [],
        'data_quality_issues': [],
        'recommendations': []
    }

    # Current database status from audit
    db_status = {
        'florida_parcels': 0,  # Will be updated from actual analysis
        'nav_assessments': db_audit.get('Core Property Info', {}).get('tables', {}).get('nav_assessments', {}).get('count', 0),
        'property_assessments': 0,
        'properties': db_audit.get('Core Property Info', {}).get('tables', {}).get('properties', {}).get('count', 0),
        'property_sales_history': db_audit.get('Core Property Info', {}).get('tables', {}).get('property_sales_history', {}).get('count', 0)
    }

    print(f"\nDATABASE CURRENT STATUS:")
    print("-" * 40)
    for table, count in db_status.items():
        print(f"  {table}: {count:,} records")

    # Analyze each county
    counties_data = {}
    total_local_records = 0
    total_size_mb = 0

    for county_info in inventory['counties']:
        county = county_info['county']
        county_analysis = {
            'county': county,
            'data_types': {},
            'total_records': 0,
            'total_size_mb': 0,
            'upload_priority': 0,
            'issues': []
        }

        # Analyze each data type
        for data_type in ['NAL', 'NAP', 'NAV', 'SDF']:
            if data_type in county_info['data_types']:
                dt_info = county_info['data_types'][data_type]

                dt_analysis = {
                    'available': dt_info['available'],
                    'files': len(dt_info.get('files', [])),
                    'records': 0,
                    'size_mb': 0,
                    'quality_score': 0
                }

                if dt_info['available'] and 'files' in dt_info:
                    for file_info in dt_info['files']:
                        dt_analysis['records'] += file_info.get('records', 0)
                        dt_analysis['size_mb'] += file_info.get('size_mb', 0)

                        # Quality assessment
                        if 'quality' in file_info:
                            quality = file_info['quality']
                            if quality.get('has_header', False):
                                dt_analysis['quality_score'] += 25
                            if len(quality.get('columns', [])) > 10:
                                dt_analysis['quality_score'] += 25
                            if file_info.get('records', 0) > 1000:
                                dt_analysis['quality_score'] += 25
                            if file_info.get('size_mb', 0) > 1:
                                dt_analysis['quality_score'] += 25

                county_analysis['data_types'][data_type] = dt_analysis
                county_analysis['total_records'] += dt_analysis['records']
                county_analysis['total_size_mb'] += dt_analysis['size_mb']

        # Calculate upload priority
        priority_score = 0
        if county_analysis['total_records'] > 100000:
            priority_score += 40  # High volume
        elif county_analysis['total_records'] > 50000:
            priority_score += 30
        elif county_analysis['total_records'] > 10000:
            priority_score += 20

        # Data type completeness bonus
        available_types = sum(1 for dt in county_analysis['data_types'].values() if dt['available'])
        priority_score += available_types * 10

        # Major counties get priority boost
        major_counties = ['MIAMI-DADE', 'BROWARD', 'HILLSBOROUGH', 'ORANGE', 'PINELLAS', 'DUVAL', 'PALM BEACH']
        if county in major_counties:
            priority_score += 20

        county_analysis['upload_priority'] = priority_score

        counties_data[county] = county_analysis
        total_local_records += county_analysis['total_records']
        total_size_mb += county_analysis['total_size_mb']

    # Sort counties by priority
    priority_list = sorted(counties_data.items(), key=lambda x: x[1]['upload_priority'], reverse=True)

    # Generate analysis summary
    analysis['summary'] = {
        'total_counties_with_data': len([c for c in counties_data.values() if c['total_records'] > 0]),
        'total_local_records': total_local_records,
        'total_database_records': sum(db_status.values()),
        'data_gap_percentage': 100 - (sum(db_status.values()) / total_local_records * 100) if total_local_records > 0 else 100,
        'total_size_mb': total_size_mb,
        'counties_analysis': len(counties_data)
    }

    # Top priorities for upload
    analysis['upload_priorities'] = []
    for county, data in priority_list[:20]:  # Top 20
        analysis['upload_priorities'].append({
            'county': county,
            'priority_score': data['upload_priority'],
            'records': data['total_records'],
            'size_mb': data['total_size_mb'],
            'data_types_available': len([dt for dt in data['data_types'].values() if dt['available']]),
            'estimated_upload_time_hours': data['total_records'] / 2000  # 2000 records/hour estimate
        })

    # Data quality issues
    for county, data in counties_data.items():
        for dt_name, dt_info in data['data_types'].items():
            if dt_info['available'] and dt_info['quality_score'] < 50:
                analysis['data_quality_issues'].append(f"{county} {dt_name} has quality score {dt_info['quality_score']}/100")

    # Recommendations
    analysis['recommendations'] = [
        "Start with top 10 priority counties for immediate database population",
        "Focus on NAL (names/addresses) data first as it provides core property information",
        "Implement batch uploads with 1000-record chunks for performance",
        "Set up monitoring for upload progress and error handling",
        "Consider parallel processing for multiple counties simultaneously"
    ]

    # Save detailed analysis
    analysis['county_details'] = counties_data
    analysis['generated_at'] = datetime.now().isoformat()

    # Print summary
    print(f"\nANALYSIS SUMMARY:")
    print("-" * 40)
    print(f"Total Counties with Data: {analysis['summary']['total_counties_with_data']}")
    print(f"Total Local Records: {analysis['summary']['total_local_records']:,}")
    print(f"Total Database Records: {analysis['summary']['total_database_records']:,}")
    print(f"Data Gap: {analysis['summary']['data_gap_percentage']:.1f}%")
    print(f"Total Data Size: {analysis['summary']['total_size_mb']:.1f} MB")

    print(f"\nTOP 10 UPLOAD PRIORITIES:")
    print("-" * 40)
    for i, item in enumerate(analysis['upload_priorities'][:10]):
        print(f"{i+1:2d}. {item['county']:15} - Score: {item['priority_score']:3d}, Records: {item['records']:,}, Est. Time: {item['estimated_upload_time_hours']:.1f}h")

    return analysis

if __name__ == "__main__":
    result = analyze_missing_data()

    # Save to file
    with open('comprehensive_missing_data_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("✓ Detailed analysis saved to: comprehensive_missing_data_analysis.json")