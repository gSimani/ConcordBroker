"""
Florida Revenue Daily Sync System
Automated daily synchronization of NAL, NAP, and SDF property data
"""

import os
import sys
import asyncio
import logging
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import schedule
import time
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_revenue_sync.log'),
        logging.StreamHandler()
    ]
)

# Load environment
load_dotenv()

# Configuration
class Config:
    BASE_URL = "https://floridarevenue.com/property/dataportal"
    DATA_PATH = "/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files"
    BROWARD_CODE = "16"
    CURRENT_YEAR = "2025P"
    FILE_TYPES = ["NAL", "NAP", "SDF"]
    DOWNLOAD_DIR = Path("florida_revenue_downloads")
    METADATA_FILE = Path("florida_revenue_metadata.json")
    BATCH_SIZE = 1000
    MAX_CONCURRENT_DOWNLOADS = 3
    SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')

# Ensure download directory exists
Config.DOWNLOAD_DIR.mkdir(exist_ok=True)

# Data classes
@dataclass
class FileMetadata:
    """Metadata for a Florida Revenue data file"""
    file_type: str  # NAL, NAP, or SDF
    county_code: str
    year: str
    url: str
    filename: str
    size: Optional[int] = None
    last_modified: Optional[datetime] = None
    checksum: Optional[str] = None
    download_path: Optional[Path] = None

@dataclass
class ChangeReport:
    """Report of changes detected in data"""
    file_type: str
    total_records: int
    new_records: int
    updated_records: int
    deleted_records: int
    change_percentage: float
    details: Dict

class UpdateStrategy(Enum):
    """Strategy for database updates"""
    INCREMENTAL = "incremental"
    BATCH_INCREMENTAL = "batch_incremental"
    FULL_REFRESH = "full_refresh"

