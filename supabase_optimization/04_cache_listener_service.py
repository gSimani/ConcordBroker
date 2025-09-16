"""
=====================================================
CACHE LISTENER SERVICE
Connects PostgreSQL notifications to Redis cache invalidation
=====================================================

Chain of Thought:
1. Listen to PostgreSQL NOTIFY channels
2. Parse invalidation messages
3. Invalidate corresponding Redis keys
4. Handle reconnection and error recovery
5. Provide metrics and monitoring
"""

import os
import json
import asyncio
import psycopg2
import psycopg2.extensions
import select
import redis
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import signal
import sys
from threading import Thread, Event
from queue import Queue, Empty
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ListenerConfig:
    """Configuration for cache listener service"""
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    redis_host: str
    redis_port: int
    redis_password: str
    channels: list
    reconnect_interval: int = 5
    heartbeat_interval: int = 30

class CacheListenerService:
    """Service that listens to PostgreSQL notifications and invalidates Redis cache"""

    def __init__(self):
        self.config = ListenerConfig(
            db_host=os.getenv('POSTGRES_HOST'),
            db_name=os.getenv('POSTGRES_DATABASE'),
            db_user=os.getenv('POSTGRES_USER'),
            db_password=os.getenv('POSTGRES_PASSWORD'),
            redis_host=os.getenv('REDIS_CLOUD_HOST'),
            redis_port=int(os.getenv('REDIS_CLOUD_PORT', 6379)),
            redis_password=os.getenv('REDIS_CLOUD_PASSWORD'),
            channels=[
                'cache_invalidation',
                'cache_invalidation_stats',
                'cache_invalidation_search',
                'cache_invalidation_pattern',
                'cache_invalidation_all',
                'cache_warm',
                'cache_warm_stats'
            ]
        )

        self.db_conn = None
        self.redis_client = None
        self.running = False
        self.stop_event = Event()
        self.stats = {
            'notifications_received': 0,
            'invalidations_processed': 0,
            'errors': 0,
            'reconnections': 0,
            'cache_warm_requests': 0
        }
        self.handlers = self._setup_handlers()

    def _setup_handlers(self) -> Dict[str, Callable]:
        """Set up notification handlers for each channel"""
        return {
            'cache_invalidation': self._handle_property_invalidation,
            'cache_invalidation_stats': self._handle_stats_invalidation,
            'cache_invalidation_search': self._handle_search_invalidation,
            'cache_invalidation_pattern': self._handle_pattern_invalidation,
            'cache_invalidation_all': self._handle_flush_all,
            'cache_warm': self._handle_cache_warm,
            'cache_warm_stats': self._handle_stats_warm
        }

    def connect_database(self):
        """Connect to PostgreSQL database"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.db_conn = psycopg2.connect(
                    host=self.config.db_host,
                    database=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password,
                    async_=0  # Synchronous connection for notifications
                )
                self.db_conn.set_isolation_level(
                    psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
                )

                # Set up listeners for all channels
                cursor = self.db_conn.cursor()
                for channel in self.config.channels:
                    cursor.execute(f"LISTEN {channel};")
                    logger.info(f"Listening on channel: {channel}")

                logger.info("Connected to PostgreSQL database")
                return True

            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.config.reconnect_interval)

        return False

    def connect_redis(self):
        """Connect to Redis Cloud"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    password=self.config.redis_password,
                    decode_responses=False,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPINTVL
                        2: 3,  # TCP_KEEPCNT
                        3: 5,  # TCP_KEEPIDLE
                    }
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis Cloud")
                return True

            except Exception as e:
                logger.error(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.config.reconnect_interval)

        return False

    def _handle_property_invalidation(self, payload: str):
        """Handle property cache invalidation"""
        try:
            # Payload format: property:COUNTY:PARCEL_ID
            self.redis_client.delete(payload)
            logger.debug(f"Invalidated property cache: {payload}")
            self.stats['invalidations_processed'] += 1

        except Exception as e:
            logger.error(f"Error invalidating property cache: {e}")
            self.stats['errors'] += 1

    def _handle_stats_invalidation(self, payload: str):
        """Handle county statistics cache invalidation"""
        try:
            # Payload can be specific county or pattern
            if '*' in payload:
                # Invalidate all county stats
                self._invalidate_pattern(payload)
            else:
                # Invalidate specific county
                self.redis_client.delete(payload)

            logger.debug(f"Invalidated stats cache: {payload}")
            self.stats['invalidations_processed'] += 1

        except Exception as e:
            logger.error(f"Error invalidating stats cache: {e}")
            self.stats['errors'] += 1

    def _handle_search_invalidation(self, payload: str):
        """Handle search results cache invalidation"""
        try:
            # Search invalidations are always patterns
            self._invalidate_pattern(payload)
            logger.debug(f"Invalidated search cache: {payload}")
            self.stats['invalidations_processed'] += 1

        except Exception as e:
            logger.error(f"Error invalidating search cache: {e}")
            self.stats['errors'] += 1

    def _handle_pattern_invalidation(self, payload: str):
        """Handle pattern-based cache invalidation"""
        try:
            self._invalidate_pattern(payload)
            logger.info(f"Pattern invalidation: {payload}")
            self.stats['invalidations_processed'] += 1

        except Exception as e:
            logger.error(f"Error in pattern invalidation: {e}")
            self.stats['errors'] += 1

    def _handle_flush_all(self, payload: str):
        """Handle flush all caches request"""
        try:
            if payload == 'FLUSH_ALL':
                self.redis_client.flushdb()
                logger.warning("Flushed all cache entries")
                self.stats['invalidations_processed'] += 1

        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            self.stats['errors'] += 1

    def _handle_cache_warm(self, payload: str):
        """Handle cache warming request"""
        try:
            # Queue cache warming request
            # In production, this would trigger actual data fetching
            logger.info(f"Cache warm request: {payload}")
            self.stats['cache_warm_requests'] += 1

            # TODO: Implement actual cache warming logic
            # This would fetch data from database and populate cache

        except Exception as e:
            logger.error(f"Error in cache warming: {e}")
            self.stats['errors'] += 1

    def _handle_stats_warm(self, payload: str):
        """Handle statistics cache warming"""
        try:
            logger.info(f"Stats warm request: {payload}")
            self.stats['cache_warm_requests'] += 1

            # TODO: Implement actual stats warming logic

        except Exception as e:
            logger.error(f"Error in stats warming: {e}")
            self.stats['errors'] += 1

    def _invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        cursor = 0
        deleted = 0

        while True:
            cursor, keys = self.redis_client.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                self.redis_client.delete(*keys)
                deleted += len(keys)

            if cursor == 0:
                break

        logger.debug(f"Deleted {deleted} keys matching pattern: {pattern}")

    def listen(self):
        """Main listening loop"""
        self.running = True
        last_heartbeat = time.time()

        while self.running and not self.stop_event.is_set():
            try:
                # Check for notifications with timeout
                if select.select([self.db_conn], [], [], 1.0) == ([], [], []):
                    # Timeout - send heartbeat if needed
                    if time.time() - last_heartbeat > self.config.heartbeat_interval:
                        self._send_heartbeat()
                        last_heartbeat = time.time()
                    continue

                # Process notifications
                self.db_conn.poll()
                while self.db_conn.notifies:
                    notify = self.db_conn.notifies.pop(0)
                    self._process_notification(notify)

            except psycopg2.OperationalError:
                logger.error("Database connection lost, attempting reconnection...")
                self._reconnect()

            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break

            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                self.stats['errors'] += 1
                time.sleep(1)

    def _process_notification(self, notify):
        """Process a single notification"""
        try:
            channel = notify.channel
            payload = notify.payload

            self.stats['notifications_received'] += 1
            logger.debug(f"Notification on {channel}: {payload}")

            # Call appropriate handler
            handler = self.handlers.get(channel)
            if handler:
                handler(payload)
            else:
                logger.warning(f"No handler for channel: {channel}")

        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            self.stats['errors'] += 1

    def _send_heartbeat(self):
        """Send heartbeat to verify connections"""
        try:
            # Check database connection
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            # Check Redis connection
            self.redis_client.ping()

            logger.debug("Heartbeat successful")

        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            self._reconnect()

    def _reconnect(self):
        """Reconnect to database and Redis"""
        self.stats['reconnections'] += 1
        logger.info("Attempting to reconnect...")

        # Close existing connections
        if self.db_conn:
            try:
                self.db_conn.close()
            except:
                pass

        # Reconnect
        try:
            self.connect_database()
            self.connect_redis()
            logger.info("Reconnection successful")

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            time.sleep(self.config.reconnect_interval)

    def start(self):
        """Start the listener service"""
        logger.info("Starting Cache Listener Service...")

        # Connect to services
        self.connect_database()
        self.connect_redis()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start listening
        logger.info("Cache Listener Service started")
        self.listen()

    def stop(self):
        """Stop the listener service"""
        logger.info("Stopping Cache Listener Service...")
        self.running = False
        self.stop_event.set()

        # Close connections
        if self.db_conn:
            self.db_conn.close()

        if self.redis_client:
            self.redis_client.close()

        # Print final statistics
        self.print_stats()
        logger.info("Cache Listener Service stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

    def print_stats(self):
        """Print service statistics"""
        print("\n" + "="*60)
        print("CACHE LISTENER SERVICE STATISTICS")
        print("="*60)
        for key, value in self.stats.items():
            print(f"{key:30}: {value}")
        print("="*60)

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return self.stats.copy()

# =====================================================
# ASYNC VERSION FOR HIGH THROUGHPUT
# =====================================================

class AsyncCacheListener:
    """Asynchronous version for handling high notification volumes"""

    def __init__(self):
        self.config = ListenerConfig(
            db_host=os.getenv('POSTGRES_HOST'),
            db_name=os.getenv('POSTGRES_DATABASE'),
            db_user=os.getenv('POSTGRES_USER'),
            db_password=os.getenv('POSTGRES_PASSWORD'),
            redis_host=os.getenv('REDIS_CLOUD_HOST'),
            redis_port=int(os.getenv('REDIS_CLOUD_PORT', 6379)),
            redis_password=os.getenv('REDIS_CLOUD_PASSWORD'),
            channels=['cache_invalidation', 'cache_invalidation_stats',
                     'cache_invalidation_search']
        )

    async def run(self):
        """Run async listener"""
        import asyncpg
        import aioredis

        # Connect to PostgreSQL
        self.pg_conn = await asyncpg.connect(
            host=self.config.db_host,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password
        )

        # Connect to Redis
        self.redis = await aioredis.create_redis_pool(
            f'redis://:{self.config.redis_password}@{self.config.redis_host}:{self.config.redis_port}'
        )

        # Add listeners
        for channel in self.config.channels:
            await self.pg_conn.add_listener(channel, self._handle_notification)

        logger.info("Async cache listener started")

        # Keep running
        try:
            await asyncio.Event().wait()
        finally:
            await self.pg_conn.close()
            self.redis.close()
            await self.redis.wait_closed()

    async def _handle_notification(self, connection, pid, channel, payload):
        """Handle notification asynchronously"""
        logger.debug(f"Async notification: {channel} - {payload}")

        # Process based on channel
        if channel == 'cache_invalidation':
            await self.redis.delete(payload)
        elif channel == 'cache_invalidation_pattern':
            await self._async_pattern_delete(payload)

    async def _async_pattern_delete(self, pattern: str):
        """Delete keys matching pattern asynchronously"""
        cursor = b'0'
        while cursor:
            cursor, keys = await self.redis.scan(cursor, match=pattern)
            if keys:
                await self.redis.delete(*keys)

# =====================================================
# SERVICE RUNNER
# =====================================================

def main():
    """Main entry point for cache listener service"""
    service = CacheListenerService()

    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        service.stop()

if __name__ == "__main__":
    main()