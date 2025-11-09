#!/usr/bin/env python3
"""
Florida County Property Appraiser Data Inventory Analyzer
Scans all county folders and analyzes data completeness
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
import zipfile

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except:
        return 0

def count_csv_records(file_path):
    """Count records in CSV file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            count = sum(1 for row in reader)
            return count
    except Exception as e:
        print(f"Error counting records in {file_path}: {e}")
        return 0

def analyze_csv_quality(file_path):
    """Analyze CSV data quality"""
    try:
        quality_report = {
            'has_header': False,
            'columns': [],
            'sample_rows': 0,
            'empty_rows': 0,
            'issues': []
        }

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)

            # Check header
            try:
                header = next(reader)
                quality_report['has_header'] = True
                quality_report['columns'] = header
            except:
                quality_report['issues'].append('No header found')

            # Sample first 100 rows
            sample_count = 0
            empty_count = 0
            for row in reader:
                sample_count += 1
                if not any(row) or all(cell.strip() == '' for cell in row):
                    empty_count += 1

                if sample_count >= 100:
                    break

            quality_report['sample_rows'] = sample_count
            quality_report['empty_rows'] = empty_count

            if empty_count > sample_count * 0.1:  # More than 10% empty
                quality_report['issues'].append(f'High empty row rate: {empty_count}/{sample_count}')

        return quality_report
    except Exception as e:
        return {'error': str(e)}

