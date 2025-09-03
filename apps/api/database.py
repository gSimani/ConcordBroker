"""
Database Connection Management
Handles PostgreSQL/Supabase connections
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self.dsn = settings.DATABASE_URL
        
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=10,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Fetch a single row"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_many(self, query: str, *args) -> List[Dict]:
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Execute multiple queries in a transaction"""
        async with self.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, args_list)
    
    # Parcel-specific queries
    async def search_parcels(self, 
                           city: Optional[str] = None,
                           main_use: Optional[str] = None,
                           sub_use: Optional[str] = None,
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None,
                           min_score: Optional[float] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[Dict]:
        """Search parcels with filters"""
        
        conditions = []
        params = []
        param_count = 0
        
        if city:
            param_count += 1
            conditions.append(f"city = ${param_count}")
            params.append(city)
        
        if main_use:
            param_count += 1
            conditions.append(f"main_use = ${param_count}")
            params.append(main_use)
        
        if sub_use:
            param_count += 1
            conditions.append(f"sub_use = ${param_count}")
            params.append(sub_use)
        
        if min_value is not None:
            param_count += 1
            conditions.append(f"just_value >= ${param_count}")
            params.append(min_value)
        
        if max_value is not None:
            param_count += 1
            conditions.append(f"just_value <= ${param_count}")
            params.append(max_value)
        
        if min_score is not None:
            param_count += 1
            conditions.append(f"score >= ${param_count}")
            params.append(min_score)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(offset)
        
        query = f"""
            SELECT 
                p.folio,
                p.city,
                p.main_use,
                p.sub_use,
                p.situs_addr,
                p.owner_raw,
                p.just_value,
                p.assessed_soh,
                p.taxable,
                p.land_sf,
                p.bldg_sf,
                p.year_built,
                p.score,
                COUNT(s.id) as sale_count,
                MAX(s.sale_date) as last_sale_date,
                MAX(s.price) as last_sale_price
            FROM parcels p
            LEFT JOIN sales s ON p.folio = s.folio
            {where_clause}
            GROUP BY 
                p.folio, p.city, p.main_use, p.sub_use,
                p.situs_addr, p.owner_raw, p.just_value,
                p.assessed_soh, p.taxable, p.land_sf,
                p.bldg_sf, p.year_built, p.score
            ORDER BY p.score DESC NULLS LAST
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """
        
        return await self.fetch_many(query, *params)
    
    async def get_parcel_details(self, folio: str) -> Optional[Dict]:
        """Get detailed parcel information"""
        
        # Get parcel base data
        parcel = await self.fetch_one(
            """
            SELECT * FROM parcels WHERE folio = $1
            """,
            folio
        )
        
        if not parcel:
            return None
        
        # Get sales history
        sales = await self.fetch_many(
            """
            SELECT * FROM sales 
            WHERE folio = $1 
            ORDER BY sale_date DESC
            """,
            folio
        )
        parcel['sales'] = sales
        
        # Get recorded documents
        docs = await self.fetch_many(
            """
            SELECT rd.* 
            FROM recorded_docs rd
            JOIN doc_parcels dp ON rd.instrument_no = dp.instrument_no
            WHERE dp.folio = $1
            ORDER BY rd.rec_datetime DESC
            LIMIT 20
            """,
            folio
        )
        parcel['documents'] = docs
        
        # Get entity info if linked
        entity = await self.fetch_one(
            """
            SELECT e.* 
            FROM entities e
            JOIN parcel_entity_links pel ON e.id = pel.entity_id
            WHERE pel.folio = $1
            ORDER BY pel.confidence DESC
            LIMIT 1
            """,
            folio
        )
        parcel['entity'] = entity
        
        return parcel
    
    async def get_entity_portfolio(self, entity_id: str) -> Dict:
        """Get all properties owned by an entity"""
        
        entity = await self.fetch_one(
            "SELECT * FROM entities WHERE id = $1",
            entity_id
        )
        
        if not entity:
            return None
        
        # Get linked parcels
        parcels = await self.fetch_many(
            """
            SELECT p.*, pel.confidence, pel.match_method
            FROM parcels p
            JOIN parcel_entity_links pel ON p.folio = pel.folio
            WHERE pel.entity_id = $1
            ORDER BY p.just_value DESC
            """,
            entity_id
        )
        
        # Get officers
        officers = await self.fetch_many(
            """
            SELECT * FROM officers
            WHERE entity_id = $1
            """,
            entity_id
        )
        
        return {
            'entity': entity,
            'parcels': parcels,
            'officers': officers,
            'total_value': sum(p.get('just_value', 0) for p in parcels),
            'property_count': len(parcels)
        }
    
    async def log_job(self, job_data: Dict) -> None:
        """Log ETL job execution"""
        await self.execute(
            """
            INSERT INTO jobs (
                job_type, started_at, finished_at, 
                ok, rows, notes, parameters
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            job_data.get('type'),
            job_data.get('started_at'),
            job_data.get('finished_at'),
            job_data.get('success', False),
            job_data.get('records_processed', 0),
            job_data.get('notes'),
            job_data.get('parameters')
        )


# Global database instance
db = Database()