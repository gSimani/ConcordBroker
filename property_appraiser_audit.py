import json
import requests
from datetime import datetime
from typing import Dict, List, Any

# MCP Server configuration
MCP_BASE_URL = "http://localhost:3001"
API_KEY = "concordbroker-mcp-key"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

def query_supabase(query_data: Dict) -> Any:
    """Execute a query through MCP Server's Supabase endpoint"""
    response = requests.post(
        f"{MCP_BASE_URL}/api/supabase/query",
        headers=HEADERS,
        json=query_data
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_all_tables():
    """Get all tables in the database"""
    query = {
        "query": """
        SELECT
            schemaname,
            tablename,
            tableowner
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'auth', 'storage', 'realtime', 'vault', 'extensions')
        ORDER BY schemaname, tablename
        """
    }
    return query_supabase(query)

def get_table_columns(table_name: str):
    """Get column details for a specific table"""
    query = {
        "query": f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = '{table_name}'
        ORDER BY ordinal_position
        """
    }
    return query_supabase(query)

def get_table_indexes(table_name: str):
    """Get indexes for a specific table"""
    query = {
        "query": f"""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = '{table_name}'
        """
    }
    return query_supabase(query)

def get_table_constraints(table_name: str):
    """Get constraints for a specific table"""
    query = {
        "query": f"""
        SELECT
            conname AS constraint_name,
            contype AS constraint_type,
            pg_get_constraintdef(c.oid) AS constraint_definition
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        JOIN pg_class r ON r.oid = c.conrelid
        WHERE n.nspname = 'public'
        AND r.relname = '{table_name}'
        """
    }
    return query_supabase(query)

def get_row_counts():
    """Get row counts for property-related tables"""
    query = {
        "query": """
        SELECT
            'florida_parcels' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT county) as unique_counties,
            COUNT(DISTINCT parcel_id) as unique_parcels,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM florida_parcels
        UNION ALL
        SELECT
            'nav_assessments' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT county) as unique_counties,
            COUNT(DISTINCT parcel_id) as unique_parcels,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM nav_assessments
        UNION ALL
        SELECT
            'sdf_sales' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT county) as unique_counties,
            COUNT(DISTINCT parcel_id) as unique_parcels,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM sdf_sales
        UNION ALL
        SELECT
            'nap_characteristics' as table_name,
            COUNT(*) as row_count,
            COUNT(DISTINCT county) as unique_counties,
            COUNT(DISTINCT parcel_id) as unique_parcels,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM nap_characteristics
        """
    }
    return query_supabase(query)

def get_county_coverage():
    """Check data coverage by county"""
    query = {
        "query": """
        SELECT
            county,
            COUNT(DISTINCT parcel_id) as parcel_count,
            COUNT(*) as total_records,
            MIN(sale_date) as earliest_sale,
            MAX(sale_date) as latest_sale,
            AVG(just_value) as avg_just_value,
            AVG(land_value) as avg_land_value
        FROM florida_parcels
        WHERE year = 2025
        GROUP BY county
        ORDER BY county
        """
    }
    return query_supabase(query)

def check_data_routing():
    """Check data routing and relationships between tables"""
    query = {
        "query": """
        SELECT
            'florida_parcels_to_nav' as relationship,
            COUNT(*) as matching_records
        FROM florida_parcels fp
        INNER JOIN nav_assessments nav
            ON fp.parcel_id = nav.parcel_id
            AND fp.county = nav.county
            AND fp.year = nav.year
        WHERE fp.year = 2025
        UNION ALL
        SELECT
            'florida_parcels_to_sdf' as relationship,
            COUNT(*) as matching_records
        FROM florida_parcels fp
        INNER JOIN sdf_sales sdf
            ON fp.parcel_id = sdf.parcel_id
            AND fp.county = sdf.county
        WHERE fp.year = 2025
        UNION ALL
        SELECT
            'florida_parcels_to_nap' as relationship,
            COUNT(*) as matching_records
        FROM florida_parcels fp
        INNER JOIN nap_characteristics nap
            ON fp.parcel_id = nap.parcel_id
            AND fp.county = nap.county
        WHERE fp.year = 2025
        """
    }
    return query_supabase(query)

def main():
    """Run complete database audit"""
    print("=" * 80)
    print("PROPERTY APPRAISER DATABASE AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # Get all tables
    print("\n1. DATABASE TABLES:")
    print("-" * 40)
    tables_result = get_all_tables()
    if tables_result and 'data' in tables_result:
        property_tables = []
        for table in tables_result['data']:
            table_name = table['tablename']
            print(f"  • {table['schemaname']}.{table_name}")

            # Identify property-related tables
            if any(keyword in table_name.lower() for keyword in ['florida', 'parcel', 'property', 'nav', 'nap', 'sdf', 'nal']):
                property_tables.append(table_name)

        print(f"\nFound {len(property_tables)} property-related tables")

    # Get detailed info for florida_parcels
    print("\n2. FLORIDA_PARCELS TABLE STRUCTURE:")
    print("-" * 40)
    columns = get_table_columns('florida_parcels')
    if columns and 'data' in columns:
        for col in columns['data']:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  • {col['column_name']}: {col['data_type']} {nullable}")

    # Get indexes
    print("\n3. INDEXES ON FLORIDA_PARCELS:")
    print("-" * 40)
    indexes = get_table_indexes('florida_parcels')
    if indexes and 'data' in indexes:
        for idx in indexes['data']:
            print(f"  • {idx['indexname']}")
            print(f"    {idx['indexdef']}")

    # Get row counts and statistics
    print("\n4. TABLE STATISTICS:")
    print("-" * 40)
    stats = get_row_counts()
    if stats and 'data' in stats:
        for stat in stats['data']:
            print(f"\n  {stat['table_name']}:")
            print(f"    - Total rows: {stat['row_count']:,}")
            print(f"    - Unique counties: {stat['unique_counties']}")
            print(f"    - Unique parcels: {stat['unique_parcels']:,}")
            print(f"    - Year range: {stat['min_year']} - {stat['max_year']}")

    # Get county coverage
    print("\n5. COUNTY COVERAGE:")
    print("-" * 40)
    coverage = get_county_coverage()
    if coverage and 'data' in coverage:
        total_parcels = 0
        for county in coverage['data']:
            print(f"  • {county['county']}: {county['parcel_count']:,} parcels")
            total_parcels += county['parcel_count']
        print(f"\nTotal parcels across all counties: {total_parcels:,}")

    # Check data routing
    print("\n6. DATA ROUTING & RELATIONSHIPS:")
    print("-" * 40)
    routing = check_data_routing()
    if routing and 'data' in routing:
        for route in routing['data']:
            print(f"  • {route['relationship']}: {route['matching_records']:,} records")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()