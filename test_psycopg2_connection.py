"""
Test PostgreSQL connection using psycopg2 (different library)
"""

import psycopg2
from psycopg2 import sql

# Connection parameters
connections_to_test = [
    {
        "name": "Direct connection (IPv6)",
        "params": {
            "host": "db.pmispwtdngkcmsrsjwbp.supabase.co",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": "West@Boca613!",
            "sslmode": "require"
        }
    },
    {
        "name": "Pooler connection (IPv4)",
        "params": {
            "host": "aws-0-us-east-1.pooler.supabase.com",
            "port": 5432,
            "database": "postgres",
            "user": "postgres.pmispwtdngkcmsrsjwbp",
            "password": "West@Boca613!",
            "sslmode": "require"
        }
    },
    {
        "name": "Pooler connection port 6543",
        "params": {
            "host": "aws-0-us-east-1.pooler.supabase.com",
            "port": 6543,
            "database": "postgres",
            "user": "postgres.pmispwtdngkcmsrsjwbp",
            "password": "West@Boca613!",
            "sslmode": "require"
        }
    }
]

print("Testing PostgreSQL connections with psycopg2...")
print("=" * 60)

for conn_info in connections_to_test:
    print(f"\nTesting: {conn_info['name']}")
    print(f"Host: {conn_info['params']['host']}")
    print(f"Port: {conn_info['params']['port']}")
    print(f"User: {conn_info['params']['user']}")
    
    try:
        # Try to connect
        conn = psycopg2.connect(**conn_info['params'])
        print("SUCCESS - Connected!")
        
        # Test query
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
        count = cur.fetchone()[0]
        print(f"Total records in florida_parcels: {count:,}")
        
        # Check statement timeout
        cur.execute("SHOW statement_timeout")
        timeout = cur.fetchone()[0]
        print(f"Current statement_timeout: {timeout}")
        
        cur.close()
        conn.close()
        
        print("\nConnection successful! This method works.")
        break  # Stop on first successful connection
        
    except Exception as e:
        print(f"FAILED: {e}")

print("\n" + "=" * 60)
