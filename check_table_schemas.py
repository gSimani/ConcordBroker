"""
Check actual table schemas in Supabase
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('apps/web/.env')

def check_schemas():
    """Check the actual schemas of tables in Supabase"""
    
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("[ERROR] Missing Supabase credentials")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    tables_to_check = [
        'property_sales_history',
        'nav_assessments', 
        'sunbiz_corporate',
        'florida_permits',
        'tax_certificates'
    ]
    
    print("="*60)
    print("TABLE SCHEMA INSPECTION")
    print("="*60)
    
    for table in tables_to_check:
        print(f"\n[TABLE] {table}")
        print("-"*40)
        
        try:
            # Get one record to see columns
            response = supabase.table(table).select('*').limit(1).execute()
            
            if response.data and len(response.data) > 0:
                columns = list(response.data[0].keys())
                print(f"Columns: {', '.join(columns)}")
                
                # Show sample data types
                sample = response.data[0]
                print("\nSample values:")
                for col, val in sample.items():
                    val_type = type(val).__name__
                    val_preview = str(val)[:50] if val else 'NULL'
                    print(f"  {col}: {val_type} = {val_preview}")
            else:
                print("Table exists but has no data to inspect columns")
                
        except Exception as e:
            error_msg = str(e)
            if 'Could not find the table' in error_msg:
                print(f"[MISSING] Table does not exist")
            else:
                print(f"[ERROR] {error_msg[:200]}")
    
    print("\n" + "="*60)
    print("SCHEMA INSPECTION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    check_schemas()