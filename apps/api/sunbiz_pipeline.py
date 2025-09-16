"""
Florida Sunbiz Data Pipeline
Automated SFTP download, parsing, and monitoring for Florida business entity data
"""

import os
import json
import paramiko
import logging
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from io import StringIO
import asyncio
import aiofiles
from supabase import create_client, Client
import schedule
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SunbizConfig:
    """Sunbiz SFTP and data configuration"""
    host: str = "sftp.floridados.gov"
    port: int = 22
    username: str = "Public"
    password: str = "PubAccess1845!"
    local_path: str = "./data/sunbiz"
    supabase_url: str = ""
    supabase_key: str = ""
    
    def __post_init__(self):
        # Load from config file
        config_path = Path("sunbiz_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                self.host = config['sftp']['host']
                self.username = config['sftp']['username']
                self.password = config['sftp']['password']

class SunbizSFTPClient:
    """SFTP client for Sunbiz data downloads"""
    
    def __init__(self, config: SunbizConfig):
        self.config = config
        self.transport = None
        self.sftp = None
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary local directories"""
        paths = [
            Path(self.config.local_path),
            Path(self.config.local_path) / "daily",
            Path(self.config.local_path) / "quarterly",
            Path(self.config.local_path) / "processed",
            Path(self.config.local_path) / "archive"
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Establish SFTP connection"""
        try:
            logger.info(f"Connecting to {self.config.host}")
            self.transport = paramiko.Transport((self.config.host, self.config.port))
            self.transport.connect(username=self.config.username, password=self.config.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            logger.info("SFTP connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Close SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()
        logger.info("SFTP connection closed")
    
    def list_daily_files(self, date: datetime = None) -> List[str]:
        """List available daily files for a given date"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y%m%d")
        patterns = [
            f"{date_str}c.txt",     # Corporate filings
            f"{date_str}ce.txt",    # Corporate events
            f"{date_str}flrf.txt",  # Lien filings
            f"{date_str}flre.txt",  # Lien events
            f"{date_str}flrd.txt",  # Lien debtors
            f"{date_str}flrs.txt",  # Lien secured parties
            f"{date_str}f.txt",     # Fictitious name filings
            f"{date_str}fe.txt",    # Fictitious name events
            f"{date_str}g.txt",     # Partnership filings
            f"{date_str}ge.txt",    # Partnership events
            f"{date_str}tm.txt",    # Mark filings
        ]
        
        available_files = []
        try:
            # Check each file pattern
            for pattern in patterns:
                try:
                    self.sftp.stat(pattern)
                    available_files.append(pattern)
                    logger.info(f"Found: {pattern}")
                except FileNotFoundError:
                    pass  # File doesn't exist for this date
        except Exception as e:
            logger.error(f"Error listing files: {e}")
        
        return available_files
    
    def download_file(self, remote_path: str, local_path: str = None) -> Optional[str]:
        """Download a file from SFTP"""
        if local_path is None:
            local_path = Path(self.config.local_path) / "daily" / Path(remote_path).name
        
        try:
            logger.info(f"Downloading {remote_path}")
            self.sftp.get(remote_path, str(local_path))
            
            # Calculate file hash
            with open(local_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            logger.info(f"Downloaded to {local_path} (hash: {file_hash[:8]}...)")
            return str(local_path)
        except Exception as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            return None
    
    def download_quarterly_file(self, filename: str) -> Optional[str]:
        """Download quarterly zip file"""
        local_path = Path(self.config.local_path) / "quarterly" / filename
        
        try:
            logger.info(f"Downloading quarterly file: {filename}")
            self.sftp.get(filename, str(local_path))
            logger.info(f"Downloaded to {local_path}")
            return str(local_path)
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None

class FixedWidthParser:
    """Parser for Sunbiz fixed-width text files"""
    
    # Field definitions for each file type
    FIELD_DEFINITIONS = {
        'corporate': {
            'filing': [
                ('doc_number', 0, 12),
                ('entity_name', 12, 200),
                ('status', 212, 10),
                ('filing_date', 222, 8),
                ('state_country', 230, 50),
                ('prin_addr1', 280, 100),
                ('prin_addr2', 380, 100),
                ('prin_city', 480, 50),
                ('prin_state', 530, 2),
                ('prin_zip', 532, 10),
                ('mail_addr1', 542, 100),
                ('mail_addr2', 642, 100),
                ('mail_city', 742, 50),
                ('mail_state', 792, 2),
                ('mail_zip', 794, 10),
                ('ein', 804, 10),
                ('registered_agent', 814, 100),
            ],
            'event': [
                ('doc_number', 0, 12),
                ('event_date', 12, 8),
                ('event_type', 20, 50),
                ('detail', 70, 200),
            ]
        },
        'fictitious': {
            'filing': [
                ('doc_number', 0, 12),
                ('name', 12, 200),
                ('owner_name', 212, 200),
                ('owner_addr1', 412, 100),
                ('owner_addr2', 512, 100),
                ('owner_city', 612, 50),
                ('owner_state', 662, 2),
                ('owner_zip', 664, 10),
                ('filed_date', 674, 8),
                ('expires_date', 682, 8),
                ('county', 690, 50),
            ],
            'event': [
                ('doc_number', 0, 12),
                ('event_date', 12, 8),
                ('event_type', 20, 50),
            ]
        },
        'lien': {
            'filing': [
                ('doc_number', 0, 12),
                ('lien_type', 12, 20),
                ('filed_date', 32, 8),
                ('lapse_date', 40, 8),
                ('amount', 48, 15),
            ],
            'debtor': [
                ('doc_number', 0, 12),
                ('debtor_name', 12, 200),
                ('debtor_addr', 212, 200),
            ],
            'secured_party': [
                ('doc_number', 0, 12),
                ('party_name', 12, 200),
                ('party_addr', 212, 200),
            ]
        },
        'partnership': {
            'filing': [
                ('doc_number', 0, 12),
                ('name', 12, 200),
                ('status', 212, 10),
                ('filed_date', 222, 8),
                ('prin_addr1', 230, 100),
                ('prin_city', 330, 50),
                ('prin_state', 380, 2),
                ('prin_zip', 382, 10),
            ]
        },
        'mark': [
            ('doc_number', 0, 12),
            ('mark_text', 12, 200),
            ('mark_type', 212, 20),
            ('status', 232, 10),
            ('filed_date', 242, 8),
            ('registration_date', 250, 8),
            ('expiration_date', 258, 8),
            ('owner_name', 266, 200),
            ('owner_addr', 466, 200),
        ]
    }
    
    @staticmethod
    def identify_file_type(filename: str) -> Tuple[str, str]:
        """Identify file type and subtype from filename"""
        fname = Path(filename).stem
        
        if fname.endswith('c'):
            return 'corporate', 'filing'
        elif fname.endswith('ce'):
            return 'corporate', 'event'
        elif fname.endswith('flrf'):
            return 'lien', 'filing'
        elif fname.endswith('flrd'):
            return 'lien', 'debtor'
        elif fname.endswith('flrs'):
            return 'lien', 'secured_party'
        elif fname.endswith('flre'):
            return 'lien', 'event'
        elif fname.endswith('f'):
            return 'fictitious', 'filing'
        elif fname.endswith('fe'):
            return 'fictitious', 'event'
        elif fname.endswith('g'):
            return 'partnership', 'filing'
        elif fname.endswith('ge'):
            return 'partnership', 'event'
        elif fname.endswith('tm'):
            return 'mark', 'filing'
        else:
            return 'unknown', 'unknown'
    
    @staticmethod
    def parse_file(filepath: str) -> pd.DataFrame:
        """Parse a fixed-width file into DataFrame"""
        file_type, subtype = FixedWidthParser.identify_file_type(filepath)
        
        if file_type == 'unknown':
            logger.error(f"Unknown file type: {filepath}")
            return pd.DataFrame()
        
        # Get field definitions
        if file_type == 'mark':
            fields = FixedWidthParser.FIELD_DEFINITIONS['mark']
        else:
            fields = FixedWidthParser.FIELD_DEFINITIONS[file_type].get(subtype, [])
        
        if not fields:
            logger.error(f"No field definitions for {file_type}/{subtype}")
            return pd.DataFrame()
        
        # Parse file
        records = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip():
                        record = {}
                        for field_name, start, end in fields:
                            value = line[start:end].strip()
                            record[field_name] = value
                        records.append(record)
            
            df = pd.DataFrame(records)
            df['file_type'] = file_type
            df['subtype'] = subtype
            df['import_date'] = datetime.now()
            df['source_file'] = Path(filepath).name
            
            logger.info(f"Parsed {len(df)} records from {filepath}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            return pd.DataFrame()

class SunbizMonitoringAgent:
    """Intelligent agent for monitoring Sunbiz data updates"""
    
    def __init__(self, config: SunbizConfig):
        self.config = config
        self.sftp_client = SunbizSFTPClient(config)
        self.parser = FixedWidthParser()
        self.supabase = None
        if config.supabase_url and config.supabase_key:
            self.supabase = create_client(config.supabase_url, config.supabase_key)
        
        # Track processed files
        self.processed_files_path = Path(config.local_path) / "processed_files.json"
        self.processed_files = self.load_processed_files()
    
    def load_processed_files(self) -> set:
        """Load list of already processed files"""
        if self.processed_files_path.exists():
            with open(self.processed_files_path) as f:
                return set(json.load(f))
        return set()
    
    def save_processed_files(self):
        """Save list of processed files"""
        with open(self.processed_files_path, 'w') as f:
            json.dump(list(self.processed_files), f)
    
    async def check_for_updates(self) -> List[str]:
        """Check SFTP for new daily files"""
        logger.info("Checking for Sunbiz updates")
        new_files = []
        
        if self.sftp_client.connect():
            # Check last 7 days for any missed files
            for days_ago in range(7):
                check_date = datetime.now() - timedelta(days=days_ago)
                
                # Skip weekends
                if check_date.weekday() >= 5:
                    continue
                
                available = self.sftp_client.list_daily_files(check_date)
                
                for filename in available:
                    if filename not in self.processed_files:
                        new_files.append(filename)
                        logger.info(f"New file found: {filename}")
            
            self.sftp_client.disconnect()
        
        return new_files
    
    async def process_new_files(self, files: List[str]):
        """Download and process new files"""
        if not files:
            logger.info("No new files to process")
            return
        
        logger.info(f"Processing {len(files)} new files")
        
        if self.sftp_client.connect():
            for filename in files:
                try:
                    # Download file
                    local_path = self.sftp_client.download_file(filename)
                    
                    if local_path:
                        # Parse file
                        df = self.parser.parse_file(local_path)
                        
                        if not df.empty:
                            # Store in database
                            await self.store_in_database(df)
                            
                            # Mark as processed
                            self.processed_files.add(filename)
                            
                            # Archive file
                            self.archive_file(local_path)
                        
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
            
            self.sftp_client.disconnect()
            self.save_processed_files()
    
    async def store_in_database(self, df: pd.DataFrame):
        """Store parsed data in Supabase"""
        if not self.supabase:
            logger.warning("Supabase not configured, skipping database storage")
            return
        
        try:
            file_type = df['file_type'].iloc[0] if not df.empty else 'unknown'
            table_name = f"sunbiz_{file_type}"
            
            # Convert DataFrame to dict records
            records = df.to_dict('records')
            
            # Batch insert (Supabase has a limit)
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                self.supabase.table(table_name).insert(batch).execute()
            
            logger.info(f"Stored {len(records)} records in {table_name}")
            
            # Log to monitoring table
            self.supabase.table('sunbiz_import_log').insert({
                'file_type': file_type,
                'records_imported': len(records),
                'source_file': df['source_file'].iloc[0] if not df.empty else '',
                'import_date': datetime.now().isoformat(),
                'success': True
            }).execute()
            
        except Exception as e:
            logger.error(f"Database storage error: {e}")
    
    def archive_file(self, filepath: str):
        """Move processed file to archive"""
        try:
            archive_path = Path(self.config.local_path) / "archive" / Path(filepath).name
            Path(filepath).rename(archive_path)
            logger.info(f"Archived {filepath}")
        except Exception as e:
            logger.error(f"Archive error: {e}")
    
    async def download_quarterly_data(self, quarter: str = None):
        """Download quarterly snapshot data"""
        if quarter is None:
            # Determine current quarter
            month = datetime.now().month
            quarter = f"{datetime.now().year}Q{((month-1)//3)+1}"
        
        logger.info(f"Downloading quarterly data for {quarter}")
        
        quarterly_files = [
            "cordata.zip", "corevent.zip",
            "flrf.zip", "flre.zip", "flrd.zip", "flrs.zip",
            "ficdata.zip", "ficevt.zip",
            "genfile.zip", "genevt.zip",
            "TMData.zip"
        ]
        
        if self.sftp_client.connect():
            for filename in quarterly_files:
                try:
                    local_path = self.sftp_client.download_quarterly_file(filename)
                    
                    if local_path:
                        # Extract and process
                        await self.process_quarterly_file(local_path)
                        
                except Exception as e:
                    logger.error(f"Error with {filename}: {e}")
            
            self.sftp_client.disconnect()
    
    async def process_quarterly_file(self, zip_path: str):
        """Extract and process quarterly zip file"""
        try:
            extract_dir = Path(self.config.local_path) / "quarterly" / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Process extracted files
            for txt_file in extract_dir.glob("*.txt"):
                df = self.parser.parse_file(str(txt_file))
                if not df.empty:
                    await self.store_in_database(df)
            
            logger.info(f"Processed quarterly file: {zip_path}")
            
        except Exception as e:
            logger.error(f"Quarterly processing error: {e}")
    
    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting Sunbiz monitoring cycle")
        
        try:
            # Check for daily updates
            new_files = await self.check_for_updates()
            
            if new_files:
                logger.info(f"Found {len(new_files)} new files")
                await self.process_new_files(new_files)
                
                # Send notification
                await self.send_notification(f"Processed {len(new_files)} new Sunbiz files")
            else:
                logger.info("No new files found")
            
            # Check if quarterly update needed
            if datetime.now().day == 5:  # Check on 5th of month
                month = datetime.now().month
                if month in [1, 4, 7, 10]:  # Quarterly months
                    await self.download_quarterly_data()
            
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
            await self.send_notification(f"Sunbiz monitoring error: {e}", error=True)
    
    async def send_notification(self, message: str, error: bool = False):
        """Send notification about updates or errors"""
        logger.info(f"Notification: {message}")
        
        if self.supabase:
            self.supabase.table('agent_notifications').insert({
                'agent_name': 'Sunbiz_Monitor',
                'message': message,
                'is_error': error,
                'timestamp': datetime.now().isoformat()
            }).execute()
    
    def start_scheduler(self):
        """Start automated scheduling"""
        # Schedule daily check at 7 AM
        schedule.every().day.at("07:00").do(
            lambda: asyncio.run(self.run_monitoring_cycle())
        )
        
        logger.info("Sunbiz monitoring scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

class SunbizDataAPI:
    """API for accessing Sunbiz data"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def search_corporations(self, name: str = None, doc_number: str = None, 
                                 status: str = None, limit: int = 100):
        """Search corporate entities"""
        query = self.supabase.table('sunbiz_corporate').select('*')
        
        if name:
            query = query.ilike('entity_name', f'%{name}%')
        if doc_number:
            query = query.eq('doc_number', doc_number)
        if status:
            query = query.eq('status', status)
        
        query = query.limit(limit)
        result = query.execute()
        
        return result.data
    
    async def search_fictitious_names(self, name: str = None, owner: str = None,
                                     county: str = None, limit: int = 100):
        """Search fictitious names (DBAs)"""
        query = self.supabase.table('sunbiz_fictitious').select('*')
        
        if name:
            query = query.ilike('name', f'%{name}%')
        if owner:
            query = query.ilike('owner_name', f'%{owner}%')
        if county:
            query = query.eq('county', county)
        
        query = query.limit(limit)
        result = query.execute()
        
        return result.data
    
    async def get_entity_events(self, doc_number: str):
        """Get all events for an entity"""
        result = self.supabase.table('sunbiz_corporate_events').select('*').eq(
            'doc_number', doc_number
        ).order('event_date', desc=True).execute()
        
        return result.data
    
    async def get_recent_filings(self, days: int = 7, file_type: str = None):
        """Get recent filings"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = self.supabase.table('sunbiz_import_log').select('*').gte(
            'import_date', cutoff_date
        )
        
        if file_type:
            query = query.eq('file_type', file_type)
        
        result = query.order('import_date', desc=True).execute()
        
        return result.data


# Main execution
async def main():
    """Main entry point"""
    # Load configuration
    config = SunbizConfig()
    
    # Initialize monitoring agent
    agent = SunbizMonitoringAgent(config)
    
    # Run initial check
    await agent.run_monitoring_cycle()
    
    # Start scheduler for continuous monitoring
    # agent.start_scheduler()  # Uncomment for production


if __name__ == "__main__":
    asyncio.run(main())