"""
Direct Database Check - Using raw SQL queries
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import httpx
import json

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

def check_database():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print(f"Connecting to: {url}")
    client = create_client(url, key)
    
    # List of potential tables to check
    tables_to_check = [
        'parcels', 
        'florida_parcels', 
        'broward_parcels',
        'properties',
        'sales_history',
        'florida_sales',
        'building_permits',
        'florida_permits',
        'sunbiz_corporations',
        'sunbiz_entities',
        'property_owners',
        'property_assessments',
        'nav_assessments',
        'sdf_sales',
        'nal_parcels',
        'nap_parcels',
        'tpp_tangible',
        'property_tax_info',
        'tracked_properties',
        'user_alerts',
        'property_profiles',
        'entity_matching',
        'florida_revenue',
        'florida_nav',
        'florida_nav_roll',
        'broward_daily_index'
    ]
    
    print("\nChecking for tables...")
    print("=" * 60)
    
    existing_tables = []
    table_details = {}
    
    for table_name in tables_to_check:
        try:
            # Try to query the table
            result = client.table(table_name).select('*', count='exact', head=True).execute()
            count = result.count if hasattr(result, 'count') else 0
            existing_tables.append(table_name)
            table_details[table_name] = count
            print(f"✓ {table_name}: {count:,} rows")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" not in error_msg.lower():
                print(f"⚠ {table_name}: Error - {error_msg[:50]}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Tables found: {len(existing_tables)}")
    print(f"  Tables checked: {len(tables_to_check)}")
    
    if existing_tables:
        print(f"\nEXISTING TABLES:")
        for table in existing_tables:
            count = table_details.get(table, 0)
            status = "EMPTY" if count == 0 else f"{count:,} rows"
            print(f"  - {table}: {status}")
        
        # Identify large tables
        large_tables = [(t, c) for t, c in table_details.items() if c > 100000]
        if large_tables:
            print(f"\nLARGE TABLES (>100K rows):")
            for table, count in sorted(large_tables, key=lambda x: x[1], reverse=True):
                print(f"  - {table}: {count:,} rows")
        
        # Identify empty tables
        empty_tables = [t for t, c in table_details.items() if c == 0]
        if empty_tables:
            print(f"\nEMPTY TABLES ({len(empty_tables)}):")
            for table in empty_tables:
                print(f"  - {table}")
    else:
        print("\nNo tables found in the database!")
        print("\nPossible issues:")
        print("1. Database not properly initialized")
        print("2. Wrong database URL or credentials")
        print("3. Tables exist in different schema")
        
    # Save results
    results = {
        "existing_tables": existing_tables,
        "table_details": table_details,
        "empty_tables": [t for t, c in table_details.items() if c == 0],
        "large_tables": [(t, c) for t, c in table_details.items() if c > 100000]
    }
    
    with open('db_check_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: db_check_results.json")

if __name__ == "__main__":
    check_database()