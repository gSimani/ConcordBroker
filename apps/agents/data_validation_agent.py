"""
Data Validation Agent
Ensures data integrity and validates field mappings between Supabase and UI
"""

import os
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv('apps/web/.env')

class DataValidationAgent:
    """
    Agent responsible for validating data integrity and field mappings
    """
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.validation_rules = {}
        self.validation_results = []
        self.mismatch_log = []
        self.integrity_issues = []
        self.field_statistics = {}
        
    def _init_supabase(self):
        """Initialize Supabase connection"""
        url = os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("VITE_SUPABASE_ANON_KEY")
        if url and key:
            return create_client(url, key)
        return None
    
    def define_validation_rules(self) -> Dict:
        """
        Define comprehensive validation rules for all fields
        """
        self.validation_rules = {
            'parcel_id': {
                'type': 'string',
                'required': True,
                'pattern': r'^[A-Z0-9]{10,20}$',
                'unique': True,
                'description': 'Parcel ID must be alphanumeric, 10-20 characters'
            },
            'phy_addr1': {
                'type': 'string',
                'required': True,
                'min_length': 5,
                'max_length': 100,
                'pattern': r'^[0-9]+\s+[A-Z\s]+',
                'description': 'Physical address must start with number followed by street name'
            },
            'phy_city': {
                'type': 'string',
                'required': True,
                'min_length': 2,
                'max_length': 50,
                'allowed_values': [
                    'FORT LAUDERDALE', 'HOLLYWOOD', 'MIAMI', 'DAVIE',
                    'CORAL SPRINGS', 'POMPANO BEACH', 'DEERFIELD BEACH',
                    'SUNRISE', 'PLANTATION', 'COOPER CITY', 'HALLANDALE BEACH'
                ],
                'description': 'City must be a valid Florida city'
            },
            'phy_zipcd': {
                'type': 'string',
                'required': False,
                'pattern': r'^\d{5}(-\d{4})?$',
                'description': 'ZIP code must be 5 or 9 digits'
            },
            'owner_name': {
                'type': 'string',
                'required': False,
                'min_length': 2,
                'max_length': 200,
                'description': 'Owner name'
            },
            'just_value': {
                'type': 'decimal',
                'required': False,
                'min_value': 0,
                'max_value': 1000000000,
                'description': 'Just value must be positive'
            },
            'taxable_value': {
                'type': 'decimal',
                'required': False,
                'min_value': 0,
                'max_value': 1000000000,
                'must_be_less_than_or_equal': 'just_value',
                'description': 'Taxable value must be <= just value'
            },
            'land_value': {
                'type': 'decimal',
                'required': False,
                'min_value': 0,
                'max_value': 1000000000,
                'must_be_less_than_or_equal': 'just_value',
                'description': 'Land value must be <= just value'
            },
            'total_living_area': {
                'type': 'integer',
                'required': False,
                'min_value': 0,
                'max_value': 100000,
                'description': 'Living area in square feet'
            },
            'land_sqft': {
                'type': 'integer',
                'required': False,
                'min_value': 0,
                'max_value': 10000000,
                'description': 'Land area in square feet'
            },
            'year_built': {
                'type': 'integer',
                'required': False,
                'min_value': 1800,
                'max_value': datetime.now().year + 2,
                'description': 'Year built must be reasonable'
            },
            'property_use': {
                'type': 'string',
                'required': False,
                'pattern': r'^\d{3}$',
                'description': 'DOR use code must be 3 digits'
            },
            'sale_price': {
                'type': 'decimal',
                'required': False,
                'min_value': 0,
                'max_value': 1000000000,
                'description': 'Sale price must be positive'
            },
            'sale_date': {
                'type': 'date',
                'required': False,
                'min_date': '1900-01-01',
                'max_date': 'today',
                'description': 'Sale date must be in the past'
            }
        }
        
        return self.validation_rules
    
    def validate_record(self, record: Dict, table: str = 'florida_parcels') -> Tuple[bool, List[str]]:
        """
        Validate a single record against rules
        """
        errors = []
        
        for field_name, rules in self.validation_rules.items():
            value = record.get(field_name)
            
            # Check required fields
            if rules.get('required') and (value is None or value == ''):
                errors.append(f"{field_name}: Required field is missing")
                continue
            
            # Skip validation if field is optional and not present
            if not rules.get('required') and (value is None or value == ''):
                continue
            
            # Type validation
            field_errors = self._validate_field_type(field_name, value, rules)
            errors.extend(field_errors)
            
            # Pattern validation
            if 'pattern' in rules and isinstance(value, str):
                if not re.match(rules['pattern'], value):
                    errors.append(f"{field_name}: Does not match pattern {rules['pattern']}")
            
            # Length validation
            if isinstance(value, str):
                if 'min_length' in rules and len(value) < rules['min_length']:
                    errors.append(f"{field_name}: Too short (min {rules['min_length']})")
                if 'max_length' in rules and len(value) > rules['max_length']:
                    errors.append(f"{field_name}: Too long (max {rules['max_length']})")
            
            # Value range validation
            if isinstance(value, (int, float)):
                if 'min_value' in rules and value < rules['min_value']:
                    errors.append(f"{field_name}: Below minimum ({rules['min_value']})")
                if 'max_value' in rules and value > rules['max_value']:
                    errors.append(f"{field_name}: Above maximum ({rules['max_value']})")
            
            # Allowed values validation
            if 'allowed_values' in rules and value not in rules['allowed_values']:
                errors.append(f"{field_name}: Not in allowed values")
            
            # Cross-field validation
            if 'must_be_less_than_or_equal' in rules:
                other_field = rules['must_be_less_than_or_equal']
                other_value = record.get(other_field)
                if other_value and value and value > other_value:
                    errors.append(f"{field_name}: Must be <= {other_field}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_field_type(self, field_name: str, value: Any, rules: Dict) -> List[str]:
        """
        Validate field type
        """
        errors = []
        expected_type = rules.get('type')
        
        if expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"{field_name}: Expected string, got {type(value).__name__}")
        
        elif expected_type == 'integer':
            if not isinstance(value, int) and not (isinstance(value, float) and value.is_integer()):
                errors.append(f"{field_name}: Expected integer, got {type(value).__name__}")
        
        elif expected_type == 'decimal':
            if not isinstance(value, (int, float)):
                errors.append(f"{field_name}: Expected number, got {type(value).__name__}")
        
        elif expected_type == 'date':
            if not isinstance(value, str):
                errors.append(f"{field_name}: Expected date string, got {type(value).__name__}")
            else:
                try:
                    datetime.strptime(value.split('T')[0], '%Y-%m-%d')
                except:
                    errors.append(f"{field_name}: Invalid date format")
        
        return errors
    
    def validate_batch(self, records: List[Dict], table: str = 'florida_parcels') -> Dict:
        """
        Validate a batch of records
        """
        results = {
            'total_records': len(records),
            'valid_records': 0,
            'invalid_records': 0,
            'errors_by_field': {},
            'sample_errors': []
        }
        
        for record in records:
            is_valid, errors = self.validate_record(record, table)
            
            if is_valid:
                results['valid_records'] += 1
            else:
                results['invalid_records'] += 1
                
                # Track errors by field
                for error in errors:
                    field = error.split(':')[0]
                    if field not in results['errors_by_field']:
                        results['errors_by_field'][field] = 0
                    results['errors_by_field'][field] += 1
                
                # Keep sample errors
                if len(results['sample_errors']) < 10:
                    results['sample_errors'].append({
                        'parcel_id': record.get('parcel_id', 'unknown'),
                        'errors': errors
                    })
        
        return results
    
    def check_data_integrity(self, table: str = 'florida_parcels') -> Dict:
        """
        Check overall data integrity in the database
        """
        print(f"[Data Validation Agent] Checking data integrity for {table}...")
        
        integrity_report = {
            'table': table,
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'statistics': {}
        }
        
        try:
            # Check for duplicates
            duplicates = self._check_duplicates(table)
            if duplicates:
                integrity_report['issues'].append({
                    'type': 'duplicates',
                    'count': len(duplicates),
                    'samples': duplicates[:5]
                })
            
            # Check for null required fields
            null_required = self._check_null_required_fields(table)
            if null_required:
                integrity_report['issues'].append({
                    'type': 'null_required_fields',
                    'fields': null_required
                })
            
            # Check for data consistency
            inconsistencies = self._check_data_consistency(table)
            if inconsistencies:
                integrity_report['issues'].append({
                    'type': 'inconsistencies',
                    'count': len(inconsistencies),
                    'samples': inconsistencies[:5]
                })
            
            # Calculate field statistics
            integrity_report['statistics'] = self._calculate_field_statistics(table)
            
        except Exception as e:
            integrity_report['error'] = str(e)
        
        return integrity_report
    
    def _check_duplicates(self, table: str) -> List[str]:
        """
        Check for duplicate parcel IDs
        """
        duplicates = []
        
        try:
            # Query for parcel_ids with count > 1
            # Note: This is a simplified check - in production you'd use SQL
            result = self.supabase.table(table).select('parcel_id').execute()
            
            if result.data:
                parcel_ids = [r['parcel_id'] for r in result.data if r.get('parcel_id')]
                seen = set()
                for pid in parcel_ids:
                    if pid in seen:
                        duplicates.append(pid)
                    seen.add(pid)
        
        except Exception as e:
            print(f"[Data Validation Agent] Error checking duplicates: {e}")
        
        return duplicates
    
    def _check_null_required_fields(self, table: str) -> Dict:
        """
        Check for null values in required fields
        """
        null_counts = {}
        
        required_fields = [
            field for field, rules in self.validation_rules.items()
            if rules.get('required')
        ]
        
        try:
            # Sample check - in production, you'd check all records
            result = self.supabase.table(table).select('*').limit(100).execute()
            
            if result.data:
                for field in required_fields:
                    null_count = sum(
                        1 for r in result.data
                        if r.get(field) is None or r.get(field) == ''
                    )
                    if null_count > 0:
                        null_counts[field] = null_count
        
        except Exception as e:
            print(f"[Data Validation Agent] Error checking null fields: {e}")
        
        return null_counts
    
    def _check_data_consistency(self, table: str) -> List[Dict]:
        """
        Check for data consistency issues
        """
        inconsistencies = []
        
        try:
            result = self.supabase.table(table).select('*').limit(100).execute()
            
            if result.data:
                for record in result.data:
                    # Check if taxable_value > just_value
                    if record.get('taxable_value') and record.get('just_value'):
                        if record['taxable_value'] > record['just_value']:
                            inconsistencies.append({
                                'parcel_id': record.get('parcel_id'),
                                'issue': 'taxable_value > just_value',
                                'values': {
                                    'taxable_value': record['taxable_value'],
                                    'just_value': record['just_value']
                                }
                            })
                    
                    # Check if land_value > just_value
                    if record.get('land_value') and record.get('just_value'):
                        if record['land_value'] > record['just_value']:
                            inconsistencies.append({
                                'parcel_id': record.get('parcel_id'),
                                'issue': 'land_value > just_value',
                                'values': {
                                    'land_value': record['land_value'],
                                    'just_value': record['just_value']
                                }
                            })
        
        except Exception as e:
            print(f"[Data Validation Agent] Error checking consistency: {e}")
        
        return inconsistencies
    
    def _calculate_field_statistics(self, table: str) -> Dict:
        """
        Calculate statistics for numeric fields
        """
        stats = {}
        
        numeric_fields = [
            'just_value', 'taxable_value', 'land_value',
            'total_living_area', 'land_sqft', 'year_built'
        ]
        
        try:
            result = self.supabase.table(table).select(','.join(numeric_fields)).limit(1000).execute()
            
            if result.data:
                for field in numeric_fields:
                    values = [
                        r[field] for r in result.data
                        if r.get(field) is not None
                    ]
                    
                    if values:
                        stats[field] = {
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'avg': sum(values) / len(values),
                            'null_count': len(result.data) - len(values)
                        }
        
        except Exception as e:
            print(f"[Data Validation Agent] Error calculating statistics: {e}")
        
        return stats
    
    def validate_ui_mapping(self, element_id: str, value: Any) -> Tuple[bool, str]:
        """
        Validate that a value is appropriate for a UI element
        """
        # Import mapping agent to get field info
        from data_mapping_agent import DataMappingAgent
        mapper = DataMappingAgent()
        mapper.create_field_mappings()
        
        # Get the Supabase field for this element
        supabase_field = mapper.get_supabase_field_for_element(element_id)
        
        if not supabase_field:
            return False, f"No mapping found for element {element_id}"
        
        # Get field name from Supabase field
        field_name = supabase_field.split('.')[-1]
        
        # Validate against rules
        if field_name in self.validation_rules:
            rules = self.validation_rules[field_name]
            errors = self._validate_field_type(field_name, value, rules)
            
            if errors:
                return False, '; '.join(errors)
        
        return True, "Valid"
    
    def generate_validation_report(self) -> Dict:
        """
        Generate comprehensive validation report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_rules': self.validation_rules,
            'recent_validations': self.validation_results[-100:],
            'mismatch_log': self.mismatch_log[-50:],
            'integrity_issues': self.integrity_issues,
            'field_statistics': self.field_statistics
        }
        
        return report
    
    def save_validation_report(self, output_path: str = "validation_report.json") -> None:
        """
        Save validation report to file
        """
        report = self.generate_validation_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[Data Validation Agent] Report saved to {output_path}")


def main():
    """
    Run the Data Validation Agent
    """
    agent = DataValidationAgent()
    
    print("[Data Validation Agent] Initializing...")
    
    # Define validation rules
    rules = agent.define_validation_rules()
    print(f"[Data Validation Agent] Defined {len(rules)} validation rules")
    
    # Test validation on sample data
    sample_record = {
        'parcel_id': '504232100001',
        'phy_addr1': '123 OCEAN BLVD',
        'phy_city': 'FORT LAUDERDALE',
        'phy_zipcd': '33301',
        'owner_name': 'SMITH JOHN',
        'just_value': 525000,
        'taxable_value': 475000,
        'land_value': 225000,
        'total_living_area': 2800,
        'year_built': 2005
    }
    
    print("\n[Data Validation Agent] Testing validation...")
    is_valid, errors = agent.validate_record(sample_record)
    print(f"  Sample record valid: {is_valid}")
    if errors:
        print(f"  Errors: {errors}")
    
    # Check data integrity
    print("\n[Data Validation Agent] Checking data integrity...")
    integrity = agent.check_data_integrity()
    print(f"  Found {len(integrity.get('issues', []))} integrity issues")
    
    # Save report
    agent.save_validation_report()


if __name__ == "__main__":
    main()