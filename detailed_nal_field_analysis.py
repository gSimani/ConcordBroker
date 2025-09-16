"""
Detailed NAL Field Analysis
Categorize and understand all 165 NAL fields
"""

import pandas as pd
import json

def analyze_nal_fields_detailed():
    """Detailed analysis of all NAL fields with categorization"""
    file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAL16P202501.csv"
    
    try:
        # Read sample data
        df = pd.read_csv(file_path, nrows=100)
        
        print("DETAILED NAL FIELD ANALYSIS")
        print("=" * 60)
        print(f"Total fields: {len(df.columns)}")
        
        # Categorize all fields
        categories = {
            'IDENTIFICATION': [],
            'PROPERTY_LOCATION': [],
            'PROPERTY_CHARACTERISTICS': [],
            'VALUATION_DATA': [],
            'TAX_ASSESSMENT': [],
            'EXEMPTIONS': [],
            'OWNERSHIP_INFO': [],
            'LEGAL_DESCRIPTION': [],
            'BUILDING_DETAILS': [],
            'LAND_INFORMATION': [],
            'CODES_CLASSIFICATIONS': [],
            'DATES_YEARS': [],
            'GEOGRAPHIC_DATA': [],
            'UTILITY_INFORMATION': [],
            'SPECIAL_DISTRICTS': [],
            'UNKNOWN': []
        }
        
        # Analyze each field
        field_details = {}
        
        for field in df.columns:
            # Sample non-null values
            sample_values = df[field].dropna().head(5).tolist()
            non_null_count = df[field].notna().sum()
            data_type = str(df[field].dtype)
            
            field_details[field] = {
                'sample_values': [str(v) for v in sample_values],
                'non_null_percentage': round(non_null_count / len(df) * 100, 1),
                'data_type': data_type
            }
            
            # Categorize field
            field_upper = field.upper()
            
            if any(term in field_upper for term in ['PARCEL', 'CO_NO', 'FILE_T', 'GRP_NO']):
                categories['IDENTIFICATION'].append(field)
            elif any(term in field_upper for term in ['PHY_', 'ADDR', 'CITY', 'ZIP']):
                categories['PROPERTY_LOCATION'].append(field)
            elif any(term in field_upper for term in ['JV', 'AV_', 'TV_', 'VALUE', 'VAL']):
                categories['VALUATION_DATA'].append(field)
            elif any(term in field_upper for term in ['EXMPT', 'HMSTD']):
                categories['EXEMPTIONS'].append(field)
            elif any(term in field_upper for term in ['OWN', 'NAME', 'FIDU']):
                categories['OWNERSHIP_INFO'].append(field)
            elif any(term in field_upper for term in ['YR_BLT', 'ACT_YR', 'ASMNT_YR']):
                categories['DATES_YEARS'].append(field)
            elif any(term in field_upper for term in ['UC', 'CD', 'SPASS']):
                categories['CODES_CLASSIFICATIONS'].append(field)
            elif any(term in field_upper for term in ['BLDNG', 'NO_', 'UNITS']):
                categories['BUILDING_DETAILS'].append(field)
            elif any(term in field_upper for term in ['LND', 'LAND', 'ACRES']):
                categories['LAND_INFORMATION'].append(field)
            elif any(term in field_upper for term in ['NBRHD', 'CENSUS', 'DIST']):
                categories['GEOGRAPHIC_DATA'].append(field)
            elif any(term in field_upper for term in ['CHNG', 'DEL', 'ADD']):
                categories['TAX_ASSESSMENT'].append(field)
            elif any(term in field_upper for term in ['UTIL', 'WATER', 'SEWER']):
                categories['UTILITY_INFORMATION'].append(field)
            elif any(term in field_upper for term in ['SPEC', 'DIST', 'MUN']):
                categories['SPECIAL_DISTRICTS'].append(field)
            else:
                categories['UNKNOWN'].append(field)
        
        # Print categorized results
        print(f"\nFIELD CATEGORIES:")
        for category, fields in categories.items():
            if fields:
                print(f"\n{category} ({len(fields)} fields):")
                for field in fields:
                    details = field_details[field]
                    sample = details['sample_values'][0] if details['sample_values'] else 'NULL'
                    print(f"  - {field:15} | {details['non_null_percentage']:5.1f}% filled | Sample: {sample}")
        
        # Show most valuable missing fields
        print(f"\nMOST VALUABLE MISSING FIELDS:")
        high_value_fields = []
        
        for category, fields in categories.items():
            if category in ['VALUATION_DATA', 'BUILDING_DETAILS', 'PROPERTY_CHARACTERISTICS', 'TAX_ASSESSMENT']:
                for field in fields:
                    if field_details[field]['non_null_percentage'] > 50:  # Well-populated fields
                        high_value_fields.append((field, category, field_details[field]))
        
        print(f"Found {len(high_value_fields)} high-value fields missing from Supabase:")
        for field, category, details in high_value_fields[:15]:
            sample = details['sample_values'][0] if details['sample_values'] else 'N/A'
            print(f"  - {field:20} ({category}) | {details['non_null_percentage']}% filled | {sample}")
        
        # Create mapping suggestions
        print(f"\nSUGGESTED FIELD MAPPINGS FOR SUPABASE:")
        mapping_suggestions = {
            'JV': 'just_value',
            'AV_SD': 'assessed_value_school_district', 
            'TV_SD': 'taxable_value_school_district',
            'ACT_YR_BLT': 'year_built',
            'PHY_CITY': 'physical_city',
            'NBRHD_CD': 'neighborhood_code',
            'DOR_UC': 'dor_use_code',
            'PA_UC': 'property_appraiser_use_code',
            'EXMPT_05': 'homestead_exemption',
            'JV_HMSTD': 'just_value_homestead',
            'NO_BULDNG': 'number_of_buildings'
        }
        
        for nal_field, suggested_name in mapping_suggestions.items():
            if nal_field in field_details:
                details = field_details[nal_field]
                sample = details['sample_values'][0] if details['sample_values'] else 'N/A'
                print(f"  {nal_field} -> {suggested_name} | {details['non_null_percentage']}% filled | {sample}")
        
        # Save detailed analysis
        analysis_data = {
            'total_fields': len(df.columns),
            'categories': {cat: fields for cat, fields in categories.items() if fields},
            'field_details': field_details,
            'mapping_suggestions': mapping_suggestions
        }
        
        with open('detailed_nal_analysis.json', 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\nDetailed analysis saved to: detailed_nal_analysis.json")
        
        return analysis_data
        
    except Exception as e:
        print(f"Error analyzing NAL file: {e}")
        return None

if __name__ == "__main__":
    analyze_nal_fields_detailed()