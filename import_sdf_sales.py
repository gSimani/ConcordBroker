#!/usr/bin/env python3
"""
SDF Sales Data Importer for Broward County
Imports sales data from CSV files into Supabase property_sales_history table
"""

import os
import csv
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sdf_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SDFImporter:
    def __init__(self):
        """Initialize the SDF importer with database connection"""
        self.load_environment()
        self.connection = None
        self.cursor = None
        
    def load_environment(self):
        """Load environment variables from .env file"""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Get database connection details
        self.database_url = os.getenv('POSTGRES_URL_NON_POOLING')
        if not self.database_url:
            # Fallback to individual components
            host = os.getenv('POSTGRES_HOST', 'db.pmispwtdngkcmsrsjwbp.supabase.co')
            database = os.getenv('POSTGRES_DATABASE', 'postgres')
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD')
            
            if password:
                # URL encode the password to handle special characters
                import urllib.parse
                encoded_password = urllib.parse.quote_plus(password)
                self.database_url = f"postgresql://{user}:{encoded_password}@{host}:5432/{database}?sslmode=require"
            else:
                raise ValueError("No database connection details found in environment")
    
    def connect_to_database(self):
        """Establish connection to PostgreSQL database"""
        try:
            logger.info("Connecting to database...")
            self.connection = psycopg2.connect(self.database_url)
            self.cursor = self.connection.cursor()
            logger.info("Database connection established")
            
            # Test connection
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()
            logger.info(f"PostgreSQL version: {version[0]}")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_schema(self, schema_file: Path):
        """Create the database schema from SQL file"""
        try:
            logger.info("Creating database schema...")
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            self.cursor.execute(schema_sql)
            self.connection.commit()
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            self.connection.rollback()
            raise
    
    def clear_existing_data(self):
        """Clear existing data from property_sales_history table"""
        try:
            logger.info("Clearing existing data...")
            
            # Get count before deletion
            self.cursor.execute("SELECT COUNT(*) FROM property_sales_history;")
            old_count = self.cursor.fetchone()[0]
            logger.info(f"Found {old_count:,} existing records")
            
            # Truncate table (faster than DELETE)
            self.cursor.execute("TRUNCATE TABLE property_sales_history RESTART IDENTITY;")
            self.connection.commit()
            logger.info("Existing data cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear existing data: {e}")
            self.connection.rollback()
            raise
    
    def clean_and_validate_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Clean and validate a single CSV row"""
        try:
            # Handle empty/null values
            def clean_value(value):
                if not value or value.strip() == '':
                    return None
                return value.strip().strip('"')
            
            def clean_integer(value):
                cleaned = clean_value(value)
                if cleaned is None:
                    return None
                try:
                    return int(cleaned)
                except (ValueError, TypeError):
                    return None
            
            def clean_price(value):
                cleaned = clean_value(value)
                if cleaned is None:
                    return None
                try:
                    # Remove any currency symbols and commas
                    cleaned = cleaned.replace('$', '').replace(',', '')
                    return int(float(cleaned))  # Convert to cents if needed
                except (ValueError, TypeError):
                    return None
            
            # Clean the row data
            cleaned_row = {
                'county_no': clean_value(row.get('CO_NO')),
                'parcel_id': clean_value(row.get('PARCEL_ID')),
                'state_parcel_id': clean_value(row.get('STATE_PARCEL_ID')),
                'assessment_year': clean_integer(row.get('ASMNT_YR')),
                'atv_start': clean_integer(row.get('ATV_STRT')),
                'group_no': clean_value(row.get('GRP_NO')),
                'dor_use_code': clean_value(row.get('DOR_UC')),
                'neighborhood_code': clean_value(row.get('NBRHD_CD')),
                'market_area': clean_value(row.get('MKT_AR')),
                'census_block': clean_value(row.get('CENSUS_BK')),
                'sale_id_code': clean_value(row.get('SALE_ID_CD')),
                'sale_change_code': clean_value(row.get('SAL_CHG_CD')),
                'verification_code': clean_value(row.get('VI_CD')),
                'or_book': clean_value(row.get('OR_BOOK')),
                'or_page': clean_value(row.get('OR_PAGE')),
                'clerk_no': clean_value(row.get('CLERK_NO')),
                'quality_code': clean_value(row.get('QUAL_CD')),
                'sale_year': clean_integer(row.get('SALE_YR')),
                'sale_month': clean_integer(row.get('SALE_MO')),
                'sale_price': clean_price(row.get('SALE_PRC')),
                'multi_parcel_sale': clean_value(row.get('MULTI_PAR_SAL')),
                'rs_id': clean_value(row.get('RS_ID')),
                'mp_id': clean_value(row.get('MP_ID'))
            }
            
            # Validate required fields
            if not cleaned_row['parcel_id']:
                return None
            
            if not cleaned_row['sale_year'] or not cleaned_row['sale_month']:
                return None
            
            # Validate sale date
            if cleaned_row['sale_year'] < 1900 or cleaned_row['sale_year'] > 2030:
                return None
                
            if cleaned_row['sale_month'] < 1 or cleaned_row['sale_month'] > 12:
                return None
            
            return cleaned_row
            
        except Exception as e:
            logger.warning(f"Error cleaning row: {e}")
            return None
    
    def import_csv_file(self, csv_file: Path, batch_size: int = 1000, test_mode: bool = False):
        """Import CSV file into database"""
        try:
            logger.info(f"Starting import of {csv_file}")
            
            # Read CSV file
            total_rows = 0
            valid_rows = 0
            error_rows = 0
            batch_data = []
            
            start_time = time.time()
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    total_rows += 1
                    
                    # Test mode: only process first 100 rows
                    if test_mode and total_rows > 100:
                        logger.info("Test mode: stopping after 100 rows")
                        break
                    
                    # Clean and validate row
                    cleaned_row = self.clean_and_validate_row(row)
                    
                    if cleaned_row:
                        batch_data.append(cleaned_row)
                        valid_rows += 1
                    else:
                        error_rows += 1
                    
                    # Process batch
                    if len(batch_data) >= batch_size:
                        self.insert_batch(batch_data)
                        batch_data = []
                        
                        # Progress update
                        if total_rows % (batch_size * 10) == 0:
                            elapsed = time.time() - start_time
                            rate = total_rows / elapsed if elapsed > 0 else 0
                            logger.info(f"Processed {total_rows:,} rows ({valid_rows:,} valid, {error_rows:,} errors) - {rate:.0f} rows/sec")
                
                # Process remaining batch
                if batch_data:
                    self.insert_batch(batch_data)
            
            # Final statistics
            elapsed = time.time() - start_time
            rate = total_rows / elapsed if elapsed > 0 else 0
            
            logger.info(f"Import completed in {elapsed:.1f} seconds")
            logger.info(f"Total rows processed: {total_rows:,}")
            logger.info(f"Valid rows imported: {valid_rows:,}")
            logger.info(f"Error rows skipped: {error_rows:,}")
            logger.info(f"Average rate: {rate:.0f} rows/sec")
            
            # Verify import
            self.cursor.execute("SELECT COUNT(*) FROM property_sales_history;")
            final_count = self.cursor.fetchone()[0]
            logger.info(f"Final database count: {final_count:,} records")
            
        except Exception as e:
            logger.error(f"Failed to import CSV file: {e}")
            raise
    
    def insert_batch(self, batch_data: List[Dict[str, Any]]):
        """Insert a batch of records into the database"""
        try:
            # Prepare the SQL statement
            insert_sql = """
                INSERT INTO property_sales_history (
                    county_no, parcel_id, state_parcel_id, assessment_year, atv_start,
                    group_no, dor_use_code, neighborhood_code, market_area, census_block,
                    sale_id_code, sale_change_code, verification_code, or_book, or_page,
                    clerk_no, quality_code, sale_year, sale_month, sale_price,
                    multi_parcel_sale, rs_id, mp_id
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """
            
            # Prepare values tuple
            values = [
                (
                    row['county_no'], row['parcel_id'], row['state_parcel_id'],
                    row['assessment_year'], row['atv_start'], row['group_no'],
                    row['dor_use_code'], row['neighborhood_code'], row['market_area'],
                    row['census_block'], row['sale_id_code'], row['sale_change_code'],
                    row['verification_code'], row['or_book'], row['or_page'],
                    row['clerk_no'], row['quality_code'], row['sale_year'],
                    row['sale_month'], row['sale_price'], row['multi_parcel_sale'],
                    row['rs_id'], row['mp_id']
                )
                for row in batch_data
            ]
            
            # Execute batch insert
            execute_values(self.cursor, insert_sql, values, page_size=1000)
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to insert batch: {e}")
            self.connection.rollback()
            raise
    
    def create_additional_indexes(self):
        """Create additional indexes after data import for better performance"""
        try:
            logger.info("Creating additional indexes...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sales_county_parcel ON property_sales_history(county_no, parcel_id);",
                "CREATE INDEX IF NOT EXISTS idx_sales_price_range ON property_sales_history(sale_price) WHERE sale_price > 0;",
                "CREATE INDEX IF NOT EXISTS idx_sales_recent ON property_sales_history(sale_date DESC) WHERE sale_date >= '2020-01-01';",
                "CREATE INDEX IF NOT EXISTS idx_sales_quality_valid ON property_sales_history(quality_code) WHERE quality_code IN ('01', '02', '03');",
            ]
            
            for index_sql in indexes:
                self.cursor.execute(index_sql)
                self.connection.commit()
            
            logger.info("Additional indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create additional indexes: {e}")
            self.connection.rollback()
            # Don't raise - indexes are optional
    
    def analyze_data(self):
        """Analyze the imported data and provide statistics"""
        try:
            logger.info("Analyzing imported data...")
            
            queries = [
                ("Total records", "SELECT COUNT(*) FROM property_sales_history"),
                ("Date range", "SELECT MIN(sale_date), MAX(sale_date) FROM property_sales_history WHERE sale_date IS NOT NULL"),
                ("Price range", "SELECT MIN(sale_price), MAX(sale_price) FROM property_sales_history WHERE sale_price > 0"),
                ("Unique parcels", "SELECT COUNT(DISTINCT parcel_id) FROM property_sales_history"),
                ("Quality codes", "SELECT quality_code, COUNT(*) FROM property_sales_history WHERE quality_code IS NOT NULL GROUP BY quality_code ORDER BY COUNT(*) DESC LIMIT 10"),
                ("Sales by year", "SELECT sale_year, COUNT(*) FROM property_sales_history GROUP BY sale_year ORDER BY sale_year DESC LIMIT 10")
            ]
            
            for description, query in queries:
                self.cursor.execute(query)
                result = self.cursor.fetchall()
                logger.info(f"{description}: {result}")
                
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
    
    def close_connection(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

def main():
    """Main execution function"""
    try:
        # File paths
        csv_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\SDF16P202501.csv")
        schema_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\create_sdf_sales_schema.sql")
        
        # Validate files exist
        if not csv_file.exists():
            logger.error(f"CSV file not found: {csv_file}")
            return False
            
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        # Check command line arguments
        test_mode = '--test' in sys.argv
        skip_schema = '--skip-schema' in sys.argv
        
        # Initialize importer
        importer = SDFImporter()
        importer.connect_to_database()
        
        try:
            # Create schema (unless skipped)
            if not skip_schema:
                importer.create_schema(schema_file)
                importer.clear_existing_data()
            
            # Import data
            importer.import_csv_file(csv_file, batch_size=1000, test_mode=test_mode)
            
            # Create additional indexes
            importer.create_additional_indexes()
            
            # Analyze results
            importer.analyze_data()
            
            logger.info("SDF import completed successfully!")
            return True
            
        finally:
            importer.close_connection()
    
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)