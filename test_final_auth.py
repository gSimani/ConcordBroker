"""
Final authentication test with confirmed password
Testing both pooler and alternative connection methods
"""

import psycopg2
import sys

# Confirmed password
PASSWORD = "West@Boca613!"

print("=" * 70)
print("FINAL AUTHENTICATION TEST")
print("Password confirmed: West@Boca613!")
print("=" * 70)

# Test configurations
tests = [
    {
        "name": "Test 1: Pooler with project ref (port 6543)",
        "host": "aws-0-us-east-1.pooler.supabase.com",
        "port": 6543,
        "user": "postgres.pmispwtdngkcmsrsjwbp",
        "database": "postgres",
        "password": PASSWORD,
        "sslmode": "require"
    },
    {
        "name": "Test 2: Pooler with project ref (port 5432)",
        "host": "aws-0-us-east-1.pooler.supabase.com", 
        "port": 5432,
        "user": "postgres.pmispwtdngkcmsrsjwbp",
        "database": "postgres",
        "password": PASSWORD,
        "sslmode": "require"
    },
    {
        "name": "Test 3: Direct connection (if DNS works)",
        "host": "db.pmispwtdngkcmsrsjwbp.supabase.co",
        "port": 5432,
        "user": "postgres",
        "database": "postgres", 
        "password": PASSWORD,
        "sslmode": "require"
    }
]

successful = False

for test in tests:
    print(f"\n{test['name']}")
    print("-" * 50)
    print(f"Host: {test['host']}")
    print(f"Port: {test['port']}")
    print(f"User: {test['user']}")
    
    try:
        conn = psycopg2.connect(
            host=test['host'],
            port=test['port'],
            database=test['database'],
            user=test['user'],
            password=test['password'],
            sslmode=test['sslmode'],
            connect_timeout=10
        )
        
        print(">>> SUCCESS! Connected to database <<<")
        
        # Quick test
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_user, COUNT(*) FROM public.florida_parcels")
        db, user, count = cur.fetchone()
        print(f"Database: {db}")
        print(f"User: {user}")
        print(f"Records in florida_parcels: {count:,}")
        
        cur.close()
        conn.close()
        
        successful = True
        print("\n" + "=" * 70)
        print("CONNECTION SUCCESSFUL - Ready to proceed with data upload!")
        print(f"Use this configuration for the COPY loader:")
        print(f"  Host: {test['host']}")
        print(f"  Port: {test['port']}")
        print(f"  User: {test['user']}")
        print("=" * 70)
        break
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "Tenant or user not found" in error_msg:
            print("ERROR: Authentication failed - 'Tenant or user not found'")
            print(">>> This means the password or username format is incorrect <<<")
        elif "could not translate host name" in error_msg:
            print("ERROR: DNS resolution failed (IPv6 only host)")
        elif "timeout" in error_msg.lower():
            print("ERROR: Connection timeout")
        else:
            print(f"ERROR: {error_msg[:100]}...")
    except Exception as e:
        print(f"ERROR: {str(e)[:100]}...")

if not successful:
    print("\n" + "=" * 70)
    print("ALL CONNECTION ATTEMPTS FAILED")
    print("=" * 70)
    print("\nISSUES IDENTIFIED:")
    print("1. Pooler connections return: 'Tenant or user not found'")
    print("   - This indicates the password might be incorrect")
    print("   - OR the project might be paused/restricted")
    print("")
    print("2. Direct connection fails with DNS resolution")
    print("   - The host only has IPv6 addressing")
    print("   - Windows has issues with IPv6 connections")
    print("")
    print("RECOMMENDED ACTIONS:")
    print("1. Reset the database password in Supabase Dashboard:")
    print("   Dashboard -> Settings -> Database -> Reset Database Password")
    print("")
    print("2. Or provide an IPv4 address for the direct host")
    print("")
    print("3. Or disable timeouts for REST API uploads:")
    print("   ALTER DATABASE postgres SET statement_timeout = 0;")
    print("=" * 70)