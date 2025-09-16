"""
Parser for Florida Revenue NAP (Non-Ad Valorem Parcel) Files
Parses NAP files for all Florida counties
"""

import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NAPParser:
    """Parser for Florida NAP county files"""
    
    # NAP field structure (fixed-width format)
    # Based on Florida Revenue NAP specification
    NAP_FIELD_LAYOUT = [
        {'name': 'PARCEL_ID', 'start': 1, 'end': 30, 'type': 'string', 'description': 'Parcel identification number'},
        {'name': 'CO_NO', 'start': 31, 'end': 32, 'type': 'string', 'description': 'County number'},
        {'name': 'ASMNT_YR', 'start': 33, 'end': 36, 'type': 'integer', 'description': 'Assessment year'},
        {'name': 'NAP_CD', 'start': 37, 'end': 40, 'type': 'string', 'description': 'Non-ad valorem assessment code'},
        {'name': 'NAP_DESC', 'start': 41, 'end': 120, 'type': 'string', 'description': 'Non-ad valorem assessment description'},
        {'name': 'NAP_AMT', 'start': 121, 'end': 135, 'type': 'numeric', 'description': 'Non-ad valorem assessment amount'},
        {'name': 'LEVYING_AUTH', 'start': 136, 'end': 185, 'type': 'string', 'description': 'Levying authority'},
        {'name': 'DISTRICT_CD', 'start': 186, 'end': 195, 'type': 'string', 'description': 'District code'},
        {'name': 'DISTRICT_NAME', 'start': 196, 'end': 275, 'type': 'string', 'description': 'District name'},
        {'name': 'ASSESSMENT_TYPE', 'start': 276, 'end': 285, 'type': 'string', 'description': 'Type of assessment'},
        {'name': 'RATE_TYPE', 'start': 286, 'end': 295, 'type': 'string', 'description': 'Rate type (flat/percentage)'},
        {'name': 'RATE_AMT', 'start': 296, 'end': 310, 'type': 'numeric', 'description': 'Rate amount'},
        {'name': 'UNIT_TYPE', 'start': 311, 'end': 320, 'type': 'string', 'description': 'Unit type for assessment'},
        {'name': 'UNIT_COUNT', 'start': 321, 'end': 330, 'type': 'numeric', 'description': 'Number of units'},
        {'name': 'BASE_AMT', 'start': 331, 'end': 345, 'type': 'numeric', 'description': 'Base amount for calculation'},
        {'name': 'EXEMPT_AMT', 'start': 346, 'end': 360, 'type': 'numeric', 'description': 'Exemption amount'},
        {'name': 'DELINQUENT_FLAG', 'start': 361, 'end': 361, 'type': 'string', 'description': 'Delinquent status flag'},
        {'name': 'PAYMENT_STATUS', 'start': 362, 'end': 371, 'type': 'string', 'description': 'Payment status'},
        {'name': 'DUE_DATE', 'start': 372, 'end': 379, 'type': 'string', 'description': 'Payment due date'},
        {'name': 'PAID_DATE', 'start': 380, 'end': 387, 'type': 'string', 'description': 'Payment date'},
        {'name': 'LIEN_FLAG', 'start': 388, 'end': 388, 'type': 'string', 'description': 'Lien status flag'},
        {'name': 'LIEN_DATE', 'start': 389, 'end': 396, 'type': 'string', 'description': 'Lien date'},
        {'name': 'CERTIFICATE_NO', 'start': 397, 'end': 416, 'type': 'string', 'description': 'Tax certificate number'},
        {'name': 'BOND_FLAG', 'start': 417, 'end': 417, 'type': 'string', 'description': 'Bond flag'},
        {'name': 'BOND_AMT', 'start': 418, 'end': 432, 'type': 'numeric', 'description': 'Bond amount'},
        {'name': 'SPECIAL_BENEFIT', 'start': 433, 'end': 447, 'type': 'numeric', 'description': 'Special benefit amount'},
        {'name': 'CDD_FLAG', 'start': 448, 'end': 448, 'type': 'string', 'description': 'CDD (Community Development District) flag'},
        {'name': 'CDD_NAME', 'start': 449, 'end': 528, 'type': 'string', 'description': 'CDD name'},
        {'name': 'HOA_FLAG', 'start': 529, 'end': 529, 'type': 'string', 'description': 'HOA flag'},
        {'name': 'HOA_NAME', 'start': 530, 'end': 609, 'type': 'string', 'description': 'HOA name'},
        {'name': 'MSBU_FLAG', 'start': 610, 'end': 610, 'type': 'string', 'description': 'MSBU (Municipal Service Benefit Unit) flag'},
        {'name': 'MSBU_NAME', 'start': 611, 'end': 690, 'type': 'string', 'description': 'MSBU name'},
        {'name': 'CREATED_DATE', 'start': 691, 'end': 698, 'type': 'string', 'description': 'Record creation date'},
        {'name': 'MODIFIED_DATE', 'start': 699, 'end': 706, 'type': 'string', 'description': 'Record modification date'},
        {'name': 'RECORD_STATUS', 'start': 707, 'end': 707, 'type': 'string', 'description': 'Record status flag'}
    ]
    
    def __init__(self):
        """Initialize NAP parser"""
        self.field_map = {field['name']: field for field in self.NAP_FIELD_LAYOUT}
        self.total_fields = len(self.NAP_FIELD_LAYOUT)
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single line of NAP data
        
        Args:
            line: Fixed-width line from NAP file
            
        Returns:
            Parsed record as dictionary
        """
        record = {}
        
        for field in self.NAP_FIELD_LAYOUT:
            # Extract field value (adjusting for 1-based indexing)
            start = field['start'] - 1
            end = field['end']
            
            if start < len(line):
                value = line[start:end].strip()
                
                # Convert based on type
                if field['type'] == 'integer':
                    try:
                        record[field['name']] = int(value) if value else None
                    except ValueError:
                        record[field['name']] = None
                elif field['type'] == 'numeric':
                    try:
                        # Handle decimal values
                        if value:
                            # Remove any formatting characters
                            value = value.replace(',', '').replace('$', '')
                            record[field['name']] = float(value)
                        else:
                            record[field['name']] = None
                    except ValueError:
                        record[field['name']] = None
                else:
                    # String type
                    record[field['name']] = value if value else None
            else:
                record[field['name']] = None
        
        return record
    
    def parse_file(self, file_path: Path, max_records: Optional[int] = None) -> Dict:
        """
        Parse a NAP file
        
        Args:
            file_path: Path to NAP file
            max_records: Maximum records to parse (None for all)
            
        Returns:
            Parsing results with records and statistics
        """
        logger.info(f"Parsing NAP file: {file_path}")
        
        if not file_path.exists():
            return {
                'success': False,
                'error': f"File not found: {file_path}",
                'records': []
            }
        
        records = []
        errors = []
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    line_count += 1
                    
                    # Check max records limit
                    if max_records and len(records) >= max_records:
                        logger.info(f"Reached max records limit ({max_records})")
                        break
                    
                    try:
                        record = self.parse_line(line)
                        
                        # Validate record has key fields
                        if record.get('PARCEL_ID'):
                            records.append(record)
                        else:
                            errors.append({
                                'line': line_num,
                                'error': 'Missing PARCEL_ID',
                                'data': line[:50] + '...' if len(line) > 50 else line
                            })
                    
                    except Exception as e:
                        errors.append({
                            'line': line_num,
                            'error': str(e),
                            'data': line[:50] + '...' if len(line) > 50 else line
                        })
                    
                    # Progress logging
                    if line_count % 10000 == 0:
                        logger.info(f"Parsed {line_count:,} lines, {len(records):,} valid records")
            
            # Calculate statistics
            stats = self.calculate_statistics(records)
            
            logger.info(f"Parsing complete: {len(records):,} records from {line_count:,} lines")
            
            if errors:
                logger.warning(f"Encountered {len(errors)} parsing errors")
            
            return {
                'success': True,
                'file': str(file_path),
                'total_lines': line_count,
                'total_records': len(records),
                'records': records,
                'errors': errors[:100],  # Limit errors to first 100
                'error_count': len(errors),
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error parsing NAP file: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(file_path),
                'records': records
            }
    
    def calculate_statistics(self, records: List[Dict]) -> Dict:
        """
        Calculate statistics for parsed records
        
        Args:
            records: List of parsed NAP records
            
        Returns:
            Statistics dictionary
        """
        if not records:
            return {}
        
        stats = {
            'total_records': len(records),
            'unique_parcels': len(set(r['PARCEL_ID'] for r in records if r.get('PARCEL_ID'))),
            'unique_districts': len(set(r['DISTRICT_CD'] for r in records if r.get('DISTRICT_CD'))),
            'unique_assessments': len(set(r['NAP_CD'] for r in records if r.get('NAP_CD'))),
            'total_assessment_amount': sum(r.get('NAP_AMT', 0) or 0 for r in records),
            'delinquent_count': sum(1 for r in records if r.get('DELINQUENT_FLAG') == 'Y'),
            'lien_count': sum(1 for r in records if r.get('LIEN_FLAG') == 'Y'),
            'cdd_count': sum(1 for r in records if r.get('CDD_FLAG') == 'Y'),
            'hoa_count': sum(1 for r in records if r.get('HOA_FLAG') == 'Y'),
            'msbu_count': sum(1 for r in records if r.get('MSBU_FLAG') == 'Y')
        }
        
        # Assessment type breakdown
        assessment_types = {}
        for record in records:
            assessment_type = record.get('ASSESSMENT_TYPE', 'Unknown')
            if assessment_type:
                assessment_types[assessment_type] = assessment_types.get(assessment_type, 0) + 1
        
        stats['assessment_types'] = assessment_types
        
        # District breakdown
        districts = {}
        for record in records:
            district = record.get('DISTRICT_NAME', 'Unknown')
            if district:
                districts[district] = districts.get(district, 0) + 1
        
        # Top 10 districts
        stats['top_districts'] = dict(sorted(districts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Payment status breakdown
        payment_status = {}
        for record in records:
            status = record.get('PAYMENT_STATUS', 'Unknown')
            if status:
                payment_status[status] = payment_status.get(status, 0) + 1
        
        stats['payment_status'] = payment_status
        
        return stats
    
    def validate_record(self, record: Dict) -> List[str]:
        """
        Validate a NAP record
        
        Args:
            record: Parsed NAP record
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not record.get('PARCEL_ID'):
            errors.append("Missing PARCEL_ID")
        
        if not record.get('CO_NO'):
            errors.append("Missing CO_NO (County Number)")
        
        if not record.get('ASMNT_YR'):
            errors.append("Missing ASMNT_YR (Assessment Year)")
        
        # Validate year
        if record.get('ASMNT_YR'):
            year = record['ASMNT_YR']
            if not (2000 <= year <= 2030):
                errors.append(f"Invalid ASMNT_YR: {year}")
        
        # Validate amounts
        if record.get('NAP_AMT') is not None and record['NAP_AMT'] < 0:
            errors.append(f"Negative NAP_AMT: {record['NAP_AMT']}")
        
        # Validate flags
        for flag_field in ['DELINQUENT_FLAG', 'LIEN_FLAG', 'CDD_FLAG', 'HOA_FLAG', 'MSBU_FLAG', 'BOND_FLAG']:
            if record.get(flag_field) and record[flag_field] not in ['Y', 'N', '']:
                errors.append(f"Invalid {flag_field}: {record[flag_field]}")
        
        return errors
    
    def save_parsed_data(self, parsed_data: Dict, output_path: Path, format: str = 'json'):
        """
        Save parsed NAP data to file
        
        Args:
            parsed_data: Parsed data dictionary
            output_path: Output file path
            format: Output format ('json' or 'csv')
        """
        if format == 'json':
            # Save as JSON
            with open(output_path, 'w') as f:
                json.dump(parsed_data, f, indent=2, default=str)
            logger.info(f"Saved parsed data to {output_path}")
            
        elif format == 'csv' and parsed_data.get('records'):
            # Save as CSV
            records = parsed_data['records']
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
            
            logger.info(f"Saved {len(records)} records to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAP File Parser')
    parser.add_argument('file', help='NAP file to parse')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--max-records', type=int, help='Maximum records to parse')
    parser.add_argument('--validate', action='store_true', help='Validate records')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize parser
    nap_parser = NAPParser()
    
    # Parse file
    file_path = Path(args.file)
    result = nap_parser.parse_file(file_path, max_records=args.max_records)
    
    if result['success']:
        print(f"\nSuccessfully parsed {result['total_records']:,} records")
        
        if args.stats or not args.output:
            # Show statistics
            stats = result.get('statistics', {})
            print("\nStatistics:")
            print(f"  Total records: {stats.get('total_records', 0):,}")
            print(f"  Unique parcels: {stats.get('unique_parcels', 0):,}")
            print(f"  Unique districts: {stats.get('unique_districts', 0):,}")
            print(f"  Total assessment amount: ${stats.get('total_assessment_amount', 0):,.2f}")
            print(f"  Delinquent count: {stats.get('delinquent_count', 0):,}")
            print(f"  Properties with liens: {stats.get('lien_count', 0):,}")
            
            if stats.get('top_districts'):
                print("\n  Top Districts:")
                for district, count in list(stats['top_districts'].items())[:5]:
                    print(f"    - {district}: {count:,}")
        
        if args.validate:
            # Validate records
            invalid_count = 0
            for record in result['records'][:1000]:  # Validate first 1000
                errors = nap_parser.validate_record(record)
                if errors:
                    invalid_count += 1
            
            print(f"\nValidation: {invalid_count} invalid records in first 1000")
        
        if args.output:
            # Save output
            output_path = Path(args.output)
            nap_parser.save_parsed_data(result, output_path, format=args.format)
            print(f"\nSaved to {output_path}")
    
    else:
        print(f"Error parsing file: {result.get('error')}")