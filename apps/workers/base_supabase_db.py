"""
Base Supabase Database Class
Shared database functionality for all Florida data agents
"""

import asyncio
import asyncpg
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

from supabase_config import supabase_config, SupabaseOptimizer, SupabaseUpdateMonitor

logger = logging.getLogger(__name__)

class BaseSupabaseDB(ABC):
    """Base database class for Supabase operations"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.pool: Optional[asyncpg.Pool] = None
        self.supabase = supabase_config.get_supabase_client()
        self.monitor: Optional[SupabaseUpdateMonitor] = None
        self.optimizer = SupabaseOptimizer()
        
    async def connect(self):
        """Connect to Supabase database"""
        if not self.pool:
            self.pool = await supabase_config.get_db_pool()
            self.monitor = SupabaseUpdateMonitor(self.pool)
            await self.monitor.initialize_tracking_tables()
            await self.create_tables()
            logger.info(f"{self.agent_name} connected to Supabase")
    
    async def disconnect(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info(f"{self.agent_name} disconnected from Supabase")
    
    @abstractmethod
    async def create_tables(self):
        """Create agent-specific tables - must be implemented by subclasses"""
        pass
    
    async def check_for_updates(self, source_url: str, file_path: str = None) -> bool:
        """Check if data source has been updated"""
        if not file_path:
            return True
        
        # Calculate file hash if file exists
        file_hash = None
        file_size = None
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            file_size = os.path.getsize(file_path)
        
        return await self.monitor.check_for_update(
            self.agent_name, 
            source_url, 
            file_hash, 
            file_size
        )
    
    async def record_update(self, source_url: str, stats: Dict[str, Any]):
        """Record update results"""
        await self.monitor.record_update(self.agent_name, source_url, stats)
    
    async def update_agent_status(self, status: str, error: str = None, 
                                 runtime_seconds: float = None):
        """Update agent status"""
        from datetime import datetime, timedelta
        
        # Calculate next run based on schedule
        schedule = supabase_config.AGENT_SCHEDULES.get(self.agent_name, {})
        next_run = self.calculate_next_run(schedule)
        
        await self.monitor.update_agent_status(self.agent_name, {
            'is_active': error is None,
            'last_run': datetime.now(),
            'next_run': next_run,
            'average_runtime_seconds': runtime_seconds,
            'last_error': error,
            'configuration': schedule
        })
    
    def calculate_next_run(self, schedule: Dict) -> datetime:
        """Calculate next run time based on schedule"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        frequency = schedule.get('frequency', 'daily')
        time_str = schedule.get('time', '00:00')
        hour, minute = map(int, time_str.split(':'))
        
        if frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == 'weekly':
            days_ahead = 7  # Default to weekly
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        elif frequency == 'monthly':
            next_run = now.replace(day=schedule.get('day', 1), hour=hour, minute=minute)
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        else:
            next_run = now + timedelta(hours=1)  # Default fallback
        
        return next_run
    
    async def bulk_upsert(self, table_name: str, records: List[Dict], 
                         unique_columns: List[str], batch_size: int = 1000) -> Dict:
        """Bulk upsert records to Supabase"""
        stats = {
            'total': len(records),
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        if not records:
            return stats
        
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            try:
                # Build the INSERT ... ON CONFLICT query
                columns = list(batch[0].keys())
                placeholders = [f"${j+1}" for j in range(len(columns))]
                
                on_conflict = f"ON CONFLICT ({', '.join(unique_columns)}) DO UPDATE SET "
                update_cols = [f"{col} = EXCLUDED.{col}" for col in columns 
                             if col not in unique_columns and col != 'created_at']
                
                query = f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    {on_conflict} {', '.join(update_cols)}
                    RETURNING (xmax = 0) AS inserted
                """
                
                async with self.pool.acquire() as conn:
                    # Use prepared statement for better performance
                    stmt = await conn.prepare(query)
                    
                    for record in batch:
                        result = await stmt.fetchrow(*[record[col] for col in columns])
                        if result['inserted']:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1
                            
            except Exception as e:
                logger.error(f"Bulk upsert error: {e}")
                stats['errors'] += len(batch)
        
        return stats
    
    async def get_latest_records(self, table_name: str, limit: int = 100, 
                                filters: Dict = None) -> List[Dict]:
        """Get latest records from a table"""
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if filters:
            where_clauses = []
            for i, (key, value) in enumerate(filters.items(), 1):
                where_clauses.append(f"{key} = ${i}")
                params.append(value)
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def optimize_tables(self, tables: List[str]):
        """Optimize database tables for performance"""
        await self.optimizer.analyze_tables(self.pool, tables)
    
    async def refresh_views(self, views: List[str]):
        """Refresh materialized views"""
        for view in views:
            await self.optimizer.refresh_materialized_view(self.pool, view)
    
    async def get_analytics(self, query: str, params: List = None) -> List[Dict]:
        """Execute analytics query"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *(params or []))
            return [dict(row) for row in rows]
    
    async def log_job(self, job_data: Dict):
        """Log job execution to tracking table"""
        job_data['agent_name'] = self.agent_name
        await self.record_update(
            job_data.get('source_url', 'manual_run'),
            job_data
        )