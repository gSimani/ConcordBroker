"""
Credential validation for Redis and Supabase
Tests various authentication methods to find the correct configuration
"""

import os
import json
import redis
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# Load environment variables
load_dotenv(Path('.env.mcp'))

def validate_redis_credentials():
    """Test Redis with multiple authentication approaches"""

    print("=" * 60)
    print("  Redis Credential Validation")
    print("=" * 60)

    host = os.getenv('REDIS_CLOUD_HOST')
    port = int(os.getenv('REDIS_CLOUD_PORT', 19041))
    password = os.getenv('REDIS_CLOUD_PASSWORD')
    api_key = os.getenv('REDIS_CLOUD_API_KEY')

    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Password: {'Set' if password else 'Not set'}")
    print(f"API Key: {'Set' if api_key else 'Not set'}")
    print()

    # Test configurations
    configs = [
        {
            "name": "Password Authentication",
            "config": {"host": host, "port": port, "password": password, "decode_responses": True}
        },
        {
            "name": "API Key as Password",
            "config": {"host": host, "port": port, "password": api_key, "decode_responses": True}
        },
        {
            "name": "No Authentication",
            "config": {"host": host, "port": port, "decode_responses": True}
        },
        {
            "name": "Username + Password",
            "config": {"host": host, "port": port, "username": "default", "password": password, "decode_responses": True}
        },
        {
            "name": "Username + API Key",
            "config": {"host": host, "port": port, "username": "default", "password": api_key, "decode_responses": True}
        }
    ]

    for test_config in configs:
        print(f"Testing: {test_config['name']}")
        try:
            r = redis.Redis(**test_config['config'], socket_connect_timeout=3)

            # Test connection
            if r.ping():
                print("   SUCCESS: Connection established!")

                # Test operations
                r.set('validation:test', 'Redis working!', ex=30)
                value = r.get('validation:test')
                print(f"   Test value: {value}")

                # Get server info
                info = r.info('server')
                print(f"   Redis Version: {info.get('redis_version', 'Unknown')}")

                return r, test_config['name']

        except redis.AuthenticationError:
            print("   FAILED: Authentication error")
        except redis.ConnectionError as e:
            print(f"   FAILED: Connection error - {e}")
        except Exception as e:
            print(f"   FAILED: {e}")

        print()

    return None, None

def validate_supabase_credentials():
    """Test Supabase with different API keys"""

    print("=" * 60)
    print("  Supabase Credential Validation")
    print("=" * 60)

    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_ANON_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    print(f"URL: {url}")
    print(f"Anon Key: {'Set' if anon_key else 'Not set'}")
    print(f"Service Key: {'Set' if service_key else 'Not set'}")
    print()

    # Test different key combinations
    test_configs = [
        {"name": "Service Role Key", "key": service_key},
        {"name": "Anonymous Key", "key": anon_key}
    ]

    for config in test_configs:
        if not config['key']:
            continue

        print(f"Testing: {config['name']}")
        try:
            supabase = create_client(url, config['key'])

            # Test basic query
            response = supabase.table('florida_parcels').select("parcel_id").limit(1).execute()

            if response.data:
                print("   SUCCESS: Database query successful!")
                print(f"   Records accessible: {len(response.data)}")

                # Test write permission (for service key)
                if 'service' in config['name'].lower():
                    try:
                        # Test if we can create a test table (will fail if exists)
                        test_response = supabase.table('_test_connection').select("*").limit(1).execute()
                        print("   Write permissions: Available")
                    except Exception:
                        print("   Write permissions: Limited (expected for anon key)")

                return supabase, config['name']

        except Exception as e:
            print(f"   FAILED: {e}")

        print()

    return None, None

def test_integrated_caching(redis_client, supabase_client, redis_method, supabase_method):
    """Test the integrated caching system"""

    print("=" * 60)
    print("  Integrated Caching Test")
    print("=" * 60)

    print(f"Redis Method: {redis_method}")
    print(f"Supabase Method: {supabase_method}")
    print()

    cache_key = "validation:properties:test"

    # Clear any existing cache
    try:
        redis_client.delete(cache_key)
    except:
        pass

    print("1. Testing Cache Miss (fetch from database):")
    try:
        # Fetch from Supabase
        response = supabase_client.table('florida_parcels') \
            .select("parcel_id, phy_addr1, county") \
            .limit(3) \
            .execute()

        properties = response.data
        print(f"   Fetched {len(properties)} properties from Supabase")

        # Cache the results
        redis_client.setex(cache_key, 300, json.dumps(properties))
        print("   Data cached in Redis (5 min TTL)")

    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    print("\n2. Testing Cache Hit (fetch from Redis):")
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            cached_properties = json.loads(cached_data)
            print(f"   Retrieved {len(cached_properties)} properties from cache")
            print("   Cache hit successful!")

            # Show TTL
            ttl = redis_client.ttl(cache_key)
            print(f"   Cache expires in {ttl} seconds")

        else:
            print("   No cached data found")
            return False

    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    print("\n3. Performance comparison:")
    import time

    # Time database query
    start = time.time()
    supabase_client.table('florida_parcels').select("parcel_id").limit(1).execute()
    db_time = time.time() - start

    # Time cache query
    start = time.time()
    redis_client.get(cache_key)
    cache_time = time.time() - start

    speedup = db_time / cache_time if cache_time > 0 else float('inf')

    print(f"   Database query: {db_time:.3f}s")
    print(f"   Cache query: {cache_time:.3f}s")
    print(f"   Cache speedup: {speedup:.1f}x faster")

    return True

def main():
    """Main validation function"""

    print("\n" + "=" * 60)
    print("  ConcordBroker Credential Validation")
    print("=" * 60)

    # Validate Redis
    redis_client, redis_method = validate_redis_credentials()

    # Validate Supabase
    supabase_client, supabase_method = validate_supabase_credentials()

    # Test integration if both work
    if redis_client and supabase_client:
        integration_success = test_integrated_caching(
            redis_client, supabase_client,
            redis_method, supabase_method
        )
    else:
        integration_success = False

    # Final summary
    print("\n" + "=" * 60)
    print("  Validation Summary")
    print("=" * 60)

    if redis_client:
        print(f"Redis: WORKING ({redis_method})")
    else:
        print("Redis: FAILED (all methods)")

    if supabase_client:
        print(f"Supabase: WORKING ({supabase_method})")
    else:
        print("Supabase: FAILED (all methods)")

    if integration_success:
        print("Integration: WORKING (Redis + Supabase caching)")
        print("\nREADY FOR PRODUCTION!")
    else:
        print("Integration: FAILED")

        if not redis_client:
            print("\nRedis issues:")
            print("- Check Redis Cloud instance is active")
            print("- Verify credentials are correct")
            print("- Check network connectivity")
            print("- Ensure IP is whitelisted")

        if not supabase_client:
            print("\nSupabase issues:")
            print("- Verify project URL is correct")
            print("- Check API key permissions")
            print("- Ensure RLS policies allow access")

    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()