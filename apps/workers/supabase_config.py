"""
Supabase Configuration and Connection Management
Centralized configuration for all data agents to use Supabase
"""

import os
from typing import Optional, Dict, Any
import asyncpg
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseConfig:
    """Centralized Supabase configuration for all agents"""
    
    # Supabase credentials (set these in environment variables)
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
    SUPABASE_ANON_KEY: str = os.getenv('SUPABASE_ANON_KEY', 'your-anon-key')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', 'your-service-key')
    
    # Direct database connection (for bulk operations)
    SUPABASE_DB_URL: str = os.getenv(
        'SUPABASE_DB_URL',
        'postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres'
    )
    
    # Connection pooling settings
    POOL_MIN_SIZE: int = 2
    POOL_MAX_SIZE: int = 10
    POOL_MAX_QUERIES: int = 50000
    POOL_MAX_INACTIVE_CONNECTION_LIFETIME: float = 300.0
    
    # Data update settings
    UPDATE_CHECK_INTERVAL: int = 3600  # Check for updates every hour
    ENABLE_AUTO_UPDATES: bool = True
    ENABLE_NOTIFICATIONS: bool = True
    
    # County configurations
    COUNTIES = {
        'broward': {'code': '16', 'name': 'Broward', 'active': True},
        'miami_dade': {'code': '25', 'name': 'Miami-Dade', 'active': True},
        'palm_beach': {'code': '50', 'name': 'Palm Beach', 'active': True}
    }
    
    # Agent update schedules (cron-like)
    AGENT_SCHEDULES = {
        'sunbiz': {'frequency': 'daily', 'time': '02:00'},
        'bcpa': {'frequency': 'daily', 'time': '03:00'},
        'official_records': {'frequency': 'daily', 'time': '04:00'},
        'tpp': {'frequency': 'weekly', 'day': 'monday', 'time': '05:00'},
        'nav': {'frequency': 'weekly', 'day': 'tuesday', 'time': '05:00'},
        'sdf_sales': {'frequency': 'daily', 'time': '06:00'},
        'dor_processor': {'frequency': 'monthly', 'day': 1, 'time': '01:00'}
    }
    
    @classmethod
    def get_supabase_client(cls) -> Client:
        """Get Supabase client for API operations"""
        return create_client(cls.SUPABASE_URL, cls.SUPABASE_SERVICE_KEY)
    
    @classmethod
    async def get_db_pool(cls) -> asyncpg.Pool:
        """Get database connection pool for bulk operations"""
        return await asyncpg.create_pool(
            cls.SUPABASE_DB_URL,
            min_size=cls.POOL_MIN_SIZE,
            max_size=cls.POOL_MAX_SIZE,
            max_queries=cls.POOL_MAX_QUERIES,
            max_inactive_connection_lifetime=cls.POOL_MAX_INACTIVE_CONNECTION_LIFETIME,
            command_timeout=60
        )
    
    @classmethod
    def get_table_name(cls, agent_name: str, table_suffix: str = '') -> str:
        """Generate consistent table names for Supabase"""
        prefix = f"fl_{agent_name}"
        if table_suffix:
            return f"{prefix}_{table_suffix}"
        return prefix
    
    @classmethod
    def get_update_tracking_table(cls) -> str:
        """Get the name of the update tracking table"""
        return "fl_data_updates"
    
    @classmethod
    def get_agent_status_table(cls) -> str:
        """Get the name of the agent status table"""
        return "fl_agent_status"

class SupabaseOptimizer:
    """Database optimization utilities for Supabase"""
    
    @staticmethod
    async def create_optimized_indexes(pool: asyncpg.Pool, table_name: str, indexes: Dict[str, str]):
        """Create optimized indexes for a table"""
        async with pool.acquire() as conn:
            for index_name, index_def in indexes.items():
                try:
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {table_name} {index_def}
                    """)
                    logger.info(f"Created index {index_name} on {table_name}")
                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
    
    @staticmethod
    async def enable_row_level_security(pool: asyncpg.Pool, table_name: str):
        """Enable row-level security for a table"""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY
            """)
            logger.info(f"Enabled RLS on {table_name}")
    
    @staticmethod
    async def create_materialized_view(pool: asyncpg.Pool, view_name: str, query: str):
        """Create a materialized view for performance"""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS
                {query}
            """)
            
            # Create index on materialized view
            await conn.execute(f"""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_{view_name}_id
                ON {view_name} (id)
            """)
            logger.info(f"Created materialized view {view_name}")
    
    @staticmethod
    async def refresh_materialized_view(pool: asyncpg.Pool, view_name: str, concurrent: bool = True):
        """Refresh a materialized view"""
        async with pool.acquire() as conn:
            concurrently = "CONCURRENTLY" if concurrent else ""
            await conn.execute(f"""
                REFRESH MATERIALIZED VIEW {concurrently} {view_name}
            """)
            logger.info(f"Refreshed materialized view {view_name}")
    
    @staticmethod
    async def analyze_tables(pool: asyncpg.Pool, tables: list):
        """Run ANALYZE on tables for query optimization"""
        async with pool.acquire() as conn:
            for table in tables:
                await conn.execute(f"ANALYZE {table}")
                logger.info(f"Analyzed table {table}")
    
    @staticmethod
    async def create_partition(pool: asyncpg.Pool, parent_table: str, partition_key: str, partition_type: str = 'RANGE'):
        """Create table partitioning for large datasets"""
        async with pool.acquire() as conn:
            # Example for monthly partitioning by date
            if partition_type == 'RANGE' and 'date' in partition_key:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {parent_table}_2025_01 
                    PARTITION OF {parent_table}
                    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01')
                """)
                logger.info(f"Created partition for {parent_table}")

