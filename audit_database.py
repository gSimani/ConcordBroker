"""
Audit current Supabase database schema and tables
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

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

    # Get all tables by querying information_schema
    tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """

    try:
        # Execute using RPC if available, or try direct query
        result = supabase.rpc('execute_sql', {'query': tables_query}).execute()
        tables = result.data
    except Exception as e:
        print(f"Error querying information_schema: {e}")
        # Fallback: Try known tables
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
            'nav_details'
        ]
        tables = [{'table_name': t} for t in known_tables]

    print(f"\n📊 Found {len(tables)} tables in public schema\n")

    for table_info in tables:
        table_name = table_info['table_name']
        print(f"\n{'=' * 80}")
        print(f"TABLE: {table_name}")
        print(f"{'=' * 80}")

        try:
            # Get row count
            count_result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
            row_count = count_result.count if hasattr(count_result, 'count') else 'N/A'

            print(f"📈 Total Records: {row_count:,}" if isinstance(row_count, int) else f"📈 Total Records: {row_count}")

            # Get sample record to show structure
            sample = supabase.table(table_name).select('*').limit(1).execute()

            if sample.data and len(sample.data) > 0:
                print(f"\n📋 Columns:")
                for col in sample.data[0].keys():
                    sample_value = sample.data[0][col]
                    value_type = type(sample_value).__name__
                    print(f"   • {col} ({value_type})")

                print(f"\n🔍 Sample Record:")
                for key, value in sample.data[0].items():
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + '...'
                    print(f"   {key}: {str_value}")
            else:
                print("   ⚠️  No data in table")

        except Exception as e:
            print(f"   ❌ Error accessing table: {e}")

    print(f"\n{'=' * 80}")
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    audit_database()
