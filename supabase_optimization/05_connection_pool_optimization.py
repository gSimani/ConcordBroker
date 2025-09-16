"""
=====================================================
STEP 5: CONNECTION POOL OPTIMIZATION
Expected Performance Gain: 2x for connection overhead
=====================================================

Chain of Thought:
1. Implement advanced connection pooling with psycopg3
2. Add circuit breaker pattern for resilience
3. Implement retry logic with exponential backoff
4. Add connection health monitoring
5. Create pool warmup strategies
6. Monitor pool metrics
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta
import threading
from queue import Queue, Empty, Full
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import asyncpg
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# CONNECTION POOL CONFIGURATION
# =====================================================

@dataclass
class PoolConfig:
    """Connection pool configuration"""
    # Basic settings
    min_connections: int = 2
    max_connections: int = 20

    # Connection settings
    host: str = field(default_factory=lambda: os.getenv('POSTGRES_HOST'))
    database: str = field(default_factory=lambda: os.getenv('POSTGRES_DATABASE'))
    user: str = field(default_factory=lambda: os.getenv('POSTGRES_USER'))
    password: str = field(default_factory=lambda: os.getenv('POSTGRES_PASSWORD'))
    port: int = 5432

    # Timeout settings
    connection_timeout: int = 10  # seconds
    idle_timeout: int = 300  # 5 minutes
    max_lifetime: int = 3600  # 1 hour

    # Pool behavior
    overflow: int = 10  # Extra connections when pool is exhausted
    recycle: int = 3600  # Recycle connections after 1 hour
    pre_ping: bool = True  # Test connections before use

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # Circuit breaker settings
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception_types: tuple = (psycopg2.OperationalError, psycopg2.InterfaceError)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

# =====================================================
# CIRCUIT BREAKER PATTERN
# =====================================================

class CircuitBreaker:
    """Circuit breaker for database connections"""

    def __init__(self, config: PoolConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception_types as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.config.recovery_timeout)

    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:  # Require 3 successes to close
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    logger.info("Circuit breaker CLOSED")

    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN (half-open test failed)")
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPEN (failures: {self.failure_count})")

# =====================================================
# ADVANCED CONNECTION POOL
# =====================================================

class OptimizedConnectionPool:
    """Optimized connection pool with monitoring and resilience"""

    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self.circuit_breaker = CircuitBreaker(self.config)
        self._pool = None
        self._stats = {
            'connections_created': 0,
            'connections_recycled': 0,
            'connections_failed': 0,
            'checkout_time': [],
            'query_time': [],
            'pool_size': 0,
            'active_connections': 0,
            'idle_connections': 0
        }
        self._connection_info = {}  # Track connection metadata
        self._lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                host=self.config.host,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                port=self.config.port,
                connect_timeout=self.config.connection_timeout,
                options='-c statement_timeout=30000',  # 30 second statement timeout
                cursor_factory=RealDictCursor
            )

            # Warm up the pool
            self._warmup_pool()
            logger.info(f"Connection pool initialized with {self.config.min_connections}-{self.config.max_connections} connections")

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _warmup_pool(self):
        """Pre-create minimum connections"""
        for _ in range(self.config.min_connections):
            try:
                conn = self._pool.getconn()
                self._pool.putconn(conn)
                self._stats['connections_created'] += 1
            except Exception as e:
                logger.warning(f"Failed to warm up connection: {e}")

    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """Get a connection from the pool with automatic return"""
        start_time = time.time()
        conn = None

        try:
            # Use circuit breaker
            conn = self.circuit_breaker.call(
                self._get_connection_with_retry,
                timeout
            )

            # Track checkout time
            checkout_time = time.time() - start_time
            self._stats['checkout_time'].append(checkout_time)

            # Test connection if pre_ping enabled
            if self.config.pre_ping:
                self._test_connection(conn)

            # Check if connection needs recycling
            if self._should_recycle(conn):
                conn = self._recycle_connection(conn)

            yield conn

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self._stats['connections_failed'] += 1
            raise

        finally:
            if conn:
                self._pool.putconn(conn)

    def _get_connection_with_retry(self, timeout: Optional[float] = None) -> psycopg2.extensions.connection:
        """Get connection with retry logic"""
        retry_delay = self.config.retry_delay

        for attempt in range(self.config.max_retries):
            try:
                conn = self._pool.getconn()

                # Store connection metadata
                conn_id = id(conn)
                if conn_id not in self._connection_info:
                    self._connection_info[conn_id] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'query_count': 0
                    }
                else:
                    self._connection_info[conn_id]['last_used'] = time.time()

                return conn

            except pool.PoolError as e:
                if attempt == self.config.max_retries - 1:
                    raise

                logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s")
                time.sleep(retry_delay)
                retry_delay *= self.config.retry_backoff

    def _test_connection(self, conn: psycopg2.extensions.connection) -> bool:
        """Test if connection is alive"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False

    def _should_recycle(self, conn: psycopg2.extensions.connection) -> bool:
        """Check if connection should be recycled"""
        conn_id = id(conn)
        if conn_id not in self._connection_info:
            return False

        info = self._connection_info[conn_id]
        age = time.time() - info['created_at']

        return age > self.config.max_lifetime

    def _recycle_connection(self, conn: psycopg2.extensions.connection) -> psycopg2.extensions.connection:
        """Recycle a connection"""
        conn_id = id(conn)

        try:
            # Close old connection
            conn.close()

            # Create new connection
            new_conn = psycopg2.connect(
                host=self.config.host,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                port=self.config.port,
                connect_timeout=self.config.connection_timeout,
                cursor_factory=RealDictCursor
            )

            # Update metadata
            new_conn_id = id(new_conn)
            self._connection_info[new_conn_id] = {
                'created_at': time.time(),
                'last_used': time.time(),
                'query_count': 0
            }

            # Clean up old metadata
            if conn_id in self._connection_info:
                del self._connection_info[conn_id]

            self._stats['connections_recycled'] += 1
            logger.debug(f"Recycled connection {conn_id} -> {new_conn_id}")

            return new_conn

        except Exception as e:
            logger.error(f"Failed to recycle connection: {e}")
            raise

    def execute_query(self, query: str, params: Optional[tuple] = None,
                      fetch: bool = True) -> Union[List[Dict], None]:
        """Execute a query with connection pooling"""
        start_time = time.time()

        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)

                    if fetch:
                        result = cursor.fetchall()
                        result = [dict(row) for row in result]
                    else:
                        conn.commit()
                        result = cursor.rowcount

                    # Track query time
                    query_time = time.time() - start_time
                    self._stats['query_time'].append(query_time)

                    # Update connection query count
                    conn_id = id(conn)
                    if conn_id in self._connection_info:
                        self._connection_info[conn_id]['query_count'] += 1

                    return result

            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution failed: {e}")
                raise

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            stats = self._stats.copy()

            # Calculate averages
            if stats['checkout_time']:
                stats['avg_checkout_time'] = statistics.mean(stats['checkout_time'])
                stats['max_checkout_time'] = max(stats['checkout_time'])

            if stats['query_time']:
                stats['avg_query_time'] = statistics.mean(stats['query_time'])
                stats['p95_query_time'] = statistics.quantiles(stats['query_time'], n=20)[18]  # 95th percentile

            # Get pool status
            stats['pool_size'] = len(self._pool._pool) if self._pool else 0
            stats['circuit_breaker_state'] = self.circuit_breaker.state.value

            return stats

    def close(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Connection pool closed")

# =====================================================
# ASYNC CONNECTION POOL
# =====================================================

class AsyncOptimizedPool:
    """Async version for high-concurrency applications"""

    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self._pool = None
        self._semaphore = None

    async def initialize(self):
        """Initialize async pool"""
        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            port=self.config.port,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            max_inactive_connection_lifetime=self.config.idle_timeout,
            command_timeout=self.config.connection_timeout
        )

        self._semaphore = asyncio.Semaphore(self.config.max_connections)
        logger.info("Async connection pool initialized")

    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from async pool"""
        async with self._semaphore:
            async with self._pool.acquire() as connection:
                yield connection

    async def execute(self, query: str, *params):
        """Execute query with async pool"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *params)

    async def close(self):
        """Close async pool"""
        await self._pool.close()