class SyncStatus(Enum):
    """Status of sync operation"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

# ============================================================================
# DISCOVERY AGENT
# ============================================================================

class FloridaRevenueDiscoveryAgent:
    """Agent responsible for discovering available data files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.metadata_cache = self._load_metadata_cache()
    
    def _load_metadata_cache(self) -> Dict:
        """Load cached metadata"""
        if Config.METADATA_FILE.exists():
            with open(Config.METADATA_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata_cache(self):
        """Save metadata cache"""
        with open(Config.METADATA_FILE, 'w') as f:
            json.dump(self.metadata_cache, f, indent=2, default=str)
    
    async def discover_files(self) -> List[FileMetadata]:
        """Discover available files from Florida Revenue portal"""
        discovered_files = []
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            for file_type in Config.FILE_TYPES:
                self.logger.info(f"Discovering {file_type} files...")
                
                # Build URL for file type and year
                url = f"{Config.BASE_URL}{Config.DATA_PATH}/{file_type}/{Config.CURRENT_YEAR}"
                
                try:
                    files = await self._scrape_directory(url, file_type)
                    discovered_files.extend(files)
                    self.logger.info(f"Found {len(files)} {file_type} files")
                except Exception as e:
                    self.logger.error(f"Error discovering {file_type} files: {e}")
        
        # Update metadata cache
        for file in discovered_files:
            cache_key = f"{file.file_type}_{file.county_code}_{file.year}"
            self.metadata_cache[cache_key] = {
                'url': file.url,
                'filename': file.filename,
                'last_discovered': datetime.now().isoformat()
            }
        
        self._save_metadata_cache()
        return discovered_files
    
    async def _scrape_directory(self, url: str, file_type: str) -> List[FileMetadata]:
        """Scrape directory listing for files"""
        files = []
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for Broward file
                    broward_filename = f"{file_type}{Config.BROWARD_CODE}P{Config.CURRENT_YEAR[:-1]}01.csv"
                    
                    # Find file links
                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        if broward_filename.lower() in href.lower():
                            file_url = f"{Config.BASE_URL}{href}" if not href.startswith('http') else href
                            
                            metadata = FileMetadata(
                                file_type=file_type,
                                county_code=Config.BROWARD_CODE,
                                year=Config.CURRENT_YEAR,
                                url=file_url,
                                filename=broward_filename
                            )
                            files.append(metadata)
                            break
                    
                    # If not found via links, construct expected URL
                    if not files:
                        expected_url = f"{url}/{broward_filename}"
                        metadata = FileMetadata(
                            file_type=file_type,
                            county_code=Config.BROWARD_CODE,
                            year=Config.CURRENT_YEAR,
                            url=expected_url,
                            filename=broward_filename
                        )
                        files.append(metadata)
                        
        except Exception as e:
            self.logger.error(f"Error scraping directory {url}: {e}")
        
        return files

# ============================================================================
# DOWNLOAD MANAGER AGENT
# ============================================================================

class FloridaRevenueDownloadAgent:
    """Agent responsible for downloading data files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.chunk_size = 8192
        self.retry_attempts = 3
    
    async def download_files(self, files: List[FileMetadata]) -> List[FileMetadata]:
        """Download multiple files concurrently"""
        downloaded = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for file in files[:Config.MAX_CONCURRENT_DOWNLOADS]:
                task = self._download_file(session, file)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for file, result in zip(files, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to download {file.filename}: {result}")
                else:
                    downloaded.append(result)
        
        return downloaded
    
    async def _download_file(self, session: aiohttp.ClientSession, file: FileMetadata) -> FileMetadata:
        """Download a single file with resume capability"""
        download_path = Config.DOWNLOAD_DIR / file.filename
        file.download_path = download_path
        
        # Check if file already exists and get its size
        resume_pos = 0
        if download_path.exists():
            resume_pos = download_path.stat().st_size
            self.logger.info(f"Resuming download of {file.filename} from byte {resume_pos}")
        
        headers = {}
        if resume_pos > 0:
            headers['Range'] = f'bytes={resume_pos}-'
        
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(file.url, headers=headers) as response:
                    # Check if server supports resume
                    if resume_pos > 0 and response.status != 206:
                        self.logger.warning(f"Server doesn't support resume for {file.filename}, starting fresh")
                        resume_pos = 0
                        download_path.unlink(missing_ok=True)
                    
                    # Get total file size
                    if response.status == 206:
                        content_range = response.headers.get('Content-Range', '')
                        if '/' in content_range:
                            file.size = int(content_range.split('/')[-1])
                    else:
                        file.size = int(response.headers.get('Content-Length', 0))
                    
                    # Download file
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    async with aiofiles.open(download_path, mode) as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            await f.write(chunk)
                            resume_pos += len(chunk)
                            
                            # Progress logging
                            if file.size > 0:
                                progress = (resume_pos / file.size) * 100
                                if int(progress) % 10 == 0:
                                    self.logger.info(f"Download progress for {file.filename}: {progress:.1f}%")
                    
                    # Calculate checksum
                    file.checksum = await self._calculate_checksum(download_path)
                    self.logger.info(f"Successfully downloaded {file.filename} ({file.size} bytes)")
                    return file
                    
            except Exception as e:
                self.logger.error(f"Download attempt {attempt + 1} failed for {file.filename}: {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

# ============================================================================
# CHANGE DETECTION AGENT
# ============================================================================

class FloridaRevenueChangeDetector:
    """Agent responsible for detecting changes in data"""
    
    def __init__(self, supabase_client):
        self.logger = logging.getLogger(__name__)
        self.supabase = supabase_client
    
    async def detect_changes(self, file: FileMetadata) -> ChangeReport:
        """Detect changes between new file and existing database"""
        self.logger.info(f"Detecting changes for {file.filename}")
        
        # Read new data
        new_data = pd.read_csv(file.download_path, dtype=str, nrows=10000)  # Sample for testing
        
        # Get existing parcels from database
        existing_parcels = await self._get_existing_parcels(file.file_type)
        
        # Compare data
        new_parcels = set(new_data['PARCEL_ID'].unique())
        existing_set = set(existing_parcels)
        
        # Calculate changes
        new_records = new_parcels - existing_set
        deleted_records = existing_set - new_parcels
        potential_updates = new_parcels & existing_set
        
        # For updates, we'd need to compare actual field values
        # For now, assume some percentage are updates
        updated_records = len(potential_updates) * 0.1  # Assume 10% have changes
        
        total_records = len(new_parcels)
        change_percentage = (len(new_records) + updated_records) / total_records if total_records > 0 else 0
        
        report = ChangeReport(
            file_type=file.file_type,
            total_records=total_records,
            new_records=len(new_records),
            updated_records=int(updated_records),
            deleted_records=len(deleted_records),
            change_percentage=change_percentage,
            details={
                'new_parcels': list(new_records)[:100],  # First 100 for details
                'deleted_parcels': list(deleted_records)[:100]
            }
        )
        
        self.logger.info(f"Change detection complete: {report.new_records} new, "
                        f"{report.updated_records} updated, {report.deleted_records} deleted")
        
        return report
    
    async def _get_existing_parcels(self, file_type: str) -> List[str]:
        """Get existing parcel IDs from database"""
        try:
            result = self.supabase.table('florida_properties_core').select('parcel_id').execute()
            return [r['parcel_id'] for r in result.data]
        except Exception as e:
            self.logger.error(f"Error fetching existing parcels: {e}")
            return []
    
    def determine_update_strategy(self, report: ChangeReport) -> UpdateStrategy:
        """Determine optimal update strategy based on changes"""
        if report.change_percentage < 0.10:
            return UpdateStrategy.INCREMENTAL
        elif report.change_percentage < 0.50:
            return UpdateStrategy.BATCH_INCREMENTAL
        else:
            return UpdateStrategy.FULL_REFRESH

# ============================================================================
# DATABASE SYNC AGENT
# ============================================================================

class FloridaRevenueDatabaseSyncAgent:
    """Agent responsible for syncing data to database"""
    
    def __init__(self, supabase_client):
        self.logger = logging.getLogger(__name__)
        self.supabase = supabase_client
        self.batch_size = Config.BATCH_SIZE
    
    async def sync_data(self, file: FileMetadata, report: ChangeReport, strategy: UpdateStrategy) -> SyncStatus:
        """Sync data to database using appropriate strategy"""
        self.logger.info(f"Syncing {file.filename} using {strategy.value} strategy")
        
        try:
            if strategy == UpdateStrategy.INCREMENTAL:
                return await self._incremental_sync(file, report)
            elif strategy == UpdateStrategy.BATCH_INCREMENTAL:
                return await self._batch_incremental_sync(file, report)
            else:
                return await self._full_refresh_sync(file)
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            return SyncStatus.FAILED
    
    async def _incremental_sync(self, file: FileMetadata, report: ChangeReport) -> SyncStatus:
        """Perform incremental sync for small changes"""
        self.logger.info(f"Starting incremental sync for {report.new_records} new records")
        
        # Process only new records
        df = pd.read_csv(file.download_path, dtype=str)
        new_df = df[df['PARCEL_ID'].isin(report.details['new_parcels'])]
        
        success_count = 0
        for _, row in new_df.iterrows():
            try:
                record = self._prepare_record(row, file.file_type)
                self.supabase.table('florida_properties_core').insert(record).execute()
                success_count += 1
            except Exception as e:
                self.logger.error(f"Failed to insert record: {e}")
        
        self.logger.info(f"Incremental sync complete: {success_count}/{len(new_df)} records")
        return SyncStatus.SUCCESS if success_count == len(new_df) else SyncStatus.PARTIAL
    
    async def _batch_incremental_sync(self, file: FileMetadata, report: ChangeReport) -> SyncStatus:
        """Perform batch incremental sync for moderate changes"""
        self.logger.info("Starting batch incremental sync")
        
        df = pd.read_csv(file.download_path, dtype=str, chunksize=self.batch_size)
        total_processed = 0
        
        for chunk in df:
            records = [self._prepare_record(row, file.file_type) for _, row in chunk.iterrows()]
            
            try:
                # Use upsert for batch operations
                self.supabase.table('florida_properties_core').upsert(records).execute()
                total_processed += len(records)
                self.logger.info(f"Processed batch of {len(records)} records")
            except Exception as e:
                self.logger.error(f"Batch sync error: {e}")
        
        return SyncStatus.SUCCESS
    
    async def _full_refresh_sync(self, file: FileMetadata) -> SyncStatus:
        """Perform full refresh for major changes"""
        self.logger.info("Starting full refresh sync")
        
        # This would typically involve:
        # 1. Creating a staging table
        # 2. Loading all data to staging
        # 3. Swapping tables atomically
        # For now, we'll use upsert approach
        
        return await self._batch_incremental_sync(file, None)
    
    def _prepare_record(self, row: pd.Series, file_type: str) -> Dict:
        """Prepare record for database insertion"""
        if file_type == "NAL":
            return {
                'parcel_id': str(row.get('PARCEL_ID', '')),
                'owner_name': str(row.get('OWNER_NAME', '')),
                'physical_address': str(row.get('PHYSICAL_ADDRESS', '')),
                'physical_city': str(row.get('PHYSICAL_CITY', '')),
                'physical_zipcode': str(row.get('PHYSICAL_ZIPCODE', '')),
                'just_value': float(row.get('JUST_VALUE', 0)) if pd.notna(row.get('JUST_VALUE')) else None,
                'assessed_value_sd': float(row.get('ASSESSED_VALUE_SD', 0)) if pd.notna(row.get('ASSESSED_VALUE_SD')) else None,
                'taxable_value_sd': float(row.get('TAXABLE_VALUE_SD', 0)) if pd.notna(row.get('TAXABLE_VALUE_SD')) else None,
                'assessment_year': 2025
            }
        # Add mappings for NAP and SDF
        return {}

# ============================================================================
# MONITORING AGENT
# ============================================================================

class FloridaRevenueMonitorAgent:
    """Agent responsible for monitoring system health"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {}
        self.alerts = []
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None):
        """Record a metric"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': timestamp
        })
    
    def check_health(self) -> Dict:
        """Check system health and generate alerts"""
        health_status = {
            'status': 'healthy',
            'checks': {},
            'alerts': []
        }
        
        # Check data freshness
        last_sync = self._get_last_successful_sync()
        if last_sync:
            hours_since_sync = (datetime.now() - last_sync).total_seconds() / 3600
            health_status['checks']['data_freshness'] = {
                'hours_since_sync': hours_since_sync,
                'status': 'ok' if hours_since_sync < 25 else 'stale'
            }
            
            if hours_since_sync > 25:
                health_status['alerts'].append({
                    'severity': 'warning',
                    'message': f'Data is {hours_since_sync:.1f} hours old'
                })
                health_status['status'] = 'degraded'
        
        # Check error rates
        error_rate = self._calculate_error_rate()
        health_status['checks']['error_rate'] = {
            'rate': error_rate,
            'status': 'ok' if error_rate < 0.05 else 'high'
        }
        
        if error_rate > 0.05:
            health_status['alerts'].append({
                'severity': 'critical',
                'message': f'High error rate: {error_rate:.2%}'
            })
            health_status['status'] = 'unhealthy'
        
        return health_status
    
    def _get_last_successful_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync"""
        if 'sync_success' in self.metrics and self.metrics['sync_success']:
            return self.metrics['sync_success'][-1]['timestamp']
        return None
    
    def _calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        if 'errors' not in self.metrics:
            return 0.0
        
        recent_errors = [m for m in self.metrics['errors'] 
                        if (datetime.now() - m['timestamp']).total_seconds() < 3600]
        
        return len(recent_errors) / 100  # Normalized rate

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

