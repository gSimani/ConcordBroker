"""
Schema Validator for Broward County Export Files
Validates data files against extracted schema definitions
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates data files against Broward County export schema"""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with schema
        
        Args:
            schema_path: Path to schema JSON file
        """
        self.schema = {}
        self.validation_rules = {}
        self.errors = []
        self.warnings = []
        
        if schema_path and schema_path.exists():
            self.load_schema(schema_path)
        
        # Define validation rules for common field types
        self._define_validation_rules()
    
    def load_schema(self, schema_path: Path):
        """Load schema from JSON file"""
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
            logger.info(f"Loaded schema with {len(self.schema.get('file_layouts', {}))} file layouts")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
    
    def _define_validation_rules(self):
        """Define validation rules for field types"""
        self.validation_rules = {
            'PARCEL_ID': {
                'type': 'string',
                'pattern': r'^\d{12,15}$',
                'required': True,
                'description': 'Parcel identification number'
            },
            'DATE': {
                'type': 'date',
                'formats': ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d'],
                'description': 'Date field'
            },
            'AMOUNT': {
                'type': 'numeric',
                'min': 0,
                'max': 999999999,
                'description': 'Monetary amount'
            },
            'ZIP': {
                'type': 'string',
                'pattern': r'^\d{5}(-\d{4})?$',
                'description': 'ZIP code'
            },
            'PHONE': {
                'type': 'string',
                'pattern': r'^[\d\s\-\(\)]+$',
                'description': 'Phone number'
            },
            'EMAIL': {
                'type': 'string',
                'pattern': r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                'description': 'Email address'
            },
            'BOOLEAN': {
                'type': 'boolean',
                'values': ['Y', 'N', 'YES', 'NO', 'TRUE', 'FALSE', '1', '0'],
                'description': 'Boolean field'
            }
        }
    
    def validate_file(self, file_path: Path, file_type: Optional[str] = None) -> Dict:
        """
        Validate a data file against schema
        
        Args:
            file_path: Path to data file
            file_type: Optional file type identifier
            
        Returns:
            Validation results
        """
        if not file_path.exists():
            return {'valid': False, 'error': f"File not found: {file_path}"}
        
        logger.info(f"Validating file: {file_path}")
        
        # Reset errors and warnings
        self.errors = []
        self.warnings = []
        
        # Determine file type if not provided
        if not file_type:
            file_type = self._determine_file_type(file_path)
        
        # Get schema for this file type
        file_schema = self._get_file_schema(file_type)
        
        # Validate based on file extension
        if file_path.suffix.lower() == '.csv':
            result = self._validate_csv(file_path, file_schema)
        elif file_path.suffix.lower() == '.txt':
            result = self._validate_text(file_path, file_schema)
        elif file_path.suffix.lower() == '.json':
            result = self._validate_json(file_path, file_schema)
        else:
            result = {'valid': False, 'error': f"Unsupported file type: {file_path.suffix}"}
        
        # Add errors and warnings to result
        result['errors'] = self.errors
        result['warnings'] = self.warnings
        result['error_count'] = len(self.errors)
        result['warning_count'] = len(self.warnings)
        
        return result
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine file type from filename"""
        filename = file_path.name.upper()
        
        # Common patterns
        if 'DEED' in filename:
            return 'deed'
        elif 'MTG' in filename or 'MORTGAGE' in filename:
            return 'mortgage'
        elif 'SALE' in filename or 'SDF' in filename:
            return 'sales'
        elif 'NAL' in filename or 'PROPERTY' in filename:
            return 'property'
        elif 'OWNER' in filename:
            return 'owner'
        else:
            return 'unknown'
    
    def _get_file_schema(self, file_type: str) -> Dict:
        """Get schema for specific file type"""
        if not self.schema:
            return {}
        
        file_layouts = self.schema.get('file_layouts', {})
        
        # Try exact match first
        for layout_name, layout in file_layouts.items():
            if file_type.lower() in layout_name.lower():
                return layout
        
        # Return empty schema if not found
        return {'fields': []}
    
    def _validate_csv(self, file_path: Path, schema: Dict) -> Dict:
        """Validate CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                # Get expected fields from schema
                expected_fields = {field.get('name', '').upper() 
                                 for field in schema.get('fields', [])}
                
                # Check headers if schema defined
                if expected_fields and reader.fieldnames:
                    actual_fields = {field.upper() for field in reader.fieldnames}
                    
                    missing_fields = expected_fields - actual_fields
                    extra_fields = actual_fields - expected_fields
                    
                    if missing_fields:
                        self.warnings.append(f"Missing expected fields: {missing_fields}")
                    if extra_fields:
                        self.warnings.append(f"Extra fields not in schema: {extra_fields}")
                
                # Validate rows
                row_count = 0
                for row_num, row in enumerate(reader, 1):
                    row_count += 1
                    self._validate_row(row, schema, row_num)
                    
                    # Limit validation to prevent memory issues
                    if row_num > 10000:
                        self.warnings.append(f"Validation limited to first 10,000 rows")
                        break
                
                return {
                    'valid': len(self.errors) == 0,
                    'rows_validated': row_count,
                    'file_type': 'csv'
                }
                
        except Exception as e:
            self.errors.append(f"Failed to validate CSV: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _validate_text(self, file_path: Path, schema: Dict) -> Dict:
        """Validate text file (fixed-width or delimited)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                row_count = 0
                for line_num, line in enumerate(lines, 1):
                    if not line.strip():
                        continue
                    
                    row_count += 1
                    
                    # Try to parse based on schema positions
                    if schema.get('fields'):
                        self._validate_fixed_width_line(line, schema, line_num)
                    
                    # Limit validation
                    if line_num > 10000:
                        self.warnings.append(f"Validation limited to first 10,000 lines")
                        break
                
                return {
                    'valid': len(self.errors) == 0,
                    'rows_validated': row_count,
                    'file_type': 'text'
                }
                
        except Exception as e:
            self.errors.append(f"Failed to validate text file: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _validate_json(self, file_path: Path, schema: Dict) -> Dict:
        """Validate JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate structure
            if isinstance(data, list):
                for i, record in enumerate(data[:10000]):
                    self._validate_record(record, schema, i + 1)
            elif isinstance(data, dict):
                self._validate_record(data, schema, 1)
            
            return {
                'valid': len(self.errors) == 0,
                'records_validated': len(data) if isinstance(data, list) else 1,
                'file_type': 'json'
            }
            
        except Exception as e:
            self.errors.append(f"Failed to validate JSON: {e}")
            return {'valid': False, 'error': str(e)}
    
    def _validate_row(self, row: Dict, schema: Dict, row_num: int):
        """Validate a single row"""
        for field_def in schema.get('fields', []):
            field_name = field_def.get('name', '')
            field_type = field_def.get('type', '')
            required = field_def.get('required', False)
            
            value = row.get(field_name)
            
            # Check required fields
            if required and not value:
                self.errors.append(f"Row {row_num}: Required field '{field_name}' is empty")
                continue
            
            # Validate based on type
            if value and field_type:
                self._validate_field_value(value, field_type, field_name, row_num)
    
    def _validate_record(self, record: Dict, schema: Dict, record_num: int):
        """Validate a JSON record"""
        self._validate_row(record, schema, record_num)
    
    def _validate_fixed_width_line(self, line: str, schema: Dict, line_num: int):
        """Validate fixed-width format line"""
        for field_def in schema.get('fields', []):
            start_pos = field_def.get('start_pos')
            end_pos = field_def.get('end_pos')
            field_name = field_def.get('name', '')
            
            if start_pos and end_pos:
                try:
                    start = int(start_pos) - 1  # Convert to 0-based
                    end = int(end_pos)
                    
                    if len(line) >= end:
                        value = line[start:end].strip()
                        
                        if field_def.get('required') and not value:
                            self.errors.append(f"Line {line_num}: Required field '{field_name}' is empty")
                        
                except (ValueError, IndexError) as e:
                    self.warnings.append(f"Line {line_num}: Could not extract field '{field_name}': {e}")
    
    def _validate_field_value(self, value: Any, field_type: str, field_name: str, row_num: int):
        """Validate individual field value"""
        # Check against validation rules
        rule = self.validation_rules.get(field_type.upper())
        
        if not rule:
            return
        
        # Type validation
        if rule['type'] == 'string' and 'pattern' in rule:
            import re
            if not re.match(rule['pattern'], str(value)):
                self.warnings.append(f"Row {row_num}: Field '{field_name}' value '{value}' doesn't match pattern")
        
        elif rule['type'] == 'numeric':
            try:
                num_value = float(str(value).replace(',', '').replace('$', ''))
                if 'min' in rule and num_value < rule['min']:
                    self.warnings.append(f"Row {row_num}: Field '{field_name}' value {num_value} below minimum")
                if 'max' in rule and num_value > rule['max']:
                    self.warnings.append(f"Row {row_num}: Field '{field_name}' value {num_value} above maximum")
            except ValueError:
                self.errors.append(f"Row {row_num}: Field '{field_name}' has invalid numeric value: {value}")
        
        elif rule['type'] == 'date':
            valid_date = False
            for fmt in rule.get('formats', []):
                try:
                    datetime.strptime(str(value), fmt)
                    valid_date = True
                    break
                except ValueError:
                    continue
            
            if not valid_date:
                self.warnings.append(f"Row {row_num}: Field '{field_name}' has invalid date format: {value}")
        
        elif rule['type'] == 'boolean':
            if str(value).upper() not in rule.get('values', []):
                self.warnings.append(f"Row {row_num}: Field '{field_name}' has invalid boolean value: {value}")
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation results"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors[:10],  # First 10 errors
            'warnings': self.warnings[:10],  # First 10 warnings
            'valid': len(self.errors) == 0
        }


if __name__ == "__main__":
    # Test the validator
    validator = SchemaValidator()
    
    # Load schema if available
    schema_path = Path("data/broward_layout_schema/extracted/schema.json")
    if schema_path.exists():
        validator.load_schema(schema_path)
    
    # Test validation on a sample file
    test_file = Path("data/broward_daily_index/raw/sample.csv")
    if test_file.exists():
        result = validator.validate_file(test_file)
        print(f"\nValidation Result: {json.dumps(result, indent=2)}")
    else:
        print("No test file available")