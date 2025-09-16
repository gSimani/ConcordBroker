#!/usr/bin/env python3
"""
Advanced Pipeline Implementation for Supabase
Implements the top optimization strategies from research
"""

import psycopg2
import redis
import asyncio
import hashlib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import aioredis
import asyncpg

logging.basicConfig(level=logging.INFO)

# ============================================================
# 1. PARTITIONING MANAGER
# ============================================================

class PartitionManager:
    """Manages table partitioning for optimal query performance"""

    def __init__(self, conn):
        self.conn = conn

    def create_county_partitions(self):
        """Create partitions by county for florida_parcels"""
        cursor = self.conn.cursor()

        # Get list of counties
        cursor.execute("""
            SELECT DISTINCT county
            FROM florida_parcels
            WHERE county IS NOT NULL
            ORDER BY county
        """)
        counties = [row[0] for row in cursor.fetchall()]

        # Create parent partitioned table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS florida_parcels_partitioned (
                LIKE florida_parcels INCLUDING ALL
            ) PARTITION BY LIST (county)
        """)

        # Create partition for each county
        for county in counties:
            partition_name = f"florida_parcels_{county.lower().replace(' ', '_')}"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF florida_parcels_partitioned
                FOR VALUES IN ('{county}')
            """)
            logging.info(f"Created partition for {county}")

        self.conn.commit()
        cursor.close()

        return counties

    def migrate_to_partitioned(self, batch_size=10000):
        """Migrate data to partitioned table"""
        cursor = self.conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM florida_parcels")
        total = cursor.fetchone()[0]

        # Migrate in batches
        for offset in range(0, total, batch_size):
            cursor.execute(f"""
                INSERT INTO florida_parcels_partitioned
                SELECT * FROM florida_parcels
                LIMIT {batch_size} OFFSET {offset}
                ON CONFLICT DO NOTHING
            """)
            self.conn.commit()
            logging.info(f"Migrated {offset + batch_size}/{total} records")

        cursor.close()

# ============================================================
# 2. MATERIALIZED VIEW MANAGER
# ============================================================

class MaterializedViewManager:
    """Manages materialized views for fast analytics"""

    def __init__(self, conn):
        self.conn = conn

    def create_analytics_views(self):
        """Create materialized views for common analytics"""
        views = [
            {
                'name': 'mv_county_statistics',
                'query': """
                    SELECT
                        county,
                        COUNT(*) as property_count,
                        AVG(just_value) as avg_value,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY just_value) as median_value,
                        SUM(just_value) as total_value,
                        AVG(total_living_area) as avg_living_area,
                        COUNT(DISTINCT owner_name) as unique_owners
                    FROM florida_parcels
                    WHERE just_value > 0
                    GROUP BY county
                """
            },
            {
                'name': 'mv_monthly_sales',
                'query': """
                    SELECT
                        county,
                        DATE_TRUNC('month', sale_date) as month,
                        COUNT(*) as sale_count,
                        AVG(sale_price) as avg_price,
                        MIN(sale_price) as min_price,
                        MAX(sale_price) as max_price,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price) as median_price
                    FROM florida_parcels
                    WHERE sale_price > 0 AND sale_date IS NOT NULL
                    GROUP BY county, DATE_TRUNC('month', sale_date)
                """
            },
            {
                'name': 'mv_property_valuations',
                'query': """
                    SELECT
                        parcel_id,
                        county,
                        just_value,
                        sale_price,
                        CASE
                            WHEN sale_price > 0 THEN sale_price / just_value
                            ELSE NULL
                        END as price_to_value_ratio,
                        total_living_area,
                        year_built,
                        bedrooms,
                        bathrooms,
                        land_sqft,
                        CASE
                            WHEN total_living_area > 0 THEN just_value / total_living_area
                            ELSE NULL
                        END as value_per_sqft
                    FROM florida_parcels
                    WHERE just_value > 0
                """
            }
        ]

        cursor = self.conn.cursor()

        for view in views:
            cursor.execute(f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {view['name']} AS
                {view['query']}
                WITH DATA
            """)

            # Create indexes on materialized views
            if 'county' in view['query']:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{view['name']}_county
                    ON {view['name']}(county)
                """)

            self.conn.commit()
            logging.info(f"Created materialized view: {view['name']}")

        cursor.close()

    def refresh_views(self, concurrent=True):
        """Refresh materialized views"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT matviewname
            FROM pg_matviews
            WHERE schemaname = 'public'
        """)

        views = [row[0] for row in cursor.fetchall()]

        for view in views:
            if concurrent:
                cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
            else:
                cursor.execute(f"REFRESH MATERIALIZED VIEW {view}")

            logging.info(f"Refreshed view: {view}")

        self.conn.commit()
        cursor.close()