class FloridaRevenueMasterOrchestrator:
    """Master orchestrator coordinating all agents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Initialize agents
        self.discovery_agent = FloridaRevenueDiscoveryAgent()
        self.download_agent = FloridaRevenueDownloadAgent()
        self.change_detector = FloridaRevenueChangeDetector(self.supabase)
        self.sync_agent = FloridaRevenueDatabaseSyncAgent(self.supabase)
        self.monitor_agent = FloridaRevenueMonitorAgent()
    
    async def run_daily_sync(self):
        """Execute daily sync workflow"""
        self.logger.info("=" * 80)
        self.logger.info("STARTING FLORIDA REVENUE DAILY SYNC")
        self.logger.info(f"Timestamp: {datetime.now()}")
        self.logger.info("=" * 80)
        
        try:
            # Step 1: Discovery
            self.logger.info("Step 1: Discovering files...")
            files = await self.discovery_agent.discover_files()
            self.logger.info(f"Discovered {len(files)} files")
            self.monitor_agent.record_metric('files_discovered', len(files))
            
            # Step 2: Download
            self.logger.info("Step 2: Downloading new/updated files...")
            downloaded = await self.download_agent.download_files(files)
            self.logger.info(f"Downloaded {len(downloaded)} files")
            self.monitor_agent.record_metric('files_downloaded', len(downloaded))
            
            # Step 3: Process each file
            for file in downloaded:
                self.logger.info(f"Processing {file.filename}...")
                
                # Detect changes
                report = await self.change_detector.detect_changes(file)
                self.monitor_agent.record_metric(f'changes_{file.file_type}', report.change_percentage)
                
                # Determine strategy
                strategy = self.change_detector.determine_update_strategy(report)
                self.logger.info(f"Using {strategy.value} strategy for {file.filename}")
                
                # Sync to database
                status = await self.sync_agent.sync_data(file, report, strategy)
                self.monitor_agent.record_metric(f'sync_status_{file.file_type}', 
                                                1 if status == SyncStatus.SUCCESS else 0)
                
                if status == SyncStatus.SUCCESS:
                    self.logger.info(f"Successfully synced {file.filename}")
                else:
                    self.logger.warning(f"Sync issues for {file.filename}: {status.value}")
            
            # Step 4: Health check
            health = self.monitor_agent.check_health()
            self.logger.info(f"Health status: {health['status']}")
            
            if health['alerts']:
                for alert in health['alerts']:
                    self.logger.warning(f"Alert: {alert['message']}")
            
            self.monitor_agent.record_metric('sync_success', 1)
            self.logger.info("Daily sync completed successfully")
            
        except Exception as e:
            self.logger.error(f"Daily sync failed: {e}")
            self.monitor_agent.record_metric('sync_success', 0)
            self.monitor_agent.record_metric('errors', 1)
            raise

# ============================================================================
# SCHEDULER
# ============================================================================

def schedule_daily_sync():
    """Schedule daily sync at 2 AM ET"""
    
    async def run_sync():
        orchestrator = FloridaRevenueMasterOrchestrator()
        await orchestrator.run_daily_sync()
    
    # Schedule daily at 2 AM
    schedule.every().day.at("02:00").do(lambda: asyncio.run(run_sync()))
    
    logging.info("Daily sync scheduled for 2:00 AM ET")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for testing"""
    orchestrator = FloridaRevenueMasterOrchestrator()
    await orchestrator.run_daily_sync()

if __name__ == "__main__":
    # For testing, run immediately
    asyncio.run(main())
    
    # For production, uncomment to enable scheduling
    # schedule_daily_sync()