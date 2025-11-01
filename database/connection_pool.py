#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Connection Pool
Reuses connections for better performance and resource efficiency
"""

import os
import sys
import psycopg2
from psycopg2 import pool
from typing import Optional
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.mcp')

class ConnectionPool:
    """
    Singleton connection pool for database connections
    Reuses connections instead of creating new ones for every query
    """

    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            # Configuration
            min_conn = int(os.getenv('DB_POOL_MIN', '5'))
            max_conn = int(os.getenv('DB_POOL_MAX', '100'))

            print(f"  🔌 Initializing connection pool (min: {min_conn}, max: {max_conn})")

            # Create threaded connection pool
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                host=os.getenv('SUPABASE_HOST'),
                database=os.getenv('SUPABASE_DB', 'postgres'),
                user=os.getenv('SUPABASE_USER', 'postgres'),
                password=os.getenv('SUPABASE_PASSWORD'),
                port=int(os.getenv('SUPABASE_PORT', '5432')),
                # Performance settings
                connect_timeout=10,
                options='-c statement_timeout=30000'  # 30 second query timeout
            )

            print(f"  ✅ Connection pool initialized")

        except Exception as e:
            print(f"  ❌ Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self._initialize_pool()

        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"  ❌ Failed to get connection from pool: {e}")
            raise

    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool and conn:
            self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit=False):
        """
        Context manager for getting a cursor
        Automatically handles connection checkout/return and commit/rollback

        Usage:
            with pool.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO ...")
        """
        conn = None
        cursor = None

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            yield cursor

            if commit:
                conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)

    def close_all(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            print("  🔒 Connection pool closed")


# Global singleton instance
pool = ConnectionPool()


# Example usage for agents
class PooledAgentBase:
    """
    Base class for agents using connection pooling
    Inherit from this instead of creating connections directly
    """

    def __init__(self):
        self.pool = pool

    def execute_query(self, sql, params=None, commit=False):
        """
        Execute a query using the connection pool

        Args:
            sql: SQL query string
            params: Query parameters (tuple)
            commit: Whether to commit (for INSERT/UPDATE/DELETE)

        Returns:
            Query results (for SELECT) or None
        """
        with self.pool.get_cursor(commit=commit) as cursor:
            cursor.execute(sql, params)

            if sql.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return None

    def execute_many(self, sql, params_list, commit=True):
        """
        Execute many queries in a batch
        More efficient for bulk operations

        Args:
            sql: SQL query string
            params_list: List of parameter tuples
            commit: Whether to commit

        Returns:
            Number of rows affected
        """
        with self.pool.get_cursor(commit=commit) as cursor:
            cursor.executemany(sql, params_list)
            return cursor.rowcount


# Test function
def test_connection_pool():
    """Test the connection pool"""
    print("\n" + "="*70)
    print("  🧪 TESTING CONNECTION POOL")
    print("="*70)
    print()

    try:
        # Test basic query
        print("  [1/4] Testing basic query...")
        with pool.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM florida_parcels;")
            result = cursor.fetchone()
            print(f"  ✅ Query successful: {result[0]:,} properties")

        # Test multiple connections
        print("\n  [2/4] Testing multiple concurrent connections...")
        connections = []
        for i in range(10):
            conn = pool.get_connection()
            connections.append(conn)
        print(f"  ✅ Got {len(connections)} connections")

        # Return connections
        for conn in connections:
            pool.return_connection(conn)
        print(f"  ✅ Returned all connections")

        # Test commit
        print("\n  [3/4] Testing commit...")
        with pool.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO agent_metrics (agent_id, metric_type, metric_name, metric_value)
                VALUES ('test', 'test', 'connection_pool_test', 1)
                ON CONFLICT DO NOTHING;
            """)
        print("  ✅ Commit successful")

        # Test using PooledAgentBase
        print("\n  [4/4] Testing PooledAgentBase...")
        agent = PooledAgentBase()
        result = agent.execute_query("SELECT COUNT(*) FROM agent_registry;")
        print(f"  ✅ Agent query successful: {result[0][0]} agents")

        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED")
        print("="*70)
        print()

    except Exception as e:
        print(f"\n  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_connection_pool()
