"""
Parser for Broward County Daily Index Extract Files
Parses various record types from the daily index files
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

# Import schema validator for enhanced parsing
sys.path.append(str(Path(__file__).parent.parent))
try:
    from broward_layout_schema.schema_validator import SchemaValidator
    SCHEMA_VALIDATOR_AVAILABLE = True
except ImportError:
    SCHEMA_VALIDATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class BrowardIndexParser:
    """Parser for Broward County daily index files"""
    
    # Common record types in daily index files
    RECORD_TYPES = {
        'DEED': 'Real Estate Deed',
        'MTG': 'Mortgage',
        'SAT': 'Satisfaction of Mortgage',
        'LIS': 'Lis Pendens',
        'LP': 'Limited Partnership',
        'ASSIGN': 'Assignment',
        'REL': 'Release',
        'LIEN': 'Lien',
        'JUDG': 'Judgment',
        'PLAT': 'Plat',
        'CONDO': 'Condominium',
        'EASE': 'Easement',
        'AGREE': 'Agreement',
        'AFFID': 'Affidavit'
    }
    
    def __init__(self):
        """Initialize the parser"""
        self.stats = {
            'files_parsed': 0,
            'records_parsed': 0,
            'errors': 0
        }
        
        # Initialize schema validator if available
        self.validator = None
        if SCHEMA_VALIDATOR_AVAILABLE:
            schema_path = Path(__file__).parent.parent / "broward_layout_schema" / "extracted" / "schema.json"
            if schema_path.exists():
                self.validator = SchemaValidator(schema_path)
                logger.info("Schema validator loaded for enhanced parsing")
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse a single daily index file
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List of parsed records
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        # Validate file against schema if validator available
        if self.validator:
            validation_result = self.validator.validate_file(file_path)
            if not validation_result.get('valid'):
                logger.warning(f"File validation warnings: {validation_result.get('warnings', [])[:3]}")
        
        # Determine file type and parse accordingly
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            return self._parse_csv(file_path)
        elif suffix == '.txt':
            return self._parse_text(file_path)
        elif suffix == '.xml':
            return self._parse_xml(file_path)
        elif suffix == '.json':
            return self._parse_json(file_path)
        else:
            # Try to parse as CSV by default
            return self._parse_csv(file_path)
    
    def _parse_csv(self, file_path: Path) -> List[Dict]:
        """Parse CSV format daily index file"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Common delimiters
                delimiter = ','
                if '\t' in sample:
                    delimiter = '\t'
                elif '|' in sample:
                    delimiter = '|'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        record = self._parse_record(row)
                        if record:
                            records.append(record)
                            self.stats['records_parsed'] += 1
                    except Exception as e:
                        logger.debug(f"Error parsing row {row_num}: {e}")
                        self.stats['errors'] += 1
            
            self.stats['files_parsed'] += 1
            logger.info(f"Parsed {len(records)} records from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse CSV file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return records
    
    def _parse_text(self, file_path: Path) -> List[Dict]:
        """Parse text format daily index file (fixed-width or delimited)"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Try to detect format
            if len(lines) > 0:
                # Check if it's fixed-width or delimited
                first_line = lines[0]
                
                if '\t' in first_line or '|' in first_line:
                    # Delimited format
                    delimiter = '\t' if '\t' in first_line else '|'
                    
                    for line_num, line in enumerate(lines, 1):
                        if line.strip():
                            parts = line.strip().split(delimiter)
                            record = self._parse_text_parts(parts)
                            if record:
                                records.append(record)
                                self.stats['records_parsed'] += 1
                else:
                    # Fixed-width format - parse based on position
                    for line_num, line in enumerate(lines, 1):
                        if line.strip():
                            record = self._parse_fixed_width(line)
                            if record:
                                records.append(record)
                                self.stats['records_parsed'] += 1
            
            self.stats['files_parsed'] += 1
            logger.info(f"Parsed {len(records)} records from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse text file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return records
    
    def _parse_xml(self, file_path: Path) -> List[Dict]:
        """Parse XML format daily index file"""
        records = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Common XML structures for property records
            for record_elem in root.findall('.//Record'):
                record = {}
                
                for child in record_elem:
                    tag = child.tag
                    value = child.text
                    
                    if value:
                        record[tag.lower()] = value.strip()
                
                if record:
                    parsed = self._parse_record(record)
                    if parsed:
                        records.append(parsed)
                        self.stats['records_parsed'] += 1
            
            self.stats['files_parsed'] += 1
            logger.info(f"Parsed {len(records)} records from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse XML file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return records
    
    def _parse_json(self, file_path: Path) -> List[Dict]:
        """Parse JSON format daily index file"""
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of records
                for item in data:
                    record = self._parse_record(item)
                    if record:
                        records.append(record)
                        self.stats['records_parsed'] += 1
            elif isinstance(data, dict):
                # Object with records array
                if 'records' in data:
                    for item in data['records']:
                        record = self._parse_record(item)
                        if record:
                            records.append(record)
                            self.stats['records_parsed'] += 1
                else:
                    # Single record
                    record = self._parse_record(data)
                    if record:
                        records.append(record)
                        self.stats['records_parsed'] += 1
            
            self.stats['files_parsed'] += 1
            logger.info(f"Parsed {len(records)} records from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse JSON file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return records
    
    def _parse_record(self, raw_record: Dict) -> Optional[Dict]:
        """
        Parse and standardize a single record
        
        Args:
            raw_record: Raw record data
            
        Returns:
            Standardized record or None if invalid
        """
        # Standardize field names
        record = {}
        
        # Map common field variations to standard names
        field_mappings = {
            # Document fields
            'doc_type': ['doc_type', 'document_type', 'type', 'doctype', 'rec_type'],
            'doc_number': ['doc_number', 'document_number', 'doc_no', 'docno', 'instrument_number'],
            'book': ['book', 'book_no', 'or_book', 'liber'],
            'page': ['page', 'page_no', 'or_page', 'folio'],
            'recorded_date': ['recorded_date', 'rec_date', 'record_date', 'date_recorded'],
            
            # Party fields
            'grantor': ['grantor', 'party1', 'from_party', 'seller'],
            'grantee': ['grantee', 'party2', 'to_party', 'buyer'],
            
            # Property fields
            'parcel_id': ['parcel_id', 'parcel_number', 'folio', 'pin', 'parcel'],
            'legal_desc': ['legal_desc', 'legal_description', 'legal', 'description'],
            'address': ['address', 'property_address', 'location', 'situs'],
            
            # Transaction fields
            'consideration': ['consideration', 'amount', 'sale_price', 'price'],
            'doc_stamps': ['doc_stamps', 'documentary_stamps', 'stamps', 'tax']
        }
        
        # Normalize keys (lowercase, remove spaces)
        normalized = {}
        for key, value in raw_record.items():
            if value:
                norm_key = key.lower().strip().replace(' ', '_')
                normalized[norm_key] = str(value).strip()
        
        # Map to standard fields
        for standard_field, variations in field_mappings.items():
            for variation in variations:
                if variation in normalized:
                    record[standard_field] = normalized[variation]
                    break
        
        # Parse dates
        if 'recorded_date' in record:
            record['recorded_date'] = self._parse_date(record['recorded_date'])
        
        # Parse amounts
        if 'consideration' in record:
            record['consideration'] = self._parse_amount(record['consideration'])
        
        if 'doc_stamps' in record:
            record['doc_stamps'] = self._parse_amount(record['doc_stamps'])
        
        # Determine record type
        if 'doc_type' in record:
            record['record_type'] = self._categorize_record_type(record['doc_type'])
        
        # Add metadata
        record['source'] = 'broward_daily_index'
        record['parsed_at'] = datetime.now().isoformat()
        
        # Validate minimum required fields
        if 'doc_number' in record or 'parcel_id' in record:
            return record
        
        return None
    
    def _parse_text_parts(self, parts: List[str]) -> Optional[Dict]:
        """Parse delimited text parts into a record"""
        if len(parts) < 3:
            return None
        
        # Common field order in delimited files
        record = {}
        
        # Adjust based on actual file format
        if len(parts) >= 6:
            record['doc_type'] = parts[0]
            record['doc_number'] = parts[1]
            record['recorded_date'] = parts[2]
            record['grantor'] = parts[3]
            record['grantee'] = parts[4]
            record['consideration'] = parts[5] if len(parts) > 5 else None
        
        return self._parse_record(record)
    
    def _parse_fixed_width(self, line: str) -> Optional[Dict]:
        """Parse fixed-width format line"""
        # Common fixed-width positions (adjust based on actual format)
        positions = {
            'doc_type': (0, 10),
            'doc_number': (10, 25),
            'recorded_date': (25, 35),
            'book': (35, 40),
            'page': (40, 45),
            'grantor': (45, 95),
            'grantee': (95, 145),
            'consideration': (145, 155)
        }
        
        record = {}
        for field, (start, end) in positions.items():
            if len(line) > start:
                value = line[start:min(end, len(line))].strip()
                if value:
                    record[field] = value
        
        return self._parse_record(record)
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats"""
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%Y%m%d',
            '%d-%b-%Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # Return original if can't parse
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse monetary amounts"""
        try:
            # Remove common formatting
            clean = amount_str.replace('$', '').replace(',', '').replace(' ', '')
            return float(clean)
        except (ValueError, AttributeError):
            return None
    
    def _categorize_record_type(self, doc_type: str) -> str:
        """Categorize document type"""
        doc_type_upper = doc_type.upper()
        
        for key, category in self.RECORD_TYPES.items():
            if key in doc_type_upper:
                return category
        
        return 'Other'
    
    def get_stats(self) -> Dict:
        """Get parsing statistics"""
        return self.stats.copy()