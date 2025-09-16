#!/usr/bin/env python3
"""
NAL CSV Parser Agent
===================
High-performance CSV parsing agent for NAL data files.
Handles large files (753K+ records) with memory-efficient streaming and validation.
"""

import asyncio
import logging
import csv
import io
import os
import sys
from typing import Dict, List, Any, Optional, AsyncIterator, Tuple
from pathlib import Path
import pandas as pd
import aiofiles
from dataclasses import dataclass
import chardet
import time

logger = logging.getLogger(__name__)

@dataclass
class ParseResult:
    """Result of parsing operation"""
    success: bool
    records_parsed: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    processing_time: float = 0
    memory_usage_mb: float = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class HeaderInfo:
    """Information about CSV header structure"""
    fields: List[str]
    field_count: int
    encoding: str
    delimiter: str
    has_quotes: bool
    estimated_record_size: int

class NALCSVParserAgent:
    """
    Agent specialized in parsing NAL CSV files efficiently
    
    Features:
    - Memory-efficient streaming for large files
    - Automatic encoding detection
    - Field validation and type inference
    - Progress tracking and error handling
    - Resumable parsing with checkpoints
    """
    
    def __init__(self, csv_file_path: str, chunk_size: int = 10000):
        self.csv_file_path = Path(csv_file_path)
        self.chunk_size = chunk_size
        self.header_info: Optional[HeaderInfo] = None
        self.total_records: Optional[int] = None
        
        # Parsing configuration
        self.max_field_size = 1000000  # 1MB per field
        self.encoding = 'utf-8'
        self.delimiter = ','
        self.quote_char = '"'
        
        # Performance metrics
        self.parse_start_time = None
        self.records_processed = 0
        
        # Validation
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        logger.info(f"NAL CSV Parser initialized for file: {self.csv_file_path}")
        logger.info(f"File size: {self.csv_file_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    async def detect_encoding_and_format(self) -> Dict[str, Any]:
        """
        Detect CSV encoding and format parameters
        
        Returns:
            Dictionary with encoding and format information
        """
        logger.info("Detecting CSV encoding and format...")
        
        try:
            # Read sample for encoding detection
            with open(self.csv_file_path, 'rb') as f:
                raw_sample = f.read(8192)  # Read 8KB sample
                encoding_result = chardet.detect(raw_sample)
                detected_encoding = encoding_result['encoding']
                confidence = encoding_result['confidence']
            
            logger.info(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
            
            # Try to read with detected encoding
            try:
                with open(self.csv_file_path, 'r', encoding=detected_encoding) as f:
                    sample_lines = [f.readline() for _ in range(5)]
            except UnicodeDecodeError:
                logger.warning(f"Failed to read with {detected_encoding}, falling back to utf-8")
                detected_encoding = 'utf-8'
                with open(self.csv_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample_lines = [f.readline() for _ in range(5)]
            
            # Detect CSV format
            sample_text = ''.join(sample_lines)
            sniffer = csv.Sniffer()
            
            try:
                dialect = sniffer.sniff(sample_text)
                delimiter = dialect.delimiter
                quote_char = dialect.quotechar
                has_quotes = quote_char is not None
            except csv.Error:
                # Fallback to defaults
                delimiter = ','
                quote_char = '"'
                has_quotes = True
            
            # Estimate record size
            if sample_lines:
                avg_line_length = sum(len(line) for line in sample_lines) / len(sample_lines)
                estimated_record_size = int(avg_line_length)
            else:
                estimated_record_size = 1000
            
            format_info = {
                'encoding': detected_encoding,
                'delimiter': delimiter,
                'quote_char': quote_char,
                'has_quotes': has_quotes,
                'estimated_record_size': estimated_record_size,
                'sample_lines': sample_lines[:3]  # First 3 lines for inspection
            }
            
            # Update instance variables
            self.encoding = detected_encoding
            self.delimiter = delimiter
            self.quote_char = quote_char
            
            logger.info(f"CSV format detection complete:")
            logger.info(f"  Delimiter: '{delimiter}'")
            logger.info(f"  Quote char: '{quote_char}'")
            logger.info(f"  Has quotes: {has_quotes}")
            logger.info(f"  Estimated record size: {estimated_record_size} bytes")
            
            return format_info
            
        except Exception as e:
            logger.error(f"Encoding/format detection failed: {e}")
            raise
    
    async def parse_header(self) -> HeaderInfo:
        """
        Parse and analyze CSV header
        
        Returns:
            HeaderInfo with field structure details
        """
        if self.header_info is not None:
            return self.header_info
        
        logger.info("Parsing CSV header...")
        
        try:
            # Detect format if not done already
            if not hasattr(self, 'encoding'):
                await self.detect_encoding_and_format()
            
            # Read header line
            with open(self.csv_file_path, 'r', encoding=self.encoding) as f:
                reader = csv.reader(
                    f, 
                    delimiter=self.delimiter, 
                    quotechar=self.quote_char
                )
                header_row = next(reader)
            
            # Clean and validate field names
            cleaned_fields = []
            for field in header_row:
                cleaned_field = field.strip()
                if not cleaned_field:
                    logger.warning(f"Empty field name found at position {len(cleaned_fields)}")
                    cleaned_field = f"FIELD_{len(cleaned_fields)}"
                cleaned_fields.append(cleaned_field)
            
            # Check for duplicates
            field_counts = {}
            for field in cleaned_fields:
                field_counts[field] = field_counts.get(field, 0) + 1
            
            duplicates = [field for field, count in field_counts.items() if count > 1]
            if duplicates:
                logger.warning(f"Duplicate field names found: {duplicates}")
            
            self.header_info = HeaderInfo(
                fields=cleaned_fields,
                field_count=len(cleaned_fields),
                encoding=self.encoding,
                delimiter=self.delimiter,
                has_quotes=self.quote_char is not None,
                estimated_record_size=getattr(self, 'estimated_record_size', 1000)
            )
            
            logger.info(f"Header parsed successfully: {len(cleaned_fields)} fields")
            logger.debug(f"Fields: {', '.join(cleaned_fields[:10])}{'...' if len(cleaned_fields) > 10 else ''}")
            
            return self.header_info
            
        except Exception as e:
            logger.error(f"Header parsing failed: {e}")
            raise
    
    async def get_record_count(self) -> int:
        """
        Get total record count (excluding header)
        
        Returns:
            Total number of data records
        """
        if self.total_records is not None:
            return self.total_records
        
        logger.info("Counting total records...")
        start_time = time.time()
        
        try:
            record_count = 0
            
            with open(self.csv_file_path, 'r', encoding=self.encoding) as f:
                # Skip header
                next(f)
                
                # Count remaining lines efficiently
                for line in f:
                    if line.strip():  # Skip empty lines
                        record_count += 1
            
            self.total_records = record_count
            count_time = time.time() - start_time
            
            logger.info(f"Record count complete: {record_count:,} records in {count_time:.2f}s")
            
            return record_count
            
        except Exception as e:
            logger.error(f"Record counting failed: {e}")
            raise
    
    async def validate_csv_structure(self, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Validate CSV structure by analyzing a sample of records
        
        Args:
            sample_size: Number of records to sample for validation
            
        Returns:
            Validation report with findings and recommendations
        """
        logger.info(f"Validating CSV structure with sample size: {sample_size}")
        
        try:
            # Ensure header is parsed
            if self.header_info is None:
                await self.parse_header()
            
            validation_report = {
                'is_valid': True,
                'field_count_consistency': True,
                'data_type_inference': {},
                'null_percentages': {},
                'value_samples': {},
                'errors': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Initialize field analysis
            field_counts = {field: 0 for field in self.header_info.fields}
            field_nulls = {field: 0 for field in self.header_info.fields}
            field_samples = {field: [] for field in self.header_info.fields}
            field_types = {field: set() for field in self.header_info.fields}
            
            records_analyzed = 0
            inconsistent_records = 0
            
            # Sample records for analysis
            with open(self.csv_file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(
                    f,
                    fieldnames=self.header_info.fields,
                    delimiter=self.delimiter,
                    quotechar=self.quote_char
                )
                
                # Skip header
                next(reader)
                
                for record in reader:
                    if records_analyzed >= sample_size:
                        break
                    
                    records_analyzed += 1
                    
                    # Check field count consistency
                    if len(record) != self.header_info.field_count:
                        inconsistent_records += 1
                        if inconsistent_records == 1:  # Log first occurrence
                            logger.warning(f"Inconsistent field count in record {records_analyzed}: "
                                         f"expected {self.header_info.field_count}, got {len(record)}")
                    
                    # Analyze each field
                    for field_name, value in record.items():
                        if field_name in field_counts:
                            field_counts[field_name] += 1
                            
                            # Check for null/empty values
                            if not value or value.strip() == '':
                                field_nulls[field_name] += 1
                            else:
                                # Collect sample values
                                if len(field_samples[field_name]) < 10:
                                    field_samples[field_name].append(value.strip())
                                
                                # Infer data types
                                inferred_type = self._infer_value_type(value.strip())
                                field_types[field_name].add(inferred_type)
            
            # Analyze results
            if inconsistent_records > 0:
                validation_report['field_count_consistency'] = False
                validation_report['errors'].append(
                    f"{inconsistent_records}/{records_analyzed} records have inconsistent field counts"
                )
            
            # Calculate null percentages and finalize type inference
            for field in self.header_info.fields:
                total_count = field_counts[field]
                null_count = field_nulls[field]
                
                if total_count > 0:
                    null_percentage = (null_count / total_count) * 100
                    validation_report['null_percentages'][field] = null_percentage
                    
                    # Warn about high null percentages
                    if null_percentage > 50:
                        validation_report['warnings'].append(
                            f"Field '{field}' has {null_percentage:.1f}% null values"
                        )
                    
                    # Determine primary data type
                    field_type_set = field_types[field]
                    if len(field_type_set) == 1:
                        primary_type = list(field_type_set)[0]
                    elif 'numeric' in field_type_set and 'integer' in field_type_set:
                        primary_type = 'numeric'
                    elif field_type_set:
                        # Mixed types - use most common or default to string
                        primary_type = 'mixed'
                    else:
                        primary_type = 'unknown'
                    
                    validation_report['data_type_inference'][field] = primary_type
                    validation_report['value_samples'][field] = field_samples[field]
            
            # Generate recommendations
            if validation_report['errors']:
                validation_report['is_valid'] = False
                validation_report['recommendations'].append(
                    "Fix field count inconsistencies before import"
                )
            
            if validation_report['warnings']:
                validation_report['recommendations'].append(
                    "Review fields with high null percentages for data quality"
                )
            
            # Performance recommendations
            large_text_fields = [
                field for field, samples in field_samples.items()
                if any(len(str(sample)) > 100 for sample in samples)
            ]
            
            if large_text_fields:
                validation_report['recommendations'].append(
                    f"Consider text field optimization for: {', '.join(large_text_fields[:5])}"
                )
            
            logger.info(f"CSV validation complete: {records_analyzed} records analyzed")
            logger.info(f"Valid: {validation_report['is_valid']}, "
                       f"Errors: {len(validation_report['errors'])}, "
                       f"Warnings: {len(validation_report['warnings'])}")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"CSV validation failed: {e}")
            raise
    
    async def read_chunks(self) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Async generator that yields chunks of parsed CSV records
        
        Yields:
            Lists of record dictionaries, each up to chunk_size records
        """
        if self.header_info is None:
            await self.parse_header()
        
        logger.info(f"Starting chunked CSV reading with chunk size: {self.chunk_size}")
        self.parse_start_time = time.time()
        self.records_processed = 0
        
        try:
            with open(self.csv_file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(
                    f,
                    fieldnames=self.header_info.fields,
                    delimiter=self.delimiter,
                    quotechar=self.quote_char
                )
                
                # Skip header line
                next(reader)
                
                chunk = []
                
                for row in reader:
                    # Clean and process row
                    cleaned_row = {}
                    for field_name, value in row.items():
                        # Handle None values from DictReader
                        if value is None:
                            cleaned_value = ''
                        else:
                            cleaned_value = str(value).strip()
                        cleaned_row[field_name] = cleaned_value
                    
                    chunk.append(cleaned_row)
                    self.records_processed += 1
                    
                    # Yield chunk when it reaches the target size
                    if len(chunk) >= self.chunk_size:
                        logger.debug(f"Yielding chunk of {len(chunk)} records "
                                   f"(total processed: {self.records_processed})")
                        yield chunk
                        chunk = []
                        
                        # Allow other coroutines to run
                        await asyncio.sleep(0.001)
                
                # Yield remaining records
                if chunk:
                    logger.debug(f"Yielding final chunk of {len(chunk)} records")
                    yield chunk
            
            total_time = time.time() - self.parse_start_time
            records_per_second = self.records_processed / total_time if total_time > 0 else 0
            
            logger.info(f"CSV reading complete: {self.records_processed:,} records in {total_time:.2f}s")
            logger.info(f"Processing speed: {records_per_second:.0f} records/second")
            
        except Exception as e:
            logger.error(f"Chunked reading failed: {e}")
            raise
    
    async def read_specific_chunk(self, start_record: int, chunk_size: int = None) -> List[Dict[str, Any]]:
        """
        Read a specific chunk of records (useful for recovery/resume)
        
        Args:
            start_record: Zero-based index of first record to read
            chunk_size: Number of records to read (defaults to instance chunk_size)
            
        Returns:
            List of record dictionaries
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        if self.header_info is None:
            await self.parse_header()
        
        logger.debug(f"Reading specific chunk: records {start_record} to {start_record + chunk_size - 1}")
        
        try:
            records = []
            current_record = 0
            
            with open(self.csv_file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(
                    f,
                    fieldnames=self.header_info.fields,
                    delimiter=self.delimiter,
                    quotechar=self.quote_char
                )
                
                # Skip header
                next(reader)
                
                for row in reader:
                    if current_record >= start_record:
                        if len(records) >= chunk_size:
                            break
                        
                        # Clean and process row
                        cleaned_row = {}
                        for field_name, value in row.items():
                            if value is None:
                                cleaned_value = ''
                            else:
                                cleaned_value = str(value).strip()
                            cleaned_row[field_name] = cleaned_value
                        
                        records.append(cleaned_row)
                    
                    current_record += 1
            
            logger.debug(f"Retrieved {len(records)} records starting from record {start_record}")
            return records
            
        except Exception as e:
            logger.error(f"Specific chunk reading failed: {e}")
            raise
    
    def _infer_value_type(self, value: str) -> str:
        """
        Infer the data type of a string value
        
        Args:
            value: String value to analyze
            
        Returns:
            Inferred type: 'integer', 'numeric', 'date', 'boolean', 'string'
        """
        if not value:
            return 'empty'
        
        # Try integer
        try:
            int(value)
            return 'integer'
        except ValueError:
            pass
        
        # Try float/numeric
        try:
            float(value)
            return 'numeric'
        except ValueError:
            pass
        
        # Check for boolean-like values
        if value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 'y', 'n'):
            return 'boolean'
        
        # Check for date-like patterns
        if self._looks_like_date(value):
            return 'date'
        
        # Default to string
        return 'string'
    
    def _looks_like_date(self, value: str) -> bool:
        """Check if value looks like a date"""
        # Simple date pattern matching
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'^\d{8}$',             # YYYYMMDD
        ]
        
        import re
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        return False
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """
        Get current parsing statistics
        
        Returns:
            Dictionary with parsing performance metrics
        """
        if self.parse_start_time is None:
            return {'status': 'not_started'}
        
        elapsed_time = time.time() - self.parse_start_time
        records_per_second = self.records_processed / elapsed_time if elapsed_time > 0 else 0
        
        return {
            'status': 'running',
            'records_processed': self.records_processed,
            'elapsed_time_seconds': elapsed_time,
            'records_per_second': records_per_second,
            'total_records': self.total_records,
            'progress_percentage': (
                (self.records_processed / self.total_records * 100) 
                if self.total_records else 0
            )
        }

# Utility function for testing
async def test_parser(csv_file_path: str, sample_size: int = 100):
    """
    Test function to validate parser with a CSV file
    
    Args:
        csv_file_path: Path to CSV file to test
        sample_size: Number of records to process for testing
    """
    parser = NALCSVParserAgent(csv_file_path, chunk_size=sample_size)
    
    print(f"Testing NAL CSV Parser with file: {csv_file_path}")
    
    # Test format detection
    format_info = await parser.detect_encoding_and_format()
    print(f"Format detected: {format_info}")
    
    # Test header parsing
    header_info = await parser.parse_header()
    print(f"Header parsed: {header_info.field_count} fields")
    print(f"First 10 fields: {header_info.fields[:10]}")
    
    # Test record counting
    record_count = await parser.get_record_count()
    print(f"Total records: {record_count:,}")
    
    # Test structure validation
    validation = await parser.validate_csv_structure(sample_size)
    print(f"Validation result: Valid={validation['is_valid']}")
    print(f"Errors: {len(validation['errors'])}, Warnings: {len(validation['warnings'])}")
    
    # Test chunked reading
    chunk_count = 0
    total_records = 0
    
    async for chunk in parser.read_chunks():
        chunk_count += 1
        total_records += len(chunk)
        print(f"Chunk {chunk_count}: {len(chunk)} records")
        
        if chunk_count >= 3:  # Test first 3 chunks
            break
    
    print(f"Processed {chunk_count} chunks with {total_records} total records")
    
    # Show parsing stats
    stats = parser.get_parsing_stats()
    print(f"Parsing stats: {stats}")

if __name__ == "__main__":
    # CLI for testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python nal_csv_parser_agent.py <csv_file_path> [sample_size]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    asyncio.run(test_parser(csv_path, sample_size))