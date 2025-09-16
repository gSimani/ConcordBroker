"""
Filter Validation and Mapping Agent
====================================
This agent ensures all property filters work correctly by mapping UI values
to the actual database values and validating filter combinations.

Author: ConcordBroker Team
Date: 2025-01-07
"""

import os
import json
import csv
import requests
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv('apps/web/.env')

class FilterValidationAgent:
    """
    Agent for validating and mapping property search filters to database values.
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Florida DOR Property Use Codes Mapping
        # Based on Florida Department of Revenue classifications
        self.property_type_mappings = {
            # UI Values to DOR Codes
            'Residential': {
                'codes': ['001', '002', '003', '004', '005', '006', '007', '008', '009'],
                'db_values': ['RESIDENTIAL', 'Residential', 'residential', 'RES'],
                'dor_codes': list(range(1, 10)),  # DOR codes 01-09
                'description': 'Single Family, Condos, Mobile Homes, Multi-family',
                'subtypes': {
                    'Single Family': ['001', '002', '003'],
                    'Condo': ['004', '005'],
                    'Mobile Home': ['006', '007'],
                    'Multi-family': ['008', '009']
                }
            },
            'Commercial': {
                'codes': ['010', '011', '012', '013', '014', '015', '016', '017', '018', '019'],
                'db_values': ['COMMERCIAL', 'Commercial', 'commercial', 'COM', 'COMM'],
                'dor_codes': list(range(10, 40)),  # DOR codes 10-39
                'description': 'Stores, Offices, Hotels, Apartments (10+ units)',
                'subtypes': {
                    'Retail': ['011', '012', '013'],
                    'Office': ['017', '018'],
                    'Hotel/Motel': ['019', '039'],
                    'Mixed Use': ['010', '015', '016']
                }
            },
            'Industrial': {
                'codes': ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049'],
                'db_values': ['INDUSTRIAL', 'Industrial', 'industrial', 'IND'],
                'dor_codes': list(range(40, 50)),  # DOR codes 40-49
                'description': 'Manufacturing, Warehouses, Processing Plants',
                'subtypes': {
                    'Light Manufacturing': ['041', '042'],
                    'Heavy Manufacturing': ['043', '044'],
                    'Warehouse': ['048', '049'],
                    'Processing': ['045', '046', '047']
                }
            },
            'Agricultural': {
                'codes': ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059'],
                'db_values': ['AGRICULTURAL', 'Agricultural', 'agricultural', 'AG', 'AGR'],
                'dor_codes': list(range(50, 70)),  # DOR codes 50-69
                'description': 'Farms, Groves, Ranches, Timber',
                'subtypes': {
                    'Cropland': ['051', '052', '053'],
                    'Grazing': ['054', '055', '056'],
                    'Orchard/Grove': ['057', '058'],
                    'Timber': ['059', '060']
                }
            },
            'Vacant': {
                'codes': ['000', '090', '091', '092', '093', '094', '095'],
                'db_values': ['VACANT', 'Vacant', 'vacant', 'VAC'],
                'dor_codes': [0, 90, 91, 92, 93, 94, 95],
                'description': 'Vacant Land, Lots',
                'subtypes': {
                    'Residential Vacant': ['000', '001V'],
                    'Commercial Vacant': ['090', '091'],
                    'Industrial Vacant': ['092'],
                    'Agricultural Vacant': ['093', '094']
                }
            },
            'Institutional': {
                'codes': ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '080', '081', '082', '083', '084', '085', '086'],
                'db_values': ['INSTITUTIONAL', 'Institutional', 'institutional', 'INST', 'GOV', 'GOVT'],
                'dor_codes': list(range(70, 90)),  # DOR codes 70-89
                'description': 'Schools, Churches, Hospitals, Government',
                'subtypes': {
                    'Schools': ['071', '072', '073'],
                    'Churches': ['077', '078'],
                    'Hospitals': ['074', '075', '076'],
                    'Government': ['080', '081', '082', '083', '084', '085', '086']
                }
            },
            'Mixed Use': {
                'codes': ['015', '016', '029', '039'],
                'db_values': ['MIXED', 'Mixed Use', 'mixed use', 'MIXED USE', 'MXD'],
                'dor_codes': [15, 16, 29, 39],
                'description': 'Properties with multiple uses',
                'subtypes': {}
            },
            'All Properties': {
                'codes': ['*'],
                'db_values': ['*'],
                'dor_codes': ['*'],
                'description': 'All property types',
                'subtypes': {}
            }
        }
        
        # City name standardization
        self.city_mappings = {
            'Fort Lauderdale': ['Fort Lauderdale', 'FORT LAUDERDALE', 'FT LAUDERDALE', 'FT. LAUDERDALE', 'Ft Lauderdale'],
            'Hollywood': ['Hollywood', 'HOLLYWOOD'],
            'Pembroke Pines': ['Pembroke Pines', 'PEMBROKE PINES', 'PEMBROKE PNS'],
            'Coral Springs': ['Coral Springs', 'CORAL SPRINGS', 'CORAL SPGS'],
            'Miramar': ['Miramar', 'MIRAMAR'],
            'Davie': ['Davie', 'DAVIE'],
            'Plantation': ['Plantation', 'PLANTATION'],
            'Sunrise': ['Sunrise', 'SUNRISE'],
            'Pompano Beach': ['Pompano Beach', 'POMPANO BEACH', 'POMPANO BCH', 'POMPANO'],
            'Deerfield Beach': ['Deerfield Beach', 'DEERFIELD BEACH', 'DEERFIELD BCH', 'DEERFIELD'],
            'Tamarac': ['Tamarac', 'TAMARAC'],
            'Weston': ['Weston', 'WESTON'],
            'Coconut Creek': ['Coconut Creek', 'COCONUT CREEK', 'COCONUT CRK'],
            'Margate': ['Margate', 'MARGATE'],
            'Lauderhill': ['Lauderhill', 'LAUDERHILL'],
            'Oakland Park': ['Oakland Park', 'OAKLAND PARK', 'OAKLAND PK'],
            'Hallandale Beach': ['Hallandale Beach', 'HALLANDALE BEACH', 'HALLANDALE BCH', 'HALLANDALE'],
            'Cooper City': ['Cooper City', 'COOPER CITY'],
            'Dania Beach': ['Dania Beach', 'DANIA BEACH', 'DANIA'],
            'Wilton Manors': ['Wilton Manors', 'WILTON MANORS', 'WILTON MNRS']
        }
        
        # Price range presets
        self.price_ranges = {
            'Under $100K': {'min': 0, 'max': 100000},
            '$100K-$250K': {'min': 100000, 'max': 250000},
            '$250K-$500K': {'min': 250000, 'max': 500000},
            '$500K-$1M': {'min': 500000, 'max': 1000000},
            '$1M-$2.5M': {'min': 1000000, 'max': 2500000},
            '$2.5M-$5M': {'min': 2500000, 'max': 5000000},
            'Over $5M': {'min': 5000000, 'max': None}
        }
        
        # Advanced filter fields
        self.advanced_filters = {
            'bedrooms': {'field': 'beds_val', 'type': 'number'},
            'bathrooms': {'field': 'baths_val', 'type': 'number'},
            'squareFootage': {'field': 'tot_lvg_area', 'type': 'number'},
            'lotSize': {'field': 'lnd_sqfoot', 'type': 'number'},
            'yearBuilt': {'field': 'act_yr_blt', 'type': 'number'},
            'hasPool': {'field': 'pool', 'type': 'boolean'},
            'hasGarage': {'field': 'garage_spaces', 'type': 'number'},
            'waterfront': {'field': 'water_front_cd', 'type': 'boolean'},
            'hasHOA': {'field': 'hoa_fee', 'type': 'boolean'},
            'foreclosure': {'field': 'has_foreclosure', 'type': 'boolean'},
            'taxDeed': {'field': 'has_tax_deed', 'type': 'boolean'},
            'taxLien': {'field': 'has_tax_lien', 'type': 'boolean'}
        }
    
    def validate_property_type_filter(self, ui_value: str) -> Dict[str, Any]:
        """
        Validate and map property type from UI to database values.
        """
        # Check if it's a known property type
        for prop_type, config in self.property_type_mappings.items():
            if ui_value.lower() == prop_type.lower():
                return {
                    'valid': True,
                    'ui_value': ui_value,
                    'db_field': 'dor_cd',
                    'db_values': config['dor_codes'],
                    'codes': config['codes'],
                    'description': config['description'],
                    'query': self._build_property_type_query(config)
                }
        
        # Check if it's a DOR code directly
        for prop_type, config in self.property_type_mappings.items():
            if ui_value in config['codes']:
                return {
                    'valid': True,
                    'ui_value': prop_type,
                    'db_field': 'dor_cd',
                    'db_values': [ui_value],
                    'codes': [ui_value],
                    'description': config['description'],
                    'query': f"dor_cd=eq.{ui_value}"
                }
        
        return {
            'valid': False,
            'ui_value': ui_value,
            'error': f"Unknown property type: {ui_value}",
            'suggestions': list(self.property_type_mappings.keys())
        }
    
    def _build_property_type_query(self, config: Dict) -> str:
        """
        Build Supabase query string for property type filter.
        """
        if config['dor_codes'] == ['*']:
            return None  # No filter for "All Properties"
        
        # Use IN operator for multiple codes
        if len(config['dor_codes']) > 1:
            codes = ','.join(str(c) for c in config['dor_codes'])
            return f"dor_cd=in.({codes})"
        else:
            return f"dor_cd=eq.{config['dor_codes'][0]}"
    
    def validate_city_filter(self, ui_value: str) -> Dict[str, Any]:
        """
        Validate and standardize city name.
        """
        # Check exact match first
        for standard_city, variations in self.city_mappings.items():
            if ui_value in variations:
                return {
                    'valid': True,
                    'ui_value': ui_value,
                    'standard_value': standard_city,
                    'db_field': 'phy_city',
                    'query': f"phy_city=ilike.%{standard_city}%"
                }
        
        # Check case-insensitive match
        ui_value_upper = ui_value.upper()
        for standard_city, variations in self.city_mappings.items():
            if any(ui_value_upper == v.upper() for v in variations):
                return {
                    'valid': True,
                    'ui_value': ui_value,
                    'standard_value': standard_city,
                    'db_field': 'phy_city',
                    'query': f"phy_city=ilike.%{standard_city}%"
                }
        
        # Unknown city - still allow it but warn
        return {
            'valid': True,
            'ui_value': ui_value,
            'standard_value': ui_value,
            'db_field': 'phy_city',
            'query': f"phy_city=ilike.%{ui_value}%",
            'warning': f"City '{ui_value}' not in standard list"
        }
    
    def validate_price_filter(self, min_price: Optional[str], max_price: Optional[str]) -> Dict[str, Any]:
        """
        Validate price range filters.
        """
        result = {'valid': True, 'db_field': 'jv'}
        
        # Parse min price
        if min_price:
            try:
                min_val = float(min_price.replace(',', '').replace('$', ''))
                result['min_value'] = min_val
                result['min_query'] = f"jv=gte.{int(min_val)}"
            except ValueError:
                result['valid'] = False
                result['error'] = f"Invalid min price: {min_price}"
        
        # Parse max price
        if max_price:
            try:
                max_val = float(max_price.replace(',', '').replace('$', ''))
                result['max_value'] = max_val
                result['max_query'] = f"jv=lte.{int(max_val)}"
            except ValueError:
                result['valid'] = False
                result['error'] = f"Invalid max price: {max_price}"
        
        # Validate range logic
        if result.get('min_value') and result.get('max_value'):
            if result['min_value'] > result['max_value']:
                result['valid'] = False
                result['error'] = "Min price cannot be greater than max price"
        
        return result
    
    def validate_all_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all filters and generate query parameters.
        """
        validation_results = {
            'valid': True,
            'filters': {},
            'queries': [],
            'errors': [],
            'warnings': []
        }
        
        # Validate property type
        if filters.get('propertyType'):
            prop_result = self.validate_property_type_filter(filters['propertyType'])
            if prop_result['valid']:
                validation_results['filters']['propertyType'] = prop_result
                if prop_result.get('query'):
                    validation_results['queries'].append(prop_result['query'])
            else:
                validation_results['valid'] = False
                validation_results['errors'].append(prop_result['error'])
        
        # Validate city
        if filters.get('city'):
            city_result = self.validate_city_filter(filters['city'])
            validation_results['filters']['city'] = city_result
            if city_result.get('query'):
                validation_results['queries'].append(city_result['query'])
            if city_result.get('warning'):
                validation_results['warnings'].append(city_result['warning'])
        
        # Validate price range
        if filters.get('minPrice') or filters.get('maxPrice'):
            price_result = self.validate_price_filter(
                filters.get('minPrice'),
                filters.get('maxPrice')
            )
            if price_result['valid']:
                validation_results['filters']['price'] = price_result
                if price_result.get('min_query'):
                    validation_results['queries'].append(price_result['min_query'])
                if price_result.get('max_query'):
                    validation_results['queries'].append(price_result['max_query'])
            else:
                validation_results['valid'] = False
                validation_results['errors'].append(price_result['error'])
        
        # Build final query string
        if validation_results['queries']:
            validation_results['query_string'] = '&'.join(validation_results['queries'])
        
        return validation_results
    
    def analyze_database_values(self) -> Dict[str, Any]:
        """
        Analyze actual values in database to ensure mappings are correct.
        """
        print("\n" + "="*60)
        print("ANALYZING DATABASE VALUES")
        print("="*60)
        
        analysis = {
            'property_types': {},
            'cities': {},
            'price_ranges': {},
            'recommendations': []
        }
        
        # Check actual DOR codes in database
        url = f"{self.supabase_url}/rest/v1/florida_parcels?select=dor_cd&limit=1000"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                dor_codes = defaultdict(int)
                
                for record in data:
                    if record.get('dor_cd'):
                        dor_codes[record['dor_cd']] += 1
                
                analysis['property_types'] = dict(dor_codes)
                
                # Map codes to types
                for code, count in dor_codes.items():
                    found = False
                    for prop_type, config in self.property_type_mappings.items():
                        if str(code) in config['codes'] or int(code) in config.get('dor_codes', []):
                            found = True
                            break
                    
                    if not found:
                        analysis['recommendations'].append(
                            f"Unknown DOR code {code} found {count} times - needs mapping"
                        )
        except Exception as e:
            print(f"Error analyzing database: {e}")
        
        return analysis
    
    def generate_filter_fixes(self) -> str:
        """
        Generate TypeScript code to fix filter issues.
        """
        typescript_code = """// Property Filter Mapping Service
// Generated by Filter Validation Agent

export const PropertyTypeMappings = {
  // UI display values to database codes
  Residential: {
    dorCodes: ['001', '002', '003', '004', '005', '006', '007', '008', '009'],
    dorRange: { min: 1, max: 9 },
    label: 'Residential',
    icon: 'Home',
    color: 'green',
    subtypes: {
      'Single Family': ['001', '002', '003'],
      'Condo': ['004', '005'],
      'Mobile Home': ['006', '007'],
      'Multi-family': ['008', '009']
    }
  },
  Commercial: {
    dorCodes: ['010', '011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024', '025', '026', '027', '028', '029', '030', '031', '032', '033', '034', '035', '036', '037', '038', '039'],
    dorRange: { min: 10, max: 39 },
    label: 'Commercial',
    icon: 'Building',
    color: 'blue',
    subtypes: {
      'Retail': ['011', '012', '013'],
      'Office': ['017', '018'],
      'Hotel/Motel': ['019', '039'],
      'Mixed Use': ['010', '015', '016']
    }
  },
  Industrial: {
    dorCodes: ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049'],
    dorRange: { min: 40, max: 49 },
    label: 'Industrial',
    icon: 'Factory',
    color: 'purple',
    subtypes: {
      'Light Manufacturing': ['041', '042'],
      'Heavy Manufacturing': ['043', '044'],
      'Warehouse': ['048', '049']
    }
  },
  Agricultural: {
    dorCodes: ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059', '060', '061', '062', '063', '064', '065', '066', '067', '068', '069'],
    dorRange: { min: 50, max: 69 },
    label: 'Agricultural',
    icon: 'Wheat',
    color: 'green',
    subtypes: {
      'Cropland': ['051', '052', '053'],
      'Grazing': ['054', '055', '056'],
      'Orchard/Grove': ['057', '058']
    }
  },
  Vacant: {
    dorCodes: ['000', '090', '091', '092', '093', '094', '095'],
    dorRange: { min: 90, max: 95 },
    label: 'Vacant Land',
    icon: 'Map',
    color: 'gray',
    subtypes: {}
  },
  Institutional: {
    dorCodes: ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '080', '081', '082', '083', '084', '085', '086', '087', '088', '089'],
    dorRange: { min: 70, max: 89 },
    label: 'Institutional',
    icon: 'Building2',
    color: 'teal',
    subtypes: {
      'Schools': ['071', '072', '073'],
      'Churches': ['077', '078'],
      'Hospitals': ['074', '075', '076'],
      'Government': ['080', '081', '082', '083', '084', '085', '086']
    }
  }
};

export function mapPropertyTypeToQuery(uiValue: string): string | null {
  const mapping = PropertyTypeMappings[uiValue];
  if (!mapping) return null;
  
  // Create query for Supabase
  if (mapping.dorRange) {
    return `dor_cd.gte.${mapping.dorRange.min}&dor_cd.lte.${mapping.dorRange.max}`;
  }
  
  return null;
}

export function getDorCodePropertyType(dorCode: string | number): string {
  const code = typeof dorCode === 'string' ? parseInt(dorCode) : dorCode;
  
  if (code >= 1 && code <= 9) return 'Residential';
  if (code >= 10 && code <= 39) return 'Commercial';
  if (code >= 40 && code <= 49) return 'Industrial';
  if (code >= 50 && code <= 69) return 'Agricultural';
  if (code >= 70 && code <= 89) return 'Institutional';
  if (code >= 90 && code <= 95) return 'Vacant';
  if (code === 0) return 'Vacant';
  
  return 'Other';
}

export function buildFilterQuery(filters: any) {
  const queryParts: string[] = [];
  
  // Property Type Filter
  if (filters.propertyType && filters.propertyType !== 'All Properties') {
    const mapping = PropertyTypeMappings[filters.propertyType];
    if (mapping && mapping.dorRange) {
      queryParts.push(`dor_cd.gte.${mapping.dorRange.min}`);
      queryParts.push(`dor_cd.lte.${mapping.dorRange.max}`);
    }
  }
  
  // City Filter
  if (filters.city) {
    queryParts.push(`phy_city.ilike.%${filters.city}%`);
  }
  
  // Price Range
  if (filters.minPrice) {
    queryParts.push(`jv.gte.${filters.minPrice}`);
  }
  if (filters.maxPrice) {
    queryParts.push(`jv.lte.${filters.maxPrice}`);
  }
  
  // Advanced Filters
  if (filters.bedrooms) {
    queryParts.push(`beds_val.gte.${filters.bedrooms}`);
  }
  if (filters.bathrooms) {
    queryParts.push(`baths_val.gte.${filters.bathrooms}`);
  }
  if (filters.squareFootage) {
    queryParts.push(`tot_lvg_area.gte.${filters.squareFootage}`);
  }
  if (filters.yearBuilt) {
    queryParts.push(`act_yr_blt.gte.${filters.yearBuilt}`);
  }
  
  // Boolean filters
  if (filters.hasPool) {
    queryParts.push(`pool.eq.Y`);
  }
  if (filters.waterfront) {
    queryParts.push(`water_front_cd.neq.`);
  }
  if (filters.foreclosure) {
    queryParts.push(`has_foreclosure.eq.true`);
  }
  if (filters.taxDeed) {
    queryParts.push(`has_tax_deed.eq.true`);
  }
  if (filters.taxLien) {
    queryParts.push(`has_tax_lien.eq.true`);
  }
  
  return queryParts.join('&');
}
"""
        
        return typescript_code
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """
        Run complete filter validation and generate fixes.
        """
        print("\n" + "="*60)
        print("FILTER VALIDATION AGENT")
        print("="*60)
        
        # Test filters
        test_cases = [
            {'propertyType': 'Commercial'},
            {'propertyType': 'Residential', 'city': 'Fort Lauderdale'},
            {'propertyType': 'Industrial', 'minPrice': '500000', 'maxPrice': '2000000'},
            {'city': 'Hollywood', 'bedrooms': '3', 'bathrooms': '2'}
        ]
        
        results = {
            'test_results': [],
            'database_analysis': self.analyze_database_values(),
            'fixes_generated': False,
            'recommendations': []
        }
        
        print("\nTesting filter combinations...")
        for test in test_cases:
            validation = self.validate_all_filters(test)
            results['test_results'].append({
                'input': test,
                'validation': validation
            })
            
            if validation['valid']:
                print(f"  OK: {test}")
                if validation.get('query_string'):
                    print(f"      Query: {validation['query_string']}")
            else:
                print(f"  FAIL: {test}")
                for error in validation['errors']:
                    print(f"      Error: {error}")
        
        # Generate TypeScript fixes
        typescript_fixes = self.generate_filter_fixes()
        
        # Save fixes
        fixes_path = 'apps/web/src/lib/propertyFilterMappings.ts'
        os.makedirs(os.path.dirname(fixes_path), exist_ok=True)
        with open(fixes_path, 'w') as f:
            f.write(typescript_fixes)
        
        results['fixes_generated'] = True
        results['fixes_file'] = fixes_path
        
        # Generate recommendations
        results['recommendations'] = [
            "1. Update PropertySearchSupabase to use the new mapping functions",
            "2. Replace hardcoded '001' values with proper DOR code ranges",
            "3. Implement the buildFilterQuery function for consistent queries",
            "4. Add property type badges that show the correct type based on DOR codes",
            "5. Test all filter combinations with real data"
        ]
        
        print("\n" + "="*60)
        print("VALIDATION COMPLETE")
        print("="*60)
        print(f"\nGenerated fixes saved to: {fixes_path}")
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  - {rec}")
        
        return results


# Main execution
if __name__ == "__main__":
    agent = FilterValidationAgent()
    agent.run_complete_validation()