import os
import json
from supabase import create_client, Client
from datetime import datetime
import sys

def connect_to_supabase():
    """Connect to Supabase using environment variables"""
    try:
        # Try to read from .env.mcp first
        env_file = ".env.mcp"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value.strip('"\'')

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            print("[ERROR] Missing Supabase credentials")
            print(f"SUPABASE_URL: {'OK' if supabase_url else 'MISSING'}")
            print(f"SUPABASE_KEY: {'OK' if supabase_key else 'MISSING'}")
            return None

        print(f"[INFO] Connecting to: {supabase_url}")
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase

    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return None

def get_all_tables(supabase):
    """Get list of all tables in the database by trying common table names"""
    # Common table names to check
    common_tables = [
        'florida_parcels', 'florida_sales', 'sales_history',
        'property_sales', 'sdf_sales', 'parcel_sales',
        'tax_deeds', 'properties', 'sales_data', 'sdf_data',
        'property_records', 'real_estate_sales', 'transactions',
        'property_transactions', 'deed_records', 'parcel_data'
    ]

    existing_tables = []
    for table in common_tables:
        try:
            print(f"  Checking table: {table}")
            response = supabase.table(table).select("*").limit(1).execute()
            existing_tables.append(table)
            print(f"  [FOUND] {table}")
        except Exception as e:
            print(f"  [NOT FOUND] {table}: {str(e)[:50]}...")

    return existing_tables

def get_table_schema(supabase, table_name):
    """Get column information for a table by analyzing sample data"""
    try:
        # Get sample data to infer schema
        sample = supabase.table(table_name).select("*").limit(5).execute()
        if sample.data and len(sample.data) > 0:
            columns = []
            for col in sample.data[0].keys():
                # Infer data type from sample values
                sample_value = sample.data[0][col]
                if sample_value is None:
                    # Try to find non-null value
                    for row in sample.data:
                        if row[col] is not None:
                            sample_value = row[col]
                            break

                if sample_value is None:
                    data_type = "unknown"
                elif isinstance(sample_value, str):
                    data_type = "text"
                elif isinstance(sample_value, int):
                    data_type = "integer"
                elif isinstance(sample_value, float):
                    data_type = "numeric"
                elif isinstance(sample_value, bool):
                    data_type = "boolean"
                else:
                    data_type = type(sample_value).__name__

                columns.append({
                    'column_name': col,
                    'data_type': data_type,
                    'is_nullable': 'YES'
                })
            return columns
        return []

    except Exception as e:
        print(f"[ERROR] Error getting schema for {table_name}: {e}")
        return []

def find_sales_tables(tables):
    """Identify tables that likely contain sales data"""
    sales_keywords = ['sales', 'sdf', 'transaction', 'deed', 'transfer']
    sales_tables = []

    for table in tables:
        table_lower = table.lower()
        if any(keyword in table_lower for keyword in sales_keywords):
            sales_tables.append(table)

    # Always check florida_parcels as it might have sales columns
    if 'florida_parcels' in tables and 'florida_parcels' not in sales_tables:
        sales_tables.append('florida_parcels')

    return sales_tables

def analyze_sales_columns(columns):
    """Identify columns that likely contain sales information"""
    sales_column_keywords = [
        'sale', 'price', 'amount', 'value', 'date', 'transaction',
        'book', 'page', 'cin', 'deed', 'transfer', 'sold'
    ]

    sales_columns = []
    for col in columns:
        col_name = col['column_name'].lower()
        if any(keyword in col_name for keyword in sales_column_keywords):
            sales_columns.append(col)

    return sales_columns

def test_sales_data(supabase, table_name, test_parcels):
    """Test fetching sales data for specific parcels"""
    try:
        print(f"\n[TEST] Testing sales data in {table_name}:")

        # First, get a sample of any data
        sample = supabase.table(table_name).select("*").limit(5).execute()
        if sample.data:
            print(f"  [OK] Found {len(sample.data)} sample records")

            # Check if parcel_id column exists
            if 'parcel_id' in sample.data[0]:
                for parcel_id in test_parcels:
                    parcel_data = supabase.table(table_name).select("*").eq('parcel_id', parcel_id).limit(5).execute()
                    if parcel_data.data:
                        print(f"  [OK] Found {len(parcel_data.data)} records for parcel {parcel_id}")
                        # Show first record
                        record = parcel_data.data[0]
                        sales_info = {}
                        for key, value in record.items():
                            if any(kw in key.lower() for kw in ['sale', 'price', 'amount', 'date']):
                                sales_info[key] = value
                        if sales_info:
                            print(f"    Sales data: {json.dumps(sales_info, default=str, indent=2)}")
                    else:
                        print(f"  [NONE] No records found for parcel {parcel_id}")
            else:
                print("  [WARN] No parcel_id column found - showing sample record structure:")
                print(f"    {json.dumps(sample.data[0], default=str, indent=2)}")
        else:
            print(f"  [EMPTY] No data found in {table_name}")

    except Exception as e:
        print(f"  [ERROR] Error testing {table_name}: {e}")

def main():
    print("Supabase Sales Data Analysis")
    print("=" * 50)

    # Test parcels
    test_parcels = [
        '1078130000370',
        '5032100100120',
        '5032100200010',
        '3218460080100'
    ]

    # Connect to Supabase
    supabase = connect_to_supabase()
    if not supabase:
        return

    print("[SUCCESS] Connected to Supabase successfully!")

    # Get all tables
    print("\n[INFO] Getting all tables...")
    all_tables = get_all_tables(supabase)
    print(f"Found {len(all_tables)} tables:")
    for table in all_tables:
        print(f"  - {table}")

    # Find sales-related tables
    print("\n[INFO] Identifying sales-related tables...")
    sales_tables = find_sales_tables(all_tables)
    print(f"Sales-related tables found: {sales_tables}")

    # Analyze each sales table
    results = {}
    for table in sales_tables:
        print(f"\n[INFO] Analyzing table: {table}")
        print("-" * 30)

        # Get schema
        columns = get_table_schema(supabase, table)
        if columns:
            print(f"Columns ({len(columns)}):")
            sales_columns = analyze_sales_columns(columns)

            for col in columns:
                marker = "[SALES]" if col in sales_columns else "       "
                print(f"{marker} {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")

            if sales_columns:
                print(f"\n[SALES] Sales-related columns found:")
                for col in sales_columns:
                    print(f"  - {col['column_name']} ({col['data_type']})")

            results[table] = {
                'total_columns': len(columns),
                'sales_columns': [col['column_name'] for col in sales_columns],
                'all_columns': [col['column_name'] for col in columns]
            }

            # Test with sample data
            test_sales_data(supabase, table, test_parcels)
        else:
            print("[ERROR] Could not retrieve schema")
            results[table] = {'error': 'Could not retrieve schema'}

    # Summary
    print("\n[SUMMARY] ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Total tables analyzed: {len(sales_tables)}")

    for table, data in results.items():
        if 'error' not in data:
            print(f"\n{table}:")
            print(f"  - Total columns: {data['total_columns']}")
            print(f"  - Sales columns: {len(data['sales_columns'])}")
            if data['sales_columns']:
                print(f"  - Sales fields: {', '.join(data['sales_columns'])}")

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sales_analysis_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'all_tables': all_tables,
            'sales_tables': sales_tables,
            'analysis_results': results,
            'test_parcels': test_parcels
        }, f, indent=2, default=str)

    print(f"\n[INFO] Results saved to: {filename}")

if __name__ == "__main__":
    main()