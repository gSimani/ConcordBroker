"""
Supabase Database Audit Script
Connects to Supabase and reports data counts for all tables
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio
import pandas as pd

# Load environment variables
load_dotenv()

class SupabaseAuditor:
    def __init__(self):
        """Initialize Supabase client"""
        # Try to load from apps/web/.env first
        web_env_path = os.path.join('apps', 'web', '.env')
        if os.path.exists(web_env_path):
            load_dotenv(web_env_path)
        
        supabase_url = os.getenv('VITE_SUPABASE_URL') or os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
        
        # Hardcode as fallback if env not found
        if not supabase_url:
            supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        if not supabase_key:
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.audit_results = {}
        
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        # Common tables in your ConcordBroker database
        tables = [
            # Core property tables
            'parcels',
            'florida_parcels',
            'properties',
            
            # Sales and history
            'sales_history',
            'florida_sdf_sales',
            'sdf_sales',
            
            # Assessments and taxes
            'tax_assessments',
            'florida_nav_assessments',
            'nav_assessments',
            'tax_certificates',
            'tax_deed_sales',
            
            # Building and permits
            'building_permits',
            'florida_permits',
            
            # Business entities
            'sunbiz_corporations',
            'sunbiz_principals',
            'business_entities',
            
            # Ownership and entities
            'ownership_history',
            'entity_relationships',
            
            # Geographic and mapping
            'florida_mapping_data',
            'broward_daily_index',
            
            # Additional Florida tables
            'florida_nal_counties',
            'florida_nap_counties',
            'florida_nav_roll',
            'florida_revenue',
            
            # Property characteristics
            'property_characteristics',
            'property_use_codes',
            
            # Analytics and aggregates
            'property_analytics',
            'market_trends',
            
            # Pipeline and processing
            'pipeline_runs',
            'data_sync_log',
            
            # Agent tables
            'agent_conversations',
            'agent_tasks',
            'agent_results'
        ]
        
        return tables
    
    def count_table_rows(self, table_name: str) -> Dict[str, Any]:
        """Count rows in a specific table"""
        try:
            # Try to count using a select query with count
            response = self.supabase.table(table_name).select('*', count='exact').execute()
            
            # Get the count from the response
            if hasattr(response, 'count'):
                count = response.count
            else:
                # Fallback: count the returned data
                count = len(response.data) if response.data else 0
            
            # Get sample data (first 5 rows)
            sample_response = self.supabase.table(table_name).select('*').limit(5).execute()
            sample_data = sample_response.data if sample_response.data else []
            
            # Get column information from sample
            columns = list(sample_data[0].keys()) if sample_data else []
            
            return {
                'table_name': table_name,
                'row_count': count,
                'status': 'success',
                'columns': columns,
                'column_count': len(columns),
                'sample_data': sample_data[:2],  # Just 2 samples for report
                'has_data': count > 0
            }
            
        except Exception as e:
            return {
                'table_name': table_name,
                'row_count': 0,
                'status': 'error',
                'error': str(e),
                'columns': [],
                'column_count': 0,
                'sample_data': [],
                'has_data': False
            }
    
    def analyze_table_distribution(self, table_name: str) -> Dict[str, Any]:
        """Analyze data distribution in key tables"""
        analysis = {}
        
        try:
            if table_name in ['parcels', 'florida_parcels']:
                # Analyze by city
                city_response = self.supabase.table(table_name).select('site_city').execute()
                if city_response.data:
                    cities = [row.get('site_city', 'Unknown') for row in city_response.data]
                    city_counts = pd.Series(cities).value_counts().to_dict()
                    analysis['cities'] = dict(list(city_counts.items())[:10])  # Top 10 cities
                
                # Analyze by property type
                type_response = self.supabase.table(table_name).select('property_use_code').limit(1000).execute()
                if type_response.data:
                    types = [row.get('property_use_code', 'Unknown') for row in type_response.data]
                    type_counts = pd.Series(types).value_counts().to_dict()
                    analysis['property_types'] = dict(list(type_counts.items())[:10])
            
            elif table_name == 'sales_history':
                # Get recent sales count by year
                sales_response = self.supabase.table(table_name).select('sale_date').limit(1000).execute()
                if sales_response.data:
                    years = []
                    for row in sales_response.data:
                        if row.get('sale_date'):
                            try:
                                year = row['sale_date'][:4]
                                years.append(year)
                            except:
                                pass
                    if years:
                        year_counts = pd.Series(years).value_counts().to_dict()
                        analysis['sales_by_year'] = dict(sorted(year_counts.items(), reverse=True)[:5])
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def run_audit(self) -> Dict[str, Any]:
        """Run complete audit of all tables"""
        print("Starting Supabase database audit...")
        print("=" * 60)
        
        tables = self.get_all_tables()
        results = {
            'audit_timestamp': datetime.now().isoformat(),
            'total_tables_checked': len(tables),
            'tables_with_data': 0,
            'empty_tables': 0,
            'error_tables': 0,
            'total_rows': 0,
            'table_details': {},
            'summary': {}
        }
        
        # Check each table
        for table in tables:
            print(f"Checking table: {table}...")
            table_info = self.count_table_rows(table)
            
            # Update counters
            if table_info['status'] == 'success':
                if table_info['row_count'] > 0:
                    results['tables_with_data'] += 1
                    results['total_rows'] += table_info['row_count']
                    
                    # Analyze key tables
                    if table in ['parcels', 'florida_parcels', 'sales_history']:
                        table_info['distribution'] = self.analyze_table_distribution(table)
                else:
                    results['empty_tables'] += 1
            else:
                results['error_tables'] += 1
            
            results['table_details'][table] = table_info
            
            # Print progress
            status = "[OK]" if table_info['status'] == 'success' else "[ERROR]"
            count = f"{table_info['row_count']:,}" if table_info['status'] == 'success' else "ERROR"
            print(f"  {status} {table}: {count} rows")
        
        # Create summary
        results['summary'] = {
            'tables_with_most_data': [],
            'empty_tables_list': [],
            'error_tables_list': []
        }
        
        # Sort tables by row count
        sorted_tables = sorted(
            [(name, info['row_count']) for name, info in results['table_details'].items() 
             if info['status'] == 'success' and info['row_count'] > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        results['summary']['tables_with_most_data'] = sorted_tables[:10]
        results['summary']['empty_tables_list'] = [
            name for name, info in results['table_details'].items() 
            if info['status'] == 'success' and info['row_count'] == 0
        ]
        results['summary']['error_tables_list'] = [
            name for name, info in results['table_details'].items() 
            if info['status'] == 'error'
        ]
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted report"""
        report = []
        report.append("=" * 80)
        report.append("SUPABASE DATABASE AUDIT REPORT")
        report.append("=" * 80)
        report.append(f"Audit Date: {results['audit_timestamp']}")
        report.append("")
        
        # Overview
        report.append("OVERVIEW")
        report.append("-" * 40)
        report.append(f"Total Tables Checked: {results['total_tables_checked']}")
        report.append(f"Tables with Data: {results['tables_with_data']}")
        report.append(f"Empty Tables: {results['empty_tables']}")
        report.append(f"Error Tables: {results['error_tables']}")
        report.append(f"Total Rows (all tables): {results['total_rows']:,}")
        report.append("")
        
        # Top tables by row count
        report.append("TOP 10 TABLES BY ROW COUNT")
        report.append("-" * 40)
        for table_name, count in results['summary']['tables_with_most_data']:
            report.append(f"{table_name:30} {count:>15,} rows")
        report.append("")
        
        # Detailed table information
        report.append("DETAILED TABLE INFORMATION")
        report.append("-" * 40)
        
        for table_name, info in results['table_details'].items():
            if info['status'] == 'success' and info['row_count'] > 0:
                report.append(f"\n{table_name}")
                report.append(f"  Rows: {info['row_count']:,}")
                report.append(f"  Columns: {info['column_count']} - {', '.join(info['columns'][:10])}")
                
                if 'distribution' in info and info['distribution']:
                    if 'cities' in info['distribution']:
                        report.append(f"  Top Cities:")
                        for city, count in list(info['distribution']['cities'].items())[:5]:
                            report.append(f"    - {city}: {count:,}")
                    
                    if 'property_types' in info['distribution']:
                        report.append(f"  Top Property Types:")
                        for ptype, count in list(info['distribution']['property_types'].items())[:5]:
                            report.append(f"    - {ptype}: {count:,}")
                    
                    if 'sales_by_year' in info['distribution']:
                        report.append(f"  Sales by Year:")
                        for year, count in list(info['distribution']['sales_by_year'].items())[:5]:
                            report.append(f"    - {year}: {count:,}")
        
        # Empty tables
        if results['summary']['empty_tables_list']:
            report.append("\nEMPTY TABLES")
            report.append("-" * 40)
            for table_name in results['summary']['empty_tables_list']:
                report.append(f"  - {table_name}")
        
        # Error tables
        if results['summary']['error_tables_list']:
            report.append("\nTABLES WITH ERRORS")
            report.append("-" * 40)
            for table_name in results['summary']['error_tables_list']:
                error = results['table_details'][table_name].get('error', 'Unknown error')
                report.append(f"  - {table_name}: {error}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main execution function"""
    try:
        # Create auditor
        auditor = SupabaseAuditor()
        
        # Run audit
        results = auditor.run_audit()
        
        # Generate report
        report = auditor.generate_report(results)
        
        # Print report
        print("\n" + report)
        
        # Save report to file
        report_filename = f"supabase_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_filename}")
        
        # Save detailed JSON results
        json_filename = f"supabase_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Detailed JSON saved to: {json_filename}")
        
        return results
        
    except Exception as e:
        print(f"Error running audit: {e}")
        return None

if __name__ == "__main__":
    main()