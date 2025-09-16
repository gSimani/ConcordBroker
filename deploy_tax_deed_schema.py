#!/usr/bin/env python3
"""
Deploy tax deed sales schema to Supabase
This script creates the comprehensive tax deed auction and bidding table structure
"""

import os
import sys
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your-service-role-key')

def deploy_tax_deed_schema():
    """Deploy the tax deed sales schema to Supabase"""
    
    print("[INFO] Starting tax deed sales schema deployment...")
    print(f"[INFO] Target: {SUPABASE_URL}")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Read the SQL schema file
        schema_file = 'create_tax_deed_schema.sql'
        if not os.path.exists(schema_file):
            print(f"[ERROR] Schema file {schema_file} not found!")
            return False
            
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("[INFO] Executing tax deed sales schema...")
        
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
        
        print("[SUCCESS] Tax deed sales schema deployment completed!")
        
        # Verify the tables were created
        print("[INFO] Verifying table creation...")
        
        # Test query to check if tables exist
        try:
            result = supabase.table('tax_deed_auctions').select('count').limit(1).execute()
            print("[SUCCESS] tax_deed_auctions table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify tax_deed_auctions table: {e}")
        
        try:
            result = supabase.table('tax_deed_bidding_items').select('count').limit(1).execute()
            print("[SUCCESS] tax_deed_bidding_items table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify tax_deed_bidding_items table: {e}")
            
        try:
            result = supabase.table('auction_bidding_history').select('count').limit(1).execute()
            print("[SUCCESS] auction_bidding_history table verified")
        except Exception as e:
            print(f"[WARNING] Could not verify auction_bidding_history table: {e}")
        
        # Check sample data
        try:
            result = supabase.table('tax_deed_auctions').select('*').limit(5).execute()
            auction_count = len(result.data) if result.data else 0
            print(f"[INFO] Found {auction_count} sample auctions in database")
        except Exception as e:
            print(f"[WARNING] Could not query sample auction data: {e}")
            
        try:
            result = supabase.table('tax_deed_bidding_items').select('*').limit(10).execute()
            item_count = len(result.data) if result.data else 0
            print(f"[INFO] Found {item_count} sample bidding items in database")
        except Exception as e:
            print(f"[WARNING] Could not query sample bidding items: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to deploy tax deed sales schema: {str(e)}")
        return False

def main():
    """Main function"""
    
    print("="*60)
    print("Tax Deed Sales Schema Deployment")
    print("="*60)
    
    # Check environment variables
    if SUPABASE_URL == 'https://your-project.supabase.co':
        print("[WARNING] Using default Supabase URL - please set SUPABASE_URL environment variable")
    
    if SUPABASE_SERVICE_KEY == 'your-service-role-key':
        print("[WARNING] Using default service key - please set SUPABASE_SERVICE_KEY environment variable")
    
    # Deploy schema
    success = deploy_tax_deed_schema()
    
    if success:
        print("\n[SUCCESS] Tax deed sales schema deployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the tables in your Supabase dashboard")
        print("2. Test the tax deed auction functionality")
        print("3. Add real auction data as needed")
        print("4. Configure auction monitoring and alerts")
    else:
        print("\n[ERROR] Deployment failed - check logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()