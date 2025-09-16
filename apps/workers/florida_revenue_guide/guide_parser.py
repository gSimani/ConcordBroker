"""
PDF Parser for Florida Revenue NAL/SDF/NAP Users Guide
Extracts field definitions, schema specifications, and data formats
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
import PyPDF2

logger = logging.getLogger(__name__)

class FloridaRevenueGuideParser:
    """Parses the Florida Revenue Users Guide to extract schema definitions"""
    
    def __init__(self):
        """Initialize the PDF parser"""
        self.schemas = {
            'NAL': {'name': 'Name Address Library', 'fields': []},
            'SDF': {'name': 'Sales Data File', 'fields': []},
            'NAP': {'name': 'Non-Ad Valorem Parcel', 'fields': []},
            'NAV': {'name': 'Non-Ad Valorem Assessment', 'fields': []},
            'TPP': {'name': 'Tangible Personal Property', 'fields': []}
        }
        self.field_definitions = []
        self.data_types = {}
        self.record_layouts = {}
        
    def parse_pdf(self, pdf_path: Path) -> Dict:
        """
        Parse the Florida Revenue Users Guide PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted schema information
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return {}
        
        logger.info(f"Parsing Florida Revenue Users Guide: {pdf_path}")
        
        try:
            # Use pdfplumber for table extraction
            with pdfplumber.open(pdf_path) as pdf:
                self._parse_with_pdfplumber(pdf)
            
            # Also use PyPDF2 for text extraction
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                self._parse_with_pypdf2(pdf_reader)
            
            # Process and combine results
            result = self._process_extracted_data()
            
            logger.info(f"Successfully parsed PDF. Found {len(self.field_definitions)} field definitions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            return {}
    
    def _parse_with_pdfplumber(self, pdf):
        """Parse PDF using pdfplumber for structured data extraction"""
        for page_num, page in enumerate(pdf.pages, 1):
            logger.debug(f"Processing page {page_num}")
            
            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                self._process_table(table, page_num)
            
            # Extract text for context
            text = page.extract_text()
            if text:
                self._process_page_text(text, page_num)
    
    def _parse_with_pypdf2(self, pdf_reader):
        """Parse PDF using PyPDF2 for additional text extraction"""
        num_pages = len(pdf_reader.pages)
        
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            # Look for field specifications
            self._extract_field_specifications(text, page_num + 1)
            
            # Look for data type definitions
            self._extract_data_types(text, page_num + 1)
    
    def _process_table(self, table: List[List], page_num: int):
        """Process extracted table data"""
        if not table or len(table) < 2:
            return
        
        # Clean up headers
        headers = [str(cell).strip() if cell else '' for cell in table[0]]
        headers_lower = [h.lower() for h in headers]
        
        # Identify table type based on headers
        if any('field' in h for h in headers_lower):
            self._process_field_table(table, headers, page_num)
        elif any('record' in h for h in headers_lower):
            self._process_record_layout_table(table, headers, page_num)
        elif any('code' in h for h in headers_lower):
            self._process_code_table(table, headers, page_num)
    
    def _process_field_table(self, table: List[List], headers: List[str], page_num: int):
        """Process field definition table"""
        # Identify which file type this table is for
        file_type = self._identify_file_type_from_context(page_num)
        
        for row in table[1:]:  # Skip header row
            if len(row) < len(headers):
                continue
            
            field_def = {}
            for i, header in enumerate(headers):
                if i < len(row) and row[i]:
                    field_def[self._normalize_header(header)] = str(row[i]).strip()
            
            if field_def:
                field_def['source_page'] = page_num
                field_def['file_type'] = file_type
                
                # Parse field properties
                self._parse_field_properties(field_def)
                
                self.field_definitions.append(field_def)
                
                # Add to appropriate schema
                if file_type in self.schemas:
                    self.schemas[file_type]['fields'].append(field_def)
    
    def _process_record_layout_table(self, table: List[List], headers: List[str], page_num: int):
        """Process record layout table"""
        file_type = self._identify_file_type_from_context(page_num)
        
        if file_type not in self.record_layouts:
            self.record_layouts[file_type] = []
        
        for row in table[1:]:
            if not any(row):
                continue
            
            layout_info = {}
            for i, header in enumerate(headers):
                if i < len(row) and row[i]:
                    layout_info[self._normalize_header(header)] = str(row[i]).strip()
            
            if layout_info:
                layout_info['source_page'] = page_num
                self.record_layouts[file_type].append(layout_info)
    
    def _process_code_table(self, table: List[List], headers: List[str], page_num: int):
        """Process code/lookup table"""
        # Extract code definitions (e.g., qualification codes, use codes)
        code_type = None
        
        for row in table[1:]:
            if len(row) >= 2:
                code = str(row[0]).strip() if row[0] else ''
                description = str(row[1]).strip() if row[1] else ''
                
                if code and description:
                    if not code_type:
                        # Try to determine code type from headers or content
                        if any('qual' in h.lower() for h in headers):
                            code_type = 'qualification_codes'
                        elif any('use' in h.lower() for h in headers):
                            code_type = 'use_codes'
                        elif any('type' in h.lower() for h in headers):
                            code_type = 'type_codes'
                        else:
                            code_type = 'general_codes'
                    
                    if code_type not in self.data_types:
                        self.data_types[code_type] = {}
                    
                    self.data_types[code_type][code] = description
    
    def _process_page_text(self, text: str, page_num: int):
        """Process page text for additional information"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Look for file type indicators
            if 'name address library' in line_lower or 'nal file' in line_lower:
                self._current_file_type = 'NAL'
            elif 'sales data file' in line_lower or 'sdf file' in line_lower:
                self._current_file_type = 'SDF'
            elif 'non-ad valorem parcel' in line_lower or 'nap file' in line_lower:
                self._current_file_type = 'NAP'
            elif 'non-ad valorem assessment' in line_lower or 'nav file' in line_lower:
                self._current_file_type = 'NAV'
            elif 'tangible personal property' in line_lower or 'tpp file' in line_lower:
                self._current_file_type = 'TPP'
            
            # Look for field definitions in text
            if 'field name' in line_lower or 'column' in line_lower:
                self._extract_inline_field_spec(lines, i, page_num)
    
    def _extract_field_specifications(self, text: str, page_num: int):
        """Extract field specifications from text"""
        # Common patterns for field definitions
        patterns = [
            # Field Name: Type(Length) - Description
            r'([A-Z_]+):\s*(\w+)\((\d+)\)\s*[-–]\s*(.+)',
            # Field_Name TYPE LENGTH Description
            r'([A-Z_]+)\s+([A-Z]+)\s+(\d+)\s+(.+)',
            # Column: Name, Type, Length, Description
            r'Column:\s*([A-Z_]+),\s*(\w+),\s*(\d+),\s*(.+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                field_def = {
                    'field_name': match.group(1),
                    'data_type': match.group(2),
                    'length': match.group(3),
                    'description': match.group(4).strip(),
                    'source_page': page_num
                }
                
                # Determine file type from context
                field_def['file_type'] = self._identify_file_type_from_field_name(field_def['field_name'])
                
                self.field_definitions.append(field_def)
    
    def _extract_data_types(self, text: str, page_num: int):
        """Extract data type definitions from text"""
        # Look for sections defining data types
        if 'data types' in text.lower() or 'field types' in text.lower():
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                # Common data type patterns
                type_match = re.match(r'([A-Z]+)\s*[-–]\s*(.+)', line)
                if type_match:
                    data_type = type_match.group(1)
                    description = type_match.group(2)
                    
                    if 'data_type_definitions' not in self.data_types:
                        self.data_types['data_type_definitions'] = {}
                    
                    self.data_types['data_type_definitions'][data_type] = description
    
    def _extract_inline_field_spec(self, lines: List[str], start_idx: int, page_num: int):
        """Extract field specifications from inline text"""
        # Look for field definitions in surrounding lines
        for i in range(start_idx + 1, min(len(lines), start_idx + 50)):
            line = lines[i].strip()
            if not line:
                continue
            
            # Try to parse as field definition
            field_match = re.match(r'^(\d+)?\s*([A-Z_]+)\s+(\w+)\s+(\d+)\s*[-]?\s*(\d*)\s*(.*)?$', line)
            if field_match:
                field_def = {
                    'position': field_match.group(1) if field_match.group(1) else '',
                    'field_name': field_match.group(2),
                    'data_type': field_match.group(3),
                    'start_pos': field_match.group(4),
                    'end_pos': field_match.group(5) if field_match.group(5) else '',
                    'description': field_match.group(6) if field_match.group(6) else '',
                    'source_page': page_num
                }
                
                # Clean up and add
                field_def = {k: v for k, v in field_def.items() if v}
                if 'field_name' in field_def:
                    self.field_definitions.append(field_def)
    
    def _parse_field_properties(self, field_def: Dict):
        """Parse and enhance field properties"""
        # Extract position if present
        if 'position' in field_def or 'pos' in field_def:
            pos_str = field_def.get('position', field_def.get('pos', ''))
            if '-' in pos_str:
                start, end = pos_str.split('-')
                field_def['start_pos'] = start.strip()
                field_def['end_pos'] = end.strip()
        
        # Parse data type and length
        if 'type' in field_def:
            type_str = field_def['type']
            # Extract length from type if format is TYPE(LENGTH)
            type_match = re.match(r'(\w+)\((\d+)\)', type_str)
            if type_match:
                field_def['data_type'] = type_match.group(1)
                field_def['length'] = type_match.group(2)
            else:
                field_def['data_type'] = type_str
        
        # Normalize field names
        if 'field_name' in field_def:
            field_def['field_name'] = field_def['field_name'].upper().replace(' ', '_')
        elif 'name' in field_def:
            field_def['field_name'] = field_def['name'].upper().replace(' ', '_')
        
        # Add validation rules based on data type
        self._add_validation_rules(field_def)
    
    def _add_validation_rules(self, field_def: Dict):
        """Add validation rules based on field properties"""
        data_type = field_def.get('data_type', '').upper()
        field_name = field_def.get('field_name', '').upper()
        
        # Common validation rules
        if data_type in ['INTEGER', 'INT', 'NUMBER', 'NUMERIC']:
            field_def['validation'] = {'type': 'numeric', 'integer': True}
        elif data_type in ['DECIMAL', 'FLOAT', 'DOUBLE']:
            field_def['validation'] = {'type': 'numeric', 'integer': False}
        elif data_type in ['DATE']:
            field_def['validation'] = {'type': 'date', 'format': 'YYYYMMDD'}
        elif data_type in ['CHAR', 'VARCHAR', 'TEXT', 'STRING']:
            field_def['validation'] = {'type': 'string'}
            if 'length' in field_def:
                field_def['validation']['max_length'] = int(field_def['length'])
        
        # Field-specific rules
        if 'PARCEL' in field_name:
            field_def['validation'] = {'type': 'parcel_id', 'pattern': r'^\d{12,15}$'}
        elif 'ZIP' in field_name:
            field_def['validation'] = {'type': 'zip_code', 'pattern': r'^\d{5}(-\d{4})?$'}
        elif 'PHONE' in field_name:
            field_def['validation'] = {'type': 'phone', 'pattern': r'^[\d\s\-\(\)]+$'}
        elif 'EMAIL' in field_name:
            field_def['validation'] = {'type': 'email', 'pattern': r'^[^\s@]+@[^\s@]+\.[^\s@]+$'}
        elif 'AMOUNT' in field_name or 'PRICE' in field_name or 'VALUE' in field_name:
            field_def['validation'] = {'type': 'currency', 'min': 0}
    
    def _identify_file_type_from_context(self, page_num: int) -> str:
        """Identify file type based on page context"""
        # Use last known file type or default
        return getattr(self, '_current_file_type', 'UNKNOWN')
    
    def _identify_file_type_from_field_name(self, field_name: str) -> str:
        """Identify file type based on field name patterns"""
        field_upper = field_name.upper()
        
        # Common field patterns
        if any(x in field_upper for x in ['OWNER', 'MAIL', 'ADDR']):
            return 'NAL'
        elif any(x in field_upper for x in ['SALE', 'QUAL', 'DEED', 'OR_']):
            return 'SDF'
        elif any(x in field_upper for x in ['NON_AD', 'ASSESSMENT']):
            return 'NAV'
        elif any(x in field_upper for x in ['TANGIBLE', 'TPP']):
            return 'TPP'
        
        return 'UNKNOWN'
    
    def _normalize_header(self, header: str) -> str:
        """Normalize header names for consistency"""
        return header.lower().replace(' ', '_').replace('-', '_').strip()
    
    def _process_extracted_data(self) -> Dict:
        """Process and organize all extracted data"""
        # Build final schema structure
        schema = {
            'version': 'extracted',
            'source': 'Florida Revenue NAL/SDF/NAP Users Guide',
            'extraction_date': str(datetime.now()),
            'file_schemas': self.schemas,
            'field_definitions': self.field_definitions,
            'record_layouts': self.record_layouts,
            'data_types': self.data_types,
            'statistics': {
                'total_fields': len(self.field_definitions),
                'files_documented': len([s for s in self.schemas if self.schemas[s]['fields']]),
                'code_tables': len(self.data_types),
                'field_breakdown': {
                    file_type: len(schema['fields'])
                    for file_type, schema in self.schemas.items()
                }
            }
        }
        
        return schema
    
    def save_schema(self, schema: Dict, output_path: Path):
        """Save extracted schema to JSON file"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(schema, f, indent=2, default=str)
            logger.info(f"Schema saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save schema: {e}")
    
    def get_file_schema(self, file_type: str) -> Optional[Dict]:
        """Get schema for a specific file type"""
        return self.schemas.get(file_type.upper())
    
    def get_field_definitions(self, file_type: Optional[str] = None) -> List[Dict]:
        """Get field definitions, optionally filtered by file type"""
        if not file_type:
            return self.field_definitions
        
        # Filter by file type
        file_type_upper = file_type.upper()
        return [f for f in self.field_definitions 
                if f.get('file_type', '').upper() == file_type_upper]


if __name__ == "__main__":
    # Test the parser
    parser = FloridaRevenueGuideParser()
    
    # Assume PDF has been downloaded
    pdf_path = Path("data/florida_revenue_guide/pdfs/NAL_SDF_NAP_Users_Guide_latest.pdf")
    
    if pdf_path.exists():
        schema = parser.parse_pdf(pdf_path)
        
        # Save schema
        output_path = Path("data/florida_revenue_guide/extracted/schema.json")
        parser.save_schema(schema, output_path)
        
        # Print summary
        if 'statistics' in schema:
            print(f"\nExtracted Schema Summary:")
            print(f"  Total Fields: {schema['statistics']['total_fields']}")
            print(f"  Files Documented: {schema['statistics']['files_documented']}")
            print(f"  Field Breakdown:")
            for file_type, count in schema['statistics']['field_breakdown'].items():
                print(f"    {file_type}: {count} fields")
    else:
        print(f"PDF not found at {pdf_path}")