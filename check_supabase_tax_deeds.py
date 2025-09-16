import os
from supabase import create_client, Client
import json
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

def check_tax_deed_database():
    print("Connecting to Supabase...")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    analysis_results = {
        "timestamp": datetime.now().isoformat(),
        "database_url": SUPABASE_URL,
        "tables_checked": [],
        "errors": []
    }
    
    try:
        # Check for tax deed related tables
        tax_deed_tables = [
            'tax_deed_bidding_items',
            'tax_deed_sales',
            'tax_deeds',
            'tax_deed_auctions',
            'broward_tax_deeds',
            'auction_items'
        ]
        
        for table_name in tax_deed_tables:
            try:
                print(f"\nChecking table: {table_name}")
                
                # Try to get a count of records
                response = supabase.table(table_name).select("*", count="exact").limit(1).execute()
                
                count = response.count if hasattr(response, 'count') else len(response.data)
                print(f"Table {table_name}: {count} records found")
                
                # Get sample data
                sample_response = supabase.table(table_name).select("*").limit(5).execute()
                sample_data = sample_response.data
                
                # Get table schema info
                if sample_data:
                    columns = list(sample_data[0].keys()) if sample_data else []
                else:
                    columns = []
                
                table_info = {
                    "table_name": table_name,
                    "record_count": count,
                    "columns": columns,
                    "sample_data": sample_data,
                    "exists": True
                }
                
                analysis_results["tables_checked"].append(table_info)
                
            except Exception as e:
                error_msg = f"Error checking table {table_name}: {str(e)}"
                print(error_msg)
                analysis_results["errors"].append(error_msg)
                analysis_results["tables_checked"].append({
                    "table_name": table_name,
                    "record_count": 0,
                    "columns": [],
                    "sample_data": [],
                    "exists": False,
                    "error": str(e)
                })
        
        # Try to find tables with 'tax' or 'deed' in the name
        print("\nTrying to discover other tax/deed related tables...")
        try:
            # This is a workaround to list tables - we'll try common naming patterns
            other_patterns = [
                'public.tax_deed_bidding_items',
                'public.tax_deeds',
                'public.broward_tax_deed_sales',
                'tax_certificate_sales',
                'deed_auctions'
            ]
            
            for pattern in other_patterns:
                try:
                    response = supabase.table(pattern).select("*", count="exact").limit(1).execute()
                    count = response.count if hasattr(response, 'count') else len(response.data)
                    print(f"Found table {pattern}: {count} records")
                    
                    if count > 0:
                        sample_response = supabase.table(pattern).select("*").limit(3).execute()
                        sample_data = sample_response.data
                        columns = list(sample_data[0].keys()) if sample_data else []
                        
                        analysis_results["tables_checked"].append({
                            "table_name": pattern,
                            "record_count": count,
                            "columns": columns,
                            "sample_data": sample_data,
                            "exists": True,
                            "discovered": True
                        })
                        
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"Error discovering tables: {e}")
        
        # Summarize findings
        existing_tables = [t for t in analysis_results["tables_checked"] if t["exists"]]
        total_records = sum(t["record_count"] for t in existing_tables)
        
        print(f"\n=== SUMMARY ===")
        print(f"Tables found: {len(existing_tables)}")
        print(f"Total records across all tables: {total_records}")
        
        for table in existing_tables:
            if table["record_count"] > 0:
                print(f"  - {table['table_name']}: {table['record_count']} records")
                print(f"    Columns: {', '.join(table['columns'][:10])}{'...' if len(table['columns']) > 10 else ''}")
        
        # Save results
        with open('supabase_tax_deed_analysis.json', 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        return analysis_results
        
    except Exception as e:
        error_msg = f"Critical error: {str(e)}"
        print(error_msg)
        analysis_results["errors"].append(error_msg)
        return analysis_results

if __name__ == "__main__":
    results = check_tax_deed_database()
    print("\nAnalysis complete. Results saved to 'supabase_tax_deed_analysis.json'")