def analyze_zip_contents(zip_path):
    """Analyze contents of ZIP file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            total_size = sum(info.file_size for info in zip_ref.infolist())
            return {
                'files': file_list,
                'file_count': len(file_list),
                'total_uncompressed_size_mb': round(total_size / (1024 * 1024), 2)
            }
    except Exception as e:
        return {'error': str(e)}

def analyze_county_folder(county_path):
    """Analyze a single county folder"""
    county_name = os.path.basename(county_path)

    analysis = {
        'county': county_name,
        'path': county_path,
        'data_types': {},
        'total_files': 0,
        'total_size_mb': 0,
        'completeness_score': 0,
        'issues': [],
        'last_modified': None
    }

    if not os.path.exists(county_path):
        analysis['issues'].append('County folder not found')
        return analysis

    # Get all files in county folder
    try:
        all_files = []
        for root, dirs, files in os.walk(county_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)

        analysis['total_files'] = len(all_files)

        # Analyze each data type
        data_types = ['NAL', 'NAP', 'NAV', 'SDF']

        for data_type in data_types:
            type_files = [f for f in all_files if data_type in os.path.basename(f).upper()]

            if type_files:
                analysis['data_types'][data_type] = {
                    'available': True,
                    'files': [],
                    'total_records': 0,
                    'total_size_mb': 0
                }

                for file_path in type_files:
                    file_info = {
                        'filename': os.path.basename(file_path),
                        'path': file_path,
                        'size_mb': get_file_size_mb(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }

                    # Analyze based on file type
                    if file_path.endswith('.csv'):
                        file_info['records'] = count_csv_records(file_path)
                        file_info['quality'] = analyze_csv_quality(file_path)
                        analysis['data_types'][data_type]['total_records'] += file_info['records']
                    elif file_path.endswith('.zip'):
                        file_info['zip_contents'] = analyze_zip_contents(file_path)

                    analysis['data_types'][data_type]['files'].append(file_info)
                    analysis['data_types'][data_type]['total_size_mb'] += file_info['size_mb']
                    analysis['total_size_mb'] += file_info['size_mb']

            else:
                analysis['data_types'][data_type] = {
                    'available': False,
                    'files': [],
                    'total_records': 0,
                    'total_size_mb': 0
                }

        # Calculate completeness score (0-100)
        available_types = sum(1 for dt in data_types if analysis['data_types'][dt]['available'])
        analysis['completeness_score'] = (available_types / len(data_types)) * 100

        # Get latest modification time
        if all_files:
            latest_mod = max(os.path.getmtime(f) for f in all_files)
            analysis['last_modified'] = datetime.fromtimestamp(latest_mod).isoformat()

    except Exception as e:
        analysis['issues'].append(f'Error analyzing folder: {str(e)}')

    return analysis

def main():
    """Main analysis function"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

    print("Starting Florida County Property Data Inventory Analysis...")
    print(f"Base path: {base_path}")

    # Get all county directories
    county_dirs = []
    try:
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # Skip special directories
                if item not in ['NAL_2025', 'NAL_2025P']:
                    county_dirs.append(item_path)
    except Exception as e:
        print(f"Error reading base directory: {e}")
        return

    print(f"Found {len(county_dirs)} county directories to analyze")

    # Initialize inventory
    inventory = {
        'generated_at': datetime.now().isoformat(),
        'base_path': base_path,
        'total_counties': len(county_dirs),
        'counties': [],
        'summary': {
            'total_counties': len(county_dirs),
            'complete_counties': 0,
            'partial_counties': 0,
            'empty_counties': 0,
            'data_type_coverage': {},
            'total_files': 0,
            'total_size_mb': 0,
            'total_records': 0
        }
    }

    # Analyze each county
    for i, county_path in enumerate(sorted(county_dirs), 1):
        county_name = os.path.basename(county_path)
        print(f"[{i:2d}/{len(county_dirs)}] Analyzing {county_name}...")

        analysis = analyze_county_folder(county_path)
        inventory['counties'].append(analysis)

        # Update summary statistics
        inventory['summary']['total_files'] += analysis['total_files']
        inventory['summary']['total_size_mb'] += analysis['total_size_mb']

        for data_type, info in analysis['data_types'].items():
            inventory['summary']['total_records'] += info['total_records']

            if data_type not in inventory['summary']['data_type_coverage']:
                inventory['summary']['data_type_coverage'][data_type] = 0
            if info['available']:
                inventory['summary']['data_type_coverage'][data_type] += 1

        # Categorize completeness
        if analysis['completeness_score'] == 100:
            inventory['summary']['complete_counties'] += 1
        elif analysis['completeness_score'] > 0:
            inventory['summary']['partial_counties'] += 1
        else:
            inventory['summary']['empty_counties'] += 1

    # Calculate coverage percentages
    total_counties = len(county_dirs)
    for data_type in inventory['summary']['data_type_coverage']:
        count = inventory['summary']['data_type_coverage'][data_type]
        percentage = (count / total_counties) * 100 if total_counties > 0 else 0
        inventory['summary']['data_type_coverage'][data_type] = {
            'counties_with_data': count,
            'percentage': round(percentage, 1)
        }

    # Save inventory
    output_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\county_data_inventory.json"

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        print(f"Inventory saved to: {output_path}")
    except Exception as e:
        print(f"Error saving inventory: {e}")
        return

    # Print summary
    print("\n" + "="*60)
    print("FLORIDA COUNTY DATA INVENTORY SUMMARY")
    print("="*60)
    print(f"Total Counties: {inventory['summary']['total_counties']}")
    print(f"Complete (100%): {inventory['summary']['complete_counties']}")
    print(f"Partial Data: {inventory['summary']['partial_counties']}")
    print(f"No Data: {inventory['summary']['empty_counties']}")
    print(f"Total Files: {inventory['summary']['total_files']:,}")
    print(f"Total Size: {inventory['summary']['total_size_mb']:,.1f} MB")
    print(f"Total Records: {inventory['summary']['total_records']:,}")

    print("\nDATA TYPE COVERAGE:")
    for data_type, coverage in inventory['summary']['data_type_coverage'].items():
        print(f"   {data_type}: {coverage['counties_with_data']}/{total_counties} counties ({coverage['percentage']}%)")

    print("\nCOUNTIES WITH ISSUES:")
    for county in inventory['counties']:
        if county['issues']:
            print(f"   {county['county']}: {', '.join(county['issues'])}")

    print("\nFull inventory report saved to county_data_inventory.json")

if __name__ == "__main__":
    main()