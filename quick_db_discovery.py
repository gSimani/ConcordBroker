#!/usr/bin/env python3
"""
Quick Database Discovery Script
==============================
Fast discovery of all tables and basic structure without heavy analysis
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

def get_db_url():
    """Get cleaned database URL"""
    url = os.getenv('DATABASE_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
        if '&supa=' in url:
            url = url.split('&supa=')[0]
        if '&pgbouncer=' in url:
            url = url.split('&pgbouncer=')[0]
        return url
    raise ValueError("No DATABASE_URL found")

def discover_tables():
    """Quick table discovery"""
    db_url = get_db_url()
    engine = create_engine(db_url, pool_size=5, max_overflow=10)

    with engine.connect() as conn:
        inspector = inspect(engine)

        # Get all tables
        table_names = inspector.get_table_names()
        view_names = inspector.get_view_names()

        print(f"Found {len(table_names)} tables and {len(view_names)} views")

        tables_info = {}

        for table_name in table_names:
            print(f"Analyzing table: {table_name}")

            # Get basic info
            columns = inspector.get_columns(table_name)
            pk_constraint = inspector.get_pk_constraint(table_name)

            # Quick row count
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            except Exception as e:
                print(f"  Warning: Could not count rows in {table_name}: {e}")
                row_count = 0

            tables_info[table_name] = {
                'type': 'table',
                'row_count': row_count,
                'column_count': len(columns),
                'columns': [{'name': col['name'], 'type': str(col['type'])} for col in columns],
                'primary_keys': pk_constraint.get('constrained_columns', [])
            }

            print(f"  {row_count:,} rows, {len(columns)} columns")

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"database_discovery_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'discovery_timestamp': datetime.now().isoformat(),
                'database_summary': {
                    'total_tables': len(table_names),
                    'total_views': len(view_names),
                    'table_names': table_names,
                    'view_names': view_names
                },
                'tables': tables_info
            }, f, indent=2, default=str)

        print(f"\nResults saved to {output_file}")

        # Print summary
        print("\n" + "="*50)
        print("DATABASE DISCOVERY SUMMARY")
        print("="*50)

        total_rows = sum(info['row_count'] for info in tables_info.values())
        print(f"Total Tables: {len(table_names)}")
        print(f"Total Views: {len(view_names)}")
        print(f"Total Rows: {total_rows:,}")

        # Show largest tables
        sorted_tables = sorted(tables_info.items(), key=lambda x: x[1]['row_count'], reverse=True)
        print(f"\nLargest Tables:")
        for i, (name, info) in enumerate(sorted_tables[:10], 1):
            print(f"{i:2d}. {name:<30} {info['row_count']:>10,} rows")

        # Look for sales tables
        sales_tables = [name for name in table_names if any(keyword in name.lower() for keyword in ['sale', 'sdf', 'transaction'])]
        print(f"\nSales-related tables found:")
        for table in sales_tables:
            rows = tables_info[table]['row_count']
            print(f"  - {table}: {rows:,} rows")

        # Look for property tables
        property_tables = [name for name in table_names if any(keyword in name.lower() for keyword in ['property', 'parcel', 'florida'])]
        print(f"\nProperty-related tables found:")
        for table in property_tables:
            rows = tables_info[table]['row_count']
            print(f"  - {table}: {rows:,} rows")

        return tables_info

if __name__ == "__main__":
    discover_tables()