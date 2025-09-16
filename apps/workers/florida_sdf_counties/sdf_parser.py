"""
Parser for Florida Revenue SDF (Sales Data File) Files
Parses property sales data for all Florida counties
"""

import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SDFParser:
    """Parser for Florida SDF sales data files"""
    
    # SDF field structure (fixed-width format based on Florida Revenue specification)
    SDF_FIELD_LAYOUT = [
        {'name': 'CO_NO', 'start': 1, 'end': 2, 'type': 'string', 'description': 'County number'},
        {'name': 'PARCEL_ID', 'start': 3, 'end': 32, 'type': 'string', 'description': 'Parcel identification number'},
        {'name': 'SALE_YR', 'start': 33, 'end': 36, 'type': 'integer', 'description': 'Sale year'},
        {'name': 'SALE_MO', 'start': 37, 'end': 38, 'type': 'integer', 'description': 'Sale month'},
        {'name': 'SALE_DAY', 'start': 39, 'end': 40, 'type': 'integer', 'description': 'Sale day'},
        {'name': 'SALE_PRC', 'start': 41, 'end': 52, 'type': 'numeric', 'description': 'Sale price'},
        {'name': 'OR_BOOK', 'start': 53, 'end': 57, 'type': 'string', 'description': 'Official records book'},
        {'name': 'OR_PAGE', 'start': 58, 'end': 62, 'type': 'string', 'description': 'Official records page'},
        {'name': 'CLERK_NO', 'start': 63, 'end': 74, 'type': 'string', 'description': 'Clerk instrument number'},
        {'name': 'QUAL_CD', 'start': 75, 'end': 76, 'type': 'string', 'description': 'Qualification code'},
        {'name': 'VI_CD', 'start': 77, 'end': 77, 'type': 'string', 'description': 'Vacant/improved code'},
        {'name': 'GRANTOR', 'start': 78, 'end': 147, 'type': 'string', 'description': 'Grantor name'},
        {'name': 'GRANTEE', 'start': 148, 'end': 217, 'type': 'string', 'description': 'Grantee name'},
        {'name': 'MULTI_PAR_SAL', 'start': 218, 'end': 218, 'type': 'string', 'description': 'Multi-parcel sale flag'},
        {'name': 'SALE_TYPE', 'start': 219, 'end': 220, 'type': 'string', 'description': 'Type of sale'},
        {'name': 'DEED_TYPE', 'start': 221, 'end': 222, 'type': 'string', 'description': 'Type of deed'},
        {'name': 'REA_CD', 'start': 223, 'end': 223, 'type': 'string', 'description': 'Real estate agent code'},
        {'name': 'FIN_CD', 'start': 224, 'end': 224, 'type': 'string', 'description': 'Financing code'},
        {'name': 'VERIF_CD', 'start': 225, 'end': 225, 'type': 'string', 'description': 'Verification code'},
        {'name': 'INSTR_TYP', 'start': 226, 'end': 227, 'type': 'string', 'description': 'Instrument type'},
        {'name': 'FORECLOSURE', 'start': 228, 'end': 228, 'type': 'string', 'description': 'Foreclosure flag'},
        {'name': 'REO_FLAG', 'start': 229, 'end': 229, 'type': 'string', 'description': 'REO (bank-owned) flag'},
        {'name': 'SHORT_SALE', 'start': 230, 'end': 230, 'type': 'string', 'description': 'Short sale flag'},
        {'name': 'RESALE_FLAG', 'start': 231, 'end': 231, 'type': 'string', 'description': 'Resale flag'},
        {'name': 'ARMS_LENGTH', 'start': 232, 'end': 232, 'type': 'string', 'description': 'Arms length transaction flag'},
        {'name': 'DISTRESSED', 'start': 233, 'end': 233, 'type': 'string', 'description': 'Distressed sale flag'},
        {'name': 'TRANSFER_ACREAGE', 'start': 234, 'end': 243, 'type': 'numeric', 'description': 'Transfer acreage'},
        {'name': 'PROPERTY_USE', 'start': 244, 'end': 246, 'type': 'string', 'description': 'Property use code'},
        {'name': 'SITE_ADDRESS', 'start': 247, 'end': 346, 'type': 'string', 'description': 'Site address'},
        {'name': 'SITE_CITY', 'start': 347, 'end': 396, 'type': 'string', 'description': 'Site city'},
        {'name': 'SITE_ZIP', 'start': 397, 'end': 406, 'type': 'string', 'description': 'Site ZIP code'}
    ]
    
    # Qualification codes and their meanings
    QUAL_CODES = {
        'Q': 'Qualified - Arms length transaction',
        'U': 'Unqualified - Not arms length',
        'W': 'Warranty deed',
        'S': 'Special warranty deed',
        'B': 'Bargain and sale deed',
        'C': 'Contract for deed',
        'T': 'Trustee deed',
        'D': 'Deed',
        'E': 'Exchange',
        'F': 'Foreclosure',
        'G': 'Gift',
        'L': 'Lease',
        'N': 'No deed',
        'P': 'Personal representative deed',
        'Q': 'Quit claim deed',
        'R': 'Trustee deed upon sale',
        'V': 'Non-validated',
        'X': 'Corrective deed',
        'Y': 'Corporation/partnership deed',
        'Z': 'Transfer to/from trust'
    }
    
    def __init__(self):
        """Initialize SDF parser"""
        self.field_map = {field['name']: field for field in self.SDF_FIELD_LAYOUT}
        self.total_fields = len(self.SDF_FIELD_LAYOUT)
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single line of SDF data
        
        Args:
            line: Fixed-width line from SDF file
            
        Returns:
            Parsed record as dictionary
        """
        record = {}
        
        for field in self.SDF_FIELD_LAYOUT:
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
        
        # Add derived fields
        if record.get('SALE_YR') and record.get('SALE_MO'):
            try:
                sale_day = record.get('SALE_DAY', 1) or 1
                record['SALE_DATE'] = f"{record['SALE_YR']}-{str(record['SALE_MO']).zfill(2)}-{str(sale_day).zfill(2)}"
            except:
                record['SALE_DATE'] = None
        
        # Decode qualification code
        if record.get('QUAL_CD'):
            record['QUAL_DESC'] = self.QUAL_CODES.get(record['QUAL_CD'], 'Unknown')
        
        # Parse flags
        record['IS_MULTI_PARCEL'] = record.get('MULTI_PAR_SAL') == 'Y'
        record['IS_FORECLOSURE'] = record.get('FORECLOSURE') == 'Y'
        record['IS_REO'] = record.get('REO_FLAG') == 'Y'
        record['IS_SHORT_SALE'] = record.get('SHORT_SALE') == 'Y'
        record['IS_ARMS_LENGTH'] = record.get('ARMS_LENGTH') == 'Y'
        record['IS_DISTRESSED'] = record.get('DISTRESSED') == 'Y'
        
        return record
    
    def parse_file(self, file_path: Path, max_records: Optional[int] = None) -> Dict:
        """
        Parse an SDF file
        
        Args:
            file_path: Path to SDF file
            max_records: Maximum records to parse (None for all)
            
        Returns:
            Parsing results with records and statistics
        """
        logger.info(f"Parsing SDF file: {file_path}")
        
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
                    # Skip empty lines or headers
                    if not line.strip() or line.startswith('#'):
                        continue
                    
                    line_count += 1
                    
                    # Check max records limit
                    if max_records and len(records) >= max_records:
                        logger.info(f"Reached max records limit ({max_records})")
                        break
                    
                    try:
                        record = self.parse_line(line)
                        
                        # Validate record has key fields
                        if record.get('PARCEL_ID') and record.get('SALE_PRC'):
                            records.append(record)
                        else:
                            errors.append({
                                'line': line_num,
                                'error': 'Missing PARCEL_ID or SALE_PRC',
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
            logger.error(f"Error parsing SDF file: {e}")
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
            records: List of parsed SDF records
            
        Returns:
            Statistics dictionary
        """
        if not records:
            return {}
        
        stats = {
            'total_records': len(records),
            'total_sales_volume': sum(r.get('SALE_PRC', 0) or 0 for r in records),
            'average_sale_price': 0,
            'median_sale_price': 0,
            'qualified_sales': sum(1 for r in records if r.get('QUAL_CD') == 'Q'),
            'arms_length_sales': sum(1 for r in records if r.get('IS_ARMS_LENGTH')),
            'foreclosure_sales': sum(1 for r in records if r.get('IS_FORECLOSURE')),
            'reo_sales': sum(1 for r in records if r.get('IS_REO')),
            'short_sales': sum(1 for r in records if r.get('IS_SHORT_SALE')),
            'distressed_sales': sum(1 for r in records if r.get('IS_DISTRESSED')),
            'multi_parcel_sales': sum(1 for r in records if r.get('IS_MULTI_PARCEL'))
        }
        
        # Calculate average
        valid_prices = [r['SALE_PRC'] for r in records if r.get('SALE_PRC') and r['SALE_PRC'] > 0]
        if valid_prices:
            stats['average_sale_price'] = sum(valid_prices) / len(valid_prices)
            
            # Calculate median
            sorted_prices = sorted(valid_prices)
            n = len(sorted_prices)
            if n % 2 == 0:
                stats['median_sale_price'] = (sorted_prices[n//2 - 1] + sorted_prices[n//2]) / 2
            else:
                stats['median_sale_price'] = sorted_prices[n//2]
        
        # Year breakdown
        year_counts = {}
        for record in records:
            year = record.get('SALE_YR')
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        stats['sales_by_year'] = dict(sorted(year_counts.items()))
        
        # Month breakdown for current year
        current_year = datetime.now().year
        month_counts = {}
        for record in records:
            if record.get('SALE_YR') == current_year:
                month = record.get('SALE_MO')
                if month:
                    month_counts[month] = month_counts.get(month, 0) + 1
        
        stats['current_year_by_month'] = month_counts
        
        # Property use breakdown
        use_codes = {}
        for record in records:
            use_code = record.get('PROPERTY_USE', 'Unknown')
            if use_code:
                use_codes[use_code] = use_codes.get(use_code, 0) + 1
        
        stats['property_use_codes'] = dict(sorted(use_codes.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Qualification code breakdown
        qual_codes = {}
        for record in records:
            qual_code = record.get('QUAL_CD', 'Unknown')
            if qual_code:
                qual_codes[qual_code] = qual_codes.get(qual_code, 0) + 1
        
        stats['qualification_codes'] = qual_codes
        
        # Price ranges
        price_ranges = {
            'under_100k': 0,
            '100k_250k': 0,
            '250k_500k': 0,
            '500k_1m': 0,
            '1m_2m': 0,
            'over_2m': 0
        }
        
        for record in records:
            price = record.get('SALE_PRC', 0) or 0
            if price > 0:
                if price < 100000:
                    price_ranges['under_100k'] += 1
                elif price < 250000:
                    price_ranges['100k_250k'] += 1
                elif price < 500000:
                    price_ranges['250k_500k'] += 1
                elif price < 1000000:
                    price_ranges['500k_1m'] += 1
                elif price < 2000000:
                    price_ranges['1m_2m'] += 1
                else:
                    price_ranges['over_2m'] += 1
        
        stats['price_ranges'] = price_ranges
        
        return stats
    
    def validate_record(self, record: Dict) -> List[str]:
        """
        Validate an SDF record
        
        Args:
            record: Parsed SDF record
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not record.get('PARCEL_ID'):
            errors.append("Missing PARCEL_ID")
        
        if not record.get('CO_NO'):
            errors.append("Missing CO_NO (County Number)")
        
        # Validate sale year
        if record.get('SALE_YR'):
            year = record['SALE_YR']
            if not (1900 <= year <= 2030):
                errors.append(f"Invalid SALE_YR: {year}")
        
        # Validate sale price
        if record.get('SALE_PRC') is not None:
            price = record['SALE_PRC']
            if price < 0:
                errors.append(f"Negative SALE_PRC: {price}")
            elif price > 1000000000:  # Over $1 billion
                errors.append(f"Suspiciously high SALE_PRC: {price}")
        
        # Validate qualification code
        if record.get('QUAL_CD'):
            if record['QUAL_CD'] not in self.QUAL_CODES:
                errors.append(f"Unknown QUAL_CD: {record['QUAL_CD']}")
        
        return errors
    
    def save_parsed_data(self, parsed_data: Dict, output_path: Path, format: str = 'json'):
        """
        Save parsed SDF data to file
        
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
    
    parser = argparse.ArgumentParser(description='Florida SDF File Parser')
    parser.add_argument('file', help='SDF file to parse')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    parser.add_argument('--max-records', type=int, help='Maximum records to parse')
    parser.add_argument('--validate', action='store_true', help='Validate records')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize parser
    sdf_parser = SDFParser()
    
    # Parse file
    file_path = Path(args.file)
    result = sdf_parser.parse_file(file_path, max_records=args.max_records)
    
    if result['success']:
        print(f"\nSuccessfully parsed {result['total_records']:,} records")
        
        if args.stats or not args.output:
            # Show statistics
            stats = result.get('statistics', {})
            print("\nStatistics:")
            print(f"  Total records: {stats.get('total_records', 0):,}")
            print(f"  Total sales volume: ${stats.get('total_sales_volume', 0):,.2f}")
            print(f"  Average sale price: ${stats.get('average_sale_price', 0):,.2f}")
            print(f"  Median sale price: ${stats.get('median_sale_price', 0):,.2f}")
            print(f"  Arms length sales: {stats.get('arms_length_sales', 0):,}")
            print(f"  Foreclosure sales: {stats.get('foreclosure_sales', 0):,}")
            
            if stats.get('price_ranges'):
                print("\n  Price Ranges:")
                for range_name, count in stats['price_ranges'].items():
                    print(f"    {range_name}: {count:,}")
        
        if args.validate:
            # Validate records
            invalid_count = 0
            for record in result['records'][:1000]:  # Validate first 1000
                errors = sdf_parser.validate_record(record)
                if errors:
                    invalid_count += 1
            
            print(f"\nValidation: {invalid_count} invalid records in first 1000")
        
        if args.output:
            # Save output
            output_path = Path(args.output)
            sdf_parser.save_parsed_data(result, output_path, format=args.format)
            print(f"\nSaved to {output_path}")
    
    else:
        print(f"Error parsing file: {result.get('error')}")