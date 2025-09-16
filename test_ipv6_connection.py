"""
Test PostgreSQL connection using IPv6 bracketed literal with host parameter
Based on Supabase guidance for Windows IPv6 connections
"""

import psycopg2
import sys

# IPv6 address from DNS resolution
IPV6_ADDRESS = "2600:1f18:2e13:9d1e:1be4:2e84:a39b:d518"
HOST_NAME = "db.pmispwtdngkcmsrsjwbp.supabase.co"
PASSWORD = "West@Boca613!"

print("=" * 70)
print("TESTING IPv6 DIRECT CONNECTION (Windows Workaround)")
print("=" * 70)

print(f"\nIPv6 Address: [{IPV6_ADDRESS}]")
print(f"Host (for SNI): {HOST_NAME}")
print(f"User: postgres")
print(f"Port: 5432")
print(f"Database: postgres")

# Try different connection methods
connection_attempts = [
    {
        "name": "Method 1: Parameters with hostaddr",
        "params": {
            "host": HOST_NAME,  # For SNI
            "hostaddr": IPV6_ADDRESS,  # Actual IPv6
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": PASSWORD,
            "sslmode": "require"
        }
    },
    {
        "name": "Method 2: Bracketed IPv6 in host",
        "params": {
            "host": f"[{IPV6_ADDRESS}]",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": PASSWORD,
            "sslmode": "require"
        }
    },
    {
        "name": "Method 3: Direct IPv6 as host",
        "params": {
            "host": IPV6_ADDRESS,
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": PASSWORD,
            "sslmode": "require"
        }
    }
]

conn = None
successful_method = None

for attempt in connection_attempts:
    try:
        print(f"\n{attempt['name']}...")
        conn = psycopg2.connect(**attempt['params'])
        print(">>> SUCCESS! Connected to database <<<")
        successful_method = attempt['name']
        break
    except Exception as e:
        print(f"Failed: {str(e)[:100]}")
        continue

if not conn:
    print("\n" + "=" * 70)
    print("ALL CONNECTION ATTEMPTS FAILED")
    print("=" * 70)
    print("\n✗ All IPv6 connection methods failed")
    print("\nTroubleshooting:")
    print("1. Check if Windows firewall allows outbound port 5432")
    print("2. Verify IPv6 connectivity is enabled")
    print("3. Consider using WSL2 as an alternative")
    print("4. Or use REST API with timeout workarounds")
    sys.exit(1)

try:
    print(f"\nUsing: {successful_method}")
    print(">>> SUCCESS! Connected to database via IPv6 <<<")
    
    # Test queries
    cur = conn.cursor()
    
    # Get database info
    cur.execute("SELECT current_database(), current_user, version()")
    db, user, version = cur.fetchone()
    print(f"\nDatabase: {db}")
    print(f"User: {user}")
    print(f"Version: {version[:50]}...")
    
    # Check florida_parcels table
    cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
    count = cur.fetchone()[0]
    print(f"\nTotal records in florida_parcels: {count:,}")
    
    # Check statement timeout
    cur.execute("SHOW statement_timeout")
    timeout = cur.fetchone()[0]
    print(f"Current statement_timeout: {timeout}")
    
    # Check for staging table
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'florida_parcels_staging'
        )
    """)
    staging_exists = cur.fetchone()[0]
    print(f"Staging table exists: {staging_exists}")
    
    # Get top 5 counties by count
    print("\nTop 5 counties by record count:")
    cur.execute("""
        SELECT county, COUNT(*) as count
        FROM public.florida_parcels
        GROUP BY county
        ORDER BY count DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<20} {row[1]:>10,}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("IPv6 CONNECTION SUCCESSFUL!")
    print("Ready for COPY operations")
    print("=" * 70)
    
    print("\nNext steps:")
    print("1. Update optimized_psycopg_loader.py with this connection format")
    print("2. Run the COPY loader to upload remaining 6.2M records")
    print("3. Create indexes after bulk load completes")
    
except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    if conn:
        conn.close()
    sys.exit(1)