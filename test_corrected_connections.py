"""
Test PostgreSQL connections with corrected credentials from Supabase support
"""

import psycopg2
from psycopg2 import sql

# Password provided
PASSWORD = "West@Boca613!"

# Connection parameters per Supabase support guidance
connections_to_test = [
    {
        "name": "Pooler connection (for testing only)",
        "params": {
            "host": "aws-0-us-east-1.pooler.supabase.com",
            "port": 6543,
            "database": "postgres",
            "user": "postgres.pmispwtdngkcmsrsjwbp",  # Correct format with project ref
            "password": PASSWORD,
            "sslmode": "require"
        }
    },
    {
        "name": "Direct connection (for COPY operations)",
        "params": {
            "host": "db.pmispwtdngkcmsrsjwbp.supabase.co",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",  # Just postgres for direct
            "password": PASSWORD,
            "sslmode": "require"
        }
    }
]

print("Testing PostgreSQL connections with CORRECTED credentials...")
print("=" * 60)

successful_connection = None

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
        
        # Get version
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"Database version: {version[:50]}...")
        
        # Get record count
        cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
        count = cur.fetchone()[0]
        print(f"Total records in florida_parcels: {count:,}")
        
        # Check statement timeout
        cur.execute("SHOW statement_timeout")
        timeout = cur.fetchone()[0]
        print(f"Current statement_timeout: {timeout}")
        
        # Check if staging table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'florida_parcels_staging'
            )
        """)
        staging_exists = cur.fetchone()[0]
        print(f"Staging table exists: {staging_exists}")
        
        # If this is direct connection, save it
        if "Direct" in conn_info['name']:
            successful_connection = conn_info['params']
            print("\nDIRECT CONNECTION SUCCESSFUL - Ready for COPY operations!")
        
        cur.close()
        
        # Keep connection open if it's the direct one
        if "Direct" not in conn_info['name']:
            conn.close()
        else:
            # Test a COPY-compatible operation
            cur = conn.cursor()
            cur.execute("SELECT 1")
            print("Can execute queries - connection is stable")
            cur.close()
            conn.close()
        
    except Exception as e:
        print(f"FAILED: {e}")

print("\n" + "=" * 60)

if successful_connection:
    print("\nREADY TO PROCEED WITH COPY OPERATIONS")
    print(f"Connection string for COPY:")
    print(f"postgresql://{successful_connection['user']}:PASSWORD@{successful_connection['host']}:{successful_connection['port']}/{successful_connection['database']}?sslmode=require")
else:
    print("\nNo successful connection - check with Supabase support")
    print("The direct host may only have IPv6 which is causing issues on Windows")
    print("Consider using a cloud environment or WSL for the upload")