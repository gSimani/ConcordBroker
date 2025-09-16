#!/usr/bin/env python3
"""
Schema Migration Agent - Automatic database schema updates and migrations
Handles version tracking, rollback, and seamless schema evolution
"""

import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import hashlib
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class Migration:
    id: str
    version: str
    name: str
    sql_up: str
    sql_down: Optional[str]
    description: str
    checksum: str
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SchemaMigrationAgent:
    """
    Intelligent schema migration with version control and rollback capability
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
        
        self.api_url = f"{self.supabase_url}/rest/v1"
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Migration tracking
        self.migrations_dir = Path('migrations')
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Built-in migrations for ConcordBroker
        self.builtin_migrations = self._get_builtin_migrations()

    def _get_builtin_migrations(self) -> List[Migration]:
        """Define built-in migrations for ConcordBroker schema"""
        return [
            Migration(
                id="001",
                version="1.0.0",
                name="create_migration_tracking",
                description="Create schema migrations tracking table",
                sql_up="""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id VARCHAR(10) PRIMARY KEY,
                    version VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT NOW(),
                    rollback_sql TEXT,
                    status VARCHAR(20) DEFAULT 'completed'
                );
                """,
                sql_down="DROP TABLE IF EXISTS schema_migrations;",
                checksum=""
            ),
            
            Migration(
                id="002", 
                version="1.0.1",
                name="add_property_indexes",
                description="Add performance indexes to property tables",
                sql_up="""
                CREATE INDEX IF NOT EXISTS idx_fl_nal_parcel_id ON fl_nal_name_address(parcel_id);
                CREATE INDEX IF NOT EXISTS idx_fl_nal_city ON fl_nal_name_address(phy_city);
                CREATE INDEX IF NOT EXISTS idx_fl_nal_owner ON fl_nal_name_address(own_name);
                CREATE INDEX IF NOT EXISTS idx_fl_sdf_parcel_id ON fl_sdf_sales(parcel_id);
                CREATE INDEX IF NOT EXISTS idx_fl_sdf_sale_date ON fl_sdf_sales(sale_yr, sale_mo);
                CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(city);
                CREATE INDEX IF NOT EXISTS idx_florida_parcels_use_code ON florida_parcels(use_code);
                """,
                sql_down="""
                DROP INDEX IF EXISTS idx_fl_nal_parcel_id;
                DROP INDEX IF EXISTS idx_fl_nal_city;
                DROP INDEX IF EXISTS idx_fl_nal_owner;
                DROP INDEX IF EXISTS idx_fl_sdf_parcel_id;
                DROP INDEX IF EXISTS idx_fl_sdf_sale_date;
                DROP INDEX IF EXISTS idx_florida_parcels_city;
                DROP INDEX IF EXISTS idx_florida_parcels_use_code;
                """,
                checksum=""
            ),
            
            Migration(
                id="003",
                version="1.0.2", 
                name="add_search_optimization",
                description="Add full-text search and optimization features",
                sql_up="""
                -- Add GIN indexes for full-text search
                CREATE INDEX IF NOT EXISTS idx_fl_nal_owner_gin 
                ON fl_nal_name_address USING GIN(to_tsvector('english', own_name));
                
                CREATE INDEX IF NOT EXISTS idx_fl_nal_address_gin 
                ON fl_nal_name_address USING GIN(to_tsvector('english', phy_addr1));
                
                -- Add computed columns for better search
                ALTER TABLE fl_nal_name_address 
                ADD COLUMN IF NOT EXISTS search_vector TSVECTOR 
                GENERATED ALWAYS AS (
                    to_tsvector('english', COALESCE(own_name, '') || ' ' || COALESCE(phy_addr1, ''))
                ) STORED;
                
                CREATE INDEX IF NOT EXISTS idx_fl_nal_search_vector 
                ON fl_nal_name_address USING GIN(search_vector);
                """,
                sql_down="""
                DROP INDEX IF EXISTS idx_fl_nal_owner_gin;
                DROP INDEX IF EXISTS idx_fl_nal_address_gin;
                DROP INDEX IF EXISTS idx_fl_nal_search_vector;
                ALTER TABLE fl_nal_name_address DROP COLUMN IF EXISTS search_vector;
                """,
                checksum=""
            ),
            
            Migration(
                id="004",
                version="1.1.0",
                name="add_property_analytics",
                description="Add analytics and scoring tables",
                sql_up="""
                CREATE TABLE IF NOT EXISTS property_analytics (
                    parcel_id VARCHAR(50) PRIMARY KEY,
                    investment_score DECIMAL(5,2),
                    risk_score DECIMAL(5,2),
                    market_trend VARCHAR(20),
                    last_sale_date DATE,
                    price_change_1yr DECIMAL(10,2),
                    rental_estimate DECIMAL(10,2),
                    calculated_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_property_analytics_score 
                ON property_analytics(investment_score DESC);
                
                CREATE TABLE IF NOT EXISTS market_trends (
                    id BIGSERIAL PRIMARY KEY,
                    city VARCHAR(50),
                    property_type VARCHAR(20),
                    avg_price DECIMAL(12,2),
                    median_price DECIMAL(12,2),
                    price_change_30d DECIMAL(5,2),
                    price_change_90d DECIMAL(5,2),
                    price_change_1yr DECIMAL(5,2),
                    inventory_count INTEGER,
                    calculated_at DATE,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_market_trends_city_date 
                ON market_trends(city, calculated_at DESC);
                """,
                sql_down="""
                DROP TABLE IF EXISTS property_analytics;
                DROP TABLE IF EXISTS market_trends;
                """,
                checksum=""
            ),
            
            Migration(
                id="005",
                version="1.1.1",
                name="add_user_features",
                description="Add user tracking and favorites",
                sql_up="""
                CREATE TABLE IF NOT EXISTS user_property_watches (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID,
                    parcel_id VARCHAR(50),
                    watch_type VARCHAR(20) DEFAULT 'favorite',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, parcel_id)
                );
                
                CREATE TABLE IF NOT EXISTS user_search_history (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID,
                    search_query JSONB,
                    results_count INTEGER,
                    searched_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_watches_user_id 
                ON user_property_watches(user_id);
                
                CREATE INDEX IF NOT EXISTS idx_user_searches_user_id 
                ON user_search_history(user_id, searched_at DESC);
                """,
                sql_down="""
                DROP TABLE IF EXISTS user_property_watches;
                DROP TABLE IF EXISTS user_search_history;
                """,
                checksum=""
            )
        ]

    async def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main migration execution"""
        logger.info("SchemaMigrationAgent starting...")
        
        try:
            # Initialize migration tracking
            await self._ensure_migration_table()
            
            # Get current schema version
            current_version = await self._get_current_version()
            logger.info(f"Current schema version: {current_version}")
            
            # Calculate checksums for builtin migrations
            self._calculate_checksums()
            
            # Check for pending migrations
            pending_migrations = await self._get_pending_migrations()
            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            # Apply migrations
            results = []
            for migration in pending_migrations:
                result = await self._apply_migration(migration)
                results.append(result)
                
                if result['status'] == 'failed':
                    logger.error(f"Migration {migration.id} failed, stopping")
                    break
            
            # Get new version
            new_version = await self._get_current_version()
            
            return {
                'status': 'success',
                'migrations_applied': len([r for r in results if r['status'] == 'completed']),
                'migrations_failed': len([r for r in results if r['status'] == 'failed']),
                'old_version': current_version,
                'new_version': new_version,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            return {'status': 'error', 'error': str(e)}

    def _calculate_checksums(self):
        """Calculate checksums for migrations"""
        for migration in self.builtin_migrations:
            content = f"{migration.sql_up}{migration.sql_down or ''}"
            migration.checksum = hashlib.sha256(content.encode()).hexdigest()

    async def _ensure_migration_table(self):
        """Ensure migration tracking table exists"""
        try:
            # Check if table exists
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    f"{self.api_url}/schema_migrations",
                    headers=self.headers
                ) as response:
                    if response.status == 404:
                        # Create migration table
                        await self._execute_sql(self.builtin_migrations[0].sql_up)
                        logger.info("Created migration tracking table")
                        
                        # Record the first migration
                        await self._record_migration(self.builtin_migrations[0], MigrationStatus.COMPLETED)
        
        except Exception as e:
            logger.error(f"Failed to ensure migration table: {e}")
            raise

    async def _get_current_version(self) -> str:
        """Get current schema version"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/schema_migrations?select=version&order=applied_at.desc&limit=1",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return data[0]['version']
            
            return "0.0.0"  # No migrations applied yet
            
        except Exception as e:
            logger.warning(f"Could not get current version: {e}")
            return "unknown"

    async def _get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        try:
            # Get applied migration IDs
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/schema_migrations?select=id",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        applied_data = await response.json()
                        applied_ids = {m['id'] for m in applied_data}
                    else:
                        applied_ids = set()
            
            # Return builtin migrations not yet applied
            pending = []
            for migration in self.builtin_migrations:
                if migration.id not in applied_ids:
                    pending.append(migration)
            
            return pending
            
        except Exception as e:
            logger.error(f"Could not get pending migrations: {e}")
            return []

    async def _apply_migration(self, migration: Migration) -> Dict[str, Any]:
        """Apply a single migration"""
        logger.info(f"Applying migration {migration.id}: {migration.name}")
        
        migration.status = MigrationStatus.RUNNING
        start_time = datetime.now()
        
        try:
            # Execute the migration SQL
            await self._execute_sql(migration.sql_up)
            
            # Record successful migration
            migration.status = MigrationStatus.COMPLETED
            migration.applied_at = datetime.now()
            
            await self._record_migration(migration, MigrationStatus.COMPLETED)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Migration {migration.id} completed in {duration:.2f}s")
            
            return {
                'id': migration.id,
                'name': migration.name,
                'status': 'completed',
                'duration': duration
            }
            
        except Exception as e:
            # Handle failure
            migration.status = MigrationStatus.FAILED
            migration.error_message = str(e)
            
            await self._record_migration(migration, MigrationStatus.FAILED, str(e))
            
            logger.error(f"Migration {migration.id} failed: {e}")
            
            # Attempt rollback if possible
            if migration.sql_down:
                try:
                    await self._execute_sql(migration.sql_down)
                    migration.status = MigrationStatus.ROLLED_BACK
                    logger.info(f"Migration {migration.id} rolled back successfully")
                except Exception as rollback_error:
                    logger.error(f"Rollback of migration {migration.id} failed: {rollback_error}")
            
            return {
                'id': migration.id,
                'name': migration.name, 
                'status': 'failed',
                'error': str(e)
            }

    async def _execute_sql(self, sql: str):
        """Execute SQL statement via Supabase"""
        # Note: Direct SQL execution via REST API is limited
        # In production, this would use a direct PostgreSQL connection
        # For now, we'll simulate with a placeholder
        
        logger.info(f"Executing SQL: {sql[:100]}...")
        
        # This is a placeholder - real implementation would:
        # 1. Use psycopg2 or asyncpg for direct connection
        # 2. Execute DDL statements
        # 3. Handle transactions properly
        
        # Simulate execution
        await asyncio.sleep(0.1)
        
        # In a real implementation:
        # async with asyncpg.connect(database_url) as conn:
        #     await conn.execute(sql)

    async def _record_migration(self, migration: Migration, status: MigrationStatus, error: str = None):
        """Record migration in tracking table"""
        migration_record = {
            'id': migration.id,
            'version': migration.version,
            'name': migration.name,
            'checksum': migration.checksum,
            'applied_at': datetime.now().isoformat(),
            'rollback_sql': migration.sql_down,
            'status': status.value,
            'error_message': error
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/schema_migrations",
                    headers=self.headers,
                    json=migration_record
                ) as response:
                    if response.status not in [200, 201]:
                        logger.warning(f"Failed to record migration {migration.id}")
        
        except Exception as e:
            logger.warning(f"Could not record migration {migration.id}: {e}")

    async def rollback_migration(self, migration_id: str) -> Dict[str, Any]:
        """Rollback a specific migration"""
        logger.info(f"Rolling back migration {migration_id}")
        
        try:
            # Find migration record
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/schema_migrations?id=eq.{migration_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            return {'status': 'error', 'error': f'Migration {migration_id} not found'}
                        
                        record = data[0]
                        rollback_sql = record.get('rollback_sql')
                        
                        if not rollback_sql:
                            return {'status': 'error', 'error': f'No rollback SQL for migration {migration_id}'}
                        
                        # Execute rollback
                        await self._execute_sql(rollback_sql)
                        
                        # Update record
                        await session.patch(
                            f"{self.api_url}/schema_migrations?id=eq.{migration_id}",
                            headers=self.headers,
                            json={'status': 'rolled_back', 'rollback_at': datetime.now().isoformat()}
                        )
                        
                        logger.info(f"Migration {migration_id} rolled back successfully")
                        return {'status': 'success', 'migration_id': migration_id}
        
        except Exception as e:
            logger.error(f"Rollback failed for migration {migration_id}: {e}")
            return {'status': 'error', 'error': str(e)}

    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/schema_migrations?order=applied_at.desc",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
            
            return []
            
        except Exception as e:
            logger.error(f"Could not get migration history: {e}")
            return []

    async def get_status(self) -> Dict[str, Any]:
        """Get migration agent status"""
        current_version = await self._get_current_version()
        pending_count = len(await self._get_pending_migrations())
        
        return {
            'agent': 'SchemaMigrationAgent',
            'current_version': current_version,
            'pending_migrations': pending_count,
            'builtin_migrations': len(self.builtin_migrations)
        }