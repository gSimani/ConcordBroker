"""
Test direct PostgreSQL connection using psycopg
"""

import psycopg

# Try different connection variations
connections_to_test = [
    {
        "name": "Pooler with full user",
        "conn_string": "postgresql://postgres.pmispwtdngkcmsrsjwbp:West@Boca613!@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    },
    {
        "name": "Pooler port 6543", 
        "conn_string": "postgresql://postgres.pmispwtdngkcmsrsjwbp:West@Boca613!@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    }
]

print("Testing PostgreSQL connections with psycopg...")
print("=" * 60)

for conn_info in connections_to_test:
    print(f"\nTesting: {conn_info['name']}")
    print(f"Connection string: {conn_info['conn_string'][:50]}...")
    
    try:
        # Try to connect
        with psycopg.connect(conn_info['conn_string']) as conn:
            print("SUCCESS - Connected!")
            
            # Test query
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
                count = cur.fetchone()[0]
                print(f"Total records in florida_parcels: {count:,}")
                
                # Check statement timeout
                cur.execute("SHOW statement_timeout")
                timeout = cur.fetchone()[0]
                print(f"Current statement_timeout: {timeout}")
                
            break  # Stop on first successful connection
            
    except Exception as e:
        print(f"FAILED: {e}")

print("\n" + "=" * 60)