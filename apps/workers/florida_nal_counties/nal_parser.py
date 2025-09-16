"""
Parser for Florida Revenue NAL (Name Address Library) Files
Parses NAL files for all Florida counties
"""

import re
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NALParser:
    """Parser for Florida NAL county files"""
    
    # NAL field structure (fixed-width format)
    NAL_FIELD_LAYOUT = [
        {'name': 'PARCEL_ID', 'start': 1, 'end': 30, 'type': 'string', 'description': 'Parcel identification number'},
        {'name': 'CO_NO', 'start': 31, 'end': 32, 'type': 'string', 'description': 'County number'},
        {'name': 'ASMNT_YR', 'start': 33, 'end': 36, 'type': 'integer', 'description': 'Assessment year'},
        {'name': 'OWN_NAME', 'start': 37, 'end': 106, 'type': 'string', 'description': 'Owner name'},
        {'name': 'OWN_ADDR1', 'start': 107, 'end': 166, 'type': 'string', 'description': 'Owner address line 1'},
        {'name': 'OWN_ADDR2', 'start': 167, 'end': 226, 'type': 'string', 'description': 'Owner address line 2'},
        {'name': 'OWN_CITY', 'start': 227, 'end': 271, 'type': 'string', 'description': 'Owner city'},
        {'name': 'OWN_STATE', 'start': 272, 'end': 273, 'type': 'string', 'description': 'Owner state'},
        {'name': 'OWN_ZIPCD', 'start': 274, 'end': 283, 'type': 'string', 'description': 'Owner ZIP code'},
        {'name': 'OWN_STATE_DOMICILE', 'start': 284, 'end': 285, 'type': 'string', 'description': 'Owner state of domicile'},
        {'name': 'VI_CD', 'start': 286, 'end': 286, 'type': 'string', 'description': 'Vacancy indicator'},
        {'name': 'FIDU_CD', 'start': 287, 'end': 287, 'type': 'string', 'description': 'Fiduciary code'},
        {'name': 'S_LEGAL', 'start': 288, 'end': 337, 'type': 'string', 'description': 'Short legal description'},
        {'name': 'APP_STAT', 'start': 338, 'end': 339, 'type': 'string', 'description': 'Appraisal status'},
        {'name': 'CNTY_CD', 'start': 340, 'end': 344, 'type': 'string', 'description': 'County code'},
        {'name': 'FILE_T', 'start': 345, 'end': 349, 'type': 'string', 'description': 'File type'},
        {'name': 'JV', 'start': 350, 'end': 360, 'type': 'numeric', 'description': 'Just value'},
        {'name': 'AV', 'start': 361, 'end': 371, 'type': 'numeric', 'description': 'Assessed value'},
        {'name': 'TV', 'start': 372, 'end': 382, 'type': 'numeric', 'description': 'Taxable value'},
        {'name': 'JV_CHNG', 'start': 383, 'end': 383, 'type': 'string', 'description': 'Just value change flag'},
        {'name': 'AV_SD', 'start': 384, 'end': 394, 'type': 'numeric', 'description': 'Assessed value school district'},
        {'name': 'TV_SD', 'start': 395, 'end': 405, 'type': 'numeric', 'description': 'Taxable value school district'},
        {'name': 'JV_HMSTD', 'start': 406, 'end': 416, 'type': 'numeric', 'description': 'Just value homestead'},
        {'name': 'AV_HMSTD', 'start': 417, 'end': 427, 'type': 'numeric', 'description': 'Assessed value homestead'},
        {'name': 'JV_NON_HMSTD_RESD', 'start': 428, 'end': 438, 'type': 'numeric', 'description': 'Just value non-homestead residential'},
        {'name': 'AV_NON_HMSTD_RESD', 'start': 439, 'end': 449, 'type': 'numeric', 'description': 'Assessed value non-homestead residential'},
        {'name': 'JV_RESD_NON_RESD', 'start': 450, 'end': 460, 'type': 'numeric', 'description': 'Just value residential/non-residential'},
        {'name': 'AV_RESD_NON_RESD', 'start': 461, 'end': 471, 'type': 'numeric', 'description': 'Assessed value residential/non-residential'},
        {'name': 'SEQ_NO', 'start': 472, 'end': 472, 'type': 'string', 'description': 'Sequence number'},
        {'name': 'RS_CD', 'start': 473, 'end': 473, 'type': 'string', 'description': 'Real/personal status code'},
        {'name': 'MP_CD', 'start': 474, 'end': 474, 'type': 'string', 'description': 'Multiple parcel code'},
        {'name': 'PREV_HMSTD', 'start': 475, 'end': 475, 'type': 'string', 'description': 'Previous homestead flag'},
        {'name': 'HMSTD_EXEMPT', 'start': 476, 'end': 487, 'type': 'numeric', 'description': 'Homestead exemption'},
        {'name': 'OTH_EXEMPT', 'start': 488, 'end': 499, 'type': 'numeric', 'description': 'Other exemption'},
        {'name': 'CLASS_USE_CD', 'start': 500, 'end': 502, 'type': 'string', 'description': 'Classification use code'},
        {'name': 'TAXING_DIST', 'start': 503, 'end': 506, 'type': 'string', 'description': 'Taxing district'},
        {'name': 'JV_CLASS_USE', 'start': 507, 'end': 517, 'type': 'numeric', 'description': 'Just value by classification use'},
        {'name': 'TV_CLASS_USE', 'start': 518, 'end': 528, 'type': 'numeric', 'description': 'Taxable value by classification use'},
        {'name': 'FIDU_NAME', 'start': 529, 'end': 598, 'type': 'string', 'description': 'Fiduciary name'},
        {'name': 'FIDU_ADDR1', 'start': 599, 'end': 658, 'type': 'string', 'description': 'Fiduciary address line 1'},
        {'name': 'FIDU_ADDR2', 'start': 659, 'end': 718, 'type': 'string', 'description': 'Fiduciary address line 2'},
        {'name': 'FIDU_CITY', 'start': 719, 'end': 763, 'type': 'string', 'description': 'Fiduciary city'},
        {'name': 'FIDU_STATE', 'start': 764, 'end': 765, 'type': 'string', 'description': 'Fiduciary state'},
        {'name': 'FIDU_ZIPCD', 'start': 766, 'end': 775, 'type': 'string', 'description': 'Fiduciary ZIP code'},
        {'name': 'FIDU_STATE_DOMICILE', 'start': 776, 'end': 777, 'type': 'string', 'description': 'Fiduciary state of domicile'},
        {'name': 'OWNER_PREV', 'start': 778, 'end': 847, 'type': 'string', 'description': 'Previous owner name'},
        {'name': 'SITUS_ADDR1', 'start': 848, 'end': 907, 'type': 'string', 'description': 'Situs address line 1'},
        {'name': 'SITUS_ADDR2', 'start': 908, 'end': 967, 'type': 'string', 'description': 'Situs address line 2'},
        {'name': 'SITUS_CITY', 'start': 968, 'end': 1012, 'type': 'string', 'description': 'Situs city'},
        {'name': 'SITUS_STATE', 'start': 1013, 'end': 1014, 'type': 'string', 'description': 'Situs state'},
        {'name': 'SITUS_ZIPCD', 'start': 1015, 'end': 1024, 'type': 'string', 'description': 'Situs ZIP code'}
    ]
    
    def __init__(self):
        """Initialize the NAL parser"""
        self.stats = {
            'files_parsed': 0,
            'records_parsed': 0,
            'errors': 0
        }
    
    def parse_file(self, file_path: Path) -> List[Dict]:
        """
        Parse a single NAL file
        
        Args:
            file_path: Path to the NAL file
            
        Returns:
            List of parsed records
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        logger.info(f"Parsing NAL file: {file_path}")
        
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        record = self._parse_line(line)
                        if record:
                            records.append(record)
                            self.stats['records_parsed'] += 1
                            
                            # Progress reporting
                            if self.stats['records_parsed'] % 10000 == 0:
                                logger.info(f"  Parsed {self.stats['records_parsed']:,} records...")
                                
                    except Exception as e:
                        if self.stats['errors'] < 100:  # Limit error logging
                            logger.debug(f"Error parsing line {line_num}: {e}")
                        self.stats['errors'] += 1
            
            self.stats['files_parsed'] += 1
            logger.info(f"Parsed {len(records):,} records from {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse NAL file {file_path}: {e}")
            self.stats['errors'] += 1
        
        return records
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single line from NAL file (fixed-width format)
        
        Args:
            line: Line from the file
            
        Returns:
            Parsed record or None if invalid
        """
        if len(line) < 100:  # Minimum expected line length
            return None
        
        record = {}
        
        for field in self.NAL_FIELD_LAYOUT:
            try:
                # Extract field value (convert to 0-based indexing)
                start = field['start'] - 1
                end = field['end']
                
                if len(line) >= end:
                    value = line[start:end].strip()
                else:
                    value = line[start:].strip() if len(line) > start else ''
                
                # Convert based on type
                if value:
                    if field['type'] == 'integer':
                        try:
                            record[field['name']] = int(value)
                        except ValueError:
                            record[field['name']] = None
                    elif field['type'] == 'numeric':
                        try:
                            record[field['name']] = float(value)
                        except ValueError:
                            record[field['name']] = None
                    else:
                        record[field['name']] = value
                else:
                    record[field['name']] = None
                    
            except Exception as e:
                logger.debug(f"Error parsing field {field['name']}: {e}")
        
        # Validate minimum required fields
        if record.get('PARCEL_ID') and record.get('CO_NO'):
            # Add metadata
            record['source'] = 'florida_nal'
            record['parsed_at'] = datetime.now().isoformat()
            
            # Clean up parcel ID
            if record['PARCEL_ID']:
                record['PARCEL_ID'] = record['PARCEL_ID'].replace('-', '').replace(' ', '')
            
            return record
        
        return None
    
    def parse_to_csv(self, file_path: Path, output_path: Path) -> bool:
        """
        Parse NAL file and save to CSV
        
        Args:
            file_path: Path to NAL file
            output_path: Path for output CSV
            
        Returns:
            Success status
        """
        records = self.parse_file(file_path)
        
        if not records:
            logger.warning(f"No records parsed from {file_path}")
            return False
        
        try:
            # Get all field names
            fieldnames = [field['name'] for field in self.NAL_FIELD_LAYOUT]
            fieldnames.extend(['source', 'parsed_at'])
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
            
            logger.info(f"Saved {len(records):,} records to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            return False
    
    def extract_summary(self, records: List[Dict]) -> Dict:
        """
        Extract summary statistics from parsed records
        
        Args:
            records: List of parsed NAL records
            
        Returns:
            Summary statistics
        """
        if not records:
            return {}
        
        summary = {
            'total_records': len(records),
            'county_code': records[0].get('CO_NO') if records else None,
            'assessment_year': records[0].get('ASMNT_YR') if records else None,
            'unique_parcels': len(set(r.get('PARCEL_ID') for r in records if r.get('PARCEL_ID'))),
            'homestead_count': sum(1 for r in records if r.get('HMSTD_EXEMPT', 0) > 0),
            'total_just_value': sum(r.get('JV', 0) for r in records if r.get('JV')),
            'total_taxable_value': sum(r.get('TV', 0) for r in records if r.get('TV')),
            'avg_just_value': None,
            'avg_taxable_value': None,
            'property_types': {}
        }
        
        # Calculate averages
        if summary['total_records'] > 0:
            summary['avg_just_value'] = summary['total_just_value'] / summary['total_records']
            summary['avg_taxable_value'] = summary['total_taxable_value'] / summary['total_records']
        
        # Count property types
        for record in records:
            use_code = record.get('CLASS_USE_CD', 'Unknown')
            if use_code:
                summary['property_types'][use_code] = summary['property_types'].get(use_code, 0) + 1
        
        return summary
    
    def get_stats(self) -> Dict:
        """Get parsing statistics"""
        return self.stats.copy()


class NALBatchProcessor:
    """Process multiple NAL files in batch"""
    
    def __init__(self, output_dir: str = "data/florida_nal_processed"):
        """
        Initialize batch processor
        
        Args:
            output_dir: Directory for processed files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = FloridaNALParser()
        self.processing_log = []
    
    def process_county(self, file_path: Path, county_code: str) -> Dict:
        """
        Process a single county NAL file
        
        Args:
            file_path: Path to NAL file
            county_code: County code
            
        Returns:
            Processing result
        """
        logger.info(f"Processing NAL file for county {county_code}")
        
        result = {
            'county_code': county_code,
            'file_path': str(file_path),
            'start_time': datetime.now().isoformat()
        }
        
        try:
            # Parse the file
            records = self.parser.parse_file(file_path)
            
            if records:
                # Save to CSV
                csv_filename = f"NAL_{county_code}_processed.csv"
                csv_path = self.output_dir / csv_filename
                
                fieldnames = [field['name'] for field in self.parser.NAL_FIELD_LAYOUT]
                fieldnames.extend(['source', 'parsed_at'])
                
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                # Extract summary
                summary = self.parser.extract_summary(records)
                
                result['status'] = 'success'
                result['records_parsed'] = len(records)
                result['output_file'] = str(csv_path)
                result['summary'] = summary
                
                # Save summary
                summary_path = self.output_dir / f"NAL_{county_code}_summary.json"
                with open(summary_path, 'w') as f:
                    json.dump(summary, f, indent=2)
                
            else:
                result['status'] = 'no_records'
                result['records_parsed'] = 0
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Failed to process county {county_code}: {e}")
        
        result['end_time'] = datetime.now().isoformat()
        
        self.processing_log.append(result)
        
        return result
    
    def process_all_counties(self, input_dir: Path) -> Dict:
        """
        Process all county NAL files in a directory
        
        Args:
            input_dir: Directory containing NAL files
            
        Returns:
            Processing summary
        """
        nal_files = list(input_dir.glob("NAL*.txt"))
        
        logger.info(f"Found {len(nal_files)} NAL files to process")
        
        results = {
            'total_files': len(nal_files),
            'successful': 0,
            'failed': 0,
            'total_records': 0,
            'counties': []
        }
        
        for file_path in nal_files:
            # Extract county code from filename (NAL06P2025.txt -> 06)
            match = re.match(r'NAL(\d{2})P', file_path.name)
            if match:
                county_code = match.group(1)
                
                result = self.process_county(file_path, county_code)
                
                if result['status'] == 'success':
                    results['successful'] += 1
                    results['total_records'] += result['records_parsed']
                else:
                    results['failed'] += 1
                
                results['counties'].append({
                    'county_code': county_code,
                    'status': result['status'],
                    'records': result.get('records_parsed', 0)
                })
        
        # Save processing log
        log_path = self.output_dir / "processing_log.json"
        with open(log_path, 'w') as f:
            json.dump(self.processing_log, f, indent=2, default=str)
        
        return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Parse single file
        file_path = Path(sys.argv[1])
        
        if file_path.exists():
            parser = FloridaNALParser()
            records = parser.parse_file(file_path)
            
            print(f"\nParsed {len(records):,} records")
            
            if records:
                # Show sample record
                print("\nSample record:")
                sample = records[0]
                for key, value in list(sample.items())[:10]:
                    print(f"  {key}: {value}")
                
                # Show summary
                summary = parser.extract_summary(records)
                print("\nSummary:")
                print(f"  Total records: {summary['total_records']:,}")
                print(f"  Unique parcels: {summary['unique_parcels']:,}")
                print(f"  Homestead count: {summary['homestead_count']:,}")
                print(f"  Avg just value: ${summary['avg_just_value']:,.2f}")
        else:
            print(f"File not found: {file_path}")
    else:
        print("Usage: python nal_parser.py <nal_file.txt>")