"""
Fixed Sunbiz Loader - Uses correct existing table names
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SunbizLoader:
    def __init__(self):
        # Use correct Supabase credentials
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ Supabase client initialized")
        
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.stats = {
            'corporations': 0,
            'fictitious': 0,
            'partnerships': 0,
            'liens': 0,
            'errors': 0
        }
    
    def parse_corporation_line(self, line: str) -> Optional[Dict]:
        """Parse corporation data from fixed-width format"""
        try:
            if len(line.strip()) < 100:
                return None
            
            # Map to existing sunbiz_corporate table structure
            corp = {
                'doc_number': line[0:12].strip(),  # Using doc_number instead of entity_id
                'entity_name': line[12:212].strip()[:255],
                'status': line[212:218].strip(),
                'entity_type': line[218:228].strip(),
                'filing_date': self.parse_date(line[228:236].strip()),
                'state': line[236:238].strip(),
                'principal_address': line[238:338].strip(),
                'principal_city': line[338:388].strip(),
                'principal_state': line[388:390].strip(),
                'principal_zip': line[390:400].strip(),
                'mailing_address': line[400:500].strip() if len(line) > 400 else '',
                'mailing_city': line[500:550].strip() if len(line) > 500 else '',
                'mailing_state': line[550:552].strip() if len(line) > 550 else '',
                'mailing_zip': line[552:562].strip() if len(line) > 552 else '',
                'registered_agent_name': line[562:662].strip() if len(line) > 562 else '',
                'registered_agent_address': line[662:762].strip() if len(line) > 662 else '',
                'ein_number': line[844:854].strip() if len(line) > 844 else '',
                'last_event': line[862:872].strip() if len(line) > 862 else '',
                'event_date': self.parse_date(line[872:880].strip()) if len(line) > 872 else None,
            }
            
            # Only return if we have a valid doc_number
            if corp['doc_number'] and len(corp['doc_number']) >= 6:
                return corp
                
        except Exception as e:
            logger.debug(f"Error parsing line: {e}")
        
        return None
    
    def parse_fictitious_line(self, line: str) -> Optional[Dict]:
        """Parse fictitious name data"""
        try:
            if len(line.strip()) < 50:
                return None
            
            fic = {
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
            
            if fic['doc_number']:
                return fic
                
        except Exception as e:
            logger.debug(f"Error parsing fictitious: {e}")
        
        return None
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date from YYYYMMDD to YYYY-MM-DD"""
        if not date_str or len(date_str) != 8:
            return None
        try:
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            # Validate date components
            if int(year) > 1900 and int(month) <= 12 and int(day) <= 31:
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    async def load_corporations(self, limit: Optional[int] = None):
        """Load corporation data into sunbiz_corporate table"""
        logger.info("🏢 Loading corporation data...")
        
        cor_path = self.data_path / "cor"
        if not cor_path.exists():
            logger.error(f"Corporation path not found: {cor_path}")
            return
        
        # Get recent files
        txt_files = list(cor_path.glob("2025*.txt"))[:10]  # Start with recent files
        
        if not txt_files:
            txt_files = list(cor_path.glob("*.txt"))[:10]
        
        logger.info(f"Processing {len(txt_files)} corporation files")
        
        batch = []
        batch_size = 100  # Smaller batches for testing
        total_loaded = 0
        
        for file_idx, file_path in enumerate(txt_files):
            if limit and total_loaded >= limit:
                break
                
            logger.info(f"Processing {file_path.name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f):
                        if limit and total_loaded >= limit:
                            break
                        
                        corp = self.parse_corporation_line(line)
                        if corp:
                            batch.append(corp)
                            
                            if len(batch) >= batch_size:
                                try:
                                    # Insert into sunbiz_corporate (not corporations)
                                    self.supabase.table('sunbiz_corporate').upsert(batch).execute()
                                    self.stats['corporations'] += len(batch)
                                    total_loaded += len(batch)
                                    logger.info(f"  Loaded {total_loaded} corporations")
                                    batch = []
                                except Exception as e:
                                    logger.error(f"Batch insert error: {e}")
                                    self.stats['errors'] += 1
                                    batch = []
                        
                        if line_num > 0 and line_num % 1000 == 0:
                            logger.info(f"  Processed {line_num} lines")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Insert remaining batch
        if batch:
            try:
                self.supabase.table('sunbiz_corporate').upsert(batch).execute()
                self.stats['corporations'] += len(batch)
                total_loaded += len(batch)
            except Exception as e:
                logger.error(f"Final batch error: {e}")
        
        logger.info(f"✅ Loaded {self.stats['corporations']} corporations")
    
    async def load_fictitious_names(self, limit: Optional[int] = None):
        """Load fictitious names into sunbiz_fictitious table"""
        logger.info("📝 Loading fictitious names...")
        
        fic_path = self.data_path / "fic"
        if not fic_path.exists():
            logger.warning(f"Fictitious path not found: {fic_path}")
            return
        
        txt_files = list(fic_path.glob("*.txt"))[:5]  # Start with a few files
        logger.info(f"Processing {len(txt_files)} fictitious files")
        
        batch = []
        batch_size = 100
        total_loaded = 0
        
        for file_path in txt_files:
            if limit and total_loaded >= limit:
                break
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if limit and total_loaded >= limit:
                            break
                        
                        fic = self.parse_fictitious_line(line)
                        if fic:
                            batch.append(fic)
                            
                            if len(batch) >= batch_size:
                                try:
                                    self.supabase.table('sunbiz_fictitious').upsert(batch).execute()
                                    self.stats['fictitious'] += len(batch)
                                    total_loaded += len(batch)
                                    batch = []
                                except Exception as e:
                                    logger.error(f"Batch insert error: {e}")
                                    self.stats['errors'] += 1
                                    batch = []
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        if batch:
            try:
                self.supabase.table('sunbiz_fictitious').upsert(batch).execute()
                self.stats['fictitious'] += len(batch)
            except:
                pass
        
        logger.info(f"✅ Loaded {self.stats['fictitious']} fictitious names")
    
    async def run(self):
        """Main execution"""
        logger.info("=" * 60)
        logger.info("SUNBIZ DATA LOADER - FIXED VERSION")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Load with limits for testing
        await self.load_corporations(limit=5000)  # Load 5000 corps first
        await self.load_fictitious_names(limit=1000)  # Load 1000 fictitious
        
        duration = datetime.now() - start_time
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("LOADING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"🏢 Corporations: {self.stats['corporations']:,}")
        logger.info(f"📝 Fictitious Names: {self.stats['fictitious']:,}")
        logger.info(f"📊 Total Records: {self.stats['corporations'] + self.stats['fictitious']:,}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        logger.info("\n✅ Initial load complete!")
        logger.info("To load ALL data, remove the limit parameters and run again")

async def main():
    loader = SunbizLoader()
    await loader.run()

if __name__ == "__main__":
    asyncio.run(main())