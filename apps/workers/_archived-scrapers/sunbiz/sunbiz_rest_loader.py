"""
Sunbiz REST API Loader
High-throughput loader using Supabase REST API with batching
Fallback when direct PostgreSQL access isn't available
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import io
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import aiohttp
from supabase import create_client, Client

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SunbizRESTLoader:
    """High-performance loader using Supabase REST API"""
    
    def __init__(self):
        # Use service role key for data loading (bypasses RLS)
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        # Using service role key from .env
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if service_key:
            self.supabase_key = service_key
            logger.info("✅ Using service role key for data loading")
        else:
            # Hardcoded service role key as fallback
            self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
            logger.info("✅ Using hardcoded service role key for data loading")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        
        # Optimized settings for REST API
        self.batch_size = 1000  # Optimal for REST API
        self.concurrent_batches = 3  # Parallel uploads
        
        self.stats = {
            'files_processed': 0,
            'total_rows': 0,
            'errors': 0,
            'start_time': None
        }
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse YYYYMMDD to YYYY-MM-DD"""
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
        """Parse corporation line to match sunbiz_corporate schema"""
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
            
            doc_number = line[0:12].strip()
            if not doc_number:
                return None
            
            return {
                'doc_number': doc_number,
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
    
    async def insert_batch(self, table_name: str, batch: List[Dict]):
        """Insert batch with retry logic"""
        if not batch:
            return 0
        
        try:
            result = self.supabase.table(table_name).upsert(batch, on_conflict='doc_number').execute()
            
            if result.data:
                return len(batch)
            else:
                logger.error(f"No data returned from {table_name} upsert")
                return 0
                
        except Exception as e:
            logger.error(f"Batch insert error for {table_name}: {e}")
            
            # Try individual inserts for failed batch
            success_count = 0
            for record in batch:
                try:
                    self.supabase.table(table_name).upsert(record, on_conflict='doc_number').execute()
                    success_count += 1
                except:
                    self.stats['errors'] += 1
            
            return success_count
    
    async def process_file(self, file_path: Path, table_name: str, parse_func, batch_log: int = 50000):
        """Process single file"""
        logger.info(f"Processing {file_path.name} → {table_name}")
        
        batch = []
        rows_processed = 0
        rows_inserted = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = parse_func(line)
                    
                    if parsed and parsed.get('doc_number'):
                        # Clean record
                        clean_record = {}
                        for key, value in parsed.items():
                            if value is None:
                                clean_record[key] = None
                            else:
                                clean_record[key] = str(value).strip() if value else None
                        
                        batch.append(clean_record)
                        
                        if len(batch) >= self.batch_size:
                            inserted = await self.insert_batch(table_name, batch)
                            rows_inserted += inserted
                            batch = []
                            
                            if rows_inserted % batch_log == 0:
                                logger.info(f"  Inserted {rows_inserted:,} rows from {file_path.name}")
                    
                    rows_processed += 1
            
            # Insert remaining batch
            if batch:
                inserted = await self.insert_batch(table_name, batch)
                rows_inserted += inserted
            
            logger.info(f"✅ {file_path.name}: {rows_inserted:,} rows inserted from {rows_processed:,} lines")
            return rows_inserted
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def load_corporations(self, file_limit: Optional[int] = None):
        """Load corporation data"""
        logger.info("🏢 Loading corporation data...")
        
        cor_path = self.data_path / "cor"
        if not cor_path.exists():
            logger.error(f"Corporation path not found: {cor_path}")
            return
        
        # Get files
        files = list(cor_path.glob("*.txt"))
        
        # Include year subdirectories
        for year_dir in cor_path.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                files.extend(year_dir.glob("*.txt"))
        
        # Filter and sort
        files = [f for f in files if 'README' not in f.name.upper() and 'WELCOME' not in f.name.upper()]
        files.sort(reverse=True)  # Most recent first
        
        if file_limit:
            files = files[:file_limit]
        
        logger.info(f"Found {len(files)} corporation files")
        
        total_rows = 0
        
        for file_idx, file_path in enumerate(files, 1):
            logger.info(f"\n📁 File {file_idx}/{len(files)}: {file_path.name}")
            
            rows = await self.process_file(file_path, 'sunbiz_corporate', self.parse_corporate_line)
            total_rows += rows
            self.stats['files_processed'] += 1
            
            # Progress update
            if file_idx % 10 == 0:
                logger.info(f"📊 Progress: {file_idx}/{len(files)} files, {total_rows:,} total rows")
        
        self.stats['total_rows'] += total_rows
        logger.info(f"✅ Corporation load complete: {total_rows:,} rows from {len(files)} files")
    
    async def load_fictitious(self, file_limit: Optional[int] = None):
        """Load fictitious names"""
        logger.info("📝 Loading fictitious names...")
        
        fic_path = self.data_path / "fic"
        if not fic_path.exists():
            logger.warning(f"Fictitious path not found: {fic_path}")
            return
        
        files = list(fic_path.glob("*.txt"))
        files = [f for f in files if 'README' not in f.name.upper()]
        
        if file_limit:
            files = files[:file_limit]
        
        logger.info(f"Found {len(files)} fictitious files")
        
        total_rows = 0
        
        for file_idx, file_path in enumerate(files, 1):
            logger.info(f"\n📁 File {file_idx}/{len(files)}: {file_path.name}")
            
            rows = await self.process_file(file_path, 'sunbiz_fictitious', self.parse_fictitious_line)
            total_rows += rows
            self.stats['files_processed'] += 1
        
        self.stats['total_rows'] += total_rows
        logger.info(f"✅ Fictitious load complete: {total_rows:,} rows")
    
    async def run(self, corporate_limit: Optional[int] = None, fictitious_limit: Optional[int] = None):
        """Main execution"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("SUNBIZ REST API LOADER - PRODUCTION")
        logger.info("=" * 60)
        
        try:
            # Load corporations (main dataset)
            await self.load_corporations(corporate_limit)
            
            # Load fictitious names
            await self.load_fictitious(fictitious_limit)
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Load interrupted by user")
        except Exception as e:
            logger.error(f"Load failed: {e}")
        
        duration = datetime.now() - self.stats['start_time']
        rate = self.stats['total_rows'] / duration.total_seconds() if duration.total_seconds() > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("LOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"📁 Files processed: {self.stats['files_processed']:,}")
        logger.info(f"📊 Total rows: {self.stats['total_rows']:,}")
        logger.info(f"⚡ Rate: {rate:.0f} records/second")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sunbiz REST API Loader')
    parser.add_argument('--corp-limit', type=int, help='Limit corporation files (for testing)')
    parser.add_argument('--fic-limit', type=int, help='Limit fictitious files (for testing)')
    
    args = parser.parse_args()
    
    loader = SunbizRESTLoader()
    await loader.run(args.corp_limit, args.fic_limit)

if __name__ == "__main__":
    asyncio.run(main())