# ============================================================
# 3. INTELLIGENT CACHE SYSTEM
# ============================================================

class IntelligentCache:
    """Multi-tier caching with predictive preloading"""

    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            db=0
        )
        self.cache_stats = {'hits': 0, 'misses': 0}

    def _generate_key(self, query: str, params: tuple) -> str:
        """Generate cache key from query and parameters"""
        key_str = f"{query}:{json.dumps(params, default=str)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, params: tuple = ()) -> Optional[Any]:
        """Get from cache"""
        key = self._generate_key(query, params)
        cached = self.redis_client.get(key)

        if cached:
            self.cache_stats['hits'] += 1
            return json.loads(cached)
        else:
            self.cache_stats['misses'] += 1
            return None

    def set(self, query: str, params: tuple, data: Any, ttl: int = 3600):
        """Set cache with TTL"""
        key = self._generate_key(query, params)
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(data, default=str)
        )

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0

        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': hit_rate,
            'memory_usage': self.redis_client.info()['used_memory_human']
        }

    def preload_common_queries(self, conn):
        """Preload frequently accessed queries"""
        common_queries = [
            ("SELECT COUNT(*) FROM florida_parcels", ()),
            ("SELECT DISTINCT county FROM florida_parcels ORDER BY county", ()),
            ("SELECT * FROM mv_county_statistics ORDER BY property_count DESC", ())
        ]

        cursor = conn.cursor()

        for query, params in common_queries:
            cursor.execute(query, params)
            data = cursor.fetchall()
            self.set(query, params, data, ttl=7200)  # 2 hour TTL

        cursor.close()
        logging.info(f"Preloaded {len(common_queries)} common queries")

# ============================================================
# 4. DATA VERIFICATION PIPELINE
# ============================================================

@dataclass
class ValidationRule:
    field: str
    validator: callable
    error_message: str
    severity: str = 'ERROR'

