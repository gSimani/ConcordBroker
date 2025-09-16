"""
Process the downloaded corprindata.zip file to extract all officer emails
Uses the high-performance pipeline we built earlier
"""

import sys
import io
import os
import zipfile
from pathlib import Path
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import ThreadedConnectionPool
from urllib.parse import urlparse
import re
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CorprinDataProcessor:
    """Process corprindata.zip for officer emails using high-performance pipeline"""
    
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.corprin_file = self.base_path / "corprindata.zip"
        
        # Database connection
        db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        parsed = urlparse(db_url)
        self.conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password.replace('%40', '@') if parsed.password else None,
            'sslmode': 'require'
        }
        
        self.conn_pool = ThreadedConnectionPool(1, 10, **self.conn_params)
        
        # Pipeline queues
        self.parse_queue = Queue(maxsize=100)
        self.db_queue = Queue(maxsize=100)
        
        # Stats
        self.stats = {
            'files_processed': 0,
            'records_processed': 0,
            'emails_found': 0,
            'phones_found': 0,
            'start_time': time.time()
        }
        
        # Control
        self.stop_event = threading.Event()
    
    def check_file_ready(self):
        """Check if corprindata.zip is ready"""
        if not self.corprin_file.exists():
            print(f"❌ File not found: {self.corprin_file}")
            print("Run: python download_corprindata_background.py")
            return False
        
        size_mb = self.corprin_file.stat().st_size / (1024 * 1024)
        print(f"✅ Found file: {self.corprin_file.name} ({size_mb:.1f} MB)")
        
        # Check if it's the complete file (should be ~665MB)
        if size_mb < 600:
            print(f"⚠️ File seems incomplete. Expected ~665MB, got {size_mb:.1f} MB")
            print("Download may still be in progress")
            return False
            
        return True
    
    def parse_principal_record(self, line: str, filename: str) -> dict:
        """Parse principal/officer record and extract contact info"""
        # Principal data format varies, but typically pipe-delimited
        parts = line.strip().split('|')
        
        if len(parts) < 3:
            return None
        
        record = {
            'doc_number': parts[0][:20] if parts else '',
            'entity_name': parts[1][:500] if len(parts) > 1 else '',
            'principal_name': parts[2][:500] if len(parts) > 2 else '',
            'principal_title': parts[3][:200] if len(parts) > 3 else '',
            'principal_address': parts[4][:500] if len(parts) > 4 else '',
            'source_file': filename[:255],
            'import_date': datetime.now()
        }
        
        # Look for email anywhere in the record
        full_text = '|'.join(parts)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        emails = re.findall(email_pattern, full_text, re.IGNORECASE)
        if emails:
            record['principal_email'] = emails[0].lower()[:255]
            self.stats['emails_found'] += 1
        
        # Look for phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, full_text)
        if phones:
            record['principal_phone'] = phones[0][:50]
            self.stats['phones_found'] += 1
        
        return record
    
    def parser_worker(self):
        """Worker to parse officer data"""
        while not self.stop_event.is_set():
            try:
                task = self.parse_queue.get(timeout=2)
                if task is None:
                    break
                
                filename, content = task
                
                # Decode content
                try:
                    if isinstance(content, bytes):
                        text = content.decode('utf-8', errors='ignore')
                    else:
                        text = content
                except:
                    text = str(content)
                
                lines = text.split('\n')
                batch = []
                
                for line in lines:
                    if line.strip():
                        record = self.parse_principal_record(line, filename)
                        if record and record.get('doc_number'):
                            batch.append(record)
                            
                            if len(batch) >= 1000:
                                self.db_queue.put(batch)
                                batch = []
                
                if batch:
                    self.db_queue.put(batch)
                
                self.stats['files_processed'] += 1
                
            except Empty:
                continue
            except Exception as e:
                print(f"Parser error: {e}")
    
    def db_writer_worker(self):
        """Worker to write to database"""
        conn = self.conn_pool.getconn()
        try:
            cur = conn.cursor()
            
            while not self.stop_event.is_set():
                try:
                    batch = self.db_queue.get(timeout=2)
                    if batch is None:
                        break
                    
                    # Insert batch
                    values = [
                        (
                            r.get('doc_number'),
                            r.get('entity_name'),
                            r.get('principal_name'),
                            r.get('principal_title'),
                            r.get('principal_address'),
                            r.get('principal_email'),
                            r.get('principal_phone'),
                            r.get('source_file'),
                            r.get('import_date')
                        )
                        for r in batch
                    ]
                    
                    execute_values(
                        cur,
                        """
                        INSERT INTO sunbiz_principal_data 
                        (doc_number, entity_name, principal_name, principal_title,
                         principal_address, principal_email, principal_phone, 
                         source_file, import_date)
                        VALUES %s
                        ON CONFLICT (doc_number, principal_name) DO UPDATE SET
                            principal_email = COALESCE(EXCLUDED.principal_email, sunbiz_principal_data.principal_email),
                            principal_phone = COALESCE(EXCLUDED.principal_phone, sunbiz_principal_data.principal_phone),
                            import_date = EXCLUDED.import_date
                        """,
                        values,
                        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    )
                    
                    conn.commit()
                    self.stats['records_processed'] += len(batch)
                    
                    # Progress update
                    if self.stats['records_processed'] % 10000 == 0:
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['records_processed'] / elapsed if elapsed > 0 else 0
                        print(f"✅ Processed: {self.stats['records_processed']:,} | "
                              f"Emails: {self.stats['emails_found']:,} | "
                              f"Rate: {rate:.0f}/sec")
                        
                except Empty:
                    continue
                except Exception as e:
                    print(f"DB error: {e}")
                    conn.rollback()
                    
        finally:
            self.conn_pool.putconn(conn)
    
    def process_zip_file(self):
        """Process the ZIP file"""
        print("\n📂 Processing corprindata.zip...")
        
        try:
            with zipfile.ZipFile(self.corprin_file, 'r') as zf:
                files = zf.namelist()
                print(f"Found {len(files)} files in ZIP")
                
                # Process each file
                for i, filename in enumerate(files):
                    print(f"\n📄 Processing {filename} ({i+1}/{len(files)})")
                    
                    try:
                        with zf.open(filename) as f:
                            # Read in chunks to avoid memory issues
                            chunk_size = 10 * 1024 * 1024  # 10MB chunks
                            chunk_num = 0
                            
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                
                                chunk_num += 1
                                chunk_filename = f"{filename}_chunk_{chunk_num}"
                                
                                # Queue for processing
                                self.parse_queue.put((chunk_filename, chunk))
                                
                                # Don't overwhelm the queue
                                while self.parse_queue.qsize() > 50:
                                    time.sleep(0.1)
                                    
                    except Exception as e:
                        print(f"   ❌ Error processing {filename}: {e}")
                        
        except Exception as e:
            print(f"❌ Error opening ZIP: {e}")
            return False
        
        return True
    
    def setup_database(self):
        """Setup database tables"""
        conn = self.conn_pool.getconn()
        try:
            conn.autocommit = True
            cur = conn.cursor()
            
            # Create table if not exists (don't drop existing)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_principal_data (
                    id SERIAL PRIMARY KEY,
                    doc_number VARCHAR(20),
                    entity_name VARCHAR(500),
                    principal_name VARCHAR(500),
                    principal_title VARCHAR(200),
                    principal_address VARCHAR(500),
                    principal_email VARCHAR(255),
                    principal_phone VARCHAR(50),
                    source_file VARCHAR(255),
                    import_date TIMESTAMP DEFAULT NOW(),
                    UNIQUE(doc_number, principal_name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_principal_doc ON sunbiz_principal_data(doc_number);
                CREATE INDEX IF NOT EXISTS idx_principal_email ON sunbiz_principal_data(principal_email) WHERE principal_email IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_principal_phone ON sunbiz_principal_data(principal_phone) WHERE principal_phone IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_principal_name ON sunbiz_principal_data(principal_name);
            """)
            
            print("✅ Database tables ready")
            
        finally:
            conn.autocommit = False
            self.conn_pool.putconn(conn)
    
    def create_final_views(self):
        """Create final views for easy querying"""
        conn = self.conn_pool.getconn()
        try:
            cur = conn.cursor()
            
            # Create comprehensive contacts view
            cur.execute("DROP MATERIALIZED VIEW IF EXISTS florida_business_contacts CASCADE")
            
            cur.execute("""
                CREATE MATERIALIZED VIEW florida_business_contacts AS
                SELECT DISTINCT
                    spd.doc_number,
                    spd.entity_name,
                    spd.principal_name,
                    spd.principal_title,
                    spd.principal_email,
                    spd.principal_phone,
                    spd.principal_address,
                    sc.status as entity_status,
                    sc.filing_date,
                    'principal_data' as source
                FROM sunbiz_principal_data spd
                LEFT JOIN sunbiz_corporate sc ON spd.doc_number = sc.doc_number
                WHERE spd.principal_email IS NOT NULL 
                   OR spd.principal_phone IS NOT NULL
                
                UNION
                
                SELECT DISTINCT
                    so.doc_number,
                    sc.entity_name,
                    so.officer_name as principal_name,
                    so.officer_title as principal_title,
                    so.officer_email as principal_email,
                    so.officer_phone as principal_phone,
                    so.officer_address as principal_address,
                    sc.status as entity_status,
                    sc.filing_date,
                    'officer_data' as source
                FROM sunbiz_officers so
                LEFT JOIN sunbiz_corporate sc ON so.doc_number = sc.doc_number
                WHERE so.officer_email IS NOT NULL 
                   OR so.officer_phone IS NOT NULL;
                
                CREATE INDEX idx_florida_contacts_email 
                    ON florida_business_contacts(principal_email) 
                    WHERE principal_email IS NOT NULL;
                    
                CREATE INDEX idx_florida_contacts_entity 
                    ON florida_business_contacts(entity_name);
            """)
            
            conn.commit()
            
            # Count results
            cur.execute("SELECT COUNT(*) FROM florida_business_contacts WHERE principal_email IS NOT NULL")
            email_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM florida_business_contacts WHERE principal_phone IS NOT NULL")
            phone_count = cur.fetchone()[0]
            
            print(f"\n✅ Created comprehensive contacts view:")
            print(f"   📧 {email_count:,} email addresses")
            print(f"   📞 {phone_count:,} phone numbers")
            
        finally:
            self.conn_pool.putconn(conn)
    
    def run(self):
        """Main processing pipeline"""
        print("=" * 60)
        print("FLORIDA CORPORATE PRINCIPAL DATA PROCESSOR")
        print("=" * 60)
        print("Processing 665MB corprindata.zip for officer emails")
        
        # Check if file is ready
        if not self.check_file_ready():
            return False
        
        # Setup database
        self.setup_database()
        
        # Start workers
        print("\n🚀 Starting processing pipeline...")
        
        # Start parser workers
        parser_threads = []
        for i in range(4):  # 4 parser threads
            t = threading.Thread(target=self.parser_worker, name=f"Parser-{i}")
            t.start()
            parser_threads.append(t)
        
        # Start DB writer threads
        db_threads = []
        for i in range(2):  # 2 DB writer threads
            t = threading.Thread(target=self.db_writer_worker, name=f"DBWriter-{i}")
            t.start()
            db_threads.append(t)
        
        print(f"✅ Started {len(parser_threads + db_threads)} worker threads")
        
        # Process the ZIP file
        success = self.process_zip_file()
        
        # Signal completion
        for _ in parser_threads:
            self.parse_queue.put(None)
        
        # Wait for parsers to finish
        for t in parser_threads:
            t.join()
        
        # Signal DB writers
        for _ in db_threads:
            self.db_queue.put(None)
        
        # Wait for DB writers to finish
        for t in db_threads:
            t.join()
        
        # Final statistics
        elapsed = time.time() - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)
        print(f"✅ Files processed: {self.stats['files_processed']}")
        print(f"✅ Records processed: {self.stats['records_processed']:,}")
        print(f"📧 Emails found: {self.stats['emails_found']:,}")
        print(f"📞 Phones found: {self.stats['phones_found']:,}")
        print(f"⏱️ Total time: {elapsed/60:.1f} minutes")
        
        if self.stats['records_processed'] > 0:
            rate = self.stats['records_processed'] / elapsed
            print(f"🚀 Average rate: {rate:.0f} records/second")
        
        if success and self.stats['emails_found'] > 0:
            # Create final views
            self.create_final_views()
            
            print("\n🎉 SUCCESS! Officer email extraction complete")
            print("\n📊 Query examples:")
            print("-- All contacts with emails:")
            print("SELECT * FROM florida_business_contacts WHERE principal_email IS NOT NULL LIMIT 10;")
            print("\n-- Search by company:")
            print("SELECT * FROM florida_business_contacts WHERE entity_name ILIKE '%concord%';")
            print("\n-- Export all emails:")
            print("SELECT DISTINCT principal_email FROM florida_business_contacts WHERE principal_email IS NOT NULL;")
        
        return success

if __name__ == "__main__":
    processor = CorprinDataProcessor()
    processor.run()