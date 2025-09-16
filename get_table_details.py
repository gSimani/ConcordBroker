#!/usr/bin/env python3
"""
Get detailed information about key tables in ConcordBroker Supabase database
"""

import requests
import json

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Key tables to examine in detail
key_tables = [
    "florida_parcels",
    "tax_deed_auctions",
    "tax_deed_bidding_items",
    "sunbiz_contacts",
    "sunbiz_officers",
    "property_assessments",
    "nav_assessments",
    "tax_certificates",
    "florida_active_entities_with_contacts",
    "property_tax_certificate_summary"
]

def get_table_sample(table_name, limit=3):
    """Get sample records from a table"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}",
            headers=headers,
            params={"limit": limit}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting sample for {table_name}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting sample for {table_name}: {e}")
        return []

def analyze_key_tables():
    """Analyze key tables in detail"""
    print("Detailed Analysis of Key ConcordBroker Tables")
    print("=" * 60)

    detailed_analysis = {}

    for table_name in key_tables:
        print(f"\nAnalyzing: {table_name}")
        print("-" * 40)

        # Get sample records
        sample_records = get_table_sample(table_name, limit=2)

        if sample_records:
            first_record = sample_records[0]

            print(f"Records found: {len(sample_records)}")
            print(f"Columns ({len(first_record)}): {', '.join(first_record.keys())}")

            # Show sample data for key fields
            if table_name == "florida_parcels":
                key_fields = ["parcel_id", "county", "year", "owner_name", "phy_addr1", "land_sqft", "just_value"]
            elif table_name == "tax_deed_bidding_items":
                key_fields = ["parcel_id", "tax_deed_number", "legal_situs_address", "assessed_value", "bid_amount"]
            elif table_name == "sunbiz_contacts":
                key_fields = ["doc_number", "officer_name", "officer_email", "officer_phone", "entity_name"]
            elif table_name == "property_assessments":
                key_fields = ["parcel_id", "county_name", "owner_name", "property_address", "total_value"]
            else:
                # Show first 5 fields as sample
                key_fields = list(first_record.keys())[:5]

            print("\nSample data:")
            for field in key_fields:
                if field in first_record:
                    value = first_record[field]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {field}: {value}")

            detailed_analysis[table_name] = {
                "record_count": len(sample_records),
                "columns": list(first_record.keys()),
                "sample_record": first_record
            }
        else:
            print("No records found")
            detailed_analysis[table_name] = {
                "record_count": 0,
                "columns": [],
                "sample_record": {}
            }

    # Check for specific property appraiser county distribution
    print(f"\n\nCOUNTY DATA ANALYSIS")
    print("=" * 60)

    # Check florida_parcels county distribution
    print("\nFlorida Parcels County Distribution:")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/florida_parcels",
            headers=headers,
            params={"select": "county", "limit": "10"}
        )
        if response.status_code == 200:
            data = response.json()
            counties = [record.get('county') for record in data if record.get('county')]
            unique_counties = list(set(counties))
            print(f"  Sample counties found: {unique_counties}")
        else:
            print(f"  Could not retrieve county data: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

    # Save detailed analysis
    with open('detailed_table_analysis.json', 'w') as f:
        json.dump(detailed_analysis, f, indent=2)

    print(f"\nDetailed analysis saved to: detailed_table_analysis.json")

if __name__ == "__main__":
    analyze_key_tables()