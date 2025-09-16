"""
Parser for Florida Revenue NAV (Non-Ad Valorem Assessment) Files
Parses NAV district files
"""

import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NAVParser:
    """Parser for Florida NAV district files"""
    
    # NAV field structure (fixed-width format based on Florida Revenue specification)
    NAV_FIELD_LAYOUT = [
        {'name': 'DISTRICT_CODE', 'start': 1, 'end': 10, 'type': 'string', 'description': 'District code'},
        {'name': 'DISTRICT_NAME', 'start': 11, 'end': 90, 'type': 'string', 'description': 'District name'},
        {'name': 'COUNTY_CODE', 'start': 91, 'end': 92, 'type': 'string', 'description': 'County code'},
        {'name': 'COUNTY_NAME', 'start': 93, 'end': 142, 'type': 'string', 'description': 'County name'},
        {'name': 'ASSESSMENT_YEAR', 'start': 143, 'end': 146, 'type': 'integer', 'description': 'Assessment year'},
        {'name': 'DISTRICT_TYPE', 'start': 147, 'end': 156, 'type': 'string', 'description': 'Type of district'},
        {'name': 'LEVY_TYPE', 'start': 157, 'end': 166, 'type': 'string', 'description': 'Type of levy'},
        {'name': 'LEVY_RATE', 'start': 167, 'end': 181, 'type': 'numeric', 'description': 'Levy rate'},
        {'name': 'TOTAL_ASSESSED_VALUE', 'start': 182, 'end': 201, 'type': 'numeric', 'description': 'Total assessed value'},
        {'name': 'TOTAL_TAXABLE_VALUE', 'start': 202, 'end': 221, 'type': 'numeric', 'description': 'Total taxable value'},
        {'name': 'TOTAL_LEVY_AMOUNT', 'start': 222, 'end': 241, 'type': 'numeric', 'description': 'Total levy amount'},
        {'name': 'PARCEL_COUNT', 'start': 242, 'end': 251, 'type': 'integer', 'description': 'Number of parcels'},
        {'name': 'EXEMPT_VALUE', 'start': 252, 'end': 271, 'type': 'numeric', 'description': 'Total exempt value'},
        {'name': 'HOMESTEAD_COUNT', 'start': 272, 'end': 281, 'type': 'integer', 'description': 'Number of homestead properties'},
        {'name': 'AUTHORITY_NAME', 'start': 282, 'end': 381, 'type': 'string', 'description': 'Levying authority name'},
        {'name': 'AUTHORITY_TYPE', 'start': 382, 'end': 391, 'type': 'string', 'description': 'Type of authority'},
        {'name': 'SERVICE_TYPE', 'start': 392, 'end': 441, 'type': 'string', 'description': 'Type of service provided'},
        {'name': 'BOND_ISSUE', 'start': 442, 'end': 461, 'type': 'string', 'description': 'Bond issue identifier'},
        {'name': 'BOND_AMOUNT', 'start': 462, 'end': 481, 'type': 'numeric', 'description': 'Bond amount'},
        {'name': 'MATURITY_DATE', 'start': 482, 'end': 489, 'type': 'string', 'description': 'Bond maturity date'},
        {'name': 'COLLECTION_METHOD', 'start': 490, 'end': 509, 'type': 'string', 'description': 'Collection method'},
        {'name': 'BILLING_FREQUENCY', 'start': 510, 'end': 519, 'type': 'string', 'description': 'Billing frequency'},
        {'name': 'DUE_DATE', 'start': 520, 'end': 527, 'type': 'string', 'description': 'Payment due date'},
        {'name': 'DELINQUENT_DATE', 'start': 528, 'end': 535, 'type': 'string', 'description': 'Delinquency date'},
        {'name': 'PENALTY_RATE', 'start': 536, 'end': 545, 'type': 'numeric', 'description': 'Penalty rate'},
        {'name': 'CREATED_DATE', 'start': 546, 'end': 553, 'type': 'string', 'description': 'Record creation date'},
        {'name': 'MODIFIED_DATE', 'start': 554, 'end': 561, 'type': 'string', 'description': 'Record modification date'},
        {'name': 'STATUS', 'start': 562, 'end': 571, 'type': 'string', 'description': 'District status'},
        {'name': 'NOTES', 'start': 572, 'end': 771, 'type': 'string', 'description': 'Additional notes'}
    ]
    
    def __init__(self):
        """Initialize NAV parser"""
        self.field_map = {field['name']: field for field in self.NAV_FIELD_LAYOUT}
        self.total_fields = len(self.NAV_FIELD_LAYOUT)
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single line of NAV data
        
        Args:
            line: Fixed-width line from NAV file
            
        Returns:
            Parsed record as dictionary
        """
        record = {}
        
        for field in self.NAV_FIELD_LAYOUT:
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
        Parse a NAV file
        
        Args:
            file_path: Path to NAV file
            max_records: Maximum records to parse (None for all)
            
        Returns:
            Parsing results with records and statistics
        """
        logger.info(f"Parsing NAV file: {file_path}")
        
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
                        if record.get('DISTRICT_CODE'):
                            records.append(record)
                        else:
                            errors.append({
                                'line': line_num,
                                'error': 'Missing DISTRICT_CODE',
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
            logger.error(f"Error parsing NAV file: {e}")
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
            records: List of parsed NAV records
            
        Returns:
            Statistics dictionary
        """
        if not records:
            return {}
        
        stats = {
            'total_records': len(records),
            'unique_districts': len(set(r['DISTRICT_CODE'] for r in records if r.get('DISTRICT_CODE'))),
            'unique_counties': len(set(r['COUNTY_CODE'] for r in records if r.get('COUNTY_CODE'))),
            'total_levy_amount': sum(r.get('TOTAL_LEVY_AMOUNT', 0) or 0 for r in records),
            'total_assessed_value': sum(r.get('TOTAL_ASSESSED_VALUE', 0) or 0 for r in records),
            'total_taxable_value': sum(r.get('TOTAL_TAXABLE_VALUE', 0) or 0 for r in records),
            'total_parcel_count': sum(r.get('PARCEL_COUNT', 0) or 0 for r in records),
            'total_bond_amount': sum(r.get('BOND_AMOUNT', 0) or 0 for r in records)
        }
        
        # District type breakdown
        district_types = {}
        for record in records:
            district_type = record.get('DISTRICT_TYPE', 'Unknown')
            if district_type:
                district_types[district_type] = district_types.get(district_type, 0) + 1
        
        stats['district_types'] = district_types
        
        # Authority type breakdown
        authority_types = {}
        for record in records:
            authority_type = record.get('AUTHORITY_TYPE', 'Unknown')
            if authority_type:
                authority_types[authority_type] = authority_types.get(authority_type, 0) + 1
        
        stats['authority_types'] = authority_types
        
        # Service type breakdown
        service_types = {}
        for record in records:
            service_type = record.get('SERVICE_TYPE', 'Unknown')
            if service_type:
                service_types[service_type] = service_types.get(service_type, 0) + 1
        
        # Top 10 service types
        stats['top_service_types'] = dict(sorted(service_types.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Counties with most districts
        counties = {}
        for record in records:
            county = record.get('COUNTY_NAME', 'Unknown')
            if county:
                counties[county] = counties.get(county, 0) + 1
        
        stats['top_counties'] = dict(sorted(counties.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return stats
    
    def validate_record(self, record: Dict) -> List[str]:
        """
        Validate a NAV record
        
        Args:
            record: Parsed NAV record
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not record.get('DISTRICT_CODE'):
            errors.append("Missing DISTRICT_CODE")
        
        if not record.get('COUNTY_CODE'):
            errors.append("Missing COUNTY_CODE")
        
        if not record.get('ASSESSMENT_YEAR'):
            errors.append("Missing ASSESSMENT_YEAR")
        
        # Validate year
        if record.get('ASSESSMENT_YEAR'):
            year = record['ASSESSMENT_YEAR']
            if not (2000 <= year <= 2030):
                errors.append(f"Invalid ASSESSMENT_YEAR: {year}")
        
        # Validate amounts
        if record.get('TOTAL_LEVY_AMOUNT') is not None and record['TOTAL_LEVY_AMOUNT'] < 0:
            errors.append(f"Negative TOTAL_LEVY_AMOUNT: {record['TOTAL_LEVY_AMOUNT']}")
        
        if record.get('LEVY_RATE') is not None and record['LEVY_RATE'] < 0:
            errors.append(f"Negative LEVY_RATE: {record['LEVY_RATE']}")
        
        return errors
    
    def save_parsed_data(self, parsed_data: Dict, output_path: Path, format: str = 'json'):
        """
        Save parsed NAV data to file
        
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
    
    parser = argparse.ArgumentParser(description='Florida NAV File Parser')
    parser.add_argument('file', help='NAV file to parse')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--max-records', type=int, help='Maximum records to parse')
    parser.add_argument('--validate', action='store_true', help='Validate records')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize parser
    nav_parser = NAVParser()
    
    # Parse file
    file_path = Path(args.file)
    result = nav_parser.parse_file(file_path, max_records=args.max_records)
    
    if result['success']:
        print(f"\nSuccessfully parsed {result['total_records']:,} records")
        
        if args.stats or not args.output:
            # Show statistics
            stats = result.get('statistics', {})
            print("\nStatistics:")
            print(f"  Total records: {stats.get('total_records', 0):,}")
            print(f"  Unique districts: {stats.get('unique_districts', 0):,}")
            print(f"  Unique counties: {stats.get('unique_counties', 0):,}")
            print(f"  Total levy amount: ${stats.get('total_levy_amount', 0):,.2f}")
            print(f"  Total assessed value: ${stats.get('total_assessed_value', 0):,.2f}")
            print(f"  Total parcels: {stats.get('total_parcel_count', 0):,}")
            
            if stats.get('top_counties'):
                print("\n  Top Counties:")
                for county, count in list(stats['top_counties'].items())[:5]:
                    print(f"    - {county}: {count:,} districts")
        
        if args.validate:
            # Validate records
            invalid_count = 0
            for record in result['records'][:1000]:  # Validate first 1000
                errors = nav_parser.validate_record(record)
                if errors:
                    invalid_count += 1
            
            print(f"\nValidation: {invalid_count} invalid records in first 1000")
        
        if args.output:
            # Save output
            output_path = Path(args.output)
            nav_parser.save_parsed_data(result, output_path, format=args.format)
            print(f"\nSaved to {output_path}")
    
    else:
        print(f"Error parsing file: {result.get('error')}")