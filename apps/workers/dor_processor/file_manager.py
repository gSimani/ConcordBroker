"""
Automated File Management Agent for DOR Data
Monitors, organizes, and manages Florida DOR data files
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import hashlib
import json
import aiohttp
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class FileMetadata:
    """Metadata for tracked files"""
    filename: str
    filepath: Path
    county: str
    year: int
    file_type: str
    size: int
    checksum: str
    status: FileStatus
    source_url: Optional[str]
    download_date: Optional[datetime]
    process_date: Optional[datetime]
    record_count: Optional[int]
    error_message: Optional[str]
    

class DORFileManager:
    """Manages DOR data files and orchestrates processing"""
    
    def __init__(self):
        self.base_dir = Path(os.getenv('DOR_DATA_DIR', 'C:/Users/gsima/Documents/MyProject/ConcordBroker/data/dor'))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.raw_dir = self.base_dir / 'raw'
        self.processed_dir = self.base_dir / 'processed'
        self.archive_dir = self.base_dir / 'archive'
        self.metadata_dir = self.base_dir / 'metadata'
        
        for dir in [self.raw_dir, self.processed_dir, self.archive_dir, self.metadata_dir]:
            dir.mkdir(exist_ok=True)
            
        self.file_registry: Dict[str, FileMetadata] = {}
        self.load_registry()
        
        self.counties = self.load_county_list()
        self.observer = None
        
    def load_county_list(self) -> List[Dict]:
        """Load Florida counties and their codes"""
        return [
            {"name": "Alachua", "code": "01"},
            {"name": "Baker", "code": "02"},
            {"name": "Bay", "code": "03"},
            {"name": "Bradford", "code": "04"},
            {"name": "Brevard", "code": "05"},
            {"name": "Broward", "code": "06"},
            {"name": "Calhoun", "code": "07"},
            {"name": "Charlotte", "code": "08"},
            {"name": "Citrus", "code": "09"},
            {"name": "Clay", "code": "10"},
            {"name": "Collier", "code": "11"},
            {"name": "Columbia", "code": "12"},
            {"name": "Miami-Dade", "code": "13"},
            {"name": "DeSoto", "code": "14"},
            {"name": "Dixie", "code": "15"},
            {"name": "Duval", "code": "16"},
            {"name": "Escambia", "code": "17"},
            {"name": "Flagler", "code": "18"},
            {"name": "Franklin", "code": "19"},
            {"name": "Gadsden", "code": "20"},
            {"name": "Gilchrist", "code": "21"},
            {"name": "Glades", "code": "22"},
            {"name": "Gulf", "code": "23"},
            {"name": "Hamilton", "code": "24"},
            {"name": "Hardee", "code": "25"},
            {"name": "Hendry", "code": "26"},
            {"name": "Hernando", "code": "27"},
            {"name": "Highlands", "code": "28"},
            {"name": "Hillsborough", "code": "29"},
            {"name": "Holmes", "code": "30"},
            {"name": "Indian River", "code": "31"},
            {"name": "Jackson", "code": "32"},
            {"name": "Jefferson", "code": "33"},
            {"name": "Lafayette", "code": "34"},
            {"name": "Lake", "code": "35"},
            {"name": "Lee", "code": "36"},
            {"name": "Leon", "code": "37"},
            {"name": "Levy", "code": "38"},
            {"name": "Liberty", "code": "39"},
            {"name": "Madison", "code": "40"},
            {"name": "Manatee", "code": "41"},
            {"name": "Marion", "code": "42"},
            {"name": "Martin", "code": "43"},
            {"name": "Monroe", "code": "44"},
            {"name": "Nassau", "code": "45"},
            {"name": "Okaloosa", "code": "46"},
            {"name": "Okeechobee", "code": "47"},
            {"name": "Orange", "code": "48"},
            {"name": "Osceola", "code": "49"},
            {"name": "Palm Beach", "code": "50"},
            {"name": "Pasco", "code": "51"},
            {"name": "Pinellas", "code": "52"},
            {"name": "Polk", "code": "53"},
            {"name": "Putnam", "code": "54"},
            {"name": "St. Johns", "code": "55"},
            {"name": "St. Lucie", "code": "56"},
            {"name": "Santa Rosa", "code": "57"},
            {"name": "Sarasota", "code": "58"},
            {"name": "Seminole", "code": "59"},
            {"name": "Sumter", "code": "60"},
            {"name": "Suwannee", "code": "61"},
            {"name": "Taylor", "code": "62"},
            {"name": "Union", "code": "63"},
            {"name": "Volusia", "code": "64"},
            {"name": "Wakulla", "code": "65"},
            {"name": "Walton", "code": "66"},
            {"name": "Washington", "code": "67"}
        ]
        
    def load_registry(self):
        """Load file registry from metadata"""
        registry_file = self.metadata_dir / 'file_registry.json'
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    value['filepath'] = Path(value['filepath'])
                    value['status'] = FileStatus(value['status'])
                    if value['download_date']:
                        value['download_date'] = datetime.fromisoformat(value['download_date'])
                    if value['process_date']:
                        value['process_date'] = datetime.fromisoformat(value['process_date'])
                    self.file_registry[key] = FileMetadata(**value)
                    
    def save_registry(self):
        """Save file registry to metadata"""
        registry_file = self.metadata_dir / 'file_registry.json'
        data = {}
        for key, metadata in self.file_registry.items():
            item = asdict(metadata)
            item['filepath'] = str(item['filepath'])
            item['status'] = item['status'].value
            if item['download_date']:
                item['download_date'] = item['download_date'].isoformat()
            if item['process_date']:
                item['process_date'] = item['process_date'].isoformat()
            data[key] = item
            
        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
        
    def parse_filename(self, filename: str) -> Dict:
        """Extract county and year from filename"""
        parts = filename.replace('.zip', '').replace('.xlsx', '').replace('.csv', '').split('_')
        
        county = None
        year = None
        
        for part in parts:
            if part in [c['name'] for c in self.counties]:
                county = part
            try:
                y = int(part)
                if 2020 <= y <= 2030:
                    year = y
            except ValueError:
                pass
                
        return {'county': county or 'Unknown', 'year': year or datetime.now().year}
        
    def register_file(self, filepath: Path, source_url: Optional[str] = None) -> FileMetadata:
        """Register a new file in the system"""
        
        file_info = self.parse_filename(filepath.name)
        
        metadata = FileMetadata(
            filename=filepath.name,
            filepath=filepath,
            county=file_info['county'],
            year=file_info['year'],
            file_type=filepath.suffix,
            size=filepath.stat().st_size if filepath.exists() else 0,
            checksum=self.calculate_checksum(filepath) if filepath.exists() else '',
            status=FileStatus.DOWNLOADED if filepath.exists() else FileStatus.PENDING,
            source_url=source_url,
            download_date=datetime.now() if filepath.exists() else None,
            process_date=None,
            record_count=None,
            error_message=None
        )
        
        self.file_registry[filepath.name] = metadata
        self.save_registry()
        
        return metadata
        
    async def check_for_updates(self):
        """Check Florida DOR website for new files"""
        base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/"
        
        updates = []
        async with aiohttp.ClientSession() as session:
            for county in self.counties:
                filename = f"{county['name']}%20{county['code']}%20Preliminary%20NAL%202025.zip"
                url = base_url + filename
                
                local_filename = f"{county['name']}_2025_NAL.zip"
                local_path = self.raw_dir / local_filename
                
                if local_filename not in self.file_registry:
                    updates.append({
                        'county': county['name'],
                        'year': 2025,
                        'url': url,
                        'local_path': local_path
                    })
                    logger.info(f"New file available: {county['name']} 2025 NAL")
                    
        return updates
        
    def get_pending_files(self) -> List[FileMetadata]:
        """Get files that need processing"""
        return [
            metadata for metadata in self.file_registry.values()
            if metadata.status in [FileStatus.DOWNLOADED, FileStatus.EXTRACTED]
        ]
        
    def get_failed_files(self) -> List[FileMetadata]:
        """Get files that failed processing"""
        return [
            metadata for metadata in self.file_registry.values()
            if metadata.status == FileStatus.FAILED
        ]
        
    def archive_old_files(self, days: int = 30):
        """Archive files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for metadata in self.file_registry.values():
            if metadata.status == FileStatus.PROCESSED and metadata.process_date:
                if metadata.process_date < cutoff_date:
                    # Move to archive
                    archive_path = self.archive_dir / metadata.filename
                    if metadata.filepath.exists():
                        metadata.filepath.rename(archive_path)
                        metadata.filepath = archive_path
                        metadata.status = FileStatus.ARCHIVED
                        logger.info(f"Archived: {metadata.filename}")
                        
        self.save_registry()
        
    def cleanup_temp_files(self):
        """Clean up temporary and intermediate files"""
        patterns = ['*.tmp', '*.partial', '~$*']
        
        for pattern in patterns:
            for file in self.base_dir.rglob(pattern):
                try:
                    file.unlink()
                    logger.info(f"Deleted temp file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")
                    

