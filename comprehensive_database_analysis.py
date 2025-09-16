"""
Comprehensive Database and NAL File Analysis
Compare Supabase live data with NAL Broward County file
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

class DatabaseAnalyzer:
    def __init__(self):
        self.supabase_analysis = {}
        self.nal_analysis = {}
        self.comparison_report = {}
        
    def analyze_supabase_database(self):
        """Comprehensive analysis of all Supabase tables and fields"""
        print("=" * 80)
        print("ANALYZING LIVE SUPABASE DATABASE")
        print("=" * 80)
        
        # Get all tables from florida_parcels (main table)
        print("\n1. ANALYZING FLORIDA_PARCELS TABLE:")
        try:
            response = supabase.table('florida_parcels').select('*').limit(1).execute()
            if response.data and len(response.data) > 0:
                sample_record = response.data[0]
                florida_parcels_fields = list(sample_record.keys())
                
                print(f"   Total fields: {len(florida_parcels_fields)}")
                self.supabase_analysis['florida_parcels'] = {
                    'total_fields': len(florida_parcels_fields),
                    'fields': florida_parcels_fields,
                    'sample_data': sample_record
                }
                
                # Categorize fields
                categories = self._categorize_fields(florida_parcels_fields, sample_record)
                self.supabase_analysis['florida_parcels']['categories'] = categories
                
                print("   Field categories:")
                for cat, fields in categories.items():
                    print(f"     - {cat}: {len(fields)} fields")
                    
            else:
                print("   No data found in florida_parcels table")
        except Exception as e:
            print(f"   Error accessing florida_parcels: {e}")
        
        # Check other tables
        other_tables = [
            'tax_certificates', 'property_sales_history', 'sunbiz_entities',
            'nav_assessments', 'building_permits', 'sunbiz_corporate', 'sunbiz_fictitious'
        ]
        
        print(f"\n2. ANALYZING OTHER TABLES:")
        for table_name in other_tables:
            try:
                response = supabase.table(table_name).select('*').limit(1).execute()
                if response.data and len(response.data) > 0:
                    fields = list(response.data[0].keys())
                    print(f"   {table_name}: {len(fields)} fields")
                    self.supabase_analysis[table_name] = {
                        'total_fields': len(fields),
                        'fields': fields,
                        'sample_data': response.data[0]
                    }
                else:
                    print(f"   {table_name}: Empty or no data")
                    self.supabase_analysis[table_name] = {'total_fields': 0, 'fields': [], 'status': 'empty'}
            except Exception as e:
                print(f"   {table_name}: Error - {e}")
                self.supabase_analysis[table_name] = {'total_fields': 0, 'fields': [], 'error': str(e)}
        
        return self.supabase_analysis
    
    def analyze_nal_file(self, file_path):
        """Comprehensive analysis of NAL Broward County file"""
        print("\n" + "=" * 80)
        print("ANALYZING NAL BROWARD COUNTY FILE")
        print("=" * 80)
        print(f"File: {file_path}")
        
        try:
            if not os.path.exists(file_path):
                print(f"ERROR: File not found: {file_path}")
                return None
                
            # Read the CSV file
            df = pd.read_csv(file_path, low_memory=False, nrows=1000)  # Sample first 1000 rows
            
            print(f"\nFile Statistics:")
            print(f"   Total columns: {len(df.columns)}")
            print(f"   Sample rows analyzed: {len(df)}")
            
            # Analyze each column
            column_analysis = {}
            for col in df.columns:
                non_null_count = df[col].notna().sum()
                unique_count = df[col].nunique()
                
                # Sample values (non-null)
                sample_values = df[col].dropna().head(5).tolist()
                
                column_analysis[col] = {
                    'non_null_count': int(non_null_count),
                    'unique_count': int(unique_count),
                    'null_percentage': round((len(df) - non_null_count) / len(df) * 100, 2),
                    'sample_values': [str(v) for v in sample_values],
                    'data_type': str(df[col].dtype)
                }
            
            # Categorize NAL fields
            nal_categories = self._categorize_nal_fields(list(df.columns), df)
            
            print(f"\nNAL Field Categories:")
            for cat, fields in nal_categories.items():
                print(f"   - {cat}: {len(fields)} fields")
                
            # Store analysis
            self.nal_analysis = {
                'total_fields': len(df.columns),
                'fields': list(df.columns),
                'categories': nal_categories,
                'column_details': column_analysis,
                'sample_record': df.iloc[0].to_dict() if len(df) > 0 else {}
            }
            
            return self.nal_analysis
            
        except Exception as e:
            print(f"ERROR analyzing NAL file: {e}")
            return None
    
    def _categorize_fields(self, fields, sample_data):
        """Categorize Supabase database fields"""
        categories = {
            'identification': [],
            'location': [],
            'ownership': [],
            'property_details': [],
            'valuation': [],
            'tax_info': [],
            'dates': [],
            'system_fields': [],
            'other': []
        }
        
        for field in fields:
            field_lower = field.lower()
            value = sample_data.get(field)
            
            if any(term in field_lower for term in ['id', 'parcel', 'account', 'number']):
                categories['identification'].append(field)
            elif any(term in field_lower for term in ['addr', 'address', 'city', 'state', 'zip', 'location', 'lat', 'lon', 'coord']):
                categories['location'].append(field)
            elif any(term in field_lower for term in ['owner', 'name']):
                categories['ownership'].append(field)
            elif any(term in field_lower for term in ['use', 'type', 'bed', 'bath', 'sqft', 'acre', 'year_built', 'stories']):
                categories['property_details'].append(field)
            elif any(term in field_lower for term in ['value', 'price', 'amount', 'assessment']):
                categories['valuation'].append(field)
            elif any(term in field_lower for term in ['tax', 'mill', 'exempt']):
                categories['tax_info'].append(field)
            elif any(term in field_lower for term in ['date', 'created', 'updated', 'import']):
                categories['dates'].append(field)
            elif any(term in field_lower for term in ['import', 'source', 'year']):
                categories['system_fields'].append(field)
            else:
                categories['other'].append(field)
                
        return categories
    
    def _categorize_nal_fields(self, fields, df):
        """Categorize NAL file fields based on content and naming patterns"""
        categories = {
            'identification': [],
            'location': [],
            'ownership': [],
            'property_details': [],
            'valuation': [],
            'tax_info': [],
            'legal_description': [],
            'physical_characteristics': [],
            'zoning_planning': [],
            'dates': [],
            'codes': [],
            'other': []
        }
        
        for field in fields:
            field_lower = field.lower()
            
            # Analyze sample data to better categorize
            sample_values = df[field].dropna().head(3).astype(str).tolist()
            
            if any(term in field_lower for term in ['parcel', 'account', 'number', 'id', 'folio']):
                categories['identification'].append(field)
            elif any(term in field_lower for term in ['addr', 'address', 'street', 'city', 'zip']):
                categories['location'].append(field)
            elif any(term in field_lower for term in ['owner', 'name', 'mail']):
                categories['ownership'].append(field)
            elif any(term in field_lower for term in ['use', 'code', 'class', 'type']):
                categories['property_details'].append(field)
            elif any(term in field_lower for term in ['value', 'assess', 'just', 'market', 'land', 'build']):
                categories['valuation'].append(field)
            elif any(term in field_lower for term in ['tax', 'exempt', 'homestead']):
                categories['tax_info'].append(field)
            elif any(term in field_lower for term in ['legal', 'desc', 'subdivision', 'plat', 'lot', 'block']):
                categories['legal_description'].append(field)
            elif any(term in field_lower for term in ['sqft', 'acres', 'bed', 'bath', 'year', 'built', 'stories', 'units']):
                categories['physical_characteristics'].append(field)
            elif any(term in field_lower for term in ['zone', 'district', 'plan']):
                categories['zoning_planning'].append(field)
            elif any(term in field_lower for term in ['date', 'year']) and not any(term in field_lower for term in ['built']):
                categories['dates'].append(field)
            elif len(sample_values) > 0 and all(len(str(v)) <= 5 and str(v).isdigit() for v in sample_values if v):
                categories['codes'].append(field)
            else:
                categories['other'].append(field)
                
        return categories
    
    def generate_comparison_report(self):
        """Generate comprehensive comparison report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE COMPARISON REPORT")
        print("=" * 80)
        
        # Overall statistics
        supabase_total = self.supabase_analysis.get('florida_parcels', {}).get('total_fields', 0)
        nal_total = self.nal_analysis.get('total_fields', 0)
        
        print(f"\nOVERALL FIELD COUNT:")
        print(f"   Supabase florida_parcels: {supabase_total} fields")
        print(f"   NAL Broward County file: {nal_total} fields")
        
        if nal_total > supabase_total:
            difference = nal_total - supabase_total
            print(f"   🏆 NAL file has {difference} MORE fields ({difference/supabase_total*100:.1f}% more)")
        elif supabase_total > nal_total:
            difference = supabase_total - nal_total
            print(f"   🏆 Supabase has {difference} MORE fields ({difference/nal_total*100:.1f}% more)")
        else:
            print(f"   📊 Both have equal number of fields")
        
        # Category comparison
        print(f"\nCATEGORY-BY-CATEGORY COMPARISON:")
        supabase_cats = self.supabase_analysis.get('florida_parcels', {}).get('categories', {})
        nal_cats = self.nal_analysis.get('categories', {})
        
        all_categories = set(supabase_cats.keys()) | set(nal_cats.keys())
        
        for category in sorted(all_categories):
            sb_count = len(supabase_cats.get(category, []))
            nal_count = len(nal_cats.get(category, []))
            
            if nal_count > sb_count:
                winner = "NAL +"
                diff = nal_count - sb_count
            elif sb_count > nal_count:
                winner = "Supabase +"
                diff = sb_count - nal_count
            else:
                winner = "Tie"
                diff = 0
                
            print(f"   {category.title():20} | Supabase: {sb_count:2d} | NAL: {nal_count:2d} | {winner} {diff}")
        
        # Field mapping analysis
        print(f"\nFIELD MAPPING ANALYSIS:")
        supabase_fields = set(self.supabase_analysis.get('florida_parcels', {}).get('fields', []))
        nal_fields = set(self.nal_analysis.get('fields', []))
        
        common_fields = supabase_fields & nal_fields
        supabase_only = supabase_fields - nal_fields
        nal_only = nal_fields - supabase_fields
        
        print(f"   Common fields: {len(common_fields)}")
        print(f"   Supabase only: {len(supabase_only)}")
        print(f"   NAL only: {len(nal_only)}")
        
        # Show significant differences
        print(f"\nSIGNIFICANT DIFFERENCES:")
        
        if nal_only:
            print(f"\n   NAL-EXCLUSIVE FIELDS ({len(nal_only)} fields):")
            for field in sorted(list(nal_only)[:10]):  # Show first 10
                category = self._find_field_category(field, nal_cats)
                print(f"     - {field} ({category})")
            if len(nal_only) > 10:
                print(f"     ... and {len(nal_only) - 10} more")
        
        if supabase_only:
            print(f"\n   SUPABASE-EXCLUSIVE FIELDS ({len(supabase_only)} fields):")
            for field in sorted(list(supabase_only)[:10]):  # Show first 10
                category = self._find_field_category(field, supabase_cats)
                print(f"     - {field} ({category})")
            if len(supabase_only) > 10:
                print(f"     ... and {len(supabase_only) - 10} more")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        if nal_total > supabase_total:
            print(f"   📊 NAL file contains significantly more property data")
            print(f"   💡 Consider importing NAL data to enrich Supabase database")
            print(f"   🔄 Update data pipeline to include all NAL fields")
        
        # Data quality assessment
        self._assess_data_quality()
        
        return {
            'supabase_total': supabase_total,
            'nal_total': nal_total,
            'winner': 'NAL' if nal_total > supabase_total else 'Supabase' if supabase_total > nal_total else 'Tie',
            'difference': abs(nal_total - supabase_total),
            'common_fields': len(common_fields),
            'unique_to_nal': len(nal_only),
            'unique_to_supabase': len(supabase_only)
        }
    
    def _find_field_category(self, field, categories):
        """Find which category a field belongs to"""
        for cat, fields in categories.items():
            if field in fields:
                return cat
        return 'unknown'
    
    def _assess_data_quality(self):
        """Assess data quality and completeness"""
        print(f"\nDATA QUALITY ASSESSMENT:")
        
        # Check Supabase data completeness
        if 'florida_parcels' in self.supabase_analysis:
            sample_data = self.supabase_analysis['florida_parcels'].get('sample_data', {})
            filled_fields = sum(1 for v in sample_data.values() if v is not None and v != '')
            total_fields = len(sample_data)
            
            print(f"   Supabase completeness: {filled_fields}/{total_fields} fields ({filled_fields/total_fields*100:.1f}%)")
        
        # Check NAL data completeness
        if 'column_details' in self.nal_analysis:
            avg_completeness = sum(
                100 - details['null_percentage'] 
                for details in self.nal_analysis['column_details'].values()
            ) / len(self.nal_analysis['column_details'])
            
            print(f"   NAL completeness: Average {avg_completeness:.1f}% across all fields")
        
        print(f"\n   🎯 WINNER: The dataset with more comprehensive data will better serve property analysis")

def main():
    analyzer = DatabaseAnalyzer()
    
    # Analyze Supabase database
    supabase_analysis = analyzer.analyze_supabase_database()
    
    # Analyze NAL file
    nal_file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAL16P202501.csv"
    nal_analysis = analyzer.analyze_nal_file(nal_file_path)
    
    if nal_analysis:
        # Generate comparison report
        comparison = analyzer.generate_comparison_report()
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'supabase_analysis': supabase_analysis,
            'nal_analysis': nal_analysis,
            'comparison': comparison
        }
        
        with open('database_nal_comparison_report.json', 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: database_nal_comparison_report.json")
    else:
        print("❌ Could not complete analysis due to NAL file issues")

if __name__ == "__main__":
    main()