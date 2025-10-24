"""
Audit current Supabase database schema and tables
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv('.env.mcp')

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)

def audit_database():
    """Audit database structure and data"""

    print("=" * 80)
    print("SUPABASE DATABASE AUDIT")
    print("=" * 80)

    # Known tables from CLAUDE.md
    known_tables = [
        'florida_parcels',
        'property_sales_history',
        'florida_entities',
        'sunbiz_corporate',
        'tax_certificates',
        'property_assessments',
        'property_owners',
        'property_sales',
        'nav_summaries',
        'nav_details',
        'tax_deed_sales',
        'foreclosures',
        'permits'
    ]

    print(f"\nChecking {len(known_tables)} known tables...\n")

    table_audit = []

    for table_name in known_tables:
        print(f"Checking table: {table_name}...")

        try:
            # Get row count
            count_result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
            row_count = count_result.count

            # Get sample record to show structure
            sample = supabase.table(table_name).select('*').limit(1).execute()

            columns = []
            sample_data = None
            if sample.data and len(sample.data) > 0:
                columns = list(sample.data[0].keys())
                sample_data = sample.data[0]

            table_audit.append({
                'table': table_name,
                'records': row_count,
                'columns': columns,
                'sample': sample_data,
                'status': 'EXISTS'
            })

            print(f"  -> {row_count:,} records, {len(columns)} columns")

        except Exception as e:
            table_audit.append({
                'table': table_name,
                'records': 0,
                'columns': [],
                'sample': None,
                'status': 'NOT FOUND' if 'relation' in str(e) or 'does not exist' in str(e) else 'ERROR',
                'error': str(e)
            })
            print(f"  -> {table_audit[-1]['status']}: {e}")

    # Print detailed report
    print("\n" + "=" * 80)
    print("DETAILED TABLE REPORT")
    print("=" * 80)

    for audit in table_audit:
        print(f"\nTABLE: {audit['table']}")
        print("-" * 80)
        print(f"Status: {audit['status']}")
        print(f"Records: {audit['records']:,}")

        if audit['columns']:
            print(f"\nColumns ({len(audit['columns'])}):")
            for col in audit['columns']:
                print(f"  - {col}")

            if audit['sample']:
                print(f"\nSample Data:")
                for key, value in audit['sample'].items():
                    str_value = str(value)
                    if len(str_value) > 60:
                        str_value = str_value[:57] + '...'
                    print(f"  {key}: {str_value}")

        if audit['status'] == 'ERROR' and 'error' in audit:
            print(f"\nError: {audit['error']}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    exists = [a for a in table_audit if a['status'] == 'EXISTS']
    missing = [a for a in table_audit if a['status'] == 'NOT FOUND']
    errors = [a for a in table_audit if a['status'] == 'ERROR']

    print(f"\nTables Found: {len(exists)}")
    print(f"Tables Missing: {len(missing)}")
    print(f"Tables with Errors: {len(errors)}")

    total_records = sum(a['records'] for a in exists)
    print(f"\nTotal Records: {total_records:,}")

    if exists:
        print(f"\nLargest Tables:")
        sorted_tables = sorted(exists, key=lambda x: x['records'], reverse=True)[:5]
        for t in sorted_tables:
            print(f"  - {t['table']}: {t['records']:,} records")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    audit_database()
