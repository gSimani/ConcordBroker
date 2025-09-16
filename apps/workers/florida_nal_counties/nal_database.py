"""
Florida Revenue NAL Counties Database Loader
Loads parsed NAL data into Supabase database
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NALDatabaseLoader:
    """Loads NAL data into Supabase database"""
    
    def __init__(self):
        """Initialize database connection"""
        # Load environment variables
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
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Table name
        self.table_name = 'florida_nal_owners'
        
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
        Ensure the NAL table exists in database
        
        Returns:
            True if table exists or was created
        """
        try:
            # Check if table exists
            result = self.supabase.table(self.table_name).select('parcel_id').limit(1).execute()
            logger.info(f"Table '{self.table_name}' exists")
            return True
            
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                logger.warning(f"Table '{self.table_name}' does not exist")
                logger.info("Please create the table using the following SQL:")
                print(self.get_create_table_sql())
                return False
            else:
                logger.error(f"Error checking table: {e}")
                return False
    
    def get_create_table_sql(self) -> str:
        """Get SQL to create the NAL table"""
        return """
-- Florida NAL (Name Address Library) Owners Table
CREATE TABLE IF NOT EXISTS florida_nal_owners (
    id BIGSERIAL PRIMARY KEY,
    
    -- Key fields
    parcel_id VARCHAR(30) NOT NULL,
    county_code VARCHAR(2) NOT NULL,
    county_name VARCHAR(50),
    tax_year INTEGER,
    
    -- Owner information
    owner_name1 VARCHAR(100),
    owner_name2 VARCHAR(100),
    owner_name3 VARCHAR(100),
    owner_name4 VARCHAR(100),
    
    -- Mailing address
    mail_addr1 VARCHAR(100),
    mail_addr2 VARCHAR(100),
    mail_addr3 VARCHAR(100),
    mail_city VARCHAR(50),
    mail_state VARCHAR(2),
    mail_zip VARCHAR(10),
    mail_country VARCHAR(50),
    mail_unit_type VARCHAR(10),
    mail_unit_number VARCHAR(20),
    
    -- Physical address
    physical_addr1 VARCHAR(100),
    physical_addr2 VARCHAR(100),
    physical_city VARCHAR(50),
    physical_zip VARCHAR(10),
    
    -- Property details
    property_use_code VARCHAR(10),
    site_addr_number VARCHAR(20),
    site_addr_street VARCHAR(100),
    site_addr_unit VARCHAR(20),
    site_city VARCHAR(50),
    site_zip VARCHAR(10),
    
    -- Assessment values
    assessed_value DECIMAL(15, 2),
    taxable_value DECIMAL(15, 2),
    just_value DECIMAL(15, 2),
    
    -- Exemptions
    homestead_exemption DECIMAL(15, 2),
    exemption_codes TEXT,
    
    -- Additional fields
    confidence_flag VARCHAR(1),
    tax_district VARCHAR(10),
    millage_code VARCHAR(10),
    school_district VARCHAR(10),
    
    -- Metadata
    data_source VARCHAR(20) DEFAULT 'NAL',
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT unique_nal_parcel_county_year UNIQUE (parcel_id, county_code, tax_year)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_nal_parcel_id ON florida_nal_owners(parcel_id);
CREATE INDEX IF NOT EXISTS idx_nal_county_code ON florida_nal_owners(county_code);
CREATE INDEX IF NOT EXISTS idx_nal_owner_name ON florida_nal_owners(owner_name1);
CREATE INDEX IF NOT EXISTS idx_nal_mail_zip ON florida_nal_owners(mail_zip);
CREATE INDEX IF NOT EXISTS idx_nal_site_zip ON florida_nal_owners(site_zip);
CREATE INDEX IF NOT EXISTS idx_nal_tax_year ON florida_nal_owners(tax_year);

-- Enable Row Level Security
ALTER TABLE florida_nal_owners ENABLE ROW LEVEL SECURITY;

-- Create policy for read access
CREATE POLICY "Enable read access for all users" ON florida_nal_owners
    FOR SELECT USING (true);

-- Add comments
COMMENT ON TABLE florida_nal_owners IS 'Florida Revenue NAL (Name Address Library) data for all counties';
COMMENT ON COLUMN florida_nal_owners.parcel_id IS 'Property parcel identification number';
COMMENT ON COLUMN florida_nal_owners.county_code IS 'Two-digit Florida county code';
COMMENT ON COLUMN florida_nal_owners.owner_name1 IS 'Primary owner name';
COMMENT ON COLUMN florida_nal_owners.mail_addr1 IS 'Primary mailing address line';
COMMENT ON COLUMN florida_nal_owners.assessed_value IS 'Property assessed value';
COMMENT ON COLUMN florida_nal_owners.homestead_exemption IS 'Homestead exemption amount';
"""
    
    def prepare_record(self, parsed_record: Dict, county_code: str, county_name: str, year: int) -> Dict:
        """
        Prepare a parsed NAL record for database insertion
        
        Args:
            parsed_record: Parsed NAL record from parser
            county_code: Two-digit county code
            county_name: County name
            year: Tax year
            
        Returns:
            Prepared record for database
        """
        # Map parsed fields to database columns
        db_record = {
            'parcel_id': parsed_record.get('PARCEL_ID', '').strip(),
            'county_code': county_code,
            'county_name': county_name,
            'tax_year': year,
            
            # Owner names
            'owner_name1': parsed_record.get('OWNER_NAME1', '').strip()[:100] or None,
            'owner_name2': parsed_record.get('OWNER_NAME2', '').strip()[:100] or None,
            'owner_name3': parsed_record.get('OWNER_NAME3', '').strip()[:100] or None,
            'owner_name4': parsed_record.get('OWNER_NAME4', '').strip()[:100] or None,
            
            # Mailing address
            'mail_addr1': parsed_record.get('MAIL_ADDR1', '').strip()[:100] or None,
            'mail_addr2': parsed_record.get('MAIL_ADDR2', '').strip()[:100] or None,
            'mail_addr3': parsed_record.get('MAIL_ADDR3', '').strip()[:100] or None,
            'mail_city': parsed_record.get('MAIL_CITY', '').strip()[:50] or None,
            'mail_state': parsed_record.get('MAIL_STATE', '').strip()[:2] or None,
            'mail_zip': parsed_record.get('MAIL_ZIPCODE', '').strip()[:10] or None,
            'mail_country': parsed_record.get('MAIL_COUNTRY', '').strip()[:50] or None,
            'mail_unit_type': parsed_record.get('MAIL_UNIT_TYPE', '').strip()[:10] or None,
            'mail_unit_number': parsed_record.get('MAIL_UNIT_NUMBER', '').strip()[:20] or None,
            
            # Physical address
            'physical_addr1': parsed_record.get('PHYSICAL_ADDR1', '').strip()[:100] or None,
            'physical_addr2': parsed_record.get('PHYSICAL_ADDR2', '').strip()[:100] or None,
            'physical_city': parsed_record.get('PHYSICAL_CITY', '').strip()[:50] or None,
            'physical_zip': parsed_record.get('PHYSICAL_ZIPCODE', '').strip()[:10] or None,
            
            # Property details
            'property_use_code': parsed_record.get('PROPERTY_USE', '').strip()[:10] or None,
            'site_addr_number': parsed_record.get('SITE_ADDR_NUMBER', '').strip()[:20] or None,
            'site_addr_street': parsed_record.get('SITE_ADDR_STREET', '').strip()[:100] or None,
            'site_addr_unit': parsed_record.get('SITE_ADDR_UNIT', '').strip()[:20] or None,
            'site_city': parsed_record.get('SITE_CITY', '').strip()[:50] or None,
            'site_zip': parsed_record.get('SITE_ZIPCODE', '').strip()[:10] or None,
            
            # Assessment values
            'assessed_value': self._parse_decimal(parsed_record.get('ASSESSED_VALUE')),
            'taxable_value': self._parse_decimal(parsed_record.get('TAXABLE_VALUE')),
            'just_value': self._parse_decimal(parsed_record.get('JUST_VALUE')),
            
            # Exemptions
            'homestead_exemption': self._parse_decimal(parsed_record.get('HOMESTEAD_EXEMPTION')),
            'exemption_codes': parsed_record.get('EXEMPTION_CODES', '').strip() or None,
            
            # Additional fields
            'confidence_flag': parsed_record.get('CONFIDENCE_FLAG', '').strip()[:1] or None,
            'tax_district': parsed_record.get('TAX_DISTRICT', '').strip()[:10] or None,
            'millage_code': parsed_record.get('MILLAGE_CODE', '').strip()[:10] or None,
            'school_district': parsed_record.get('SCHOOL_DISTRICT', '').strip()[:10] or None,
            
            # Metadata
            'data_source': 'NAL',
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
    
    def load_batch(self, records: List[Dict], county_code: str, county_name: str, year: int) -> Dict:
        """
        Load a batch of NAL records to database
        
        Args:
            records: List of parsed NAL records
            county_code: County code
            county_name: County name
            year: Tax year
            
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
                result = self.supabase.table(self.table_name).upsert(
                    prepared_records,
                    on_conflict='parcel_id,county_code,tax_year'
                ).execute()
                
                loaded = len(prepared_records)
                self.stats['successful_inserts'] += loaded
                self.stats['batch_count'] += 1
                
                return {'loaded': loaded, 'failed': 0}
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to insert batch after {self.max_retries} attempts: {e}")
                    self.stats['failed_inserts'] += len(prepared_records)
                    return {'loaded': 0, 'failed': len(prepared_records)}
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
    
    def load_file(self, file_path: Path, parsed_data: Dict, county_code: str, county_name: str, year: int) -> Dict:
        """
        Load a complete NAL file to database
        
        Args:
            file_path: Path to NAL file
            parsed_data: Parsed data from NALParser
            county_code: County code
            county_name: County name
            year: Tax year
            
        Returns:
            Load summary
        """
        logger.info(f"Loading NAL data for {county_name} ({county_code}) - Year {year}")
        
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
            year: Tax year to verify
            
        Returns:
            Verification results
        """
        try:
            # Count records for this county/year
            result = self.supabase.table(self.table_name).select(
                'parcel_id',
                count='exact'
            ).eq('county_code', county_code).eq('tax_year', year).execute()
            
            count = result.count if hasattr(result, 'count') else len(result.data)
            
            # Get sample records
            sample = self.supabase.table(self.table_name).select(
                'parcel_id,owner_name1,mail_city,assessed_value'
            ).eq('county_code', county_code).eq('tax_year', year).limit(5).execute()
            
            return {
                'verified': True,
                'county_code': county_code,
                'year': year,
                'record_count': count,
                'sample_records': sample.data if sample.data else []
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
    
    from nal_parser import NALParser
    
    # Test with a sample file
    loader = NALDatabaseLoader()
    
    # Check if table exists
    if loader.ensure_table_exists():
        print("Table exists, ready to load data")
        
        # Example: Load Broward County NAL file
        nal_file = Path("data/florida_nal_counties/raw/NAL06P2025.txt")
        
        if nal_file.exists():
            print(f"\nParsing {nal_file}...")
            parser = NALParser()
            parsed = parser.parse_file(nal_file)
            
            if parsed['success']:
                print(f"Parsed {parsed['total_records']} records")
                
                # Load to database
                result = loader.load_file(
                    nal_file,
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
            print(f"File not found: {nal_file}")
    else:
        print("\nTable does not exist. Please create it first in Supabase.")
        print("SQL provided above.")