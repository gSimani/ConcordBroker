#!/usr/bin/env python3
"""
Check current Supabase database schema for NAP data import planning
"""

import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv
import json

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
    
    print("=== SUPABASE DATABASE SCHEMA ANALYSIS ===")
    print(f"Database URL: {url}")
    
    try:
        # Get all tables in the public schema
        result = supabase.rpc('get_table_info', {}).execute()
        
        if result.data:
            print(f"\nFound {len(result.data)} tables:")
            for table in result.data:
                print(f"- {table}")
        else:
            print("\nNo tables found or RPC not available. Checking manually...")
            
        # Try to get table information using SQL query
        query = """
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        ORDER BY table_name, ordinal_position;
        """
        
        # Use the service key to run queries
        result = supabase.postgrest.rpc('exec_sql', {'sql': query}).execute()
        
        if not result.data:
            print("Cannot access schema info. Trying alternative method...")
            
            # Check for common property-related tables
            common_tables = [
                'florida_parcels', 'broward_properties', 'properties', 
                'nap_data', 'assessments', 'sales_history', 'permits',
                'tax_certificates', 'sunbiz_entities'
            ]
            
            schema_info = {}
            for table_name in common_tables:
                try:
                    # Try to get a single row to check if table exists
                    result = supabase.table(table_name).select("*").limit(1).execute()
                    schema_info[table_name] = "EXISTS"
                    print(f"✓ Table '{table_name}' exists")
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        schema_info[table_name] = "NOT_EXISTS"
                    else:
                        schema_info[table_name] = f"ERROR: {str(e)}"
            
            print(f"\n=== TABLE EXISTENCE CHECK ===")
            for table, status in schema_info.items():
                print(f"{table}: {status}")
                
    except Exception as e:
        print(f"Error checking schema: {e}")
        
        # Fallback - check for existing data
        print("\n=== FALLBACK: CHECKING FOR EXISTING PROPERTY DATA ===")
        
        test_queries = [
            ("florida_parcels", "SELECT COUNT(*) as count FROM florida_parcels"),
            ("properties", "SELECT COUNT(*) as count FROM properties"),
            ("broward_properties", "SELECT COUNT(*) as count FROM broward_properties"),
            ("nap_data", "SELECT COUNT(*) as count FROM nap_data")
        ]
        
        for table_name, query in test_queries:
            try:
                result = supabase.postgrest.rpc('exec_sql', {'sql': query}).execute()
                if result.data:
                    print(f"✓ {table_name}: {result.data[0].get('count', 0)} records")
            except Exception as e:
                print(f"✗ {table_name}: {str(e)}")

if __name__ == "__main__":
    main()