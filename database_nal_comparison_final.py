"""
Final Database vs NAL Comparison Report
Simple analysis without Unicode issues
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

def analyze_supabase():
    """Analyze Supabase database structure"""
    print("ANALYZING SUPABASE DATABASE")
    print("=" * 50)
    
    # Get florida_parcels structure
    try:
        response = supabase.table('florida_parcels').select('*').limit(1).execute()
        if response.data:
            supabase_fields = list(response.data[0].keys())
            print(f"Florida_parcels table: {len(supabase_fields)} fields")
            return supabase_fields
        else:
            print("No data in florida_parcels")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_nal_file():
    """Analyze NAL file structure"""
    print("\nANALYZING NAL FILE")
    print("=" * 50)
    
    file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAL16P202501.csv"
    
    try:
        df = pd.read_csv(file_path, nrows=100)  # Just sample
        nal_fields = list(df.columns)
        print(f"NAL file: {len(nal_fields)} fields")
        
        # Show sample of field names
        print(f"\nSample NAL fields:")
        for field in nal_fields[:20]:
            print(f"  - {field}")
        if len(nal_fields) > 20:
            print(f"  ... and {len(nal_fields) - 20} more fields")
            
        return nal_fields
    except Exception as e:
        print(f"Error reading NAL file: {e}")
        return []

def compare_datasets(supabase_fields, nal_fields):
    """Compare the two datasets"""
    print("\nCOMPARISON REPORT")
    print("=" * 50)
    
    sb_count = len(supabase_fields)
    nal_count = len(nal_fields)
    
    print(f"Supabase florida_parcels: {sb_count} fields")
    print(f"NAL Broward County file: {nal_count} fields")
    
    if nal_count > sb_count:
        diff = nal_count - sb_count
        percentage = (diff / sb_count) * 100
        print(f"\nWINNER: NAL file")
        print(f"NAL has {diff} MORE fields ({percentage:.1f}% more data)")
    else:
        print(f"Supabase has more or equal fields")
    
    # Field overlap analysis
    sb_set = set(supabase_fields)
    nal_set = set(nal_fields)
    
    common = sb_set & nal_set
    sb_only = sb_set - nal_set
    nal_only = nal_set - sb_set
    
    print(f"\nFIELD OVERLAP:")
    print(f"Common fields: {len(common)}")
    print(f"Supabase only: {len(sb_only)}")
    print(f"NAL only: {len(nal_only)}")
    
    if common:
        print(f"\nCommon fields:")
        for field in sorted(list(common)[:10]):
            print(f"  - {field}")
    
    if nal_only:
        print(f"\nNAL-exclusive fields (showing first 20):")
        for field in sorted(list(nal_only)[:20]):
            print(f"  - {field}")
        if len(nal_only) > 20:
            print(f"  ... and {len(nal_only) - 20} more NAL-only fields")
    
    # Recommendations
    print(f"\nRECOMMENDations:")
    if nal_count > sb_count:
        print(f"1. NAL file contains {percentage:.1f}% more property data fields")
        print(f"2. Consider enriching Supabase with NAL data")
        print(f"3. Update data pipeline to import all NAL fields")
        print(f"4. This will significantly enhance property analysis capabilities")
    
    return {
        'supabase_count': sb_count,
        'nal_count': nal_count,
        'winner': 'NAL' if nal_count > sb_count else 'Supabase',
        'difference': abs(nal_count - sb_count),
        'percentage_diff': percentage if nal_count > sb_count else 0
    }

def main():
    # Analyze both datasets
    supabase_fields = analyze_supabase()
    nal_fields = analyze_nal_file()
    
    if supabase_fields and nal_fields:
        comparison = compare_datasets(supabase_fields, nal_fields)
        
        # Save detailed field lists
        report_data = {
            'supabase_fields': supabase_fields,
            'nal_fields': nal_fields,
            'comparison': comparison
        }
        
        with open('field_comparison_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: field_comparison_report.json")
        
        # Final summary
        print(f"\nFINAL SUMMARY:")
        print(f"NAL Broward file contains {comparison['percentage_diff']:.1f}% more data fields")
        print(f"This represents a significant opportunity to enhance property data")

if __name__ == "__main__":
    main()