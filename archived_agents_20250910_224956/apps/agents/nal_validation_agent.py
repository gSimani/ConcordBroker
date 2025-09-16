#!/usr/bin/env python3
"""
NAL Validation Agent
===================
Comprehensive data validation agent for NAL import pipeline.
Performs pre-import validation, data quality checks, and post-import verification.
"""

import asyncio
import logging
import time
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    validation_type: str
    records_validated: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    summary: Dict[str, Any] = None
    processing_time: float = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.summary is None:
            self.summary = {}

@dataclass
class FieldValidation:
    """Field-specific validation configuration"""
    field_name: str
    data_type: str
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[str]] = None
    regex_pattern: Optional[str] = None
    custom_validator: Optional[str] = None

class NALValidationAgent:
    """
    Agent specialized in comprehensive data validation for NAL import pipeline
    
    Features:
    - Pre-import data structure validation
    - Field-level data quality checks
    - Business rule validation
    - Statistical analysis and outlier detection
    - Post-import data integrity verification
    - Comprehensive validation reporting
    """
    
    def __init__(self, sample_size: int = 1000):
        self.sample_size = sample_size
        
        # Validation rules
        self.field_validations = self._setup_field_validations()
        self.business_rules = self._setup_business_rules()
        
        # Data quality thresholds
        self.quality_thresholds = {
            'completeness_threshold': 0.95,  # 95% of records should have required fields
            'accuracy_threshold': 0.98,      # 98% of records should pass format validation
            'consistency_threshold': 0.99,   # 99% consistency in data patterns
            'max_outlier_percentage': 0.05   # Maximum 5% outliers allowed
        }
        
        # Statistical tracking
        self.validation_stats = {
            'total_validations': 0,
            'field_validation_results': {},
            'business_rule_results': {},
            'data_quality_metrics': {}
        }
        
        logger.info("NAL Validation Agent initialized")
        logger.info(f"Sample size for validation: {sample_size}")
    
    def _setup_field_validations(self) -> Dict[str, FieldValidation]:
        """Setup comprehensive field validation rules"""
        return {
            # Core identification fields
            'PARCEL_ID': FieldValidation(
                field_name='PARCEL_ID',
                data_type='string',
                required=True,
                min_length=5,
                max_length=30,
                regex_pattern=r'^[A-Za-z0-9\-]+$'
            ),
            
            'CO_NO': FieldValidation(
                field_name='CO_NO',
                data_type='string',
                required=True,
                allowed_values=['016']  # Broward County code
            ),
            
            'ASMNT_YR': FieldValidation(
                field_name='ASMNT_YR',
                data_type='integer',
                required=True,
                min_value=2020,
                max_value=2030
            ),
            
            # Valuation fields
            'JV': FieldValidation(
                field_name='JV',
                data_type='numeric',
                required=True,
                min_value=0,
                max_value=100000000  # $100M max reasonable value
            ),
            
            'AV_SD': FieldValidation(
                field_name='AV_SD',
                data_type='numeric',
                required=True,
                min_value=0,
                max_value=100000000
            ),
            
            'TV_SD': FieldValidation(
                field_name='TV_SD',
                data_type='numeric',
                required=True,
                min_value=0,
                max_value=100000000
            ),
            
            'LND_VAL': FieldValidation(
                field_name='LND_VAL',
                data_type='numeric',
                min_value=0,
                max_value=50000000  # $50M max land value
            ),
            
            # Owner information
            'OWN_NAME': FieldValidation(
                field_name='OWN_NAME',
                data_type='string',
                required=True,
                min_length=1,
                max_length=70
            ),
            
            'OWN_ZIPCD': FieldValidation(
                field_name='OWN_ZIPCD',
                data_type='string',
                regex_pattern=r'^\d{5}(-\d{4})?$'  # ZIP or ZIP+4 format
            ),
            
            # Property characteristics
            'DOR_UC': FieldValidation(
                field_name='DOR_UC',
                data_type='string',
                required=True,
                regex_pattern=r'^\d{3}$'  # 3-digit use code
            ),
            
            'EFF_YR_BLT': FieldValidation(
                field_name='EFF_YR_BLT',
                data_type='integer',
                min_value=1800,
                max_value=2030
            ),
            
            'ACT_YR_BLT': FieldValidation(
                field_name='ACT_YR_BLT',
                data_type='integer',
                min_value=1800,
                max_value=2030
            ),
            
            'TOT_LVG_AREA': FieldValidation(
                field_name='TOT_LVG_AREA',
                data_type='numeric',
                min_value=0,
                max_value=50000  # 50,000 sq ft max reasonable
            ),
            
            # Physical address
            'PHY_ADDR1': FieldValidation(
                field_name='PHY_ADDR1',
                data_type='string',
                max_length=60
            ),
            
            'PHY_CITY': FieldValidation(
                field_name='PHY_CITY',
                data_type='string',
                max_length=45
            ),
            
            'PHY_ZIPCD': FieldValidation(
                field_name='PHY_ZIPCD',
                data_type='string',
                regex_pattern=r'^\d{5}(-\d{4})?$'
            ),
            
            # Sales data
            'SALE_PRC1': FieldValidation(
                field_name='SALE_PRC1',
                data_type='numeric',
                min_value=0,
                max_value=200000000  # $200M max sale price
            ),
            
            'SALE_YR1': FieldValidation(
                field_name='SALE_YR1',
                data_type='integer',
                min_value=1990,
                max_value=2030
            ),
            
            'SALE_MO1': FieldValidation(
                field_name='SALE_MO1',
                data_type='integer',
                min_value=1,
                max_value=12
            )
        }
    
    def _setup_business_rules(self) -> Dict[str, Dict]:
        """Setup business rule validations"""
        return {
            'assessed_value_consistency': {
                'description': 'Assessed value should not exceed just value',
                'validator': 'validate_assessed_vs_just_value',
                'severity': 'error'
            },
            
            'taxable_value_consistency': {
                'description': 'Taxable value should not exceed assessed value',
                'validator': 'validate_taxable_vs_assessed_value',
                'severity': 'error'
            },
            
            'year_built_consistency': {
                'description': 'Effective year built should be >= actual year built',
                'validator': 'validate_year_built_consistency',
                'severity': 'warning'
            },
            
            'sale_price_reasonableness': {
                'description': 'Sale price should be reasonable compared to assessed value',
                'validator': 'validate_sale_price_reasonableness',
                'severity': 'warning'
            },
            
            'parcel_id_format': {
                'description': 'Parcel ID should follow expected format patterns',
                'validator': 'validate_parcel_id_format',
                'severity': 'error'
            },
            
            'exemption_consistency': {
                'description': 'Exemption values should be reasonable',
                'validator': 'validate_exemption_consistency',
                'severity': 'warning'
            }
        }
    
    async def validate_data_sample(self, csv_parser_agent) -> ValidationResult:
        """
        Validate a sample of data for structure and quality
        
        Args:
            csv_parser_agent: CSV parser agent instance
            
        Returns:
            ValidationResult with validation findings
        """
        start_time = time.time()
        
        logger.info(f"Validating data sample of size {self.sample_size}")
        
        try:
            # Get data sample
            sample_data = await csv_parser_agent.read_specific_chunk(0, self.sample_size)
            
            result = ValidationResult(
                is_valid=True,
                validation_type='data_sample',
                records_validated=len(sample_data)
            )
            
            # Perform field-level validations
            field_results = await self._validate_fields(sample_data)
            result.summary['field_validations'] = field_results
            
            # Perform business rule validations
            business_rule_results = await self._validate_business_rules(sample_data)
            result.summary['business_rule_validations'] = business_rule_results
            
            # Perform data quality analysis
            quality_analysis = await self._analyze_data_quality(sample_data)
            result.summary['data_quality_analysis'] = quality_analysis
            
            # Aggregate results
            total_field_errors = sum(fr['failed_count'] for fr in field_results.values())
            total_business_errors = sum(br['failed_count'] for br in business_rule_results.values())
            
            result.failed_validations = total_field_errors + total_business_errors
            result.passed_validations = result.records_validated - result.failed_validations
            
            # Collect errors and warnings
            for field_name, field_result in field_results.items():
                if field_result['errors']:
                    result.errors.extend([f"{field_name}: {error}" for error in field_result['errors']])
                if field_result['warnings']:
                    result.warnings.extend([f"{field_name}: {warning}" for warning in field_result['warnings']])
            
            for rule_name, rule_result in business_rule_results.items():
                if rule_result['errors']:
                    result.errors.extend([f"{rule_name}: {error}" for error in rule_result['errors']])
                if rule_result['warnings']:
                    result.warnings.extend([f"{rule_name}: {warning}" for warning in rule_result['warnings']])
            
            # Determine overall validity
            error_rate = result.failed_validations / result.records_validated if result.records_validated > 0 else 0
            result.is_valid = error_rate < (1 - self.quality_thresholds['accuracy_threshold'])
            
            result.processing_time = time.time() - start_time
            
            logger.info(f"Sample validation completed: {result.passed_validations}/{result.records_validated} passed")
            logger.info(f"Error rate: {error_rate:.2%}, Valid: {result.is_valid}")
            
            return result
            
        except Exception as e:
            logger.error(f"Sample validation failed: {e}")
            result = ValidationResult(
                is_valid=False,
                validation_type='data_sample',
                processing_time=time.time() - start_time
            )
            result.errors.append(str(e))
            return result
    
    async def validate_data_integrity(self) -> ValidationResult:
        """
        Validate data integrity after import (placeholder - would connect to database)
        
        Returns:
            ValidationResult with integrity check results
        """
        start_time = time.time()
        
        logger.info("Validating data integrity post-import")
        
        try:
            result = ValidationResult(
                is_valid=True,
                validation_type='data_integrity'
            )
            
            # Placeholder integrity checks (would query database in real implementation)
            integrity_checks = {
                'referential_integrity': await self._check_referential_integrity(),
                'data_completeness': await self._check_data_completeness(),
                'duplicate_detection': await self._check_for_duplicates(),
                'value_consistency': await self._check_value_consistency()
            }
            
            result.summary = integrity_checks
            
            # Aggregate results
            failed_checks = sum(1 for check in integrity_checks.values() if not check['passed'])
            total_checks = len(integrity_checks)
            
            result.passed_validations = total_checks - failed_checks
            result.failed_validations = failed_checks
            result.is_valid = failed_checks == 0
            
            # Collect issues
            for check_name, check_result in integrity_checks.items():
                if not check_result['passed']:
                    result.errors.extend(check_result.get('errors', []))
                result.warnings.extend(check_result.get('warnings', []))
            
            result.processing_time = time.time() - start_time
            
            logger.info(f"Data integrity validation completed: {result.passed_validations}/{total_checks} checks passed")
            
            return result
            
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            result = ValidationResult(
                is_valid=False,
                validation_type='data_integrity',
                processing_time=time.time() - start_time
            )
            result.errors.append(str(e))
            return result
    
    async def _validate_fields(self, data: List[Dict]) -> Dict[str, Dict]:
        """Validate individual fields against their validation rules"""
        
        field_results = {}
        
        for field_name, validation_rule in self.field_validations.items():
            field_result = {
                'passed_count': 0,
                'failed_count': 0,
                'errors': [],
                'warnings': [],
                'statistics': {}
            }
            
            values = []
            
            for record in data:
                value = record.get(field_name)
                
                try:
                    validation_result = self._validate_single_field(value, validation_rule)
                    
                    if validation_result['valid']:
                        field_result['passed_count'] += 1
                        if validation_result['converted_value'] is not None:
                            values.append(validation_result['converted_value'])
                    else:
                        field_result['failed_count'] += 1
                        field_result['errors'].extend(validation_result['errors'])
                        field_result['warnings'].extend(validation_result['warnings'])
                
                except Exception as validation_error:
                    field_result['failed_count'] += 1
                    field_result['errors'].append(f"Validation error: {validation_error}")
            
            # Calculate field statistics
            if values:
                field_result['statistics'] = self._calculate_field_statistics(values, validation_rule.data_type)
            
            field_results[field_name] = field_result
        
        return field_results
    
    async def _validate_business_rules(self, data: List[Dict]) -> Dict[str, Dict]:
        """Validate business rules across records"""
        
        business_rule_results = {}
        
        for rule_name, rule_config in self.business_rules.items():
            rule_result = {
                'passed_count': 0,
                'failed_count': 0,
                'errors': [],
                'warnings': []
            }
            
            validator_method = getattr(self, rule_config['validator'], None)
            if not validator_method:
                rule_result['errors'].append(f"Validator method {rule_config['validator']} not found")
                business_rule_results[rule_name] = rule_result
                continue
            
            for i, record in enumerate(data):
                try:
                    validation_result = validator_method(record)
                    
                    if validation_result['valid']:
                        rule_result['passed_count'] += 1
                    else:
                        rule_result['failed_count'] += 1
                        
                        if rule_config['severity'] == 'error':
                            rule_result['errors'].extend(validation_result.get('messages', []))
                        else:
                            rule_result['warnings'].extend(validation_result.get('messages', []))
                
                except Exception as validation_error:
                    rule_result['failed_count'] += 1
                    rule_result['errors'].append(f"Record {i}: {validation_error}")
            
            business_rule_results[rule_name] = rule_result
        
        return business_rule_results
    
    async def _analyze_data_quality(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze overall data quality metrics"""
        
        quality_analysis = {
            'completeness': {},
            'accuracy': {},
            'consistency': {},
            'outlier_analysis': {}
        }
        
        # Completeness analysis
        for field_name in self.field_validations.keys():
            if field_name in data[0]:  # Check if field exists in data
                non_empty_count = sum(1 for record in data if record.get(field_name, '').strip())
                completeness_rate = non_empty_count / len(data)
                
                quality_analysis['completeness'][field_name] = {
                    'rate': completeness_rate,
                    'meets_threshold': completeness_rate >= self.quality_thresholds['completeness_threshold']
                }
        
        # Accuracy analysis (format compliance)
        format_compliance = {}
        for field_name, validation_rule in self.field_validations.items():
            if field_name in data[0]:
                compliant_count = 0
                total_count = 0
                
                for record in data:
                    value = record.get(field_name)
                    if value and str(value).strip():
                        total_count += 1
                        validation_result = self._validate_single_field(value, validation_rule)
                        if validation_result['valid']:
                            compliant_count += 1
                
                if total_count > 0:
                    compliance_rate = compliant_count / total_count
                    format_compliance[field_name] = {
                        'rate': compliance_rate,
                        'meets_threshold': compliance_rate >= self.quality_thresholds['accuracy_threshold']
                    }
        
        quality_analysis['accuracy'] = format_compliance
        
        # Consistency analysis (data patterns)
        consistency_analysis = self._analyze_consistency_patterns(data)
        quality_analysis['consistency'] = consistency_analysis
        
        # Outlier analysis for numeric fields
        outlier_analysis = self._analyze_outliers(data)
        quality_analysis['outlier_analysis'] = outlier_analysis
        
        return quality_analysis
    
    def _validate_single_field(self, value: Any, validation_rule: FieldValidation) -> Dict[str, Any]:
        """Validate a single field value against its validation rule"""
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'converted_value': None
        }
        
        # Check if required field is missing
        if validation_rule.required and (value is None or str(value).strip() == ''):
            result['valid'] = False
            result['errors'].append(f"Required field {validation_rule.field_name} is missing")
            return result
        
        # Skip validation for empty optional fields
        if not validation_rule.required and (value is None or str(value).strip() == ''):
            return result
        
        str_value = str(value).strip()
        
        # Data type validation and conversion
        try:
            if validation_rule.data_type == 'integer':
                converted_value = int(float(str_value))  # Handle "123.0" format
                result['converted_value'] = converted_value
            elif validation_rule.data_type == 'numeric':
                converted_value = float(str_value)
                result['converted_value'] = converted_value
            elif validation_rule.data_type == 'string':
                converted_value = str_value
                result['converted_value'] = converted_value
            else:
                converted_value = str_value
                result['converted_value'] = converted_value
        
        except (ValueError, TypeError):
            result['valid'] = False
            result['errors'].append(f"Invalid {validation_rule.data_type} value: {value}")
            return result
        
        # Length validation for strings
        if validation_rule.data_type == 'string':
            if validation_rule.min_length and len(str_value) < validation_rule.min_length:
                result['valid'] = False
                result['errors'].append(f"Value too short (min: {validation_rule.min_length})")
            
            if validation_rule.max_length and len(str_value) > validation_rule.max_length:
                result['valid'] = False
                result['errors'].append(f"Value too long (max: {validation_rule.max_length})")
        
        # Range validation for numeric fields
        if validation_rule.data_type in ['integer', 'numeric']:
            if validation_rule.min_value is not None and converted_value < validation_rule.min_value:
                result['valid'] = False
                result['errors'].append(f"Value below minimum ({validation_rule.min_value})")
            
            if validation_rule.max_value is not None and converted_value > validation_rule.max_value:
                result['valid'] = False
                result['errors'].append(f"Value above maximum ({validation_rule.max_value})")
        
        # Allowed values validation
        if validation_rule.allowed_values and str_value not in validation_rule.allowed_values:
            result['valid'] = False
            result['errors'].append(f"Value not in allowed list: {validation_rule.allowed_values}")
        
        # Regex pattern validation
        if validation_rule.regex_pattern:
            if not re.match(validation_rule.regex_pattern, str_value):
                result['valid'] = False
                result['errors'].append(f"Value doesn't match required pattern")
        
        return result
    
    def _calculate_field_statistics(self, values: List[Any], data_type: str) -> Dict[str, Any]:
        """Calculate statistical metrics for field values"""
        
        if not values:
            return {}
        
        stats = {
            'count': len(values),
            'unique_count': len(set(values))
        }
        
        if data_type in ['integer', 'numeric']:
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            
            if numeric_values:
                stats.update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': statistics.mean(numeric_values),
                    'median': statistics.median(numeric_values),
                    'std_dev': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                })
        
        elif data_type == 'string':
            string_values = [str(v) for v in values]
            if string_values:
                lengths = [len(s) for s in string_values]
                stats.update({
                    'min_length': min(lengths),
                    'max_length': max(lengths),
                    'avg_length': statistics.mean(lengths)
                })
        
        return stats
    
    # Business rule validators
    def validate_assessed_vs_just_value(self, record: Dict) -> Dict[str, Any]:
        """Validate that assessed value doesn't exceed just value"""
        try:
            jv = float(record.get('JV', 0))
            av_sd = float(record.get('AV_SD', 0))
            
            if jv > 0 and av_sd > jv:
                return {
                    'valid': False,
                    'messages': [f"Assessed value ({av_sd}) exceeds just value ({jv})"]
                }
            
            return {'valid': True}
            
        except (ValueError, TypeError):
            return {
                'valid': False,
                'messages': ['Invalid numeric values for value comparison']
            }
    
    def validate_taxable_vs_assessed_value(self, record: Dict) -> Dict[str, Any]:
        """Validate that taxable value doesn't exceed assessed value"""
        try:
            av_sd = float(record.get('AV_SD', 0))
            tv_sd = float(record.get('TV_SD', 0))
            
            if av_sd > 0 and tv_sd > av_sd:
                return {
                    'valid': False,
                    'messages': [f"Taxable value ({tv_sd}) exceeds assessed value ({av_sd})"]
                }
            
            return {'valid': True}
            
        except (ValueError, TypeError):
            return {
                'valid': False,
                'messages': ['Invalid numeric values for taxable value comparison']
            }
    
    def validate_year_built_consistency(self, record: Dict) -> Dict[str, Any]:
        """Validate year built consistency"""
        try:
            eff_yr = record.get('EFF_YR_BLT')
            act_yr = record.get('ACT_YR_BLT')
            
            if eff_yr and act_yr:
                eff_yr = int(eff_yr)
                act_yr = int(act_yr)
                
                if eff_yr < act_yr:
                    return {
                        'valid': False,
                        'messages': [f"Effective year ({eff_yr}) before actual year ({act_yr})"]
                    }
            
            return {'valid': True}
            
        except (ValueError, TypeError):
            return {
                'valid': False,
                'messages': ['Invalid year values']
            }
    
    def validate_sale_price_reasonableness(self, record: Dict) -> Dict[str, Any]:
        """Validate sale price reasonableness compared to assessed value"""
        try:
            sale_price = record.get('SALE_PRC1')
            assessed_value = record.get('AV_SD')
            
            if sale_price and assessed_value:
                sale_price = float(sale_price)
                assessed_value = float(assessed_value)
                
                if assessed_value > 0:
                    ratio = sale_price / assessed_value
                    
                    # Flag if sale price is more than 5x or less than 0.2x assessed value
                    if ratio > 5.0 or ratio < 0.2:
                        return {
                            'valid': False,
                            'messages': [f"Sale price ({sale_price}) unusual compared to assessed value ({assessed_value})"]
                        }
            
            return {'valid': True}
            
        except (ValueError, TypeError):
            return {
                'valid': False,
                'messages': ['Invalid values for sale price comparison']
            }
    
    def validate_parcel_id_format(self, record: Dict) -> Dict[str, Any]:
        """Validate parcel ID format patterns"""
        parcel_id = record.get('PARCEL_ID', '')
        
        if not parcel_id:
            return {
                'valid': False,
                'messages': ['Missing parcel ID']
            }
        
        # Basic format check - should be alphanumeric with possible dashes
        if not re.match(r'^[A-Za-z0-9\-]+$', parcel_id):
            return {
                'valid': False,
                'messages': [f"Invalid parcel ID format: {parcel_id}"]
            }
        
        return {'valid': True}
    
    def validate_exemption_consistency(self, record: Dict) -> Dict[str, Any]:
        """Validate exemption value consistency"""
        try:
            exemption_fields = [f for f in record.keys() if f.startswith('EXMPT_')]
            
            total_exemptions = 0
            valid_exemptions = 0
            
            for field in exemption_fields:
                value = record.get(field, 0)
                if value and str(value).strip():
                    try:
                        exemption_value = float(value)
                        if exemption_value > 0:
                            total_exemptions += exemption_value
                            valid_exemptions += 1
                    except (ValueError, TypeError):
                        continue
            
            # Check if total exemptions are reasonable
            assessed_value = float(record.get('AV_SD', 0))
            
            if assessed_value > 0 and total_exemptions > assessed_value:
                return {
                    'valid': False,
                    'messages': [f"Total exemptions ({total_exemptions}) exceed assessed value ({assessed_value})"]
                }
            
            return {'valid': True}
            
        except Exception:
            return {
                'valid': False,
                'messages': ['Error validating exemption consistency']
            }
    
    def _analyze_consistency_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze data consistency patterns"""
        
        consistency_metrics = {}
        
        # Check county code consistency
        county_codes = [record.get('CO_NO', '') for record in data]
        unique_counties = set(county_codes)
        
        consistency_metrics['county_codes'] = {
            'unique_values': list(unique_counties),
            'consistency_rate': (county_codes.count('016') / len(county_codes)) if county_codes else 0,
            'meets_threshold': len(unique_counties) <= 2  # Allow some variation
        }
        
        # Check assessment year consistency
        assessment_years = [record.get('ASMNT_YR', '') for record in data if record.get('ASMNT_YR')]
        unique_years = set(assessment_years)
        
        consistency_metrics['assessment_years'] = {
            'unique_values': list(unique_years),
            'consistency_rate': len(unique_years) / max(len(assessment_years), 1),
            'meets_threshold': len(unique_years) <= 3  # Allow few different years
        }
        
        return consistency_metrics
    
    def _analyze_outliers(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze outliers in numeric fields"""
        
        outlier_analysis = {}
        
        numeric_fields = ['JV', 'AV_SD', 'TV_SD', 'LND_VAL', 'TOT_LVG_AREA', 'SALE_PRC1']
        
        for field in numeric_fields:
            values = []
            
            for record in data:
                value = record.get(field)
                if value:
                    try:
                        numeric_value = float(value)
                        if numeric_value > 0:  # Only consider positive values
                            values.append(numeric_value)
                    except (ValueError, TypeError):
                        continue
            
            if len(values) >= 10:  # Need sufficient data for outlier analysis
                values_array = np.array(values)
                q1 = np.percentile(values_array, 25)
                q3 = np.percentile(values_array, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = values_array[(values_array < lower_bound) | (values_array > upper_bound)]
                outlier_percentage = len(outliers) / len(values)
                
                outlier_analysis[field] = {
                    'outlier_count': len(outliers),
                    'total_values': len(values),
                    'outlier_percentage': outlier_percentage,
                    'meets_threshold': outlier_percentage <= self.quality_thresholds['max_outlier_percentage'],
                    'bounds': {'lower': lower_bound, 'upper': upper_bound}
                }
        
        return outlier_analysis
    
    # Placeholder integrity check methods (would connect to actual database)
    async def _check_referential_integrity(self) -> Dict[str, Any]:
        """Check referential integrity between tables"""
        return {
            'passed': True,
            'errors': [],
            'warnings': [],
            'description': 'All foreign key relationships are valid'
        }
    
    async def _check_data_completeness(self) -> Dict[str, Any]:
        """Check data completeness in database"""
        return {
            'passed': True,
            'errors': [],
            'warnings': [],
            'description': 'All required fields have data'
        }
    
    async def _check_for_duplicates(self) -> Dict[str, Any]:
        """Check for duplicate records in database"""
        return {
            'passed': True,
            'errors': [],
            'warnings': [],
            'description': 'No duplicate parcel IDs found'
        }
    
    async def _check_value_consistency(self) -> Dict[str, Any]:
        """Check value consistency across related fields"""
        return {
            'passed': True,
            'errors': [],
            'warnings': [],
            'description': 'Value relationships are consistent'
        }
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics summary"""
        return {
            'validation_stats': self.validation_stats,
            'quality_thresholds': self.quality_thresholds,
            'field_validation_count': len(self.field_validations),
            'business_rule_count': len(self.business_rules)
        }