class FileWatcher(FileSystemEventHandler):
    """Watch for new files and trigger processing"""
    
    def __init__(self, manager: DORFileManager, processor_callback):
        self.manager = manager
        self.processor_callback = processor_callback
        
    def on_created(self, event):
        if not event.is_directory:
            filepath = Path(event.src_path)
            if filepath.suffix in ['.zip', '.xlsx', '.csv', '.txt']:
                logger.info(f"New file detected: {filepath}")
                metadata = self.manager.register_file(filepath)
                asyncio.create_task(self.processor_callback(metadata))
                
    def on_modified(self, event):
        if not event.is_directory:
            filepath = Path(event.src_path)
            if filepath.name in self.manager.file_registry:
                # Update checksum
                metadata = self.manager.file_registry[filepath.name]
                new_checksum = self.manager.calculate_checksum(filepath)
                if new_checksum != metadata.checksum:
                    logger.info(f"File modified: {filepath}")
                    metadata.checksum = new_checksum
                    metadata.status = FileStatus.DOWNLOADED
                    self.manager.save_registry()
                    

class DORDataAgent:
    """Main agent that orchestrates file management and processing"""
    
    def __init__(self):
        self.manager = DORFileManager()
        self.watcher = FileWatcher(self.manager, self.process_file)
        self.observer = Observer()
        self.processing_queue = asyncio.Queue()
        
    async def start(self):
        """Start the agent"""
        logger.info("Starting DOR Data Agent")
        
        # Start file watcher
        self.observer.schedule(self.watcher, str(self.manager.raw_dir), recursive=True)
        self.observer.start()
        
        # Start background tasks
        asyncio.create_task(self.update_checker())
        asyncio.create_task(self.process_queue())
        asyncio.create_task(self.maintenance_task())
        
        logger.info("DOR Data Agent started successfully")
        
    async def stop(self):
        """Stop the agent"""
        self.observer.stop()
        self.observer.join()
        
    async def update_checker(self):
        """Periodically check for new files"""
        while True:
            try:
                updates = await self.manager.check_for_updates()
                for update in updates:
                    await self.processing_queue.put(update)
                    
            except Exception as e:
                logger.error(f"Error checking updates: {e}")
                
            await asyncio.sleep(3600)  # Check every hour
            
    async def process_queue(self):
        """Process files from the queue"""
        while True:
            try:
                item = await self.processing_queue.get()
                await self.process_file(item)
                
            except Exception as e:
                logger.error(f"Error processing queue item: {e}")
                
    async def process_file(self, metadata: FileMetadata):
        """Process a single file"""
        try:
            logger.info(f"Processing: {metadata.filename}")
            metadata.status = FileStatus.PROCESSING
            self.manager.save_registry()
            
            # Import and use the DuckDB processor
            from duckdb_processor import DORDuckDBProcessor
            
            processor = DORDuckDBProcessor()
            await processor.initialize()
            
            result = await processor.process_county_data(
                url=metadata.source_url,
                county=metadata.county,
                year=metadata.year
            )
            
            metadata.status = FileStatus.PROCESSED
            metadata.process_date = datetime.now()
            metadata.record_count = result.get('properties', 0)
            
            await processor.close()
            
        except Exception as e:
            logger.error(f"Error processing {metadata.filename}: {e}")
            metadata.status = FileStatus.FAILED
            metadata.error_message = str(e)
            
        finally:
            self.manager.save_registry()
            
    async def maintenance_task(self):
        """Periodic maintenance tasks"""
        while True:
            try:
                # Archive old files
                self.manager.archive_old_files(days=30)
                
                # Clean up temp files
                self.manager.cleanup_temp_files()
                
                # Retry failed files
                for metadata in self.manager.get_failed_files():
                    if metadata.error_message and 'timeout' in metadata.error_message.lower():
                        await self.processing_queue.put(metadata)
                        
            except Exception as e:
                logger.error(f"Error in maintenance: {e}")
                
            await asyncio.sleep(86400)  # Run daily
            
    async def manual_download(self, county: str, year: int = 2025):
        """Manually trigger download for a specific county"""
        base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/{year}P/"
        
        county_info = next((c for c in self.manager.counties if c['name'] == county), None)
        if not county_info:
            logger.error(f"County not found: {county}")
            return
            
        filename = f"{county}%20{county_info['code']}%20Preliminary%20NAL%20{year}.zip"
        url = base_url.format(year=year) + filename
        
        local_filename = f"{county}_{year}_NAL.zip"
        local_path = self.manager.raw_dir / local_filename
        
        metadata = self.manager.register_file(local_path, url)
        await self.processing_queue.put(metadata)
        
        logger.info(f"Queued download: {county} {year}")
        

async def main():
    """Main execution"""
    agent = DORDataAgent()
    
    try:
        await agent.start()
        
        # Manual trigger for Broward County
        await agent.manual_download("Broward", 2025)
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
            # Display status
            pending = agent.manager.get_pending_files()
            if pending:
                logger.info(f"Pending files: {len(pending)}")
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())