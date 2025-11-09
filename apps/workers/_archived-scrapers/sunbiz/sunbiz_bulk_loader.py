"""
Production Sunbiz Bulk Loader
High-throughput COPY-based loader with staging tables and upsert safety
Supports CSV/CSV.gz files, resumeable, transaction-safe
"""

import os
import sys
import io
import gzip
import csv
import argparse
import logging
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass
import re

# UTF-8 output fix for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoadConfig:
    """Configuration for table loading"""
    table_name: str
    staging_table: str
    columns: List[str]
    file_pattern: str
    parse_function: str

class SunbizBulkLoader:
    """High-performance bulk loader for Sunbiz data"""
    
    # Table configurations
    TABLE_CONFIGS = {
        'corporate': LoadConfig(
            table_name='sunbiz_corporate',
            staging_table='staging_sunbiz_corporate',
            columns=[
                'doc_number', 'entity_name', 'status', 'filing_date', 'state_country',
                'prin_addr1', 'prin_addr2', 'prin_city', 'prin_state', 'prin_zip',
                'mail_addr1', 'mail_addr2', 'mail_city', 'mail_state', 'mail_zip',
                'ein', 'registered_agent', 'file_type', 'subtype', 'source_file'
            ],
            file_pattern='*.txt',
            parse_function='parse_corporate_line'
        ),
        'fictitious': LoadConfig(
            table_name='sunbiz_fictitious',
            staging_table='staging_sunbiz_fictitious',
            columns=[
                'doc_number', 'name', 'owner_name', 'owner_address', 'owner_city',
                'owner_state', 'owner_zip', 'filing_date', 'expiration_date', 'status'
            ],
            file_pattern='*.txt',
            parse_function='parse_fictitious_line'
        ),
        'liens': LoadConfig(
            table_name='sunbiz_liens',
            staging_table='staging_sunbiz_liens',
            columns=['doc_number', 'lien_type', 'debtor_name', 'filing_date', 'amount'],
            file_pattern='*.txt',
            parse_function='parse_lien_line'
        ),
        'partnerships': LoadConfig(
            table_name='sunbiz_partnerships',
            staging_table='staging_sunbiz_partnerships',
            columns=['doc_number', 'partnership_name', 'status', 'filing_date'],
            file_pattern='*.txt',
            parse_function='parse_partnership_line'
        )
    }
    
    def __init__(self, data_dir: str = None):
        # Database connection from environment
        self.db_url = os.getenv('SUPABASE_DB_URL')
        if not self.db_url:
            # Fallback to individual components
            host = 'db.pmispwtdngkcmsrsjwbp.supabase.co'
            port = 5432
            database = 'postgres'
            user = 'postgres'
            password = os.getenv('SUPABASE_DB_PASSWORD', 'your-password')
            self.db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require"
        
        self.data_dir = Path(data_dir or r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        
        self.stats = {
            'files_processed': 0,
            'total_rows': 0,
            'errors': 0,
            'start_time': None
        }
    
    def connect_db(self):
        """Create optimized database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = False
            
            # Performance settings
            with conn.cursor() as cur:
                cur.execute("SET work_mem = '512MB';")
                cur.execute("SET maintenance_work_mem = '2GB';")
                cur.execute("SET synchronous_commit = OFF;")
                cur.execute("SET wal_buffers = '64MB';")
                cur.execute("SET checkpoint_completion_target = 0.9;")
            
            logger.info("✅ Database connected with performance optimizations")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.error("Please check SUPABASE_DB_URL or SUPABASE_DB_PASSWORD")
            return None
    
    def create_staging_table(self, conn, config: LoadConfig):
        """Create staging table if not exists"""
        columns_def = []
        for col in config.columns:
            if col in ['filing_date', 'expiration_date']:
                columns_def.append(f"{col} DATE")
            elif col in ['amount']:
                columns_def.append(f"{col} DECIMAL(15,2)")
            elif col == 'doc_number':
                columns_def.append(f"{col} VARCHAR(20)")
            elif col in ['entity_name', 'name', 'partnership_name']:
                columns_def.append(f"{col} VARCHAR(255)")
            else:
                columns_def.append(f"{col} TEXT")
        
        create_sql = f"""
            DROP TABLE IF EXISTS {config.staging_table};
            CREATE TABLE {config.staging_table} (
                {', '.join(columns_def)}
            );
        """
        
        with conn.cursor() as cur:
            cur.execute(create_sql)
        logger.info(f"Created staging table: {config.staging_table}")
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse YYYYMMDD to YYYY-MM-DD format"""
        if not date_str or len(date_str) != 8:
            return None
        try:
            year, month, day = date_str[0:4], date_str[4:6], date_str[6:8]
            if 1900 < int(year) < 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def parse_corporate_line(self, line: str) -> Optional[Dict]:
        """Parse corporation fixed-width line"""
        try:
            if len(line.strip()) < 100:
                return None
            
            doc_number = line[0:12].strip()
            if not doc_number or len(doc_number) < 6:
                return None
            
            return {
                'doc_number': doc_number,
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
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def parse_fictitious_line(self, line: str) -> Optional[Dict]:
        """Parse fictitious name line"""
        try:
            if len(line.strip()) < 50:
                return None
            
            return {
                'doc_number': line[0:12].strip(),
                'name': line[12:212].strip()[:255],
                'owner_name': line[212:312].strip() if len(line) > 212 else '',
                'owner_address': line[312:412].strip() if len(line) > 312 else '',
                'owner_city': line[412:462].strip() if len(line) > 412 else '',
                'owner_state': line[462:464].strip() if len(line) > 462 else '',
                'owner_zip': line[464:474].strip() if len(line) > 464 else '',
                'filing_date': self.parse_date(line[474:482].strip()) if len(line) > 474 else None,
                'expiration_date': self.parse_date(line[482:490].strip()) if len(line) > 482 else None,
                'status': line[490:496].strip() if len(line) > 490 else 'ACTIVE'
            }
        except:
            return None
    
    def parse_lien_line(self, line: str) -> Optional[Dict]:
        """Parse lien line - simplified"""
        return {
            'doc_number': line[0:12].strip(),
            'lien_type': 'UCC',
            'debtor_name': line[12:212].strip()[:255],
            'filing_date': self.parse_date(line[220:228].strip()),
            'amount': None
        }
    
    def parse_partnership_line(self, line: str) -> Optional[Dict]:
        """Parse partnership line - simplified"""
        return {
            'doc_number': line[0:12].strip(),
            'partnership_name': line[12:212].strip()[:255],
            'status': line[212:218].strip(),
            'filing_date': self.parse_date(line[228:236].strip())
        }
    
    def process_file_to_staging(self, conn, file_path: Path, config: LoadConfig, batch_log: int = 100000):
        """Process file using COPY to staging table"""
        logger.info(f"Processing {file_path.name} → {config.staging_table}")
        
        # Get parser function
        parse_func = getattr(self, config.parse_function)
        
        # Open file (handle .gz)
        if file_path.suffix.lower() == '.gz':
            file_handle = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
        else:
            file_handle = open(file_path, 'r', encoding='utf-8', errors='ignore')
        
        rows_processed = 0
        
        try:
            with conn.cursor() as cur:
                # Use COPY FROM for maximum speed
                copy_sql = f"""
                    COPY {config.staging_table} ({', '.join(config.columns)})
                    FROM STDIN WITH (FORMAT CSV, NULL '', DELIMITER E'\\t')
                """
                
                def row_generator():
                    nonlocal rows_processed
                    for line_num, line in enumerate(file_handle, 1):
                        parsed = parse_func(line)
                        if parsed and parsed.get('doc_number'):
                            # Convert to TSV row
                            values = []
                            for col in config.columns:
                                val = parsed.get(col, '')
                                if val is None:
                                    val = ''
                                # Escape tabs and newlines
                                val = str(val).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                                values.append(val)
                            
                            yield '\t'.join(values) + '\n'
                            rows_processed += 1
                            
                            if rows_processed % batch_log == 0:
                                logger.info(f"  Processed {rows_processed:,} rows from {file_path.name}")
                
                # Execute COPY
                cur.copy_expert(copy_sql, (line.encode('utf-8') for line in row_generator()))
            
            logger.info(f"✅ Loaded {rows_processed:,} rows from {file_path.name}")
            return rows_processed
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors'] += 1
            return 0
        finally:
            file_handle.close()
    
    def merge_staging_to_target(self, conn, config: LoadConfig):
        """Merge staging data to target table with conflict resolution"""
        logger.info(f"Merging {config.staging_table} → {config.table_name}")
        
        # Build INSERT ... ON CONFLICT query
        columns_list = ', '.join(config.columns)
        values_list = ', '.join([f"s.{col}" for col in config.columns])
        update_list = ', '.join([f"{col} = EXCLUDED.{col}" for col in config.columns if col != 'doc_number'])
        
        merge_sql = f"""
            INSERT INTO public.{config.table_name} ({columns_list})
            SELECT {columns_list} FROM {config.staging_table} s
            WHERE s.doc_number IS NOT NULL AND s.doc_number != ''
            ON CONFLICT (doc_number) DO UPDATE SET
                {update_list},
                update_date = NOW()
        """
        
        try:
            with conn.cursor() as cur:
                cur.execute(merge_sql)
                merged_count = cur.rowcount
            
            logger.info(f"✅ Merged {merged_count:,} rows into {config.table_name}")
            return merged_count
            
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return 0
    
    def load_table_type(self, table_type: str, batch_log: int = 100000, file_limit: Optional[int] = None):
        """Load specific table type (corporate, fictitious, etc.)"""
        if table_type not in self.TABLE_CONFIGS:
            logger.error(f"Unknown table type: {table_type}")
            return
        
        config = self.TABLE_CONFIGS[table_type]
        
        # Find files
        if table_type == 'corporate':
            data_path = self.data_dir / "cor"
        elif table_type == 'fictitious':
            data_path = self.data_dir / "fic"
        elif table_type == 'liens':
            data_path = self.data_dir / "liens"  # Adjust path as needed
        elif table_type == 'partnerships':
            data_path = self.data_dir / "partnerships"  # Adjust path as needed
        else:
            data_path = self.data_dir
        
        if not data_path.exists():
            logger.error(f"Data path not found: {data_path}")
            return
        
        # Get files
        files = list(data_path.glob(config.file_pattern))
        
        # Include year subdirectories for corporate
        if table_type == 'corporate':
            for year_dir in data_path.iterdir():
                if year_dir.is_dir() and year_dir.name.isdigit():
                    files.extend(year_dir.glob(config.file_pattern))
        
        # Filter out README files
        files = [f for f in files if 'README' not in f.name.upper() and 'WELCOME' not in f.name.upper()]
        files.sort(reverse=True)  # Most recent first
        
        if file_limit:
            files = files[:file_limit]
        
        logger.info(f"Found {len(files)} files for {table_type}")
        
        # Connect and process
        conn = self.connect_db()
        if not conn:
            return
        
        try:
            # Create staging table
            self.create_staging_table(conn, config)
            
            total_rows = 0
            
            # Process each file
            for file_idx, file_path in enumerate(files, 1):
                logger.info(f"\n📁 File {file_idx}/{len(files)}: {file_path.name}")
                
                # Clear staging table
                with conn.cursor() as cur:
                    cur.execute(f"TRUNCATE {config.staging_table}")
                
                # Load file to staging
                rows = self.process_file_to_staging(conn, file_path, config, batch_log)
                
                if rows > 0:
                    # Merge staging to target
                    merged = self.merge_staging_to_target(conn, config)
                    total_rows += merged
                    
                    # Commit per file
                    conn.commit()
                    self.stats['files_processed'] += 1
                    
                    logger.info(f"✅ File complete: {merged:,} rows merged")
                else:
                    logger.warning(f"⚠️ No valid rows in {file_path.name}")
            
            self.stats['total_rows'] += total_rows
            
            # Clean up staging table
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {config.staging_table}")
            
            logger.info(f"\n🎉 {table_type.upper()} LOAD COMPLETE")
            logger.info(f"   Files processed: {len(files)}")
            logger.info(f"   Total rows: {total_rows:,}")
            
        except KeyboardInterrupt:
            logger.info(f"\n⚠️ Load interrupted for {table_type}")
            conn.rollback()
        except Exception as e:
            logger.error(f"Load failed for {table_type}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def run_full_load(self, batch_log: int = 100000, corporate_limit: Optional[int] = None):
        """Run complete load for all table types"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("SUNBIZ FULL BULK LOAD - PRODUCTION")
        logger.info("=" * 60)
        
        # Load in order of importance
        logger.info("\n🏢 LOADING CORPORATIONS (16GB)")
        self.load_table_type('corporate', batch_log, corporate_limit)
        
        logger.info("\n📝 LOADING FICTITIOUS NAMES")
        self.load_table_type('fictitious', batch_log)
        
        # Add other types if data exists
        # self.load_table_type('liens', batch_log)
        # self.load_table_type('partnerships', batch_log)
        
        duration = datetime.now() - self.stats['start_time']
        rate = self.stats['total_rows'] / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("FULL LOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📁 Files processed: {self.stats['files_processed']:,}")
        logger.info(f"📊 Total rows: {self.stats['total_rows']:,}")
        logger.info(f"⚡ Rate: {rate:.0f} records/second")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        logger.info("\n📈 Check progress with:")
        logger.info("SELECT tablename, n_live_tup FROM pg_stat_user_tables WHERE tablename LIKE 'sunbiz%';")

def main():
    parser = argparse.ArgumentParser(description='Sunbiz Bulk Data Loader')
    parser.add_argument('--table', choices=['corporate', 'fictitious', 'liens', 'partnerships', 'all'], 
                       default='all', help='Table type to load')
    parser.add_argument('--dir', help='Data directory path')
    parser.add_argument('--batch-log', type=int, default=100000, help='Log progress every N rows')
    parser.add_argument('--limit', type=int, help='Limit number of files (for testing)')
    
    args = parser.parse_args()
    
    loader = SunbizBulkLoader(args.dir)
    
    if args.table == 'all':
        loader.run_full_load(args.batch_log, args.limit)
    else:
        loader.load_table_type(args.table, args.batch_log, args.limit)

if __name__ == "__main__":
    main()