"""
Complete Sunbiz Database Loader for Supabase
Processes all Sunbiz data types and loads them into Supabase
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Corporation:
    """Corporation entity from cor/ folder"""
    entity_id: str
    entity_name: str
    status: str
    entity_type: str
    filing_date: Optional[str]
    state_country: str
    principal_address: str
    principal_city: str
    principal_state: str
    principal_zip: str
    mailing_address: str
    mailing_city: str
    mailing_state: str
    mailing_zip: str
    registered_agent_name: str
    registered_agent_address: str
    registered_agent_city: str
    registered_agent_state: str
    registered_agent_zip: str
    document_number: str
    fei_number: str
    date_filed: Optional[str]
    last_event: str
    event_date: Optional[str]
    event_file_number: str

@dataclass
class FictitiousName:
    """Fictitious name from fic/ folder"""
    registration_id: str
    name: str
    owner_name: str
    owner_address: str
    owner_city: str
    owner_state: str
    owner_zip: str
    registration_date: Optional[str]
    expiration_date: Optional[str]
    status: str

@dataclass
class RegisteredAgent:
    """Registered agent from AG/ folder"""
    agent_id: str
    agent_name: str
    agent_type: str
    address: str
    city: str
    state: str
    zip_code: str
    entity_count: int

class SunbizCompleteLoader:
    def __init__(self, data_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc"):
        self.data_path = Path(data_path)
        
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_key:
            logger.error("❌ SUPABASE_ANON_KEY not found in environment variables")
            raise ValueError("Please set SUPABASE_ANON_KEY in your .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
        
        # Statistics
        self.stats = {
            'corporations': 0,
            'fictitious_names': 0,
            'agents': 0,
            'total_processed': 0,
            'errors': 0
        }
    
    def parse_corporation_line(self, line: str) -> Optional[Corporation]:
        """Parse a corporation data line (fixed-width format)"""
        try:
            # Skip empty lines
            if len(line.strip()) < 100:
                return None
            
            # Fixed-width field positions (based on analysis)
            corp = Corporation(
                entity_id=line[0:12].strip(),
                entity_name=line[12:212].strip(),
                status=line[212:218].strip(),
                entity_type=line[218:228].strip(),
                filing_date=line[228:236].strip() or None,
                state_country=line[236:238].strip(),
                principal_address=line[238:338].strip(),
                principal_city=line[338:388].strip(),
                principal_state=line[388:390].strip(),
                principal_zip=line[390:400].strip(),
                mailing_address=line[400:500].strip(),
                mailing_city=line[500:550].strip(),
                mailing_state=line[550:552].strip(),
                mailing_zip=line[552:562].strip(),
                registered_agent_name=line[562:662].strip() if len(line) > 562 else '',
                registered_agent_address=line[662:762].strip() if len(line) > 662 else '',
                registered_agent_city=line[762:812].strip() if len(line) > 762 else '',
                registered_agent_state=line[812:814].strip() if len(line) > 812 else '',
                registered_agent_zip=line[814:824].strip() if len(line) > 814 else '',
                document_number=line[824:844].strip() if len(line) > 824 else '',
                fei_number=line[844:854].strip() if len(line) > 844 else '',
                date_filed=line[854:862].strip() if len(line) > 854 else None,
                last_event=line[862:872].strip() if len(line) > 862 else '',
                event_date=line[872:880].strip() if len(line) > 872 else None,
                event_file_number=line[880:900].strip() if len(line) > 880 else ''
            )
            
            # Validate entity_id
            if not corp.entity_id or len(corp.entity_id) < 6:
                return None
            
            return corp
            
        except Exception as e:
            logger.debug(f"Error parsing corporation line: {e}")
            return None
    
    def parse_fictitious_line(self, line: str) -> Optional[FictitiousName]:
        """Parse a fictitious name line"""
        try:
            if len(line.strip()) < 50:
                return None
            
            fic = FictitiousName(
                registration_id=line[0:12].strip(),
                name=line[12:212].strip(),
                owner_name=line[212:312].strip(),
                owner_address=line[312:412].strip(),
                owner_city=line[412:462].strip(),
                owner_state=line[462:464].strip(),
                owner_zip=line[464:474].strip(),
                registration_date=line[474:482].strip() or None,
                expiration_date=line[482:490].strip() or None,
                status=line[490:496].strip() if len(line) > 490 else 'ACTIVE'
            )
            
            if not fic.registration_id:
                return None
                
            return fic
            
        except Exception as e:
            logger.debug(f"Error parsing fictitious name: {e}")
            return None
    
    def parse_agent_line(self, line: str) -> Optional[RegisteredAgent]:
        """Parse a registered agent line"""
        try:
            if len(line.strip()) < 50:
                return None
            
            agent = RegisteredAgent(
                agent_id=line[0:12].strip(),
                agent_name=line[12:212].strip(),
                agent_type=line[212:222].strip(),
                address=line[222:322].strip(),
                city=line[322:372].strip(),
                state=line[372:374].strip(),
                zip_code=line[374:384].strip(),
                entity_count=int(line[384:390].strip()) if len(line) > 384 and line[384:390].strip().isdigit() else 0
            )
            
            if not agent.agent_id:
                return None
                
            return agent
            
        except Exception as e:
            logger.debug(f"Error parsing agent: {e}")
            return None
    
    async def create_database_schema(self):
        """Create all necessary tables in Supabase"""
        logger.info("📋 Creating database schema...")
        
        # SQL to create tables
        schema_sql = """
        -- Corporations table
        CREATE TABLE IF NOT EXISTS sunbiz_corporations (
            entity_id VARCHAR(20) PRIMARY KEY,
            entity_name VARCHAR(255) NOT NULL,
            status VARCHAR(20),
            entity_type VARCHAR(50),
            filing_date DATE,
            state_country VARCHAR(2),
            principal_address TEXT,
            principal_city VARCHAR(100),
            principal_state VARCHAR(2),
            principal_zip VARCHAR(10),
            mailing_address TEXT,
            mailing_city VARCHAR(100),
            mailing_state VARCHAR(2),
            mailing_zip VARCHAR(10),
            registered_agent_name VARCHAR(255),
            registered_agent_address TEXT,
            registered_agent_city VARCHAR(100),
            registered_agent_state VARCHAR(2),
            registered_agent_zip VARCHAR(10),
            document_number VARCHAR(50),
            fei_number VARCHAR(20),
            date_filed DATE,
            last_event VARCHAR(50),
            event_date DATE,
            event_file_number VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Fictitious names table
        CREATE TABLE IF NOT EXISTS sunbiz_fictitious_names (
            registration_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            owner_name VARCHAR(255),
            owner_address TEXT,
            owner_city VARCHAR(100),
            owner_state VARCHAR(2),
            owner_zip VARCHAR(10),
            registration_date DATE,
            expiration_date DATE,
            status VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Registered agents table
        CREATE TABLE IF NOT EXISTS sunbiz_registered_agents (
            agent_id VARCHAR(20) PRIMARY KEY,
            agent_name VARCHAR(255) NOT NULL,
            agent_type VARCHAR(50),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(2),
            zip_code VARCHAR(10),
            entity_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Entity name search table (for fast lookups)
        CREATE TABLE IF NOT EXISTS sunbiz_entity_search (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            entity_id VARCHAR(20),
            entity_name VARCHAR(255),
            normalized_name VARCHAR(255),
            entity_type VARCHAR(50),
            source_table VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_corp_name ON sunbiz_corporations(entity_name);
        CREATE INDEX IF NOT EXISTS idx_corp_status ON sunbiz_corporations(status);
        CREATE INDEX IF NOT EXISTS idx_corp_zip ON sunbiz_corporations(principal_zip);
        CREATE INDEX IF NOT EXISTS idx_corp_filing_date ON sunbiz_corporations(filing_date);
        
        CREATE INDEX IF NOT EXISTS idx_fic_name ON sunbiz_fictitious_names(name);
        CREATE INDEX IF NOT EXISTS idx_fic_owner ON sunbiz_fictitious_names(owner_name);
        
        CREATE INDEX IF NOT EXISTS idx_agent_name ON sunbiz_registered_agents(agent_name);
        
        CREATE INDEX IF NOT EXISTS idx_search_normalized ON sunbiz_entity_search(normalized_name);
        CREATE INDEX IF NOT EXISTS idx_search_entity_id ON sunbiz_entity_search(entity_id);
        """
        
        # Save schema to file
        with open('sunbiz_complete_schema.sql', 'w') as f:
            f.write(schema_sql)
        
        logger.info("✅ Schema SQL saved to sunbiz_complete_schema.sql")
        logger.info("📌 Please run this SQL in your Supabase dashboard")
        
        return schema_sql
    
    async def load_corporations(self, batch_size: int = 500):
        """Load corporation data from cor/ folder"""
        logger.info("🏢 Loading corporation data...")
        
        cor_path = self.data_path / "cor"
        if not cor_path.exists():
            logger.error(f"Corporation path not found: {cor_path}")
            return
        
        # Get all .txt files
        txt_files = []
        
        # Check main directory
        txt_files.extend(cor_path.glob("*.txt"))
        
        # Check year subdirectories
        for year_dir in cor_path.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                txt_files.extend(year_dir.glob("*.txt"))
        
        # Sort by name (most recent first)
        txt_files.sort(reverse=True)
        
        logger.info(f"Found {len(txt_files)} corporation files")
        
        batch = []
        
        for file_idx, file_path in enumerate(txt_files):
            logger.info(f"Processing file {file_idx + 1}/{len(txt_files)}: {file_path.name}")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f):
                        corp = self.parse_corporation_line(line)
                        
                        if corp:
                            # Convert to dict and clean data
                            corp_dict = asdict(corp)
                            
                            # Format dates
                            for date_field in ['filing_date', 'date_filed', 'event_date']:
                                if corp_dict[date_field]:
                                    try:
                                        # Parse YYYYMMDD format
                                        if len(corp_dict[date_field]) == 8:
                                            year = corp_dict[date_field][0:4]
                                            month = corp_dict[date_field][4:6]
                                            day = corp_dict[date_field][6:8]
                                            corp_dict[date_field] = f"{year}-{month}-{day}"
                                    except:
                                        corp_dict[date_field] = None
                            
                            batch.append(corp_dict)
                            
                            # Insert batch when full
                            if len(batch) >= batch_size:
                                await self.insert_batch('sunbiz_corporations', batch)
                                self.stats['corporations'] += len(batch)
                                logger.info(f"  Inserted {self.stats['corporations']} corporations...")
                                batch = []
                        
                        # Progress update
                        if line_num > 0 and line_num % 10000 == 0:
                            logger.info(f"  Processed {line_num} lines from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Insert remaining batch
        if batch:
            await self.insert_batch('sunbiz_corporations', batch)
            self.stats['corporations'] += len(batch)
        
        logger.info(f"✅ Loaded {self.stats['corporations']} corporations")
    
    async def load_fictitious_names(self, batch_size: int = 500):
        """Load fictitious names from fic/ folder"""
        logger.info("📝 Loading fictitious names...")
        
        fic_path = self.data_path / "fic"
        if not fic_path.exists():
            logger.warning(f"Fictitious names path not found: {fic_path}")
            return
        
        txt_files = list(fic_path.glob("*.txt"))
        logger.info(f"Found {len(txt_files)} fictitious name files")
        
        batch = []
        
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        fic = self.parse_fictitious_line(line)
                        
                        if fic:
                            fic_dict = asdict(fic)
                            
                            # Format dates
                            for date_field in ['registration_date', 'expiration_date']:
                                if fic_dict[date_field]:
                                    try:
                                        if len(fic_dict[date_field]) == 8:
                                            year = fic_dict[date_field][0:4]
                                            month = fic_dict[date_field][4:6]
                                            day = fic_dict[date_field][6:8]
                                            fic_dict[date_field] = f"{year}-{month}-{day}"
                                    except:
                                        fic_dict[date_field] = None
                            
                            batch.append(fic_dict)
                            
                            if len(batch) >= batch_size:
                                await self.insert_batch('sunbiz_fictitious_names', batch)
                                self.stats['fictitious_names'] += len(batch)
                                batch = []
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.stats['errors'] += 1
        
        if batch:
            await self.insert_batch('sunbiz_fictitious_names', batch)
            self.stats['fictitious_names'] += len(batch)
        
        logger.info(f"✅ Loaded {self.stats['fictitious_names']} fictitious names")
    
    async def load_registered_agents(self, batch_size: int = 500):
        """Load registered agents from AG/ folder"""
        logger.info("👤 Loading registered agents...")
        
        ag_path = self.data_path / "AG"
        if not ag_path.exists():
            logger.warning(f"Agents path not found: {ag_path}")
            return
        
        txt_files = list(ag_path.glob("*.txt"))
        logger.info(f"Found {len(txt_files)} agent files")
        
        batch = []
        
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        agent = self.parse_agent_line(line)
                        
                        if agent:
                            batch.append(asdict(agent))
                            
                            if len(batch) >= batch_size:
                                await self.insert_batch('sunbiz_registered_agents', batch)
                                self.stats['agents'] += len(batch)
                                batch = []
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.stats['errors'] += 1
        
        if batch:
            await self.insert_batch('sunbiz_registered_agents', batch)
            self.stats['agents'] += len(batch)
        
        logger.info(f"✅ Loaded {self.stats['agents']} registered agents")
    
    async def insert_batch(self, table_name: str, batch: List[Dict]):
        """Insert a batch of records to Supabase"""
        try:
            # Upsert batch
            response = self.supabase.table(table_name).upsert(batch).execute()
            
            if response.data:
                logger.debug(f"Inserted {len(batch)} records to {table_name}")
            
        except Exception as e:
            logger.error(f"Error inserting batch to {table_name}: {e}")
            self.stats['errors'] += 1
            
            # Try inserting one by one for failed batch
            for record in batch:
                try:
                    self.supabase.table(table_name).upsert(record).execute()
                except Exception as e2:
                    logger.debug(f"Failed to insert record: {e2}")
    
    async def build_search_index(self):
        """Build search index for fast entity lookups"""
        logger.info("🔍 Building search index...")
        
        try:
            # Get corporations
            corps = self.supabase.table('sunbiz_corporations').select('entity_id,entity_name,entity_type').execute()
            
            if corps.data:
                logger.info(f"Indexing {len(corps.data)} corporations...")
                
                batch = []
                for corp in corps.data:
                    batch.append({
                        'entity_id': corp['entity_id'],
                        'entity_name': corp['entity_name'],
                        'normalized_name': self.normalize_name(corp['entity_name']),
                        'entity_type': corp['entity_type'],
                        'source_table': 'sunbiz_corporations'
                    })
                    
                    if len(batch) >= 500:
                        await self.insert_batch('sunbiz_entity_search', batch)
                        batch = []
                
                if batch:
                    await self.insert_batch('sunbiz_entity_search', batch)
            
            # Get fictitious names
            fics = self.supabase.table('sunbiz_fictitious_names').select('registration_id,name').execute()
            
            if fics.data:
                logger.info(f"Indexing {len(fics.data)} fictitious names...")
                
                batch = []
                for fic in fics.data:
                    batch.append({
                        'entity_id': fic['registration_id'],
                        'entity_name': fic['name'],
                        'normalized_name': self.normalize_name(fic['name']),
                        'entity_type': 'FICTITIOUS',
                        'source_table': 'sunbiz_fictitious_names'
                    })
                    
                    if len(batch) >= 500:
                        await self.insert_batch('sunbiz_entity_search', batch)
                        batch = []
                
                if batch:
                    await self.insert_batch('sunbiz_entity_search', batch)
            
            logger.info("✅ Search index built successfully")
            
        except Exception as e:
            logger.error(f"Error building search index: {e}")
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for searching"""
        if not name:
            return ""
        
        # Convert to uppercase
        name = name.upper()
        
        # Remove common suffixes
        suffixes = [' LLC', ' INC', ' CORP', ' CORPORATION', ' LTD', ' LIMITED',
                   ' LP', ' LLP', ' PA', ' PLLC', ' PLC', ' PC', ' COMPANY', ' CO']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        # Remove punctuation
        name = re.sub(r'[^\w\s]', '', name)
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        return name
    
    async def run(self):
        """Main execution function"""
        logger.info("=" * 60)
        logger.info("SUNBIZ COMPLETE DATABASE LOADER")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Create schema
        await self.create_database_schema()
        
        # Wait for user to create tables
        input("\n⏸️  Please create the tables in Supabase using the SQL in 'sunbiz_complete_schema.sql'\n   Press Enter when done...")
        
        # Load all data types
        await self.load_corporations()
        await self.load_fictitious_names()
        await self.load_registered_agents()
        
        # Build search index
        await self.build_search_index()
        
        # Calculate total time
        duration = datetime.now() - start_time
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"🏢 Corporations: {self.stats['corporations']:,}")
        logger.info(f"📝 Fictitious Names: {self.stats['fictitious_names']:,}")
        logger.info(f"👤 Registered Agents: {self.stats['agents']:,}")
        logger.info(f"📊 Total Records: {sum([self.stats['corporations'], self.stats['fictitious_names'], self.stats['agents']]):,}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)

async def main():
    """Run the complete loader"""
    loader = SunbizCompleteLoader()
    await loader.run()

if __name__ == "__main__":
    asyncio.run(main())