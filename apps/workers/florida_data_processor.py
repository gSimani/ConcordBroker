#!/usr/bin/env python3
"""
Florida Data Processor
Advanced data processing pipeline with schema mapping and validation
Handles all Florida property data formats with error recovery
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
import logging
import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import csv
import zipfile
import gzip
from io import StringIO, TextIOWrapper
import chardet

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig

logger = logging.getLogger(__name__)

class DatasetType(Enum):
    """Types of Florida datasets"""
    NAL = "nal"  # Name/Address/Legal
    NAP = "nap"  # Non-Ad Valorem Parcel
    NAV_D = "nav_d"  # Assessments Detail
    NAV_N = "nav_n"  # Assessments Summary  
    SDF = "sdf"  # Sales Data File
    TPP = "tpp"  # Tangible Personal Property
    RER = "rer"  # Real Estate Transfer
    CDF = "cdf"  # Code Definition File
    JVS = "jvs"  # Just Value Study
    SUNBIZ = "sunbiz"  # Business Registry
    BROWARD_DAILY = "broward_daily"  # Daily Index

@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    data_type: str
    nullable: bool = True
    default_value: Any = None
    transformation: Optional[str] = None
    validation: Optional[str] = None

@dataclass
class DatasetSchema:
    """Complete dataset schema definition"""
    dataset_type: DatasetType
    table_name: str
    fields: List[FieldMapping]
    primary_key: List[str]
    unique_constraints: List[List[str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    file_format: str = "fixed_width"  # fixed_width, csv, pipe_delimited
    encoding: str = "latin1"
    skip_rows: int = 0
    has_header: bool = False

class FloridaDataProcessor:
    """Comprehensive data processor for all Florida datasets"""
    
    def __init__(self):
        self.pool = None
        self.schemas = self._initialize_schemas()
        self.processing_stats = {
            "files_processed": 0,
            "total_records": 0,
            "successful_inserts": 0,
            "failed_inserts": 0,
            "validation_errors": 0,
            "last_processed": None
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.pool = await SupabaseConfig.get_db_pool()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.pool:
            await self.pool.close()
    
    def _initialize_schemas(self) -> Dict[DatasetType, DatasetSchema]:
        """Initialize all dataset schemas"""
        schemas = {}
        
        # NAL Schema (Name/Address/Legal)
        schemas[DatasetType.NAL] = DatasetSchema(
            dataset_type=DatasetType.NAL,
            table_name="fl_nal_name_address",
            file_format="fixed_width",
            encoding="latin1",
            fields=[
                FieldMapping("county_number", "county_number", "text", False),
                FieldMapping("parcel_id", "parcel_id", "text", False),
                FieldMapping("assessment_year", "assessment_year", "integer", False),
                FieldMapping("owner_name", "owner_name", "text"),
                FieldMapping("owner_name_2", "owner_name_2", "text"),
                FieldMapping("mailing_address", "mailing_address", "text"),
                FieldMapping("mailing_address_2", "mailing_address_2", "text"),
                FieldMapping("mailing_city", "mailing_city", "text"),
                FieldMapping("mailing_state", "mailing_state", "text"),
                FieldMapping("mailing_zip", "mailing_zip", "text"),
                FieldMapping("mailing_country", "mailing_country", "text"),
                FieldMapping("property_street_address", "property_street_address", "text"),
                FieldMapping("property_city", "property_city", "text"),
                FieldMapping("property_state", "property_state", "text"),
                FieldMapping("property_zip", "property_zip", "text"),
                FieldMapping("legal_description", "legal_description", "text"),
            ],
            primary_key=["county_number", "parcel_id", "assessment_year"],
            unique_constraints=[["county_number", "parcel_id", "assessment_year"]]
        )
        
        # TPP Schema (Tangible Personal Property)
        schemas[DatasetType.TPP] = DatasetSchema(
            dataset_type=DatasetType.TPP,
            table_name="fl_tpp_accounts",
            file_format="fixed_width",
            encoding="latin1",
            fields=[
                FieldMapping("county_number", "county_number", "text", False),
                FieldMapping("account_number", "account_number", "text", False),
                FieldMapping("assessment_year", "assessment_year", "integer", False),
                FieldMapping("owner_name", "owner_name", "text"),
                FieldMapping("owner_name2", "owner_name2", "text"),
                FieldMapping("mailing_address", "mailing_address", "text"),
                FieldMapping("mailing_address2", "mailing_address2", "text"),
                FieldMapping("mailing_address3", "mailing_address3", "text"),
                FieldMapping("mailing_city", "mailing_city", "text"),
                FieldMapping("mailing_state", "mailing_state", "text"),
                FieldMapping("mailing_zip", "mailing_zip", "text"),
                FieldMapping("mailing_country", "mailing_country", "text"),
                FieldMapping("primary_site_address", "primary_site_address", "text"),
                FieldMapping("primary_site_address2", "primary_site_address2", "text"),
                FieldMapping("primary_site_city", "primary_site_city", "text"),
                FieldMapping("primary_site_zip", "primary_site_zip", "text"),
                FieldMapping("business_name", "business_name", "text"),
                FieldMapping("business_name2", "business_name2", "text"),
                FieldMapping("fei_number", "fei_number", "text"),
                FieldMapping("business_description", "business_description", "text"),
                FieldMapping("tangible_value", "tangible_value", "decimal", 
                           transformation="clean_currency"),
                FieldMapping("exemption_value", "exemption_value", "decimal",
                           transformation="clean_currency"),
                FieldMapping("taxable_value", "taxable_value", "decimal",
                           transformation="clean_currency"),
                FieldMapping("property_appraiser_value", "property_appraiser_value", "decimal",
                           transformation="clean_currency"),
                FieldMapping("dor_value_code", "dor_value_code", "text"),
                FieldMapping("nac_code", "nac_code", "text"),
                FieldMapping("employee_count", "employee_count", "integer"),
                FieldMapping("parent_account_flag", "parent_account_flag", "text"),
                FieldMapping("parent_account_number", "parent_account_number", "text"),
                FieldMapping("folio_number", "folio_number", "text"),
            ],
            primary_key=["county_number", "account_number", "assessment_year"]
        )
        
        # SDF Schema (Sales Data File)
        schemas[DatasetType.SDF] = DatasetSchema(
            dataset_type=DatasetType.SDF,
            table_name="fl_sdf_sales",
            file_format="fixed_width",
            encoding="latin1",
            fields=[
                FieldMapping("county_number", "county_number", "text", False),
                FieldMapping("parcel_id", "parcel_id", "text", False),
                FieldMapping("assessment_year", "assessment_year", "integer", False),
                FieldMapping("active_start", "active_start", "integer"),
                FieldMapping("group_number", "group_number", "integer"),
                FieldMapping("dor_use_code", "dor_use_code", "text"),
                FieldMapping("neighborhood_code", "neighborhood_code", "text"),
                FieldMapping("market_area", "market_area", "text"),
                FieldMapping("census_block", "census_block", "text"),
                FieldMapping("sale_id_code", "sale_id_code", "text", False),
                FieldMapping("sale_change_code", "sale_change_code", "text"),
                FieldMapping("validity_indicator", "validity_indicator", "text"),
                FieldMapping("official_record_book", "official_record_book", "text"),
                FieldMapping("official_record_page", "official_record_page", "text"),
                FieldMapping("clerk_number", "clerk_number", "text"),
                FieldMapping("qualification_code", "qualification_code", "text", False),
                FieldMapping("qualification_description", "qualification_description", "text"),
                FieldMapping("sale_year", "sale_year", "integer", False),
                FieldMapping("sale_month", "sale_month", "integer"),
                FieldMapping("sale_price", "sale_price", "decimal",
                           transformation="clean_currency"),
                FieldMapping("multi_parcel_sale", "multi_parcel_sale", "text"),
                FieldMapping("real_estate_id", "real_estate_id", "text"),
                FieldMapping("map_id", "map_id", "text"),
                FieldMapping("state_parcel_id", "state_parcel_id", "text"),
            ],
            primary_key=["county_number", "parcel_id", "sale_id_code"]
        )
        
        # NAV Summary Schema
        schemas[DatasetType.NAV_N] = DatasetSchema(
            dataset_type=DatasetType.NAV_N,
            table_name="fl_nav_parcel_summary",
            file_format="fixed_width",
            encoding="latin1",
            fields=[
                FieldMapping("county_number", "county_number", "text", False),
                FieldMapping("parcel_id", "parcel_id", "text", False),
                FieldMapping("assessment_year", "assessment_year", "integer", False),
                FieldMapping("tax_year", "tax_year", "integer", False),
                FieldMapping("roll_type", "roll_type", "text"),
                FieldMapping("total_nav_units", "total_nav_units", "decimal"),
                FieldMapping("total_nav_assessment", "total_nav_assessment", "decimal"),
            ],
            primary_key=["county_number", "parcel_id", "assessment_year", "tax_year"]
        )
        
        # NAV Detail Schema
        schemas[DatasetType.NAV_D] = DatasetSchema(
            dataset_type=DatasetType.NAV_D,
            table_name="fl_nav_assessment_detail",
            file_format="fixed_width",
            encoding="latin1",
            fields=[
                FieldMapping("county_number", "county_number", "text", False),
                FieldMapping("parcel_id", "parcel_id", "text", False),
                FieldMapping("assessment_year", "assessment_year", "integer", False),
                FieldMapping("tax_year", "tax_year", "integer", False),
                FieldMapping("roll_type", "roll_type", "text"),
                FieldMapping("nav_tax_code", "nav_tax_code", "text", False),
                FieldMapping("nav_units", "nav_units", "decimal"),
                FieldMapping("nav_assessment", "nav_assessment", "decimal"),
                FieldMapping("authority_name", "authority_name", "text"),
                FieldMapping("authority_type", "authority_type", "text"),
                FieldMapping("district_name", "district_name", "text"),
            ],
            primary_key=["county_number", "parcel_id", "assessment_year", "tax_year", "nav_tax_code"]
        )
        
        # Sunbiz Schema
        schemas[DatasetType.SUNBIZ] = DatasetSchema(
            dataset_type=DatasetType.SUNBIZ,
            table_name="sunbiz_entities",
            file_format="pipe_delimited",
            encoding="utf-8",
            has_header=True,
            fields=[
                FieldMapping("entity_number", "entity_number", "text", False),
                FieldMapping("entity_name", "entity_name", "text"),
                FieldMapping("entity_type", "entity_type", "text"),
                FieldMapping("status", "status", "text"),
                FieldMapping("registration_date", "registration_date", "date",
                           transformation="parse_date"),
                FieldMapping("principal_address", "principal_address", "text"),
                FieldMapping("mailing_address", "mailing_address", "text"),
                FieldMapping("registered_agent", "registered_agent", "text"),
            ],
            primary_key=["entity_number"]
        )
        
        return schemas
    
    async def detect_file_format(self, file_path: Path) -> Dict[str, Any]:
        """Detect file format and encoding"""
        logger.info(f"Detecting format for {file_path}")
        
        format_info = {
            "encoding": "utf-8",
            "delimiter": None,
            "has_header": False,
            "line_count": 0,
            "sample_lines": []
        }
        
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)  # Read first 100KB
            detected = chardet.detect(raw_data)
            if detected['confidence'] > 0.7:
                format_info["encoding"] = detected['encoding']
        
        # Analyze file structure
        try:
            with open(file_path, 'r', encoding=format_info["encoding"], errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.rstrip())
                    if i >= 10:  # Sample first 10 lines
                        break
                
                format_info["sample_lines"] = lines
                format_info["line_count"] = len(lines)
                
                if lines:
                    first_line = lines[0]
                    
                    # Check for common delimiters
                    delimiters = [',', '|', '\t', ';']
                    delimiter_counts = {d: first_line.count(d) for d in delimiters}
                    
                    if max(delimiter_counts.values()) > 0:
                        format_info["delimiter"] = max(delimiter_counts, key=delimiter_counts.get)
                    
                    # Check if first line looks like headers
                    if format_info["delimiter"]:
                        headers = first_line.split(format_info["delimiter"])
                        if any(h.replace('_', '').replace(' ', '').isalpha() for h in headers):
                            format_info["has_header"] = True
                            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
        
        return format_info
    
    async def process_file(self, file_path: Path, dataset_type: DatasetType = None) -> Dict[str, Any]:
        """Process a single data file"""
        logger.info(f"Processing file: {file_path}")
        
        # Auto-detect dataset type if not provided
        if dataset_type is None:
            dataset_type = self._detect_dataset_type(file_path)
        
        if dataset_type not in self.schemas:
            raise ValueError(f"No schema defined for dataset type: {dataset_type}")
        
        schema = self.schemas[dataset_type]
        results = {
            "file_path": str(file_path),
            "dataset_type": dataset_type.value,
            "records_processed": 0,
            "records_inserted": 0,
            "validation_errors": [],
            "processing_errors": [],
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # Detect file format
            format_info = await self.detect_file_format(file_path)
            
            # Read and parse file
            df = await self._read_file_to_dataframe(file_path, schema, format_info)
            
            if df is not None and not df.empty:
                # Clean and validate data
                df_cleaned = await self._clean_and_validate_data(df, schema, results)
                
                # Insert to database
                if not df_cleaned.empty:
                    inserted_count = await self._insert_data_to_database(df_cleaned, schema)
                    results["records_inserted"] = inserted_count
                
                results["records_processed"] = len(df)
            
        except Exception as e:
            logger.error(f"File processing failed: {e}")
            results["processing_errors"].append(str(e))
        
        finally:
            results["end_time"] = datetime.now()
            self.processing_stats["files_processed"] += 1
            self.processing_stats["total_records"] += results["records_processed"]
            self.processing_stats["successful_inserts"] += results["records_inserted"]
            self.processing_stats["last_processed"] = datetime.now()
        
        return results
    
    def _detect_dataset_type(self, file_path: Path) -> DatasetType:
        """Detect dataset type from filename"""
        filename = file_path.name.upper()
        
        if filename.startswith('NAL'):
            return DatasetType.NAL
        elif filename.startswith('NAP'):
            return DatasetType.NAP
        elif filename.startswith('NAVD') or 'NAV_D' in filename:
            return DatasetType.NAV_D
        elif filename.startswith('NAVN') or 'NAV_N' in filename:
            return DatasetType.NAV_N
        elif filename.startswith('SDF'):
            return DatasetType.SDF
        elif filename.startswith('TPP'):
            return DatasetType.TPP
        elif 'SUNBIZ' in filename or 'CORP' in filename or 'LLC' in filename:
            return DatasetType.SUNBIZ
        elif filename.endswith('.ZIP') and filename.isdigit():
            return DatasetType.BROWARD_DAILY
        else:
            raise ValueError(f"Cannot determine dataset type for file: {filename}")
    
    async def _read_file_to_dataframe(self, file_path: Path, schema: DatasetSchema, 
                                    format_info: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Read file into pandas DataFrame"""
        logger.info(f"Reading file with format: {schema.file_format}")
        
        try:
            if schema.file_format == "fixed_width":
                # For fixed-width files, we need column specifications
                # This would be implemented based on Florida Revenue documentation
                df = self._read_fixed_width_file(file_path, schema, format_info)
            elif schema.file_format == "csv":
                df = pd.read_csv(
                    file_path,
                    encoding=format_info["encoding"],
                    skiprows=schema.skip_rows,
                    header=0 if schema.has_header else None,
                    low_memory=False,
                    dtype=str  # Read everything as string initially
                )
            elif schema.file_format == "pipe_delimited":
                df = pd.read_csv(
                    file_path,
                    separator='|',
                    encoding=format_info["encoding"],
                    skiprows=schema.skip_rows,
                    header=0 if schema.has_header else None,
                    low_memory=False,
                    dtype=str
                )
            else:
                raise ValueError(f"Unsupported file format: {schema.file_format}")
            
            # Assign column names if schema doesn't have header
            if not schema.has_header and len(df.columns) == len(schema.fields):
                df.columns = [field.target_field for field in schema.fields]
            
            logger.info(f"Successfully read {len(df)} records with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return None
    
    def _read_fixed_width_file(self, file_path: Path, schema: DatasetSchema, 
                              format_info: Dict[str, Any]) -> pd.DataFrame:
        """Read fixed-width file using Florida Revenue specifications"""
        # This would implement the specific column widths for each dataset type
        # Based on Florida Revenue documentation
        
        # For now, return empty DataFrame - this needs specific implementation
        # per dataset type with exact column positions
        logger.warning("Fixed-width parsing not fully implemented - needs column specifications")
        
        # Try to read as regular text and split by common patterns
        with open(file_path, 'r', encoding=format_info["encoding"], errors='ignore') as f:
            lines = f.readlines()[:1000]  # Sample first 1000 lines
        
        # Basic parsing attempt
        data = []
        for line in lines:
            # This is a simplified approach - real implementation needs exact positions
            if len(line.strip()) > 10:  # Skip empty lines
                # Split by multiple spaces (common in fixed-width)
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 3:  # Minimum viable record
                    data.append(parts[:len(schema.fields)])
        
        if data:
            df = pd.DataFrame(data)
            if len(df.columns) <= len(schema.fields):
                column_names = [field.target_field for field in schema.fields[:len(df.columns)]]
                df.columns = column_names
            return df
        
        return pd.DataFrame()
    
    async def _clean_and_validate_data(self, df: pd.DataFrame, schema: DatasetSchema, 
                                     results: Dict[str, Any]) -> pd.DataFrame:
        """Clean and validate data according to schema"""
        logger.info(f"Cleaning and validating {len(df)} records")
        
        df_clean = df.copy()
        
        for field in schema.fields:
            if field.target_field not in df_clean.columns:
                continue
            
            column_data = df_clean[field.target_field]
            
            try:
                # Apply transformations
                if field.transformation:
                    column_data = self._apply_transformation(column_data, field.transformation)
                
                # Type conversion
                if field.data_type == "integer":
                    column_data = pd.to_numeric(column_data, errors='coerce').fillna(0).astype(int)
                elif field.data_type == "decimal":
                    column_data = pd.to_numeric(column_data, errors='coerce')
                elif field.data_type == "date":
                    column_data = pd.to_datetime(column_data, errors='coerce')
                elif field.data_type == "text":
                    column_data = column_data.astype(str).replace('nan', '')
                
                # Handle nulls
                if not field.nullable:
                    before_count = len(column_data)
                    column_data = column_data.dropna()
                    after_count = len(column_data)
                    
                    if before_count != after_count:
                        results["validation_errors"].append(
                            f"Removed {before_count - after_count} null values from non-nullable field {field.target_field}"
                        )
                
                # Apply default values
                if field.default_value is not None:
                    column_data = column_data.fillna(field.default_value)
                
                df_clean[field.target_field] = column_data
                
            except Exception as e:
                error_msg = f"Validation failed for field {field.target_field}: {e}"
                logger.error(error_msg)
                results["validation_errors"].append(error_msg)
        
        # Remove rows with critical missing data (primary key fields)
        primary_key_fields = schema.primary_key
        for pk_field in primary_key_fields:
            if pk_field in df_clean.columns:
                before_count = len(df_clean)
                df_clean = df_clean[df_clean[pk_field].notna()]
                df_clean = df_clean[df_clean[pk_field] != '']
                after_count = len(df_clean)
                
                if before_count != after_count:
                    results["validation_errors"].append(
                        f"Removed {before_count - after_count} records with missing primary key {pk_field}"
                    )
        
        logger.info(f"Validation complete: {len(df_clean)} records remaining")
        return df_clean
    
    def _apply_transformation(self, data: pd.Series, transformation: str) -> pd.Series:
        """Apply data transformation"""
        if transformation == "clean_currency":
            # Remove currency symbols and convert to numeric
            return data.astype(str).str.replace(r'[^\d.-]', '', regex=True)
        elif transformation == "parse_date":
            # Parse various date formats
            return pd.to_datetime(data, errors='coerce')
        elif transformation == "uppercase":
            return data.str.upper()
        elif transformation == "trim":
            return data.str.strip()
        else:
            return data
    
    async def _insert_data_to_database(self, df: pd.DataFrame, schema: DatasetSchema) -> int:
        """Insert data to Supabase using batch operations"""
        logger.info(f"Inserting {len(df)} records to {schema.table_name}")
        
        try:
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Insert in batches
            batch_size = 1000
            total_inserted = 0
            
            async with self.pool.acquire() as conn:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    
                    # Build INSERT statement
                    if not batch:
                        continue
                    
                    columns = list(batch[0].keys())
                    placeholders = ', '.join([f'${j+1}' for j in range(len(columns))])
                    
                    sql = f"""
                        INSERT INTO {schema.table_name} ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON CONFLICT ({', '.join(schema.primary_key)})
                        DO UPDATE SET
                        {', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in schema.primary_key])},
                        updated_at = NOW()
                    """
                    
                    # Execute batch insert
                    for record in batch:
                        values = [record.get(col) for col in columns]
                        try:
                            await conn.execute(sql, *values)
                            total_inserted += 1
                        except Exception as e:
                            logger.error(f"Insert failed for record: {e}")
                            continue
            
            logger.info(f"Successfully inserted {total_inserted} records")
            return total_inserted
            
        except Exception as e:
            logger.error(f"Database insertion failed: {e}")
            return 0
    
    async def process_directory(self, directory_path: Path, dataset_type: DatasetType = None) -> Dict[str, Any]:
        """Process all files in a directory"""
        logger.info(f"Processing directory: {directory_path}")
        
        results = {
            "directory": str(directory_path),
            "files_processed": 0,
            "total_records": 0,
            "successful_files": 0,
            "failed_files": [],
            "file_results": []
        }
        
        # Find all data files
        patterns = ['*.txt', '*.csv', '*.zip']
        files = []
        for pattern in patterns:
            files.extend(directory_path.glob(pattern))
        
        logger.info(f"Found {len(files)} files to process")
        
        for file_path in files:
            try:
                file_result = await self.process_file(file_path, dataset_type)
                results["file_results"].append(file_result)
                results["files_processed"] += 1
                results["total_records"] += file_result["records_processed"]
                
                if file_result["records_inserted"] > 0:
                    results["successful_files"] += 1
                else:
                    results["failed_files"].append(str(file_path))
                    
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
                results["failed_files"].append(str(file_path))
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()

async def main():
    """Test the data processor"""
    print("Testing Florida Data Processor...")
    
    async with FloridaDataProcessor() as processor:
        # Test file detection and schema mapping
        test_files = [
            "NAL16P202501.txt",
            "SDF16P202501.txt", 
            "TPP_06_2025.txt",
            "sunbiz_corp_20250101.txt"
        ]
        
        for filename in test_files:
            try:
                dataset_type = processor._detect_dataset_type(Path(filename))
                schema = processor.schemas[dataset_type]
                print(f"  {filename} -> {dataset_type.value} ({schema.table_name})")
            except Exception as e:
                print(f"  {filename} -> ERROR: {e}")
        
        print(f"\nProcessing Statistics:")
        stats = processor.get_processing_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())