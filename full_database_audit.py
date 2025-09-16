"""
Full Database Audit - Using Supabase connection to list and analyze all tables
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import httpx

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

class SupabaseDatabaseAuditor:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        
        print(f"Connecting to Supabase: {self.url}")
        self.client = create_client(self.url, self.key)
        
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "database_url": self.url,
            "tables": {},
            "empty_tables": [],
            "large_tables": [],
            "table_categories": {},
            "summary": {}
        }
    
    def get_all_tables(self):
        """Try multiple methods to get all tables"""
        print("\nAttempting to discover all tables...")
        
        # Comprehensive list of potential table names based on the project
        potential_tables = [
            # Core property tables
            'parcels', 'properties', 'florida_parcels', 'broward_parcels',
            'palm_beach_parcels', 'miami_dade_parcels',
            
            # Sales and history
            'sales_history', 'florida_sales', 'sdf_sales', 'property_sales',
            'recent_sales', 'sale_transactions',
            
            # Tax and financial
            'tax_certificates', 'property_tax_info', 'tax_assessments',
            'property_valuations', 'florida_revenue', 'tpp_tangible',
            
            # Permits and improvements
            'building_permits', 'florida_permits', 'property_improvements',
            'permit_history', 'construction_permits',
            
            # Business entities
            'sunbiz_corporations', 'sunbiz_entities', 'business_entities',
            'corporate_owners', 'entity_matching', 'property_entities',
            
            # Assessments
            'property_assessments', 'nav_assessments', 'nap_parcels',
            'nal_parcels', 'florida_nav', 'florida_nav_roll',
            
            # Ownership
            'property_owners', 'owner_history', 'owner_changes',
            
            # Tracking and monitoring
            'tracked_properties', 'user_alerts', 'property_searches',
            'property_profiles', 'watchlist_properties',
            
            # Land use and characteristics
            'land_use_codes', 'property_characteristics', 'zoning_info',
            
            # Index and reference
            'broward_daily_index', 'property_index', 'parcel_index',
            
            # Florida specific data
            'fl_parcels', 'fl_sales', 'fl_permits', 'fl_tax_info',
            'fl_tpp_accounts', 'fl_nav_parcel_summary', 'fl_nav_assessment_detail',
            'fl_sdf_sales', 'fl_data_updates', 'fl_agent_status',
            
            # System tables
            'users', 'profiles', 'settings', 'system_config',
            'audit_logs', 'error_logs', 'data_sync_logs'
        ]
        
        discovered_tables = []
        
        for table_name in potential_tables:
            try:
                # Try to query each table
                result = self.client.table(table_name).select('*', count='exact', head=True).execute()
                discovered_tables.append(table_name)
                print(f"  ✓ Found: {table_name}")
            except Exception as e:
                error_str = str(e)
                if "does not exist" not in error_str.lower() and "not found" not in error_str.lower():
                    # Table might exist but has other issues
                    print(f"  ? Possible table with access issue: {table_name}")
        
        return discovered_tables
    
    def analyze_table(self, table_name):
        """Analyze a single table in detail"""
        analysis = {
            "name": table_name,
            "row_count": 0,
            "columns": [],
            "sample_data": None,
            "is_empty": True,
            "size_category": "Empty",
            "category": self.categorize_table(table_name)
        }
        
        try:
            # Get row count
            result = self.client.table(table_name).select('*', count='exact', head=True).execute()
            analysis["row_count"] = result.count if hasattr(result, 'count') else 0
            analysis["is_empty"] = analysis["row_count"] == 0
            
            # Get sample data and columns if table has data
            if analysis["row_count"] > 0:
                sample_result = self.client.table(table_name).select('*').limit(1).execute()
                if sample_result.data:
                    analysis["columns"] = list(sample_result.data[0].keys())
                    analysis["sample_data"] = sample_result.data[0]
            
            # Categorize by size
            row_count = analysis["row_count"]
            if row_count == 0:
                analysis["size_category"] = "Empty"
            elif row_count < 100:
                analysis["size_category"] = "Tiny (<100)"
            elif row_count < 1000:
                analysis["size_category"] = "Small (<1K)"
            elif row_count < 10000:
                analysis["size_category"] = "Medium (<10K)"
            elif row_count < 100000:
                analysis["size_category"] = "Large (<100K)"
            elif row_count < 1000000:
                analysis["size_category"] = "Very Large (<1M)"
            else:
                analysis["size_category"] = "Massive (>1M)"
            
        except Exception as e:
            analysis["error"] = str(e)[:200]
        
        return analysis
    
    def categorize_table(self, table_name):
        """Categorize table by its name/purpose"""
        name_lower = table_name.lower()
        
        if any(x in name_lower for x in ['parcel', 'propert']):
            return "Properties"
        elif any(x in name_lower for x in ['sale', 'sdf', 'transaction']):
            return "Sales"
        elif any(x in name_lower for x in ['tax', 'assessment', 'valuation', 'revenue']):
            return "Tax/Financial"
        elif any(x in name_lower for x in ['permit', 'building', 'construction']):
            return "Permits"
        elif any(x in name_lower for x in ['sunbiz', 'entity', 'corp', 'business', 'owner']):
            return "Entities/Ownership"
        elif any(x in name_lower for x in ['track', 'watch', 'alert', 'user']):
            return "User/Tracking"
        elif any(x in name_lower for x in ['nav', 'nap', 'nal', 'tpp']):
            return "Florida Revenue"
        elif any(x in name_lower for x in ['index', 'log', 'status', 'config']):
            return "System"
        else:
            return "Other"
    
    def run_comprehensive_audit(self):
        """Run the full audit"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SUPABASE DATABASE AUDIT")
        print("="*80)
        
        # Discover tables
        tables = self.get_all_tables()
        print(f"\nDiscovered {len(tables)} tables in the database")
        
        # Analyze each table
        print("\nAnalyzing table contents...")
        print("-"*80)
        
        total_rows = 0
        
        for table_name in sorted(tables):
            analysis = self.analyze_table(table_name)
            self.audit_results["tables"][table_name] = analysis
            
            # Update categories
            category = analysis["category"]
            if category not in self.audit_results["table_categories"]:
                self.audit_results["table_categories"][category] = []
            self.audit_results["table_categories"][category].append(table_name)
            
            # Track empty and large tables
            if analysis["is_empty"]:
                self.audit_results["empty_tables"].append(table_name)
            
            if analysis["row_count"] > 100000:
                self.audit_results["large_tables"].append({
                    "name": table_name,
                    "rows": analysis["row_count"],
                    "size": analysis["size_category"]
                })
            
            total_rows += analysis["row_count"]
            
            # Print progress
            status = "EMPTY" if analysis["is_empty"] else f"{analysis['row_count']:,} rows"
            print(f"  {table_name:40} {status:20} [{analysis['category']}]")
        
        # Generate summary
        self.audit_results["summary"] = {
            "total_tables": len(tables),
            "empty_tables": len(self.audit_results["empty_tables"]),
            "populated_tables": len(tables) - len(self.audit_results["empty_tables"]),
            "large_tables": len(self.audit_results["large_tables"]),
            "total_rows": total_rows,
            "tables_by_category": {k: len(v) for k, v in self.audit_results["table_categories"].items()}
        }
        
        return self.audit_results
    
    def print_detailed_report(self):
        """Print comprehensive report"""
        print("\n" + "="*80)
        print("AUDIT RESULTS SUMMARY")
        print("="*80)
        
        summary = self.audit_results["summary"]
        
        print(f"\nDATABASE OVERVIEW:")
        print(f"  Total Tables:      {summary['total_tables']}")
        print(f"  Populated Tables:  {summary['populated_tables']}")
        print(f"  Empty Tables:      {summary['empty_tables']}")
        print(f"  Large Tables:      {summary['large_tables']}")
        print(f"  Total Rows:        {summary['total_rows']:,}")
        
        print(f"\nTABLES BY CATEGORY:")
        for category, count in summary['tables_by_category'].items():
            print(f"  {category:20} {count} tables")
        
        # Show populated tables by category
        print("\n" + "="*80)
        print("POPULATED TABLES BY CATEGORY")
        print("="*80)
        
        for category in self.audit_results["table_categories"]:
            tables_in_category = self.audit_results["table_categories"][category]
            populated = [t for t in tables_in_category 
                        if not self.audit_results["tables"][t]["is_empty"]]
            
            if populated:
                print(f"\n{category.upper()}:")
                for table in populated:
                    info = self.audit_results["tables"][table]
                    print(f"  • {table}: {info['row_count']:,} rows ({info['size_category']})")
                    if info.get('columns'):
                        cols_preview = ', '.join(info['columns'][:5])
                        if len(info['columns']) > 5:
                            cols_preview += f" ... +{len(info['columns'])-5} more"
                        print(f"    Columns: {cols_preview}")
        
        # Show large tables
        if self.audit_results["large_tables"]:
            print("\n" + "="*80)
            print("LARGE TABLES REQUIRING OPTIMIZATION")
            print("="*80)
            for table in sorted(self.audit_results["large_tables"], 
                              key=lambda x: x['rows'], reverse=True):
                print(f"  • {table['name']}: {table['rows']:,} rows")
        
        # Show empty tables
        if self.audit_results["empty_tables"]:
            print("\n" + "="*80)
            print("EMPTY TABLES")
            print("="*80)
            
            # Group empty tables by category
            empty_by_category = {}
            for table in self.audit_results["empty_tables"]:
                category = self.audit_results["tables"][table]["category"]
                if category not in empty_by_category:
                    empty_by_category[category] = []
                empty_by_category[category].append(table)
            
            for category, tables in empty_by_category.items():
                print(f"\n{category}:")
                for table in sorted(tables):
                    print(f"  • {table}")
    
    def generate_recommendations(self):
        """Generate specific recommendations based on audit"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS & ACTION ITEMS")
        print("="*80)
        
        # Large table optimizations
        if self.audit_results["large_tables"]:
            print("\n1. LARGE TABLE OPTIMIZATIONS NEEDED:")
            for table in self.audit_results["large_tables"]:
                print(f"\n   {table['name']} ({table['rows']:,} rows):")
                
                if 'parcel' in table['name'].lower() or 'propert' in table['name'].lower():
                    print("   • Partition by county_code or property_type")
                    print("   • Create indexes on: parcel_id, owner_name, address")
                    print("   • Consider materialized view for common queries")
                
                elif 'sale' in table['name'].lower():
                    print("   • Partition by sale_date (monthly or yearly)")
                    print("   • Index on: property_id, sale_date, sale_price")
                    print("   • Archive sales older than 5 years")
                
                elif 'permit' in table['name'].lower():
                    print("   • Partition by permit_date")
                    print("   • Index on: property_id, permit_type, status")
        
        # Empty table analysis
        if self.audit_results["empty_tables"]:
            print("\n2. EMPTY TABLES TO ADDRESS:")
            
            critical_empty = [t for t in self.audit_results["empty_tables"] 
                            if any(x in t for x in ['parcel', 'property', 'sale'])]
            
            if critical_empty:
                print("\n   CRITICAL (Core functionality):")
                for table in critical_empty:
                    print(f"   • {table} - REQUIRES IMMEDIATE DATA LOAD")
            
            secondary_empty = [t for t in self.audit_results["empty_tables"] 
                             if t not in critical_empty]
            
            if secondary_empty:
                print("\n   SECONDARY (Enhanced features):")
                for table in secondary_empty[:5]:  # Show first 5
                    print(f"   • {table}")
                if len(secondary_empty) > 5:
                    print(f"   ... and {len(secondary_empty)-5} more")
        
        print("\n3. DATA PIPELINE PRIORITIES:")
        print("   1. Load core property data (parcels/properties tables)")
        print("   2. Import sales history for market analysis")
        print("   3. Sync business entity data from Sunbiz")
        print("   4. Setup regular data refresh schedules")
        print("   5. Implement data quality checks")
        
        print("\n4. NEXT STEPS:")
        print("   • Review DATABASE_TO_UI_MAPPING.md for UI requirements")
        print("   • Run data loading scripts for empty critical tables")
        print("   • Setup database indexes for large tables")
        print("   • Configure data partitioning strategy")
        print("   • Implement caching layer for frequent queries")
    
    def save_report(self):
        """Save audit results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_file = f"supabase_audit_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        
        # Save text report
        txt_file = f"supabase_audit_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            # Redirect print to file
            import sys
            old_stdout = sys.stdout
            sys.stdout = f
            
            self.print_detailed_report()
            self.generate_recommendations()
            
            sys.stdout = old_stdout
        
        print(f"\n📁 Reports saved:")
        print(f"   • JSON: {json_file}")
        print(f"   • Text: {txt_file}")
        
        return json_file, txt_file

def main():
    try:
        auditor = SupabaseDatabaseAuditor()
        auditor.run_comprehensive_audit()
        auditor.print_detailed_report()
        auditor.generate_recommendations()
        auditor.save_report()
        
    except Exception as e:
        print(f"\n❌ Error during audit: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()