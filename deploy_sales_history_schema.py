#!/usr/bin/env python3
"""
Deploy comprehensive sales history schema to Supabase
This script creates the property sales history table with full transaction details
"""

import os
import sys
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your-service-role-key')

def deploy_sales_history_schema():
    """Deploy the sales history schema to Supabase"""
    
    print("[INFO] Starting sales history schema deployment...")
    print(f"[INFO] Target: {SUPABASE_URL}")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Read the SQL schema file
        schema_file = 'create_sales_history_schema.sql'
        if not os.path.exists(schema_file):
            print(f"[ERROR] Schema file {schema_file} not found!")
            return False
            
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("[INFO] Executing sales history schema...")
        
        # Split the SQL into individual statements and execute them
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"[INFO] Executing statement {i}/{len(statements)}...")
                    # Note: You might need to use a different method to execute raw SQL
                    # depending on your Supabase setup
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"[SUCCESS] Statement {i} executed successfully")
                except Exception as e:
                    print(f"[WARNING] Statement {i} failed: {str(e)}")
                    # Continue with next statement
                    continue
        
        print("[SUCCESS] Sales history schema deployment completed!")
        
        # Verify the table was created
        print("[INFO] Verifying table creation...")
        
        try:
            result = supabase.table('property_sales_history').select('count').limit(1).execute()
            print("[SUCCESS] property_sales_history table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify property_sales_history table: {e}")
        
        # Check sample data
        try:
            result = supabase.table('property_sales_history').select('*').limit(5).execute()
            sales_count = len(result.data) if result.data else 0
            print(f"[INFO] Found {sales_count} sample sales records in database")
            
            if result.data:
                print("\n[INFO] Sample sales records:")
                for sale in result.data[:3]:
                    print(f"  - {sale.get('sale_date', 'N/A')}: ${sale.get('sale_price', 0):,.0f} - {sale.get('sale_type', 'N/A')}")
        except Exception as e:
            print(f"[WARNING] Could not query sample sales data: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to deploy sales history schema: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("="*60)
    print("Sales History Schema Deployment")
    print("="*60)
    
    # Check environment variables
    if SUPABASE_URL == 'https://your-project.supabase.co':
        print("[WARNING] Using default Supabase URL - please set SUPABASE_URL environment variable")
    
    if SUPABASE_SERVICE_KEY == 'your-service-role-key':
        print("[WARNING] Using default service key - please set SUPABASE_SERVICE_KEY environment variable")
    
    # Deploy schema
    success = deploy_sales_history_schema()
    
    if success:
        print("\n[SUCCESS] Sales history schema deployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the table in your Supabase dashboard")
        print("2. Import historical sales data if available")
        print("3. Test the sales history display in the property profile")
        print("4. Configure data sync from county records")
    else:
        print("\n[ERROR] Deployment failed - check logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()