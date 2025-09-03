"""
Parser for Sunbiz Fixed-Width Data Files
Handles corporate entity, officer, and event files
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, AsyncGenerator, Any
import asyncio

import aiofiles
import polars as pl

logger = logging.getLogger(__name__)


class SunbizParser:
    """Parser for fixed-width Sunbiz data files"""
    
    # File layouts based on Sunbiz Data Usage Guide
    LAYOUTS = {
        'corporate': {
            'document_number': (0, 12),
            'entity_name': (12, 212),
            'status': (212, 222),
            'filing_type': (222, 232),
            'state': (232, 234),
            'fei_ein': (234, 246),
            'date_filed': (246, 254),  # YYYYMMDD
            'effective_date': (254, 262),
            'principal_addr1': (262, 322),
            'principal_addr2': (322, 382),
            'principal_city': (382, 422),
            'principal_state': (422, 424),
            'principal_zip': (424, 434),
            'mailing_addr1': (434, 494),
            'mailing_addr2': (494, 554),
            'mailing_city': (554, 594),
            'mailing_state': (594, 596),
            'mailing_zip': (596, 606),
            'registered_agent_name': (606, 706),
            'registered_agent_addr1': (706, 766),
            'registered_agent_addr2': (766, 826),
            'registered_agent_city': (826, 866),
            'registered_agent_state': (866, 868),
            'registered_agent_zip': (868, 878),
            'last_event': (878, 888),
            'last_event_date': (888, 896),
            'last_event_filed_date': (896, 904),
        },
        'officer': {
            'document_number': (0, 12),
            'officer_name': (12, 112),
            'officer_title': (112, 152),
            'officer_addr1': (152, 212),
            'officer_addr2': (212, 272),
            'officer_city': (272, 312),
            'officer_state': (312, 314),
            'officer_zip': (314, 324),
            'is_manager': (324, 325),  # Y/N
        },
        'event': {
            'document_number': (0, 12),
            'event_code': (12, 22),
            'event_date': (22, 30),  # YYYYMMDD
            'event_filed_date': (30, 38),
            'effective_date': (38, 46),
            'description': (46, 146),
        },
        'fictitious': {
            'document_number': (0, 12),
            'fictitious_name': (12, 212),
            'owner_name': (212, 312),
            'owner_addr1': (312, 372),
            'owner_addr2': (372, 432),
            'owner_city': (432, 472),
            'owner_state': (472, 474),
            'owner_zip': (474, 484),
            'county': (484, 487),
            'registration_date': (487, 495),
            'expiration_date': (495, 503),
        }
    }
    
    def detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        filename_lower = filename.lower()
        
        if 'corp' in filename_lower and 'off' not in filename_lower:
            return 'corporate'
        elif 'off' in filename_lower:
            return 'officer'
        elif 'event' in filename_lower or 'hist' in filename_lower:
            return 'event'
        elif 'fic' in filename_lower:
            return 'fictitious'
        else:
            # Try to detect from file content
            return 'corporate'  # Default
    
    def parse_line(self, line: str, file_type: str) -> Dict[str, Any]:
        """Parse a single line based on file type"""
        layout = self.LAYOUTS.get(file_type, self.LAYOUTS['corporate'])
        record = {}
        
        for field_name, (start, end) in layout.items():
            try:
                value = line[start:end].strip()
                
                # Convert dates
                if 'date' in field_name and value and value.isdigit() and len(value) == 8:
                    year = int(value[:4])
                    month = int(value[4:6])
                    day = int(value[6:8])
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        record[field_name] = datetime(year, month, day).isoformat()
                    else:
                        record[field_name] = None
                # Convert boolean flags
                elif field_name == 'is_manager':
                    record[field_name] = value.upper() == 'Y'
                # Regular string field
                else:
                    record[field_name] = value if value else None
                    
            except (IndexError, ValueError) as e:
                logger.debug(f"Error parsing field {field_name}: {e}")
                record[field_name] = None
        
        return record
    
    async def parse_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Parse entire file and return list of records"""
        file_type = self.detect_file_type(filepath.name)
        logger.info(f"Parsing {filepath.name} as {file_type} file")
        
        records = []
        line_count = 0
        error_count = 0
        
        async with aiofiles.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            async for line in f:
                line_count += 1
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                try:
                    record = self.parse_line(line, file_type)
                    
                    # Only add if document number exists
                    if record.get('document_number'):
                        record['_file_type'] = file_type
                        record['_source_file'] = filepath.name
                        record['_parsed_at'] = datetime.now().isoformat()
                        records.append(record)
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 10:  # Log first 10 errors
                        logger.warning(f"Error parsing line {line_count}: {e}")
        
        logger.info(f"Parsed {len(records)} records from {line_count} lines "
                   f"({error_count} errors)")
        
        return records
    
    async def parse_file_chunked(self, filepath: Path, 
                                chunk_size: int = 10000) -> AsyncGenerator[List[Dict], None]:
        """Parse file in chunks for memory efficiency"""
        file_type = self.detect_file_type(filepath.name)
        logger.info(f"Parsing {filepath.name} in chunks of {chunk_size}")
        
        chunk = []
        line_count = 0
        
        async with aiofiles.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            async for line in f:
                line_count += 1
                
                if not line.strip():
                    continue
                
                try:
                    record = self.parse_line(line, file_type)
                    
                    if record.get('document_number'):
                        record['_file_type'] = file_type
                        record['_source_file'] = filepath.name
                        record['_parsed_at'] = datetime.now().isoformat()
                        chunk.append(record)
                    
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                        logger.debug(f"Processed {line_count} lines")
                        
                except Exception as e:
                    logger.debug(f"Error parsing line {line_count}: {e}")
        
        # Yield remaining records
        if chunk:
            yield chunk
    
    async def validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate a parsed record"""
        file_type = record.get('_file_type')
        
        if file_type == 'corporate':
            # Must have document number and entity name
            if not record.get('document_number') or not record.get('entity_name'):
                return False
            
            # Document number format check
            doc_num = record['document_number']
            if not (6 <= len(doc_num) <= 12):
                return False
            
        elif file_type == 'officer':
            # Must have document number and officer name
            if not record.get('document_number') or not record.get('officer_name'):
                return False
        
        return True
    
    def normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for matching"""
        if not name:
            return ""
        
        # Convert to uppercase
        normalized = name.upper()
        
        # Remove common suffixes
        suffixes = [
            ', LLC', ' LLC', ', INC', ' INC', ', CORP', ' CORP',
            ', CORPORATION', ' CORPORATION', ', LP', ' LP',
            ', LLP', ' LLP', ', PA', ' PA', ', PC', ' PC',
            ', PLLC', ' PLLC', ', LTD', ' LTD', ', LIMITED', ' LIMITED'
        ]
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                break
        
        # Remove extra spaces and punctuation
        normalized = ' '.join(normalized.split())
        
        # Remove special characters except spaces
        normalized = ''.join(c for c in normalized if c.isalnum() or c == ' ')
        
        return normalized.strip()