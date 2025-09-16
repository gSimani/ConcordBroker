"""
Parser for Florida Revenue NAV Assessment Roll Files
Based on NAV Layout PDF specification for Tables N and D
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class NAVRollParser:
    """Parser for Florida NAV Assessment Roll files (Table N and Table D)"""
    
    # Table N field definitions (Parcel account records)
    TABLE_N_FIELDS = [
        {'name': 'roll_type', 'position': 1, 'type': 'alpha', 'length': 1, 'description': 'Roll Type (N for Non ad valorem)'},
        {'name': 'county_number', 'position': 2, 'type': 'numeric', 'length': 2, 'description': 'DOR 2 digit county number (11-77)'},
        {'name': 'pa_parcel_number', 'position': 3, 'type': 'alphanumeric', 'length': 26, 'description': 'Unique parcel number from property appraiser'},
        {'name': 'tc_account_number', 'position': 4, 'type': 'numeric', 'length': 30, 'description': 'Tax Collector real estate account number'},
        {'name': 'tax_year', 'position': 5, 'type': 'numeric', 'length': 4, 'description': '4 digit year'},
        {'name': 'total_assessments', 'position': 6, 'type': 'numeric', 'length': 12, 'description': 'Total amount of all non ad valorem assessments'},
        {'name': 'number_of_assessments', 'position': 7, 'type': 'numeric', 'length': 3, 'description': 'Count of total number of assessments'},
        {'name': 'tax_roll_sequence_number', 'position': 8, 'type': 'numeric', 'length': 7, 'description': 'Sequential number on roll'}
    ]
    
    # Table D field definitions (Assessment detail records)
    TABLE_D_FIELDS = [
        {'name': 'record_type', 'position': 1, 'type': 'alpha', 'length': 1, 'description': 'Record Type (D for detail)'},
        {'name': 'county_number', 'position': 2, 'type': 'numeric', 'length': 2, 'description': 'DOR 2 digit county number (11-77)'},
        {'name': 'pa_parcel_number', 'position': 3, 'type': 'alphanumeric', 'length': 26, 'description': 'Unique parcel number from property appraiser'},
        {'name': 'levy_identifier', 'position': 4, 'type': 'alphanumeric', 'length': 12, 'description': 'Unique identifier for assessment'},
        {'name': 'local_government_code', 'position': 5, 'type': 'numeric', 'length': 1, 'description': 'Type of levy authority'},
        {'name': 'function_code', 'position': 6, 'type': 'numeric', 'length': 2, 'description': 'Primary intended use (codes 1-10)'},
        {'name': 'assessment_amount', 'position': 7, 'type': 'numeric', 'length': 9, 'description': 'Dollar amount of assessment'},
        {'name': 'tax_roll_sequence_number', 'position': 8, 'type': 'numeric', 'length': 7, 'description': 'Sequential number in table'}
    ]
    
    # Local government codes from DR-503NA
    LOCAL_GOVERNMENT_CODES = {
        '1': 'County',
        '2': 'Municipality',
        '3': 'Independent Special District',
        '4': 'Dependent Special District',
        '5': 'MSBU/MSTU',
        '6': 'Water Management District',
        '7': 'Other'
    }
    
    # Function codes from DR-503NA
    FUNCTION_CODES = {
        '1': 'Fire Protection',
        '2': 'Garbage/Solid Waste',
        '3': 'Lighting',
        '4': 'Parks and Recreation',
        '5': 'Stormwater/Drainage',
        '6': 'Waste/Sewer',
        '7': 'Water',
        '8': 'Road/Street Improvement',
        '9': 'Mosquito Control',
        '10': 'Other'
    }
    
    def __init__(self):
        """Initialize NAV Roll parser"""
        self.table_n_records = []
        self.table_d_records = []
        self.statistics = {}
    
    def parse_csv_line(self, line: str, field_definitions: List[Dict]) -> Dict[str, Any]:
        """
        Parse a single CSV line based on field definitions
        
        Args:
            line: CSV line to parse
            field_definitions: Field definitions for the table
            
        Returns:
            Parsed record as dictionary
        """
        values = line.strip().split(',')
        record = {}
        
        for i, field_def in enumerate(field_definitions):
            if i < len(values):
                value = values[i].strip()
                
                # Convert based on type
                if field_def['type'] == 'numeric':
                    try:
                        if 'amount' in field_def['name'] or 'assessment' in field_def['name']:
                            # Handle decimal values for money
                            record[field_def['name']] = float(value) if value else 0.0
                        else:
                            record[field_def['name']] = int(value) if value else 0
                    except ValueError:
                        record[field_def['name']] = None
                        logger.debug(f"Could not parse numeric value: {value} for field {field_def['name']}")
                else:
                    # Alpha or alphanumeric
                    record[field_def['name']] = value if value else None
            else:
                record[field_def['name']] = None
        
        return record
    
    def parse_table_n(self, file_path: Path) -> Tuple[bool, List[Dict], Dict]:
        """
        Parse Table N (Parcel account records) file
        
        Args:
            file_path: Path to NAVN*.TXT file
            
        Returns:
            Tuple of (success, records, statistics)
        """
        records = []
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                
                for line_num, row in enumerate(reader, 1):
                    if not row:
                        continue
                    
                    # Join row back to string for parsing
                    line = ','.join(row)
                    
                    try:
                        record = self.parse_csv_line(line, self.TABLE_N_FIELDS)
                        
                        # Validate roll type
                        if record.get('roll_type') == 'N':
                            records.append(record)
                        else:
                            errors.append(f"Line {line_num}: Invalid roll type '{record.get('roll_type')}'")
                    
                    except Exception as e:
                        errors.append(f"Line {line_num}: {str(e)}")
                    
                    # Progress logging
                    if line_num % 10000 == 0:
                        logger.info(f"Parsed {line_num:,} lines from Table N")
            
            # Calculate statistics
            stats = {
                'total_records': len(records),
                'total_parcels': len(set(r['pa_parcel_number'] for r in records if r.get('pa_parcel_number'))),
                'total_assessment_amount': sum(r.get('total_assessments', 0) or 0 for r in records),
                'avg_assessments_per_parcel': sum(r.get('number_of_assessments', 0) or 0 for r in records) / len(records) if records else 0,
                'parse_errors': len(errors)
            }
            
            # County breakdown
            counties = {}
            for record in records:
                county = record.get('county_number', 'Unknown')
                if county:
                    counties[county] = counties.get(county, 0) + 1
            stats['counties'] = counties
            
            logger.info(f"Successfully parsed {len(records):,} Table N records")
            
            if errors:
                logger.warning(f"Encountered {len(errors)} parsing errors")
                for error in errors[:10]:  # Show first 10 errors
                    logger.debug(error)
            
            return True, records, stats
            
        except Exception as e:
            logger.error(f"Error parsing Table N file: {e}")
            return False, [], {'error': str(e)}
    
    def parse_table_d(self, file_path: Path) -> Tuple[bool, List[Dict], Dict]:
        """
        Parse Table D (Assessment detail records) file
        
        Args:
            file_path: Path to NAVD*.TXT file
            
        Returns:
            Tuple of (success, records, statistics)
        """
        records = []
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                
                for line_num, row in enumerate(reader, 1):
                    if not row:
                        continue
                    
                    # Join row back to string for parsing
                    line = ','.join(row)
                    
                    try:
                        record = self.parse_csv_line(line, self.TABLE_D_FIELDS)
                        
                        # Validate record type
                        if record.get('record_type') == 'D':
                            # Add decoded values
                            if record.get('local_government_code'):
                                record['local_government_type'] = self.LOCAL_GOVERNMENT_CODES.get(
                                    str(record['local_government_code']), 'Unknown'
                                )
                            
                            if record.get('function_code'):
                                record['function_description'] = self.FUNCTION_CODES.get(
                                    str(record['function_code']), 'Other'
                                )
                            
                            records.append(record)
                        else:
                            errors.append(f"Line {line_num}: Invalid record type '{record.get('record_type')}'")
                    
                    except Exception as e:
                        errors.append(f"Line {line_num}: {str(e)}")
                    
                    # Progress logging
                    if line_num % 10000 == 0:
                        logger.info(f"Parsed {line_num:,} lines from Table D")
            
            # Calculate statistics
            stats = {
                'total_records': len(records),
                'unique_levies': len(set(r['levy_identifier'] for r in records if r.get('levy_identifier'))),
                'total_assessment_amount': sum(r.get('assessment_amount', 0) or 0 for r in records),
                'parse_errors': len(errors)
            }
            
            # Government type breakdown
            gov_types = {}
            for record in records:
                gov_type = record.get('local_government_type', 'Unknown')
                if gov_type:
                    gov_types[gov_type] = gov_types.get(gov_type, 0) + 1
            stats['government_types'] = gov_types
            
            # Function breakdown
            functions = {}
            for record in records:
                function = record.get('function_description', 'Unknown')
                if function:
                    functions[function] = functions.get(function, 0) + 1
            stats['function_types'] = functions
            
            logger.info(f"Successfully parsed {len(records):,} Table D records")
            
            if errors:
                logger.warning(f"Encountered {len(errors)} parsing errors")
                for error in errors[:10]:  # Show first 10 errors
                    logger.debug(error)
            
            return True, records, stats
            
        except Exception as e:
            logger.error(f"Error parsing Table D file: {e}")
            return False, [], {'error': str(e)}
    
    def parse_nav_roll_files(self, table_n_path: Path, table_d_path: Path) -> Dict:
        """
        Parse both Table N and Table D files together
        
        Args:
            table_n_path: Path to NAVN*.TXT file
            table_d_path: Path to NAVD*.TXT file
            
        Returns:
            Combined parsing results
        """
        logger.info(f"Parsing NAV Roll files:")
        logger.info(f"  Table N: {table_n_path}")
        logger.info(f"  Table D: {table_d_path}")
        
        # Parse Table N
        n_success, n_records, n_stats = self.parse_table_n(table_n_path)
        
        # Parse Table D
        d_success, d_records, d_stats = self.parse_table_d(table_d_path)
        
        if not n_success or not d_success:
            return {
                'success': False,
                'error': f"Failed to parse files. Table N: {n_stats.get('error')}, Table D: {d_stats.get('error')}"
            }
        
        # Match assessments to parcels
        parcel_assessments = {}
        for d_record in d_records:
            parcel_id = d_record.get('pa_parcel_number')
            if parcel_id:
                if parcel_id not in parcel_assessments:
                    parcel_assessments[parcel_id] = []
                parcel_assessments[parcel_id].append(d_record)
        
        # Combine data
        combined_records = []
        for n_record in n_records:
            parcel_id = n_record.get('pa_parcel_number')
            if parcel_id:
                assessments = parcel_assessments.get(parcel_id, [])
                combined_record = {
                    **n_record,
                    'assessments': assessments,
                    'assessment_count': len(assessments),
                    'calculated_total': sum(a.get('assessment_amount', 0) or 0 for a in assessments)
                }
                combined_records.append(combined_record)
        
        # Overall statistics
        overall_stats = {
            'table_n': n_stats,
            'table_d': d_stats,
            'combined': {
                'total_parcels': len(combined_records),
                'parcels_with_assessments': sum(1 for r in combined_records if r['assessment_count'] > 0),
                'total_assessment_amount': sum(r['calculated_total'] for r in combined_records),
                'avg_assessments_per_parcel': sum(r['assessment_count'] for r in combined_records) / len(combined_records) if combined_records else 0
            }
        }
        
        return {
            'success': True,
            'table_n_records': n_records,
            'table_d_records': d_records,
            'combined_records': combined_records,
            'statistics': overall_stats
        }
    
    def extract_filename_info(self, filename: str) -> Dict:
        """
        Extract county, year, and submission info from filename
        Example: NAVN110901.TXT -> County 11, Year 2009, Submission 01
        
        Args:
            filename: NAV filename
            
        Returns:
            Dictionary with extracted information
        """
        info = {}
        
        # Remove extension
        name = Path(filename).stem.upper()
        
        if name.startswith('NAVN'):
            info['table'] = 'N'
            code = name[4:]
        elif name.startswith('NAVD'):
            info['table'] = 'D'
            code = name[4:]
        else:
            return info
        
        # Extract county (2 digits), year (2 digits), submission (2 digits)
        if len(code) >= 6:
            info['county_number'] = code[:2]
            info['year'] = '20' + code[2:4]  # Assuming 2000s
            info['submission'] = code[4:6]
        
        return info


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAV Assessment Roll Parser')
    parser.add_argument('--table-n', help='Path to NAVN*.TXT file', required=True)
    parser.add_argument('--table-d', help='Path to NAVD*.TXT file', required=True)
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--stats-only', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize parser
    nav_parser = NAVRollParser()
    
    # Parse files
    table_n_path = Path(args.table_n)
    table_d_path = Path(args.table_d)
    
    result = nav_parser.parse_nav_roll_files(table_n_path, table_d_path)
    
    if result['success']:
        print(f"\nSuccessfully parsed NAV Roll files")
        
        # Show statistics
        stats = result['statistics']
        print("\nTable N Statistics:")
        print(f"  Total records: {stats['table_n']['total_records']:,}")
        print(f"  Total parcels: {stats['table_n']['total_parcels']:,}")
        print(f"  Total assessments: ${stats['table_n']['total_assessment_amount']:,.2f}")
        
        print("\nTable D Statistics:")
        print(f"  Total records: {stats['table_d']['total_records']:,}")
        print(f"  Unique levies: {stats['table_d']['unique_levies']:,}")
        print(f"  Total amount: ${stats['table_d']['total_assessment_amount']:,.2f}")
        
        if stats['table_d'].get('government_types'):
            print("\n  Government Types:")
            for gov_type, count in stats['table_d']['government_types'].items():
                print(f"    {gov_type}: {count:,}")
        
        if stats['table_d'].get('function_types'):
            print("\n  Function Types:")
            for func, count in stats['table_d']['function_types'].items():
                print(f"    {func}: {count:,}")
        
        print("\nCombined Statistics:")
        print(f"  Total parcels: {stats['combined']['total_parcels']:,}")
        print(f"  Parcels with assessments: {stats['combined']['parcels_with_assessments']:,}")
        print(f"  Total assessment amount: ${stats['combined']['total_assessment_amount']:,.2f}")
        print(f"  Avg assessments per parcel: {stats['combined']['avg_assessments_per_parcel']:.2f}")
        
        if args.output and not args.stats_only:
            # Save output
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nSaved results to {output_path}")
    
    else:
        print(f"Error parsing files: {result.get('error')}")