"""
Database module for Sunbiz SFTP data
Handles storage and queries for Florida business filings
"""

import asyncpg
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SunbizSFTPDB:
    """Database operations for Sunbiz SFTP data"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or 'postgresql://localhost/sunbiz'
        self.pool = None
    
    async def connect(self):
        """Connect to database"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            await self.create_tables()
    
    async def disconnect(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Create necessary tables"""
        async with self.pool.acquire() as conn:
            # Corporate filings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_corporate_filings (
                    id SERIAL PRIMARY KEY,
                    doc_number VARCHAR(20) UNIQUE NOT NULL,
                    entity_name TEXT NOT NULL,
                    entity_type VARCHAR(100),
                    fei_number VARCHAR(20),
                    filing_date DATE,
                    status VARCHAR(50),
                    registered_agent_name TEXT,
                    principal_city VARCHAR(100),
                    principal_state VARCHAR(2),
                    principal_zip VARCHAR(20),
                    mailing_city VARCHAR(100),
                    mailing_state VARCHAR(2),
                    officer1_name TEXT,
                    officer1_title VARCHAR(100),
                    data_source VARCHAR(50) DEFAULT 'SFTP',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Corporate events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_corporate_events (
                    id SERIAL PRIMARY KEY,
                    doc_number VARCHAR(20),
                    event_date DATE,
                    event_type VARCHAR(100),
                    event_description TEXT,
                    filing_number VARCHAR(50),
                    effective_date DATE,
                    document_code VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate_filings(doc_number)
                )
            """)
            
            # Registered agents tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_registered_agents (
                    agent_name TEXT PRIMARY KEY,
                    entity_count INTEGER DEFAULT 0,
                    active_entities INTEGER DEFAULT 0,
                    inactive_entities INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Daily download tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_download_log (
                    id SERIAL PRIMARY KEY,
                    download_date DATE,
                    file_type VARCHAR(20),
                    filename VARCHAR(100),
                    records_processed INTEGER,
                    new_records INTEGER,
                    updated_records INTEGER,
                    duration_seconds FLOAT,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sunbiz_entity_name 
                ON sunbiz_corporate_filings(entity_name);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sunbiz_agent_name 
                ON sunbiz_corporate_filings(registered_agent_name);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sunbiz_status 
                ON sunbiz_corporate_filings(status);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sunbiz_filing_date 
                ON sunbiz_corporate_filings(filing_date);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sunbiz_event_date 
                ON sunbiz_corporate_events(event_date);
            """)
    
    async def bulk_insert_corporate_filings(self, filings: List[Dict]) -> Dict:
        """Bulk insert corporate filings"""
        stats = {
            'total_records': len(filings),
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        async with self.pool.acquire() as conn:
            for filing in filings:
                try:
                    # Parse date if provided
                    filing_date = None
                    if filing.get('filing_date'):
                        try:
                            filing_date = datetime.strptime(filing['filing_date'], '%Y%m%d').date()
                        except:
                            pass
                    
                    # Upsert filing
                    result = await conn.execute("""
                        INSERT INTO sunbiz_corporate_filings (
                            doc_number, entity_name, entity_type, fei_number,
                            filing_date, status, registered_agent_name,
                            principal_city, principal_state
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (doc_number) DO UPDATE SET
                            entity_name = $2,
                            entity_type = $3,
                            status = $6,
                            registered_agent_name = $7,
                            updated_at = NOW()
                        RETURNING (xmax = 0) AS inserted
                    """, filing['doc_number'], filing['entity_name'], 
                        filing.get('entity_type'), filing.get('fei_number'),
                        filing_date, filing.get('status'),
                        filing.get('registered_agent_name'),
                        filing.get('principal_city'), filing.get('principal_state'))
                    
                    if result:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                    
                    # Update registered agent stats
                    if filing.get('registered_agent_name'):
                        await self.update_agent_stats(filing['registered_agent_name'])
                        
                except Exception as e:
                    logger.error(f"Failed to insert filing {filing.get('doc_number')}: {e}")
                    stats['errors'] += 1
        
        return stats
    
    async def bulk_insert_corporate_events(self, events: List[Dict]) -> Dict:
        """Bulk insert corporate events"""
        stats = {
            'total_events': len(events),
            'created': 0,
            'errors': 0
        }
        
        async with self.pool.acquire() as conn:
            for event in events:
                try:
                    # Parse dates
                    event_date = None
                    if event.get('event_date'):
                        try:
                            event_date = datetime.strptime(event['event_date'], '%Y%m%d').date()
                        except:
                            pass
                    
                    await conn.execute("""
                        INSERT INTO sunbiz_corporate_events (
                            doc_number, event_date, event_type,
                            event_description, filing_number
                        ) VALUES ($1, $2, $3, $4, $5)
                    """, event['doc_number'], event_date,
                        event.get('event_type'), event.get('event_description'),
                        event.get('filing_number'))
                    
                    stats['created'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert event: {e}")
                    stats['errors'] += 1
        
        return stats
    
    async def update_agent_stats(self, agent_name: str):
        """Update registered agent statistics"""
        async with self.pool.acquire() as conn:
            # Count entities for this agent
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active,
                    COUNT(CASE WHEN status != 'ACTIVE' THEN 1 END) as inactive
                FROM sunbiz_corporate_filings
                WHERE registered_agent_name = $1
            """, agent_name)
            
            # Update or insert agent stats
            await conn.execute("""
                INSERT INTO sunbiz_registered_agents (
                    agent_name, entity_count, active_entities, inactive_entities
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (agent_name) DO UPDATE SET
                    entity_count = $2,
                    active_entities = $3,
                    inactive_entities = $4,
                    last_updated = NOW()
            """, agent_name, stats['total'], stats['active'], stats['inactive'])
    
    async def search_by_entity_name(self, search_term: str) -> List[Dict]:
        """Search for entities by name"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    doc_number, entity_name, entity_type, 
                    status, filing_date, registered_agent_name,
                    principal_city, principal_state
                FROM sunbiz_corporate_filings
                WHERE UPPER(entity_name) LIKE UPPER($1)
                ORDER BY filing_date DESC
                LIMIT 100
            """, f"%{search_term}%")
            
            return [dict(row) for row in rows]
    
    async def get_entities_by_agent(self, agent_name: str) -> List[Dict]:
        """Get all entities managed by a registered agent"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    doc_number, entity_name, entity_type,
                    status, filing_date, principal_city
                FROM sunbiz_corporate_filings
                WHERE UPPER(registered_agent_name) = UPPER($1)
                ORDER BY entity_name
            """, agent_name)
            
            return [dict(row) for row in rows]
    
    async def get_daily_summary(self, date: datetime) -> Dict:
        """Get summary of filings for a specific date"""
        async with self.pool.acquire() as conn:
            # Get filing stats
            filing_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_filings,
                    COUNT(CASE WHEN entity_type LIKE '%CORP%' THEN 1 END) as new_corporations,
                    COUNT(CASE WHEN entity_type LIKE '%LLC%' THEN 1 END) as new_llcs,
                    COUNT(CASE WHEN entity_type LIKE '%PARTNERSHIP%' THEN 1 END) as new_partnerships,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_filings
                FROM sunbiz_corporate_filings
                WHERE filing_date = $1
            """, date.date())
            
            # Get event stats
            event_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(CASE WHEN event_type LIKE '%DISSOL%' THEN 1 END) as dissolutions,
                    COUNT(CASE WHEN event_type LIKE '%AMEND%' THEN 1 END) as amendments,
                    COUNT(CASE WHEN event_type LIKE '%ANNUAL%' THEN 1 END) as annual_reports
                FROM sunbiz_corporate_events
                WHERE event_date = $1
            """, date.date())
            
            # Get top agents for the day
            top_agents = await conn.fetch("""
                SELECT 
                    registered_agent_name,
                    COUNT(*) as filing_count
                FROM sunbiz_corporate_filings
                WHERE filing_date = $1
                    AND registered_agent_name IS NOT NULL
                GROUP BY registered_agent_name
                ORDER BY filing_count DESC
                LIMIT 5
            """, date.date())
            
            return {
                'date': date.isoformat(),
                'filings': dict(filing_stats) if filing_stats else {},
                'events': dict(event_stats) if event_stats else {},
                'top_agents': [dict(row) for row in top_agents]
            }
    
    async def get_agent_portfolio_summary(self) -> List[Dict]:
        """Get summary of all registered agents"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    agent_name,
                    entity_count,
                    active_entities,
                    inactive_entities,
                    last_updated
                FROM sunbiz_registered_agents
                WHERE entity_count > 10
                ORDER BY entity_count DESC
                LIMIT 100
            """)
            
            return [dict(row) for row in rows]
    
    async def identify_major_business_owners(self) -> List[Dict]:
        """Identify entities that own multiple businesses"""
        async with self.pool.acquire() as conn:
            # Look for common officer names across entities
            rows = await conn.fetch("""
                SELECT 
                    officer1_name as owner_name,
                    COUNT(DISTINCT doc_number) as entity_count,
                    STRING_AGG(DISTINCT entity_type, ', ') as entity_types,
                    COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_count
                FROM sunbiz_corporate_filings
                WHERE officer1_name IS NOT NULL
                    AND LENGTH(officer1_name) > 5
                GROUP BY officer1_name
                HAVING COUNT(DISTINCT doc_number) > 5
                ORDER BY entity_count DESC
                LIMIT 50
            """)
            
            return [dict(row) for row in rows]
    
    async def log_job(self, job_data: Dict):
        """Log download job"""
        async with self.pool.acquire() as conn:
            for file_info in job_data.get('files_processed', []):
                await conn.execute("""
                    INSERT INTO sunbiz_download_log (
                        download_date, file_type, filename,
                        records_processed, new_records, updated_records,
                        duration_seconds, success, error_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, datetime.fromisoformat(job_data['date']).date(),
                    file_info.get('file_type'), file_info.get('filename'),
                    file_info.get('stats', {}).get('total_records', 0),
                    file_info.get('stats', {}).get('created', 0),
                    file_info.get('stats', {}).get('updated', 0),
                    job_data.get('duration_seconds', 0),
                    job_data.get('success', False),
                    ', '.join(job_data.get('errors', [])) if job_data.get('errors') else None)