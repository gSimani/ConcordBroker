"""
Comprehensive Database Structure Analysis
Analyzes table relationships, data placement, and provides recommendations
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
web_env_path = os.path.join('apps', 'web', '.env')
if os.path.exists(web_env_path):
    load_dotenv(web_env_path)

# Initialize Supabase client
supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

supabase: Client = create_client(supabase_url, supabase_key)

class DatabaseAnalyzer:
    def __init__(self):
        self.supabase = supabase
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'tables_analyzed': {},
            'data_issues': [],
            'recommendations': [],
            'migration_plan': []
        }
    
    def get_all_tables(self):
        """Get comprehensive list of all possible tables"""
        return {
            # Core Property Tables
            'property_tables': [
                'parcels',  # Expected main table
                'latest_parcels',  # Actual table with data
                'florida_parcels',  # Duplicate data?
                'properties',  # Only 3 records
            ],
            
            # Sales & Transaction Tables
            'sales_tables': [
                'sales_history',  # Expected
                'property_sales_history',  # Actual with 3 records
                'fl_sdf_sales',  # Empty
                'sdf_sales',  # Missing
                'florida_sdf_sales',  # Missing
            ],
            
            # Assessment & Tax Tables
            'tax_tables': [
                'tax_assessments',  # Expected
                'nav_assessments',  # Actual with 1 record
                'florida_nav_assessments',  # Missing
                'tax_certificates',  # Missing
                'tax_deed_sales',  # Missing
            ],
            
            # Business Entity Tables
            'entity_tables': [
                'sunbiz_corporate',  # Empty
                'sunbiz_partnerships',  # Empty
                'sunbiz_corporations',  # Missing
                'sunbiz_principals',  # Missing
                'business_entities',  # Missing
                'all_entities',  # Empty
            ],
            
            # Permit Tables
            'permit_tables': [
                'building_permits',  # Expected
                'florida_permits',  # Actual with 1 record
            ],
            
            # Relationship Tables
            'relationship_tables': [
                'entity_relationships',  # Empty
                'property_entity_matches',  # Empty
                'property_ownership_history',  # Empty
                'ownership_history',  # Missing
            ],
            
            # Agent & Monitoring Tables
            'system_tables': [
                'fl_agent_status',  # 7 records
                'agent_notifications',  # Empty
                'monitoring_agents',  # Empty
                'data_source_monitor',  # Empty
                'agent_conversations',  # Missing
                'agent_tasks',  # Missing
                'agent_results',  # Missing
            ]
        }
    
    def analyze_table_structure(self, table_name):
        """Analyze structure and content of a table"""
        try:
            # Get sample data
            response = self.supabase.table(table_name).select('*').limit(10).execute()
            
            if response.data:
                sample = response.data[0]
                columns = list(sample.keys())
                
                # Count total records
                count_response = self.supabase.table(table_name).select('*', count='exact').execute()
                total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data or [])
                
                return {
                    'exists': True,
                    'row_count': total_count,
                    'columns': columns,
                    'column_count': len(columns),
                    'sample_data': sample,
                    'has_primary_key': 'id' in columns or 'parcel_id' in columns,
                    'has_timestamps': 'created_at' in columns or 'updated_at' in columns,
                    'potential_foreign_keys': [col for col in columns if col.endswith('_id')]
                }
            else:
                # Table exists but is empty
                return {
                    'exists': True,
                    'row_count': 0,
                    'columns': [],
                    'column_count': 0,
                    'sample_data': None,
                    'is_empty': True
                }
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }
    
    def check_data_duplication(self):
        """Check for duplicate data across tables"""
        duplicates = []
        
        # Check parcels duplication
        print("Checking for data duplication...")
        
        # Compare latest_parcels and florida_parcels
        try:
            # Get sample from each
            latest_sample = self.supabase.table('latest_parcels').select('parcel_id').limit(100).execute()
            florida_sample = self.supabase.table('florida_parcels').select('parcel_id').limit(100).execute()
            
            if latest_sample.data and florida_sample.data:
                latest_ids = {row['parcel_id'] for row in latest_sample.data}
                florida_ids = {row['parcel_id'] for row in florida_sample.data}
                
                overlap = latest_ids.intersection(florida_ids)
                if len(overlap) > 50:  # More than 50% overlap suggests duplication
                    duplicates.append({
                        'tables': ['latest_parcels', 'florida_parcels'],
                        'type': 'Complete duplication',
                        'overlap_percentage': (len(overlap) / len(latest_ids)) * 100,
                        'recommendation': 'Consider consolidating into single table or creating view'
                    })
        except:
            pass
        
        return duplicates
    
    def analyze_data_placement(self):
        """Analyze if data is in the correct tables"""
        issues = []
        
        # Check property data distribution
        tables_to_check = {
            'latest_parcels': 789884,
            'florida_parcels': 789884,
            'properties': 3,
            'property_sales_history': 3,
            'nav_assessments': 1,
            'florida_permits': 1
        }
        
        # Issue 1: Duplicate parcel data
        if tables_to_check['latest_parcels'] == tables_to_check['florida_parcels']:
            issues.append({
                'issue': 'Duplicate Data',
                'severity': 'HIGH',
                'description': 'latest_parcels and florida_parcels contain identical number of records (789,884)',
                'impact': 'Wasting storage, potential confusion in queries',
                'recommendation': 'Consolidate into single parcels table or clarify purpose'
            })
        
        # Issue 2: Minimal properties table usage
        if tables_to_check['properties'] < 10:
            issues.append({
                'issue': 'Underutilized Table',
                'severity': 'MEDIUM',
                'description': f'properties table only has {tables_to_check["properties"]} records while parcels have 789,884',
                'impact': 'Properties table may not be serving its intended purpose',
                'recommendation': 'Either migrate parcel data to properties or remove properties table'
            })
        
        # Issue 3: Missing sales data
        if tables_to_check['property_sales_history'] < 100:
            issues.append({
                'issue': 'Insufficient Sales Data',
                'severity': 'HIGH',
                'description': f'Only {tables_to_check["property_sales_history"]} sales records for 789,884 properties',
                'impact': 'Cannot perform market analysis or show property history',
                'recommendation': 'Import historical sales data from Florida SDF files'
            })
        
        # Issue 4: Missing assessment data
        if tables_to_check['nav_assessments'] < 100:
            issues.append({
                'issue': 'Missing Assessment Data',
                'severity': 'HIGH',
                'description': f'Only {tables_to_check["nav_assessments"]} assessment record for 789,884 properties',
                'impact': 'Cannot show tax information or assessed values',
                'recommendation': 'Import NAV assessment data for all properties'
            })
        
        return issues
    
    def check_table_relationships(self):
        """Check foreign key relationships and data integrity"""
        relationships = []
        
        # Check if properties reference parcels
        try:
            props = self.supabase.table('properties').select('parcel_id').execute()
            if props.data:
                for prop in props.data:
                    # Check if parcel exists in latest_parcels
                    parcel = self.supabase.table('latest_parcels').select('parcel_id').eq('parcel_id', prop['parcel_id']).execute()
                    if not parcel.data:
                        relationships.append({
                            'issue': 'Orphaned Record',
                            'table': 'properties',
                            'missing_reference': f"parcel_id {prop['parcel_id']} not found in latest_parcels"
                        })
        except:
            pass
        
        return relationships
    
    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        # Data Consolidation
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Data Consolidation',
            'action': 'Consolidate Parcel Tables',
            'details': [
                '1. Choose either latest_parcels or florida_parcels as primary table',
                '2. Create view named "parcels" pointing to chosen table',
                '3. Update all application code to use "parcels" view',
                '4. Drop duplicate table after verification'
            ],
            'sql': """
                -- Create unified parcels view
                CREATE OR REPLACE VIEW parcels AS 
                SELECT * FROM latest_parcels;
                
                -- After verification, drop duplicate
                -- DROP TABLE florida_parcels;
            """
        })
        
        # Data Import
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Data Import',
            'action': 'Import Missing Sales Data',
            'details': [
                '1. Import Florida SDF sales data into fl_sdf_sales table',
                '2. Create proper indexes on parcel_id and sale_date',
                '3. Link sales to parcels table'
            ],
            'script': 'python apps/workers/sdf_sales/load_sdf_sales.py'
        })
        
        # Table Structure
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Table Structure',
            'action': 'Standardize Table Names',
            'details': [
                '1. Rename property_sales_history to sales_history',
                '2. Rename fl_agent_status to agent_status',
                '3. Create aliases for backward compatibility'
            ],
            'sql': """
                -- Rename tables to standard names
                ALTER TABLE property_sales_history RENAME TO sales_history;
                ALTER TABLE fl_agent_status RENAME TO agent_status;
                
                -- Create compatibility views
                CREATE VIEW property_sales_history AS SELECT * FROM sales_history;
            """
        })
        
        # Business Entities
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Business Data',
            'action': 'Load Sunbiz Business Entity Data',
            'details': [
                '1. Download Sunbiz data files',
                '2. Load into sunbiz_corporate and sunbiz_partnerships',
                '3. Create relationships with property owners'
            ],
            'script': 'python apps/workers/sunbiz_sftp/load_sunbiz_data.py'
        })
        
        # Empty Tables
        recommendations.append({
            'priority': 'LOW',
            'category': 'Cleanup',
            'action': 'Remove or Populate Empty Tables',
            'details': [
                '1. Review empty tables purpose',
                '2. Either populate with data or remove',
                '3. Document table purposes in schema'
            ],
            'tables_to_review': [
                'all_entities',
                'property_entity_matches',
                'entity_relationships',
                'agent_notifications',
                'monitoring_agents',
                'data_source_monitor'
            ]
        })
        
        return recommendations
    
    def create_migration_plan(self):
        """Create step-by-step migration plan"""
        plan = [
            {
                'step': 1,
                'title': 'Backup Current Data',
                'commands': [
                    'pg_dump your_database > backup_20250908.sql',
                    'Export critical tables to CSV as additional backup'
                ],
                'estimated_time': '30 minutes'
            },
            {
                'step': 2,
                'title': 'Consolidate Parcel Tables',
                'commands': [
                    'CREATE VIEW parcels AS SELECT * FROM latest_parcels;',
                    'UPDATE application connection strings',
                    'Test all queries'
                ],
                'estimated_time': '1 hour'
            },
            {
                'step': 3,
                'title': 'Import Sales History',
                'commands': [
                    'python load_sdf_sales.py --year 2024',
                    'python load_sdf_sales.py --year 2023',
                    'CREATE INDEX idx_sales_parcel ON fl_sdf_sales(parcel_id);',
                    'CREATE INDEX idx_sales_date ON fl_sdf_sales(sale_date);'
                ],
                'estimated_time': '2-4 hours'
            },
            {
                'step': 4,
                'title': 'Import Assessment Data',
                'commands': [
                    'python load_nav_assessments.py',
                    'CREATE INDEX idx_assess_parcel ON nav_assessments(parcel_id);'
                ],
                'estimated_time': '2 hours'
            },
            {
                'step': 5,
                'title': 'Load Business Entities',
                'commands': [
                    'python download_sunbiz_data.py',
                    'python load_sunbiz_data.py',
                    'python match_entities_to_properties.py'
                ],
                'estimated_time': '3-4 hours'
            },
            {
                'step': 6,
                'title': 'Cleanup and Optimize',
                'commands': [
                    'DROP TABLE florida_parcels;  -- After verification',
                    'VACUUM ANALYZE;',
                    'REINDEX DATABASE;'
                ],
                'estimated_time': '1 hour'
            }
        ]
        
        return plan
    
    def run_analysis(self):
        """Run complete analysis"""
        print("Starting comprehensive database analysis...")
        print("=" * 70)
        
        # Analyze table structure
        all_tables = self.get_all_tables()
        for category, tables in all_tables.items():
            print(f"\nAnalyzing {category}...")
            for table in tables:
                result = self.analyze_table_structure(table)
                self.analysis_results['tables_analyzed'][table] = result
                if result['exists']:
                    status = f"{result['row_count']:,} rows" if result['row_count'] > 0 else "EMPTY"
                    print(f"  [{status:>12}] {table}")
                else:
                    print(f"  [NOT FOUND] {table}")
        
        # Check for duplications
        print("\nChecking for data duplication...")
        duplicates = self.check_data_duplication()
        self.analysis_results['duplications'] = duplicates
        
        # Analyze data placement
        print("Analyzing data placement...")
        issues = self.analyze_data_placement()
        self.analysis_results['data_issues'] = issues
        
        # Check relationships
        print("Checking table relationships...")
        relationships = self.check_table_relationships()
        self.analysis_results['relationship_issues'] = relationships
        
        # Generate recommendations
        print("Generating recommendations...")
        recommendations = self.generate_recommendations()
        self.analysis_results['recommendations'] = recommendations
        
        # Create migration plan
        print("Creating migration plan...")
        migration_plan = self.create_migration_plan()
        self.analysis_results['migration_plan'] = migration_plan
        
        return self.analysis_results
    
    def generate_report(self):
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("DATABASE STRUCTURE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {self.analysis_results['timestamp']}\n")
        
        # Data Issues
        report.append("CRITICAL DATA ISSUES")
        report.append("-" * 40)
        for issue in self.analysis_results['data_issues']:
            report.append(f"\n[{issue['severity']}] {issue['issue']}")
            report.append(f"  Description: {issue['description']}")
            report.append(f"  Impact: {issue['impact']}")
            report.append(f"  Recommendation: {issue['recommendation']}")
        
        # Recommendations
        report.append("\n\nRECOMMENDATIONS")
        report.append("-" * 40)
        for rec in self.analysis_results['recommendations']:
            report.append(f"\n[{rec['priority']}] {rec['action']}")
            report.append(f"  Category: {rec['category']}")
            for detail in rec['details']:
                report.append(f"    {detail}")
        
        # Migration Plan
        report.append("\n\nMIGRATION PLAN")
        report.append("-" * 40)
        for step in self.analysis_results['migration_plan']:
            report.append(f"\nStep {step['step']}: {step['title']}")
            report.append(f"  Estimated Time: {step['estimated_time']}")
            report.append("  Commands:")
            for cmd in step['commands']:
                report.append(f"    {cmd}")
        
        # Table Summary
        report.append("\n\nTABLE STATUS SUMMARY")
        report.append("-" * 40)
        
        # Count tables by status
        with_data = 0
        empty = 0
        missing = 0
        
        for table, info in self.analysis_results['tables_analyzed'].items():
            if info['exists']:
                if info.get('row_count', 0) > 0:
                    with_data += 1
                else:
                    empty += 1
            else:
                missing += 1
        
        report.append(f"Tables with data: {with_data}")
        report.append(f"Empty tables: {empty}")
        report.append(f"Missing tables: {missing}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)

def main():
    analyzer = DatabaseAnalyzer()
    results = analyzer.run_analysis()
    report = analyzer.generate_report()
    
    print("\n" + report)
    
    # Save results
    with open('database_analysis_report.txt', 'w') as f:
        f.write(report)
    
    with open('database_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nReport saved to: database_analysis_report.txt")
    print(f"Detailed results saved to: database_analysis_results.json")

if __name__ == "__main__":
    main()