"""
FLORIDA SUNBIZ DAILY UPDATER - Direct SFTP to Supabase
======================================================
Automatically downloads and processes daily updates from Florida DOS
directly into Supabase without local storage.

Based on lessons learned from the successful bulk upload:
- Proper deduplication to avoid duplicate key errors
- Efficient COPY command for bulk inserts
- Direct streaming from SFTP to database
"""

import os
import io
import logging
import psycopg2
import paramiko
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse
from io import StringIO
import schedule
import time
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DAILY-UPDATER] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaDailyUpdater:
    """Direct SFTP-to-Supabase daily updater for Florida business data"""
    
    def __init__(self):
        # SFTP Configuration
        self.sftp_host = 'sftp.floridados.gov'
        self.sftp_port = 22
        self.sftp_user = 'Public'
        self.sftp_pass = 'PubAccess1845!'
        
        # Supabase Configuration
        self.db_url = os.getenv('SUPABASE_DB_URL', 
            "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require")
        
        # File type identifiers
        self.file_types = {
            'c': 'corporate_filings',
            'ce': 'corporate_events',
            'f': 'fictitious_names',
            'fe': 'fictitious_events',
            'gp': 'general_partnerships',
            'gpe': 'general_partnership_events',
            'lien': 'federal_tax_liens',
            'mk': 'mark_filings'
        }
        
        # Track processed files
        self.processed_files_table = 'florida_daily_processed_files'
        self.ensure_tracking_table()
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'errors': 0,
            'start_time': None
        }
    
    def ensure_tracking_table(self):
        """Create table to track processed daily files"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS florida_daily_processed_files (
                        id SERIAL PRIMARY KEY,
                        file_name VARCHAR(255) UNIQUE NOT NULL,
                        file_type VARCHAR(50),
                        file_date DATE,
                        records_processed INTEGER DEFAULT 0,
                        entities_created INTEGER DEFAULT 0,
                        entities_updated INTEGER DEFAULT 0,
                        processing_time_seconds FLOAT,
                        processed_at TIMESTAMP DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'completed',
                        error_message TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_processed_files_date 
                    ON florida_daily_processed_files(file_date DESC);
                """)
                conn.commit()
                logger.info("Tracking table ensured")
        except Exception as e:
            logger.error(f"Error creating tracking table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_db_connection(self):
        """Get Supabase database connection"""
        parsed = urlparse(self.db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require',
            connect_timeout=30,
            options='-c statement_timeout=300000'  # 5 minute timeout
        )
        return conn
    
    def get_sftp_connection(self):
        """Establish SFTP connection to Florida DOS"""
        try:
            transport = paramiko.Transport((self.sftp_host, self.sftp_port))
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)
            logger.info(f"Connected to SFTP server: {self.sftp_host}")
            return sftp, transport
        except Exception as e:
            logger.error(f"SFTP connection failed: {e}")
            raise
    
    def is_file_processed(self, conn, file_name: str) -> bool:
        """Check if a daily file has already been processed"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM florida_daily_processed_files 
                        WHERE file_name = %s AND status = 'completed'
                    )
                """, (file_name,))
                return cur.fetchone()[0]
        except:
            return False
    
    def parse_record(self, line: str, line_num: int, file_name: str, file_date: str) -> Optional[Dict]:
        """Parse a record from daily file using proven logic"""
        try:
            if len(line) < 100:
                return None
            
            # Generate unique entity_id with DAILY prefix for daily updates
            base_id = line[0:12].strip()
            entity_id = f"D{file_date}_{base_id or f'FL{line_num:06d}'}_{line_num}"[:50]
            
            business_name = line[12:212].strip()[:255]
            if not business_name:
                return None
            
            # Parse date fields
            def parse_date(date_str):
                if not date_str or len(date_str) != 8:
                    return None
                try:
                    year, month, day = date_str[0:4], date_str[4:6], date_str[6:8]
                    if 1900 < int(year) < 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                        return f"{year}-{month}-{day}"
                except:
                    pass
                return None
            
            return {
                'entity_id': entity_id,
                'entity_type': line[218:219] if len(line) > 218 else 'C',
                'business_name': business_name,
                'dba_name': '',
                'entity_status': line[212:218].strip()[:50] if len(line) > 212 else 'ACTIVE',
                'business_address_line1': line[238:338].strip()[:255] if len(line) > 238 else '',
                'business_address_line2': '',
                'business_city': line[338:388].strip()[:100] if len(line) > 338 else '',
                'business_state': line[388:390].strip()[:2] if len(line) > 388 else 'FL',
                'business_zip': line[390:400].strip()[:10] if len(line) > 390 else '',
                'business_county': '',
                'mailing_address_line1': line[400:500].strip()[:255] if len(line) > 400 else '',
                'mailing_address_line2': '',
                'mailing_city': line[500:550].strip()[:100] if len(line) > 500 else '',
                'mailing_state': line[550:552].strip()[:2] if len(line) > 550 else '',
                'mailing_zip': line[552:562].strip()[:10] if len(line) > 552 else '',
                'formation_date': parse_date(line[228:236].strip()),
                'registration_date': parse_date(line[228:236].strip()),
                'last_update_date': datetime.now().date().isoformat(),
                'source_file': file_name,
                'source_record_line': line_num,
                'is_daily_update': True
            }
        except Exception as e:
            logger.warning(f"Parse error line {line_num}: {e}")
            return None
    
    def deduplicate_records(self, records: List[Dict]) -> List[Dict]:
        """CRITICAL: Deduplicate to prevent duplicate key errors"""
        seen_entity_ids = set()
        deduplicated = []
        
        for record in records:
            entity_id = record.get('entity_id')
            if entity_id and entity_id not in seen_entity_ids:
                seen_entity_ids.add(entity_id)
                deduplicated.append(record)
        
        return deduplicated
    
    def upsert_records(self, conn, records: List[Dict]) -> Dict[str, int]:
        """Insert or update records using efficient UPSERT"""
        if not records:
            return {'created': 0, 'updated': 0}
        
        # Deduplicate first!
        records = self.deduplicate_records(records)
        
        try:
            # Prepare CSV data for COPY
            output = StringIO()
            for record in records:
                row = [
                    record['entity_id'],
                    record['entity_type'],
                    record['business_name'],
                    record['dba_name'],
                    record['entity_status'],
                    record['business_address_line1'],
                    record['business_address_line2'],
                    record['business_city'],
                    record['business_state'],
                    record['business_zip'],
                    record['business_county'],
                    record['mailing_address_line1'],
                    record['mailing_address_line2'],
                    record['mailing_city'],
                    record['mailing_state'],
                    record['mailing_zip'],
                    record['formation_date'] or '\\N',
                    record['registration_date'] or '\\N',
                    record['last_update_date'] or '\\N',
                    record['source_file'],
                    str(record['source_record_line'])
                ]
                output.write('\t'.join(str(v) if v else '' for v in row) + '\n')
            
            output.seek(0)
            
            # Create temp table for staging
            with conn.cursor() as cur:
                # Create temp table
                cur.execute("""
                    CREATE TEMP TABLE temp_daily_updates (
                        entity_id VARCHAR(50),
                        entity_type VARCHAR(10),
                        business_name VARCHAR(255),
                        dba_name VARCHAR(255),
                        entity_status VARCHAR(50),
                        business_address_line1 VARCHAR(255),
                        business_address_line2 VARCHAR(255),
                        business_city VARCHAR(100),
                        business_state VARCHAR(2),
                        business_zip VARCHAR(10),
                        business_county VARCHAR(50),
                        mailing_address_line1 VARCHAR(255),
                        mailing_address_line2 VARCHAR(255),
                        mailing_city VARCHAR(100),
                        mailing_state VARCHAR(2),
                        mailing_zip VARCHAR(10),
                        formation_date DATE,
                        registration_date DATE,
                        last_update_date DATE,
                        source_file VARCHAR(255),
                        source_record_line INTEGER
                    )
                """)
                
                # Bulk load into temp table
                cur.copy_expert("""
                    COPY temp_daily_updates FROM STDIN 
                    WITH (FORMAT text, NULL '\\N', DELIMITER E'\t')
                """, output)
                
                # Perform UPSERT from temp table
                cur.execute("""
                    INSERT INTO florida_entities 
                    SELECT * FROM temp_daily_updates
                    ON CONFLICT (entity_id) 
                    DO UPDATE SET
                        business_name = EXCLUDED.business_name,
                        entity_status = EXCLUDED.entity_status,
                        business_address_line1 = EXCLUDED.business_address_line1,
                        business_city = EXCLUDED.business_city,
                        business_state = EXCLUDED.business_state,
                        business_zip = EXCLUDED.business_zip,
                        mailing_address_line1 = EXCLUDED.mailing_address_line1,
                        mailing_city = EXCLUDED.mailing_city,
                        mailing_state = EXCLUDED.mailing_state,
                        mailing_zip = EXCLUDED.mailing_zip,
                        last_update_date = EXCLUDED.last_update_date,
                        source_file = EXCLUDED.source_file;
                """)
                
                # Get stats
                updated_count = cur.rowcount
                
                # Drop temp table
                cur.execute("DROP TABLE temp_daily_updates")
                
                conn.commit()
                
                return {'created': len(records), 'updated': updated_count}
                
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            conn.rollback()
            return {'created': 0, 'updated': 0}
    
    def process_daily_file(self, sftp, file_name: str, file_path: str) -> bool:
        """Process a single daily file directly from SFTP to Supabase"""
        start_time = time.time()
        conn = self.get_db_connection()
        
        try:
            # Check if already processed
            if self.is_file_processed(conn, file_name):
                logger.info(f"File {file_name} already processed, skipping")
                return True
            
            logger.info(f"Processing daily file: {file_name}")
            
            # Extract date from filename (yyyymmdd format)
            file_date = file_name[:8] if len(file_name) >= 8 else datetime.now().strftime('%Y%m%d')
            
            # Read file directly from SFTP into memory
            file_obj = io.BytesIO()
            sftp.getfo(file_path, file_obj)
            file_obj.seek(0)
            
            # Parse records
            records = []
            lines = file_obj.read().decode('utf-8', errors='ignore').splitlines()
            
            for line_num, line in enumerate(lines, 1):
                if len(line) < 50:
                    continue
                
                record = self.parse_record(line, line_num, file_name, file_date)
                if record:
                    records.append(record)
                
                # Process in batches of 1000
                if len(records) >= 1000:
                    result = self.upsert_records(conn, records)
                    self.stats['entities_created'] += result['created']
                    self.stats['entities_updated'] += result['updated']
                    records = []
            
            # Process remaining records
            if records:
                result = self.upsert_records(conn, records)
                self.stats['entities_created'] += result['created']
                self.stats['entities_updated'] += result['updated']
            
            # Mark file as processed
            processing_time = time.time() - start_time
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO florida_daily_processed_files 
                    (file_name, file_type, file_date, records_processed, 
                     entities_created, entities_updated, processing_time_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    file_name,
                    self.identify_file_type(file_name),
                    datetime.strptime(file_date, '%Y%m%d').date(),
                    len(lines),
                    self.stats['entities_created'],
                    self.stats['entities_updated'],
                    processing_time
                ))
                conn.commit()
            
            self.stats['files_processed'] += 1
            logger.info(f"Completed {file_name}: {len(lines)} records in {processing_time:.2f}s")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error processing {file_name}: {e}")
            self.stats['errors'] += 1
            
            # Log error
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO florida_daily_processed_files 
                        (file_name, status, error_message)
                        VALUES (%s, 'failed', %s)
                    """, (file_name, str(e)))
                    conn.commit()
            except:
                pass
            
            conn.close()
            return False
    
    def identify_file_type(self, file_name: str) -> str:
        """Identify file type from filename"""
        for suffix, file_type in self.file_types.items():
            if suffix in file_name.lower():
                return file_type
        return 'unknown'
    
    def get_daily_files(self, sftp, days_back: int = 7) -> List[tuple]:
        """Get list of daily files from the last N days"""
        daily_files = []
        
        # Navigate to the correct directory
        # Based on the website, files are in different directories
        directories = [
            '/Corporate_Data/Daily',
            '/Fictitious_Name_Data/Daily',
            '/General_Partnership_Data/Daily',
            '/Federal_Tax_Lien_Data/Daily',
            '/Mark_Data/Daily'
        ]
        
        for directory in directories:
            try:
                sftp.chdir(directory)
                files = sftp.listdir()
                
                # Filter for recent files (last N days)
                for file_name in files:
                    if file_name.endswith('.txt'):
                        # Parse date from filename
                        try:
                            file_date_str = file_name[:8]
                            file_date = datetime.strptime(file_date_str, '%Y%m%d')
                            
                            # Check if within date range
                            if file_date >= datetime.now() - timedelta(days=days_back):
                                file_path = f"{directory}/{file_name}"
                                daily_files.append((file_name, file_path))
                                logger.info(f"Found daily file: {file_name} in {directory}")
                        except:
                            continue
                            
            except Exception as e:
                logger.warning(f"Could not access directory {directory}: {e}")
                continue
        
        return daily_files
    
    def run_daily_update(self, days_back: int = 7):
        """Main method to run daily update process"""
        logger.info("="*70)
        logger.info("FLORIDA DAILY UPDATE STARTING")
        logger.info("="*70)
        
        self.stats['start_time'] = datetime.now()
        
        # Connect to SFTP
        sftp, transport = self.get_sftp_connection()
        
        try:
            # Get list of daily files
            daily_files = self.get_daily_files(sftp, days_back)
            
            if not daily_files:
                logger.info("No new daily files found")
                return
            
            logger.info(f"Found {len(daily_files)} daily files to process")
            
            # Process each file
            for file_name, file_path in daily_files:
                success = self.process_daily_file(sftp, file_name, file_path)
                if not success:
                    logger.warning(f"Failed to process {file_name}")
            
            # Print summary
            elapsed = datetime.now() - self.stats['start_time']
            logger.info("="*70)
            logger.info("DAILY UPDATE COMPLETE")
            logger.info(f"Files processed: {self.stats['files_processed']}")
            logger.info(f"Entities created: {self.stats['entities_created']:,}")
            logger.info(f"Entities updated: {self.stats['entities_updated']:,}")
            logger.info(f"Errors: {self.stats['errors']}")
            logger.info(f"Runtime: {elapsed}")
            logger.info("="*70)
            
        finally:
            sftp.close()
            transport.close()
    
    def schedule_daily_updates(self):
        """Schedule daily updates to run automatically"""
        logger.info("Scheduling daily updates...")
        
        # Schedule to run every day at 2 AM EST
        schedule.every().day.at("02:00").do(lambda: self.run_daily_update(days_back=1))
        
        # Also run immediately for testing
        self.run_daily_update(days_back=7)
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    updater = FloridaDailyUpdater()
    
    # For immediate testing, just run once
    updater.run_daily_update(days_back=7)
    
    # Uncomment to enable scheduled runs
    # updater.schedule_daily_updates()

if __name__ == "__main__":
    main()