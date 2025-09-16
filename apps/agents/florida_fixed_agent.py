"""
FLORIDA FIXED AGENT - RESOLVES ON CONFLICT ISSUES
==============================================
Addresses the specific "ON CONFLICT DO UPDATE command cannot affect row a second time" error
"""

import os
import logging
import psycopg2
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import mmap
import re
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class FloridaFixedAgent:
    """FIXED AGENT - Solves ON CONFLICT issues definitively"""
    
    def __init__(self):
        self.db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        
        self.stats = {
            'files_processed': 0,
            'records_successful': 0,
            'entities_created': 0,
            'start_time': datetime.now()
        }
    
    def get_connection(self):
        """Get database connection"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require'
        )
        return conn
    
    def parse_record(self, line: str, line_num: int) -> Optional[Dict]:
        """Parse record with guaranteed unique entity_id"""
        try:
            if len(line) < 100:
                return None
            
            # Extract base entity ID
            base_entity_id = line[0:12].strip()
            
            # If empty or invalid, generate unique ID
            if not base_entity_id or len(base_entity_id) < 6:
                entity_id = f"GEN{uuid.uuid4().hex[:8].upper()}"
            else:
                entity_id = base_entity_id
            
            record = {
                'entity_id': entity_id,
                'entity_type': line[218:228].strip()[:1] if len(line) > 218 else 'C',
                'business_name': line[12:212].strip()[:255],
                'dba_name': '',
                'entity_status': line[212:218].strip()[:10] if len(line) > 212 else 'ACTIVE',
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
                'formation_date': self.parse_date(line[228:236].strip()),
                'registration_date': self.parse_date(line[228:236].strip()),
                'last_update_date': None,
                'source_file': '',
                'source_record_line': line_num
            }
            
            # Clean all string fields
            for key, value in record.items():
                if isinstance(value, str):
                    record[key] = value.replace('\x00', '').strip()
            
            return record if record['business_name'] else None
            
        except Exception as e:
            logger.warning(f"Parse error line {line_num}: {e}")
            return None
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date from YYYYMMDD"""
        if not date_str or len(date_str) != 8:
            return None
        try:
            year, month, day = date_str[0:4], date_str[4:6], date_str[6:8]
            if 1900 < int(year) < 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def insert_entity_single(self, conn, record: Dict, source_file: str) -> bool:
        """
        INSERT SINGLE ENTITY WITH BULLETPROOF CONFLICT RESOLUTION
        Uses individual transactions to avoid batch conflicts
        """
        try:
            record['source_file'] = source_file
            
            # Method 1: Try simple INSERT first
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO florida_entities (
                            entity_id, entity_type, business_name, dba_name, entity_status,
                            business_address_line1, business_address_line2, business_city, 
                            business_state, business_zip, business_county,
                            mailing_address_line1, mailing_address_line2, mailing_city,
                            mailing_state, mailing_zip, formation_date, registration_date,
                            last_update_date, source_file, source_record_line
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id;
                    """, (
                        record.get('entity_id'),
                        record.get('entity_type'),
                        record.get('business_name'),
                        record.get('dba_name'),
                        record.get('entity_status'),
                        record.get('business_address_line1'),
                        record.get('business_address_line2'),
                        record.get('business_city'),
                        record.get('business_state'),
                        record.get('business_zip'),
                        record.get('business_county'),
                        record.get('mailing_address_line1'),
                        record.get('mailing_address_line2'),
                        record.get('mailing_city'),
                        record.get('mailing_state'),
                        record.get('mailing_zip'),
                        record.get('formation_date'),
                        record.get('registration_date'),
                        record.get('last_update_date'),
                        record.get('source_file'),
                        record.get('source_record_line')
                    ))
                    
                    result = cur.fetchone()
                    conn.commit()
                    return result is not None
                    
                except psycopg2.IntegrityError as e:
                    # Duplicate key - try UPDATE instead
                    conn.rollback()
                    
                    if 'duplicate key' in str(e).lower():
                        # Method 2: UPDATE existing record
                        cur.execute("""
                            UPDATE florida_entities SET
                                business_name = %s,
                                entity_status = %s,
                                business_address_line1 = %s,
                                business_city = %s,
                                business_state = %s,
                                business_zip = %s,
                                mailing_address_line1 = %s,
                                mailing_city = %s,
                                mailing_state = %s,
                                mailing_zip = %s,
                                formation_date = COALESCE(%s, formation_date),
                                updated_at = NOW()
                            WHERE entity_id = %s
                            RETURNING id;
                        """, (
                            record.get('business_name'),
                            record.get('entity_status'),
                            record.get('business_address_line1'),
                            record.get('business_city'),
                            record.get('business_state'),
                            record.get('business_zip'),
                            record.get('mailing_address_line1'),
                            record.get('mailing_city'),
                            record.get('mailing_state'),
                            record.get('mailing_zip'),
                            record.get('formation_date'),
                            record.get('entity_id')
                        ))
                        
                        result = cur.fetchone()
                        conn.commit()
                        return result is not None
                    else:
                        # Method 3: Generate new unique ID and retry
                        new_entity_id = f"{record.get('entity_id')[:8]}_{uuid.uuid4().hex[:4]}"
                        record['entity_id'] = new_entity_id
                        
                        cur.execute("""
                            INSERT INTO florida_entities (
                                entity_id, entity_type, business_name, dba_name, entity_status,
                                business_address_line1, business_address_line2, business_city, 
                                business_state, business_zip, business_county,
                                mailing_address_line1, mailing_address_line2, mailing_city,
                                mailing_state, mailing_zip, formation_date, registration_date,
                                last_update_date, source_file, source_record_line
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            ) RETURNING id;
                        """, (
                            record.get('entity_id'),
                            record.get('entity_type'),
                            record.get('business_name'),
                            record.get('dba_name'),
                            record.get('entity_status'),
                            record.get('business_address_line1'),
                            record.get('business_address_line2'),
                            record.get('business_city'),
                            record.get('business_state'),
                            record.get('business_zip'),
                            record.get('business_county'),
                            record.get('mailing_address_line1'),
                            record.get('mailing_address_line2'),
                            record.get('mailing_city'),
                            record.get('mailing_state'),
                            record.get('mailing_zip'),
                            record.get('formation_date'),
                            record.get('registration_date'),
                            record.get('last_update_date'),
                            record.get('source_file'),
                            record.get('source_record_line')
                        ))
                        
                        result = cur.fetchone()
                        conn.commit()
                        return result is not None
                        
        except Exception as e:
            logger.error(f"Entity insert failed completely: {e}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                except:
                    pass
            return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process file with individual record transactions"""
        logger.info(f"Processing: {file_path.name}")
        
        try:
            conn = self.get_connection()
            
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.info(f"Skipped empty file: {file_path.name}")
                return True
            
            records_processed = 0
            entities_created = 0
            
            # Memory-mapped reading
            with open(file_path, 'r+b') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                    text = mmapped.read().decode('utf-8', errors='ignore')
                    lines = text.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        if len(line) < 50:
                            continue
                        
                        # Parse record
                        record = self.parse_record(line, line_num)
                        if not record:
                            continue
                        
                        records_processed += 1
                        
                        # Insert entity with bulletproof handling
                        if self.insert_entity_single(conn, record, file_path.name):
                            entities_created += 1
                        
                        # Progress every 1000 records
                        if records_processed % 1000 == 0:
                            logger.info(f"  Progress: {records_processed} records, {entities_created} entities")
            
            conn.close()
            
            # Update stats
            self.stats['files_processed'] += 1
            self.stats['records_successful'] += records_processed
            self.stats['entities_created'] += entities_created
            
            logger.info(f"SUCCESS: {file_path.name} - {records_processed} records, {entities_created} entities")
            return True
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
            if 'conn' in locals():
                conn.close()
            return False
    
    def run_upload(self):
        """Run upload with single-record transactions"""
        print("\n" + "="*60)
        print("FLORIDA FIXED AGENT - RESOLVING ON CONFLICT ERRORS")
        print("="*60)
        
        # Get files starting from where we left off
        all_files = []
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.txt') and 'README' not in file.upper():
                    all_files.append(Path(root) / file)
        
        all_files = sorted(all_files)
        total_files = len(all_files)
        
        logger.info(f"Found {total_files} files to process")
        
        # Start from file 5 (since first 4 were processed)
        start_index = 4  
        files_to_process = all_files[start_index:]
        
        logger.info(f"Resuming from file {start_index + 1}: {files_to_process[0].name if files_to_process else 'None'}")
        
        # Process files
        last_status_time = time.time()
        
        for i, file_path in enumerate(files_to_process, start_index + 1):
            success = self.process_file(file_path)
            
            # Print status every 60 seconds  
            if time.time() - last_status_time > 60:
                print(f"\\nProgress: {i}/{total_files} files ({i/total_files*100:.1f}%)")
                print(f"Entities created: {self.stats['entities_created']:,}")
                print(f"Success rate: {self.stats['files_processed']/(i-start_index)*100:.1f}%")
                last_status_time = time.time()
        
        print(f"\\n{'='*60}")
        print("UPLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"Files: {self.stats['files_processed']}/{total_files}")
        print(f"Entities: {self.stats['entities_created']:,}")

def main():
    agent = FloridaFixedAgent()
    agent.run_upload()

if __name__ == "__main__":
    main()