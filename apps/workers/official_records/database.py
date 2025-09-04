"""
Database operations for Official Records data
"""

import asyncio
import asyncpg
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from .scraper import PropertyTransfer

logger = logging.getLogger(__name__)

class OfficialRecordsDB:
    """Database handler for Official Records data"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        # Create tables if needed
        await self.create_tables()
        
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            
    async def create_tables(self):
        """Create Official Records tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS official_records_transfers (
                    id SERIAL PRIMARY KEY,
                    recording_date DATE NOT NULL,
                    doc_type VARCHAR(100) NOT NULL,
                    book_page VARCHAR(50),
                    instrument_number VARCHAR(50) UNIQUE NOT NULL,
                    grantor TEXT NOT NULL,
                    grantee TEXT NOT NULL,
                    consideration NUMERIC(12, 2),
                    legal_description TEXT,
                    parcel_id VARCHAR(50),
                    doc_stamps NUMERIC(10, 2),
                    mortgage_amount NUMERIC(12, 2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transfers_recording_date 
                ON official_records_transfers(recording_date DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transfers_parcel_id 
                ON official_records_transfers(parcel_id) 
                WHERE parcel_id IS NOT NULL
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transfers_grantor 
                ON official_records_transfers(LOWER(grantor))
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transfers_grantee 
                ON official_records_transfers(LOWER(grantee))
            """)
            
            # Create entity activity tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS entity_transfer_activity (
                    id SERIAL PRIMARY KEY,
                    entity_name VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL, -- 'grantor' or 'grantee'
                    transfer_id INTEGER REFERENCES official_records_transfers(id),
                    recording_date DATE NOT NULL,
                    doc_type VARCHAR(100),
                    consideration NUMERIC(12, 2),
                    parcel_id VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_activity_name 
                ON entity_transfer_activity(LOWER(entity_name))
            """)
            
            # Create high-value transfers view
            await conn.execute("""
                CREATE OR REPLACE VIEW high_value_transfers AS
                SELECT * FROM official_records_transfers
                WHERE consideration > 1000000
                   OR mortgage_amount > 1000000
                   OR doc_stamps > 7000  -- Indicates ~$1M sale
                ORDER BY recording_date DESC
            """)
            
    async def insert_transfer(self, transfer: PropertyTransfer) -> int:
        """Insert a property transfer record"""
        async with self.pool.acquire() as conn:
            # Check if already exists
            exists = await conn.fetchval(
                "SELECT 1 FROM official_records_transfers WHERE instrument_number = $1",
                transfer.instrument_number
            )
            
            if exists:
                # Update existing record
                result = await conn.fetchrow("""
                    UPDATE official_records_transfers
                    SET recording_date = $1,
                        doc_type = $2,
                        book_page = $3,
                        grantor = $4,
                        grantee = $5,
                        consideration = $6,
                        legal_description = $7,
                        parcel_id = $8,
                        doc_stamps = $9,
                        mortgage_amount = $10,
                        updated_at = NOW()
                    WHERE instrument_number = $11
                    RETURNING id
                """,
                    datetime.strptime(transfer.recording_date, '%m/%d/%Y'),
                    transfer.doc_type,
                    transfer.book_page,
                    transfer.grantor,
                    transfer.grantee,
                    transfer.consideration,
                    transfer.legal_description,
                    transfer.parcel_id,
                    transfer.doc_stamps,
                    transfer.mortgage_amount,
                    transfer.instrument_number
                )
            else:
                # Insert new record
                result = await conn.fetchrow("""
                    INSERT INTO official_records_transfers (
                        recording_date, doc_type, book_page, instrument_number,
                        grantor, grantee, consideration, legal_description,
                        parcel_id, doc_stamps, mortgage_amount
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                """,
                    datetime.strptime(transfer.recording_date, '%m/%d/%Y'),
                    transfer.doc_type,
                    transfer.book_page,
                    transfer.instrument_number,
                    transfer.grantor,
                    transfer.grantee,
                    transfer.consideration,
                    transfer.legal_description,
                    transfer.parcel_id,
                    transfer.doc_stamps,
                    transfer.mortgage_amount
                )
                
            return result['id']
            
    async def bulk_insert_transfers(self, transfers: List[PropertyTransfer]) -> int:
        """Bulk insert multiple transfers"""
        count = 0
        for transfer in transfers:
            try:
                await self.insert_transfer(transfer)
                count += 1
            except Exception as e:
                logger.error(f"Error inserting transfer {transfer.instrument_number}: {e}")
                
        return count
        
    async def get_recent_transfers(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent property transfers"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM official_records_transfers
                WHERE recording_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY recording_date DESC
                LIMIT %s
            """, days, limit)
            
            return [dict(row) for row in rows]
            
    async def get_parcel_history(self, parcel_id: str) -> List[Dict[str, Any]]:
        """Get transfer history for a specific parcel"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM official_records_transfers
                WHERE parcel_id = $1
                ORDER BY recording_date DESC
            """, parcel_id)
            
            return [dict(row) for row in rows]
            
    async def track_entity(self, entity_name: str) -> Dict[str, List[Dict]]:
        """Track all transfers involving an entity"""
        async with self.pool.acquire() as conn:
            # Find as grantor (seller)
            grantor_rows = await conn.fetch("""
                SELECT * FROM official_records_transfers
                WHERE LOWER(grantor) LIKE LOWER($1)
                ORDER BY recording_date DESC
            """, f'%{entity_name}%')
            
            # Find as grantee (buyer)
            grantee_rows = await conn.fetch("""
                SELECT * FROM official_records_transfers
                WHERE LOWER(grantee) LIKE LOWER($1)
                ORDER BY recording_date DESC
            """, f'%{entity_name}%')
            
            # Update entity activity table
            for row in grantor_rows:
                await conn.execute("""
                    INSERT INTO entity_transfer_activity (
                        entity_name, role, transfer_id, recording_date,
                        doc_type, consideration, parcel_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT DO NOTHING
                """, entity_name, 'grantor', row['id'], row['recording_date'],
                    row['doc_type'], row['consideration'], row['parcel_id'])
                    
            for row in grantee_rows:
                await conn.execute("""
                    INSERT INTO entity_transfer_activity (
                        entity_name, role, transfer_id, recording_date,
                        doc_type, consideration, parcel_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT DO NOTHING
                """, entity_name, 'grantee', row['id'], row['recording_date'],
                    row['doc_type'], row['consideration'], row['parcel_id'])
                    
            return {
                'as_grantor': [dict(row) for row in grantor_rows],
                'as_grantee': [dict(row) for row in grantee_rows]
            }
            
    async def get_high_value_transfers(
        self,
        min_value: float = 1000000,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Get high-value transfers"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM high_value_transfers
                WHERE recording_date >= CURRENT_DATE - INTERVAL '%s days'
                  AND (consideration >= %s OR mortgage_amount >= %s)
                ORDER BY COALESCE(consideration, mortgage_amount) DESC
            """, days, min_value, min_value)
            
            return [dict(row) for row in rows]
            
    async def find_flips(
        self,
        max_days_between: int = 365,
        min_profit: float = 50000
    ) -> List[Dict[str, Any]]:
        """Find potential property flips"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                WITH flip_candidates AS (
                    SELECT 
                        t1.parcel_id,
                        t1.recording_date as buy_date,
                        t1.grantee as buyer,
                        t1.consideration as buy_price,
                        t2.recording_date as sell_date,
                        t2.grantor as seller,
                        t2.consideration as sell_price,
                        t2.consideration - t1.consideration as profit,
                        t2.recording_date - t1.recording_date as days_held
                    FROM official_records_transfers t1
                    JOIN official_records_transfers t2 
                        ON t1.parcel_id = t2.parcel_id
                        AND t1.grantee = t2.grantor
                        AND t2.recording_date > t1.recording_date
                        AND t2.recording_date - t1.recording_date <= %s
                    WHERE t1.consideration IS NOT NULL
                      AND t2.consideration IS NOT NULL
                      AND t2.consideration - t1.consideration >= %s
                )
                SELECT * FROM flip_candidates
                ORDER BY profit DESC
            """, max_days_between, min_profit)
            
            return [dict(row) for row in rows]