"""
Test direct PostgreSQL connection with correct format
"""

import psycopg

# Direct connection for COPY operations (not pooler)
CONNECTION_STRING = "postgresql://postgres:West@Boca613!@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres?sslmode=require"

print("Testing DIRECT database connection for COPY operations...")
print("=" * 60)
print(f"Host: db.pmispwtdngkcmsrsjwbp.supabase.co")
print(f"User: postgres (without .ref suffix)")
print(f"SSL: required")
print("=" * 60)

try:
    # Connect to direct database (not pooler)
    print("\nConnecting to direct database...")
    with psycopg.connect(CONNECTION_STRING) as conn:
        print("SUCCESS! Connected to direct database")
        
        # Test queries
        with conn.cursor() as cur:
            # Check total records
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
            
            # Get top counties
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
            
        print("\n" + "=" * 60)
        print("Connection test SUCCESSFUL!")
        print("Ready for COPY operations")
        
except Exception as e:
    print(f"\nFAILED: {e}")
    print("\nTroubleshooting:")
    print("1. Check if project is paused in Supabase dashboard")
    print("2. Verify project ref: pmispwtdngkcmsrsjwbp")
    print("3. Check network/firewall allows port 5432")
    print("4. Try from Supabase Dashboard -> Settings -> Database -> Connection string")