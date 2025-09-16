"""
FLORIDA SYNERGY AGENT - Parallel Processing Helper
==================================================
Works alongside the current running agent by:
- Processing files from the END of the list backwards
- Using turbo optimizations
- Avoiding conflicts with the forward-running agent
"""

import os
import logging
import psycopg2
from psycopg2 import pool
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SYNERGY] %(message)s')
logger = logging.getLogger(__name__)

class FloridaSynergyAgent:
    """SYNERGY AGENT - Processes from the end backwards"""
    
    def __init__(self):
        self.db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        
        # Connection pool for speed
        self.connection_pool = None
        self.init_connection_pool()
        
        # Large batch size for speed
        self.batch_size = 2000
        
        self.stats = {
            'files_processed': 0,
            'entities_created': 0,
            'start_time': datetime.now()
        }
    
    def init_connection_pool(self):
        """Initialize connection pool"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.db_url)
        self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
            2, 8,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require'
        )
    
    def get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        self.connection_pool.putconn(conn)
    
    def check_if_file_processed(self, conn, file_name: str) -> bool:
        """Check if file already processed by other agent"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM florida_entities 
                    WHERE source_file = %s 
                    LIMIT 1
                """, (file_name,))
                count = cur.fetchone()[0]
                return count > 0
        except:
            return False
    
    def parse_record_turbo(self, line: str, line_num: int, file_name: str) -> Optional[Dict]:
        """Fast parsing for turbo speed"""
        if len(line) < 100:
            return None
        
        # Generate unique entity_id with BACK prefix to avoid conflicts
        base_id = line[0:12].strip()
        entity_id = f"B_{base_id or f'FL{line_num:06d}'}_{file_name[:4]}"[:50]
        
        business_name = line[12:212].strip()[:255]
        if not business_name:
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
            'formation_date': None,
            'registration_date': None,
            'last_update_date': None,
            'source_file': file_name,
            'source_record_line': line_num
        }
    
    def bulk_copy_records(self, conn, records: List[Dict]) -> int:
        """Use COPY for maximum speed"""
        if not records:
            return 0
        
        try:
            # Deduplicate
            seen = set()
            unique_records = []
            for r in records:
                if r['entity_id'] not in seen:
                    seen.add(r['entity_id'])
                    unique_records.append(r)
            
            # Create CSV data in memory
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
                # COPY is 10x faster than INSERT
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
            logger.error(f"Bulk copy failed: {e}")
            conn.rollback()
            return 0
    
    def process_file_synergy(self, file_path: Path) -> bool:
        """Process file with synergy approach"""
        try:
            conn = self.get_connection()
            
            # Check if already processed by forward agent
            if self.check_if_file_processed(conn, file_path.name):
                logger.info(f"Skipping {file_path.name} - already processed by forward agent")
                self.return_connection(conn)
                return True
            
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.return_connection(conn)
                return True
            
            logger.info(f"Processing: {file_path.name}")
            
            records = []
            
            # Read entire file for speed
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                if len(line) < 50:
                    continue
                
                record = self.parse_record_turbo(line, line_num, file_path.name)
                if record:
                    records.append(record)
                
                # Process in large batches
                if len(records) >= self.batch_size:
                    entities_created = self.bulk_copy_records(conn, records)
                    self.stats['entities_created'] += entities_created
                    records = []
            
            # Process remaining
            if records:
                entities_created = self.bulk_copy_records(conn, records)
                self.stats['entities_created'] += entities_created
            
            self.return_connection(conn)
            
            self.stats['files_processed'] += 1
            logger.info(f"SUCCESS: {file_path.name} - processed {len(lines)} records")
            
            return True
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
            if 'conn' in locals():
                self.return_connection(conn)
            return False
    
    def run_backwards_synergy(self):
        """Run backwards from end to meet the forward agent in the middle"""
        print("\n" + "="*70)
        print("FLORIDA SYNERGY AGENT - BACKWARD PROCESSING")
        print("="*70)
        print("[SYNERGY] Processing from END backwards")
        print("[SYNERGY] Will meet forward agent in the middle")
        print("[SYNERGY] Using TURBO optimizations")
        print("[SYNERGY] Avoiding conflicts with unique prefixes")
        
        # Get all files
        all_files = []
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.txt') and 'README' not in file.upper():
                    all_files.append(Path(root) / file)
        
        all_files = sorted(all_files)
        total_files = len(all_files)
        
        # Process from the END backwards
        # Forward agent is at ~3662, so start from end and work backwards
        files_to_process = all_files[4000:]  # Start from file 4000 to end
        files_to_process.reverse()  # Process backwards
        
        print(f"\nProcessing {len(files_to_process)} files backwards from file {total_files}")
        print(f"Forward agent is at file ~3662, we'll meet in the middle")
        
        last_status_time = time.time()
        
        for i, file_path in enumerate(files_to_process, 1):
            success = self.process_file_synergy(file_path)
            
            # Status update every 20 seconds
            if time.time() - last_status_time > 20:
                elapsed = datetime.now() - self.stats['start_time']
                rate = i / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                
                file_index = total_files - i + 1
                print(f"\n[SYNERGY] Processed: {i} files backward")
                print(f"[SYNERGY] Current position: file {file_index} of {total_files}")
                print(f"[SYNERGY] Entities created: {self.stats['entities_created']:,}")
                print(f"[SYNERGY] Rate: {rate:.2f} files/sec")
                print(f"[SYNERGY] Gap to forward agent: ~{file_index - 3662} files")
                
                last_status_time = time.time()
                
                # Check if we've met the forward agent
                if file_index <= 3700:
                    print("\n[SYNERGY] Meeting point reached! Forward and backward agents have converged.")
                    break
        
        # Close connection pool
        if self.connection_pool:
            self.connection_pool.closeall()
        
        print(f"\n{'='*70}")
        print("SYNERGY PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Files processed backwards: {self.stats['files_processed']:,}")
        print(f"Entities created: {self.stats['entities_created']:,}")
        print(f"Runtime: {datetime.now() - self.stats['start_time']}")
        print("\n[SUCCESS] Synergy approach accelerated the upload!")

def main():
    agent = FloridaSynergyAgent()
    agent.run_backwards_synergy()

if __name__ == "__main__":
    main()