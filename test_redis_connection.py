"""
Test Redis Cloud connection and integration with Supabase
Provides detailed diagnostics for connection issues
"""

import os
import sys
import json
import time
import redis
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# Load environment variables
load_dotenv(Path('.env.mcp'))

def test_redis_connection():
    """Test Redis Cloud connection with detailed diagnostics"""

    print("=" * 60)
    print("  Redis Cloud Connection Test")
    print("=" * 60)
    print()

    # Get Redis configuration
    redis_host = os.getenv('REDIS_CLOUD_HOST')
    redis_port = os.getenv('REDIS_CLOUD_PORT', 19041)
    redis_password = os.getenv('REDIS_CLOUD_PASSWORD')

    print(" Redis Configuration:")
    print(f"  Host: {redis_host}")
    print(f"  Port: {redis_port}")
    print(f"  Password: {' Set' if redis_password else ' Not set'}")
    print()

    # Test different connection methods
    print(" Testing connection methods...")
    print()

    # Method 1: Direct connection
    print("1 Testing direct connection...")
    try:
        r = redis.Redis(
            host=redis_host,
            port=int(redis_port),
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5
        )

        # Test ping
        if r.ping():
            print("    Direct connection successful!")

            # Test basic operations
            print("\n   Testing basic operations:")

            # Set a value
            r.set('test:key', 'Hello from Redis!', ex=60)
            print("    SET operation successful")

            # Get the value
            value = r.get('test:key')
            print(f"    GET operation successful: {value}")

            # Get server info
            info = r.info('server')
            print(f"\n    Redis Server Info:")
            print(f"      Version: {info.get('redis_version', 'Unknown')}")
            print(f"      Mode: {info.get('redis_mode', 'Unknown')}")

            return r

    except redis.ConnectionError as e:
        print(f"    Connection failed: {e}")
    except redis.TimeoutError:
        print("    Connection timeout")
    except Exception as e:
        print(f"    Unexpected error: {e}")

    print()

    # Method 2: Connection pool
    print("2 Testing connection pool...")
    try:
        pool = redis.ConnectionPool(
            host=redis_host,
            port=int(redis_port),
            password=redis_password,
            decode_responses=True,
            max_connections=10,
            socket_connect_timeout=5
        )

        r = redis.Redis(connection_pool=pool)

        if r.ping():
            print("    Connection pool successful!")
            return r

    except Exception as e:
        print(f"    Connection pool failed: {e}")

    print()

    # Method 3: URL format
    print("3 Testing URL connection...")
    try:
        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        r = redis.from_url(redis_url, decode_responses=True)

        if r.ping():
            print("    URL connection successful!")
            return r

    except Exception as e:
        print(f"    URL connection failed: {e}")

    return None


def test_supabase_connection():
    """Test Supabase connection"""

    print("\n" + "=" * 60)
    print("  Supabase Connection Test")
    print("=" * 60)
    print()

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    print(" Supabase Configuration:")
    print(f"  URL: {supabase_url}")
    print(f"  Key: {' Set' if supabase_key else ' Not set'}")
    print()

    if not supabase_url or not supabase_key:
        print(" Supabase credentials not found")
        return None

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Test query
        print(" Testing database query...")
        response = supabase.table('florida_parcels').select("*").limit(1).execute()

        if response.data:
            print(" Supabase connection successful!")
            print(f"   Found {len(response.data)} record(s)")
            return supabase
        else:
            print(" Connection successful but no data found")
            return supabase

    except Exception as e:
        print(f" Supabase connection failed: {e}")
        return None


def test_caching_strategy(redis_client, supabase_client):
    """Test caching strategy with Redis and Supabase"""

    if not redis_client or not supabase_client:
        print("\n Skipping caching strategy test (missing connections)")
        return

    print("\n" + "=" * 60)
    print("  Caching Strategy Test")
    print("=" * 60)
    print()

    # Test cached query
    print(" Testing cached database query...")

    cache_key = "properties:broward:limit5"

    # Check cache first
    cached_data = redis_client.get(cache_key)

    if cached_data:
        print(" Cache HIT - Data retrieved from Redis")
        properties = json.loads(cached_data)
    else:
        print(" Cache MISS - Fetching from database...")

        # Fetch from Supabase
        response = supabase_client.table('florida_parcels') \
            .select("parcel_id, phy_addr1, phy_city, county, just_value") \
            .eq('county', 'BROWARD') \
            .limit(5) \
            .execute()

        properties = response.data

        if properties:
            # Store in cache for 5 minutes
            redis_client.setex(
                cache_key,
                300,
                json.dumps(properties)
            )
            print(" Data cached for future requests")

    print(f"\n Found {len(properties)} properties:")
    for prop in properties[:3]:  # Show first 3
        print(f"  - {prop.get('parcel_id', 'N/A')}: {prop.get('phy_addr1', 'N/A')}")

    # Test cache stats
    print("\n Cache Performance:")

    # Get memory usage
    memory_info = redis_client.info('memory')
    used_memory = memory_info.get('used_memory_human', 'Unknown')
    print(f"  Memory Used: {used_memory}")

    # Get key count
    db_size = redis_client.dbsize()
    print(f"  Total Keys: {db_size}")

    # Get TTL of our key
    ttl = redis_client.ttl(cache_key)
    print(f"  Cache TTL: {ttl} seconds")


def main():
    """Main test function"""

    print("\n[Starting Redis Cloud & Supabase Integration Test]\n")

    # Test Redis
    redis_client = test_redis_connection()

    # Test Supabase
    supabase_client = test_supabase_connection()

    # Test caching strategy
    test_caching_strategy(redis_client, supabase_client)

    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)

    if redis_client:
        try:
            if redis_client.ping():
                print(" Redis Cloud: Connected")
        except:
            print(" Redis Cloud: Not Connected")
    else:
        print(" Redis Cloud: Not Connected")

    if supabase_client:
        print(" Supabase: Connected")
    else:
        print(" Supabase: Not Connected")

    print("\n" + "=" * 60 + "\n")

    if redis_client and supabase_client:
        print("[SUCCESS] Integration ready for production!")
    elif not redis_client:
        print(" Redis connection failed - will use in-memory cache as fallback")
        print("\nTroubleshooting tips:")
        print("1. Check if Redis Cloud instance is active")
        print("2. Verify credentials in .env.mcp")
        print("3. Check network connectivity")
        print("4. Ensure Redis Cloud allows connections from your IP")

    if not supabase_client:
        print("\n Supabase connection failed")
        print("\nTroubleshooting tips:")
        print("1. Verify SUPABASE_URL and SUPABASE_ANON_KEY in .env.mcp")
        print("2. Check if Supabase project is active")
        print("3. Verify network connectivity")


if __name__ == "__main__":
    main()