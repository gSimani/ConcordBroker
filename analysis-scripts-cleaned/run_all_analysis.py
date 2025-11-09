#!/usr/bin/env python3
"""
Master Runner - Execute All Analysis Scripts
Runs all 10 core analysis scripts and consolidates output
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = [
    '01_database_structure.py',
    '02_property_use_codes.py',
    '03_large_buildings.py',
    '04_sales_analysis.py',
    '05_county_inventory.py',
    '06_missing_data_check.py',
    '07_county_deep_dive_template.py',
    '08_contact_extraction.py',
    '09_proforma_analysis.py',
    '10_exemption_fields.py',
]

def run_script(script_name):
    """Run a single analysis script"""
    print(f"\n{'='*80}")
    print(f"Running: {script_name}")
    print('='*80)

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"[+] {script_name} completed successfully")
            return {'script': script_name, 'status': 'success', 'output': result.stdout}
        else:
            print(f"[-] {script_name} failed")
            print(f"Error: {result.stderr}")
            return {'script': script_name, 'status': 'failed', 'error': result.stderr}

    except subprocess.TimeoutExpired:
        print(f"[-] {script_name} timed out")
        return {'script': script_name, 'status': 'timeout'}

    except Exception as e:
        print(f"[-] {script_name} error: {str(e)}")
        return {'script': script_name, 'status': 'error', 'error': str(e)}

def main():
    print("ConcordBroker Analysis Suite")
    print(f"Starting at: {datetime.now().isoformat()}")

    results = {
        'timestamp': datetime.now().isoformat(),
        'scripts_run': [],
        'summary': {}
    }

    for script in SCRIPTS:
        result = run_script(script)
        results['scripts_run'].append(result)

    # Summary
    success_count = sum(1 for r in results['scripts_run'] if r['status'] == 'success')
    failed_count = len(results['scripts_run']) - success_count

    results['summary'] = {
        'total': len(SCRIPTS),
        'successful': success_count,
        'failed': failed_count
    }

    # Save consolidated results
    output_file = f"analysis_suite_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Total scripts: {results['summary']['total']}")
    print(f"Successful: {results['summary']['successful']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
