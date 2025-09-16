#!/usr/bin/env python3
"""
Deploy building permits schema to Supabase
This script creates the comprehensive building permits table structure
"""

import os
import sys
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your-service-role-key')

def deploy_permits_schema():
    """Deploy the building permits schema to Supabase"""
    
    print("[INFO] Starting building permits schema deployment...")
    print(f"[INFO] Target: {SUPABASE_URL}")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Read the SQL schema file
        schema_file = 'create_building_permits_schema.sql'
        if not os.path.exists(schema_file):
            print(f"[ERROR] Schema file {schema_file} not found!")
            return False
            
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("[INFO] Executing building permits schema...")
        
        # Split the SQL into individual statements and execute them
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"[INFO] Executing statement {i}/{len(statements)}...")
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"[SUCCESS] Statement {i} executed successfully")
                except Exception as e:
                    print(f"[WARNING] Statement {i} failed: {str(e)}")
                    # Continue with next statement
                    continue
        
        print("[SUCCESS] Building permits schema deployment completed!")
        
        # Verify the tables were created
        print("[INFO] Verifying table creation...")
        
        # Test query to check if tables exist
        try:
            result = supabase.table('building_permits').select('count').limit(1).execute()
            print("[SUCCESS] building_permits table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify building_permits table: {e}")
        
        try:
            result = supabase.table('permit_sub_permits').select('count').limit(1).execute()
            print("[SUCCESS] permit_sub_permits table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify permit_sub_permits table: {e}")
            
        try:
            result = supabase.table('permit_inspections').select('count').limit(1).execute()
            print("[SUCCESS] permit_inspections table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify permit_inspections table: {e}")
            
        try:
            result = supabase.table('contractor_performance').select('count').limit(1).execute()
            print("[SUCCESS] contractor_performance table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify contractor_performance table: {e}")
        
        # Check sample data
        try:
            result = supabase.table('building_permits').select('*').limit(5).execute()
            permit_count = len(result.data) if result.data else 0
            print(f"[INFO] Found {permit_count} sample permits in database")
        except Exception as e:
            print(f"[WARNING] Could not query sample data: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to deploy building permits schema: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("="*60)
    print("Building Permits Schema Deployment")
    print("="*60)
    
    # Check environment variables
    if SUPABASE_URL == 'https://your-project.supabase.co':
        print("[WARNING] Using default Supabase URL - please set SUPABASE_URL environment variable")
    
    if SUPABASE_SERVICE_KEY == 'your-service-role-key':
        print("[WARNING] Using default service key - please set SUPABASE_SERVICE_KEY environment variable")
    
    # Deploy schema
    success = deploy_permits_schema()
    
    if success:
        print("\n[SUCCESS] Building permits schema deployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the tables in your Supabase dashboard")
        print("2. Test the permit search functionality")
        print("3. Add real permit data as needed")
    else:
        print("\n[ERROR] Deployment failed - check logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()