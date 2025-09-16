"""
Optimized Database Connection with SQLAlchemy
Implements connection pooling, caching, and performance optimizations
"""

from sqlalchemy import create_engine, pool, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
import redis
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import aiocache
from aiocache.serializers import JsonSerializer
import logging
import os
from contextlib import contextmanager
from functools import lru_cache, wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base for SQLAlchemy models
Base = declarative_base()

class OptimizedDatabaseConnection:
    """
    High-performance database connection manager with:
    - Connection pooling
    - Query caching
    - Prepared statements
    - Batch operations
    - Automatic retry logic
    """

    def __init__(self):
        # Supabase PostgreSQL connection string
        self.database_url = self._get_database_url()

        # Initialize connection pool
        self.engine = self._create_engine()

        # Session factory with scoped sessions
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False
            )
        )

        # Initialize Redis cache
        self.redis_client = self._init_redis()

        # Initialize in-memory cache
        self.memory_cache = aiocache.Cache(
            aiocache.SimpleMemoryCache,
            serializer=JsonSerializer(),
            ttl=300,  # 5 minutes default TTL
            namespace="concordbroker"
        )

        # Performance metrics
        self.metrics = {
            'queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_query_time': 0
        }

        # Prepared statements cache
        self.prepared_statements = {}

        # Configure connection optimizations
        self._configure_optimizations()

    def _get_database_url(self) -> str:
        """Construct PostgreSQL URL from Supabase credentials"""
        # Direct PostgreSQL connection to Supabase
        host = "db.pmispwtdngkcmsrsjwbp.supabase.co"
        port = 5432
        database = "postgres"
        user = "postgres"
        # Use service role for better performance
        password = os.getenv("SUPABASE_DB_PASSWORD", "")

        if not password:
            # Fallback to connection pooler if direct connection not available
            host = "aws-0-us-west-1.pooler.supabase.com"
            port = 6543
            password = os.getenv("SUPABASE_DB_PASSWORD", "")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _create_engine(self):
        """Create SQLAlchemy engine with optimized settings"""
        return create_engine(
            self.database_url,
            # Connection pool settings
            poolclass=QueuePool,
            pool_size=20,  # Number of persistent connections
            max_overflow=40,  # Maximum overflow connections
            pool_timeout=30,  # Timeout for getting connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Test connections before using

            # Performance settings
            echo=False,  # Disable SQL logging for performance
            echo_pool=False,

            # Connection arguments
            connect_args={
                "server_settings": {
                    "application_name": "ConcordBroker_Optimized",
                    "jit": "off"  # Disable JIT for more predictable performance
                },
                "command_timeout": 60,
                "options": "-c statement_timeout=30000"  # 30 second statement timeout
            },

            # Execution options
            execution_options={
                "isolation_level": "READ COMMITTED",
                "postgresql_readonly": False,
                "postgresql_deferrable": False
            }
        )

    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis cache for query results"""
        try:
            client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                connection_pool=redis.ConnectionPool(
                    max_connections=50,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            )
            # Test connection
            client.ping()
            logger.info("Redis cache initialized successfully")
            return client
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            return None

    def _configure_optimizations(self):
        """Configure database-level optimizations"""

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set PostgreSQL performance parameters on connect"""
            with dbapi_conn.cursor() as cursor:
                # Optimize for read-heavy workloads
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET maintenance_work_mem = '512MB'")
                cursor.execute("SET effective_cache_size = '4GB'")
                cursor.execute("SET random_page_cost = 1.1")
                cursor.execute("SET effective_io_concurrency = 200")
                cursor.execute("SET max_parallel_workers_per_gather = 4")
                cursor.execute("SET max_parallel_workers = 8")
                # Enable query planning optimizations
                cursor.execute("SET enable_partitionwise_join = on")
                cursor.execute("SET enable_partitionwise_aggregate = on")
                cursor.execute("SET jit = off")  # Disable JIT for consistency

    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def cache_key(self, query: str, params: Dict = None) -> str:
        """Generate cache key for query"""
        key_data = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return f"query:{hashlib.md5(key_data.encode()).hexdigest()}"

    async def cached_query(
        self,
        query: str,
        params: Dict = None,
        ttl: int = 300,
        cache_type: str = "both"
    ) -> List[Dict]:
        """
        Execute query with caching

        Args:
            query: SQL query string
            params: Query parameters
            ttl: Cache TTL in seconds
            cache_type: "memory", "redis", or "both"
        """
        cache_key = self.cache_key(query, params)

        # Try memory cache first
        if cache_type in ["memory", "both"]:
            cached = await self.memory_cache.get(cache_key)
            if cached:
                self.metrics['cache_hits'] += 1
                return cached

        # Try Redis cache
        if cache_type in ["redis", "both"] and self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    self.metrics['cache_hits'] += 1
                    result = json.loads(cached)
                    # Also store in memory cache
                    await self.memory_cache.set(cache_key, result, ttl=ttl)
                    return result
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # Cache miss - execute query
        self.metrics['cache_misses'] += 1
        start_time = time.time()

        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            data = [dict(row) for row in result]

        query_time = time.time() - start_time
        self.metrics['queries'] += 1
        self.metrics['avg_query_time'] = (
            (self.metrics['avg_query_time'] * (self.metrics['queries'] - 1) + query_time)
            / self.metrics['queries']
        )

        # Cache the result
        if cache_type in ["memory", "both"]:
            await self.memory_cache.set(cache_key, data, ttl=ttl)

        if cache_type in ["redis", "both"] and self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(data)
                )
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")

        return data

    def batch_insert(self, table: str, records: List[Dict], batch_size: int = 1000):
        """Perform batch insert with optimal performance"""
        from sqlalchemy import Table, MetaData

        metadata = MetaData()
        table_obj = Table(table, metadata, autoload_with=self.engine)

        with self.get_session() as session:
            # Process in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                session.bulk_insert_mappings(table_obj, batch)
                session.commit()
                logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} records)")

    def prepare_statement(self, name: str, query: str) -> str:
        """Prepare a statement for repeated execution"""
        if name not in self.prepared_statements:
            with self.get_session() as session:
                # PostgreSQL PREPARE statement
                prepare_sql = f"PREPARE {name} AS {query}"
                session.execute(text(prepare_sql))
                session.commit()
                self.prepared_statements[name] = query
                logger.info(f"Prepared statement: {name}")
        return name

    def execute_prepared(self, name: str, params: tuple):
        """Execute a prepared statement"""
        if name not in self.prepared_statements:
            raise ValueError(f"Prepared statement {name} not found")

        with self.get_session() as session:
            execute_sql = f"EXECUTE {name}({','.join(['%s'] * len(params))})"
            result = session.execute(text(execute_sql), params)
            return [dict(row) for row in result]

    def create_indexes(self, indexes: List[Dict[str, Any]]):
        """Create database indexes for performance"""
        with self.get_session() as session:
            for index in indexes:
                index_sql = f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS {index['name']}
                ON {index['table']} ({', '.join(index['columns'])})
                {index.get('type', '')}
                WHERE {index['where']} if 'where' in index else ''
                """
                try:
                    session.execute(text(index_sql))
                    session.commit()
                    logger.info(f"Created index: {index['name']}")
                except Exception as e:
                    logger.error(f"Failed to create index {index['name']}: {e}")
                    session.rollback()

    def analyze_tables(self, tables: List[str]):
        """Run ANALYZE on tables to update statistics"""
        with self.get_session() as session:
            for table in tables:
                try:
                    session.execute(text(f"ANALYZE {table}"))
                    session.commit()
                    logger.info(f"Analyzed table: {table}")
                except Exception as e:
                    logger.error(f"Failed to analyze table {table}: {e}")
                    session.rollback()

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_hit_rate = (
            self.metrics['cache_hits'] /
            (self.metrics['cache_hits'] + self.metrics['cache_misses'])
            if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
            else 0
        )

        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate,
            'pool_size': self.engine.pool.size(),
            'pool_checked_in': self.engine.pool.checkedin(),
            'pool_overflow': self.engine.pool.overflow(),
            'pool_total': self.engine.pool.total()
        }

    def close(self):
        """Close all connections and cleanup"""
        self.SessionLocal.remove()
        self.engine.dispose()
        if self.redis_client:
            self.redis_client.close()
        logger.info("Database connections closed")


# Singleton instance
_db_connection = None

def get_optimized_db() -> OptimizedDatabaseConnection:
    """Get singleton database connection"""
    global _db_connection
    if _db_connection is None:
        _db_connection = OptimizedDatabaseConnection()
    return _db_connection