class SupabaseUpdateMonitor:
    """Monitor data sources for updates"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def initialize_tracking_tables(self):
        """Create tables for tracking updates"""
        async with self.pool.acquire() as conn:
            # Update tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_data_updates (
                    id SERIAL PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    source_url TEXT,
                    last_checked TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_modified TIMESTAMP WITH TIME ZONE,
                    file_hash TEXT,
                    file_size BIGINT,
                    status TEXT DEFAULT 'pending',
                    records_processed INTEGER DEFAULT 0,
                    new_records INTEGER DEFAULT 0,
                    updated_records INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(agent_name, source_url)
                )
            """)
            
            # Agent status table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_agent_status (
                    agent_name TEXT PRIMARY KEY,
                    is_active BOOLEAN DEFAULT true,
                    last_run TIMESTAMP WITH TIME ZONE,
                    next_run TIMESTAMP WITH TIME ZONE,
                    total_runs INTEGER DEFAULT 0,
                    successful_runs INTEGER DEFAULT 0,
                    failed_runs INTEGER DEFAULT 0,
                    average_runtime_seconds FLOAT,
                    last_error TEXT,
                    configuration JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updates_agent_status 
                ON fl_data_updates(agent_name, status)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updates_last_checked 
                ON fl_data_updates(last_checked)
            """)
    
    async def check_for_update(self, agent_name: str, source_url: str, 
                              current_hash: str = None, current_size: int = None) -> bool:
        """Check if a data source has been updated"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT file_hash, file_size, last_modified
                FROM fl_data_updates
                WHERE agent_name = $1 AND source_url = $2
            """, agent_name, source_url)
            
            if not result:
                # First time checking this source
                return True
            
            # Check if file has changed
            if current_hash and result['file_hash'] != current_hash:
                return True
            
            if current_size and result['file_size'] != current_size:
                return True
            
            return False
    
    async def record_update(self, agent_name: str, source_url: str, 
                           update_data: Dict[str, Any]):
        """Record an update check result"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_data_updates (
                    agent_name, source_url, last_modified, file_hash, file_size,
                    status, records_processed, new_records, updated_records,
                    error_message, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (agent_name, source_url) 
                DO UPDATE SET
                    last_checked = NOW(),
                    last_modified = $3,
                    file_hash = $4,
                    file_size = $5,
                    status = $6,
                    records_processed = $7,
                    new_records = $8,
                    updated_records = $9,
                    error_message = $10,
                    metadata = $11
            """, agent_name, source_url, 
                update_data.get('last_modified'),
                update_data.get('file_hash'),
                update_data.get('file_size'),
                update_data.get('status', 'completed'),
                update_data.get('records_processed', 0),
                update_data.get('new_records', 0),
                update_data.get('updated_records', 0),
                update_data.get('error_message'),
                update_data.get('metadata', {})
            )
    
    async def update_agent_status(self, agent_name: str, status_data: Dict[str, Any]):
        """Update agent status"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_agent_status (
                    agent_name, is_active, last_run, next_run, total_runs,
                    successful_runs, failed_runs, average_runtime_seconds,
                    last_error, configuration
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (agent_name) 
                DO UPDATE SET
                    is_active = $2,
                    last_run = $3,
                    next_run = $4,
                    total_runs = fl_agent_status.total_runs + 1,
                    successful_runs = CASE 
                        WHEN $9 IS NULL THEN fl_agent_status.successful_runs + 1
                        ELSE fl_agent_status.successful_runs
                    END,
                    failed_runs = CASE
                        WHEN $9 IS NOT NULL THEN fl_agent_status.failed_runs + 1
                        ELSE fl_agent_status.failed_runs
                    END,
                    average_runtime_seconds = $8,
                    last_error = $9,
                    configuration = $10,
                    updated_at = NOW()
            """, agent_name,
                status_data.get('is_active', True),
                status_data.get('last_run'),
                status_data.get('next_run'),
                status_data.get('total_runs', 0),
                status_data.get('successful_runs', 0),
                status_data.get('failed_runs', 0),
                status_data.get('average_runtime_seconds'),
                status_data.get('last_error'),
                status_data.get('configuration', {})
            )
    
    async def get_pending_updates(self) -> list:
        """Get list of pending updates to process"""
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT agent_name, source_url, last_checked
                FROM fl_data_updates
                WHERE status = 'pending'
                OR last_checked < NOW() - INTERVAL '1 hour'
                ORDER BY last_checked ASC
            """)

# Export configuration
supabase_config = SupabaseConfig()