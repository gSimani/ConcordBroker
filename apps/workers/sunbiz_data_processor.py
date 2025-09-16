"""
Sunbiz Data Processor
Processes downloaded Sunbiz corporation data for entity matching with tax deed properties
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import asyncio
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SunbizEntity:
    """Represents a Sunbiz business entity"""
    entity_id: str
    entity_name: str
    entity_type: str  # LLC, INC, CORP, etc.
    status: str
    filing_date: str
    principal_address: str
    principal_city: str
    principal_state: str
    principal_zip: str
    mailing_address: str
    mailing_city: str
    mailing_state: str
    mailing_zip: str
    registered_agent: str
    officers: List[Dict[str, str]]
    document_number: str
    fei_number: str = ""
    
class SunbizDataProcessor:
    def __init__(self, data_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"):
        self.data_path = Path(data_path)
        self.entities = {}
        self.name_index = defaultdict(list)  # Maps normalized names to entity IDs
        self.address_index = defaultdict(list)  # Maps addresses to entity IDs
        
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase credentials not found")
            self.supabase = None
    
    def parse_corporation_line(self, line: str) -> Optional[Dict]:
        """Parse a single line from corporation data file"""
        try:
            # Corporation data format is fixed-width
            # Format: EntityID(12) + EntityName(200) + Status(6) + Address fields...
            
            if len(line) < 100:
                return None
            
            entity_data = {
                'entity_id': line[0:12].strip(),
                'entity_name': line[12:212].strip(),
                'status': line[212:218].strip(),
                'entity_type': line[218:224].strip(),
                'principal_address': line[224:324].strip(),
                'principal_city': line[324:374].strip(),
                'principal_state': line[374:376].strip(),
                'principal_zip': line[376:386].strip(),
                'mailing_address': line[386:486].strip(),
                'mailing_city': line[486:536].strip(),
                'mailing_state': line[536:538].strip(),
                'mailing_zip': line[538:548].strip(),
                'filing_date': line[548:556].strip(),
                'registered_agent': '',
                'officers': []
            }
            
            # Extract registered agent if present
            if len(line) > 600:
                entity_data['registered_agent'] = line[556:656].strip()
            
            # Extract officers if present
            if len(line) > 700:
                officer_section = line[656:].strip()
                # Parse officer data (simplified - would need more complex parsing for full data)
                officers = []
                officer_pattern = r'([A-Z]+)\s+([A-Z]+)\s+([A-Z]?)\s+P'
                for match in re.finditer(officer_pattern, officer_section):
                    officers.append({
                        'last_name': match.group(1),
                        'first_name': match.group(2),
                        'middle': match.group(3) if match.group(3) else '',
                        'title': 'MGR'  # Would need to parse actual title
                    })
                entity_data['officers'] = officers
            
            return entity_data
            
        except Exception as e:
            logger.debug(f"Error parsing line: {e}")
            return None
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for matching"""
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
    
    def load_corporation_data(self, limit: Optional[int] = None) -> int:
        """Load corporation data from downloaded files"""
        logger.info("Loading corporation data from files...")
        
        cor_path = self.data_path / "doc" / "cor"
        if not cor_path.exists():
            logger.error(f"Corporation data path not found: {cor_path}")
            return 0
        
        loaded_count = 0
        
        # Get all .txt files
        txt_files = list(cor_path.glob("*.txt"))
        
        # Also check year directories
        for year_dir in cor_path.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                txt_files.extend(year_dir.glob("*.txt"))
        
        # Sort files by name (which includes date)
        txt_files.sort(reverse=True)  # Most recent first
        
        for file_path in txt_files:
            if limit and loaded_count >= limit:
                break
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if limit and loaded_count >= limit:
                            break
                        
                        entity_data = self.parse_corporation_line(line)
                        if entity_data and entity_data['entity_id']:
                            # Store entity
                            self.entities[entity_data['entity_id']] = entity_data
                            
                            # Build name index
                            normalized = self.normalize_name(entity_data['entity_name'])
                            if normalized:
                                self.name_index[normalized].append(entity_data['entity_id'])
                            
                            # Build address index
                            if entity_data['principal_address']:
                                addr_key = f"{entity_data['principal_address']}_{entity_data['principal_zip']}"
                                self.address_index[addr_key].append(entity_data['entity_id'])
                            
                            loaded_count += 1
                            
                            if loaded_count % 10000 == 0:
                                logger.info(f"Loaded {loaded_count} entities...")
                
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
        
        logger.info(f"✅ Loaded {loaded_count} corporation entities")
        logger.info(f"✅ Built name index with {len(self.name_index)} unique names")
        logger.info(f"✅ Built address index with {len(self.address_index)} unique addresses")
        
        return loaded_count
    
    def match_entity(self, name: str, address: Optional[str] = None) -> List[Dict]:
        """Match a name/address to Sunbiz entities"""
        matches = []
        
        # Try name matching
        normalized = self.normalize_name(name)
        if normalized in self.name_index:
            for entity_id in self.name_index[normalized]:
                entity = self.entities.get(entity_id)
                if entity:
                    matches.append({
                        'entity_id': entity_id,
                        'entity_name': entity['entity_name'],
                        'match_type': 'name',
                        'confidence': 0.9
                    })
        
        # Try fuzzy name matching if no exact match
        if not matches and normalized:
            for idx_name, entity_ids in self.name_index.items():
                if normalized in idx_name or idx_name in normalized:
                    for entity_id in entity_ids[:3]:  # Limit to top 3
                        entity = self.entities.get(entity_id)
                        if entity:
                            matches.append({
                                'entity_id': entity_id,
                                'entity_name': entity['entity_name'],
                                'match_type': 'fuzzy_name',
                                'confidence': 0.6
                            })
        
        # Try address matching if provided
        if address and not matches:
            # Normalize address
            addr_parts = address.upper().split()
            for addr_key, entity_ids in self.address_index.items():
                if any(part in addr_key for part in addr_parts if len(part) > 3):
                    for entity_id in entity_ids[:2]:  # Limit to top 2
                        entity = self.entities.get(entity_id)
                        if entity:
                            matches.append({
                                'entity_id': entity_id,
                                'entity_name': entity['entity_name'],
                                'match_type': 'address',
                                'confidence': 0.5
                            })
        
        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    async def create_sunbiz_tables(self):
        """Create Sunbiz entity tables in Supabase"""
        sql = """
        -- Create Sunbiz entities table
        CREATE TABLE IF NOT EXISTS sunbiz_entities (
            entity_id VARCHAR(20) PRIMARY KEY,
            entity_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(20),
            status VARCHAR(20),
            filing_date DATE,
            principal_address TEXT,
            principal_city VARCHAR(100),
            principal_state VARCHAR(2),
            principal_zip VARCHAR(10),
            mailing_address TEXT,
            mailing_city VARCHAR(100),
            mailing_state VARCHAR(2),
            mailing_zip VARCHAR(10),
            registered_agent VARCHAR(255),
            officers JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create index for faster searches
        CREATE INDEX IF NOT EXISTS idx_sunbiz_entity_name ON sunbiz_entities(entity_name);
        CREATE INDEX IF NOT EXISTS idx_sunbiz_normalized_name ON sunbiz_entities(UPPER(entity_name));
        CREATE INDEX IF NOT EXISTS idx_sunbiz_principal_zip ON sunbiz_entities(principal_zip);
        
        -- Create entity matches table for tax deed properties
        CREATE TABLE IF NOT EXISTS tax_deed_entity_matches (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID,
            parcel_number VARCHAR(50),
            applicant_name VARCHAR(255),
            entity_id VARCHAR(20),
            entity_name VARCHAR(255),
            match_type VARCHAR(50),
            confidence DECIMAL(3,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (entity_id) REFERENCES sunbiz_entities(entity_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_entity_matches_property ON tax_deed_entity_matches(property_id);
        CREATE INDEX IF NOT EXISTS idx_entity_matches_parcel ON tax_deed_entity_matches(parcel_number);
        """
        
        logger.info("Creating Sunbiz tables in database...")
        # Note: This SQL would need to be run manually in Supabase dashboard
        return sql
    
    async def save_entities_to_db(self, batch_size: int = 100):
        """Save entities to Supabase database"""
        if not self.supabase:
            logger.warning("Supabase not configured - cannot save entities")
            return
        
        logger.info(f"Saving {len(self.entities)} entities to database...")
        
        saved_count = 0
        batch = []
        
        for entity_id, entity in self.entities.items():
            # Prepare entity for database
            db_entity = {
                'entity_id': entity_id,
                'entity_name': entity['entity_name'][:255] if entity['entity_name'] else '',
                'entity_type': entity.get('entity_type', ''),
                'status': entity.get('status', ''),
                'filing_date': entity.get('filing_date', None),
                'principal_address': entity.get('principal_address', ''),
                'principal_city': entity.get('principal_city', ''),
                'principal_state': entity.get('principal_state', ''),
                'principal_zip': entity.get('principal_zip', ''),
                'mailing_address': entity.get('mailing_address', ''),
                'mailing_city': entity.get('mailing_city', ''),
                'mailing_state': entity.get('mailing_state', ''),
                'mailing_zip': entity.get('mailing_zip', ''),
                'registered_agent': entity.get('registered_agent', ''),
                'officers': json.dumps(entity.get('officers', []))
            }
            
            batch.append(db_entity)
            
            if len(batch) >= batch_size:
                try:
                    # Insert batch
                    self.supabase.table('sunbiz_entities').upsert(batch).execute()
                    saved_count += len(batch)
                    logger.info(f"Saved {saved_count} entities...")
                    batch = []
                except Exception as e:
                    logger.error(f"Error saving batch: {e}")
                    batch = []
        
        # Save remaining batch
        if batch:
            try:
                self.supabase.table('sunbiz_entities').upsert(batch).execute()
                saved_count += len(batch)
            except Exception as e:
                logger.error(f"Error saving final batch: {e}")
        
        logger.info(f"✅ Saved {saved_count} entities to database")
    
    async def match_tax_deed_properties(self):
        """Match tax deed properties with Sunbiz entities"""
        if not self.supabase:
            logger.warning("Supabase not configured")
            return
        
        logger.info("Matching tax deed properties with Sunbiz entities...")
        
        # Get tax deed properties
        try:
            result = self.supabase.table('tax_deed_properties').select('*').execute()
            properties = result.data if result.data else []
            
            logger.info(f"Found {len(properties)} tax deed properties to match")
            
            matches_count = 0
            
            for prop in properties:
                applicant = prop.get('applicant_name', '')
                if not applicant:
                    continue
                
                # Find matches
                matches = self.match_entity(applicant, prop.get('situs_address'))
                
                if matches:
                    # Save matches to database
                    for match in matches:
                        match_record = {
                            'property_id': prop.get('id'),
                            'parcel_number': prop.get('parcel_number'),
                            'applicant_name': applicant,
                            'entity_id': match['entity_id'],
                            'entity_name': match['entity_name'],
                            'match_type': match['match_type'],
                            'confidence': match['confidence']
                        }
                        
                        try:
                            self.supabase.table('tax_deed_entity_matches').insert(match_record).execute()
                            matches_count += 1
                        except Exception as e:
                            logger.debug(f"Error saving match: {e}")
            
            logger.info(f"✅ Created {matches_count} entity matches")
            
        except Exception as e:
            logger.error(f"Error matching properties: {e}")


