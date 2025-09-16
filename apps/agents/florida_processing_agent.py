#!/usr/bin/env python3
"""
Florida Processing Agent
Specialized agent for processing downloaded Florida property data files

Features:
- Data validation and quality checks
- CSV parsing with error handling
- Data transformation and normalization
- Duplicate detection and deduplication
- Batch processing for performance
- Memory-efficient handling of large files
- Schema validation and mapping
"""

import asyncio
import pandas as pd
import numpy as np
import logging
import json
import csv
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass, asdict
import io
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single file"""
    filename: str
    file_type: str  # NAL, NAP, SDF
    county_code: str
    year: str
    records_processed: int
    records_valid: int
    records_invalid: int
    data_quality_score: float
    processing_duration: float
    errors: List[Dict[str, Any]]
    processed_data: Optional[List[Dict[str, Any]]] = None

@dataclass
class ValidationRule:
    """Data validation rule"""
    field_name: str
    rule_type: str  # required, format, range, enum
    rule_params: Dict[str, Any]
    severity: str  # error, warning, info

class FloridaProcessingAgent:
    """Agent responsible for processing Florida property data files"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Processing configuration
        self.batch_size = self.config.get("processing", {}).get("batch_size", 10000)
        self.max_workers = self.config.get("processing", {}).get("max_workers", mp.cpu_count())
        self.memory_limit_mb = self.config.get("processing", {}).get("memory_limit_mb", 2048)
        self.validation_enabled = self.config.get("processing", {}).get("enable_validation", True)
        
        # File encoding detection
        self.encoding_options = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        # Statistics
        self.stats = {
            "files_processed": 0,
            "records_processed": 0,
            "records_valid": 0,
            "records_invalid": 0,
            "processing_errors": 0,
            "last_processing": None,
            "average_processing_time": 0.0
        }
        
        # Validation rules for each file type
        self.validation_rules = self._initialize_validation_rules()
        
        # Data transformation mappings
        self.field_mappings = self._initialize_field_mappings()

    async def initialize(self):
        """Initialize the processing agent"""
        logger.info("Initializing Florida Processing Agent...")
        
        # Validate configuration
        if self.max_workers > mp.cpu_count():
            logger.warning(f"max_workers ({self.max_workers}) exceeds CPU count ({mp.cpu_count()})")
            self.max_workers = mp.cpu_count()
        
        logger.info(f"✅ Florida Processing Agent initialized (workers: {self.max_workers}, batch_size: {self.batch_size})")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("✅ Florida Processing Agent cleanup complete")

    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Initialize validation rules for each file type"""
        return {
            "NAL": [
                ValidationRule("PARCEL_ID", "required", {}, "error"),
                ValidationRule("OWNER_NAME", "required", {}, "error"),
                ValidationRule("PROPERTY_ADDRESS", "required", {}, "warning"),
                ValidationRule("COUNTY_CODE", "format", {"pattern": r"^\d{2}$"}, "error"),
                ValidationRule("YEAR", "format", {"pattern": r"^\d{4}P?$"}, "error"),
            ],
            "NAP": [
                ValidationRule("PARCEL_ID", "required", {}, "error"),
                ValidationRule("ASSESSED_VALUE", "format", {"pattern": r"^\d+(\.\d{2})?$"}, "warning"),
                ValidationRule("PROPERTY_USE_CODE", "required", {}, "warning"),
                ValidationRule("COUNTY_CODE", "format", {"pattern": r"^\d{2}$"}, "error"),
            ],
            "SDF": [
                ValidationRule("PARCEL_ID", "required", {}, "error"),
                ValidationRule("SALE_DATE", "format", {"pattern": r"^\d{4}-\d{2}-\d{2}$"}, "error"),
                ValidationRule("SALE_PRICE", "range", {"min": 0, "max": 100000000}, "warning"),
                ValidationRule("QUALIFIED_SALE", "enum", {"values": ["Y", "N", "U"]}, "warning"),
            ]
        }

    def _initialize_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize field name mappings for database compatibility"""
        return {
            "NAL": {
                "PARCEL_ID": "parcel_id",
                "OWNER_NAME": "owner_name", 
                "PROPERTY_ADDRESS": "property_address",
                "OWNER_ADDRESS": "owner_address",
                "COUNTY_CODE": "county_code",
                "YEAR": "year"
            },
            "NAP": {
                "PARCEL_ID": "parcel_id",
                "ASSESSED_VALUE": "assessed_value",
                "JUST_VALUE": "just_value", 
                "PROPERTY_USE_CODE": "property_use_code",
                "COUNTY_CODE": "county_code",
                "YEAR": "year"
            },
            "SDF": {
                "PARCEL_ID": "parcel_id",
                "SALE_DATE": "sale_date",
                "SALE_PRICE": "sale_price",
                "QUALIFIED_SALE": "qualified_sale",
                "COUNTY_CODE": "county_code",
                "YEAR": "year"
            }
        }

    async def process_files(self, downloaded_files: List[Any]) -> Dict[str, Any]:
        """Process a list of downloaded files"""
        logger.info(f"⚙️ Starting processing of {len(downloaded_files)} files...")
        
        processing_start = datetime.now()
        results = []
        errors = []
        total_records_processed = 0
        total_records_valid = 0
        
        # Process files concurrently with limited parallelism
        semaphore = asyncio.Semaphore(min(self.max_workers, len(downloaded_files)))
        
        tasks = []
        for file_metadata in downloaded_files:
            task = asyncio.create_task(
                self._process_single_file(semaphore, file_metadata)
            )
            tasks.append(task)
        
        # Wait for all processing tasks to complete
        processing_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        for result in processing_results:
            if isinstance(result, Exception):
                errors.append({
                    "component": "file_processing",
                    "error": str(result),
                    "timestamp": datetime.now()
                })
            elif result:
                results.append(result)
                total_records_processed += result.records_processed
                total_records_valid += result.records_valid
                
                if result.errors:
                    errors.extend(result.errors)
        
        processing_duration = (datetime.now() - processing_start).total_seconds()
        
        # Update statistics
        self.stats["files_processed"] += len(results)
        self.stats["records_processed"] += total_records_processed
        self.stats["records_valid"] += total_records_valid
        self.stats["processing_errors"] += len(errors)
        self.stats["last_processing"] = datetime.now()
        
        # Update average processing time
        if self.stats["files_processed"] > 0:
            self.stats["average_processing_time"] = (
                (self.stats["average_processing_time"] * (self.stats["files_processed"] - len(results)) + 
                 processing_duration) / self.stats["files_processed"]
            )
        
        logger.info(f"✅ Processing complete: {len(results)} files processed, "
                   f"{total_records_processed} records processed, "
                   f"{total_records_valid} valid records "
                   f"({processing_duration:.2f}s)")
        
        return {
            "files_processed": len(results),
            "processing_results": results,
            "processed_data": [r for result in results for r in result.processed_data] if results else [],
            "total_records_processed": total_records_processed,
            "total_records_valid": total_records_valid,
            "processing_duration": processing_duration,
            "errors": errors
        }

    async def _process_single_file(self, semaphore: asyncio.Semaphore, 
                                 file_metadata: Any) -> Optional[ProcessingResult]:
        """Process a single file with error handling"""
        async with semaphore:
            start_time = datetime.now()
            
            try:
                # Extract file information
                filename = getattr(file_metadata, 'filename', str(file_metadata))
                local_path = getattr(file_metadata, 'local_path', str(file_metadata))
                file_type = getattr(file_metadata, 'file_type', self._detect_file_type(filename))
                county_code = getattr(file_metadata, 'county_code', self._extract_county_code(filename))
                year = getattr(file_metadata, 'year', self._extract_year(filename))
                
                if not local_path or not Path(local_path).exists():
                    raise FileNotFoundError(f"File not found: {local_path}")
                
                logger.info(f"Processing {filename} ({file_type}, County: {county_code}, Year: {year})")
                
                # Detect file encoding
                encoding = await self._detect_encoding(Path(local_path))
                
                # Process the file in batches
                processed_records = []
                total_records = 0
                valid_records = 0
                errors = []
                
                async for batch_result in self._process_file_in_batches(
                    Path(local_path), file_type, encoding
                ):
                    total_records += batch_result["records_count"]
                    valid_records += batch_result["valid_records_count"]
                    processed_records.extend(batch_result["processed_records"])
                    errors.extend(batch_result["errors"])
                
                # Calculate data quality score
                quality_score = valid_records / total_records if total_records > 0 else 0.0
                
                processing_duration = (datetime.now() - start_time).total_seconds()
                
                result = ProcessingResult(
                    filename=filename,
                    file_type=file_type,
                    county_code=county_code,
                    year=year,
                    records_processed=total_records,
                    records_valid=valid_records,
                    records_invalid=total_records - valid_records,
                    data_quality_score=quality_score,
                    processing_duration=processing_duration,
                    errors=errors,
                    processed_data=processed_records
                )
                
                logger.info(f"✅ Processed {filename}: {total_records} records, "
                           f"{valid_records} valid ({quality_score:.1%} quality)")
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to process {getattr(file_metadata, 'filename', 'unknown')}: {e}")
                
                return ProcessingResult(
                    filename=getattr(file_metadata, 'filename', 'unknown'),
                    file_type=getattr(file_metadata, 'file_type', 'unknown'),
                    county_code=getattr(file_metadata, 'county_code', 'unknown'),
                    year=getattr(file_metadata, 'year', 'unknown'),
                    records_processed=0,
                    records_valid=0,
                    records_invalid=0,
                    data_quality_score=0.0,
                    processing_duration=(datetime.now() - start_time).total_seconds(),
                    errors=[{
                        "component": "file_processing",
                        "filename": getattr(file_metadata, 'filename', 'unknown'),
                        "error": str(e),
                        "timestamp": datetime.now()
                    }],
                    processed_data=[]
                )

    async def _detect_encoding(self, file_path: Path) -> str:
        """Detect the encoding of a file"""
        try:
            # Try each encoding option
            for encoding in self.encoding_options:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Read first few lines to test encoding
                        for _ in range(10):
                            line = f.readline()
                            if not line:
                                break
                    logger.debug(f"Detected encoding {encoding} for {file_path.name}")
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            # Default to utf-8 if nothing else works
            logger.warning(f"Could not detect encoding for {file_path.name}, defaulting to utf-8")
            return 'utf-8'
            
        except Exception as e:
            logger.warning(f"Encoding detection failed for {file_path.name}: {e}")
            return 'utf-8'

    async def _process_file_in_batches(self, file_path: Path, file_type: str, 
                                     encoding: str) -> Iterator[Dict[str, Any]]:
        """Process a file in batches to handle large files efficiently"""
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.reader(f, delimiter='\t')  # Most Florida files are tab-delimited
                
                # Read header
                try:
                    headers = next(reader)
                    headers = [h.strip().upper() for h in headers]
                except StopIteration:
                    logger.error(f"Empty file: {file_path.name}")
                    return
                
                # Get field mappings for this file type
                field_mapping = self.field_mappings.get(file_type, {})
                validation_rules = self.validation_rules.get(file_type, [])
                
                batch_records = []
                batch_count = 0
                
                for row_number, row in enumerate(reader, start=2):  # Start at 2 because of header
                    try:
                        # Convert row to dictionary
                        if len(row) != len(headers):
                            # Handle missing or extra columns
                            row = row + [''] * (len(headers) - len(row))
                            row = row[:len(headers)]
                        
                        record = dict(zip(headers, row))
                        
                        # Apply field mappings
                        mapped_record = {}
                        for original_field, mapped_field in field_mapping.items():
                            if original_field in record:
                                mapped_record[mapped_field] = record[original_field].strip()
                        
                        # Add metadata
                        mapped_record.update({
                            'file_type': file_type,
                            'source_file': file_path.name,
                            'row_number': row_number,
                            'processed_at': datetime.now().isoformat()
                        })
                        
                        batch_records.append(mapped_record)
                        batch_count += 1
                        
                        # Process batch when it reaches the configured size
                        if len(batch_records) >= self.batch_size:
                            yield await self._process_batch(batch_records, validation_rules, file_type)
                            batch_records = []
                        
                    except Exception as e:
                        logger.warning(f"Error processing row {row_number} in {file_path.name}: {e}")
                        continue
                
                # Process final batch if any records remain
                if batch_records:
                    yield await self._process_batch(batch_records, validation_rules, file_type)
                
        except Exception as e:
            logger.error(f"Failed to process file {file_path.name}: {e}")
            yield {
                "records_count": 0,
                "valid_records_count": 0,
                "processed_records": [],
                "errors": [{
                    "component": "batch_processing",
                    "filename": file_path.name,
                    "error": str(e),
                    "timestamp": datetime.now()
                }]
            }

    async def _process_batch(self, batch_records: List[Dict[str, Any]], 
                           validation_rules: List[ValidationRule], 
                           file_type: str) -> Dict[str, Any]:
        """Process a batch of records with validation and transformation"""
        valid_records = []
        errors = []
        
        for record in batch_records:
            try:
                # Validate record if validation is enabled
                if self.validation_enabled:
                    validation_errors = self._validate_record(record, validation_rules)
                    
                    # Filter out records with critical errors
                    critical_errors = [e for e in validation_errors if e.get("severity") == "error"]
                    if critical_errors:
                        errors.extend(validation_errors)
                        continue
                    
                    # Log warnings but include the record
                    warning_errors = [e for e in validation_errors if e.get("severity") == "warning"]
                    if warning_errors:
                        errors.extend(warning_errors)
                
                # Apply data transformations
                transformed_record = self._transform_record(record, file_type)
                
                # Generate record hash for deduplication
                transformed_record['record_hash'] = self._generate_record_hash(transformed_record)
                
                valid_records.append(transformed_record)
                
            except Exception as e:
                errors.append({
                    "component": "record_processing",
                    "row_number": record.get("row_number", "unknown"),
                    "error": str(e),
                    "timestamp": datetime.now()
                })
        
        return {
            "records_count": len(batch_records),
            "valid_records_count": len(valid_records),
            "processed_records": valid_records,
            "errors": errors
        }

    def _validate_record(self, record: Dict[str, Any], 
                        validation_rules: List[ValidationRule]) -> List[Dict[str, Any]]:
        """Validate a record against validation rules"""
        errors = []
        
        for rule in validation_rules:
            field_value = record.get(rule.field_name, "").strip()
            
            try:
                if rule.rule_type == "required":
                    if not field_value:
                        errors.append({
                            "component": "validation",
                            "field": rule.field_name,
                            "rule": "required",
                            "severity": rule.severity,
                            "error": f"Required field '{rule.field_name}' is empty",
                            "row_number": record.get("row_number"),
                            "timestamp": datetime.now()
                        })
                
                elif rule.rule_type == "format" and field_value:
                    import re
                    pattern = rule.rule_params.get("pattern", "")
                    if pattern and not re.match(pattern, field_value):
                        errors.append({
                            "component": "validation",
                            "field": rule.field_name,
                            "rule": "format",
                            "severity": rule.severity,
                            "error": f"Field '{rule.field_name}' does not match required format",
                            "value": field_value,
                            "row_number": record.get("row_number"),
                            "timestamp": datetime.now()
                        })
                
                elif rule.rule_type == "range" and field_value:
                    try:
                        numeric_value = float(field_value.replace('$', '').replace(',', ''))
                        min_val = rule.rule_params.get("min")
                        max_val = rule.rule_params.get("max")
                        
                        if min_val is not None and numeric_value < min_val:
                            errors.append({
                                "component": "validation",
                                "field": rule.field_name,
                                "rule": "range",
                                "severity": rule.severity,
                                "error": f"Field '{rule.field_name}' below minimum value {min_val}",
                                "value": field_value,
                                "row_number": record.get("row_number"),
                                "timestamp": datetime.now()
                            })
                        
                        if max_val is not None and numeric_value > max_val:
                            errors.append({
                                "component": "validation",
                                "field": rule.field_name,
                                "rule": "range",
                                "severity": rule.severity,
                                "error": f"Field '{rule.field_name}' above maximum value {max_val}",
                                "value": field_value,
                                "row_number": record.get("row_number"),
                                "timestamp": datetime.now()
                            })
                    except ValueError:
                        errors.append({
                            "component": "validation",
                            "field": rule.field_name,
                            "rule": "range",
                            "severity": rule.severity,
                            "error": f"Field '{rule.field_name}' is not numeric",
                            "value": field_value,
                            "row_number": record.get("row_number"),
                            "timestamp": datetime.now()
                        })
                
                elif rule.rule_type == "enum" and field_value:
                    allowed_values = rule.rule_params.get("values", [])
                    if field_value not in allowed_values:
                        errors.append({
                            "component": "validation",
                            "field": rule.field_name,
                            "rule": "enum",
                            "severity": rule.severity,
                            "error": f"Field '{rule.field_name}' has invalid value",
                            "value": field_value,
                            "allowed_values": allowed_values,
                            "row_number": record.get("row_number"),
                            "timestamp": datetime.now()
                        })
                        
            except Exception as e:
                errors.append({
                    "component": "validation",
                    "field": rule.field_name,
                    "rule": rule.rule_type,
                    "severity": "error",
                    "error": f"Validation error for '{rule.field_name}': {str(e)}",
                    "row_number": record.get("row_number"),
                    "timestamp": datetime.now()
                })
        
        return errors

    def _transform_record(self, record: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """Apply data transformations to a record"""
        transformed = record.copy()
        
        try:
            # Standardize text fields
            for field in ['owner_name', 'property_address', 'owner_address']:
                if field in transformed and transformed[field]:
                    transformed[field] = self._standardize_text(transformed[field])
            
            # Normalize numeric fields
            for field in ['assessed_value', 'just_value', 'sale_price']:
                if field in transformed and transformed[field]:
                    transformed[field] = self._normalize_currency(transformed[field])
            
            # Standardize dates
            for field in ['sale_date']:
                if field in transformed and transformed[field]:
                    transformed[field] = self._standardize_date(transformed[field])
            
            # Add computed fields
            if file_type == "SDF" and 'sale_price' in transformed:
                transformed['price_per_sqft'] = self._calculate_price_per_sqft(transformed)
            
        except Exception as e:
            logger.warning(f"Transformation error for record: {e}")
        
        return transformed

    def _standardize_text(self, text: str) -> str:
        """Standardize text field (title case, remove extra spaces)"""
        if not text:
            return ""
        return ' '.join(text.strip().title().split())

    def _normalize_currency(self, value: str) -> Optional[float]:
        """Normalize currency values to float"""
        if not value:
            return None
        try:
            # Remove currency symbols and commas
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _standardize_date(self, date_str: str) -> Optional[str]:
        """Standardize date to YYYY-MM-DD format"""
        if not date_str:
            return None
        
        # Common date formats in Florida data
        formats = ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _calculate_price_per_sqft(self, record: Dict[str, Any]) -> Optional[float]:
        """Calculate price per square foot if possible"""
        try:
            sale_price = record.get('sale_price')
            # This would need living area or building area from NAP data
            # For now, return None as we don't have the area data in SDF files
            return None
        except:
            return None

    def _generate_record_hash(self, record: Dict[str, Any]) -> str:
        """Generate a hash for record deduplication"""
        try:
            # Create hash from key fields
            key_fields = ['parcel_id', 'county_code', 'year']
            hash_input = ''.join(str(record.get(field, '')) for field in key_fields)
            return hashlib.md5(hash_input.encode()).hexdigest()
        except:
            return hashlib.md5(str(record).encode()).hexdigest()

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        filename_upper = filename.upper()
        if 'NAL' in filename_upper:
            return 'NAL'
        elif 'NAP' in filename_upper:
            return 'NAP'
        elif 'SDF' in filename_upper:
            return 'SDF'
        else:
            return 'UNKNOWN'

    def _extract_county_code(self, filename: str) -> str:
        """Extract county code from filename"""
        import re
        match = re.search(r'(\d{2})', filename)
        return match.group(1) if match else 'UNKNOWN'

    def _extract_year(self, filename: str) -> str:
        """Extract year from filename"""
        import re
        match = re.search(r'(\d{4}P?)', filename)
        return match.group(1) if match else 'UNKNOWN'

    async def get_health_status(self):
        """Get health status of the processing agent"""
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class AgentHealth:
            name: str
            status: str
            last_run: Optional[datetime]
            success_rate: float
            error_count: int
            performance_metrics: Dict[str, float]
            alerts: List[str]
        
        # Calculate success rate based on data quality
        total_records = self.stats["records_processed"]
        valid_records = self.stats["records_valid"]
        success_rate = valid_records / total_records if total_records > 0 else 1.0
        
        # Determine status
        if success_rate > 0.95:
            status = "healthy"
        elif success_rate > 0.8:
            status = "degraded"
        else:
            status = "failed"
        
        alerts = []
        if self.stats["processing_errors"] > 0:
            alerts.append(f"{self.stats['processing_errors']} processing errors")
        
        if success_rate < 0.9:
            alerts.append(f"Data quality below 90% ({success_rate:.1%})")
        
        if self.stats["last_processing"]:
            time_since_last = datetime.now() - self.stats["last_processing"]
            if time_since_last > timedelta(days=2):
                alerts.append("No processing in over 2 days")
        
        return AgentHealth(
            name="processing_agent",
            status=status,
            last_run=self.stats["last_processing"],
            success_rate=success_rate,
            error_count=self.stats["processing_errors"],
            performance_metrics={
                "files_processed": self.stats["files_processed"],
                "records_processed": self.stats["records_processed"],
                "data_quality_rate": success_rate,
                "average_processing_time": self.stats["average_processing_time"]
            },
            alerts=alerts
        )