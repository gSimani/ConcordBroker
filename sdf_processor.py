"""
SDF File Processor
Advanced CSV/TXT processor for Florida Sales Data Files (SDF) with
comprehensive data validation, cleaning, and transformation.
"""

import os
import csv
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Iterator, Any
from dataclasses import dataclass, asdict
import re
from decimal import Decimal, InvalidOperation
import chardet
from io import StringIO
import traceback

from florida_counties_manager import FloridaCountiesManager


@dataclass
class ProcessingStats:
    """Track processing statistics for each county"""
    county: str
    file_path: str
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None
    data_quality_score: float = 0.0
    column_mapping: Dict[str, str] = None
    validation_errors: List[Dict] = None

    def __post_init__(self):
        if self.column_mapping is None:
            self.column_mapping = {}
        if self.validation_errors is None:
            self.validation_errors = []


class SdfFileProcessor:
    """
    Comprehensive SDF file processor with advanced data validation and cleaning
    """

    # Standard SDF column mappings (Florida DOR format)
    STANDARD_SDF_COLUMNS = {
        'PARCEL_ID': 'parcel_id',
        'IDENT': 'parcel_id',  # Alternative column name
        'PARID': 'parcel_id',  # Alternative column name

        # Sale transaction details
        'SALE_PRC1': 'sale_price',
        'SALE_PRC': 'sale_price',  # Alternative
        'SALEPRICE': 'sale_price',  # Alternative

        'SALE_YR1': 'sale_year',
        'SALE_YEAR': 'sale_year',  # Alternative
        'SALEYEAR': 'sale_year',  # Alternative

        'SALE_MO1': 'sale_month',
        'SALE_MONTH': 'sale_month',  # Alternative
        'SALEMONTH': 'sale_month',  # Alternative

        'SALE_DAY1': 'sale_day',
        'SALE_DAY': 'sale_day',  # Alternative
        'SALEDAY': 'sale_day',  # Alternative

        # Transaction parties
        'GRANTOR1': 'grantor',
        'GRANTOR': 'grantor',  # Alternative
        'SELLER': 'grantor',  # Alternative

        'GRANTEE1': 'grantee',
        'GRANTEE': 'grantee',  # Alternative
        'BUYER': 'grantee',  # Alternative

        # Document information
        'INST_TYP1': 'instrument_type',
        'INSTRUMENT_TYPE': 'instrument_type',  # Alternative
        'INSTTYPE': 'instrument_type',  # Alternative

        'INST_NUM1': 'instrument_number',
        'INSTRUMENT_NUMBER': 'instrument_number',  # Alternative
        'INSTNUM': 'instrument_number',  # Alternative

        'OR_BOOK1': 'or_book',
        'OR_BOOK': 'or_book',  # Alternative
        'ORBOOK': 'or_book',  # Alternative

        'OR_PAGE1': 'or_page',
        'OR_PAGE': 'or_page',  # Alternative
        'ORPAGE': 'or_page',  # Alternative

        'CLERK_NO1': 'clerk_no',
        'CLERK_NO': 'clerk_no',  # Alternative
        'CLERKNO': 'clerk_no',  # Alternative

        # Sale qualification
        'QUAL1': 'sale_qualification',
        'QUALIFICATION': 'sale_qualification',  # Alternative
        'QUAL': 'sale_qualification',  # Alternative

        'VI_CD1': 'quality_code',
        'VI_CODE': 'quality_code',  # Alternative
        'VICODE': 'quality_code',  # Alternative

        'REASON1': 'reason',
        'REASON': 'reason',  # Alternative

        # Property details
        'VAC_IMP1': 'vacant_improved',
        'VAC_IMP': 'vacant_improved',  # Alternative
        'VACIMP': 'vacant_improved',  # Alternative

        'USE_CD1': 'property_use',
        'USE_CODE': 'property_use',  # Alternative
        'USECODE': 'property_use',  # Alternative

        # Additional flags
        'MULTI_PAR1': 'multi_parcel',
        'MULTI_PARCEL': 'multi_parcel',  # Alternative
        'MULTIPAR': 'multi_parcel',  # Alternative
    }

    # Florida DOR quality codes for determining qualified sales
    QUALIFIED_SALE_CODES = {
        '01': 'Valid sale - verified',
        '02': 'Valid sale - not verified',
        '03': 'Valid sale - part of multi-parcel',
        '04': 'Valid sale - buyer and seller unrelated',
        '05': 'Valid sale - typical financing'
    }

    UNQUALIFIED_SALE_CODES = {
        '06': 'Not a market sale - nominal consideration',
        '07': 'Not a market sale - partial interest',
        '08': 'Not a market sale - REA sale',
        '09': 'Not a market sale - short sale',
        '10': 'Not a market sale - financing or exchange',
        '11': 'Not a market sale - related parties',
        '12': 'Not a market sale - package deal',
        '13': 'Not a market sale - different property types',
        '14': 'Not a market sale - auction',
        '15': 'Not a market sale - foreclosure',
        '16': 'Not a market sale - deed in lieu',
        '17': 'Not a market sale - bankruptcy',
        '18': 'Not a market sale - government agency',
        '19': 'Not a market sale - other'
    }

    def __init__(self, output_dir: str = None):
        """
        Initialize the SDF processor

        Args:
            output_dir: Directory to store processed data
        """
        self.output_dir = Path(output_dir or "C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/SDF_PROCESSED")
        self.counties_manager = FloridaCountiesManager()

        # Setup logging
        self.setup_logging()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Processing statistics
        self.processing_stats: Dict[str, ProcessingStats] = {}

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.output_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler = logging.FileHandler(
            log_dir / f'sdf_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger = logging.getLogger('SdfProcessor')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def detect_file_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding using chardet

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']

                self.logger.info(f"Detected encoding for {file_path.name}: {encoding} (confidence: {result['confidence']:.2f})")
                return encoding or 'utf-8'

        except Exception as e:
            self.logger.warning(f"Could not detect encoding for {file_path}: {e}")
            return 'utf-8'

    def detect_delimiter(self, file_path: Path, encoding: str = 'utf-8') -> str:
        """
        Detect CSV delimiter

        Args:
            file_path: Path to the file
            encoding: File encoding

        Returns:
            Detected delimiter
        """
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                sample = f.read(8192)  # Read first 8KB

            # Try common delimiters
            delimiters = [',', '\t', '|', ';']
            delimiter_counts = {}

            for delimiter in delimiters:
                delimiter_counts[delimiter] = sample.count(delimiter)

            # Return delimiter with highest count
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)

            if delimiter_counts[best_delimiter] > 0:
                self.logger.info(f"Detected delimiter for {file_path.name}: '{best_delimiter}'")
                return best_delimiter
            else:
                self.logger.warning(f"Could not detect delimiter for {file_path}, using comma")
                return ','

        except Exception as e:
            self.logger.warning(f"Error detecting delimiter for {file_path}: {e}")
            return ','

    def map_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Map CSV columns to standardized field names

        Args:
            columns: List of column names from CSV

        Returns:
            Dictionary mapping original columns to standard names
        """
        mapping = {}

        for col in columns:
            col_upper = col.upper().strip()

            # Direct mapping
            if col_upper in self.STANDARD_SDF_COLUMNS:
                mapping[col] = self.STANDARD_SDF_COLUMNS[col_upper]
                continue

            # Fuzzy matching for variations
            for standard_col, mapped_name in self.STANDARD_SDF_COLUMNS.items():
                if self._fuzzy_column_match(col_upper, standard_col):
                    mapping[col] = mapped_name
                    break

        self.logger.info(f"Column mapping: {len(mapping)} of {len(columns)} columns mapped")
        return mapping

    def _fuzzy_column_match(self, col1: str, col2: str) -> bool:
        """
        Fuzzy matching for column names

        Args:
            col1: First column name
            col2: Second column name

        Returns:
            True if columns match closely
        """
        # Remove common prefixes/suffixes and special characters
        clean1 = re.sub(r'[^A-Z0-9]', '', col1)
        clean2 = re.sub(r'[^A-Z0-9]', '', col2)

        # Check if one contains the other
        return clean1 in clean2 or clean2 in clean1

    def validate_parcel_id(self, parcel_id: str) -> bool:
        """
        Validate parcel ID format

        Args:
            parcel_id: Parcel ID to validate

        Returns:
            True if valid
        """
        if not parcel_id or not isinstance(parcel_id, str):
            return False

        # Remove whitespace
        parcel_id = parcel_id.strip()

        # Must have minimum length and contain numbers
        if len(parcel_id) < 5 or not any(c.isdigit() for c in parcel_id):
            return False

        return True

    def parse_sale_date(self, year: Any, month: Any, day: Any = 1) -> Optional[str]:
        """
        Parse sale date from year/month/day components

        Args:
            year: Sale year
            month: Sale month
            day: Sale day (default: 1)

        Returns:
            Formatted date string or None
        """
        try:
            if pd.isna(year) or pd.isna(month):
                return None

            year = int(float(year))
            month = int(float(month))
            day = int(float(day)) if not pd.isna(day) and day else 1

            # Validate ranges
            if not (1900 <= year <= 2025):
                return None
            if not (1 <= month <= 12):
                return None
            if not (1 <= day <= 31):
                day = 1

            return f"{year:04d}-{month:02d}-{day:02d}"

        except (ValueError, TypeError):
            return None

    def parse_sale_price(self, price: Any) -> Optional[float]:
        """
        Parse and validate sale price

        Args:
            price: Sale price value

        Returns:
            Validated price or None
        """
        if pd.isna(price):
            return None

        try:
            # Handle string formatting
            if isinstance(price, str):
                # Remove currency symbols and commas
                price = re.sub(r'[$,\s]', '', price)

            price = float(price)

            # Validate reasonable price range
            if 0 < price <= 1_000_000_000:  # Up to $1B
                return price

        except (ValueError, TypeError):
            pass

        return None

    def determine_sale_qualification(self, quality_code: str) -> Dict[str, Any]:
        """
        Determine sale qualification based on quality code

        Args:
            quality_code: Florida DOR quality code

        Returns:
            Dictionary with qualification flags
        """
        if not quality_code:
            return {
                'qualified_sale': False,
                'arms_length': False,
                'foreclosure': False,
                'rea_sale': False,
                'short_sale': False,
                'distressed_sale': False
            }

        # Normalize code
        code = str(quality_code).zfill(2)

        return {
            'qualified_sale': code in self.QUALIFIED_SALE_CODES,
            'arms_length': code in ['01', '02', '03', '04', '05'],
            'foreclosure': code in ['15', '16'],
            'rea_sale': code == '08',
            'short_sale': code == '09',
            'distressed_sale': code in ['08', '09', '15', '16', '17']
        }

    def clean_text_field(self, value: Any, max_length: int = 255) -> str:
        """
        Clean and truncate text fields

        Args:
            value: Text value to clean
            max_length: Maximum length

        Returns:
            Cleaned text
        """
        if pd.isna(value):
            return ""

        text = str(value).strip()

        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Truncate if necessary
        if len(text) > max_length:
            text = text[:max_length]

        return text

    def process_sdf_record(self, row: Dict, column_mapping: Dict[str, str], county: str) -> Optional[Dict]:
        """
        Process a single SDF record into standardized format

        Args:
            row: Raw CSV row data
            column_mapping: Column name mapping
            county: County name

        Returns:
            Processed record or None if invalid
        """
        try:
            # Extract mapped values
            mapped_row = {}
            for original_col, mapped_col in column_mapping.items():
                if original_col in row:
                    mapped_row[mapped_col] = row[original_col]

            # Validate required fields
            parcel_id = mapped_row.get('parcel_id', '')
            if not self.validate_parcel_id(parcel_id):
                return None

            # Parse sale price
            sale_price = self.parse_sale_price(mapped_row.get('sale_price'))
            if not sale_price or sale_price <= 0:
                return None

            # Parse sale date
            sale_date = self.parse_sale_date(
                mapped_row.get('sale_year'),
                mapped_row.get('sale_month'),
                mapped_row.get('sale_day', 1)
            )
            if not sale_date:
                return None

            # Determine qualification
            quality_code = self.clean_text_field(mapped_row.get('quality_code', ''), 10)
            qualification = self.determine_sale_qualification(quality_code)

            # Build standardized record
            record = {
                'parcel_id': self.clean_text_field(parcel_id, 50),
                'county': county.upper(),
                'sale_date': sale_date,
                'sale_year': int(mapped_row.get('sale_year', 0)),
                'sale_month': int(mapped_row.get('sale_month', 0)),
                'sale_day': int(mapped_row.get('sale_day', 1)),
                'sale_price': sale_price,
                'grantor': self.clean_text_field(mapped_row.get('grantor', ''), 255),
                'grantee': self.clean_text_field(mapped_row.get('grantee', ''), 255),
                'instrument_type': self.clean_text_field(mapped_row.get('instrument_type', ''), 50),
                'instrument_number': self.clean_text_field(mapped_row.get('instrument_number', ''), 50),
                'or_book': self.clean_text_field(mapped_row.get('or_book', ''), 20),
                'or_page': self.clean_text_field(mapped_row.get('or_page', ''), 20),
                'clerk_no': self.clean_text_field(mapped_row.get('clerk_no', ''), 50),
                'sale_qualification': self.clean_text_field(mapped_row.get('sale_qualification', ''), 50),
                'quality_code': quality_code,
                'vi_code': quality_code,  # Same as quality_code for compatibility
                'reason': self.clean_text_field(mapped_row.get('reason', ''), 255),
                'vacant_improved': self.clean_text_field(mapped_row.get('vacant_improved', ''), 20),
                'property_use': self.clean_text_field(mapped_row.get('property_use', ''), 50),
                'multi_parcel': str(mapped_row.get('multi_parcel', '')).upper() == 'Y',
                'data_source': 'SDF',
                'import_date': datetime.now().isoformat()
            }

            # Add qualification flags
            record.update(qualification)

            return record

        except Exception as e:
            self.logger.debug(f"Error processing record: {e}")
            return None

    def process_sdf_file(self, file_path: Path, county: str, chunk_size: int = 10000) -> Iterator[List[Dict]]:
        """
        Process SDF file in chunks

        Args:
            file_path: Path to SDF file
            county: County name
            chunk_size: Number of records per chunk

        Yields:
            Lists of processed records
        """
        if county not in self.processing_stats:
            self.processing_stats[county] = ProcessingStats(
                county=county,
                file_path=str(file_path)
            )

        stats = self.processing_stats[county]
        start_time = datetime.now()

        try:
            # Detect file properties
            encoding = self.detect_file_encoding(file_path)
            delimiter = self.detect_delimiter(file_path, encoding)

            self.logger.info(f"Processing {county} SDF file: {file_path}")

            # Read file in chunks
            chunk_reader = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                chunksize=chunk_size,
                dtype=str,  # Read all as strings initially
                na_values=['', 'NULL', 'null', 'NA', 'N/A'],
                keep_default_na=False
            )

            # Process first chunk to establish column mapping
            column_mapping = None
            processed_records = []

            for chunk_idx, chunk in enumerate(chunk_reader):
                if column_mapping is None:
                    # Establish column mapping from first chunk
                    column_mapping = self.map_columns(list(chunk.columns))
                    stats.column_mapping = column_mapping

                    if not column_mapping:
                        raise ValueError("Could not map any columns to standard format")

                chunk_records = []

                for _, row in chunk.iterrows():
                    stats.total_rows += 1

                    # Process individual record
                    record = self.process_sdf_record(row.to_dict(), column_mapping, county)

                    if record:
                        chunk_records.append(record)
                        stats.valid_rows += 1
                    else:
                        stats.invalid_rows += 1

                # Yield processed chunk
                if chunk_records:
                    yield chunk_records

                # Log progress periodically
                if chunk_idx % 10 == 0:
                    self.logger.info(
                        f"{county} progress: {stats.total_rows:,} rows processed, "
                        f"{stats.valid_rows:,} valid ({stats.valid_rows/stats.total_rows*100:.1f}%)"
                    )

        except Exception as e:
            stats.error_message = str(e)
            self.logger.error(f"Error processing {county}: {e}")
            self.logger.debug(traceback.format_exc())
            raise

        finally:
            # Calculate final statistics
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            if stats.total_rows > 0:
                stats.data_quality_score = stats.valid_rows / stats.total_rows

            self.logger.info(
                f"Completed {county}: {stats.valid_rows:,}/{stats.total_rows:,} valid records "
                f"({stats.data_quality_score*100:.1f}% quality) in {stats.processing_time:.1f}s"
            )

    def save_processed_data(self, records: List[Dict], county: str, chunk_idx: int):
        """
        Save processed records to JSON file

        Args:
            records: List of processed records
            county: County name
            chunk_idx: Chunk index for filename
        """
        output_file = self.output_dir / f"{county}_processed_chunk_{chunk_idx:04d}.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(records, f, indent=2, default=str)

            self.logger.debug(f"Saved {len(records)} records to {output_file}")

        except Exception as e:
            self.logger.error(f"Error saving processed data for {county}: {e}")

    def get_processing_summary(self) -> Dict:
        """Get comprehensive processing summary"""
        total_rows = sum(s.total_rows for s in self.processing_stats.values())
        total_valid = sum(s.valid_rows for s in self.processing_stats.values())
        total_time = sum(s.processing_time for s in self.processing_stats.values())

        return {
            'counties_processed': len(self.processing_stats),
            'total_rows': total_rows,
            'total_valid_rows': total_valid,
            'total_invalid_rows': total_rows - total_valid,
            'overall_quality_score': total_valid / total_rows if total_rows > 0 else 0,
            'total_processing_time': total_time,
            'average_processing_speed': total_rows / total_time if total_time > 0 else 0,
            'county_details': {
                county: asdict(stats) for county, stats in self.processing_stats.items()
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    processor = SdfFileProcessor()

    # Test with a sample file (would need actual SDF file)
    test_file = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/SDF_DATA/extracted/LAFAYETTE/sample.csv")

    if test_file.exists():
        print(f"Testing processor with file: {test_file}")

        for chunk_idx, records in enumerate(processor.process_sdf_file(test_file, "LAFAYETTE")):
            print(f"Processed chunk {chunk_idx}: {len(records)} records")
            processor.save_processed_data(records, "LAFAYETTE", chunk_idx)

        summary = processor.get_processing_summary()
        print("\nProcessing Summary:")
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("No test file available. Processor is ready for use.")