"""
Florida Revenue NAP Counties Database Loader
Loads parsed NAP (Non-Ad Valorem Parcel) data into Supabase database
"""

import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NAPDatabaseLoader:
    """Loads NAP data into Supabase database using REST API"""
    
    def __init__(self):
        """Initialize database connection"""
        # Load environment variables
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent.parent / "web" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try alternative path
            env_path = Path(__file__).parent.parent.parent / "web" / ".env.example"
            if env_path.exists():
                load_dotenv(env_path)
        
        # Get Supabase credentials
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
        
        # Setup headers for REST API
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Table name
        self.table_name = 'florida_nap_assessments'
        
        # Batch settings
        self.batch_size = 500
        self.max_retries = 3
        
        # Statistics
        self.stats = {
            'total_records': 0,
            'successful_inserts': 0,
            'failed_inserts': 0,
            'duplicate_skips': 0,
            'batch_count': 0
        }
    
    def ensure_table_exists(self) -> bool:
        """
        Check if the NAP table exists in database
        
        Returns:
            True if table exists
        """
        try:
            # Try to query the table
            url = f"{self.supabase_url}/rest/v1/{self.table_name}?limit=1"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                logger.info(f"Table '{self.table_name}' exists")
                return True
            elif response.status_code == 404:
                logger.warning(f"Table '{self.table_name}' does not exist")
                logger.info("Please create the table using the following SQL:")
                print(self.get_create_table_sql())
                return False
            else:
                logger.error(f"Error checking table: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking table: {e}")
            return False
    
    def get_create_table_sql(self) -> str:
        """Get SQL to create the NAP table"""
        return """
-- Florida NAP (Non-Ad Valorem Parcel) Assessments Table
CREATE TABLE IF NOT EXISTS florida_nap_assessments (
    id BIGSERIAL PRIMARY KEY,
    
    -- Key fields
    parcel_id VARCHAR(30) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    county_name VARCHAR(50),
    assessment_year INTEGER,
    
    -- Assessment information
    nap_code VARCHAR(10),
    nap_description VARCHAR(100),
    nap_amount DECIMAL(15, 2),
    
    -- Authority and district
    levying_authority VARCHAR(100),
    district_code VARCHAR(20),
    district_name VARCHAR(100),
    
    -- Assessment details
    assessment_type VARCHAR(20),
    rate_type VARCHAR(20),
    rate_amount DECIMAL(15, 4),
    unit_type VARCHAR(20),
    unit_count DECIMAL(10, 2),
    base_amount DECIMAL(15, 2),
    exempt_amount DECIMAL(15, 2),
    
    -- Payment information
    delinquent_flag CHAR(1),
    payment_status VARCHAR(20),
    due_date DATE,
    paid_date DATE,
    
    -- Lien information
    lien_flag CHAR(1),
    lien_date DATE,
    certificate_number VARCHAR(30),
    
    -- Bond information
    bond_flag CHAR(1),
    bond_amount DECIMAL(15, 2),
    special_benefit DECIMAL(15, 2),
    
    -- Special districts
    cdd_flag CHAR(1),
    cdd_name VARCHAR(100),
    hoa_flag CHAR(1),
    hoa_name VARCHAR(100),
    msbu_flag CHAR(1),
    msbu_name VARCHAR(100),
    
    -- Metadata
    data_source VARCHAR(20) DEFAULT 'NAP',
    record_status CHAR(1),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT unique_nap_parcel_county_year_code UNIQUE (parcel_id, county_code, assessment_year, nap_code)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_nap_parcel_id ON florida_nap_assessments(parcel_id);
CREATE INDEX IF NOT EXISTS idx_nap_county_code ON florida_nap_assessments(county_code);
CREATE INDEX IF NOT EXISTS idx_nap_district_code ON florida_nap_assessments(district_code);
CREATE INDEX IF NOT EXISTS idx_nap_assessment_year ON florida_nap_assessments(assessment_year);
CREATE INDEX IF NOT EXISTS idx_nap_delinquent ON florida_nap_assessments(delinquent_flag) WHERE delinquent_flag = 'Y';
CREATE INDEX IF NOT EXISTS idx_nap_lien ON florida_nap_assessments(lien_flag) WHERE lien_flag = 'Y';
CREATE INDEX IF NOT EXISTS idx_nap_amount ON florida_nap_assessments(nap_amount);

-- Enable Row Level Security
ALTER TABLE florida_nap_assessments ENABLE ROW LEVEL SECURITY;

-- Create policy for read access
CREATE POLICY "Enable read access for all users" ON florida_nap_assessments
    FOR SELECT USING (true);

-- Add comments
COMMENT ON TABLE florida_nap_assessments IS 'Florida Revenue NAP (Non-Ad Valorem Parcel) assessment data for all counties';
COMMENT ON COLUMN florida_nap_assessments.parcel_id IS 'Property parcel identification number';
COMMENT ON COLUMN florida_nap_assessments.nap_code IS 'Non-ad valorem assessment code';
COMMENT ON COLUMN florida_nap_assessments.nap_amount IS 'Assessment amount';
COMMENT ON COLUMN florida_nap_assessments.delinquent_flag IS 'Y if assessment is delinquent';
COMMENT ON COLUMN florida_nap_assessments.cdd_flag IS 'Y if property is in a Community Development District';
"""
    
    def prepare_record(self, parsed_record: Dict, county_code: str, county_name: str, year: int) -> Dict:
        """
        Prepare a parsed NAP record for database insertion
        
        Args:
            parsed_record: Parsed NAP record from parser
            county_code: Two-digit county code
            county_name: County name
            year: Assessment year
            
        Returns:
            Prepared record for database
        """
        # Map parsed fields to database columns
        db_record = {
            'parcel_id': parsed_record.get('PARCEL_ID', '').strip(),
            'county_code': county_code,
            'county_name': county_name,
            'assessment_year': year,
            
            # Assessment information
            'nap_code': parsed_record.get('NAP_CD', '').strip()[:10] or None,
            'nap_description': parsed_record.get('NAP_DESC', '').strip()[:100] or None,
            'nap_amount': self._parse_decimal(parsed_record.get('NAP_AMT')),
            
            # Authority and district
            'levying_authority': parsed_record.get('LEVYING_AUTH', '').strip()[:100] or None,
            'district_code': parsed_record.get('DISTRICT_CD', '').strip()[:20] or None,
            'district_name': parsed_record.get('DISTRICT_NAME', '').strip()[:100] or None,
            
            # Assessment details
            'assessment_type': parsed_record.get('ASSESSMENT_TYPE', '').strip()[:20] or None,
            'rate_type': parsed_record.get('RATE_TYPE', '').strip()[:20] or None,
            'rate_amount': self._parse_decimal(parsed_record.get('RATE_AMT')),
            'unit_type': parsed_record.get('UNIT_TYPE', '').strip()[:20] or None,
            'unit_count': self._parse_decimal(parsed_record.get('UNIT_COUNT')),
            'base_amount': self._parse_decimal(parsed_record.get('BASE_AMT')),
            'exempt_amount': self._parse_decimal(parsed_record.get('EXEMPT_AMT')),
            
            # Payment information
            'delinquent_flag': parsed_record.get('DELINQUENT_FLAG', '').strip()[:1] or None,
            'payment_status': parsed_record.get('PAYMENT_STATUS', '').strip()[:20] or None,
            'due_date': self._parse_date(parsed_record.get('DUE_DATE')),
            'paid_date': self._parse_date(parsed_record.get('PAID_DATE')),
            
            # Lien information
            'lien_flag': parsed_record.get('LIEN_FLAG', '').strip()[:1] or None,
            'lien_date': self._parse_date(parsed_record.get('LIEN_DATE')),
            'certificate_number': parsed_record.get('CERTIFICATE_NO', '').strip()[:30] or None,
            
            # Bond information
            'bond_flag': parsed_record.get('BOND_FLAG', '').strip()[:1] or None,
            'bond_amount': self._parse_decimal(parsed_record.get('BOND_AMT')),
            'special_benefit': self._parse_decimal(parsed_record.get('SPECIAL_BENEFIT')),
            
            # Special districts
            'cdd_flag': parsed_record.get('CDD_FLAG', '').strip()[:1] or None,
            'cdd_name': parsed_record.get('CDD_NAME', '').strip()[:100] or None,
            'hoa_flag': parsed_record.get('HOA_FLAG', '').strip()[:1] or None,
            'hoa_name': parsed_record.get('HOA_NAME', '').strip()[:100] or None,
            'msbu_flag': parsed_record.get('MSBU_FLAG', '').strip()[:1] or None,
            'msbu_name': parsed_record.get('MSBU_NAME', '').strip()[:100] or None,
            
            # Metadata
            'data_source': 'NAP',
            'record_status': parsed_record.get('RECORD_STATUS', '').strip()[:1] or None,
            'raw_data': json.dumps(parsed_record),
            'updated_at': datetime.now().isoformat()
        }
        
        # Remove None values to use database defaults
        db_record = {k: v for k, v in db_record.items() if v is not None}
        
        return db_record
    
    def _parse_decimal(self, value: Any) -> Optional[float]:
        """Parse a decimal value from string"""
        if not value:
            return None
        
        try:
            # Remove commas and dollar signs
            value = str(value).replace(',', '').replace('$', '').strip()
            
            if not value or value == '0':
                return None
            
            return float(value)
        except:
            return None
    
    def _parse_date(self, value: Any) -> Optional[str]:
        """Parse a date value to ISO format"""
        if not value:
            return None
        
        try:
            # Assuming YYYYMMDD format
            value = str(value).strip()
            if len(value) == 8:
                year = value[:4]
                month = value[4:6]
                day = value[6:8]
                return f"{year}-{month}-{day}"
            return None
        except:
            return None
    
    def load_batch(self, records: List[Dict], county_code: str, county_name: str, year: int) -> Dict:
        """
        Load a batch of NAP records to database
        
        Args:
            records: List of parsed NAP records
            county_code: County code
            county_name: County name
            year: Assessment year
            
        Returns:
            Load statistics
        """
        if not records:
            return {'loaded': 0, 'failed': 0}
        
        prepared_records = []
        
        for record in records:
            try:
                prepared = self.prepare_record(record, county_code, county_name, year)
                if prepared and prepared.get('parcel_id'):
                    prepared_records.append(prepared)
            except Exception as e:
                logger.debug(f"Error preparing record: {e}")
                continue
        
        if not prepared_records:
            return {'loaded': 0, 'failed': 0}
        
        # Attempt to insert batch
        for attempt in range(self.max_retries):
            try:
                # Use upsert to handle duplicates
                url = f"{self.supabase_url}/rest/v1/{self.table_name}"
                
                # Add upsert headers
                headers = self.headers.copy()
                headers['Prefer'] = 'resolution=merge-duplicates,return=minimal'
                
                response = requests.post(
                    url,
                    json=prepared_records,
                    headers=headers
                )
                
                if response.status_code in [200, 201, 204]:
                    loaded = len(prepared_records)
                    self.stats['successful_inserts'] += loaded
                    self.stats['batch_count'] += 1
                    
                    return {'loaded': loaded, 'failed': 0}
                else:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Failed to insert batch: {response.status_code} - {response.text}")
                        self.stats['failed_inserts'] += len(prepared_records)
                        return {'loaded': 0, 'failed': len(prepared_records)}
                    else:
                        time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to insert batch after {self.max_retries} attempts: {e}")
                    self.stats['failed_inserts'] += len(prepared_records)
                    return {'loaded': 0, 'failed': len(prepared_records)}
                else:
                    time.sleep(2 ** attempt)
        
        return {'loaded': 0, 'failed': len(prepared_records)}
    
    def load_file(self, file_path: Path, parsed_data: Dict, county_code: str, county_name: str, year: int) -> Dict:
        """
        Load a complete NAP file to database
        
        Args:
            file_path: Path to NAP file
            parsed_data: Parsed data from NAPParser
            county_code: County code
            county_name: County name
            year: Assessment year
            
        Returns:
            Load summary
        """
        logger.info(f"Loading NAP data for {county_name} ({county_code}) - Year {year}")
        
        # Ensure table exists
        if not self.ensure_table_exists():
            return {
                'status': 'error',
                'message': 'Table does not exist',
                'file': str(file_path)
            }
        
        records = parsed_data.get('records', [])
        total_records = len(records)
        
        if total_records == 0:
            logger.warning(f"No records to load from {file_path}")
            return {
                'status': 'no_data',
                'file': str(file_path),
                'records': 0
            }
        
        logger.info(f"Loading {total_records:,} records from {file_path.name}")
        
        # Reset statistics for this file
        file_stats = {
            'total_records': total_records,
            'loaded': 0,
            'failed': 0,
            'batches': 0
        }
        
        # Process in batches
        for i in range(0, total_records, self.batch_size):
            batch = records[i:i + self.batch_size]
            
            result = self.load_batch(batch, county_code, county_name, year)
            
            file_stats['loaded'] += result['loaded']
            file_stats['failed'] += result['failed']
            file_stats['batches'] += 1
            
            # Progress update
            if file_stats['batches'] % 10 == 0:
                progress = (i + len(batch)) / total_records * 100
                logger.info(f"  Progress: {progress:.1f}% - Loaded: {file_stats['loaded']:,}")
            
            # Rate limiting
            time.sleep(0.1)
        
        # Update global statistics
        self.stats['total_records'] += total_records
        
        # Log summary
        logger.info(f"Completed loading {county_name}:")
        logger.info(f"  Total records: {file_stats['total_records']:,}")
        logger.info(f"  Successfully loaded: {file_stats['loaded']:,}")
        logger.info(f"  Failed: {file_stats['failed']:,}")
        logger.info(f"  Batches: {file_stats['batches']}")
        
        return {
            'status': 'success',
            'file': str(file_path),
            'county_code': county_code,
            'county_name': county_name,
            'year': year,
            'total_records': file_stats['total_records'],
            'loaded': file_stats['loaded'],
            'failed': file_stats['failed'],
            'batches': file_stats['batches']
        }
    
    def get_statistics(self) -> Dict:
        """Get current load statistics"""
        return {
            'total_records_processed': self.stats['total_records'],
            'successful_inserts': self.stats['successful_inserts'],
            'failed_inserts': self.stats['failed_inserts'],
            'duplicate_skips': self.stats['duplicate_skips'],
            'batch_count': self.stats['batch_count'],
            'average_batch_size': (
                self.stats['successful_inserts'] / self.stats['batch_count']
                if self.stats['batch_count'] > 0 else 0
            )
        }
    
    def verify_load(self, county_code: str, year: int) -> Dict:
        """
        Verify data was loaded for a county
        
        Args:
            county_code: County code to verify
            year: Assessment year to verify
            
        Returns:
            Verification results
        """
        try:
            # Count records for this county/year
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {
                'county_code': f'eq.{county_code}',
                'assessment_year': f'eq.{year}',
                'select': 'parcel_id',
                'limit': '1',
                'head': 'true'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                # Get count from header
                content_range = response.headers.get('content-range', '')
                if content_range:
                    # Format: "0-0/total"
                    parts = content_range.split('/')
                    if len(parts) == 2:
                        count = int(parts[1])
                    else:
                        count = 0
                else:
                    count = 0
                
                # Get sample records
                params['limit'] = '5'
                params['select'] = 'parcel_id,nap_description,nap_amount,district_name'
                del params['head']
                
                response = requests.get(url, headers=self.headers, params=params)
                sample = response.json() if response.status_code == 200 else []
                
                return {
                    'verified': True,
                    'county_code': county_code,
                    'year': year,
                    'record_count': count,
                    'sample_records': sample
                }
            else:
                return {
                    'verified': False,
                    'error': f"Failed to verify: {response.status_code}"
                }
            
        except Exception as e:
            logger.error(f"Error verifying load: {e}")
            return {
                'verified': False,
                'error': str(e)
            }


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from nap_parser import NAPParser
    
    # Test with a sample file
    loader = NAPDatabaseLoader()
    
    # Check if table exists
    if loader.ensure_table_exists():
        print("Table exists, ready to load data")
        
        # Example: Load Broward County NAP file
        nap_file = Path("data/florida_nap_counties/raw/NAP06P2025.txt")
        
        if nap_file.exists():
            print(f"\nParsing {nap_file}...")
            parser = NAPParser()
            parsed = parser.parse_file(nap_file)
            
            if parsed['success']:
                print(f"Parsed {parsed['total_records']} records")
                
                # Load to database
                result = loader.load_file(
                    nap_file,
                    parsed,
                    county_code='06',
                    county_name='Broward',
                    year=2025
                )
                
                print(f"\nLoad result: {result['status']}")
                print(f"Records loaded: {result.get('loaded', 0):,}")
                
                # Verify
                verification = loader.verify_load('06', 2025)
                print(f"\nVerification: {verification}")
            else:
                print(f"Parse failed: {parsed.get('error')}")
        else:
            print(f"File not found: {nap_file}")
    else:
        print("\nTable does not exist. Please create it first in Supabase.")
        print("SQL provided above.")