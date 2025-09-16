"""
PDF Parser for Broward County Export Files Layout
Extracts schema definitions and field specifications from the PDF
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
import PyPDF2

logger = logging.getLogger(__name__)

class LayoutPDFParser:
    """Parses the Export Files Layout PDF to extract schema definitions"""
    
    def __init__(self):
        """Initialize the PDF parser"""
        self.schemas = {}
        self.field_definitions = []
        self.file_layouts = {}
        
    def parse_pdf(self, pdf_path: Path) -> Dict:
        """
        Parse the Export Files Layout PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted schema information
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return {}
        
        logger.info(f"Parsing PDF: {pdf_path}")
        
        try:
            # Use pdfplumber for table extraction
            with pdfplumber.open(pdf_path) as pdf:
                self._parse_with_pdfplumber(pdf)
            
            # Also use PyPDF2 for text extraction
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                self._parse_with_pypdf2(pdf_reader)
            
            # Combine and process results
            result = self._process_extracted_data()
            
            logger.info(f"Successfully parsed PDF. Found {len(self.file_layouts)} file layouts")
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
            
            # Look for file format specifications
            self._extract_file_formats(text, page_num + 1)
    
    def _process_table(self, table: List[List], page_num: int):
        """Process extracted table data"""
        if not table or len(table) < 2:
            return
        
        # Assume first row is header
        headers = [str(cell).strip() if cell else '' for cell in table[0]]
        
        # Look for field definition tables
        if any('field' in h.lower() for h in headers):
            self._process_field_table(table, headers, page_num)
        
        # Look for file layout tables
        elif any('file' in h.lower() or 'format' in h.lower() for h in headers):
            self._process_layout_table(table, headers, page_num)
    
    def _process_field_table(self, table: List[List], headers: List[str], page_num: int):
        """Process field definition table"""
        for row in table[1:]:  # Skip header row
            if len(row) < len(headers):
                continue
            
            field_def = {}
            for i, header in enumerate(headers):
                if i < len(row) and row[i]:
                    field_def[header.lower().replace(' ', '_')] = str(row[i]).strip()
            
            if field_def:
                field_def['source_page'] = page_num
                self.field_definitions.append(field_def)
    
    def _process_layout_table(self, table: List[List], headers: List[str], page_num: int):
        """Process file layout table"""
        current_file = None
        
        for row in table[1:]:
            if not any(row):  # Skip empty rows
                continue
            
            # Check if this row defines a new file
            first_cell = str(row[0]).strip() if row[0] else ''
            if first_cell and (first_cell.endswith('.txt') or first_cell.endswith('.csv')):
                current_file = first_cell
                if current_file not in self.file_layouts:
                    self.file_layouts[current_file] = {
                        'name': current_file,
                        'fields': [],
                        'source_page': page_num
                    }
            
            # Add field information to current file
            elif current_file:
                field_info = {}
                for i, header in enumerate(headers):
                    if i < len(row) and row[i]:
                        field_info[header.lower().replace(' ', '_')] = str(row[i]).strip()
                
                if field_info:
                    self.file_layouts[current_file]['fields'].append(field_info)
    
    def _process_page_text(self, text: str, page_num: int):
        """Process page text for additional information"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for file descriptions
            if 'daily index' in line.lower() or 'export file' in line.lower():
                self._extract_file_description(lines, i, page_num)
            
            # Look for field specifications
            elif 'field name' in line.lower() or 'column' in line.lower():
                self._extract_field_spec(lines, i, page_num)
    
    def _extract_file_formats(self, text: str, page_num: int):
        """Extract file format specifications from text"""
        # Common patterns in layout documentation
        patterns = [
            r'(\w+\.(?:txt|csv|xml))\s*[-–]\s*(.+)',  # filename.ext - description
            r'File:\s*(\w+\.(?:txt|csv|xml))',  # File: filename.ext
            r'(\w+)\s+File\s+Layout',  # NAME File Layout
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                file_name = match.group(1)
                description = match.group(2) if len(match.groups()) > 1 else ''
                
                if file_name not in self.file_layouts:
                    self.file_layouts[file_name] = {
                        'name': file_name,
                        'description': description.strip(),
                        'fields': [],
                        'source_page': page_num
                    }
    
    def _extract_file_description(self, lines: List[str], start_idx: int, page_num: int):
        """Extract file description from text lines"""
        # Look for file name and description in surrounding lines
        for i in range(max(0, start_idx - 2), min(len(lines), start_idx + 3)):
            line = lines[i].strip()
            
            # Pattern matching for file specifications
            file_match = re.search(r'(\w+\.(?:txt|csv|xml))', line, re.IGNORECASE)
            if file_match:
                file_name = file_match.group(1)
                
                # Get description from same or next line
                description = line.replace(file_name, '').strip()
                if not description and i + 1 < len(lines):
                    description = lines[i + 1].strip()
                
                if file_name not in self.file_layouts:
                    self.file_layouts[file_name] = {
                        'name': file_name,
                        'description': description,
                        'fields': [],
                        'source_page': page_num
                    }
    
    def _extract_field_spec(self, lines: List[str], start_idx: int, page_num: int):
        """Extract field specifications from text lines"""
        # Look for field definitions in tabular format
        field_pattern = r'^\s*(\w+)\s+(\w+)\s+(\d+)\s*-?\s*(\d*)\s*(.*)?$'
        
        for i in range(start_idx + 1, min(len(lines), start_idx + 50)):
            line = lines[i].strip()
            if not line:
                continue
            
            match = re.match(field_pattern, line)
            if match:
                field_def = {
                    'name': match.group(1),
                    'type': match.group(2),
                    'start_pos': match.group(3),
                    'end_pos': match.group(4) if match.group(4) else '',
                    'description': match.group(5) if match.group(5) else '',
                    'source_page': page_num
                }
                self.field_definitions.append(field_def)
    
    def _process_extracted_data(self) -> Dict:
        """Process and organize all extracted data"""
        # Organize field definitions by likely file type
        for field_def in self.field_definitions:
            # Try to match field to a file layout
            field_name = field_def.get('name', '').upper()
            
            # Common field patterns
            if 'PARCEL' in field_name:
                self._add_field_to_layout('property', field_def)
            elif 'SALE' in field_name or 'DEED' in field_name:
                self._add_field_to_layout('sales', field_def)
            elif 'MTG' in field_name or 'MORTGAGE' in field_name:
                self._add_field_to_layout('mortgage', field_def)
            elif 'OWNER' in field_name:
                self._add_field_to_layout('owner', field_def)
    
        # Build final schema structure
        schema = {
            'version': 'extracted',
            'extraction_date': str(Path.cwd()),
            'file_layouts': self.file_layouts,
            'field_definitions': self.field_definitions,
            'statistics': {
                'total_files': len(self.file_layouts),
                'total_fields': len(self.field_definitions),
                'files': list(self.file_layouts.keys())
            }
        }
        
        return schema
    
    def _add_field_to_layout(self, layout_type: str, field_def: Dict):
        """Add field definition to appropriate layout"""
        # Find or create layout
        layout_key = None
        for key in self.file_layouts:
            if layout_type.lower() in key.lower():
                layout_key = key
                break
        
        if not layout_key:
            layout_key = f"{layout_type}_fields"
            self.file_layouts[layout_key] = {
                'name': layout_key,
                'type': layout_type,
                'fields': [],
                'inferred': True
            }
        
        # Add field if not already present
        existing_names = [f.get('name') for f in self.file_layouts[layout_key]['fields']]
        if field_def.get('name') not in existing_names:
            self.file_layouts[layout_key]['fields'].append(field_def)
    
    def save_schema(self, schema: Dict, output_path: Path):
        """Save extracted schema to JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(schema, f, indent=2)
            logger.info(f"Schema saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save schema: {e}")
    
    def get_file_schema(self, file_name: str) -> Optional[Dict]:
        """Get schema for a specific file"""
        return self.file_layouts.get(file_name)
    
    def get_field_definitions(self, file_type: Optional[str] = None) -> List[Dict]:
        """Get field definitions, optionally filtered by file type"""
        if not file_type:
            return self.field_definitions
        
        # Filter by file type
        filtered = []
        for field_def in self.field_definitions:
            if file_type.lower() in str(field_def).lower():
                filtered.append(field_def)
        
        return filtered


if __name__ == "__main__":
    # Test the parser
    parser = LayoutPDFParser()
    
    # Assume PDF has been downloaded
    pdf_path = Path("data/broward_layout_schema/pdfs/ExportFilesLayout_latest.pdf")
    
    if pdf_path.exists():
        schema = parser.parse_pdf(pdf_path)
        
        # Save schema
        output_path = Path("data/broward_layout_schema/extracted/schema.json")
        output_path.parent.mkdir(exist_ok=True)
        parser.save_schema(schema, output_path)
        
        # Print summary
        print(f"\nExtracted Schema Summary:")
        print(f"  Files: {schema['statistics']['total_files']}")
        print(f"  Fields: {schema['statistics']['total_fields']}")
        print(f"  File Types: {', '.join(schema['statistics']['files'][:5])}")
    else:
        print(f"PDF not found at {pdf_path}")