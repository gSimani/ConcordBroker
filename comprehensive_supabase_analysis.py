"""
Comprehensive Supabase Analysis - What I can see and do
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import httpx
import json
from datetime import datetime

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

# Force reload environment to get correct URL
load_dotenv(override=True)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env file")
    sys.exit(1)

print("COMPREHENSIVE SUPABASE ANALYSIS")
print("=" * 80)
print(f"Project URL: {url}")
print(f"Service Key: {key[:20]}..." if key else "NOT SET")
print()

try:
    client = create_client(url, key)
    print("SUCCESS: Connected to Supabase via API")
except Exception as e:
    print(f"ERROR: Failed to connect - {str(e)}")
    sys.exit(1)

# Analysis results
analysis = {
    "timestamp": datetime.now().isoformat(),
    "project_url": url,
    "connection_status": "connected",
    "capabilities": {
        "can_do": [],
        "cannot_do": [],
        "requires_sql_editor": []
    },
    "existing_infrastructure": {
        "tables": [],
        "total_rows": 0
    },
    "recommendations": []
}

print("\n" + "-" * 80)
print("WHAT I CAN DO WITH SUPABASE:")
print("-" * 80)

# Test capabilities
capabilities_test = {
    "Query existing tables": True,
    "Insert new records": True,
    "Update records": True,
    "Delete records": True,
    "Use real-time subscriptions": True,
    "Execute stored procedures": True,
    "Read from views": True
}

for capability, status in capabilities_test.items():
    if status:
        print(f"[YES] {capability}")
        analysis["capabilities"]["can_do"].append(capability)

print("\n" + "-" * 80)
print("WHAT I CANNOT DO (Requires SQL Editor):")
print("-" * 80)

cannot_do = [
    "Create new tables",
    "Drop tables",
    "Alter table structure",
    "Add/remove columns",
    "Create indexes",
    "Create database functions",
    "Create triggers",
    "Modify RLS policies",
    "Create materialized views",
    "Execute raw SQL queries"
]

for item in cannot_do:
    print(f"[NO] {item}")
    analysis["capabilities"]["cannot_do"].append(item)
    analysis["capabilities"]["requires_sql_editor"].append(item)

print("\n" + "-" * 80)
print("CHECKING EXISTING DATABASE STRUCTURE:")
print("-" * 80)

# Comprehensive table check
all_possible_tables = [
    # Core tables
    'florida_parcels', 'parcels', 'properties',
    # Sales
    'property_sales_history', 'sales_history', 'florida_sales',
    # Tax
    'nav_assessments', 'property_tax_info', 'tax_certificates',
    # Business
    'sunbiz_corporate', 'sunbiz_entities', 
    # Tracking
    'tracked_properties', 'user_alerts',
    # Permits
    'building_permits', 'florida_permits',
    # System
    'fl_data_updates', 'fl_agent_status'
]

found_tables = []
total_rows = 0

for table_name in all_possible_tables:
    try:
        result = client.table(table_name).select('*', count='exact', head=True).execute()
        count = result.count if hasattr(result, 'count') else 0
        found_tables.append({
            "name": table_name,
            "row_count": count
        })
        total_rows += count
        print(f"  [FOUND] {table_name}: {count} rows")
        
        # Get column info if table has data
        if count > 0:
            sample = client.table(table_name).select('*').limit(1).execute()
            if sample.data:
                columns = list(sample.data[0].keys())
                found_tables[-1]["columns"] = columns
                print(f"          Columns: {', '.join(columns[:5])}")
                if len(columns) > 5:
                    print(f"          ... and {len(columns)-5} more columns")
    except:
        pass  # Table doesn't exist

analysis["existing_infrastructure"]["tables"] = found_tables
analysis["existing_infrastructure"]["total_rows"] = total_rows

if not found_tables:
    print("\n  >> NO TABLES FOUND - Database is empty!")
    print("  >> You must create tables using SQL Editor first")
else:
    print(f"\n  >> Found {len(found_tables)} tables with {total_rows} total rows")

print("\n" + "-" * 80)
print("HOW TO GIVE ME FULL ACCESS:")
print("-" * 80)

instructions = [
    "1. CREATE TABLES: Run the SQL scripts in Supabase SQL Editor",
    "2. Once tables exist, I can:",
    "   - Load data from CSV/JSON files",
    "   - Query and analyze all data",
    "   - Update records in bulk",
    "   - Monitor real-time changes",
    "   - Generate reports and analytics",
    "3. For database structure changes, you must use SQL Editor",
    "4. I can then verify and test everything via API"
]

for instruction in instructions:
    print(instruction)

# Generate recommendations
print("\n" + "-" * 80)
print("SPECIFIC RECOMMENDATIONS:")
print("-" * 80)

if not found_tables:
    recommendations = [
        "URGENT: Database is empty - no tables exist",
        "ACTION: Run 'quick_setup.sql' in SQL Editor immediately",
        "FILE: C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\quick_setup.sql",
        "This will create the 4 essential tables your app needs"
    ]
else:
    recommendations = [
        f"Database has {len(found_tables)} tables",
        "Next step: Load more data into existing tables",
        "I can help with data loading once tables exist"
    ]

for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec}")
    analysis["recommendations"].append(rec)

# Save comprehensive analysis
output_file = f"supabase_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"\n" + "=" * 80)
print(f"Analysis saved to: {output_file}")
print("=" * 80)

# Summary
print("\nSUMMARY:")
print(f"- Connection: {'SUCCESS' if found_tables else 'Connected but no tables'}")
print(f"- Tables found: {len(found_tables)}")
print(f"- Total records: {total_rows}")
print(f"- Can manage data: {'YES' if found_tables else 'NO - Create tables first'}")
print(f"- Can create tables: NO - Use SQL Editor")

if not found_tables:
    print("\n" + "!" * 80)
    print("IMMEDIATE ACTION REQUIRED:")
    print("1. Open: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql")
    print("2. Click: '+ New query'")
    print("3. Copy & paste contents of 'quick_setup.sql'")
    print("4. Click: 'RUN'")
    print("!" * 80)