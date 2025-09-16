"""
Optimized Florida Database Uploader to Supabase
Combines memory-efficient processing with real-time progress monitoring
Integrates with existing memvid architecture for maximum performance
"""

import os
import re
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Generator
import mmap
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

@dataclass
class ProgressStats:
    """Real-time progress tracking"""
    current_folder: str = ""
    files_total: int = 0
    files_processed: int = 0
    files_successful: int = 0
    files_failed: int = 0
    records_total: int = 0
    records_processed: int = 0
    entities_created: int = 0
    contacts_created: int = 0
    start_time: datetime = None
    current_file: str = ""
    current_file_progress: float = 0.0
    folders_completed: List[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.folders_completed is None:
            self.folders_completed = []

class LiveProgressReporter:
    """Real-time progress reporting with console updates"""
    
    def __init__(self, stats: ProgressStats):
        self.stats = stats
        self.lock = threading.Lock()
        self.stop_flag = False
        
    def start_monitoring(self):
        """Start the live progress display"""
        def monitor():
            while not self.stop_flag:
                self.display_progress()
                time.sleep(2)  # Update every 2 seconds
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the live progress display"""
        self.stop_flag = True
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1)
    
    def display_progress(self):
        """Display live progress information"""
        with self.lock:
            elapsed = datetime.now() - self.stats.start_time
            
            # Calculate percentages
            file_pct = (self.stats.files_processed / max(self.stats.files_total, 1)) * 100
            record_pct = (self.stats.records_processed / max(self.stats.records_total, 1)) * 100 if self.stats.records_total > 0 else 0
            
            # Calculate rates
            files_per_sec = self.stats.files_processed / max(elapsed.total_seconds(), 1)
            records_per_sec = self.stats.records_processed / max(elapsed.total_seconds(), 1)
            
            # ETA calculation
            if files_per_sec > 0:
                remaining_files = self.stats.files_total - self.stats.files_processed
                eta_seconds = remaining_files / files_per_sec
                eta = str(timedelta(seconds=int(eta_seconds)))
            else:
                eta = "Unknown"
            
            # Clear screen and display progress
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 80)
            print("🚀 FLORIDA DATABASE UPLOAD TO SUPABASE - LIVE PROGRESS")
            print("=" * 80)
            print(f"📁 Current Folder: {self.stats.current_folder}")
            print(f"📄 Current File: {self.stats.current_file}")
            print(f"   File Progress: {self.stats.current_file_progress:.1f}%")
            print("-" * 80)
            print(f"📊 Overall Progress:")
            print(f"   Files: {self.stats.files_processed:,}/{self.stats.files_total:,} ({file_pct:.1f}%)")
            print(f"   Records: {self.stats.records_processed:,} ({record_pct:.1f}%)")
            print(f"   ✅ Successful: {self.stats.files_successful:,}")
            print(f"   ❌ Failed: {self.stats.files_failed:,}")
            print("-" * 80)
            print(f"📈 Performance:")
            print(f"   Speed: {files_per_sec:.2f} files/sec | {records_per_sec:.0f} records/sec")
            print(f"   Elapsed: {elapsed}")
            print(f"   ETA: {eta}")
            print("-" * 80)
            print(f"💾 Database Results:")
            print(f"   Entities Created: {self.stats.entities_created:,}")
            print(f"   Contacts Created: {self.stats.contacts_created:,}")
            print("-" * 80)
            print(f"✅ Completed Folders: {len(self.stats.folders_completed)}")
            for folder in self.stats.folders_completed[-5:]:  # Show last 5
                print(f"   • {folder}")
            print("=" * 80)

class OptimizedFloridaUploader:
    """Memory-efficient, high-performance Florida data uploader"""
    
    def __init__(self):
        """Initialize the optimized uploader"""
        # Database connection
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Clean URL for direct psycopg2 connection
        if '&supa=' in self.db_url:
            self.db_url = self.db_url.split('&supa=')[0]
        elif '?supa=' in self.db_url:
            self.db_url = self.db_url.split('?supa=')[0]
        
        self.database_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        
        # Configuration
        self.batch_size = 1000  # Larger batches for better performance
        self.max_workers = 4    # Parallel processing threads
        self.connection_pool_size = 8
        
        # Progress tracking
        self.stats = ProgressStats()
        self.reporter = LiveProgressReporter(self.stats)
        
        # Connection pool
        self.connections = []
        self._init_connection_pool()
        
        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('florida_upload_optimized.log'),
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _init_connection_pool(self):
        """Initialize connection pool for parallel processing"""
        for _ in range(self.connection_pool_size):
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            self.connections.append(conn)

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get connection from pool"""
        if self.connections:
            return self.connections.pop()
        else:
            # Create new connection if pool is empty
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = True
            return conn

    def return_connection(self, conn: psycopg2.extensions.connection):
        """Return connection to pool"""
        if len(self.connections) < self.connection_pool_size:
            self.connections.append(conn)
        else:
            conn.close()

    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers using optimized regex"""
        pattern = re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b')
        matches = pattern.findall(text)
        return [f"{area}-{exchange}-{number}" for area, exchange, number in matches]

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses using optimized regex"""
        pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE)
        return list(set(match.lower() for match in pattern.findall(text)))

    def parse_record_optimized(self, line: str, file_path: Path) -> Optional[Dict]:
        """Parse record using memory-efficient approach"""
        line = line.strip()
        if len(line) < 50:  # Skip very short lines
            return None
        
        try:
            # Determine record type from file path
            if '/cor/' in str(file_path):
                record_type = 'corporation'
            elif '/fic/' in str(file_path):
                record_type = 'fictitious'
            else:
                record_type = 'general'
            
            # Extract entity ID (usually at the beginning)
            entity_id = line[1:12].strip() if len(line) > 12 else ""
            if not entity_id:
                return None
            
            # Extract business name (typically after entity ID)
            business_name = line[12:132].strip() if len(line) > 132 else line[12:].strip()
            if not business_name or len(business_name) < 3:
                return None
            
            # Extract other fields based on record type
            if record_type == 'corporation' and len(line) > 250:
                city = line[217:247].strip()
                state = line[247:249].strip()
                zip_code = line[249:254].strip()
                county = line[254:284].strip() if len(line) > 284 else ''
            elif record_type == 'fictitious' and len(line) > 200:
                county = line[132:144].strip()
                city = line[224:264].strip() if len(line) > 264 else ''
                state = line[264:266].strip() if len(line) > 266 else ''
                zip_code = line[266:276].strip() if len(line) > 276 else ''
            else:
                # Fallback parsing
                city = state = zip_code = county = ''
            
            # Extract contacts from full line (more efficient than multiple passes)
            phones = self.extract_phone_numbers(line)
            emails = self.extract_emails(line)
            
            return {
                'entity_id': entity_id,
                'business_name': business_name[:255],
                'city': city[:100],
                'state': state[:2] or 'FL',
                'zip_code': zip_code[:10],
                'county': county[:50],
                'phones': phones[:5],  # Limit to 5 phones
                'emails': emails[:5],  # Limit to 5 emails
                'record_type': record_type[0].upper(),
                'source_file': file_path.name,
                'raw_content': line
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing record: {e}")
            return None

    def process_file_memory_mapped(self, file_path: Path) -> Generator[Dict, None, None]:
        """Process file using memory mapping for efficiency"""
        try:
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    # Process line by line
                    current_pos = 0
                    file_size = mmapped_file.size()
                    
                    while current_pos < file_size:
                        # Find end of line
                        line_end = mmapped_file.find(b'\n', current_pos)
                        if line_end == -1:
                            line_end = file_size
                        
                        # Extract line
                        line_bytes = mmapped_file[current_pos:line_end]
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                        
                        # Update progress
                        self.stats.current_file_progress = (current_pos / file_size) * 100
                        
                        # Parse record
                        if line:
                            record = self.parse_record_optimized(line, file_path)
                            if record:
                                yield record
                        
                        current_pos = line_end + 1
                        
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")

    def batch_upload_to_supabase(self, records: List[Dict]) -> Tuple[int, int]:
        """Upload batch of records to Supabase"""
        if not records:
            return 0, 0
        
        conn = self.get_connection()
        
        try:
            cur = conn.cursor()
            
            # Prepare entities data
            entities_data = []
            contacts_data = []
            
            for record in records:
                # Entity record
                entities_data.append((
                    record['entity_id'],
                    record['record_type'],
                    record['business_name'],
                    'ACTIVE',
                    record.get('address_line1', ''),
                    record['city'],
                    record['state'],
                    record['zip_code'],
                    record['county'],
                    record['source_file'],
                    datetime.now()
                ))
                
                # Contact records
                for phone in record.get('phones', []):
                    contacts_data.append((
                        record['entity_id'],
                        'PHONE',
                        None, None, None, None,  # name fields
                        phone,
                        None,  # email
                        record['source_file'],
                        datetime.now()
                    ))
                
                for email in record.get('emails', []):
                    contacts_data.append((
                        record['entity_id'],
                        'EMAIL',
                        None, None, None, None,  # name fields
                        None,  # phone
                        email,
                        record['source_file'],
                        datetime.now()
                    ))
            
            # Insert entities (with conflict handling)
            if entities_data:
                execute_values(
                    cur,
                    """
                    INSERT INTO florida_entities 
                    (entity_id, entity_type, business_name, entity_status, 
                     business_address_line1, business_city, business_state, business_zip, 
                     business_county, source_file, created_at)
                    VALUES %s
                    ON CONFLICT (entity_id) DO UPDATE SET
                        business_name = EXCLUDED.business_name,
                        business_city = EXCLUDED.business_city,
                        updated_at = NOW()
                    """,
                    entities_data
                )
                entities_created = len(entities_data)
            else:
                entities_created = 0
            
            # Insert contacts
            if contacts_data:
                execute_values(
                    cur,
                    """
                    INSERT INTO florida_contacts 
                    (entity_id, contact_type, first_name, middle_name, last_name, title,
                     phone, email, source_file, created_at)
                    VALUES %s
                    ON CONFLICT DO NOTHING
                    """,
                    contacts_data
                )
                contacts_created = len(contacts_data)
            else:
                contacts_created = 0
            
            # Update stats
            self.stats.entities_created += entities_created
            self.stats.contacts_created += contacts_created
            
            return entities_created, contacts_created
            
        except Exception as e:
            self.logger.error(f"Database upload error: {e}")
            return 0, 0
        finally:
            self.return_connection(conn)

    def process_single_file(self, file_path: Path) -> bool:
        """Process a single file with optimized performance"""
        try:
            self.stats.current_file = file_path.name
            self.stats.current_file_progress = 0.0
            
            # Check if already processed
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT processing_status FROM florida_processing_log WHERE file_path = %s",
                    (str(file_path),)
                )
                result = cur.fetchone()
                if result and result[0] == 'COMPLETED':
                    self.logger.info(f"Skipping already processed file: {file_path}")
                    return True
            finally:
                self.return_connection(conn)
            
            # Log processing start
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO florida_processing_log 
                    (file_path, file_size, processing_status, started_at, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (file_path) DO UPDATE SET
                        processing_status = EXCLUDED.processing_status,
                        started_at = EXCLUDED.started_at
                    """,
                    (str(file_path), file_path.stat().st_size, 'PROCESSING', datetime.now(), datetime.now())
                )
            finally:
                self.return_connection(conn)
            
            # Process file in batches
            batch = []
            records_processed = 0
            
            for record in self.process_file_memory_mapped(file_path):
                batch.append(record)
                records_processed += 1
                self.stats.records_processed += 1
                
                # Upload batch when full
                if len(batch) >= self.batch_size:
                    self.batch_upload_to_supabase(batch)
                    batch = []
            
            # Upload remaining records
            if batch:
                self.batch_upload_to_supabase(batch)
            
            # Mark as completed
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE florida_processing_log 
                    SET processing_status = %s, records_processed = %s, 
                        records_successful = %s, completed_at = %s
                    WHERE file_path = %s
                    """,
                    ('COMPLETED', records_processed, records_processed, datetime.now(), str(file_path))
                )
            finally:
                self.return_connection(conn)
            
            self.stats.files_successful += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            
            # Mark as failed
            conn = self.get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE florida_processing_log 
                    SET processing_status = %s, error_details = %s, completed_at = %s
                    WHERE file_path = %s
                    """,
                    ('FAILED', str(e), datetime.now(), str(file_path))
                )
            finally:
                self.return_connection(conn)
            
            self.stats.files_failed += 1
            return False

    def get_folder_structure(self) -> Dict[str, List[Path]]:
        """Analyze folder structure and prioritize processing order"""
        folders = {}
        
        for file_path in self.database_path.rglob("*.txt"):
            folder_name = str(file_path.parent.relative_to(self.database_path))
            if folder_name not in folders:
                folders[folder_name] = []
            folders[folder_name].append(file_path)
        
        # Sort folders by priority (smaller folders first for quick wins)
        sorted_folders = dict(sorted(folders.items(), key=lambda x: len(x[1])))
        
        return sorted_folders

    def run_upload(self):
        """Execute the optimized upload process"""
        print("🚀 Starting Optimized Florida Database Upload")
        print(f"📁 Source: {self.database_path}")
        print(f"💾 Database: Supabase PostgreSQL")
        print("-" * 80)
        
        # Analyze folder structure
        folders = self.get_folder_structure()
        total_files = sum(len(files) for files in folders.values())
        
        # Initialize stats
        self.stats.files_total = total_files
        self.stats.start_time = datetime.now()
        
        # Start live progress monitoring
        self.reporter.start_monitoring()
        
        try:
            # Process folders in order
            for folder_name, files in folders.items():
                self.stats.current_folder = folder_name
                
                print(f"\n📁 Processing folder: {folder_name} ({len(files)} files)")
                
                # Process files in this folder
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    
                    for file_path in files:
                        future = executor.submit(self.process_single_file, file_path)
                        futures.append(future)
                    
                    # Wait for completion
                    for future in futures:
                        try:
                            success = future.result()
                            self.stats.files_processed += 1
                        except Exception as e:
                            self.logger.error(f"Future execution error: {e}")
                            self.stats.files_failed += 1
                            self.stats.files_processed += 1
                
                # Mark folder as completed
                self.stats.folders_completed.append(folder_name)
                
        except KeyboardInterrupt:
            print("\n⏹️ Upload interrupted by user")
            
        except Exception as e:
            self.logger.error(f"Upload process error: {e}")
            print(f"\n❌ Upload failed: {e}")
            
        finally:
            # Stop progress monitoring
            self.reporter.stop_monitoring()
            
            # Close connections
            for conn in self.connections:
                conn.close()
            
            # Final report
            self.display_final_report()

    def display_final_report(self):
        """Display final upload report"""
        elapsed = datetime.now() - self.stats.start_time
        
        print("\n" + "=" * 80)
        print("🎉 FLORIDA DATABASE UPLOAD COMPLETED")
        print("=" * 80)
        print(f"📊 Final Statistics:")
        print(f"   Total Files: {self.stats.files_total:,}")
        print(f"   ✅ Successful: {self.stats.files_successful:,}")
        print(f"   ❌ Failed: {self.stats.files_failed:,}")
        print(f"   📄 Records Processed: {self.stats.records_processed:,}")
        print(f"   🏢 Entities Created: {self.stats.entities_created:,}")
        print(f"   📞 Contacts Created: {self.stats.contacts_created:,}")
        print(f"   ⏱️ Total Time: {elapsed}")
        print(f"   🚀 Average Speed: {self.stats.files_processed / elapsed.total_seconds():.2f} files/sec")
        print("=" * 80)
        
        success_rate = (self.stats.files_successful / max(self.stats.files_total, 1)) * 100
        print(f"✅ Success Rate: {success_rate:.1f}%")
        
        if self.stats.files_failed > 0:
            print(f"❌ Check florida_upload_optimized.log for error details")
        
        print("=" * 80)

def main():
    """Main entry point"""
    uploader = OptimizedFloridaUploader()
    uploader.run_upload()

if __name__ == "__main__":
    main()