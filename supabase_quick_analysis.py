#!/usr/bin/env python3
"""
Quick Supabase Database Analysis
Simplified version focusing on essential metrics
"""

import os
import json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, inspect, text
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def analyze_supabase():
    """Perform quick database analysis"""

    print("="*80)
    print("SUPABASE DATABASE QUICK ANALYSIS")
    print("="*80)

    # Connect to database
    db_url = "postgresql://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613%21@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

    try:
        engine = create_engine(db_url, pool_pre_ping=True, pool_size=1)
        inspector = inspect(engine)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"\n✓ Connected to: {version[:50]}...")

        # 1. Get schemas
        schemas = [s for s in inspector.get_schema_names() if s not in ['pg_catalog', 'information_schema', 'pg_toast']]
        print(f"\n📊 Active Schemas: {', '.join(schemas)}")

        # 2. Analyze tables
        print("\n📋 TABLE ANALYSIS:")
        print("-" * 40)

        all_tables = []
        for schema in schemas[:3]:  # Limit to first 3 schemas
            tables = inspector.get_table_names(schema=schema)
            for table in tables[:10]:  # Limit to first 10 tables per schema
                try:
                    # Get row count
                    query = f"SELECT COUNT(*) FROM {schema}.{table}"
                    df = pd.read_sql(query, engine)
                    row_count = df.iloc[0, 0]

                    # Get columns
                    columns = inspector.get_columns(table, schema=schema)

                    all_tables.append({
                        'schema': schema,
                        'table': table,
                        'rows': row_count,
                        'columns': len(columns)
                    })

                    if row_count > 0:
                        print(f"  • {schema}.{table}: {row_count:,} rows, {len(columns)} columns")
                except Exception as e:
                    continue

        # 3. Find largest tables
        if all_tables:
            df_tables = pd.DataFrame(all_tables)
            df_tables = df_tables.sort_values('rows', ascending=False)

            print("\n🔝 TOP 5 LARGEST TABLES:")
            print("-" * 40)
            for _, row in df_tables.head(5).iterrows():
                print(f"  {row['schema']}.{row['table']}: {row['rows']:,} rows")

        # 4. Analyze florida_parcels if exists
        print("\n🏠 PROPERTY DATA ANALYSIS:")
        print("-" * 40)

        try:
            query = """
            SELECT
                COUNT(*) as total_properties,
                COUNT(DISTINCT county) as counties,
                AVG(just_value) as avg_value,
                MIN(just_value) as min_value,
                MAX(just_value) as max_value,
                AVG(living_area) as avg_living_area,
                AVG(year_built) as avg_year_built
            FROM public.florida_parcels
            WHERE just_value > 0 AND just_value < 100000000
            """

            df_props = pd.read_sql(query, engine)

            if not df_props.empty:
                row = df_props.iloc[0]
                print(f"  Total Properties: {int(row['total_properties']):,}")
                print(f"  Counties: {int(row['counties']) if pd.notna(row['counties']) else 0}")
                print(f"  Average Value: ${int(row['avg_value']):,}" if pd.notna(row['avg_value']) else "N/A")
                print(f"  Value Range: ${int(row['min_value']):,} - ${int(row['max_value']):,}" if pd.notna(row['min_value']) else "N/A")
                print(f"  Avg Living Area: {int(row['avg_living_area']):,} sqft" if pd.notna(row['avg_living_area']) else "N/A")
                print(f"  Avg Year Built: {int(row['avg_year_built'])}" if pd.notna(row['avg_year_built']) else "N/A")
        except Exception as e:
            print(f"  ⚠ Could not analyze property data: {str(e)[:50]}")

        # 5. Check data quality
        print("\n🔍 DATA QUALITY CHECK:")
        print("-" * 40)

        issues = []

        # Check for tables without primary keys
        for schema in schemas[:2]:
            tables = inspector.get_table_names(schema=schema)
            for table in tables[:10]:
                pk = inspector.get_pk_constraint(table, schema=schema)
                if not pk or not pk.get('constrained_columns'):
                    issues.append(f"{schema}.{table} has no primary key")

        if issues:
            for issue in issues[:5]:
                print(f"  ⚠ {issue}")
        else:
            print("  ✓ No major issues found")

        # 6. Database statistics
        print("\n📈 DATABASE STATISTICS:")
        print("-" * 40)

        try:
            stats_query = """
            SELECT
                pg_database_size('postgres') as db_size,
                COUNT(DISTINCT schemaname) as schema_count,
                COUNT(DISTINCT tablename) as table_count
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """

            df_stats = pd.read_sql(stats_query, engine)

            if not df_stats.empty:
                row = df_stats.iloc[0]
                db_size_mb = row['db_size'] / 1024 / 1024
                print(f"  Database Size: {db_size_mb:.2f} MB")
                print(f"  Total Schemas: {row['schema_count']}")
                print(f"  Total Tables: {row['table_count']}")
        except Exception as e:
            print(f"  ⚠ Could not get database stats")

        # 7. Save summary report
        os.makedirs('supabase_analysis_output', exist_ok=True)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'schemas': schemas,
            'tables_analyzed': len(all_tables),
            'total_rows': sum(t['rows'] for t in all_tables),
            'largest_tables': df_tables.head(5).to_dict('records') if all_tables else []
        }

        with open('supabase_analysis_output/quick_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("✓ Summary saved to: supabase_analysis_output/quick_summary.json")

        engine.dispose()
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    analyze_supabase()