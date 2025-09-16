"""
Data Validator for Florida Revenue NAL/SDF/NAP Files
Validates data files against extracted schema from Users Guide
"""

import json
import csv
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FloridaRevenueDataValidator:
    """Validates Florida Revenue data files against official schema"""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with schema
        
        Args:
            schema_path: Path to schema JSON file
        """
        self.schema = {}
        self.file_schemas = {}
        self.validation_rules = {}
        self.errors = []
        self.warnings = []
        self.info = []
        
        if schema_path and schema_path.exists():
            self.load_schema(schema_path)
        
        # Define validation rules for Florida Revenue data
        self._define_validation_rules()
    
    def load_schema(self, schema_path: Path):
        """Load schema from JSON file"""
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
            
            # Extract file schemas
            self.file_schemas = self.schema.get('file_schemas', {})
            
            logger.info(f"Loaded schema with {len(self.file_schemas)} file types")
            
            # Build validation rules from schema
            self._build_validation_from_schema()
            
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
    
    def _define_validation_rules(self):
        """Define validation rules for Florida Revenue field types"""
        self.validation_rules = {
            # NAL (Name Address Library) fields
            'PARCEL_ID': {
                'type': 'string',
                'pattern': r'^\d{12,15}$',
                'required': True,
                'description': 'Parcel identification number'
            },
            'OWNER_NAME': {
                'type': 'string',
                'max_length': 100,
                'required': True,
                'description': 'Property owner name'
            },
            'MAILING_ADDRESS': {
                'type': 'string',
                'max_length': 100,
                'description': 'Mailing address'
            },
            'ZIP_CODE': {
                'type': 'string',
                'pattern': r'^\d{5}(-\d{4})?$',
                'description': 'ZIP code'
            },
            
            # SDF (Sales Data File) fields
            'SALE_DATE': {
                'type': 'date',
                'formats': ['%Y%m%d', '%Y-%m-%d', '%m/%d/%Y'],
                'description': 'Sale date'
            },
            'SALE_PRICE': {
                'type': 'numeric',
                'min': 0,
                'max': 9999999999,
                'description': 'Sale price'
            },
            'QUAL_CODE': {
                'type': 'code',
                'valid_codes': ['U', 'Q', 'V', 'W', 'X', 'Y', 'Z'],
                'description': 'Qualification code'
            },
            'OR_BOOK': {
                'type': 'string',
                'max_length': 10,
                'description': 'Official record book'
            },
            'OR_PAGE': {
                'type': 'string',
                'max_length': 10,
                'description': 'Official record page'
            },
            
            # NAP (Non-Ad Valorem Parcel) fields
            'ASSESSMENT_YEAR': {
                'type': 'integer',
                'min': 2000,
                'max': 2050,
                'description': 'Assessment year'
            },
            'TAXABLE_VALUE': {
                'type': 'numeric',
                'min': 0,
                'description': 'Taxable value'
            },
            'EXEMPTION_VALUE': {
                'type': 'numeric',
                'min': 0,
                'description': 'Exemption value'
            },
            
            # General fields
            'COUNTY_CODE': {
                'type': 'string',
                'pattern': r'^\d{2}$',
                'description': 'County code (2 digits)'
            },
            'PHONE': {
                'type': 'string',
                'pattern': r'^[\d\s\-\(\)]+$',
                'max_length': 20,
                'description': 'Phone number'
            },
            'EMAIL': {
                'type': 'string',
                'pattern': r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                'max_length': 100,
                'description': 'Email address'
            },
            'BOOLEAN_FLAG': {
                'type': 'boolean',
                'values': ['Y', 'N', 'YES', 'NO', 'T', 'F', '1', '0'],
                'description': 'Boolean field'
            }
        }
    
    def _build_validation_from_schema(self):
        """Build validation rules from loaded schema"""
        if not self.schema:
            return
        
        # Process field definitions from schema
        for field_def in self.schema.get('field_definitions', []):
            field_name = field_def.get('field_name', '')
            
            if field_name and 'validation' in field_def:
                self.validation_rules[field_name] = field_def['validation']
    
    def validate_file(self, file_path: Path, file_type: Optional[str] = None) -> Dict:
        """
        Validate a Florida Revenue data file
        
        Args:
            file_path: Path to data file
            file_type: Optional file type (NAL, SDF, NAP, NAV, TPP)
            
        Returns:
            Validation results
        """
        if not file_path.exists():
            return {'valid': False, 'error': f"File not found: {file_path}"}
        
        logger.info(f"Validating file: {file_path}")
        
        # Reset errors and warnings
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Determine file type if not provided
        if not file_type:
            file_type = self._determine_file_type(file_path)
        
        # Get schema for this file type
        file_schema = self._get_file_schema(file_type)
        
        # Validate based on file extension
        if file_path.suffix.lower() == '.csv':
            result = self._validate_csv(file_path, file_schema, file_type)
        elif file_path.suffix.lower() in ['.txt', '.dat']:
            result = self._validate_text(file_path, file_schema, file_type)
        elif file_path.suffix.lower() == '.json':
            result = self._validate_json(file_path, file_schema, file_type)
        else:
            # Try to detect format
            result = self._validate_auto_detect(file_path, file_schema, file_type)
        
        # Add summary information
        result['file_type'] = file_type
        result['errors'] = self.errors[:100]  # Limit to first 100 errors
        result['warnings'] = self.warnings[:100]  # Limit to first 100 warnings
        result['info'] = self.info[:10]  # Limit to first 10 info messages
        result['error_count'] = len(self.errors)
        result['warning_count'] = len(self.warnings)
        result['valid'] = len(self.errors) == 0
        
        # Add file statistics
        result['file_stats'] = {
            'size_bytes': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        return result
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine file type from filename"""
        filename = file_path.name.upper()
        
        # Common Florida Revenue file patterns
        if 'NAL' in filename:
            return 'NAL'
        elif 'SDF' in filename:
            return 'SDF'
        elif 'NAP' in filename:
            return 'NAP'
        elif 'NAV' in filename:
            return 'NAV'
        elif 'TPP' in filename:
            return 'TPP'
        
        # Check for county codes (e.g., 06 for Broward)
        if filename.startswith('06'):
            if 'NAL' in filename:
                return 'NAL'
            elif 'SDF' in filename:
                return 'SDF'
        
        # Default based on content
        return self._detect_file_type_from_content(file_path)
    
    def _detect_file_type_from_content(self, file_path: Path) -> str:
        """Detect file type from file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines
                lines = [f.readline() for _ in range(10)]
                content = ' '.join(lines).upper()
                
                # Look for characteristic fields
                if 'OWNER' in content or 'MAILING' in content:
                    return 'NAL'
                elif 'SALE' in content or 'QUAL' in content:
                    return 'SDF'
                elif 'ASSESSMENT' in content:
                    return 'NAV'
                elif 'TANGIBLE' in content:
                    return 'TPP'
        except:
            pass
        
        return 'UNKNOWN'
    
    def _get_file_schema(self, file_type: str) -> Dict:
        """Get schema for specific file type"""
        if file_type in self.file_schemas:
            return self.file_schemas[file_type]
        
        # Return empty schema if not found
        return {'fields': []}
    
    def _validate_csv(self, file_path: Path, schema: Dict, file_type: str) -> Dict:
        """Validate CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                if reader.fieldnames:
                    self._validate_headers(reader.fieldnames, schema, file_type)
                
                # Validate rows
                row_count = 0
                sample_errors = 0
                
                for row_num, row in enumerate(reader, 1):
                    row_count += 1
                    
                    # Validate row
                    row_errors = self._validate_row(row, schema, file_type, row_num)
                    
                    # Sample errors to avoid memory issues
                    if row_errors and sample_errors < 100:
                        sample_errors += 1
                    
                    # Progress reporting for large files
                    if row_count % 10000 == 0:
                        self.info.append(f"Validated {row_count:,} rows...")
                    
                    # Limit validation for very large files
                    if row_count >= 100000:
                        self.info.append(f"Validation limited to first 100,000 rows")
                        break
                
                return {
                    'format': 'csv',
                    'rows_validated': row_count,
                    'headers': reader.fieldnames
                }
                
        except Exception as e:
            self.errors.append(f"Failed to validate CSV: {e}")
            return {'format': 'csv', 'error': str(e)}
    
    def _validate_text(self, file_path: Path, schema: Dict, file_type: str) -> Dict:
        """Validate text file (fixed-width or delimited)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Detect format
            if len(lines) > 0:
                first_line = lines[0]
                
                # Check if delimited
                if '\t' in first_line:
                    delimiter = '\t'
                    format_type = 'tab-delimited'
                elif '|' in first_line:
                    delimiter = '|'
                    format_type = 'pipe-delimited'
                else:
                    # Assume fixed-width
                    delimiter = None
                    format_type = 'fixed-width'
                
                row_count = 0
                for line_num, line in enumerate(lines, 1):
                    if not line.strip():
                        continue
                    
                    row_count += 1
                    
                    if delimiter:
                        # Parse delimited
                        parts = line.strip().split(delimiter)
                        self._validate_delimited_line(parts, schema, file_type, line_num)
                    else:
                        # Parse fixed-width
                        self._validate_fixed_width_line(line, schema, file_type, line_num)
                    
                    # Limit validation
                    if row_count >= 100000:
                        self.info.append(f"Validation limited to first 100,000 lines")
                        break
                
                return {
                    'format': format_type,
                    'rows_validated': row_count
                }
                
        except Exception as e:
            self.errors.append(f"Failed to validate text file: {e}")
            return {'format': 'text', 'error': str(e)}
    
    def _validate_json(self, file_path: Path, schema: Dict, file_type: str) -> Dict:
        """Validate JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate structure
            record_count = 0
            
            if isinstance(data, list):
                for i, record in enumerate(data[:100000]):
                    record_count += 1
                    self._validate_record(record, schema, file_type, i + 1)
                    
            elif isinstance(data, dict):
                if 'records' in data:
                    for i, record in enumerate(data['records'][:100000]):
                        record_count += 1
                        self._validate_record(record, schema, file_type, i + 1)
                else:
                    record_count = 1
                    self._validate_record(data, schema, file_type, 1)
            
            return {
                'format': 'json',
                'records_validated': record_count
            }
            
        except Exception as e:
            self.errors.append(f"Failed to validate JSON: {e}")
            return {'format': 'json', 'error': str(e)}
    
    def _validate_auto_detect(self, file_path: Path, schema: Dict, file_type: str) -> Dict:
        """Auto-detect format and validate"""
        try:
            # Try CSV first
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(1024)
            
            # Check for common delimiters
            if ',' in sample and sample.count(',') > 5:
                return self._validate_csv(file_path, schema, file_type)
            elif '\t' in sample:
                return self._validate_text(file_path, schema, file_type)
            else:
                # Default to text
                return self._validate_text(file_path, schema, file_type)
                
        except Exception as e:
            return {'format': 'unknown', 'error': str(e)}
    
    def _validate_headers(self, headers: List[str], schema: Dict, file_type: str):
        """Validate file headers against schema"""
        if not schema.get('fields'):
            self.info.append(f"No schema defined for {file_type}")
            return
        
        expected_fields = {f.get('field_name', '') for f in schema['fields']}
        actual_fields = set(headers)
        
        # Check for missing required fields
        required_fields = {f.get('field_name', '') 
                          for f in schema['fields'] 
                          if f.get('validation', {}).get('required')}
        
        missing_required = required_fields - actual_fields
        if missing_required:
            self.errors.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Check for extra fields
        extra_fields = actual_fields - expected_fields
        if extra_fields and len(extra_fields) < 10:
            self.warnings.append(f"Extra fields not in schema: {', '.join(list(extra_fields)[:10])}")
    
    def _validate_row(self, row: Dict, schema: Dict, file_type: str, row_num: int) -> int:
        """Validate a single row"""
        error_count = 0
        
        for field_def in schema.get('fields', []):
            field_name = field_def.get('field_name', '')
            
            if field_name in row:
                value = row[field_name]
                
                # Get validation rules
                validation = field_def.get('validation', {})
                if not validation and field_name in self.validation_rules:
                    validation = self.validation_rules[field_name]
                
                # Validate field value
                if validation:
                    is_valid, error_msg = self._validate_field_value(value, validation, field_name)
                    if not is_valid:
                        if error_count < 10:  # Limit errors per row
                            self.errors.append(f"Row {row_num}, {field_name}: {error_msg}")
                        error_count += 1
        
        return error_count
    
    def _validate_record(self, record: Dict, schema: Dict, file_type: str, record_num: int):
        """Validate a JSON record"""
        self._validate_row(record, schema, file_type, record_num)
    
    def _validate_delimited_line(self, parts: List[str], schema: Dict, file_type: str, line_num: int):
        """Validate delimited line"""
        # Map parts to fields based on position
        if schema.get('fields'):
            for i, field_def in enumerate(schema['fields']):
                if i < len(parts):
                    value = parts[i]
                    field_name = field_def.get('field_name', f'field_{i}')
                    
                    validation = field_def.get('validation', {})
                    if validation:
                        is_valid, error_msg = self._validate_field_value(value, validation, field_name)
                        if not is_valid:
                            self.errors.append(f"Line {line_num}, {field_name}: {error_msg}")
    
    def _validate_fixed_width_line(self, line: str, schema: Dict, file_type: str, line_num: int):
        """Validate fixed-width format line"""
        for field_def in schema.get('fields', []):
            start_pos = field_def.get('start_pos')
            end_pos = field_def.get('end_pos')
            field_name = field_def.get('field_name', '')
            
            if start_pos and end_pos:
                try:
                    start = int(start_pos) - 1  # Convert to 0-based
                    end = int(end_pos)
                    
                    if len(line) >= end:
                        value = line[start:end].strip()
                        
                        validation = field_def.get('validation', {})
                        if validation:
                            is_valid, error_msg = self._validate_field_value(value, validation, field_name)
                            if not is_valid:
                                self.errors.append(f"Line {line_num}, {field_name}: {error_msg}")
                        
                except (ValueError, IndexError) as e:
                    self.warnings.append(f"Line {line_num}: Could not extract field '{field_name}': {e}")
    
    def _validate_field_value(self, value: Any, validation: Dict, field_name: str) -> Tuple[bool, str]:
        """
        Validate individual field value
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value and validation.get('required'):
            return False, "Required field is empty"
        
        if not value:
            return True, ""
        
        value_str = str(value).strip()
        
        # Type validation
        val_type = validation.get('type', '')
        
        if val_type == 'string':
            if 'pattern' in validation:
                if not re.match(validation['pattern'], value_str):
                    return False, f"Value '{value_str}' doesn't match pattern {validation['pattern']}"
            
            if 'max_length' in validation:
                if len(value_str) > validation['max_length']:
                    return False, f"Value exceeds max length of {validation['max_length']}"
        
        elif val_type in ['numeric', 'integer', 'currency']:
            try:
                # Remove common formatting
                clean_value = value_str.replace(',', '').replace('$', '')
                num_value = float(clean_value)
                
                if val_type == 'integer' and not clean_value.replace('-', '').isdigit():
                    return False, f"Value '{value_str}' is not an integer"
                
                if 'min' in validation and num_value < validation['min']:
                    return False, f"Value {num_value} is below minimum {validation['min']}"
                
                if 'max' in validation and num_value > validation['max']:
                    return False, f"Value {num_value} exceeds maximum {validation['max']}"
                    
            except ValueError:
                return False, f"Invalid numeric value: {value_str}"
        
        elif val_type == 'date':
            valid_date = False
            for fmt in validation.get('formats', ['%Y%m%d']):
                try:
                    datetime.strptime(value_str, fmt)
                    valid_date = True
                    break
                except ValueError:
                    continue
            
            if not valid_date:
                return False, f"Invalid date format: {value_str}"
        
        elif val_type == 'boolean':
            valid_values = validation.get('values', ['Y', 'N'])
            if value_str.upper() not in valid_values:
                return False, f"Invalid boolean value: {value_str} (expected: {', '.join(valid_values)})"
        
        elif val_type == 'code':
            valid_codes = validation.get('valid_codes', [])
            if valid_codes and value_str not in valid_codes:
                return False, f"Invalid code: {value_str} (expected: {', '.join(valid_codes)})"
        
        elif val_type == 'parcel_id':
            if 'pattern' in validation:
                if not re.match(validation['pattern'], value_str):
                    return False, f"Invalid parcel ID format: {value_str}"
        
        elif val_type == 'zip_code':
            if 'pattern' in validation:
                if not re.match(validation['pattern'], value_str):
                    return False, f"Invalid ZIP code format: {value_str}"
        
        elif val_type == 'email':
            if 'pattern' in validation:
                if not re.match(validation['pattern'], value_str, re.IGNORECASE):
                    return False, f"Invalid email format: {value_str}"
        
        elif val_type == 'phone':
            if 'pattern' in validation:
                if not re.match(validation['pattern'], value_str):
                    return False, f"Invalid phone format: {value_str}"
        
        return True, ""
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation results"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors[:10],  # First 10 errors
            'warnings': self.warnings[:10],  # First 10 warnings
            'info': self.info,
            'valid': len(self.errors) == 0
        }


if __name__ == "__main__":
    import sys
    
    # Test the validator
    validator = FloridaRevenueDataValidator()
    
    # Load schema if available
    schema_path = Path("data/florida_revenue_guide/extracted/schema.json")
    if schema_path.exists():
        validator.load_schema(schema_path)
        print(f"Loaded schema from {schema_path}")
    
    # Test validation on a file if provided
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            result = validator.validate_file(test_file)
            print(f"\nValidation Result for {test_file.name}:")
            print(json.dumps(result, indent=2))
        else:
            print(f"File not found: {test_file}")
    else:
        print("Usage: python data_validator.py <data_file>")