#!/usr/bin/env python3
"""
Florida Data Processor Agent
Processes downloaded Florida property data files for database import.
Handles incremental updates, data validation, and format conversion.
"""

import asyncio
import logging
import pandas as pd
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass, asdict
import sqlite3
import csv
import re
from decimal import Decimal, InvalidOperation
import zipfile

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    file_path: str
    file_type: str  # NAL, NAP, SDF
    county: str
    total_records: int
    valid_records: int
    invalid_records: int
    new_records: int
    updated_records: int
    duplicates: int
    processing_time: float
    success: bool
    error: Optional[str] = None
    output_file: Optional[str] = None
    checksum: Optional[str] = None
    validation_errors: List[str] = None

@dataclass
class DataRow:
    """Standardized data row"""
    source_file: str
    row_number: int
    data: Dict[str, Any]
    errors: List[str]
    is_valid: bool

class FloridaDataProcessor:
    """Processes Florida Department of Revenue data files"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output_directory', 'florida_daily_updates/processed'))
        self.backup_dir = Path(config.get('backup_directory', 'florida_daily_updates/backups'))
        self.batch_size = config.get('batch_size', 10000)
        self.validation_enabled = config.get('enable_validation', True)
        self.create_backups = config.get('create_backups', True)
        self.max_errors = config.get('max_validation_errors', 1000)
        
        # Processing state database
        self.db_path = Path(config.get('state_db_path', 'florida_processor_state.db'))
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load field mappings and validation rules
        self.field_mappings = self._load_field_mappings()
        self.validation_rules = self._load_validation_rules()
        
        # Statistics
        self.processing_stats = {
            'files_processed': 0,
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'processing_time': 0.0
        }
    
    def _init_database(self):
        """Initialize SQLite database for processing state"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    county TEXT NOT NULL,
                    checksum TEXT,
                    total_records INTEGER,
                    valid_records INTEGER,
                    invalid_records INTEGER,
                    new_records INTEGER,
                    updated_records INTEGER,
                    processing_time REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    error TEXT,
                    output_file TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS record_checksums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_type TEXT NOT NULL,
                    county TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_type, county, record_key)
                )
            ''')
            
            conn.commit()
    
    def _load_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load field mappings for different file types"""
        return {
            'NAL': {
                'COUNTY': 'county_code',
                'PARCEL_ID': 'parcel_id',
                'PARCEL_NUM': 'parcel_number',
                'OWNER_NAME': 'owner_name',
                'OWNER_ADDR1': 'owner_address_1',
                'OWNER_ADDR2': 'owner_address_2',
                'OWNER_CITY': 'owner_city',
                'OWNER_STATE': 'owner_state',
                'OWNER_ZIP': 'owner_zip',
                'PROPERTY_ADDRESS': 'property_address',
                'PROPERTY_CITY': 'property_city',
                'PROPERTY_ZIP': 'property_zip',
                'LEGAL_DESC': 'legal_description',
                'PROPERTY_USE_CD': 'property_use_code',
                'LAND_VAL': 'land_value',
                'JUST_VAL': 'just_value',
                'ASSESSED_VAL': 'assessed_value'
            },
            'NAP': {
                'COUNTY': 'county_code',
                'PARCEL_ID': 'parcel_id',
                'PARCEL_NUM': 'parcel_number',
                'LAND_VAL': 'land_value',
                'JUST_VAL': 'just_value',
                'ASSESSED_VAL': 'assessed_value',
                'EXEMPT_VAL': 'exempt_value',
                'TAXABLE_VAL': 'taxable_value',
                'TAX_YR': 'tax_year',
                'MILLAGE': 'millage_rate'
            },
            'SDF': {
                'COUNTY': 'county_code',
                'PARCEL_ID': 'parcel_id',
                'PARCEL_NUM': 'parcel_number',
                'SALE_DATE': 'sale_date',
                'SALE_PRICE': 'sale_price',
                'DEED_BOOK': 'deed_book',
                'DEED_PAGE': 'deed_page',
                'GRANTOR': 'grantor',
                'GRANTEE': 'grantee',
                'DEED_TYPE': 'deed_type',
                'QUAL_CD': 'qualification_code'
            }
        }
    
    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules for different fields"""
        return {
            'parcel_id': {
                'required': True,
                'type': 'string',
                'max_length': 50,
                'pattern': r'^[A-Za-z0-9\-_]+$'
            },
            'county_code': {
                'required': True,
                'type': 'string',
                'valid_values': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                               '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                               '21', '22', '23', '24', '25']  # Florida county codes
            },
            'land_value': {
                'type': 'decimal',
                'min_value': 0,
                'max_value': 999999999.99
            },
            'just_value': {
                'type': 'decimal',
                'min_value': 0,
                'max_value': 999999999.99
            },
            'assessed_value': {
                'type': 'decimal',
                'min_value': 0,
                'max_value': 999999999.99
            },
            'sale_price': {
                'type': 'decimal',
                'min_value': 0,
                'max_value': 999999999.99
            },
            'sale_date': {
                'type': 'date',
                'format': 'YYYYMMDD'
            },
            'owner_name': {
                'type': 'string',
                'max_length': 255,
                'required': False
            },
            'property_address': {
                'type': 'string',
                'max_length': 255,
                'required': False
            }
        }
    
    async def process_file(self, file_path: str, file_type: str, county: str) -> ProcessingResult:
        """Process a single data file"""
        start_time = datetime.now()
        file_path_obj = Path(file_path)
        
        try:
            logger.info(f"Processing {file_type} file: {file_path}")
            
            # Validate file exists
            if not file_path_obj.exists():
                raise Exception(f"File not found: {file_path}")
            
            # Calculate file checksum
            file_checksum = await self._calculate_file_checksum(file_path_obj)
            
            # Check if already processed
            if await self._is_already_processed(file_path, file_checksum):
                logger.info(f"File already processed: {file_path}")
                return self._get_cached_result(file_path, file_checksum)
            
            # Create backup if enabled
            if self.create_backups:
                await self._create_backup(file_path_obj)
            
            # Determine file format and read data
            data_iterator = await self._read_data_file(file_path_obj, file_type)
            
            # Process data in batches
            processing_result = await self._process_data_batches(
                data_iterator, file_path, file_type, county, file_checksum
            )
            
            # Save processing result
            await self._save_processing_result(processing_result)
            
            # Update statistics
            self._update_processing_stats(processing_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_result.processing_time = processing_time
            
            logger.info(f"Completed processing {file_type} file: {processing_result.valid_records:,} valid records")
            
            return processing_result
            
        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                file_path=file_path,
                file_type=file_type,
                county=county,
                total_records=0,
                valid_records=0,
                invalid_records=0,
                new_records=0,
                updated_records=0,
                duplicates=0,
                processing_time=processing_time,
                success=False,
                error=error_msg,
                validation_errors=[]
            )
    
    async def _read_data_file(self, file_path: Path, file_type: str) -> Iterator[Dict[str, str]]:
        """Read data file and return iterator of records"""
        if file_path.suffix.lower() == '.zip':
            return await self._read_zip_file(file_path, file_type)
        elif file_path.suffix.lower() in ['.csv', '.txt']:
            return await self._read_csv_file(file_path)
        else:
            raise Exception(f"Unsupported file format: {file_path.suffix}")
    
    async def _read_zip_file(self, zip_path: Path, file_type: str) -> Iterator[Dict[str, str]]:
        """Read CSV data from zip file"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the main data file
            data_files = [name for name in zip_ref.namelist() 
                         if name.lower().endswith(('.csv', '.txt')) and not name.startswith('__')]
            
            if not data_files:
                raise Exception("No data files found in zip archive")
            
            # Use the first data file found
            data_file = data_files[0]
            logger.info(f"Reading {data_file} from {zip_path}")
            
            with zip_ref.open(data_file) as f:
                # Detect encoding
                content = f.read(8192)
                f.seek(0)
                
                encoding = 'utf-8'
                if b'\xff\xfe' in content[:2] or b'\xfe\xff' in content[:2]:
                    encoding = 'utf-16'
                elif b'\xef\xbb\xbf' in content[:3]:
                    encoding = 'utf-8-sig'
                
                # Read CSV data
                text_content = f.read().decode(encoding, errors='replace')
                
                # Parse CSV
                reader = csv.DictReader(text_content.splitlines())
                for row in reader:
                    yield row
    
    async def _read_csv_file(self, csv_path: Path) -> Iterator[Dict[str, str]]:
        """Read CSV file"""
        # Detect encoding
        with open(csv_path, 'rb') as f:
            content = f.read(8192)
            
        encoding = 'utf-8'
        if b'\xff\xfe' in content[:2] or b'\xfe\xff' in content[:2]:
            encoding = 'utf-16'
        elif b'\xef\xbb\xbf' in content[:3]:
            encoding = 'utf-8-sig'
        
        # Read CSV
        with open(csv_path, 'r', encoding=encoding, errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row
    
    async def _process_data_batches(self, data_iterator: Iterator[Dict[str, str]], 
                                  file_path: str, file_type: str, county: str, 
                                  file_checksum: str) -> ProcessingResult:
        """Process data in batches"""
        total_records = 0
        valid_records = 0
        invalid_records = 0
        new_records = 0
        updated_records = 0
        duplicates = 0
        validation_errors = []
        
        # Prepare output file
        output_file = self._get_output_file_path(file_path, file_type, county)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        batch_data = []
        batch_number = 1
        
        try:
            for row_number, raw_row in enumerate(data_iterator, 1):
                total_records += 1
                
                # Process row
                data_row = await self._process_row(raw_row, file_path, row_number, file_type)
                
                if data_row.is_valid:
                    valid_records += 1
                    
                    # Check if record is new or updated
                    record_status = await self._check_record_status(data_row, file_type, county)
                    
                    if record_status == 'new':
                        new_records += 1
                    elif record_status == 'updated':
                        updated_records += 1
                    elif record_status == 'duplicate':
                        duplicates += 1
                    
                    batch_data.append(data_row)
                else:
                    invalid_records += 1
                    validation_errors.extend(data_row.errors)
                    
                    # Limit validation errors to prevent memory issues
                    if len(validation_errors) > self.max_errors:
                        validation_errors = validation_errors[:self.max_errors]
                        validation_errors.append(f"... and {invalid_records - self.max_errors} more validation errors")
                        break
                
                # Process batch
                if len(batch_data) >= self.batch_size:
                    await self._write_batch(batch_data, output_file, batch_number == 1)
                    batch_data = []
                    batch_number += 1
                    
                    logger.debug(f"Processed batch {batch_number - 1}: {len(batch_data)} records")
            
            # Process final batch
            if batch_data:
                await self._write_batch(batch_data, output_file, batch_number == 1)
            
            # Calculate output file checksum
            output_checksum = await self._calculate_file_checksum(output_file) if output_file.exists() else None
            
            return ProcessingResult(
                file_path=file_path,
                file_type=file_type,
                county=county,
                total_records=total_records,
                valid_records=valid_records,
                invalid_records=invalid_records,
                new_records=new_records,
                updated_records=updated_records,
                duplicates=duplicates,
                processing_time=0.0,  # Will be set later
                success=True,
                output_file=str(output_file),
                checksum=output_checksum,
                validation_errors=validation_errors[:100]  # Limit errors in result
            )
            
        except Exception as e:
            logger.error(f"Error processing batches: {e}")
            raise
    
    async def _process_row(self, raw_row: Dict[str, str], file_path: str, 
                          row_number: int, file_type: str) -> DataRow:
        """Process a single data row"""
        errors = []
        processed_data = {}
        
        # Get field mappings for this file type
        field_mapping = self.field_mappings.get(file_type, {})
        
        try:
            # Map and validate fields
            for source_field, target_field in field_mapping.items():
                raw_value = raw_row.get(source_field, '').strip()
                
                # Apply validation
                if self.validation_enabled:
                    validated_value, field_errors = self._validate_field(
                        target_field, raw_value, self.validation_rules.get(target_field, {})
                    )
                    errors.extend(field_errors)
                    processed_data[target_field] = validated_value
                else:
                    processed_data[target_field] = raw_value
            
            # Add metadata
            processed_data['source_file'] = file_path
            processed_data['row_number'] = row_number
            processed_data['processed_at'] = datetime.now().isoformat()
            
            return DataRow(
                source_file=file_path,
                row_number=row_number,
                data=processed_data,
                errors=[f"Row {row_number}: {error}" for error in errors],
                is_valid=len(errors) == 0
            )
            
        except Exception as e:
            return DataRow(
                source_file=file_path,
                row_number=row_number,
                data={},
                errors=[f"Row {row_number}: Critical processing error: {str(e)}"],
                is_valid=False
            )
    
    def _validate_field(self, field_name: str, value: str, rules: Dict[str, Any]) -> Tuple[Any, List[str]]:
        """Validate a field value against rules"""
        errors = []
        validated_value = value
        
        # Check required
        if rules.get('required', False) and not value:
            errors.append(f"{field_name} is required")
            return None, errors
        
        # Skip validation for empty optional fields
        if not value and not rules.get('required', False):
            return None, errors
        
        # Type validation
        field_type = rules.get('type', 'string')
        
        if field_type == 'string':
            max_length = rules.get('max_length')
            if max_length and len(value) > max_length:
                errors.append(f"{field_name} exceeds maximum length of {max_length}")
            
            pattern = rules.get('pattern')
            if pattern and not re.match(pattern, value):
                errors.append(f"{field_name} format is invalid")
            
            valid_values = rules.get('valid_values')
            if valid_values and value not in valid_values:
                errors.append(f"{field_name} must be one of: {', '.join(valid_values)}")
        
        elif field_type == 'decimal':
            try:
                validated_value = Decimal(value.replace(',', ''))
                
                min_value = rules.get('min_value')
                if min_value is not None and validated_value < min_value:
                    errors.append(f"{field_name} must be >= {min_value}")
                
                max_value = rules.get('max_value')
                if max_value is not None and validated_value > max_value:
                    errors.append(f"{field_name} must be <= {max_value}")
                    
            except (InvalidOperation, ValueError):
                errors.append(f"{field_name} must be a valid decimal number")
                validated_value = None
        
        elif field_type == 'date':
            date_format = rules.get('format', 'YYYYMMDD')
            try:
                if date_format == 'YYYYMMDD' and len(value) == 8:
                    validated_value = datetime.strptime(value, '%Y%m%d').date()
                elif date_format == 'MM/DD/YYYY':
                    validated_value = datetime.strptime(value, '%m/%d/%Y').date()
                else:
                    raise ValueError("Unknown date format")
            except ValueError:
                errors.append(f"{field_name} must be a valid date in format {date_format}")
                validated_value = None
        
        return validated_value, errors
    
    async def _check_record_status(self, data_row: DataRow, file_type: str, county: str) -> str:
        """Check if record is new, updated, or duplicate"""
        # Create record key (typically parcel_id or similar)
        record_key = data_row.data.get('parcel_id')
        if not record_key:
            return 'new'  # Default to new if no key
        
        # Create record hash for change detection
        record_hash = self._calculate_record_hash(data_row.data)
        
        # Check database for existing record
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT checksum FROM record_checksums 
                WHERE file_type = ? AND county = ? AND record_key = ?
            ''', (file_type, county, record_key))
            
            result = cursor.fetchone()
            
            if result is None:
                # New record
                cursor.execute('''
                    INSERT INTO record_checksums (file_type, county, record_key, checksum)
                    VALUES (?, ?, ?, ?)
                ''', (file_type, county, record_key, record_hash))
                conn.commit()
                return 'new'
            
            existing_hash = result[0]
            if existing_hash != record_hash:
                # Updated record
                cursor.execute('''
                    UPDATE record_checksums 
                    SET checksum = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE file_type = ? AND county = ? AND record_key = ?
                ''', (record_hash, file_type, county, record_key))
                conn.commit()
                return 'updated'
            else:
                # Duplicate record
                return 'duplicate'
    
    def _calculate_record_hash(self, record_data: Dict[str, Any]) -> str:
        """Calculate hash for record to detect changes"""
        # Create consistent string representation
        sorted_items = sorted(record_data.items())
        record_str = json.dumps(sorted_items, default=str, sort_keys=True)
        
        return hashlib.md5(record_str.encode()).hexdigest()
    
    async def _write_batch(self, batch_data: List[DataRow], output_file: Path, write_header: bool = True):
        """Write batch of data to output file"""
        mode = 'w' if write_header else 'a'
        
        if not batch_data:
            return
        
        # Get field names from first record
        field_names = list(batch_data[0].data.keys())
        
        with open(output_file, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            
            if write_header:
                writer.writeheader()
            
            for data_row in batch_data:
                # Convert all values to strings for CSV writing
                csv_row = {}
                for key, value in data_row.data.items():
                    if value is None:
                        csv_row[key] = ''
                    elif isinstance(value, (date, datetime)):
                        csv_row[key] = value.isoformat()
                    elif isinstance(value, Decimal):
                        csv_row[key] = str(value)
                    else:
                        csv_row[key] = str(value)
                
                writer.writerow(csv_row)
    
    def _get_output_file_path(self, input_file: str, file_type: str, county: str) -> Path:
        """Get output file path for processed data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{county.lower()}_{file_type.lower()}_processed_{timestamp}.csv"
        
        return self.output_dir / filename
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _is_already_processed(self, file_path: str, checksum: str) -> bool:
        """Check if file has already been processed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM processing_history 
                WHERE file_path = ? AND checksum = ? AND success = 1
            ''', (file_path, checksum))
            
            return cursor.fetchone() is not None
    
    def _get_cached_result(self, file_path: str, checksum: str) -> ProcessingResult:
        """Get cached processing result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM processing_history 
                WHERE file_path = ? AND checksum = ? AND success = 1
                ORDER BY timestamp DESC LIMIT 1
            ''', (file_path, checksum))
            
            row = cursor.fetchone()
            if row:
                return ProcessingResult(
                    file_path=row[1],
                    file_type=row[2],
                    county=row[3],
                    total_records=row[5],
                    valid_records=row[6],
                    invalid_records=row[7],
                    new_records=row[8],
                    updated_records=row[9],
                    duplicates=0,  # Not stored in old records
                    processing_time=row[10],
                    success=True,
                    output_file=row[14],
                    checksum=row[4]
                )
        
        # Should not reach here if is_already_processed returned True
        raise Exception("Cached result not found")
    
    async def _create_backup(self, file_path: Path):
        """Create backup of input file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
    
    async def _save_processing_result(self, result: ProcessingResult):
        """Save processing result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processing_history 
                (file_path, file_type, county, checksum, total_records, valid_records, 
                 invalid_records, new_records, updated_records, processing_time, 
                 success, error, output_file, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.file_path,
                result.file_type,
                result.county,
                result.checksum,
                result.total_records,
                result.valid_records,
                result.invalid_records,
                result.new_records,
                result.updated_records,
                result.processing_time,
                result.success,
                result.error,
                result.output_file,
                json.dumps(asdict(result), default=str)
            ))
            conn.commit()
    
    def _update_processing_stats(self, result: ProcessingResult):
        """Update processing statistics"""
        self.processing_stats['files_processed'] += 1
        
        if result.success:
            self.processing_stats['total_records'] += result.total_records
            self.processing_stats['valid_records'] += result.valid_records
            self.processing_stats['invalid_records'] += result.invalid_records
            self.processing_stats['processing_time'] += result.processing_time
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats.copy()
    
    def get_processing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get processing history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM processing_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Standalone execution for testing
async def main():
    """Test the processor"""
    config = {
        'output_directory': 'test_output',
        'backup_directory': 'test_backups',
        'batch_size': 5000,
        'enable_validation': True,
        'create_backups': True
    }
    
    processor = FloridaDataProcessor(config)
    
    # Test file (replace with actual file path)
    test_file = "test_data.csv"
    
    if Path(test_file).exists():
        result = await processor.process_file(test_file, 'NAL', 'broward')
        
        print(f"Processing result:")
        print(f"  Success: {result.success}")
        print(f"  Total records: {result.total_records:,}")
        print(f"  Valid records: {result.valid_records:,}")
        print(f"  Invalid records: {result.invalid_records:,}")
        print(f"  New records: {result.new_records:,}")
        print(f"  Updated records: {result.updated_records:,}")
        print(f"  Processing time: {result.processing_time:.1f}s")
        print(f"  Output file: {result.output_file}")
        
        if result.validation_errors:
            print(f"  Validation errors (first 5):")
            for error in result.validation_errors[:5]:
                print(f"    {error}")
    else:
        print(f"Test file {test_file} not found")

if __name__ == "__main__":
    asyncio.run(main())