async def main():
    """Process Sunbiz data and match with tax deed properties"""
    processor = SunbizDataProcessor()
    
    # Load corporation data
    logger.info("=== SUNBIZ DATA PROCESSING ===")
    loaded = processor.load_corporation_data(limit=50000)  # Load first 50k for testing
    
    if loaded > 0:
        # Create tables (SQL needs to be run manually)
        sql = await processor.create_sunbiz_tables()
        logger.info("Database schema SQL generated - run in Supabase dashboard")
        
        # Save to file for reference
        with open('create_sunbiz_tables.sql', 'w') as f:
            f.write(sql)
        
        # Save entities to database
        await processor.save_entities_to_db()
        
        # Match with tax deed properties
        await processor.match_tax_deed_properties()
        
        # Test matching
        test_names = [
            "FLORIDA TAX LIEN INVESTMENTS LLC",
            "BEACH INVESTMENTS GROUP",
            "John Smith"
        ]
        
        logger.info("\n=== TEST ENTITY MATCHING ===")
        for name in test_names:
            matches = processor.match_entity(name)
            logger.info(f"\nSearching for: {name}")
            if matches:
                for match in matches:
                    logger.info(f"  Found: {match['entity_name']} (ID: {match['entity_id']}, Confidence: {match['confidence']})")
            else:
                logger.info("  No matches found")
    
    logger.info("\n✅ Sunbiz data processing complete!")


if __name__ == "__main__":
    asyncio.run(main())