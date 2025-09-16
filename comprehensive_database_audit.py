"""
Comprehensive Supabase Database Audit
Checks all tables, counts records, and identifies missing data
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('apps/web/.env')

class DatabaseAuditor:
    def __init__(self):
        self.supabase_url = os.getenv("VITE_SUPABASE_URL")
        self.supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
        self.supabase = None
        self.audit_results = {}
        
        if self.supabase_url and self.supabase_key:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print(f"[OK] Connected to Supabase")
        else:
            print("[ERROR] Failed to connect to Supabase - missing credentials")
    
    def audit_all_tables(self) -> Dict:
        """
        Audit all known tables in Supabase
        """
        print("\n" + "="*60)
        print("COMPREHENSIVE DATABASE AUDIT")
        print("="*60)
        
        # Define all expected tables and their key fields
        tables_to_audit = {
            'florida_parcels': {
                'key_fields': ['parcel_id', 'phy_addr1', 'owner_name', 'just_value'],
                'description': 'Main property data table',
                'expected_min_records': 100000
            },
            'property_sales_history': {
                'key_fields': ['parcel_id', 'sale_date', 'sale_price'],
                'description': 'Historical sales transactions',
                'expected_min_records': 50000
            },
            'nav_assessments': {
                'key_fields': ['parcel_id', 'assessment_year', 'assessment_amount'],
                'description': 'Non-ad valorem assessments',
                'expected_min_records': 10000
            },
            'sunbiz_corporate': {
                'key_fields': ['corp_number', 'corp_name', 'principal_addr'],
                'description': 'Florida business entities',
                'expected_min_records': 100000
            },
            'florida_permits': {
                'key_fields': ['permit_number', 'parcel_id', 'permit_type'],
                'description': 'Building permits data',
                'expected_min_records': 50000
            },
            'broward_daily_index': {
                'key_fields': ['doc_number', 'recording_date'],
                'description': 'Daily recorded documents',
                'expected_min_records': 10000
            },
            'tax_certificates': {
                'key_fields': ['certificate_number', 'parcel_id', 'tax_year'],
                'description': 'Tax certificate sales',
                'expected_min_records': 5000
            },
            'tax_deed_sales': {
                'key_fields': ['case_number', 'parcel_id', 'sale_date'],
                'description': 'Tax deed sale records',
                'expected_min_records': 1000
            },
            'properties': {
                'key_fields': ['id', 'parcel_id', 'address'],
                'description': 'Legacy properties table',
                'expected_min_records': 0
            }
        }
        
        for table_name, table_info in tables_to_audit.items():
            print(f"\n[AUDIT] Auditing table: {table_name}")
            print(f"   Description: {table_info['description']}")
            
            table_audit = self.audit_table(table_name, table_info['key_fields'])
            table_audit['expected_min_records'] = table_info['expected_min_records']
            table_audit['description'] = table_info['description']
            
            # Check if table meets minimum expectations
            if table_audit['exists']:
                if table_audit['record_count'] < table_info['expected_min_records']:
                    table_audit['status'] = 'NEEDS_DATA'
                    print(f"   [WARNING] Table has {table_audit['record_count']} records, expected at least {table_info['expected_min_records']}")
                else:
                    table_audit['status'] = 'OK'
                    print(f"   [OK] Table has {table_audit['record_count']} records")
            else:
                table_audit['status'] = 'MISSING'
                print(f"   [MISSING] Table does not exist or is not accessible")
            
            self.audit_results[table_name] = table_audit
        
        return self.audit_results
    
    def audit_table(self, table_name: str, key_fields: List[str]) -> Dict:
        """
        Audit a single table
        """
        result = {
            'exists': False,
            'record_count': 0,
            'sample_data': None,
            'columns': [],
            'null_counts': {},
            'has_recent_data': False
        }
        
        if not self.supabase:
            return result
        
        try:
            # Check if table exists and get count
            response = self.supabase.table(table_name).select('*', count='exact').limit(1).execute()
            
            if response:
                result['exists'] = True
                result['record_count'] = response.count if hasattr(response, 'count') else len(response.data)
                
                # Get sample data
                if response.data and len(response.data) > 0:
                    result['sample_data'] = response.data[0]
                    result['columns'] = list(response.data[0].keys())
                    
                    # Check for null values in key fields
                    sample_response = self.supabase.table(table_name).select(','.join(key_fields)).limit(100).execute()
                    if sample_response.data:
                        for field in key_fields:
                            null_count = sum(1 for row in sample_response.data if row.get(field) is None or row.get(field) == '')
                            result['null_counts'][field] = null_count
                    
                    # Check for recent data (if date fields exist)
                    date_fields = ['created_at', 'updated_at', 'sale_date', 'recording_date']
                    for date_field in date_fields:
                        if date_field in result['columns']:
                            try:
                                recent = self.supabase.table(table_name).select(date_field).order(date_field, desc=True).limit(1).execute()
                                if recent.data and recent.data[0].get(date_field):
                                    date_str = recent.data[0][date_field]
                                    # Check if date is within last 30 days
                                    from datetime import datetime, timedelta
                                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    if datetime.now(date_obj.tzinfo) - date_obj < timedelta(days=30):
                                        result['has_recent_data'] = True
                                break
                            except:
                                pass
        
        except Exception as e:
            print(f"   Error auditing table: {str(e)[:100]}")
            result['error'] = str(e)
        
        return result
    
    def check_data_sources(self) -> Dict:
        """
        Check which data sources need to be downloaded
        """
        print("\n" + "="*60)
        print("DATA SOURCE ANALYSIS")
        print("="*60)
        
        data_sources = {
            'NAL (Name & Address)': {
                'tables': ['florida_parcels'],
                'url_pattern': 'https://floridarevenue.com/property/Pages/DataPortal_NAL.aspx',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['owner_name', 'owner_addr1', 'phy_addr1']
            },
            'SDF (Sales Data)': {
                'tables': ['property_sales_history'],
                'url_pattern': 'https://floridarevenue.com/property/Pages/DataPortal_SDF.aspx',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['sale_price', 'sale_date', 'buyer_name']
            },
            'NAP (Property Characteristics)': {
                'tables': ['florida_parcels'],
                'url_pattern': 'https://floridarevenue.com/property/Pages/DataPortal_NAP.aspx',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['total_living_area', 'year_built', 'bedrooms', 'bathrooms']
            },
            'TPP (Tangible Personal Property)': {
                'tables': ['florida_parcels'],
                'url_pattern': 'https://floridarevenue.com/property/Pages/DataPortal_TPP.aspx',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['tpp_value', 'business_name']
            },
            'NAV (Non-Ad Valorem)': {
                'tables': ['nav_assessments'],
                'url_pattern': 'https://floridarevenue.com/property/Pages/DataPortal_NAV.aspx',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['assessment_amount', 'assessment_type']
            },
            'Sunbiz Corporate': {
                'tables': ['sunbiz_corporate'],
                'url_pattern': 'http://www.sunbiz.org/data-download.html',
                'counties': ['Statewide'],
                'required_fields': ['corp_number', 'corp_name', 'status']
            },
            'Building Permits': {
                'tables': ['florida_permits'],
                'url_pattern': 'County-specific permit portals',
                'counties': ['Broward', 'Miami-Dade', 'Palm Beach'],
                'required_fields': ['permit_number', 'permit_type', 'issue_date']
            }
        }
        
        recommendations = []
        
        for source_name, source_info in data_sources.items():
            print(f"\n[SOURCE] {source_name}")
            needs_download = False
            
            for table_name in source_info['tables']:
                if table_name in self.audit_results:
                    table_audit = self.audit_results[table_name]
                    
                    if table_audit['status'] == 'MISSING':
                        print(f"   [REQUIRED] Table {table_name} is missing - DOWNLOAD REQUIRED")
                        needs_download = True
                    elif table_audit['status'] == 'NEEDS_DATA':
                        print(f"   [RECOMMENDED] Table {table_name} has insufficient data - DOWNLOAD RECOMMENDED")
                        needs_download = True
                    else:
                        # Check if required fields have data
                        missing_fields = []
                        if table_audit['columns']:
                            for field in source_info['required_fields']:
                                if field not in table_audit['columns']:
                                    missing_fields.append(field)
                                elif field in table_audit['null_counts'] and table_audit['null_counts'][field] > 50:
                                    missing_fields.append(f"{field} (high nulls)")
                        
                        if missing_fields:
                            print(f"   [INCOMPLETE] Missing/incomplete fields: {', '.join(missing_fields)}")
                            needs_download = True
                        else:
                            print(f"   [COMPLETE] Data appears complete in {table_name}")
            
            if needs_download:
                recommendations.append({
                    'source': source_name,
                    'url': source_info['url_pattern'],
                    'counties': source_info['counties'],
                    'priority': 'HIGH' if 'MISSING' in str(self.audit_results) else 'MEDIUM'
                })
        
        return {
            'data_sources': data_sources,
            'recommendations': recommendations
        }
    
    def generate_report(self) -> None:
        """
        Generate comprehensive audit report
        """
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_url': self.supabase_url,
            'tables_audited': len(self.audit_results),
            'total_records': sum(t['record_count'] for t in self.audit_results.values()),
            'table_details': self.audit_results,
            'data_source_analysis': self.check_data_sources(),
            'summary': {
                'tables_ok': 0,
                'tables_need_data': 0,
                'tables_missing': 0,
                'total_records': 0
            }
        }
        
        # Calculate summary
        for table_name, audit in self.audit_results.items():
            if audit['status'] == 'OK':
                report['summary']['tables_ok'] += 1
            elif audit['status'] == 'NEEDS_DATA':
                report['summary']['tables_need_data'] += 1
            elif audit['status'] == 'MISSING':
                report['summary']['tables_missing'] += 1
            report['summary']['total_records'] += audit['record_count']
        
        # Print summary
        print(f"\n[SUMMARY]:")
        print(f"   Tables OK: {report['summary']['tables_ok']}")
        print(f"   Tables needing data: {report['summary']['tables_need_data']}")
        print(f"   Tables missing: {report['summary']['tables_missing']}")
        print(f"   Total records: {report['summary']['total_records']:,}")
        
        # Save report
        report_file = f"database_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[REPORT] Full report saved to: {report_file}")
        
        # Print recommendations
        if report['data_source_analysis']['recommendations']:
            print("\n[DOWNLOADS NEEDED]:")
            for rec in report['data_source_analysis']['recommendations']:
                print(f"   • {rec['source']} ({rec['priority']} priority)")
                print(f"     Counties: {', '.join(rec['counties'])}")
        
        return report


def main():
    """
    Run the comprehensive database audit
    """
    auditor = DatabaseAuditor()
    
    # Run audit
    auditor.audit_all_tables()
    
    # Generate report
    report = auditor.generate_report()
    
    return report


if __name__ == "__main__":
    main()