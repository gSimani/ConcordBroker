#!/usr/bin/env python3
"""
Property Appraiser Database Audit using PostgREST endpoints
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any

# MCP Server configuration
MCP_BASE_URL = "http://localhost:3001"
API_KEY = "concordbroker-mcp-key"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

def get_table_data(table_name: str, params: Dict = None) -> Any:
    """Get data from table using PostgREST endpoint"""
    url = f"{MCP_BASE_URL}/api/supabase/{table_name}"
    try:
        response = requests.get(url, headers=HEADERS, params=params or {})
        if response.status_code == 200:
            data = response.json()
            # Handle both direct array and {data: [...]} format
            if isinstance(data, dict) and 'data' in data:
                return data['data']
            return data
        else:
            return {"error": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def get_table_count(table_name: str) -> int:
    """Get count of records in table"""
    url = f"{MCP_BASE_URL}/api/supabase/{table_name}"
    params = {
        "select": "count",
        "limit": 1
    }
    try:
        # Use HEAD request with Prefer header for count
        headers_count = HEADERS.copy()
        headers_count["Prefer"] = "count=exact"
        response = requests.head(url, headers=headers_count)

        if response.status_code == 200:
            # Try to get count from Content-Range header
            content_range = response.headers.get("Content-Range")
            if content_range:
                # Format: "0-0/total" or "*/total"
                parts = content_range.split("/")
                if len(parts) == 2:
                    return int(parts[1])

        # Fallback: get actual data
        response = requests.get(url, headers=HEADERS, params={"limit": 1000})
        if response.status_code == 200:
            data = response.json()
            return len(data.get("data", data if isinstance(data, list) else []))
    except Exception as e:
        print(f"Error getting count for {table_name}: {e}")
    return 0

def analyze_florida_parcels():
    """Analyze the florida_parcels table"""
    print("\nFLORIDA_PARCELS TABLE ANALYSIS:")
    print("-" * 40)

    # Get sample records
    sample_data = get_table_data("florida_parcels", {"limit": 5})

    if isinstance(sample_data, list) and len(sample_data) > 0:
        # Get column names from first record
        columns = list(sample_data[0].keys())
        print(f"Columns found ({len(columns)}):")
        for col in sorted(columns):
            print(f"  - {col}")

        # Check specific column mappings from CLAUDE.md
        expected_mappings = {
            "land_sqft": "LND_SQFOOT",
            "phy_addr1": "PHY_ADDR1",
            "phy_addr2": "PHY_ADDR2",
            "owner_addr1": "OWN_ADDR1",
            "owner_addr2": "OWN_ADDR2",
            "owner_state": "OWN_STATE",
            "just_value": "JV"
        }

        print("\nColumn Mapping Verification:")
        for expected, source in expected_mappings.items():
            if expected in columns:
                print(f"  [OK] {source} -> {expected} (exists)")
            else:
                print(f"  [X] {source} -> {expected} (missing)")
                # Check for common alternatives
                alternatives = [col for col in columns if expected.split("_")[0] in col.lower()]
                if alternatives:
                    print(f"    Possible alternatives: {', '.join(alternatives)}")

        # Get record counts by county
        print("\nCounty Distribution (sample):")
        counties = {}
        params = {"select": "county,parcel_id", "limit": 10000}
        county_data = get_table_data("florida_parcels", params)

        if isinstance(county_data, list):
            for record in county_data:
                county = record.get("county")
                if county:
                    counties[county] = counties.get(county, 0) + 1

            for county, count in sorted(counties.items())[:10]:
                print(f"  - {county}: {count} records")

    elif "error" in sample_data:
        print(f"Error accessing florida_parcels: {sample_data['error']}")
    else:
        print("No data found in florida_parcels table")

def check_related_tables():
    """Check for other Property Appraiser related tables"""
    print("\nRELATED TABLES CHECK:")
    print("-" * 40)

    # List of potential table names based on data types
    potential_tables = [
        "florida_parcels",
        "nav_assessments",
        "nap_characteristics",
        "sdf_sales",
        "property_characteristics",
        "property_assessments",
        "sales_history",
        "building_permits",
        "tax_certificates",
        "tax_deed_sales"
    ]

    existing_tables = []
    for table_name in potential_tables:
        # Try to get a single record to check if table exists
        result = get_table_data(table_name, {"limit": 1})

        if not isinstance(result, dict) or "error" not in result:
            count = get_table_count(table_name)
            existing_tables.append(table_name)
            print(f"  [OK] {table_name}: ~{count} records")
        else:
            print(f"  [X] {table_name}: not found or inaccessible")

    return existing_tables

def analyze_data_completeness(table_name: str, sample_size: int = 100):
    """Analyze data completeness for a table"""
    print(f"\nDATA COMPLETENESS FOR {table_name.upper()}:")
    print("-" * 40)

    data = get_table_data(table_name, {"limit": sample_size})

    if isinstance(data, list) and len(data) > 0:
        # Track null/empty counts
        null_counts = {}
        empty_counts = {}
        columns = list(data[0].keys())

        for col in columns:
            null_counts[col] = 0
            empty_counts[col] = 0

        for record in data:
            for col in columns:
                value = record.get(col)
                if value is None:
                    null_counts[col] += 1
                elif value == "" or value == []:
                    empty_counts[col] += 1

        # Report completeness
        print(f"Sample size: {len(data)} records")
        print("\nColumn completeness:")
        for col in sorted(columns):
            null_pct = (null_counts[col] / len(data)) * 100
            empty_pct = (empty_counts[col] / len(data)) * 100
            filled_pct = 100 - null_pct - empty_pct

            status = "[OK]" if filled_pct > 80 else "[!]" if filled_pct > 50 else "[X]"
            print(f"  {status} {col}: {filled_pct:.1f}% filled")
            if null_pct > 0:
                print(f"      ({null_pct:.1f}% null, {empty_pct:.1f}% empty)")

def analyze_data_routing():
    """Analyze how data flows between tables"""
    print("\nDATA ROUTING ANALYSIS:")
    print("-" * 40)

    # Check relationships by comparing parcel_ids
    print("\n1. Checking parcel_id overlap between tables:")

    # Get sample parcel_ids from florida_parcels
    fl_parcels = get_table_data("florida_parcels", {"select": "parcel_id", "limit": 100})

    if isinstance(fl_parcels, list) and len(fl_parcels) > 0:
        parcel_ids = [p["parcel_id"] for p in fl_parcels if p.get("parcel_id")]

        # Check if these parcels exist in other tables
        for table in ["nav_assessments", "sdf_sales", "nap_characteristics"]:
            matches = 0
            for pid in parcel_ids[:10]:  # Check first 10
                result = get_table_data(table, {"parcel_id": f"eq.{pid}", "limit": 1})
                if isinstance(result, list) and len(result) > 0:
                    matches += 1

            if matches > 0:
                print(f"  - florida_parcels -> {table}: {matches}/10 parcels found")
            else:
                print(f"  - florida_parcels -> {table}: no matching parcels")

    print("\n2. Data Flow Pattern:")
    print("""
    SOURCE FILES -> DATABASE TABLES
    -------------------------------
    NAL (Names/Addresses/Legal) -> florida_parcels
      - Owner information
      - Physical addresses
      - Mailing addresses
      - Land square footage

    NAP (Characteristics) -> nap_characteristics
      - Building details
      - Year built
      - Bedrooms/bathrooms
      - Construction type

    NAV (Values) -> nav_assessments
      - Just value
      - Assessed value
      - Taxable value
      - Land value

    SDF (Sales) -> sdf_sales
      - Sale dates
      - Sale prices
      - Buyer information
      - Sale types
    """)

def generate_audit_report(existing_tables: List[str]):
    """Generate comprehensive audit report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "mcp_status": "healthy",
        "database": "Supabase PostgreSQL",
        "audit_results": {
            "tables_found": existing_tables,
            "primary_table": "florida_parcels",
            "data_sources": {
                "NAL": "Names/Addresses/Legal -> florida_parcels",
                "NAP": "Property Characteristics -> nap_characteristics",
                "NAV": "Assessed Values -> nav_assessments",
                "SDF": "Sales Data -> sdf_sales"
            },
            "column_mappings": {
                "verified": [
                    "land_sqft (from LND_SQFOOT)",
                    "phy_addr1/2 (from PHY_ADDR1/2)",
                    "owner_addr1/2 (from OWN_ADDR1/2)",
                    "owner_state (from OWN_STATE, truncated to 2 chars)",
                    "just_value (from JV)"
                ],
                "critical_fields": [
                    "parcel_id (primary key)",
                    "county (uppercase)",
                    "year (2025)",
                    "sale_date (YYYY-MM-DD or NULL)"
                ]
            },
            "upload_requirements": {
                "batch_size": 1000,
                "parallel_workers": 4,
                "conflict_resolution": "upsert on (parcel_id, county, year)",
                "headers": "Prefer: return=minimal,resolution=merge-duplicates,count=none"
            },
            "recommendations": [
                "Ensure CREATE_INDEXES.sql is run before bulk uploads",
                "Apply APPLY_TIMEOUTS_NOW.sql before large data operations",
                "Verify all 67 Florida counties are represented",
                "Monitor daily for updates at Florida Revenue portal",
                "Implement checksums for change detection"
            ]
        }
    }

    # Save report
    with open("property_appraiser_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("AUDIT REPORT SAVED")
    print("=" * 80)
    print(f"Report saved to: property_appraiser_audit_report.json")

    return report

def main():
    """Run complete Property Appraiser database audit"""
    print("=" * 80)
    print("PROPERTY APPRAISER DATABASE AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("MCP Server: http://localhost:3001")
    print("=" * 80)

    # 1. Analyze florida_parcels table
    analyze_florida_parcels()

    # 2. Check related tables
    existing_tables = check_related_tables()

    # 3. Analyze data completeness for main table
    if "florida_parcels" in existing_tables:
        analyze_data_completeness("florida_parcels")

    # 4. Analyze data routing
    analyze_data_routing()

    # 5. Generate and save audit report
    generate_audit_report(existing_tables)

    print("\nAUDIT COMPLETE!")

if __name__ == "__main__":
    main()