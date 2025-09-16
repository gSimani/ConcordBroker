"""
Florida Revenue NAV Assessment Roll Database Loader
Loads parsed NAV roll data to Supabase PostgreSQL database
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials in environment variables")
    sys.exit(1)

import requests

class NAVRollDatabaseLoader:
    """Loads NAV Assessment Roll data to Supabase database"""
    
    def __init__(self):
        """Initialize database loader"""
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Table names
        self.parcel_table = 'florida_nav_roll_parcels'
        self.assessment_table = 'florida_nav_roll_assessments'
        
        # Batch settings
        self.batch_size = 500
        
        logger.info("NAV Roll Database Loader initialized")
    
    def create_tables(self) -> bool:
        """
        Create NAV roll tables in database if they don't exist
        
        Returns:
            Success status
        """
        create_parcels_sql = """
        CREATE TABLE IF NOT EXISTS florida_nav_roll_parcels (
            id BIGSERIAL PRIMARY KEY,
            
            -- Key fields
            parcel_id VARCHAR(30) NOT NULL,
            county_number VARCHAR(2) NOT NULL,
            county_name VARCHAR(50),
            roll_type CHAR(1),
            
            -- Assessment information
            assessment_year INTEGER,
            taxing_authority_code VARCHAR(10),
            taxing_authority_name VARCHAR(100),
            
            -- Values
            assessed_value DECIMAL(15, 2),
            taxable_value DECIMAL(15, 2),
            
            -- Government info
            government_type VARCHAR(20),
            government_type_description VARCHAR(100),
            
            -- Status
            status VARCHAR(20),
            
            -- Metadata
            data_source VARCHAR(20) DEFAULT 'NAV_ROLL',
            file_name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT unique_nav_roll_parcel UNIQUE (parcel_id, county_number, assessment_year, taxing_authority_code)
        );
        
        CREATE INDEX IF NOT EXISTS idx_nav_roll_parcel_id ON florida_nav_roll_parcels(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_county ON florida_nav_roll_parcels(county_number);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_year ON florida_nav_roll_parcels(assessment_year);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_authority ON florida_nav_roll_parcels(taxing_authority_code);
        """
        
        create_assessments_sql = """
        CREATE TABLE IF NOT EXISTS florida_nav_roll_assessments (
            id BIGSERIAL PRIMARY KEY,
            
            -- Key fields
            parcel_id VARCHAR(30) NOT NULL,
            county_number VARCHAR(2) NOT NULL,
            assessment_year INTEGER,
            taxing_authority_code VARCHAR(10),
            
            -- Assessment details
            function_code VARCHAR(10),
            function_description VARCHAR(100),
            millage_rate DECIMAL(10, 6),
            
            -- Values
            assessed_value DECIMAL(15, 2),
            taxable_value DECIMAL(15, 2),
            tax_amount DECIMAL(15, 2),
            
            -- Additional info
            levy_type VARCHAR(20),
            district_name VARCHAR(100),
            
            -- Metadata
            data_source VARCHAR(20) DEFAULT 'NAV_ROLL',
            file_name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT unique_nav_roll_assessment UNIQUE (parcel_id, county_number, assessment_year, taxing_authority_code, function_code)
        );
        
        CREATE INDEX IF NOT EXISTS idx_nav_roll_assess_parcel ON florida_nav_roll_assessments(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_assess_county ON florida_nav_roll_assessments(county_number);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_assess_year ON florida_nav_roll_assessments(assessment_year);
        CREATE INDEX IF NOT EXISTS idx_nav_roll_assess_function ON florida_nav_roll_assessments(function_code);
        """
        
        # Note: Table creation would typically be done via Supabase dashboard
        # or migration scripts, not via REST API
        logger.info("Tables should be created via Supabase dashboard or migration scripts")
        logger.info("Parcel table: florida_nav_roll_parcels")
        logger.info("Assessment table: florida_nav_roll_assessments")
        
        return True
    
    def load_parcels(self, records: List[Dict], file_name: str, county_number: str, 
                     county_name: str, year: int) -> Dict:
        """
        Load parcel records to database
        
        Args:
            records: List of parsed parcel records
            file_name: Source file name
            county_number: County code
            county_name: County name
            year: Assessment year
            
        Returns:
            Load result
        """
        if not records:
            return {
                'status': 'no_data',
                'message': 'No parcel records to load'
            }
        
        logger.info(f"Loading {len(records):,} parcel records for {county_name}")
        
        loaded = 0
        failed = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            # Prepare batch data
            batch_data = []
            for record in batch:
                data = {
                    'parcel_id': record.get('parcel_id'),
                    'county_number': county_number,
                    'county_name': county_name,
                    'roll_type': record.get('roll_type'),
                    'assessment_year': year,
                    'taxing_authority_code': record.get('taxing_authority_code'),
                    'taxing_authority_name': self._get_authority_name(record.get('taxing_authority_code')),
                    'assessed_value': record.get('assessed_value'),
                    'taxable_value': record.get('taxable_value'),
                    'government_type': record.get('government_type'),
                    'government_type_description': self._get_government_description(record.get('government_type')),
                    'status': 'active',
                    'file_name': file_name,
                    'data_source': 'NAV_ROLL'
                }
                
                # Clean data
                data = {k: v for k, v in data.items() if v is not None}
                batch_data.append(data)
            
            # Insert batch
            try:
                url = f"{self.supabase_url}/rest/v1/{self.parcel_table}"
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=batch_data
                )
                
                if response.status_code in [200, 201]:
                    loaded += len(batch_data)
                    logger.debug(f"Loaded batch {i//self.batch_size + 1}: {len(batch_data)} records")
                else:
                    failed += len(batch_data)
                    error_msg = f"Batch insert failed: {response.status_code} - {response.text[:200]}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                failed += len(batch_data)
                error_msg = f"Error loading batch: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        result = {
            'status': 'success' if loaded > 0 else 'failed',
            'table': self.parcel_table,
            'total_records': len(records),
            'loaded': loaded,
            'failed': failed,
            'errors': errors[:10]  # Limit errors
        }
        
        logger.info(f"Parcel load complete: {loaded:,} loaded, {failed:,} failed")
        
        return result
    
    def load_assessments(self, records: List[Dict], file_name: str, county_number: str,
                        county_name: str, year: int) -> Dict:
        """
        Load assessment detail records to database
        
        Args:
            records: List of parsed assessment records
            file_name: Source file name
            county_number: County code
            county_name: County name
            year: Assessment year
            
        Returns:
            Load result
        """
        if not records:
            return {
                'status': 'no_data',
                'message': 'No assessment records to load'
            }
        
        logger.info(f"Loading {len(records):,} assessment records for {county_name}")
        
        loaded = 0
        failed = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            # Prepare batch data
            batch_data = []
            for record in batch:
                data = {
                    'parcel_id': record.get('parcel_id'),
                    'county_number': county_number,
                    'assessment_year': year,
                    'taxing_authority_code': record.get('taxing_authority_code'),
                    'function_code': record.get('function_code'),
                    'function_description': self._get_function_description(record.get('function_code')),
                    'millage_rate': record.get('millage_rate'),
                    'assessed_value': record.get('assessed_value'),
                    'taxable_value': record.get('taxable_value'),
                    'tax_amount': record.get('tax_amount'),
                    'levy_type': self._determine_levy_type(record.get('function_code')),
                    'district_name': self._get_authority_name(record.get('taxing_authority_code')),
                    'file_name': file_name,
                    'data_source': 'NAV_ROLL'
                }
                
                # Clean data
                data = {k: v for k, v in data.items() if v is not None}
                batch_data.append(data)
            
            # Insert batch
            try:
                url = f"{self.supabase_url}/rest/v1/{self.assessment_table}"
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=batch_data
                )
                
                if response.status_code in [200, 201]:
                    loaded += len(batch_data)
                    logger.debug(f"Loaded batch {i//self.batch_size + 1}: {len(batch_data)} records")
                else:
                    failed += len(batch_data)
                    error_msg = f"Batch insert failed: {response.status_code} - {response.text[:200]}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                failed += len(batch_data)
                error_msg = f"Error loading batch: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        result = {
            'status': 'success' if loaded > 0 else 'failed',
            'table': self.assessment_table,
            'total_records': len(records),
            'loaded': loaded,
            'failed': failed,
            'errors': errors[:10]  # Limit errors
        }
        
        logger.info(f"Assessment load complete: {loaded:,} loaded, {failed:,} failed")
        
        return result
    
    def load_file(self, parcel_file: Path, assessment_file: Optional[Path], 
                  parsed_data: Dict, county_number: str, county_name: str, year: int) -> Dict:
        """
        Load both parcel and assessment data from parsed files
        
        Args:
            parcel_file: Path to parcel (Table N) file
            assessment_file: Path to assessment (Table D) file (optional)
            parsed_data: Parsed data from NAVRollParser
            county_number: County code
            county_name: County name
            year: Assessment year
            
        Returns:
            Load results
        """
        logger.info(f"Loading NAV Roll data for {county_name} ({county_number}) - Year {year}")
        
        results = {
            'county': county_name,
            'county_code': county_number,
            'year': year,
            'parcels': None,
            'assessments': None,
            'status': 'pending'
        }
        
        # Load parcel records
        if 'table_n_records' in parsed_data and parsed_data['table_n_records']:
            parcel_result = self.load_parcels(
                parsed_data['table_n_records'],
                parcel_file.name,
                county_number,
                county_name,
                year
            )
            results['parcels'] = parcel_result
        
        # Load assessment records
        if 'table_d_records' in parsed_data and parsed_data['table_d_records']:
            assessment_result = self.load_assessments(
                parsed_data['table_d_records'],
                assessment_file.name if assessment_file else 'NAVD_file',
                county_number,
                county_name,
                year
            )
            results['assessments'] = assessment_result
        
        # Determine overall status
        if results['parcels'] and results['parcels']['status'] == 'success':
            if results['assessments'] and results['assessments']['status'] == 'success':
                results['status'] = 'success'
            elif results['assessments']:
                results['status'] = 'partial'
            else:
                results['status'] = 'parcels_only'
        elif results['assessments'] and results['assessments']['status'] == 'success':
            results['status'] = 'assessments_only'
        else:
            results['status'] = 'failed'
        
        # Log summary
        logger.info(f"NAV Roll load complete for {county_name}:")
        if results['parcels']:
            logger.info(f"  Parcels: {results['parcels']['loaded']:,} loaded")
        if results['assessments']:
            logger.info(f"  Assessments: {results['assessments']['loaded']:,} loaded")
        
        return results
    
    def _get_authority_name(self, code: Optional[str]) -> Optional[str]:
        """Get taxing authority name from code"""
        if not code:
            return None
        
        # Common authority codes (extend as needed)
        authorities = {
            'CO': 'County',
            'SC': 'School District',
            'CI': 'City',
            'SP': 'Special District',
            'WM': 'Water Management',
            'FI': 'Fire District',
            'LI': 'Library District',
            'HO': 'Hospital District'
        }
        
        return authorities.get(code[:2], f'Authority {code}')
    
    def _get_government_description(self, gov_type: Optional[str]) -> Optional[str]:
        """Get government type description"""
        if not gov_type:
            return None
        
        gov_types = {
            '01': 'County',
            '02': 'Municipality',
            '03': 'Independent Special District',
            '04': 'Dependent Special District',
            '05': 'School District',
            '06': 'Water Management District',
            '07': 'Regional Agency',
            '08': 'State Agency'
        }
        
        return gov_types.get(gov_type, f'Government Type {gov_type}')
    
    def _get_function_description(self, function_code: Optional[str]) -> Optional[str]:
        """Get function description from code"""
        if not function_code:
            return None
        
        functions = {
            '001': 'General Government',
            '002': 'Public Safety',
            '003': 'Physical Environment',
            '004': 'Transportation',
            '005': 'Economic Environment',
            '006': 'Human Services',
            '007': 'Culture/Recreation',
            '008': 'Debt Service',
            '009': 'Capital Projects',
            '010': 'Special Assessments'
        }
        
        return functions.get(function_code, f'Function {function_code}')
    
    def _determine_levy_type(self, function_code: Optional[str]) -> Optional[str]:
        """Determine levy type from function code"""
        if not function_code:
            return None
        
        # Map function codes to levy types
        if function_code in ['008']:
            return 'Debt Service'
        elif function_code in ['009']:
            return 'Capital'
        elif function_code in ['010']:
            return 'Special Assessment'
        else:
            return 'Operating'
    
    def get_statistics(self, county_number: Optional[str] = None, year: Optional[int] = None) -> Dict:
        """
        Get database statistics for NAV Roll data
        
        Args:
            county_number: Filter by county (optional)
            year: Filter by year (optional)
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'parcels': {
                'total_count': 0,
                'counties': [],
                'years': []
            },
            'assessments': {
                'total_count': 0,
                'total_tax_amount': 0,
                'function_breakdown': {}
            }
        }
        
        try:
            # Get parcel statistics
            url = f"{self.supabase_url}/rest/v1/{self.parcel_table}"
            params = {'select': 'count'}
            
            if county_number:
                params['county_number'] = f'eq.{county_number}'
            if year:
                params['assessment_year'] = f'eq.{year}'
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                # Parse count from response header
                count_header = response.headers.get('content-range', '0-0/0')
                total = int(count_header.split('/')[-1])
                stats['parcels']['total_count'] = total
            
            # Get assessment statistics
            url = f"{self.supabase_url}/rest/v1/{self.assessment_table}"
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                count_header = response.headers.get('content-range', '0-0/0')
                total = int(count_header.split('/')[-1])
                stats['assessments']['total_count'] = total
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
        
        return stats


if __name__ == "__main__":
    import argparse
    from nav_roll_parser import NAVRollParser
    
    parser = argparse.ArgumentParser(description='NAV Roll Database Loader')
    parser.add_argument('--parcel-file', help='Table N parcel file to load')
    parser.add_argument('--assessment-file', help='Table D assessment file to load')
    parser.add_argument('--county', default='06', help='County number')
    parser.add_argument('--county-name', default='Broward', help='County name')
    parser.add_argument('--year', type=int, default=2024, help='Assessment year')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = NAVRollDatabaseLoader()
    
    if args.create_tables:
        # Create tables
        loader.create_tables()
        print("Table creation SQL logged. Create tables via Supabase dashboard.")
        
    elif args.stats:
        # Show statistics
        stats = loader.get_statistics(args.county, args.year)
        print("\nNAV Roll Database Statistics:")
        print(f"  Parcels: {stats['parcels']['total_count']:,}")
        print(f"  Assessments: {stats['assessments']['total_count']:,}")
        
    elif args.parcel_file:
        # Parse and load file
        nav_parser = NAVRollParser()
        
        parcel_path = Path(args.parcel_file)
        assessment_path = Path(args.assessment_file) if args.assessment_file else None
        
        # Parse files
        parsed = nav_parser.parse_file(parcel_path, assessment_path)
        
        if parsed['success']:
            # Load to database
            result = loader.load_file(
                parcel_path,
                assessment_path,
                parsed,
                args.county,
                args.county_name,
                args.year
            )
            
            print(f"\nLoad complete: {result['status']}")
            if result['parcels']:
                print(f"  Parcels: {result['parcels']['loaded']:,} loaded")
            if result['assessments']:
                print(f"  Assessments: {result['assessments']['loaded']:,} loaded")
        else:
            print(f"Parse error: {parsed.get('error')}")
    
    else:
        print("Please specify --parcel-file to load or --stats to view statistics")