#!/usr/bin/env python3
"""
Direct SQL Loader for Property Appraiser Data
Bypasses REST API and loads directly via PostgreSQL
"""

import os
import csv
import json
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectPropertyLoader:
    """Direct PostgreSQL loader for Property Appraiser data"""
    
    def __init__(self):
        # Set correct credentials
        os.environ['DATABASE_URL'] = 'postgres://postgres.pmispwtdngkcmsrsjwbp:West@Boca613!@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres?sslmode=require'
        
        # Connect to database
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.cur = self.conn.cursor()
        logger.info("✅ Connected to database directly")
        
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.batch_size = 1000
        self.stats = {
            'total_records': 0,
            'counties_processed': set()
        }
    
    def load_nal_file(self, filepath: Path, county_code: str, county_name: str):
        """Load NAL (property assessments) file"""
        logger.info(f"Loading NAL file: {filepath.name}")
        
        records = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean and prepare data
                record = (
                    row.get('PARCEL_ID', '').strip(),
                    county_code,
                    county_name,
                    row.get('OWNER_NAME', '').strip()[:255],
                    row.get('OWNER_ADDRESS', '').strip()[:255],
                    row.get('OWNER_CITY', '').strip()[:100],
                    row.get('OWNER_STATE', 'FL')[:2],
                    row.get('OWNER_ZIP', '').strip()[:10],
                    row.get('PROPERTY_ADDRESS', '').strip()[:255],
                    row.get('PROPERTY_CITY', '').strip()[:100],
                    row.get('PROPERTY_ZIP', '').strip()[:10],
                    row.get('PROPERTY_USE_CODE', '').strip()[:20],
                    row.get('TAX_DISTRICT', '').strip()[:50],
                    row.get('SUBDIVISION', '').strip()[:100],
                    self.safe_float(row.get('JUST_VALUE', 0)),
                    self.safe_float(row.get('ASSESSED_VALUE', 0)),
                    self.safe_float(row.get('TAXABLE_VALUE', 0)),
                    self.safe_float(row.get('LAND_VALUE', 0)),
                    self.safe_float(row.get('BUILDING_VALUE', 0)),
                    self.safe_int(row.get('TOTAL_SQ_FT', 0)),
                    self.safe_int(row.get('LIVING_AREA', 0)),
                    self.safe_int(row.get('YEAR_BUILT', 0)),
                    self.safe_int(row.get('BEDROOMS', 0)),
                    self.safe_float(row.get('BATHROOMS', 0)),
                    row.get('POOL', '').upper() == 'Y',
                    2025  # tax_year
                )
                records.append(record)
                
                if len(records) >= self.batch_size:
                    self.insert_batch('property_assessments', records)
                    records = []
        
        # Insert remaining records
        if records:
            self.insert_batch('property_assessments', records)
    
    def insert_batch(self, table: str, records: list):
        """Insert batch of records using COPY-like performance"""
        if not records:
            return
        
        if table == 'property_assessments':
            query = """
                INSERT INTO property_assessments (
                    parcel_id, county_code, county_name, owner_name, owner_address,
                    owner_city, owner_state, owner_zip, property_address, property_city,
                    property_zip, property_use_code, tax_district, subdivision,
                    just_value, assessed_value, taxable_value, land_value, building_value,
                    total_sq_ft, living_area, year_built, bedrooms, bathrooms, pool, tax_year
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (parcel_id, county_code, tax_year) DO UPDATE SET
                    owner_name = EXCLUDED.owner_name,
                    taxable_value = EXCLUDED.taxable_value,
                    updated_at = NOW()
            """
        
        try:
            execute_batch(self.cur, query, records, page_size=self.batch_size)
            self.conn.commit()
            self.stats['total_records'] += len(records)
            logger.info(f"  ✅ Inserted {len(records)} records (Total: {self.stats['total_records']:,})")
        except Exception as e:
            logger.error(f"  ❌ Error inserting batch: {e}")
            self.conn.rollback()
    
    def safe_float(self, value):
        """Safely convert to float"""
        try:
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def safe_int(self, value):
        """Safely convert to int"""
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def process_all_counties(self):
        """Process all county files"""
        logger.info("="*70)
        logger.info("STARTING DIRECT SQL PROPERTY DATA LOAD")
        logger.info("="*70)
        
        # County mapping
        counties = {
            "11": "ALACHUA", "12": "BAKER", "13": "BAY", "14": "BRADFORD",
            "15": "BREVARD", "16": "BROWARD", "17": "CALHOUN", "18": "CHARLOTTE",
            # ... add more as needed
        }
        
        # Process first few counties as test
        for county_code, county_name in list(counties.items())[:3]:  # Test with 3 counties
            logger.info(f"\nProcessing {county_name} (Code: {county_code})")
            
            # Find NAL file
            nal_pattern = f"NAL{county_code}P*.csv"
            nal_files = list(self.data_path.glob(nal_pattern))
            
            if nal_files:
                self.load_nal_file(nal_files[0], county_code, county_name)
                self.stats['counties_processed'].add(county_name)
            else:
                logger.warning(f"  No NAL file found for {county_name}")
        
        # Final statistics
        logger.info("\n" + "="*70)
        logger.info("LOAD COMPLETE")
        logger.info(f"Total Records: {self.stats['total_records']:,}")
        logger.info(f"Counties Processed: {len(self.stats['counties_processed'])}")
        logger.info("="*70)
        
        # Close connection
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    loader = DirectPropertyLoader()
    loader.process_all_counties()