# =====================================================
# CONNECTION POOL MONITOR
# =====================================================

class PoolMonitor:
    """Monitor connection pool health and performance"""

    def __init__(self, pool: OptimizedConnectionPool):
        self.pool = pool
        self.running = False
        self._monitor_thread = None
        self._metrics_history = []

    def start(self, interval: int = 60):
        """Start monitoring"""
        self.running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Pool monitor started")

    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.running:
            metrics = self._collect_metrics()
            self._metrics_history.append(metrics)

            # Keep only last hour of metrics
            cutoff_time = time.time() - 3600
            self._metrics_history = [
                m for m in self._metrics_history
                if m['timestamp'] > cutoff_time
            ]

            # Check for issues
            self._check_health(metrics)

            time.sleep(interval)

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics"""
        stats = self.pool.get_pool_stats()
        stats['timestamp'] = time.time()
        return stats

    def _check_health(self, metrics: Dict[str, Any]):
        """Check pool health and alert on issues"""
        # Check circuit breaker
        if metrics['circuit_breaker_state'] == 'open':
            logger.error("Circuit breaker is OPEN - database connectivity issues")

        # Check connection failures
        if metrics.get('connections_failed', 0) > 10:
            logger.warning(f"High connection failure rate: {metrics['connections_failed']}")

        # Check checkout time
        if metrics.get('avg_checkout_time', 0) > 1.0:
            logger.warning(f"Slow connection checkout: {metrics['avg_checkout_time']:.2f}s")

        # Check query performance
        if metrics.get('p95_query_time', 0) > 5.0:
            logger.warning(f"Slow queries detected: p95={metrics['p95_query_time']:.2f}s")

    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join()
        logger.info("Pool monitor stopped")

    def get_report(self) -> Dict[str, Any]:
        """Generate monitoring report"""
        if not self._metrics_history:
            return {}

        latest = self._metrics_history[-1]

        # Calculate trends
        if len(self._metrics_history) > 10:
            recent = self._metrics_history[-10:]
            avg_checkout = statistics.mean([
                m.get('avg_checkout_time', 0) for m in recent
            ])
            avg_query = statistics.mean([
                m.get('avg_query_time', 0) for m in recent
            ])
        else:
            avg_checkout = latest.get('avg_checkout_time', 0)
            avg_query = latest.get('avg_query_time', 0)

        return {
            'current_state': latest.get('circuit_breaker_state'),
            'total_connections': latest.get('connections_created', 0),
            'recycled_connections': latest.get('connections_recycled', 0),
            'failed_connections': latest.get('connections_failed', 0),
            'avg_checkout_time': avg_checkout,
            'avg_query_time': avg_query,
            'pool_efficiency': self._calculate_efficiency()
        }

    def _calculate_efficiency(self) -> float:
        """Calculate pool efficiency score (0-100)"""
        if not self._metrics_history:
            return 0

        latest = self._metrics_history[-1]

        # Factors for efficiency
        checkout_score = min(100, 100 * (1.0 / max(0.1, latest.get('avg_checkout_time', 1))))
        failure_rate = latest.get('connections_failed', 0) / max(1, latest.get('connections_created', 1))
        failure_score = 100 * (1 - min(1, failure_rate))
        circuit_score = 100 if latest.get('circuit_breaker_state') == 'closed' else 0

        # Weighted average
        efficiency = (checkout_score * 0.3 + failure_score * 0.4 + circuit_score * 0.3)

        return round(efficiency, 2)

# =====================================================
# USAGE EXAMPLES
# =====================================================

def test_pool_optimization():
    """Test connection pool optimization"""
    print("\n" + "="*60)
    print("TESTING CONNECTION POOL OPTIMIZATION")
    print("="*60)

    # Initialize optimized pool
    config = PoolConfig(
        min_connections=5,
        max_connections=20,
        pre_ping=True
    )
    pool = OptimizedConnectionPool(config)
    monitor = PoolMonitor(pool)
    monitor.start(interval=10)

    try:
        # Test 1: Single connection
        print("\n1. Testing single connection checkout...")
        start = time.time()
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        single_time = time.time() - start
        print(f"   Single connection: {single_time:.4f}s")

        # Test 2: Multiple sequential connections
        print("\n2. Testing sequential connections...")
        start = time.time()
        for _ in range(10):
            with pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
        sequential_time = time.time() - start
        print(f"   10 sequential connections: {sequential_time:.4f}s")
        print(f"   Average per connection: {sequential_time/10:.4f}s")

        # Test 3: Query execution
        print("\n3. Testing query execution...")
        result = pool.execute_query(
            "SELECT COUNT(*) as count FROM florida_parcels WHERE county = %s",
            ('BROWARD',)
        )
        print(f"   Query result: {result}")

        # Test 4: Pool statistics
        print("\n4. Pool Statistics:")
        stats = pool.get_pool_stats()
        for key, value in stats.items():
            if not isinstance(value, list):
                print(f"   {key}: {value}")

        # Test 5: Monitor report
        time.sleep(2)  # Let monitor collect some data
        print("\n5. Monitor Report:")
        report = monitor.get_report()
        for key, value in report.items():
            print(f"   {key}: {value}")

    finally:
        monitor.stop()
        pool.close()

    print("\n" + "="*60)
    print("CONNECTION POOL OPTIMIZATION TEST COMPLETE")
    print("="*60)

# =====================================================
# ASYNC TESTING
# =====================================================

async def test_async_pool():
    """Test async connection pool"""
    print("\n" + "="*60)
    print("TESTING ASYNC CONNECTION POOL")
    print("="*60)

    config = PoolConfig(min_connections=5, max_connections=20)
    pool = AsyncOptimizedPool(config)

    try:
        await pool.initialize()

        # Test concurrent queries
        start = time.time()
        tasks = [
            pool.execute("SELECT COUNT(*) FROM florida_parcels WHERE county = $1", 'BROWARD')
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"10 concurrent queries completed in {elapsed:.4f}s")
        print(f"Average per query: {elapsed/10:.4f}s")

    finally:
        await pool.close()

if __name__ == "__main__":
    # Test synchronous pool
    test_pool_optimization()

    # Test async pool
    # asyncio.run(test_async_pool())