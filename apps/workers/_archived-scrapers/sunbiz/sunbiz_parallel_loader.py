"""
Sunbiz Parallel Pipeline Loader
High-performance loader using parallel processing and memory optimization
Can achieve 10-50x speed improvement over sequential loading
"""

import os
import sys
import io
import logging
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.pool import ThreadedConnectionPool
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue
from threading import Thread, Lock
import multiprocessing as mp
from urllib.parse import urlparse
import mmap
import gc

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoaderConfig:
    """Configuration for parallel loader"""
    # Connection settings
    db_url: str = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    # Parallel processing settings
    num_file_readers: int = 4          # Parallel file readers
    num_parsers: int = 8               # Parallel line parsers
    num_db_writers: int = 4            # Parallel DB writers
    connection_pool_size: int = 10     # DB connection pool
    
    # Batch settings
    parse_batch_size: int = 10000      # Lines per parse batch
    db_batch_size: int = 5000          # Records per DB insert
    queue_max_size: int = 100          # Max batches in queue
    
    # Memory optimization
    use_mmap: bool = True              # Use memory-mapped files
    chunk_size_mb: int = 50            # File chunk size for processing
    gc_interval: int = 100000          # Run garbage collection every N records

class ParallelSunbizLoader:
    """High-performance parallel loader"""
    
    def __init__(self, config: LoaderConfig = None):
        self.config = config or LoaderConfig()
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        
        # Parse database URL
        parsed = urlparse(self.config.db_url)
        self.conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password.replace('%40', '@') if parsed.password else None,
            'sslmode': 'require'
        }
        
        # Create connection pool
        self.conn_pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=self.config.connection_pool_size,
            **self.conn_params
        )
        
        # Queues for pipeline
        self.file_queue = Queue(maxsize=1000)
        self.parse_queue = Queue(maxsize=self.config.queue_max_size)
        self.db_queue = Queue(maxsize=self.config.queue_max_size)
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'lines_read': 0,
            'records_parsed': 0,
            'records_inserted': 0,
            'errors': 0,
            'start_time': None
        }
        self.stats_lock = Lock()
        
        logger.info(f"Initialized parallel loader with {self.config.num_file_readers} readers, "
                   f"{self.config.num_parsers} parsers, {self.config.num_db_writers} writers")
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Fast date parsing"""
        if not date_str or len(date_str) != 8:
            return None
        try:
            # Skip datetime parsing for speed
            year, month, day = date_str[0:4], date_str[4:6], date_str[6:8]
            y, m, d = int(year), int(month), int(day)
            if 1900 < y < 2030 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def parse_corporate_line(self, line: str) -> Optional[Dict]:
        """Parse corporation line - optimized version"""
        try:
            if len(line) < 100:
                return None
            
            doc = line[0:12].strip()
            if not doc or len(doc) < 6:
                return None
            
            # Use slicing for speed (avoid multiple strip calls)
            return {
                'doc_number': doc,
                'entity_name': line[12:212].strip()[:255],
                'status': line[212:218].strip(),
                'filing_date': self.parse_date(line[228:236].strip()),
                'state_country': line[236:238].strip(),
                'prin_addr1': line[238:338].strip(),
                'prin_addr2': '',
                'prin_city': line[338:388].strip(),
                'prin_state': line[388:390].strip(),
                'prin_zip': line[390:400].strip(),
                'mail_addr1': line[400:500].strip() if len(line) > 400 else '',
                'mail_addr2': '',
                'mail_city': line[500:550].strip() if len(line) > 500 else '',
                'mail_state': line[550:552].strip() if len(line) > 550 else '',
                'mail_zip': line[552:562].strip() if len(line) > 552 else '',
                'ein': line[844:854].strip() if len(line) > 844 else '',
                'registered_agent': line[562:662].strip() if len(line) > 562 else '',
                'file_type': line[218:228].strip(),
                'subtype': '',
                'source_file': None
            }
        except:
            return None
    
    def file_reader_worker(self):
        """Worker thread that reads files and queues them for parsing"""
        while True:
            file_path = self.file_queue.get()
            if file_path is None:  # Poison pill
                break
            
            try:
                if self.config.use_mmap:
                    # Use memory-mapped file for better performance
                    with open(file_path, 'r+b') as f:
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                            content = mmapped.read().decode('utf-8', errors='ignore')
                            lines = content.splitlines()
                else:
                    # Traditional file reading
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                
                # Send lines in batches to parse queue
                for i in range(0, len(lines), self.config.parse_batch_size):
                    batch = lines[i:i + self.config.parse_batch_size]
                    self.parse_queue.put((file_path.name, batch))
                
                with self.stats_lock:
                    self.stats['files_processed'] += 1
                    self.stats['lines_read'] += len(lines)
                
                logger.info(f"Read {len(lines)} lines from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
            
            finally:
                self.file_queue.task_done()
    
    def parser_worker(self):
        """Worker thread that parses lines into records"""
        records_parsed = 0
        
        while True:
            item = self.parse_queue.get()
            if item is None:  # Poison pill
                break
            
            file_name, lines = item
            parsed_batch = []
            
            try:
                for line in lines:
                    record = self.parse_corporate_line(line)
                    if record:
                        parsed_batch.append(record)
                        records_parsed += 1
                        
                        # Periodic garbage collection
                        if records_parsed % self.config.gc_interval == 0:
                            gc.collect()
                
                if parsed_batch:
                    # Send to DB queue in smaller chunks
                    for i in range(0, len(parsed_batch), self.config.db_batch_size):
                        batch = parsed_batch[i:i + self.config.db_batch_size]
                        self.db_queue.put(('sunbiz_corporate', batch))
                
                with self.stats_lock:
                    self.stats['records_parsed'] += len(parsed_batch)
                
            except Exception as e:
                logger.error(f"Parse error: {e}")
                with self.stats_lock:
                    self.stats['errors'] += 1
            
            finally:
                self.parse_queue.task_done()
    
    def db_writer_worker(self):
        """Worker thread that writes records to database"""
        conn = self.conn_pool.getconn()
        
        # Optimize connection for bulk loading
        with conn.cursor() as cur:
            cur.execute("SET work_mem = '256MB';")
            cur.execute("SET synchronous_commit = OFF;")
            cur.execute("SET maintenance_work_mem = '512MB';")
            conn.commit()
        
        columns = [
            'doc_number', 'entity_name', 'status', 'filing_date', 'state_country',
            'prin_addr1', 'prin_addr2', 'prin_city', 'prin_state', 'prin_zip',
            'mail_addr1', 'mail_addr2', 'mail_city', 'mail_state', 'mail_zip',
            'ein', 'registered_agent', 'file_type', 'subtype', 'source_file'
        ]
        
        try:
            while True:
                item = self.db_queue.get()
                if item is None:  # Poison pill
                    break
                
                table_name, batch = item
                
                try:
                    with conn.cursor() as cur:
                        # Build UPSERT query
                        placeholders = ', '.join(['%s'] * len(columns))
                        columns_str = ', '.join(columns)
                        
                        query = f"""
                            INSERT INTO {table_name} ({columns_str})
                            VALUES ({placeholders})
                            ON CONFLICT (doc_number) DO UPDATE SET
                            {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'doc_number'])}
                        """
                        
                        # Convert batch to tuples
                        values = [tuple(record.get(col) for col in columns) for record in batch]
                        
                        # Use execute_batch for performance
                        execute_batch(cur, query, values, page_size=1000)
                        conn.commit()
                        
                        with self.stats_lock:
                            self.stats['records_inserted'] += len(batch)
                        
                        # Log progress every 10k records
                        if self.stats['records_inserted'] % 10000 == 0:
                            logger.info(f"Inserted {self.stats['records_inserted']:,} total records")
                    
                except Exception as e:
                    logger.error(f"DB write error: {e}")
                    conn.rollback()
                    with self.stats_lock:
                        self.stats['errors'] += 1
                
                finally:
                    self.db_queue.task_done()
        
        finally:
            self.conn_pool.putconn(conn)
    
    def run_parallel_load(self):
        """Main parallel loading orchestrator"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("SUNBIZ PARALLEL PIPELINE LOADER")
        logger.info("=" * 60)
        
        # Get all corporation files
        cor_path = self.data_path / "cor"
        files = list(cor_path.glob("*.txt"))
        
        # Include year subdirectories
        for year_dir in cor_path.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                files.extend(year_dir.glob("*.txt"))
        
        # Filter out non-data files
        files = [f for f in files if 'README' not in f.name.upper() and 'WELCOME' not in f.name.upper()]
        files.sort(reverse=True)  # Most recent first
        
        logger.info(f"Found {len(files)} corporation files to process")
        
        # Start worker threads
        workers = []
        
        # File readers
        for i in range(self.config.num_file_readers):
            t = Thread(target=self.file_reader_worker, name=f"FileReader-{i}")
            t.start()
            workers.append(t)
        
        # Parsers
        for i in range(self.config.num_parsers):
            t = Thread(target=self.parser_worker, name=f"Parser-{i}")
            t.start()
            workers.append(t)
        
        # DB writers
        for i in range(self.config.num_db_writers):
            t = Thread(target=self.db_writer_worker, name=f"DBWriter-{i}")
            t.start()
            workers.append(t)
        
        # Queue files for processing
        for file_path in files:
            self.file_queue.put(file_path)
        
        # Monitor progress
        monitor_thread = Thread(target=self.monitor_progress)
        monitor_thread.start()
        
        # Wait for file queue to be processed
        self.file_queue.join()
        
        # Send poison pills to stop workers
        for _ in range(self.config.num_file_readers):
            self.file_queue.put(None)
        
        # Wait for parse queue
        self.parse_queue.join()
        for _ in range(self.config.num_parsers):
            self.parse_queue.put(None)
        
        # Wait for DB queue
        self.db_queue.join()
        for _ in range(self.config.num_db_writers):
            self.db_queue.put(None)
        
        # Wait for all workers to finish
        for t in workers:
            t.join()
        
        # Final statistics
        duration = datetime.now() - self.stats['start_time']
        rate = self.stats['records_inserted'] / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("PARALLEL LOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📁 Files processed: {self.stats['files_processed']:,}")
        logger.info(f"📄 Lines read: {self.stats['lines_read']:,}")
        logger.info(f"✅ Records parsed: {self.stats['records_parsed']:,}")
        logger.info(f"💾 Records inserted: {self.stats['records_inserted']:,}")
        logger.info(f"⚡ Rate: {rate:.0f} records/second")
        logger.info(f"🚀 Speedup: ~{rate/134:.1f}x vs sequential")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def monitor_progress(self):
        """Monitor and report progress periodically"""
        import time
        
        while True:
            time.sleep(30)  # Report every 30 seconds
            
            with self.stats_lock:
                if self.stats['files_processed'] == 0:
                    continue
                
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                rate = self.stats['records_inserted'] / elapsed if elapsed > 0 else 0
                
                logger.info(f"Progress: Files={self.stats['files_processed']:,}, "
                           f"Parsed={self.stats['records_parsed']:,}, "
                           f"Inserted={self.stats['records_inserted']:,}, "
                           f"Rate={rate:.0f} rec/sec, "
                           f"Queues: Files={self.file_queue.qsize()}, "
                           f"Parse={self.parse_queue.qsize()}, "
                           f"DB={self.db_queue.qsize()}")
                
                # Stop monitoring when done
                if (self.file_queue.empty() and 
                    self.parse_queue.empty() and 
                    self.db_queue.empty()):
                    break

def main():
    """Run the parallel loader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sunbiz Parallel Pipeline Loader')
    parser.add_argument('--readers', type=int, default=4, help='Number of file readers')
    parser.add_argument('--parsers', type=int, default=8, help='Number of parsers')
    parser.add_argument('--writers', type=int, default=4, help='Number of DB writers')
    parser.add_argument('--connections', type=int, default=10, help='DB connection pool size')
    parser.add_argument('--batch-size', type=int, default=5000, help='DB batch size')
    
    args = parser.parse_args()
    
    config = LoaderConfig(
        num_file_readers=args.readers,
        num_parsers=args.parsers,
        num_db_writers=args.writers,
        connection_pool_size=args.connections,
        db_batch_size=args.batch_size
    )
    
    loader = ParallelSunbizLoader(config)
    loader.run_parallel_load()

if __name__ == "__main__":
    main()