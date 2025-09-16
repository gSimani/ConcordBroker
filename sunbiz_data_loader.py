"""
Sunbiz Data Loader - Agent-Based Import System
Processes fixed-width corporate data files from Florida Division of Corporations
Implements OVERWRITE strategy to replace existing data
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase import create_client
from dotenv import load_dotenv
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_import.log'),
        logging.StreamHandler()
    ]
)

# Load environment
load_dotenv()

# Configuration
class Config:
    SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
    BATCH_SIZE = 500
    MAX_WORKERS = 3
    
    # Fixed-width column positions (based on data analysis)
    ENTITY_ID_START = 0
    ENTITY_ID_END = 12
    OFFICER_TYPE_START = 12
    OFFICER_TYPE_END = 16
    RECORD_TYPE_POS = 16
    LAST_NAME_START = 17
    LAST_NAME_END = 38
    FIRST_NAME_START = 38
    FIRST_NAME_END = 52
    MIDDLE_NAME_START = 52
    MIDDLE_NAME_END = 60
    ADDRESS_START = 60
    ADDRESS_END = 105
    CITY_START = 105
    CITY_END = 135
    STATE_START = 135
    STATE_END = 137
    ZIP_START = 137
    ZIP_END = 147

# Data classes
@dataclass
class ParsedRecord:
    """Parsed record from fixed-width data"""
    entity_id: str
    officer_type: str
    record_type: str
    last_name: str
    first_name: str
    middle_name: str
    street_address: str
    city: str
    state: str
    zip_code: str
    line_number: int
    file_source: str

@dataclass
class ProcessingStats:
    """Statistics for processing"""
    total_lines: int = 0
    entities_processed: int = 0
    officers_processed: int = 0
    entities_created: int = 0
    entities_updated: int = 0
    officers_created: int = 0
    officers_updated: int = 0
    errors_count: int = 0
    start_time: datetime = None
    end_time: datetime = None

# ============================================================================
# PARSING AGENT
# ============================================================================

class SunbizParsingAgent:
    """Agent responsible for parsing fixed-width data files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsed_entities = {}
        self.parsed_officers = []
    
    def parse_line(self, line: str, line_number: int, file_source: str) -> Optional[ParsedRecord]:
        """Parse a single line of fixed-width data"""
        try:
            # Skip empty lines
            if not line or len(line) < 20:
                return None
            
            # Extract fields using fixed positions
            entity_id = line[Config.ENTITY_ID_START:Config.ENTITY_ID_END].strip()
            if not entity_id:
                return None
            
            officer_type = line[Config.OFFICER_TYPE_START:Config.OFFICER_TYPE_END].strip()
            record_type = line[Config.RECORD_TYPE_POS] if len(line) > Config.RECORD_TYPE_POS else ''
            
            # Extract name fields
            last_name = line[Config.LAST_NAME_START:Config.LAST_NAME_END].strip() if len(line) > Config.LAST_NAME_START else ''
            first_name = line[Config.FIRST_NAME_START:Config.FIRST_NAME_END].strip() if len(line) > Config.FIRST_NAME_START else ''
            middle_name = line[Config.MIDDLE_NAME_START:Config.MIDDLE_NAME_END].strip() if len(line) > Config.MIDDLE_NAME_START else ''
            
            # Extract address fields
            street_address = line[Config.ADDRESS_START:Config.ADDRESS_END].strip() if len(line) > Config.ADDRESS_START else ''
            city = line[Config.CITY_START:Config.CITY_END].strip() if len(line) > Config.CITY_START else ''
            state = line[Config.STATE_START:Config.STATE_END].strip() if len(line) > Config.STATE_START else ''
            zip_code = line[Config.ZIP_START:Config.ZIP_END].strip() if len(line) > Config.ZIP_START else ''
            
            # Handle special suffixes (Esq., Jr., III, etc.)
            suffix = ''
            if 'Esq.' in officer_type:
                suffix = 'Esq.'
                officer_type = officer_type.replace('Esq.', '').strip()
            elif 'III' in officer_type:
                suffix = 'III'
                officer_type = officer_type.replace('III', '').strip()
            elif 'Jr.' in first_name or 'Sr.' in first_name:
                parts = first_name.split()
                if len(parts) > 1 and parts[-1] in ['Jr.', 'Sr.']:
                    suffix = parts[-1]
                    first_name = ' '.join(parts[:-1])
            
            # Clean record type
            if record_type not in ['P', 'C', 'G', 'D', 'T', 'S', 'V']:
                record_type = 'P' if first_name else 'C'
            
            return ParsedRecord(
                entity_id=entity_id,
                officer_type=officer_type,
                record_type=record_type,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name + (' ' + suffix if suffix else ''),
                street_address=street_address,
                city=city,
                state=state if state else 'FL',
                zip_code=zip_code,
                line_number=line_number,
                file_source=file_source
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing line {line_number}: {e}")
            return None
    
    async def parse_file(self, file_path: Path) -> Tuple[Dict, List[ParsedRecord]]:
        """Parse entire file and return entities and officers"""
        file_name = file_path.name
        self.logger.info(f"Parsing file: {file_name}")
        
        entities = {}
        officers = []
        line_count = 0
        
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                for line_number, line in enumerate(f, 1):
                    line_count += 1
                    
                    # Parse the line
                    record = self.parse_line(line, line_number, file_name)
                    if not record:
                        continue
                    
                    # Store entity info
                    if record.entity_id not in entities:
                        # Determine entity name from record
                        if record.record_type == 'C':
                            entity_name = record.last_name  # For corporations, name is in last_name field
                        else:
                            entity_name = f"{record.last_name} {record.first_name}".strip()
                        
                        entities[record.entity_id] = {
                            'entity_id': record.entity_id,
                            'entity_name': entity_name,
                            'entity_type': record.record_type,
                            'file_source': file_name
                        }
                    
                    # Store officer info
                    officers.append(record)
                    
                    # Progress logging
                    if line_count % 10000 == 0:
                        self.logger.info(f"Processed {line_count} lines from {file_name}")
        
        except Exception as e:
            self.logger.error(f"Error reading file {file_name}: {e}")
        
        self.logger.info(f"Parsing complete: {len(entities)} entities, {len(officers)} officers from {line_count} lines")
        return entities, officers

# ============================================================================
# DATABASE AGENT
# ============================================================================

class SunbizDatabaseAgent:
    """Agent responsible for database operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self.stats = ProcessingStats()
    
    def clear_existing_data(self):
        """Clear existing data for clean overwrite"""
        self.logger.info("Clearing existing Sunbiz data...")
        try:
            # Delete in correct order due to foreign keys
            self.supabase.table('sunbiz_property_matches').delete().neq('id', 0).execute()
            self.supabase.table('sunbiz_officers').delete().neq('id', 0).execute()
            self.supabase.table('sunbiz_entities').delete().neq('entity_id', '').execute()
            self.logger.info("Existing data cleared successfully")
        except Exception as e:
            self.logger.error(f"Error clearing data: {e}")
    
    def insert_entities_batch(self, entities: List[Dict]) -> int:
        """Insert batch of entities"""
        if not entities:
            return 0
        
        try:
            # Use upsert to handle conflicts
            result = self.supabase.table('sunbiz_entities').upsert(
                entities,
                on_conflict='entity_id'
            ).execute()
            
            count = len(result.data) if result.data else len(entities)
            self.stats.entities_created += count
            return count
        except Exception as e:
            self.logger.error(f"Error inserting entities: {e}")
            self.stats.errors_count += 1
            return 0
    
    def insert_officers_batch(self, officers: List[Dict]) -> int:
        """Insert batch of officers"""
        if not officers:
            return 0
        
        try:
            result = self.supabase.table('sunbiz_officers').insert(officers).execute()
            count = len(result.data) if result.data else len(officers)
            self.stats.officers_created += count
            return count
        except Exception as e:
            self.logger.error(f"Error inserting officers: {e}")
            self.stats.errors_count += 1
            return 0
    
    def process_entities(self, entities_dict: Dict):
        """Process and insert entities"""
        self.logger.info(f"Processing {len(entities_dict)} entities...")
        
        # Convert to list for batch insertion
        entities_list = list(entities_dict.values())
        
        # Process in batches
        for i in range(0, len(entities_list), Config.BATCH_SIZE):
            batch = entities_list[i:i + Config.BATCH_SIZE]
            inserted = self.insert_entities_batch(batch)
            self.stats.entities_processed += len(batch)
            
            if i % (Config.BATCH_SIZE * 10) == 0:
                self.logger.info(f"Processed {i + len(batch)} entities")
    
    def process_officers(self, officers: List[ParsedRecord]):
        """Process and insert officers"""
        self.logger.info(f"Processing {len(officers)} officers...")
        
        # Convert to database format
        officers_data = []
        for officer in officers:
            officer_dict = {
                'entity_id': officer.entity_id,
                'officer_type': officer.officer_type[:10] if officer.officer_type else None,
                'record_type': officer.record_type,
                'last_name': officer.last_name[:100] if officer.last_name else None,
                'first_name': officer.first_name[:50] if officer.first_name else None,
                'middle_name': officer.middle_name[:50] if officer.middle_name else None,
                'street_address': officer.street_address,
                'city': officer.city[:100] if officer.city else None,
                'state': officer.state[:2] if officer.state else 'FL',
                'zip_code': officer.zip_code[:10] if officer.zip_code else None,
                'file_source': officer.file_source,
                'line_number': officer.line_number
            }
            officers_data.append(officer_dict)
            
            # Process in batches
            if len(officers_data) >= Config.BATCH_SIZE:
                self.insert_officers_batch(officers_data)
                self.stats.officers_processed += len(officers_data)
                officers_data = []
        
        # Insert remaining
        if officers_data:
            self.insert_officers_batch(officers_data)
            self.stats.officers_processed += len(officers_data)
    
    def log_processing(self, file_name: str, file_hash: str, status: str):
        """Log processing details"""
        try:
            log_entry = {
                'file_name': file_name,
                'file_hash': file_hash,
                'processing_started': self.stats.start_time.isoformat() if self.stats.start_time else datetime.now().isoformat(),
                'processing_completed': self.stats.end_time.isoformat() if self.stats.end_time else None,
                'status': status,
                'total_lines': self.stats.total_lines,
                'entities_processed': self.stats.entities_processed,
                'officers_processed': self.stats.officers_processed,
                'entities_created': self.stats.entities_created,
                'officers_created': self.stats.officers_created,
                'errors_count': self.stats.errors_count
            }
            
            self.supabase.table('sunbiz_data_processing_log').insert(log_entry).execute()
            
        except Exception as e:
            self.logger.error(f"Error logging processing: {e}")

# ============================================================================
# MASTER ORCHESTRATOR
# ============================================================================

class SunbizImportOrchestrator:
    """Master orchestrator for Sunbiz data import"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsing_agent = SunbizParsingAgent()
        self.database_agent = SunbizDatabaseAgent()
        self.files_to_process = []
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def import_all_files(self, directory: str):
        """Import all corprindata files from directory"""
        self.logger.info("=" * 80)
        self.logger.info("SUNBIZ DATA IMPORT - STARTING")
        self.logger.info("=" * 80)
        
        # Find all corprindata files
        data_dir = Path(directory)
        pattern = "corprindata*.txt"
        files = sorted(data_dir.glob(pattern))
        
        if not files:
            self.logger.error(f"No files matching {pattern} found in {directory}")
            return
        
        self.logger.info(f"Found {len(files)} files to process")
        
        # Start timing
        self.database_agent.stats.start_time = datetime.now()
        
        # Clear existing data for clean overwrite
        self.database_agent.clear_existing_data()
        
        # Process each file
        all_entities = {}
        all_officers = []
        
        for file_path in files:
            self.logger.info(f"Processing file: {file_path.name}")
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # Parse file
            entities, officers = await self.parsing_agent.parse_file(file_path)
            
            # Merge entities (in case of duplicates across files)
            all_entities.update(entities)
            all_officers.extend(officers)
            
            self.database_agent.stats.total_lines += len(officers)
        
        # Insert all data
        self.logger.info("Inserting data into database...")
        self.database_agent.process_entities(all_entities)
        self.database_agent.process_officers(all_officers)
        
        # End timing
        self.database_agent.stats.end_time = datetime.now()
        duration = (self.database_agent.stats.end_time - self.database_agent.stats.start_time).total_seconds()
        
        # Log processing
        self.database_agent.log_processing(
            f"Batch import of {len(files)} files",
            file_hash,
            "SUCCESS" if self.database_agent.stats.errors_count == 0 else "PARTIAL"
        )
        
        # Print summary
        self.logger.info("=" * 80)
        self.logger.info("SUNBIZ DATA IMPORT - COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Files processed: {len(files)}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info(f"Entities created: {self.database_agent.stats.entities_created:,}")
        self.logger.info(f"Officers created: {self.database_agent.stats.officers_created:,}")
        self.logger.info(f"Errors: {self.database_agent.stats.errors_count}")
        self.logger.info(f"Processing rate: {self.database_agent.stats.total_lines / duration:.1f} records/second")
        self.logger.info("=" * 80)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    # Default to the TEMP/Sunbiz AG directory
    directory = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\Sunbiz AG"
    
    # Allow command line override
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return
    
    orchestrator = SunbizImportOrchestrator()
    await orchestrator.import_all_files(directory)

if __name__ == "__main__":
    asyncio.run(main())