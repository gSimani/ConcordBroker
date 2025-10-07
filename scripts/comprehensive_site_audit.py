"""
ConcordBroker Comprehensive Site Audit
Purpose: Map all database endpoints, UI components, and data flows
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
env_path = Path(__file__).parent.parent / '.env.mcp'
load_dotenv(env_path, override=True)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def audit_database_tables():
    """Get all tables and their row counts"""
    print("=" * 80)
    print("DATABASE TABLES AUDIT")
    print("=" * 80)

    tables_query = """
        SELECT
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC;
    """

    # Get table list via information_schema
    result = supabase.table('pg_stat_user_tables').select('*').execute()

    tables = {}
    # Get actual tables from information_schema
    info_result = supabase.rpc('execute_sql', {
        'query': "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    }).execute() if False else None

    # Manual table list based on known schema
    known_tables = [
        'florida_parcels',
        'property_sales_history',
        'sunbiz_corporate',
        'florida_entities',
        'tax_certificates',
        'owner_identities',
        'property_ownership',
        'entity_principals',
        'concordbroker_docs',
        'agent_lion_conversations',
        'agent_lion_analyses'
    ]

    for table in known_tables:
        try:
            count_result = supabase.table(table).select('*', count='exact').limit(1).execute()
            row_count = count_result.count if hasattr(count_result, 'count') else 'Unknown'

            # Get sample columns
            sample = supabase.table(table).select('*').limit(1).execute()
            columns = list(sample.data[0].keys()) if sample.data else []

            tables[table] = {
                'row_count': row_count,
                'columns': columns,
                'sample_data': sample.data[0] if sample.data else None
            }

            print(f"\n✓ {table}")
            print(f"  Rows: {row_count:,}" if isinstance(row_count, int) else f"  Rows: {row_count}")
            print(f"  Columns: {len(columns)}")
            print(f"  Key fields: {', '.join(columns[:5])}...")

        except Exception as e:
            print(f"\n✗ {table}")
            print(f"  Error: {str(e)}")
            tables[table] = {'error': str(e)}

    return tables

def audit_api_endpoints():
    """Scan for all API endpoints in the codebase"""
    print("\n" + "=" * 80)
    print("API ENDPOINTS AUDIT")
    print("=" * 80)

    api_files = [
        'apps/api/property_live_api.py',
        'apps/api/routers/properties.py',
        'apps/api/production_property_api.py',
        'apps/api/search_api.py'
    ]

    endpoints = {}

    for api_file in api_files:
        file_path = Path(__file__).parent.parent / api_file
        if file_path.exists():
            print(f"\n📄 {api_file}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Find FastAPI routes
                import re
                routes = re.findall(r'@(?:app|router)\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)

                for method, route in routes:
                    endpoint_key = f"{method.upper()} {route}"
                    endpoints[endpoint_key] = {
                        'file': api_file,
                        'method': method.upper(),
                        'route': route
                    }
                    print(f"  {method.upper():6} {route}")
        else:
            print(f"\n✗ {api_file} - File not found")

    return endpoints

def audit_ui_components():
    """Scan all React components for data requirements"""
    print("\n" + "=" * 80)
    print("UI COMPONENTS AUDIT")
    print("=" * 80)

    ui_dirs = [
        'apps/web/src/components/property',
        'apps/web/src/pages/property',
        'apps/web/src/pages/properties'
    ]

    components = {}

    for ui_dir in ui_dirs:
        dir_path = Path(__file__).parent.parent / ui_dir
        if dir_path.exists():
            print(f"\n📁 {ui_dir}")

            for file_path in dir_path.rglob('*.tsx'):
                rel_path = file_path.relative_to(Path(__file__).parent.parent)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Find data fetching patterns
                    import re

                    # Find fetch calls
                    fetches = re.findall(r'fetch\(["\']([^"\']+)["\']', content)

                    # Find useQuery hooks
                    queries = re.findall(r'useQuery\(\s*["\']([^"\']+)["\']', content)

                    # Find state variables
                    states = re.findall(r'const\s+\[(\w+),\s*set\w+\]\s*=\s*useState', content)

                    if fetches or queries or states:
                        components[str(rel_path)] = {
                            'fetches': fetches,
                            'queries': queries,
                            'states': states[:10]  # Limit to first 10
                        }

                        print(f"\n  📄 {file_path.name}")
                        if fetches:
                            print(f"    Fetch: {', '.join(fetches[:3])}")
                        if queries:
                            print(f"    Query: {', '.join(queries[:3])}")
                        if states:
                            print(f"    State: {', '.join(states[:5])}")

    return components

def audit_filters():
    """Check all filter implementations"""
    print("\n" + "=" * 80)
    print("FILTERS AUDIT")
    print("=" * 80)

    filter_file = Path(__file__).parent.parent / 'apps/web/src/pages/properties/PropertySearch.tsx'

    if filter_file.exists():
        with open(filter_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find filter inputs
            import re
            inputs = re.findall(r'<Input[^>]*placeholder="([^"]+)"', content)
            selects = re.findall(r'<Select[^>]*placeholder="([^"]+)"', content)

            print("\n✓ PropertySearch.tsx")
            print(f"  Input filters: {len(inputs)}")
            for inp in inputs[:10]:
                print(f"    - {inp}")

            print(f"\n  Select filters: {len(selects)}")
            for sel in selects[:10]:
                print(f"    - {sel}")

            return {
                'inputs': inputs,
                'selects': selects,
                'total_filters': len(inputs) + len(selects)
            }

    return {}

def generate_report(tables, endpoints, components, filters):
    """Generate comprehensive audit report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path(__file__).parent.parent / f'comprehensive_audit_report_{timestamp}.json'

    report = {
        'timestamp': timestamp,
        'database_tables': tables,
        'api_endpoints': endpoints,
        'ui_components': components,
        'filters': filters,
        'summary': {
            'total_tables': len(tables),
            'total_endpoints': len(endpoints),
            'total_components': len(components),
            'total_filters': filters.get('total_filters', 0)
        }
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"\nTotal Tables: {report['summary']['total_tables']}")
    print(f"Total API Endpoints: {report['summary']['total_endpoints']}")
    print(f"Total UI Components: {report['summary']['total_components']}")
    print(f"Total Filters: {report['summary']['total_filters']}")
    print(f"\nReport saved: {report_file}")

    return report

def main():
    print("🔍 ConcordBroker Comprehensive Site Audit")
    print("=" * 80)

    # Run audits
    tables = audit_database_tables()
    endpoints = audit_api_endpoints()
    components = audit_ui_components()
    filters = audit_filters()

    # Generate report
    report = generate_report(tables, endpoints, components, filters)

    print("\n✅ Audit complete!")

if __name__ == "__main__":
    main()
