#!/usr/bin/env python3
"""
Simple schema check for Supabase database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize Supabase client
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("ERROR: Missing Supabase credentials")
        return
    
    supabase: Client = create_client(url, service_key)
    
    print("=== SUPABASE DATABASE SCHEMA CHECK ===")
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
            # Try to get column info to check if table exists
            result = supabase.table(table_name).select("*").limit(1).execute()
            existing_tables.append(table_name)
            record_count = len(result.data) if result.data else 0
            print(f"+ {table_name}: EXISTS (sample records: {record_count})")
            
            # Try to get more records to check data volume
            try:
                count_result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
                total_count = count_result.count if hasattr(count_result, 'count') else "Unknown"
                print(f"  Total records: {total_count}")
            except:
                pass
                
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
    
    # Check if florida_parcels exists and has data
    if 'florida_parcels' in existing_tables:
        try:
            sample = supabase.table('florida_parcels').select("*").limit(5).execute()
            if sample.data:
                print(f"\n=== FLORIDA_PARCELS SAMPLE DATA ===")
                for i, record in enumerate(sample.data):
                    print(f"Record {i+1}: {list(record.keys())[:10]}...")
                    break
        except Exception as e:
            print(f"Error getting sample data: {e}")

if __name__ == "__main__":
    main()