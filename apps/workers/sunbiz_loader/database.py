"""
Database operations for Sunbiz loader
Handles entity and officer data persistence
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
import json

import asyncpg
from asyncpg.pool import Pool

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Database operations for Sunbiz data"""
    
    def __init__(self):
        self.pool: Pool = None
        self.dsn = settings.DATABASE_URL
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    async def load_entities(self, entities: List[Dict]) -> Dict:
        """Load entity records to database"""
        
        if not self.pool:
            await self.connect()
        
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0
        }
        
        async with self.pool.acquire() as conn:
            for entity in entities:
                try:
                    # Check if entity exists
                    existing = await conn.fetchrow(
                        "SELECT id FROM entities WHERE document_number = $1",
                        entity.get('document_number')
                    )
                    
                    if existing:
                        # Update existing entity
                        await conn.execute(
                            """
                            UPDATE entities SET
                                name = $2,
                                status = $3,
                                fei_ein = $4,
                                principal_addr = $5,
                                state_of_inc = $6,
                                filing_type = $7,
                                mailing_addr = $8,
                                updated_at = NOW()
                            WHERE document_number = $1
                            """,
                            entity.get('document_number'),
                            entity.get('entity_name'),
                            entity.get('status'),
                            entity.get('fei_ein'),
                            self._format_address(entity, 'principal'),
                            entity.get('state'),
                            entity.get('filing_type'),
                            self._format_address(entity, 'mailing')
                        )
                        stats["updated"] += 1
                    else:
                        # Insert new entity
                        await conn.execute(
                            """
                            INSERT INTO entities (
                                document_number, name, status, fei_ein,
                                principal_addr, state_of_inc, filing_type,
                                mailing_addr, created_date, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                            """,
                            entity.get('document_number'),
                            entity.get('entity_name'),
                            entity.get('status'),
                            entity.get('fei_ein'),
                            self._format_address(entity, 'principal'),
                            entity.get('state'),
                            entity.get('filing_type'),
                            self._format_address(entity, 'mailing'),
                            self._parse_date(entity.get('date_filed'))
                        )
                        stats["created"] += 1
                    
                    # Handle officers if present
                    if entity.get('_file_type') == 'officer':
                        await self._load_officer(conn, entity)
                        
                except Exception as e:
                    logger.error(f"Failed to load entity {entity.get('document_number')}: {e}")
                    stats["failed"] += 1
        
        logger.info(f"Loaded entities - Created: {stats['created']}, "
                   f"Updated: {stats['updated']}, Failed: {stats['failed']}")
        
        return stats
    
    async def _load_officer(self, conn, officer_data: Dict):
        """Load officer record"""
        
        # Get entity ID
        entity = await conn.fetchrow(
            "SELECT id FROM entities WHERE document_number = $1",
            officer_data.get('document_number')
        )
        
        if not entity:
            logger.warning(f"Entity not found for officer: {officer_data.get('document_number')}")
            return
        
        # Check if officer exists
        existing = await conn.fetchrow(
            """
            SELECT id FROM officers 
            WHERE entity_id = $1 AND name = $2 AND title = $3
            """,
            entity['id'],
            officer_data.get('officer_name'),
            officer_data.get('officer_title')
        )
        
        if not existing:
            # Insert officer
            await conn.execute(
                """
                INSERT INTO officers (
                    entity_id, name, title, addr, is_manager
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                entity['id'],
                officer_data.get('officer_name'),
                officer_data.get('officer_title'),
                self._format_officer_address(officer_data),
                officer_data.get('is_manager', False)
            )
    
    def _format_address(self, entity: Dict, prefix: str) -> str:
        """Format address from components"""
        
        addr_parts = []
        
        addr1 = entity.get(f'{prefix}_addr1', '').strip()
        addr2 = entity.get(f'{prefix}_addr2', '').strip()
        city = entity.get(f'{prefix}_city', '').strip()
        state = entity.get(f'{prefix}_state', '').strip()
        zip_code = entity.get(f'{prefix}_zip', '').strip()
        
        if addr1:
            addr_parts.append(addr1)
        if addr2:
            addr_parts.append(addr2)
        
        if city and state:
            addr_parts.append(f"{city}, {state} {zip_code}".strip())
        elif city:
            addr_parts.append(f"{city} {zip_code}".strip())
        
        return ', '.join(addr_parts) if addr_parts else None
    
    def _format_officer_address(self, officer: Dict) -> str:
        """Format officer address"""
        
        addr_parts = []
        
        if officer.get('officer_addr1'):
            addr_parts.append(officer['officer_addr1'].strip())
        if officer.get('officer_addr2'):
            addr_parts.append(officer['officer_addr2'].strip())
        
        city_state_zip = []
        if officer.get('officer_city'):
            city_state_zip.append(officer['officer_city'].strip())
        if officer.get('officer_state'):
            city_state_zip.append(officer['officer_state'].strip())
        if officer.get('officer_zip'):
            city_state_zip.append(officer['officer_zip'].strip())
        
        if city_state_zip:
            addr_parts.append(' '.join(city_state_zip))
        
        return ', '.join(addr_parts) if addr_parts else None
    
    def _parse_date(self, date_str: str):
        """Parse date from YYYYMMDD format"""
        
        if not date_str or not date_str.isdigit() or len(date_str) != 8:
            return None
        
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            return datetime(year, month, day)
        except:
            return None
    
    async def log_job(self, job_stats: Dict):
        """Log job execution"""
        
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO jobs (
                    job_type, started_at, finished_at, ok, 
                    rows, notes, parameters
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                job_stats.get('type', 'sunbiz_loader'),
                job_stats.get('started_at'),
                job_stats.get('finished_at'),
                job_stats.get('success', False),
                job_stats.get('records_processed', 0),
                json.dumps(job_stats.get('errors', [])) if job_stats.get('errors') else None,
                json.dumps({
                    'files': job_stats.get('files_downloaded', 0),
                    'entities_created': job_stats.get('entities_created', 0),
                    'entities_updated': job_stats.get('entities_updated', 0)
                })
            )