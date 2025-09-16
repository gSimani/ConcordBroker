#!/usr/bin/env python3
"""
NAL Field Mapping Agent
======================
Comprehensive mapping agent for all 165 NAL fields to optimized 7-table structure.
Handles data type conversions, validation, and transformation logic.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

logger = logging.getLogger(__name__)

@dataclass
class FieldMapping:
    """Represents a field mapping configuration"""
    source_field: str
    target_table: str
    target_field: str
    data_type: str
    conversion_function: str = None
    validation_rules: List[str] = None
    is_required: bool = False
    default_value: Any = None

class NALMappingAgent:
    """
    Agent responsible for mapping all 165 NAL fields to the 7-table database structure.
    Includes comprehensive data transformation and validation logic.
    """
    
    def __init__(self):
        self.comprehensive_mapping = self._create_comprehensive_mapping()
        self.conversion_functions = self._setup_conversion_functions()
        self.validation_rules = self._setup_validation_rules()
        
        logger.info("NAL Mapping Agent initialized with 165 field mappings")
    
    def _create_comprehensive_mapping(self) -> Dict[str, List[FieldMapping]]:
        """
        Create comprehensive mapping of all 165 NAL fields to database tables
        """
        return {
            'florida_properties_core': [
                # Core identification fields
                FieldMapping('CO_NO', 'florida_properties_core', 'county_code', 'VARCHAR(3)', 'convert_county_code', is_required=True),
                FieldMapping('PARCEL_ID', 'florida_properties_core', 'parcel_id', 'VARCHAR(30)', 'clean_parcel_id', is_required=True),
                FieldMapping('FILE_T', 'florida_properties_core', 'file_type', 'VARCHAR(5)', 'clean_string', is_required=True),
                FieldMapping('ASMNT_YR', 'florida_properties_core', 'assessment_year', 'INTEGER', 'convert_integer', is_required=True),
                FieldMapping('GRP_NO', 'florida_properties_core', 'group_number', 'INTEGER', 'convert_integer'),
                
                # Physical address fields
                FieldMapping('PHY_ADDR1', 'florida_properties_core', 'physical_address_1', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('PHY_ADDR2', 'florida_properties_core', 'physical_address_2', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('PHY_CITY', 'florida_properties_core', 'physical_city', 'VARCHAR(45)', 'clean_city'),
                FieldMapping('PHY_ZIPCD', 'florida_properties_core', 'physical_zipcode', 'VARCHAR(10)', 'clean_zipcode'),
                
                # Primary owner information
                FieldMapping('OWN_NAME', 'florida_properties_core', 'owner_name', 'VARCHAR(70)', 'clean_owner_name', is_required=True),
                FieldMapping('OWN_ADDR1', 'florida_properties_core', 'owner_address_1', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('OWN_CITY', 'florida_properties_core', 'owner_city', 'VARCHAR(45)', 'clean_city'),
                FieldMapping('OWN_STATE', 'florida_properties_core', 'owner_state', 'VARCHAR(50)', 'clean_state'),
                FieldMapping('OWN_ZIPCD', 'florida_properties_core', 'owner_zipcode', 'VARCHAR(10)', 'clean_zipcode'),
                
                # Property classification
                FieldMapping('DOR_UC', 'florida_properties_core', 'dor_use_code', 'VARCHAR(3)', 'clean_use_code', is_required=True),
                FieldMapping('PA_UC', 'florida_properties_core', 'property_appraiser_use_code', 'VARCHAR(3)', 'clean_use_code'),
                FieldMapping('NBRHD_CD', 'florida_properties_core', 'neighborhood_code', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('TAX_AUTH_CD', 'florida_properties_core', 'tax_authority_code', 'VARCHAR(3)', 'clean_string'),
                
                # Core valuations (most frequently accessed)
                FieldMapping('JV', 'florida_properties_core', 'just_value', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('AV_SD', 'florida_properties_core', 'assessed_value_school_district', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('TV_SD', 'florida_properties_core', 'taxable_value_school_district', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('LND_VAL', 'florida_properties_core', 'land_value', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                
                # Building basics
                FieldMapping('EFF_YR_BLT', 'florida_properties_core', 'year_built', 'INTEGER', 'convert_year'),
                FieldMapping('TOT_LVG_AREA', 'florida_properties_core', 'total_living_area', 'NUMERIC(8,2)', 'convert_numeric'),
                FieldMapping('NO_BULDNG', 'florida_properties_core', 'number_of_buildings', 'INTEGER', 'convert_integer', default_value=0),
                FieldMapping('LND_SQFOOT', 'florida_properties_core', 'land_square_footage', 'NUMERIC(12,0)', 'convert_numeric'),
            ],
            
            'property_valuations': [
                # All detailed valuation fields
                FieldMapping('AV_NSD', 'property_valuations', 'assessed_value_non_school_district', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('TV_NSD', 'property_valuations', 'taxable_value_non_school_district', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                
                # Homestead values
                FieldMapping('JV_HMSTD', 'property_valuations', 'just_value_homestead', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_HMSTD', 'property_valuations', 'assessed_value_homestead', 'NUMERIC(12,2)', 'convert_currency'),
                
                # Non-homestead residential
                FieldMapping('JV_NON_HMSTD_RESD', 'property_valuations', 'just_value_non_homestead_residential', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_NON_HMSTD_RESD', 'property_valuations', 'assessed_value_non_homestead_residential', 'NUMERIC(12,2)', 'convert_currency'),
                
                # Residential/non-residential mix
                FieldMapping('JV_RESD_NON_RESD', 'property_valuations', 'just_value_residential_non_residential', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_RESD_NON_RESD', 'property_valuations', 'assessed_value_residential_non_residential', 'NUMERIC(12,2)', 'convert_currency'),
                
                # Classification use values
                FieldMapping('JV_CLASS_USE', 'property_valuations', 'just_value_classification_use', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_CLASS_USE', 'property_valuations', 'assessed_value_classification_use', 'NUMERIC(12,2)', 'convert_currency'),
                
                # Special land categories
                FieldMapping('JV_H2O_RECHRGE', 'property_valuations', 'just_value_water_recharge', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_H2O_RECHRGE', 'property_valuations', 'assessed_value_water_recharge', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('JV_CONSRV_LND', 'property_valuations', 'just_value_conservation_land', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_CONSRV_LND', 'property_valuations', 'assessed_value_conservation_land', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('JV_HIST_COM_PROP', 'property_valuations', 'just_value_historic_commercial', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_HIST_COM_PROP', 'property_valuations', 'assessed_value_historic_commercial', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('JV_HIST_SIGNF', 'property_valuations', 'just_value_historic_significant', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_HIST_SIGNF', 'property_valuations', 'assessed_value_historic_significant', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('JV_WRKNG_WTRFNT', 'property_valuations', 'just_value_working_waterfront', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('AV_WRKNG_WTRFNT', 'property_valuations', 'assessed_value_working_waterfront', 'NUMERIC(12,2)', 'convert_currency'),
                
                # Value components
                FieldMapping('NCONST_VAL', 'property_valuations', 'new_construction_value', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('DEL_VAL', 'property_valuations', 'deleted_value', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('SPEC_FEAT_VAL', 'property_valuations', 'special_features_value', 'NUMERIC(12,2)', 'convert_currency', default_value=0),
                FieldMapping('YR_VAL_TRNSF', 'property_valuations', 'value_transfer_year', 'INTEGER', 'convert_year'),
                
                # Value change indicators
                FieldMapping('JV_CHNG', 'property_valuations', 'just_value_change_flag', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('JV_CHNG_CD', 'property_valuations', 'just_value_change_code', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('ASS_TRNSFR_FG', 'property_valuations', 'assessment_transfer_flag', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('ASS_DIF_TRNS', 'property_valuations', 'assessment_difference_transfer', 'NUMERIC(12,2)', 'convert_currency'),
            ],
            
            'property_exemptions': [
                # Previous homestead status
                FieldMapping('PREV_HMSTD_OWN', 'property_exemptions', 'previous_homestead_owner', 'VARCHAR(1)', 'clean_string'),
                
                # All exemption fields - stored in JSONB for flexible querying
                # Individual exemption fields will be collected and stored as JSON
                # We'll handle all EXMPT_* fields dynamically
            ] + [
                FieldMapping(f'EXMPT_{i:02d}', 'property_exemptions', f'exemption_{i:02d}', 'NUMERIC(12,2)', 'convert_currency')
                for i in range(1, 83) if i not in [47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]
            ],
            
            'property_characteristics': [
                # Building details
                FieldMapping('ACT_YR_BLT', 'property_characteristics', 'actual_year_built', 'INTEGER', 'convert_year'),
                FieldMapping('IMP_QUAL', 'property_characteristics', 'improvement_quality', 'INTEGER', 'convert_integer'),
                FieldMapping('CONST_CLASS', 'property_characteristics', 'construction_class', 'INTEGER', 'convert_integer'),
                FieldMapping('NO_RES_UNTS', 'property_characteristics', 'number_residential_units', 'INTEGER', 'convert_integer'),
                
                # Land information
                FieldMapping('LND_UNTS_CD', 'property_characteristics', 'land_units_code', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('NO_LND_UNTS', 'property_characteristics', 'land_units_count', 'NUMERIC(12,0)', 'convert_numeric'),
                FieldMapping('PUBLIC_LND', 'property_characteristics', 'public_land_indicator', 'VARCHAR(1)', 'clean_string'),
                
                # Quality and inspection
                FieldMapping('QUAL_CD1', 'property_characteristics', 'quality_code_1', 'INTEGER', 'convert_integer'),
                FieldMapping('VI_CD1', 'property_characteristics', 'vacancy_indicator_1', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('SAL_CHNG_CD1', 'property_characteristics', 'sale_change_code_1', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('QUAL_CD2', 'property_characteristics', 'quality_code_2', 'INTEGER', 'convert_integer'),
                FieldMapping('VI_CD2', 'property_characteristics', 'vacancy_indicator_2', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('SAL_CHNG_CD2', 'property_characteristics', 'sale_change_code_2', 'VARCHAR(3)', 'clean_string'),
                
                # Legal and geographic
                FieldMapping('S_LEGAL', 'property_characteristics', 'short_legal_description', 'VARCHAR(50)', 'clean_string'),
                FieldMapping('MKT_AR', 'property_characteristics', 'market_area', 'VARCHAR(5)', 'clean_string'),
                FieldMapping('TWN', 'property_characteristics', 'township', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('RNG', 'property_characteristics', 'range_info', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('SEC', 'property_characteristics', 'section_info', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('CENSUS_BK', 'property_characteristics', 'census_block', 'VARCHAR(15)', 'clean_string'),
            ],
            
            'property_sales_enhanced': [
                # Sale 1 information
                FieldMapping('MULTI_PAR_SAL1', 'property_sales_enhanced', 'multiple_parcel_sale_1', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('SALE_PRC1', 'property_sales_enhanced', 'sale_price_1', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('SALE_YR1', 'property_sales_enhanced', 'sale_year_1', 'INTEGER', 'convert_year'),
                FieldMapping('SALE_MO1', 'property_sales_enhanced', 'sale_month_1', 'INTEGER', 'convert_month'),
                FieldMapping('OR_BOOK1', 'property_sales_enhanced', 'official_record_book_1', 'VARCHAR(15)', 'clean_string'),
                FieldMapping('OR_PAGE1', 'property_sales_enhanced', 'official_record_page_1', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('CLERK_NO1', 'property_sales_enhanced', 'clerk_number_1', 'NUMERIC(15,0)', 'convert_numeric'),
                
                # Sale 2 information
                FieldMapping('MULTI_PAR_SAL2', 'property_sales_enhanced', 'multiple_parcel_sale_2', 'VARCHAR(1)', 'clean_string'),
                FieldMapping('SALE_PRC2', 'property_sales_enhanced', 'sale_price_2', 'NUMERIC(12,2)', 'convert_currency'),
                FieldMapping('SALE_YR2', 'property_sales_enhanced', 'sale_year_2', 'INTEGER', 'convert_year'),
                FieldMapping('SALE_MO2', 'property_sales_enhanced', 'sale_month_2', 'INTEGER', 'convert_month'),
                FieldMapping('OR_BOOK2', 'property_sales_enhanced', 'official_record_book_2', 'VARCHAR(15)', 'clean_string'),
                FieldMapping('OR_PAGE2', 'property_sales_enhanced', 'official_record_page_2', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('CLERK_NO2', 'property_sales_enhanced', 'clerk_number_2', 'NUMERIC(15,0)', 'convert_numeric'),
            ],
            
            'property_addresses': [
                # Additional owner address information (stored as separate records)
                FieldMapping('OWN_ADDR2', 'property_addresses', 'owner_address_2', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('OWN_STATE_DOM', 'property_addresses', 'owner_state_domicile', 'VARCHAR(2)', 'clean_state'),
                
                # Fiduciary information
                FieldMapping('FIDU_NAME', 'property_addresses', 'fiduciary_name', 'VARCHAR(70)', 'clean_owner_name'),
                FieldMapping('FIDU_ADDR1', 'property_addresses', 'fiduciary_address_1', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('FIDU_ADDR2', 'property_addresses', 'fiduciary_address_2', 'VARCHAR(60)', 'clean_address'),
                FieldMapping('FIDU_CITY', 'property_addresses', 'fiduciary_city', 'VARCHAR(45)', 'clean_city'),
                FieldMapping('FIDU_STATE', 'property_addresses', 'fiduciary_state', 'VARCHAR(50)', 'clean_state'),
                FieldMapping('FIDU_ZIPCD', 'property_addresses', 'fiduciary_zipcode', 'VARCHAR(10)', 'clean_zipcode'),
                FieldMapping('FIDU_CD', 'property_addresses', 'fiduciary_code', 'VARCHAR(1)', 'clean_string'),
            ],
            
            'property_admin_data': [
                # System status and codes
                FieldMapping('APP_STAT', 'property_admin_data', 'appraisal_status', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('CO_APP_STAT', 'property_admin_data', 'county_appraisal_status', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('SEQ_NO', 'property_admin_data', 'sequence_number', 'INTEGER', 'convert_integer'),
                FieldMapping('RS_ID', 'property_admin_data', 'real_personal_status_id', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('MP_ID', 'property_admin_data', 'multiple_parcel_id', 'VARCHAR(10)', 'clean_string'),
                FieldMapping('STATE_PAR_ID', 'property_admin_data', 'state_parcel_id', 'VARCHAR(25)', 'clean_string'),
                
                # Special circumstances
                FieldMapping('SPC_CIR_CD', 'property_admin_data', 'special_circumstance_code', 'VARCHAR(5)', 'clean_string'),
                FieldMapping('SPC_CIR_YR', 'property_admin_data', 'special_circumstance_year', 'INTEGER', 'convert_year'),
                FieldMapping('SPC_CIR_TXT', 'property_admin_data', 'special_circumstance_text', 'TEXT', 'clean_text'),
                
                # Administrative fields
                FieldMapping('DT_LAST_INSPT', 'property_admin_data', 'last_inspection_date', 'VARCHAR(10)', 'clean_date_string'),
                FieldMapping('PAR_SPLT', 'property_admin_data', 'parcel_split', 'NUMERIC(10,0)', 'convert_numeric'),
                FieldMapping('ALT_KEY', 'property_admin_data', 'alternative_key', 'VARCHAR(50)', 'clean_string'),
                FieldMapping('BAS_STRT', 'property_admin_data', 'base_start', 'INTEGER', 'convert_integer'),
                FieldMapping('ATV_STRT', 'property_admin_data', 'active_value_start', 'INTEGER', 'convert_integer'),
                
                # Additional assessment fields
                FieldMapping('DISTR_CD', 'property_admin_data', 'district_code', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('DISTR_YR', 'property_admin_data', 'district_year', 'INTEGER', 'convert_year'),
                FieldMapping('SPASS_CD', 'property_admin_data', 'special_assessment_code', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('CONO_PRV_HM', 'property_admin_data', 'county_previous_homestead', 'VARCHAR(3)', 'clean_string'),
                FieldMapping('PARCEL_ID_PRV_HMSTD', 'property_admin_data', 'parcel_id_previous_homestead', 'VARCHAR(30)', 'clean_parcel_id'),
            ]
        }
    
    def _setup_conversion_functions(self) -> Dict[str, callable]:
        """Setup data type conversion functions"""
        return {
            'clean_string': self._clean_string,
            'clean_parcel_id': self._clean_parcel_id,
            'clean_address': self._clean_address,
            'clean_city': self._clean_city,
            'clean_state': self._clean_state,
            'clean_zipcode': self._clean_zipcode,
            'clean_owner_name': self._clean_owner_name,
            'clean_use_code': self._clean_use_code,
            'clean_date_string': self._clean_date_string,
            'clean_text': self._clean_text,
            'convert_integer': self._convert_integer,
            'convert_numeric': self._convert_numeric,
            'convert_currency': self._convert_currency,
            'convert_year': self._convert_year,
            'convert_month': self._convert_month,
            'convert_county_code': self._convert_county_code,
        }
    
    def _setup_validation_rules(self) -> Dict[str, List[str]]:
        """Setup field validation rules"""
        return {
            'parcel_id': ['not_empty', 'max_length_30'],
            'county_code': ['not_empty', 'length_3'],
            'assessment_year': ['between_1900_2030'],
            'just_value': ['non_negative'],
            'year_built': ['between_1800_2030'],
            'zipcode': ['valid_zipcode_format'],
            'state': ['valid_state_code'],
        }
    
    async def create_comprehensive_mapping(self, nal_fields: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Create comprehensive field mapping for all NAL fields
        
        Args:
            nal_fields: List of field names from NAL CSV header
            
        Returns:
            Dictionary mapping table names to their field configurations
        """
        logger.info(f"Creating comprehensive mapping for {len(nal_fields)} NAL fields")
        
        # Create mapping dictionary
        mapping_dict = {}
        
        # Process each table's mappings
        for table_name, field_mappings in self.comprehensive_mapping.items():
            mapping_dict[table_name] = {}
            
            for field_mapping in field_mappings:
                if field_mapping.source_field in nal_fields:
                    mapping_dict[table_name][field_mapping.source_field] = {
                        'target_field': field_mapping.target_field,
                        'data_type': field_mapping.data_type,
                        'conversion_function': field_mapping.conversion_function,
                        'is_required': field_mapping.is_required,
                        'default_value': field_mapping.default_value,
                        'validation_rules': field_mapping.validation_rules or []
                    }
        
        # Handle exemption fields dynamically
        exemption_fields = {}
        for field in nal_fields:
            if field.startswith('EXMPT_'):
                exemption_fields[field] = {
                    'target_field': field.lower(),
                    'data_type': 'NUMERIC(12,2)',
                    'conversion_function': 'convert_currency',
                    'is_required': False,
                    'default_value': 0,
                    'validation_rules': ['non_negative']
                }
        
        if exemption_fields:
            mapping_dict['property_exemptions'].update(exemption_fields)
        
        logger.info(f"Comprehensive mapping created for {sum(len(fields) for fields in mapping_dict.values())} field mappings")
        
        return mapping_dict
    
    async def validate_mapping_coverage(self, nal_fields: List[str], field_mapping: Dict) -> Dict[str, Any]:
        """
        Validate that all NAL fields are properly mapped
        
        Args:
            nal_fields: List of NAL field names
            field_mapping: Generated field mapping
            
        Returns:
            Coverage validation report
        """
        mapped_fields = set()
        
        # Collect all mapped fields
        for table_fields in field_mapping.values():
            mapped_fields.update(table_fields.keys())
        
        # Find unmapped fields
        nal_field_set = set(nal_fields)
        unmapped_fields = nal_field_set - mapped_fields
        extra_mappings = mapped_fields - nal_field_set
        
        coverage_pct = (len(mapped_fields) / len(nal_fields)) * 100
        
        report = {
            'total_nal_fields': len(nal_fields),
            'mapped_fields': len(mapped_fields),
            'coverage_percentage': coverage_pct,
            'unmapped_fields': list(unmapped_fields),
            'extra_mappings': list(extra_mappings),
            'is_complete': len(unmapped_fields) == 0
        }
        
        logger.info(f"Mapping coverage: {coverage_pct:.1f}% ({len(mapped_fields)}/{len(nal_fields)} fields)")
        
        if unmapped_fields:
            logger.warning(f"Unmapped fields: {unmapped_fields}")
        
        return report
    
    async def transform_batch_data(self, data_batch: List[Dict], field_mapping: Dict) -> Dict[str, List[Dict]]:
        """
        Transform a batch of NAL data using the field mapping
        
        Args:
            data_batch: List of raw NAL record dictionaries
            field_mapping: Comprehensive field mapping configuration
            
        Returns:
            Dictionary with table names as keys and transformed records as values
        """
        logger.debug(f"Transforming batch of {len(data_batch)} records")
        
        transformed_data = {table: [] for table in field_mapping.keys()}
        transformation_errors = []
        
        for record_idx, nal_record in enumerate(data_batch):
            try:
                # Extract parcel_id for relationships
                parcel_id = self._clean_parcel_id(nal_record.get('PARCEL_ID', ''))
                if not parcel_id:
                    transformation_errors.append(f"Record {record_idx}: Missing parcel_id")
                    continue
                
                # Transform data for each table
                for table_name, table_mapping in field_mapping.items():
                    transformed_record = {'parcel_id': parcel_id}
                    
                    # Process each field mapping
                    for nal_field, mapping_config in table_mapping.items():
                        if nal_field == 'parcel_id':  # Skip parcel_id - already handled
                            continue
                        
                        try:
                            raw_value = nal_record.get(nal_field, '')
                            
                            # Apply conversion function
                            if mapping_config['conversion_function']:
                                conversion_func = self.conversion_functions.get(
                                    mapping_config['conversion_function']
                                )
                                if conversion_func:
                                    converted_value = conversion_func(raw_value)
                                else:
                                    converted_value = raw_value
                            else:
                                converted_value = raw_value
                            
                            # Handle default values
                            if converted_value is None and mapping_config['default_value'] is not None:
                                converted_value = mapping_config['default_value']
                            
                            # Validate converted value
                            if mapping_config['validation_rules']:
                                validation_result = self._validate_field_value(
                                    converted_value, 
                                    mapping_config['validation_rules'],
                                    nal_field
                                )
                                if not validation_result['is_valid']:
                                    logger.warning(
                                        f"Validation failed for {nal_field}: {validation_result['errors']}"
                                    )
                            
                            transformed_record[mapping_config['target_field']] = converted_value
                            
                        except Exception as field_error:
                            logger.warning(f"Field transformation error {nal_field}: {field_error}")
                            # Use default value or None
                            transformed_record[mapping_config['target_field']] = (
                                mapping_config.get('default_value')
                            )
                    
                    # Handle special table processing
                    if table_name == 'property_exemptions':
                        transformed_record = self._process_exemptions(transformed_record, nal_record)
                    elif table_name == 'property_sales_enhanced':
                        transformed_record = self._process_sales_data(transformed_record)
                    elif table_name == 'property_addresses':
                        # Split addresses into separate records by type
                        address_records = self._process_addresses(transformed_record, nal_record)
                        transformed_data[table_name].extend(address_records)
                        continue
                    
                    # Add metadata
                    transformed_record.update({
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    
                    transformed_data[table_name].append(transformed_record)
                    
            except Exception as record_error:
                transformation_errors.append(f"Record {record_idx}: {record_error}")
                logger.warning(f"Record transformation error: {record_error}")
        
        # Log transformation summary
        total_transformed = sum(len(records) for records in transformed_data.values())
        logger.debug(f"Transformation complete: {total_transformed} records created from {len(data_batch)} input records")
        
        if transformation_errors:
            logger.warning(f"Transformation errors: {len(transformation_errors)}")
        
        return transformed_data
    
    def _process_exemptions(self, record: Dict, nal_record: Dict) -> Dict:
        """Process exemption fields into structured format"""
        # Collect all exemption values
        exemptions = {}
        total_exemption = 0
        common_exemptions = {}
        
        for field_name, value in nal_record.items():
            if field_name.startswith('EXMPT_'):
                exemption_value = self._convert_currency(value)
                if exemption_value and exemption_value > 0:
                    exemptions[field_name] = exemption_value
                    total_exemption += exemption_value
                    
                    # Map common exemptions
                    if field_name == 'EXMPT_01':  # Homestead
                        common_exemptions['homestead_exemption'] = exemption_value
                        record['has_homestead'] = True
                    elif field_name == 'EXMPT_02':  # Senior
                        common_exemptions['senior_exemption'] = exemption_value
                    elif field_name == 'EXMPT_03':  # Disability
                        common_exemptions['disability_exemption'] = exemption_value
                    elif field_name == 'EXMPT_04':  # Veteran
                        common_exemptions['veteran_exemption'] = exemption_value
                    elif field_name in ['EXMPT_05', 'EXMPT_06']:  # Agricultural
                        common_exemptions['agricultural_exemption'] = exemption_value
                        record['has_agricultural'] = True
        
        # Update record with exemption data
        record.update(common_exemptions)
        record.update({
            'all_exemptions': json.dumps(exemptions) if exemptions else None,
            'total_exemption_amount': total_exemption,
            'active_exemption_count': len(exemptions),
            'has_homestead': record.get('has_homestead', False),
            'has_agricultural': record.get('has_agricultural', False)
        })
        
        return record
    
    def _process_sales_data(self, record: Dict) -> Dict:
        """Process sales data to create computed fields"""
        # Determine latest sale
        sale_1_date = self._create_sale_date(
            record.get('sale_year_1'), record.get('sale_month_1')
        )
        sale_2_date = self._create_sale_date(
            record.get('sale_year_2'), record.get('sale_month_2')
        )
        
        if sale_1_date and sale_2_date:
            if sale_1_date >= sale_2_date:
                record.update({
                    'latest_sale_date': sale_1_date,
                    'latest_sale_price': record.get('sale_price_1'),
                    'previous_sale_date': sale_2_date,
                    'previous_sale_price': record.get('sale_price_2')
                })
            else:
                record.update({
                    'latest_sale_date': sale_2_date,
                    'latest_sale_price': record.get('sale_price_2'),
                    'previous_sale_date': sale_1_date,
                    'previous_sale_price': record.get('sale_price_1')
                })
        elif sale_1_date:
            record.update({
                'latest_sale_date': sale_1_date,
                'latest_sale_price': record.get('sale_price_1')
            })
        elif sale_2_date:
            record.update({
                'latest_sale_date': sale_2_date,
                'latest_sale_price': record.get('sale_price_2')
            })
        
        # Calculate price change percentage
        if (record.get('latest_sale_price') and record.get('previous_sale_price') 
            and record.get('previous_sale_price') > 0):
            price_change = (
                (record['latest_sale_price'] - record['previous_sale_price']) 
                / record['previous_sale_price'] * 100
            )
            record['price_change_percentage'] = round(price_change, 4)
        
        return record
    
    def _process_addresses(self, record: Dict, nal_record: Dict) -> List[Dict]:
        """Process address data into separate records by type"""
        address_records = []
        
        # Owner address (if different from core record)
        if nal_record.get('OWN_ADDR2'):
            owner_address = {
                'parcel_id': record['parcel_id'],
                'address_type': 'owner_secondary',
                'address_2': self._clean_address(nal_record.get('OWN_ADDR2')),
                'state_domicile': self._clean_state(nal_record.get('OWN_STATE_DOM')),
                'is_primary': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            address_records.append(owner_address)
        
        # Fiduciary address
        if nal_record.get('FIDU_NAME'):
            fiduciary_address = {
                'parcel_id': record['parcel_id'],
                'address_type': 'fiduciary',
                'name': self._clean_owner_name(nal_record.get('FIDU_NAME')),
                'address_1': self._clean_address(nal_record.get('FIDU_ADDR1')),
                'address_2': self._clean_address(nal_record.get('FIDU_ADDR2')),
                'city': self._clean_city(nal_record.get('FIDU_CITY')),
                'state': self._clean_state(nal_record.get('FIDU_STATE')),
                'zipcode': self._clean_zipcode(nal_record.get('FIDU_ZIPCD')),
                'fiduciary_code': self._clean_string(nal_record.get('FIDU_CD')),
                'is_primary': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            address_records.append(fiduciary_address)
        
        return address_records
    
    # Conversion functions
    def _clean_string(self, value: Any) -> Optional[str]:
        """Clean and normalize string values"""
        if value is None or value == '':
            return None
        return str(value).strip()
    
    def _clean_parcel_id(self, value: Any) -> Optional[str]:
        """Clean and validate parcel ID"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Remove quotes and normalize
        return cleaned.replace('"', '').strip()
    
    def _clean_address(self, value: Any) -> Optional[str]:
        """Clean address field"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Title case for addresses
        return cleaned.title()
    
    def _clean_city(self, value: Any) -> Optional[str]:
        """Clean city name"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        return cleaned.title()
    
    def _clean_state(self, value: Any) -> Optional[str]:
        """Clean state code/name"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        return cleaned.upper()
    
    def _clean_zipcode(self, value: Any) -> Optional[str]:
        """Clean and validate ZIP code"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Extract numeric portion
        numeric_zip = re.sub(r'[^\d]', '', cleaned)
        if len(numeric_zip) >= 5:
            return numeric_zip[:5] + ('-' + numeric_zip[5:9] if len(numeric_zip) > 5 else '')
        return numeric_zip if numeric_zip else None
    
    def _clean_owner_name(self, value: Any) -> Optional[str]:
        """Clean owner name"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Title case but preserve all caps organizations
        if cleaned.isupper() and any(word in cleaned for word in ['LLC', 'INC', 'CORP', 'LTD']):
            return cleaned
        return cleaned.title()
    
    def _clean_use_code(self, value: Any) -> Optional[str]:
        """Clean use code"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Pad with leading zeros if needed
        return cleaned.zfill(3)
    
    def _clean_date_string(self, value: Any) -> Optional[str]:
        """Clean date string (keep as string for now)"""
        return self._clean_string(value)
    
    def _clean_text(self, value: Any) -> Optional[str]:
        """Clean text field"""
        return self._clean_string(value)
    
    def _convert_integer(self, value: Any) -> Optional[int]:
        """Convert value to integer"""
        if value is None or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _convert_numeric(self, value: Any) -> Optional[float]:
        """Convert value to numeric (float)"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _convert_currency(self, value: Any) -> Optional[float]:
        """Convert value to currency (2 decimal places)"""
        numeric_value = self._convert_numeric(value)
        if numeric_value is None:
            return None
        return round(numeric_value, 2)
    
    def _convert_year(self, value: Any) -> Optional[int]:
        """Convert and validate year"""
        year_int = self._convert_integer(value)
        if year_int is None:
            return None
        # Validate reasonable year range
        if 1800 <= year_int <= 2030:
            return year_int
        return None
    
    def _convert_month(self, value: Any) -> Optional[int]:
        """Convert and validate month"""
        month_int = self._convert_integer(value)
        if month_int is None:
            return None
        # Validate month range
        if 1 <= month_int <= 12:
            return month_int
        return None
    
    def _convert_county_code(self, value: Any) -> Optional[str]:
        """Convert and validate county code"""
        cleaned = self._clean_string(value)
        if not cleaned:
            return None
        # Pad county code to 3 digits
        return cleaned.zfill(3)
    
    def _create_sale_date(self, year: Optional[int], month: Optional[int]) -> Optional[date]:
        """Create date from year and month"""
        if not year or not month:
            return None
        try:
            return date(year, month, 1)
        except (ValueError, TypeError):
            return None
    
    def _validate_field_value(self, value: Any, rules: List[str], field_name: str) -> Dict[str, Any]:
        """Validate field value against rules"""
        errors = []
        
        for rule in rules:
            if rule == 'not_empty' and (value is None or value == ''):
                errors.append(f"{field_name}: Value cannot be empty")
            elif rule == 'non_negative' and value is not None and value < 0:
                errors.append(f"{field_name}: Value cannot be negative")
            elif rule.startswith('max_length_'):
                max_len = int(rule.split('_')[-1])
                if value and len(str(value)) > max_len:
                    errors.append(f"{field_name}: Exceeds maximum length {max_len}")
            elif rule.startswith('length_'):
                exact_len = int(rule.split('_')[-1])
                if value and len(str(value)) != exact_len:
                    errors.append(f"{field_name}: Must be exactly {exact_len} characters")
            elif rule == 'between_1900_2030' and value is not None:
                if not (1900 <= value <= 2030):
                    errors.append(f"{field_name}: Must be between 1900 and 2030")
            elif rule == 'between_1800_2030' and value is not None:
                if not (1800 <= value <= 2030):
                    errors.append(f"{field_name}: Must be between 1800 and 2030")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }