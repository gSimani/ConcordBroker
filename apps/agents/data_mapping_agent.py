"""
Data Mapping Agent
Matches website fields with Supabase database columns and manages mappings
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv('apps/web/.env')

class DataMappingAgent:
    """
    Agent responsible for mapping website fields to Supabase columns
    """
    
    def __init__(self):
        self.mappings = {}
        self.supabase_schema = {}
        self.field_types = {}
        self.transformation_rules = {}
        self.supabase = self._init_supabase()
        
    def _init_supabase(self):
        """Initialize Supabase connection"""
        url = os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("VITE_SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
        return None
    
    def discover_supabase_schema(self) -> Dict:
        """
        Discover all tables and columns in Supabase
        """
        print("[Data Mapping Agent] Discovering Supabase schema...")
        
        tables = [
            'florida_parcels',
            'properties',
            'property_sales_history',
            'nav_assessments',
            'sunbiz_corporate',
            'florida_permits'
        ]
        
        for table in tables:
            try:
                # Get sample data to infer schema
                result = self.supabase.table(table).select('*').limit(1).execute()
                
                if result.data and len(result.data) > 0:
                    columns = list(result.data[0].keys())
                    
                    # Infer data types
                    column_types = {}
                    for col, val in result.data[0].items():
                        column_types[col] = type(val).__name__
                    
                    self.supabase_schema[table] = {
                        'columns': columns,
                        'column_types': column_types,
                        'row_count': self._get_table_count(table)
                    }
                    
                    print(f"  - {table}: {len(columns)} columns, {self.supabase_schema[table]['row_count']} rows")
                    
            except Exception as e:
                print(f"  - Error accessing {table}: {str(e)[:50]}")
        
        return self.supabase_schema
    
    def _get_table_count(self, table: str) -> int:
        """Get row count for a table"""
        try:
            result = self.supabase.table(table).select('id', count='exact').limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
        except:
            return 0
    
    def create_field_mappings(self) -> Dict:
        """
        Create comprehensive field mappings between UI and database
        """
        self.mappings = {
            # Property Address Fields
            'site_address': {
                'ui_ids': ['property-card-*-address', 'property-profile-address'],
                'supabase_field': 'florida_parcels.phy_addr1',
                'data_type': 'string',
                'nullable': False,
                'display_format': 'uppercase',
                'fallback': 'No Address Available'
            },
            'city': {
                'ui_ids': ['property-card-*-city', 'property-profile-city'],
                'supabase_field': 'florida_parcels.phy_city',
                'data_type': 'string',
                'nullable': False,
                'display_format': 'uppercase',
                'fallback': 'Unknown City'
            },
            'zip_code': {
                'ui_ids': ['property-card-*-zip', 'property-profile-zip'],
                'supabase_field': 'florida_parcels.phy_zipcd',
                'data_type': 'string',
                'nullable': True,
                'display_format': 'zip',
                'fallback': ''
            },
            
            # Owner Information
            'owner_name': {
                'ui_ids': ['property-card-*-owner', 'overview-owner-name'],
                'supabase_field': 'florida_parcels.owner_name',
                'data_type': 'string',
                'nullable': True,
                'display_format': 'title_case',
                'fallback': 'Owner Unknown'
            },
            'owner_address': {
                'ui_ids': ['overview-owner-address'],
                'supabase_field': 'florida_parcels.owner_addr1',
                'data_type': 'string',
                'nullable': True,
                'display_format': 'uppercase',
                'fallback': 'N/A'
            },
            
            # Valuation Fields
            'just_value': {
                'ui_ids': ['property-card-*-just-value', 'core-just-value', 'tax-just-value'],
                'supabase_field': 'florida_parcels.just_value',
                'data_type': 'decimal',
                'nullable': True,
                'display_format': 'currency',
                'fallback': 0,
                'transformation': 'format_currency'
            },
            'taxable_value': {
                'ui_ids': ['property-card-*-taxable-value', 'core-taxable-value', 'tax-taxable-value'],
                'supabase_field': 'florida_parcels.taxable_value',
                'data_type': 'decimal',
                'nullable': True,
                'display_format': 'currency',
                'fallback': 0,
                'transformation': 'format_currency'
            },
            'land_value': {
                'ui_ids': ['property-card-*-land-value', 'core-land-value'],
                'supabase_field': 'florida_parcels.land_value',
                'data_type': 'decimal',
                'nullable': True,
                'display_format': 'currency',
                'fallback': 0,
                'transformation': 'format_currency'
            },
            
            # Property Characteristics
            'building_sqft': {
                'ui_ids': ['property-card-*-building-sqft', 'overview-living-area'],
                'supabase_field': 'florida_parcels.total_living_area',
                'data_type': 'integer',
                'nullable': True,
                'display_format': 'number_with_commas',
                'fallback': 'N/A',
                'transformation': 'format_area'
            },
            'land_sqft': {
                'ui_ids': ['property-card-*-land-sqft', 'overview-land-area'],
                'supabase_field': 'florida_parcels.land_sqft',
                'data_type': 'integer',
                'nullable': True,
                'display_format': 'number_with_commas',
                'fallback': 'N/A',
                'transformation': 'format_area'
            },
            'year_built': {
                'ui_ids': ['property-card-*-year-built', 'overview-year-built'],
                'supabase_field': 'florida_parcels.year_built',
                'data_type': 'integer',
                'nullable': True,
                'display_format': 'year',
                'fallback': 'N/A'
            },
            
            # Property Type
            'property_use_code': {
                'ui_ids': ['property-card-*-use-code', 'property-type-badge'],
                'supabase_field': 'florida_parcels.property_use',
                'data_type': 'string',
                'nullable': True,
                'display_format': 'dor_code',
                'fallback': '000',
                'transformation': 'map_property_type'
            },
            
            # Sales Information
            'last_sale_price': {
                'ui_ids': ['property-card-*-sale-price', 'sales-last-price'],
                'supabase_field': 'florida_parcels.sale_price',
                'data_type': 'decimal',
                'nullable': True,
                'display_format': 'currency',
                'fallback': 'N/A',
                'transformation': 'format_currency'
            },
            'last_sale_date': {
                'ui_ids': ['property-card-*-sale-date', 'sales-last-date'],
                'supabase_field': 'florida_parcels.sale_date',
                'data_type': 'date',
                'nullable': True,
                'display_format': 'date',
                'fallback': 'N/A',
                'transformation': 'format_date'
            },
            
            # Tax Information
            'homestead_exemption': {
                'ui_ids': ['tax-homestead-exemption'],
                'supabase_field': 'florida_parcels.homestead_exemption',
                'data_type': 'decimal',
                'nullable': True,
                'display_format': 'homestead',
                'fallback': 'None',
                'transformation': 'format_homestead'
            }
        }
        
        return self.mappings
    
    def validate_mapping(self, field_name: str, value: any) -> Tuple[bool, str]:
        """
        Validate that a value matches expected type for field
        """
        if field_name not in self.mappings:
            return False, f"Unknown field: {field_name}"
        
        mapping = self.mappings[field_name]
        expected_type = mapping['data_type']
        
        # Check for null values
        if value is None:
            if mapping['nullable']:
                return True, "Valid null value"
            else:
                return False, f"Field {field_name} cannot be null"
        
        # Type validation
        type_validators = {
            'string': lambda v: isinstance(v, str),
            'integer': lambda v: isinstance(v, (int, float)) and float(v).is_integer(),
            'decimal': lambda v: isinstance(v, (int, float)),
            'date': lambda v: isinstance(v, str) and len(v) >= 8,
            'boolean': lambda v: isinstance(v, bool)
        }
        
        if expected_type in type_validators:
            if type_validators[expected_type](value):
                return True, "Valid"
            else:
                return False, f"Expected {expected_type}, got {type(value).__name__}"
        
        return True, "No validation rule"
    
    def transform_value(self, field_name: str, value: any) -> any:
        """
        Transform a value according to field rules
        """
        if field_name not in self.mappings:
            return value
        
        mapping = self.mappings[field_name]
        
        # Handle null values
        if value is None or value == '':
            return mapping['fallback']
        
        # Apply transformation
        transformation = mapping.get('transformation')
        if transformation:
            transformers = {
                'format_currency': lambda v: f"${v:,.0f}" if isinstance(v, (int, float)) else "N/A",
                'format_area': lambda v: f"{v:,} sq ft" if isinstance(v, (int, float)) else "N/A",
                'format_date': lambda v: v.split('T')[0] if isinstance(v, str) else "N/A",
                'format_homestead': lambda v: "Yes" if v and v > 0 else "No",
                'map_property_type': self._map_property_type
            }
            
            if transformation in transformers:
                return transformers[transformation](value)
        
        # Apply display format
        display_format = mapping.get('display_format')
        if display_format:
            formatters = {
                'uppercase': lambda v: str(v).upper(),
                'title_case': lambda v: str(v).title(),
                'number_with_commas': lambda v: f"{v:,}" if isinstance(v, (int, float)) else str(v),
                'zip': lambda v: str(v).zfill(5) if v else "",
                'year': lambda v: str(int(v)) if v else "N/A"
            }
            
            if display_format in formatters:
                return formatters[display_format](value)
        
        return value
    
    def _map_property_type(self, use_code: str) -> str:
        """
        Map DOR use code to property type category
        """
        if not use_code:
            return "Unknown"
        
        first_digit = str(use_code)[0]
        mapping = {
            '0': 'Residential',
            '1': 'Commercial',
            '2': 'Commercial',
            '3': 'Commercial',
            '4': 'Industrial',
            '5': 'Agricultural',
            '6': 'Agricultural',
            '7': 'Institutional',
            '8': 'Institutional',
            '9': 'Miscellaneous'
        }
        
        return mapping.get(first_digit, 'Unknown')
    
    def get_ui_elements_for_field(self, supabase_field: str) -> List[str]:
        """
        Get all UI element IDs that should display a Supabase field
        """
        elements = []
        
        for field_name, mapping in self.mappings.items():
            if mapping['supabase_field'] == supabase_field:
                elements.extend(mapping['ui_ids'])
        
        return elements
    
    def get_supabase_field_for_element(self, element_id: str) -> Optional[str]:
        """
        Get the Supabase field that should populate a UI element
        """
        for field_name, mapping in self.mappings.items():
            for ui_id_pattern in mapping['ui_ids']:
                if '*' in ui_id_pattern:
                    # Handle wildcard patterns
                    pattern = ui_id_pattern.replace('*', '.*')
                    import re
                    if re.match(pattern, element_id):
                        return mapping['supabase_field']
                elif ui_id_pattern == element_id:
                    return mapping['supabase_field']
        
        return None
    
    def generate_mapping_report(self) -> Dict:
        """
        Generate a comprehensive mapping report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_mappings': len(self.mappings),
            'supabase_tables': len(self.supabase_schema),
            'mappings': self.mappings,
            'supabase_schema': self.supabase_schema,
            'validation_rules': {
                field: {
                    'data_type': mapping['data_type'],
                    'nullable': mapping['nullable'],
                    'has_transformation': 'transformation' in mapping
                }
                for field, mapping in self.mappings.items()
            }
        }
        
        return report
    
    def save_mapping_configuration(self, output_path: str = "data_mapping_config.json") -> None:
        """
        Save the mapping configuration
        """
        config = self.generate_mapping_report()
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"[Data Mapping Agent] Configuration saved to {output_path}")


def main():
    """
    Run the Data Mapping Agent
    """
    agent = DataMappingAgent()
    
    print("[Data Mapping Agent] Initializing...")
    
    # Discover Supabase schema
    schema = agent.discover_supabase_schema()
    
    # Create field mappings
    mappings = agent.create_field_mappings()
    
    print(f"\n[Data Mapping Agent] Created {len(mappings)} field mappings")
    
    # Test some mappings
    test_cases = [
        ('just_value', 525000),
        ('owner_name', 'SMITH JOHN'),
        ('year_built', None),
        ('property_use_code', '001')
    ]
    
    print("\n[Data Mapping Agent] Testing transformations:")
    for field, value in test_cases:
        transformed = agent.transform_value(field, value)
        print(f"  {field}: {value} → {transformed}")
    
    # Save configuration
    agent.save_mapping_configuration()


if __name__ == "__main__":
    main()