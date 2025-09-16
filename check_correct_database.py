#!/usr/bin/env python3
"""
Check correct Supabase database using explicit credentials
"""

import os
from supabase import create_client, Client

def main():
    # Use explicit credentials from the main .env file
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    
    supabase: Client = create_client(url, service_key)
    
    print("=== CORRECT SUPABASE DATABASE CHECK ===")
    print(f"Database URL: {url}")
    
    # Check for common property-related tables
    tables_to_check = [
        'florida_parcels', 
        'broward_properties', 
        'properties', 
        'nap_data',
        'nav_assessments',
        'sdf_sales',
        'assessments', 
        'sales_history', 
        'building_permits',
        'tax_certificates', 
        'sunbiz_entities',
        'permit_data',
        'tax_deed_applications'
    ]
    
    existing_tables = []
    missing_tables = []
    
    print("\n=== TABLE EXISTENCE CHECK ===")
    for table_name in tables_to_check:
        try:
            # Try to get one record to check if table exists
            result = supabase.table(table_name).select("*").limit(1).execute()
            existing_tables.append(table_name)
            
            # Try to get count
            try:
                count_result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
                total_count = count_result.count if hasattr(count_result, 'count') else "Unknown"
                print(f"+ {table_name}: EXISTS (Total: {total_count})")
            except:
                print(f"+ {table_name}: EXISTS (Count unknown)")
                
        except Exception as e:
            missing_tables.append(table_name)
            if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                print(f"- {table_name}: NOT EXISTS")
            else:
                print(f"? {table_name}: ERROR - {str(e)[:100]}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Existing tables: {len(existing_tables)}")
    print(f"Missing tables: {len(missing_tables)}")
    
    if existing_tables:
        print(f"\nEXISTING: {', '.join(existing_tables)}")
    
    if missing_tables:
        print(f"\nMISSING: {', '.join(missing_tables)}")
        
    # Check if we can create tables (test database permissions)
    print(f"\n=== DATABASE PERMISSIONS TEST ===")
    try:
        # Try to create a test table
        test_query = """
        CREATE TABLE IF NOT EXISTS test_permissions (
            id SERIAL PRIMARY KEY,
            test_field TEXT
        );
        """
        # This won't work via supabase-py, so let's try a simpler test
        result = supabase.table('test_permissions').insert({"test_field": "test"}).execute()
        print("✓ Database write permissions: OK")
        
        # Clean up
        supabase.table('test_permissions').delete().eq('test_field', 'test').execute()
        
    except Exception as e:
        print(f"✗ Database write test failed: {str(e)[:100]}")

if __name__ == "__main__":
    main()