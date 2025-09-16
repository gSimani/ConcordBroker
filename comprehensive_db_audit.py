"""
Comprehensive Database Audit Script
Analyzes all tables, identifies empty tables, and provides data distribution insights
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

# Fix for proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

class DatabaseAuditor:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        
        self.client = create_client(url, key)
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "empty_tables": [],
            "large_tables": [],
            "summary": {}
        }
    
    def get_all_tables(self):
        """Get list of all tables in the database"""
        query = """
        SELECT 
            table_name,
            table_type
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        try:
            # Execute raw SQL query
            result = self.client.rpc('exec_sql', {'query': query}).execute()
            return result.data
        except:
            # Fallback: try to get tables by checking known table names
            known_tables = [
                'parcels', 'florida_parcels', 'properties', 'broward_parcels',
                'sales_history', 'florida_sales', 'tax_certificates', 'building_permits',
                'florida_permits', 'sunbiz_corporations', 'sunbiz_entities',
                'property_owners', 'property_assessments', 'nav_assessments',
                'sdf_sales', 'nal_parcels', 'nap_parcels', 'tpp_tangible',
                'property_tax_info', 'property_characteristics', 'land_use_codes',
                'florida_revenue', 'florida_nav', 'florida_nav_roll',
                'broward_daily_index', 'property_valuations', 'property_improvements',
                'tracked_properties', 'user_alerts', 'property_searches',
                'entity_matching', 'property_entities', 'property_profiles'
            ]
            
            existing_tables = []
            for table in known_tables:
                try:
                    # Try to count rows - if successful, table exists
                    result = self.client.table(table).select('*', count='exact', head=True).execute()
                    existing_tables.append({'table_name': table})
                except:
                    pass
            
            return existing_tables
    
    def analyze_table(self, table_name):
        """Analyze a single table for row count and sample data"""
        table_info = {
            "name": table_name,
            "row_count": 0,
            "columns": [],
            "sample_data": None,
            "is_empty": True,
            "size_estimate": None
        }
        
        try:
            # Get row count
            count_result = self.client.table(table_name).select('*', count='exact', head=True).execute()
            table_info["row_count"] = count_result.count if hasattr(count_result, 'count') else 0
            table_info["is_empty"] = table_info["row_count"] == 0
            
            # Get column information
            if table_info["row_count"] > 0:
                # Get sample data to understand columns
                sample = self.client.table(table_name).select('*').limit(1).execute()
                if sample.data and len(sample.data) > 0:
                    table_info["columns"] = list(sample.data[0].keys())
                    table_info["sample_data"] = sample.data[0]
            
            # Estimate table size
            if table_info["row_count"] > 1000000:
                table_info["size_estimate"] = "Very Large (>1M rows)"
            elif table_info["row_count"] > 100000:
                table_info["size_estimate"] = "Large (>100K rows)"
            elif table_info["row_count"] > 10000:
                table_info["size_estimate"] = "Medium (>10K rows)"
            elif table_info["row_count"] > 0:
                table_info["size_estimate"] = "Small"
            else:
                table_info["size_estimate"] = "Empty"
                
        except Exception as e:
            table_info["error"] = str(e)
        
        return table_info
    
    def run_audit(self):
        """Run complete database audit"""
        print("Starting comprehensive database audit...")
        print("=" * 60)
        
        # Get all tables
        print("\n1. Fetching all tables...")
        tables = self.get_all_tables()
        print(f"   Found {len(tables)} tables")
        
        # Analyze each table
        print("\n2. Analyzing each table...")
        total_rows = 0
        
        for table in tables:
            table_name = table['table_name']
            print(f"   Analyzing: {table_name}...", end=" ")
            
            table_info = self.analyze_table(table_name)
            self.audit_results["tables"][table_name] = table_info
            
            # Track empty and large tables
            if table_info["is_empty"]:
                self.audit_results["empty_tables"].append(table_name)
                print(f"EMPTY")
            else:
                row_count = table_info["row_count"]
                total_rows += row_count
                print(f"{row_count:,} rows")
                
                if row_count > 100000:
                    self.audit_results["large_tables"].append({
                        "name": table_name,
                        "rows": row_count,
                        "size": table_info["size_estimate"]
                    })
        
        # Generate summary
        self.audit_results["summary"] = {
            "total_tables": len(tables),
            "empty_tables_count": len(self.audit_results["empty_tables"]),
            "populated_tables_count": len(tables) - len(self.audit_results["empty_tables"]),
            "large_tables_count": len(self.audit_results["large_tables"]),
            "total_rows_all_tables": total_rows
        }
        
        return self.audit_results
    
    def print_report(self):
        """Print formatted audit report"""
        print("\n" + "=" * 60)
        print("DATABASE AUDIT REPORT")
        print("=" * 60)
        
        summary = self.audit_results["summary"]
        print(f"\nSUMMARY:")
        print(f"  Total Tables: {summary['total_tables']}")
        print(f"  Populated Tables: {summary['populated_tables_count']}")
        print(f"  Empty Tables: {summary['empty_tables_count']}")
        print(f"  Large Tables (>100K rows): {summary['large_tables_count']}")
        print(f"  Total Rows (all tables): {summary['total_rows_all_tables']:,}")
        
        if self.audit_results["large_tables"]:
            print(f"\nLARGE TABLES:")
            for table in sorted(self.audit_results["large_tables"], key=lambda x: x['rows'], reverse=True):
                print(f"  - {table['name']}: {table['rows']:,} rows ({table['size']})")
        
        if self.audit_results["empty_tables"]:
            print(f"\nEMPTY TABLES ({len(self.audit_results['empty_tables'])}):")
            for table in sorted(self.audit_results["empty_tables"]):
                print(f"  - {table}")
        
        print("\nPOPULATED TABLES:")
        populated_tables = [(name, info) for name, info in self.audit_results["tables"].items() 
                           if not info.get("is_empty", True) and "error" not in info]
        
        for name, info in sorted(populated_tables, key=lambda x: x[1]['row_count'], reverse=True):
            print(f"  - {name}: {info['row_count']:,} rows")
            if info['columns']:
                print(f"    Columns ({len(info['columns'])}): {', '.join(info['columns'][:5])}", end="")
                if len(info['columns']) > 5:
                    print(f"... (+{len(info['columns'])-5} more)")
                else:
                    print()
    
    def save_results(self, filename=None):
        """Save audit results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database_audit_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        print(f"\nAudit results saved to: {filename}")
        return filename

def main():
    try:
        auditor = DatabaseAuditor()
        auditor.run_audit()
        auditor.print_report()
        auditor.save_results()
        
        # Provide recommendations
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)
        
        if auditor.audit_results["large_tables"]:
            print("\n1. LARGE TABLE OPTIMIZATION:")
            print("   Consider implementing:")
            print("   - Table partitioning for tables >1M rows")
            print("   - Proper indexing on frequently queried columns")
            print("   - Archival strategy for historical data")
            print("   - Consider using materialized views for complex queries")
        
        if auditor.audit_results["empty_tables"]:
            print("\n2. EMPTY TABLES:")
            print("   These tables may be:")
            print("   - Awaiting data migration")
            print("   - Part of future features")
            print("   - Candidates for removal if obsolete")
            print("   - Staging tables for ETL processes")
        
        print("\n3. NEXT STEPS:")
        print("   - Review the data mapping document (DATABASE_TO_UI_MAPPING.md)")
        print("   - Implement data partitioning for large tables")
        print("   - Populate empty tables with appropriate data")
        print("   - Optimize queries for large datasets")
        
    except Exception as e:
        print(f"Error during audit: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()