class DataVerificationPipeline:
    """Real-time data verification with quarantine"""

    def __init__(self, conn):
        self.conn = conn
        self.rules = self._define_rules()
        self.stats = {'processed': 0, 'valid': 0, 'invalid': 0}

    def _define_rules(self) -> Dict[str, List[ValidationRule]]:
        """Define validation rules for each table"""
        return {
            'florida_parcels': [
                ValidationRule(
                    'parcel_id',
                    lambda x: x and len(str(x)) >= 5,
                    'Invalid parcel ID'
                ),
                ValidationRule(
                    'just_value',
                    lambda x: 0 <= x <= 100_000_000 if x else True,
                    'Value out of range'
                ),
                ValidationRule(
                    'year_built',
                    lambda x: 1800 <= x <= datetime.now().year if x else True,
                    'Invalid year built'
                ),
                ValidationRule(
                    'county',
                    lambda x: x and x.upper() in self._get_valid_counties(),
                    'Invalid county'
                ),
                ValidationRule(
                    '_consistency',
                    lambda row: abs(row.get('just_value', 0) -
                                  (row.get('land_value', 0) +
                                   row.get('building_value', 0))) < 10000,
                    'Value consistency check failed',
                    severity='WARNING'
                )
            ]
        }

    def _get_valid_counties(self) -> set:
        """Get list of valid Florida counties"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT county FROM florida_parcels WHERE county IS NOT NULL")
        counties = {row[0].upper() for row in cursor.fetchall()}
        cursor.close()
        return counties

    def validate_record(self, table: str, record: Dict) -> tuple[bool, List[str]]:
        """Validate a single record"""
        if table not in self.rules:
            return True, []

        errors = []
        for rule in self.rules[table]:
            if rule.field.startswith('_'):
                # Special case for multi-field validation
                if not rule.validator(record):
                    errors.append(f"{rule.severity}: {rule.error_message}")
            else:
                value = record.get(rule.field)
                if not rule.validator(value):
                    errors.append(f"{rule.severity}: {rule.field} - {rule.error_message}")

        self.stats['processed'] += 1
        if not errors or all('WARNING' in e for e in errors):
            self.stats['valid'] += 1
            return True, errors
        else:
            self.stats['invalid'] += 1
            return False, errors

    def validate_batch(self, table: str, records: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """Validate a batch of records"""
        valid_records = []
        invalid_records = []

        for record in records:
            is_valid, errors = self.validate_record(table, record)

            if is_valid:
                valid_records.append(record)
            else:
                record['_validation_errors'] = errors
                invalid_records.append(record)

        return valid_records, invalid_records

    def quarantine_invalid(self, records: List[Dict]):
        """Move invalid records to quarantine table"""
        if not records:
            return

        cursor = self.conn.cursor()

        # Create quarantine table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_quarantine (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(255),
                record_data JSONB,
                validation_errors TEXT[],
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Insert invalid records
        for record in records:
            cursor.execute("""
                INSERT INTO data_quarantine (table_name, record_data, validation_errors)
                VALUES (%s, %s, %s)
            """, (
                record.get('_table', 'unknown'),
                json.dumps(record),
                record.get('_validation_errors', [])
            ))

        self.conn.commit()
        cursor.close()

        logging.info(f"Quarantined {len(records)} invalid records")

# ============================================================
# 5. ASYNC PROCESSING ENGINE
# ============================================================

class AsyncProcessingEngine:
    """Asynchronous processing for high throughput"""

    def __init__(self, db_url: str, max_workers: int = 10):
        self.db_url = db_url
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = []

    async def process_batch_async(self, records: List[Dict], processor_func: callable):
        """Process records asynchronously"""
        loop = asyncio.get_event_loop()

        # Create database pool
        pool = await asyncpg.create_pool(self.db_url, min_size=5, max_size=20)

        try:
            # Process records in parallel
            tasks = []
            for record in records:
                task = loop.create_task(self._process_record(pool, record, processor_func))
                tasks.append(task)

            # Wait for all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]

            logging.info(f"Processed {len(successful)} successfully, {len(failed)} failed")

            return successful, failed

        finally:
            await pool.close()

    async def _process_record(self, pool, record, processor_func):
        """Process single record"""
        async with pool.acquire() as conn:
            return await processor_func(conn, record)

# ============================================================
# 6. REAL-TIME CDC PIPELINE
# ============================================================

class CDCPipeline:
    """Change Data Capture pipeline for real-time updates"""

    def __init__(self, conn):
        self.conn = conn
        self.listeners = {}

    def setup_triggers(self, table: str):
        """Setup database triggers for CDC"""
        cursor = self.conn.cursor()

        # Create notification function
        cursor.execute(f"""
            CREATE OR REPLACE FUNCTION notify_{table}_changes()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM pg_notify(
                    '{table}_changes',
                    json_build_object(
                        'operation', TG_OP,
                        'table', TG_TABLE_NAME,
                        'data', row_to_json(NEW)
                    )::text
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create trigger
        cursor.execute(f"""
            CREATE TRIGGER {table}_change_trigger
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION notify_{table}_changes();
        """)

        self.conn.commit()
        cursor.close()

        logging.info(f"Setup CDC triggers for {table}")

    def listen(self, channel: str, callback: callable):
        """Listen for changes on a channel"""
        cursor = self.conn.cursor()
        cursor.execute(f"LISTEN {channel}")
        self.conn.commit()

        self.listeners[channel] = callback
        logging.info(f"Listening on channel: {channel}")

    def process_notifications(self):
        """Process pending notifications"""
        if self.conn.notifies:
            while self.conn.notifies:
                notify = self.conn.notifies.pop(0)
                channel = notify.channel
                payload = json.loads(notify.payload)

                if channel in self.listeners:
                    callback = self.listeners[channel]
                    callback(payload)

# ============================================================
# 7. PERFORMANCE MONITOR
# ============================================================

class PerformanceMonitor:
    """Monitor and optimize performance in real-time"""

    def __init__(self, conn):
        self.conn = conn
        self.metrics = []

    def collect_metrics(self) -> Dict:
        """Collect current performance metrics"""
        cursor = self.conn.cursor()

        metrics = {}

        # Query statistics
        cursor.execute("""
            SELECT
                COUNT(*) as active_queries,
                AVG(EXTRACT(EPOCH FROM (now() - query_start))) as avg_query_time
            FROM pg_stat_activity
            WHERE state = 'active'
        """)
        result = cursor.fetchone()
        metrics['active_queries'] = result[0]
        metrics['avg_query_time'] = result[1] or 0

        # Cache statistics
        cursor.execute("""
            SELECT
                sum(heap_blks_hit) / GREATEST(sum(heap_blks_hit) + sum(heap_blks_read), 1) * 100 as cache_hit_ratio
            FROM pg_statio_user_tables
        """)
        metrics['cache_hit_ratio'] = cursor.fetchone()[0] or 0

        # Table statistics
        cursor.execute("""
            SELECT
                tablename,
                n_tup_ins + n_tup_upd + n_tup_del as total_operations
            FROM pg_stat_user_tables
            ORDER BY total_operations DESC
            LIMIT 5
        """)
        metrics['hot_tables'] = cursor.fetchall()

        cursor.close()

        self.metrics.append({
            'timestamp': datetime.now(),
            'metrics': metrics
        })

        return metrics

    def auto_optimize(self):
        """Automatically optimize based on metrics"""
        metrics = self.collect_metrics()

        cursor = self.conn.cursor()

        # Auto-vacuum if needed
        if metrics['cache_hit_ratio'] < 80:
            logging.info("Cache hit ratio low, running VACUUM ANALYZE")
            cursor.execute("VACUUM ANALYZE")

        # Update statistics for hot tables
        for table, ops in metrics['hot_tables']:
            if ops > 10000:
                logging.info(f"Updating statistics for hot table: {table}")
                cursor.execute(f"ANALYZE {table}")

        self.conn.commit()
        cursor.close()

# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

class PipelineOrchestrator:
    """Orchestrate all optimization components"""

    def __init__(self, db_config: Dict):
        self.conn = psycopg2.connect(**db_config)
        self.partition_mgr = PartitionManager(self.conn)
        self.view_mgr = MaterializedViewManager(self.conn)
        self.cache = IntelligentCache()
        self.verifier = DataVerificationPipeline(self.conn)
        self.cdc = CDCPipeline(self.conn)
        self.monitor = PerformanceMonitor(self.conn)

    def initialize_optimizations(self):
        """Initialize all optimizations"""
        logging.info("Initializing database optimizations...")

        # 1. Create partitions
        # counties = self.partition_mgr.create_county_partitions()
        # logging.info(f"Created partitions for {len(counties)} counties")

        # 2. Create materialized views
        self.view_mgr.create_analytics_views()
        logging.info("Created materialized views")

        # 3. Preload cache
        self.cache.preload_common_queries(self.conn)
        logging.info("Preloaded cache")

        # 4. Setup CDC
        self.cdc.setup_triggers('florida_parcels')
        logging.info("Setup CDC pipeline")

        # 5. Initial performance check
        metrics = self.monitor.collect_metrics()
        logging.info(f"Initial metrics: {metrics}")

    def process_data_batch(self, table: str, records: List[Dict]) -> Dict:
        """Process a batch of data through the pipeline"""
        results = {
            'total': len(records),
            'valid': 0,
            'invalid': 0,
            'cached': 0,
            'processing_time': 0
        }

        start_time = datetime.now()

        # 1. Validate data
        valid, invalid = self.verifier.validate_batch(table, records)
        results['valid'] = len(valid)
        results['invalid'] = len(invalid)

        # 2. Quarantine invalid records
        if invalid:
            self.verifier.quarantine_invalid(invalid)

        # 3. Process valid records
        # (Insert, update, etc.)

        # 4. Invalidate related cache
        self.cache.invalidate_pattern(f"*{table}*")

        # 5. Refresh materialized views
        self.view_mgr.refresh_views(concurrent=True)

        results['processing_time'] = (datetime.now() - start_time).total_seconds()

        return results

    def get_status_report(self) -> Dict:
        """Get comprehensive status report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_stats': self.cache.get_stats(),
            'verification_stats': self.verifier.stats,
            'performance_metrics': self.monitor.collect_metrics()
        }

if __name__ == "__main__":
    # Configuration
    db_config = {
        'host': 'aws-1-us-east-1.pooler.supabase.com',
        'port': 6543,
        'database': 'postgres',
        'user': 'postgres.pmispwtdngkcmsrsjwbp',
        'password': 'West@Boca613!'
    }

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(db_config)

    # Run optimizations
    orchestrator.initialize_optimizations()

    # Get status
    status = orchestrator.get_status_report()
    print(json.dumps(status, indent=2, default=str))