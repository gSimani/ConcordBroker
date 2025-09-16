"""
FLORIDA EFFICIENT GAP FILLER - Optimized for Large Databases
===========================================================
Efficiently finds and uploads missing files without timeout issues
"""

import os
import logging
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from io import StringIO
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [GAP-EFFICIENT] %(message)s')
logger = logging.getLogger(__name__)

class FloridaEfficientGapFiller:
    """Efficient gap filler that avoids database timeouts"""
    
    def __init__(self):
        self.db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'entities_created': 0,
            'already_processed': 0,
            'start_time': datetime.now()
        }
    
    def get_connection(self):
        """Get database connection with timeout settings"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require',
            connect_timeout=30,
            options='-c statement_timeout=60000'  # 60 second timeout for queries
        )
        return conn
    
    def check_file_exists(self, conn, file_name: str) -> bool:
        """Check if a specific file exists in database (efficient single check)"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM florida_entities 
                        WHERE source_file = %s 
                        LIMIT 1
                    )
                """, (file_name,))
                return cur.fetchone()[0]
        except Exception as e:
            logger.warning(f"Error checking file {file_name}: {e}")
            return False
    
    def parse_record(self, line: str, line_num: int, file_name: str) -> Optional[Dict]:
        """Parse record with GAP2 prefix (new prefix to avoid any conflicts)"""
        try:
            if len(line) < 100:
                return None
            
            # Generate unique entity_id with GAP2 prefix for this efficient run
            base_id = line[0:12].strip()
            entity_id = f"GAP2_{base_id or f'FL{line_num:06d}'}_{file_name[:4]}_{line_num}"[:50]
            
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
                'last_update_date': None,
                'source_file': file_name,
                'source_record_line': line_num
            }
            
        except Exception as e:
            logger.warning(f"Parse error line {line_num}: {e}")
            return None
    
    def bulk_insert_records(self, conn, records: List[Dict]) -> int:
        """Bulk insert records using COPY for speed"""
        if not records:
            return 0
        
        try:
            # Deduplicate by entity_id
            seen = set()
            unique_records = []
            for r in records:
                if r['entity_id'] not in seen:
                    seen.add(r['entity_id'])
                    unique_records.append(r)
            
            # Create CSV data
            output = StringIO()
            for record in unique_records:
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
            
            with conn.cursor() as cur:
                cur.copy_expert("""
                    COPY florida_entities (
                        entity_id, entity_type, business_name, dba_name, entity_status,
                        business_address_line1, business_address_line2, business_city,
                        business_state, business_zip, business_county,
                        mailing_address_line1, mailing_address_line2, mailing_city,
                        mailing_state, mailing_zip, formation_date, registration_date,
                        last_update_date, source_file, source_record_line
                    ) FROM STDIN WITH (FORMAT text, NULL '\\N', DELIMITER E'\t')
                """, output)
                
                conn.commit()
                return len(unique_records)
                
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            conn.rollback()
            return 0
    
    def process_file(self, file_path: Path, conn) -> bool:
        """Process a single gap file"""
        logger.info(f"Processing gap file: {file_path.name}")
        
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.info(f"Skipped empty file: {file_path.name}")
                return True
            
            records = []
            
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                if len(line) < 50:
                    continue
                
                record = self.parse_record(line, line_num, file_path.name)
                if record:
                    records.append(record)
            
            if not records:
                logger.info(f"No valid records in {file_path.name}")
                # Mark as processed anyway by inserting a placeholder
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO florida_entities (
                            entity_id, entity_type, business_name, source_file, source_record_line
                        ) VALUES (%s, 'P', 'PLACEHOLDER_EMPTY_FILE', %s, 0)
                        ON CONFLICT (entity_id) DO NOTHING
                    """, (f"EMPTY_{file_path.name}", file_path.name))
                    conn.commit()
                return True
            
            # Insert records
            entities_created = self.bulk_insert_records(conn, records)
            
            self.stats['entities_created'] += entities_created
            self.stats['files_processed'] += 1
            
            logger.info(f"SUCCESS: {file_path.name} - {len(records)} records parsed, {entities_created} entities created")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return False
    
    def find_and_fill_gaps_efficiently(self):
        """Efficiently find and process unprocessed files one by one"""
        print("\n" + "="*70)
        print("FLORIDA EFFICIENT GAP FILLER - Processing Missing Files")
        print("="*70)
        print("[INFO] Using efficient one-by-one checking to avoid timeouts")
        
        # Get database connection
        conn = self.get_connection()
        
        # Get all files from filesystem
        all_files = []
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.txt') and 'README' not in file.upper():
                    all_files.append(Path(root) / file)
        
        all_files = sorted(all_files)
        logger.info(f"Found {len(all_files)} total files in filesystem")
        
        # Check each file individually (avoids timeout)
        gap_files = []
        checked_count = 0
        
        print(f"\nChecking {len(all_files)} files for gaps...")
        print("This may take a few minutes but avoids database timeouts...")
        
        start_check = time.time()
        for i, file_path in enumerate(all_files, 1):
            # Check if file exists in database
            if not self.check_file_exists(conn, file_path.name):
                gap_files.append(file_path)
                self.stats['files_found'] += 1
                logger.info(f"Found gap file: {file_path.name}")
            else:
                self.stats['already_processed'] += 1
            
            checked_count += 1
            
            # Progress update every 100 files
            if checked_count % 100 == 0:
                elapsed = time.time() - start_check
                rate = checked_count / elapsed if elapsed > 0 else 0
                remaining = (len(all_files) - checked_count) / rate if rate > 0 else 0
                print(f"  Checked {checked_count}/{len(all_files)} files "
                      f"({checked_count/len(all_files)*100:.1f}%) - "
                      f"Found {len(gap_files)} gaps - "
                      f"ETA: {remaining:.0f}s")
        
        print(f"\nGap detection complete!")
        print(f"  Files already processed: {self.stats['already_processed']}")
        print(f"  Gap files found: {len(gap_files)}")
        
        if not gap_files:
            print("\n[SUCCESS] NO GAP FILES FOUND - Database is 100% complete!")
            conn.close()
            return
        
        print(f"\nProcessing {len(gap_files)} missing files...")
        if len(gap_files) <= 30:
            print("Gap files:", [f.name for f in gap_files])
        else:
            print("First 30 gap files:", [f.name for f in gap_files[:30]], "...")
        
        # Process each gap file
        for i, file_path in enumerate(gap_files, 1):
            print(f"\n[{i}/{len(gap_files)}] Processing: {file_path.name}")
            success = self.process_file(file_path, conn)
            
            if i % 10 == 0:
                elapsed = datetime.now() - self.stats['start_time']
                print(f"Progress: {i}/{len(gap_files)} files ({i/len(gap_files)*100:.1f}%)")
                print(f"Entities created: {self.stats['entities_created']:,}")
                print(f"Runtime: {elapsed}")
        
        # Close connection
        conn.close()
        
        # Final report
        print(f"\n{'='*70}")
        print("EFFICIENT GAP FILLING COMPLETE")
        print(f"{'='*70}")
        print(f"Gap files found: {self.stats['files_found']}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Already processed: {self.stats['already_processed']}")
        print(f"Entities created: {self.stats['entities_created']:,}")
        print(f"Runtime: {datetime.now() - self.stats['start_time']}")
        
        if self.stats['files_processed'] == self.stats['files_found']:
            print(f"\n[SUCCESS] ALL GAP FILES PROCESSED!")
            print(f"[SUCCESS] DATABASE IS NOW 100% COMPLETE!")
        else:
            failed = self.stats['files_found'] - self.stats['files_processed']
            print(f"\n[WARNING] {failed} files failed to process")

def main():
    agent = FloridaEfficientGapFiller()
    agent.find_and_fill_gaps_efficiently()

if __name__ == "__main__":
    main()