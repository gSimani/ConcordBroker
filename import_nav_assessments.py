#!/usr/bin/env python3
"""
Import NAV Assessments Data
===========================

Imports NAP (Name and Property) data into nav_assessments table.
This provides property tax assessment details for properties.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nav_assessments_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NavAssessmentsImporter:
    def __init__(self):
        """Initialize the importer with database connection."""
        load_dotenv('apps/web/.env')
        
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Check apps/web/.env file.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # File paths
        self.nap_file = 'TEMP/NAP16P202501.csv'
        
        # Batch processing settings
        self.batch_size = 500
        self.max_retries = 3
        
        # Statistics
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return None
                # Remove any non-numeric characters except minus sign
                value = ''.join(c for c in value if c.isdigit() or c == '-')
                if value == '' or value == '-':
                    return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def safe_str(self, value: Any) -> Optional[str]:
        """Safely convert value to string."""
        if pd.isna(value) or value is None:
            return None
        value = str(value).strip()
        return value if value != '' else None
    
    def transform_nap_record(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a NAP CSV row into nav_assessments table format."""
        
        # Calculate total assessment
        jv_total = self.safe_float(row.get('JV_TOTAL')) or 0
        av_total = self.safe_float(row.get('AV_TOTAL')) or 0
        
        transformed = {
            'parcel_id': self.safe_str(row.get('ACCT_ID')),
            'assessment_year': self.safe_int(row.get('ASMNT_YR')),
            'tax_authority_code': self.safe_str(row.get('TAX_AUTH_CD')),
            'naics_code': self.safe_str(row.get('NAICS_CD')),
            
            # Assessment values
            'just_value_ffe': self.safe_float(row.get('JV_F_F_E')),
            'just_value_leasehold': self.safe_float(row.get('JV_LESE_IMP')),
            'just_value_total': jv_total,
            'assessed_value_total': av_total,
            'just_value_pollution_control': self.safe_float(row.get('JV_POL_CONTRL')),
            'assessed_value_pollution_control': self.safe_float(row.get('AV_POL_CONTRL')),
            
            # Tax information
            'exemption_value': self.safe_float(row.get('EXMPT_VAL')),
            'taxable_value': self.safe_float(row.get('TAX_VAL')),
            'penalty_rate': self.safe_float(row.get('PEN_RATE')),
            
            # Property details
            'property_address': self.safe_str(row.get('PHY_ADDR')),
            'property_city': self.safe_str(row.get('PHY_CITY')),
            'property_zipcode': self.safe_str(row.get('PHY_ZIPCD')),
            
            # Owner information
            'owner_name': self.safe_str(row.get('OWN_NAM')),
            'owner_address': self.safe_str(row.get('OWN_ADDR')),
            'owner_city': self.safe_str(row.get('OWN_CITY')),
            'owner_state': self.safe_str(row.get('OWN_STATE')),
            'owner_zipcode': self.safe_str(row.get('OWN_ZIPCD')),
            'owner_state_domicile': self.safe_str(row.get('OWN_STATE_DOM')),
            
            # Fiduciary information
            'fiduciary_name': self.safe_str(row.get('FIDU_NAME')),
            'fiduciary_address': self.safe_str(row.get('FIDU_ADDR')),
            'fiduciary_city': self.safe_str(row.get('FIDU_CITY')),
            'fiduciary_state': self.safe_str(row.get('FIDU_STATE')),
            'fiduciary_zipcode': self.safe_str(row.get('FIDU_ZIPCD')),
            'fiduciary_code': self.safe_str(row.get('FIDU_CD')),
            
            # Additional fields
            'file_indicator': self.safe_str(row.get('FIL')),
            'alternate_key': self.safe_str(row.get('ALT_KEY')),
            'exemptions': self.safe_str(row.get('EXMPT')),
            'account_id_change': self.safe_str(row.get('ACCT_ID_CNG')),
            'sequence_number': self.safe_int(row.get('SEQ_NO')),
            'ts_id': self.safe_str(row.get('TS_ID')),
            
            # Calculated fields for frontend
            'total_assessment': jv_total + av_total,
            'assessment_type': 'Personal Property' if self.safe_str(row.get('FILE_T')) == 'P' else 'Real Property',
            
            # Metadata
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return transformed
    
    def create_nav_assessments_table(self):
        """Create the nav_assessments table if it doesn't exist."""
        logger.info("Checking nav_assessments table...")
        
        try:
            # Check if table exists
            result = self.supabase.table('nav_assessments').select("count", count="exact").limit(1).execute()
            logger.info("Table 'nav_assessments' already exists")
            return True
        except Exception as e:
            logger.info("Table 'nav_assessments' does not exist, need to create it manually")
            logger.info("Please create the nav_assessments table in Supabase SQL editor with this schema:")
            
            schema = '''
            CREATE TABLE nav_assessments (
                id BIGSERIAL PRIMARY KEY,
                parcel_id TEXT NOT NULL,
                assessment_year INTEGER,
                tax_authority_code TEXT,
                naics_code TEXT,
                
                -- Assessment values
                just_value_ffe DECIMAL(15,2),
                just_value_leasehold DECIMAL(15,2),
                just_value_total DECIMAL(15,2),
                assessed_value_total DECIMAL(15,2),
                just_value_pollution_control DECIMAL(15,2),
                assessed_value_pollution_control DECIMAL(15,2),
                
                -- Tax information
                exemption_value DECIMAL(15,2),
                taxable_value DECIMAL(15,2),
                penalty_rate DECIMAL(5,3),
                
                -- Property details
                property_address TEXT,
                property_city TEXT,
                property_zipcode TEXT,
                
                -- Owner information
                owner_name TEXT,
                owner_address TEXT,
                owner_city TEXT,
                owner_state TEXT,
                owner_zipcode TEXT,
                owner_state_domicile TEXT,
                
                -- Fiduciary information
                fiduciary_name TEXT,
                fiduciary_address TEXT,
                fiduciary_city TEXT,
                fiduciary_state TEXT,
                fiduciary_zipcode TEXT,
                fiduciary_code TEXT,
                
                -- Additional fields
                file_indicator TEXT,
                alternate_key TEXT,
                exemptions TEXT,
                account_id_change TEXT,
                sequence_number INTEGER,
                ts_id TEXT,
                
                -- Calculated fields
                total_assessment DECIMAL(15,2),
                assessment_type TEXT,
                
                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Constraints and indexes
                UNIQUE(parcel_id, assessment_year, tax_authority_code)
            );
            
            CREATE INDEX idx_nav_assessments_parcel_id ON nav_assessments(parcel_id);
            CREATE INDEX idx_nav_assessments_assessment_year ON nav_assessments(assessment_year);
            CREATE INDEX idx_nav_assessments_total_assessment ON nav_assessments(total_assessment);
            
            ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Allow all operations on nav_assessments" ON nav_assessments
                FOR ALL USING (true) WITH CHECK (true);
            '''
            print(schema)
            return False
    
    def process_nap_file(self):
        """Process the NAP file in batches."""
        logger.info(f"Starting NAP file processing: {self.nap_file}")
        
        if not os.path.exists(self.nap_file):
            logger.error(f"NAP file not found: {self.nap_file}")
            return False
        
        batch_num = 0
        
        try:
            # Use pandas for efficient CSV reading
            chunk_size = self.batch_size
            
            for chunk in pd.read_csv(self.nap_file, chunksize=chunk_size, dtype=str):
                batch_num += 1
                logger.info(f"Processing batch {batch_num} ({len(chunk)} records)")
                
                # Transform records
                batch_records = []
                for _, row in chunk.iterrows():
                    try:
                        transformed = self.transform_nap_record(row.to_dict())
                        if transformed['parcel_id']:  # Only include records with valid parcel_id
                            batch_records.append(transformed)
                    except Exception as e:
                        logger.error(f"Error transforming record: {e}")
                        self.stats['errors'] += 1
                
                # Insert batch
                if batch_records:
                    success = self.insert_batch(batch_records)
                    if success:
                        self.stats['processed'] += len(batch_records)
                        logger.info(f"Batch {batch_num} completed: {len(batch_records)} records")
                    else:
                        logger.error(f"Batch {batch_num} failed")
                
                # Progress report every 10 batches
                if batch_num % 10 == 0:
                    logger.info(f"Progress: {self.stats['processed']} records processed")
            
        except Exception as e:
            logger.error(f"Error processing NAP file: {e}")
            return False
        
        return True
    
    def insert_batch(self, records: List[Dict[str, Any]]) -> bool:
        """Insert a batch of records using UPSERT."""
        for attempt in range(self.max_retries):
            try:
                # Use upsert to handle duplicates
                result = self.supabase.table('nav_assessments').upsert(
                    records,
                    on_conflict='parcel_id,assessment_year,tax_authority_code'
                ).execute()
                
                if result.data:
                    self.stats['inserted'] += len(records)
                    return True
                else:
                    logger.warning(f"Upsert returned no data (attempt {attempt + 1})")
                
            except Exception as e:
                logger.error(f"Error inserting batch (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats['errors'] += len(records)
                    return False
        
        return False
    
    def run_import(self):
        """Run the complete import process."""
        logger.info("Starting NAV Assessments Import")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Check/create table
            table_ready = self.create_nav_assessments_table()
            if not table_ready:
                logger.error("Please create the nav_assessments table first")
                return False
            
            # Process NAP file
            success = self.process_nap_file()
            
            if success:
                logger.info("Import completed successfully!")
            else:
                logger.error("Import failed!")
            
        except Exception as e:
            logger.error(f"Import failed with error: {e}")
            success = False
        
        finally:
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            logger.info("Import Statistics:")
            logger.info(f"  Duration: {duration}")
            logger.info(f"  Records Processed: {self.stats['processed']}")
            logger.info(f"  Records Inserted: {self.stats['inserted']}")
            logger.info(f"  Errors: {self.stats['errors']}")
        
        return success

def main():
    """Main entry point."""
    logger.info("NAV Assessments Import Script")
    logger.info("=" * 50)
    
    try:
        importer = NavAssessmentsImporter()
        success = importer.run_import()
        
        return 0 if success else 1
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())