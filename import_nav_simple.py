#!/usr/bin/env python3
"""
Simple NAV Assessments Import
============================

Imports NAP (Name and Property) data into existing nav_assessments table.
Maps CSV columns to the existing simple schema.
"""

import os
import sys
import logging
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleNavImporter:
    def __init__(self):
        """Initialize the importer with database connection."""
        load_dotenv('apps/web/.env')
        
        # Try service role key first (for admin operations), fallback to anon key
        self.supabase_url = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Check apps/web/.env file.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # File paths
        self.nap_file = 'TEMP/NAP16P202501.csv'
        
        # Batch processing settings
        self.batch_size = 1000
        self.max_retries = 3
        
        # Statistics
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def safe_float(self, value):
        """Safely convert value to float."""
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def safe_int(self, value):
        """Safely convert value to int."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def transform_record(self, row):
        """Transform CSV row to match existing table schema."""
        
        # Extract key values from CSV
        jv_total = self.safe_float(row.get('JV_TOTAL', 0))
        av_total = self.safe_float(row.get('AV_TOTAL', 0))
        tax_val = self.safe_float(row.get('TAX_VAL', 0))
        
        # Map to existing schema
        record = {
            'parcel_id': str(row.get('ACCT_ID', '')).strip(),
            'tax_year': self.safe_int(row.get('ASMNT_YR')),
            'just_value': jv_total,
            'assessed_value': av_total,
            'taxable_value': tax_val,
            'land_value': 0.0,  # Not available in NAP data
            'building_value': 0.0,  # Not available in NAP data
            'created_at': datetime.now().isoformat()
        }
        
        return record
    
    def process_file(self):
        """Process the NAP file in batches."""
        logger.info(f"Starting NAP file processing: {self.nap_file}")
        
        if not os.path.exists(self.nap_file):
            logger.error(f"NAP file not found: {self.nap_file}")
            return False
        
        batch_num = 0
        
        try:
            # Read CSV in chunks for memory efficiency
            for chunk in pd.read_csv(self.nap_file, chunksize=self.batch_size, dtype=str):
                batch_num += 1
                logger.info(f"Processing batch {batch_num} ({len(chunk)} records)")
                
                # Transform records
                batch_records = []
                for _, row in chunk.iterrows():
                    try:
                        transformed = self.transform_record(row.to_dict())
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
                        logger.info(f"Batch {batch_num} completed: {len(batch_records)} records inserted")
                    else:
                        logger.error(f"Batch {batch_num} failed")
                
                # Progress report every 10 batches
                if batch_num % 10 == 0:
                    logger.info(f"Progress: {self.stats['processed']} records processed")
            
        except Exception as e:
            logger.error(f"Error processing NAP file: {e}")
            return False
        
        return True
    
    def insert_batch(self, records):
        """Insert a batch of records."""
        for attempt in range(self.max_retries):
            try:
                # Use simple insert
                result = self.supabase.table('nav_assessments').insert(records).execute()
                
                if result.data:
                    self.stats['inserted'] += len(records)
                    return True
                else:
                    logger.warning(f"Insert returned no data (attempt {attempt + 1})")
                
            except Exception as e:
                logger.error(f"Error inserting batch (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats['errors'] += len(records)
                    return False
        
        return False
    
    def run_import(self):
        """Run the complete import process."""
        logger.info("Starting Simple NAV Assessments Import")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Process NAP file
            success = self.process_file()
            
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
    logger.info("Simple NAV Assessments Import Script")
    logger.info("=" * 50)
    
    try:
        importer = SimpleNavImporter()
        success = importer.run_import()
        
        return 0 if success else 1
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())