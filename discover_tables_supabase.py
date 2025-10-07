#!/usr/bin/env python3
"""
Discover all tables via Supabase Python client
"""

from supabase import create_client, Client
import json

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try common table names
potential_tables = [
    # Property tables
    'florida_parcels', 'fl_parcels', 'parcels', 'properties',
    # Sales tables
    'property_sales_history', 'fl_sdf_sales', 'sdf_sales', 'florida_sdf_sales', 'sales_history',
    # Entity tables
    'sunbiz_corporate', 'florida_entities', 'fl_entities', 'entities',
    # Tax tables
    'tax_certificates', 'tax_deed_items', 'tax_liens',
    # Ownership tables
    'owner_identities', 'property_ownership', 'entity_principals',
    # Views
    'sales_data_view', 'tax_deed_items_view',
]

found_tables = {}

print("\n=== DISCOVERING SUPABASE TABLES ===\n")

for table in potential_tables:
    try:
        response = supabase.table(table).select("*", count="exact").limit(0).execute()
        count = response.count or 0
        found_tables[table] = count
        print(f"[FOUND] {table:<35} {count:>15,} rows")
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg:
            # Extract suggested table name from error
            if "hint" in error_msg.lower():
                print(f"[NOT FOUND] {table:<35} (table does not exist)")
        else:
            print(f"[ERROR] {table:<35} {error_msg[:50]}")

print("\n=== SUMMARY ===")
print(f"Found {len(found_tables)} tables with data")
print(f"Total records: {sum(found_tables.values()):,}")

# Save results
with open("discovered_tables.json", "w") as f:
    json.dump(found_tables, f, indent=2)

print("\nResults saved to: discovered_tables.json")
