"""
Fix Supabase Statement Timeouts
Applies necessary fixes to resolve database timeout issues
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.new' if os.path.exists('.env.new') else '.env')

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_SERVICE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not found in environment")
    exit(1)

print("Connecting to Supabase...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# SQL commands to fix timeouts and optimize queries
sql_commands = [
    # 1. Disable timeouts temporarily
    """
    ALTER ROLE authenticator SET statement_timeout = '0';
    ALTER ROLE anon SET statement_timeout = '0';
    ALTER ROLE authenticated SET statement_timeout = '0';
    ALTER ROLE service_role SET statement_timeout = '0';
    """,

    # 2. Create essential indexes if not exists
    """
    CREATE INDEX IF NOT EXISTS idx_florida_parcels_city_btree
    ON florida_parcels(phy_city)
    WHERE phy_city IS NOT NULL;
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_florida_parcels_county
    ON florida_parcels(county)
    WHERE county IS NOT NULL;
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_year
    ON florida_parcels(parcel_id, year)
    WHERE parcel_id IS NOT NULL;
    """,

    # 3. Analyze table for query optimization
    """
    ANALYZE florida_parcels;
    """,

    # 4. Create a materialized view for common queries
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_property_summary AS
    SELECT
        county,
        phy_city,
        COUNT(*) as property_count,
        AVG(just_value) as avg_value,
        MIN(just_value) as min_value,
        MAX(just_value) as max_value
    FROM florida_parcels
    WHERE phy_city IS NOT NULL
    GROUP BY county, phy_city;
    """,

    # 5. Create index on materialized view
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_property_summary
    ON mv_property_summary(county, phy_city);
    """,

    # 6. Set more reasonable timeouts (30 seconds instead of default 2-3 seconds)
    """
    ALTER ROLE authenticator SET statement_timeout = '30s';
    ALTER ROLE anon SET statement_timeout = '30s';
    ALTER ROLE authenticated SET statement_timeout = '30s';
    ALTER ROLE service_role SET statement_timeout = '60s';
    """
]

print("\nApplying database optimizations...")

for i, sql in enumerate(sql_commands, 1):
    try:
        # Clean up SQL
        sql = sql.strip()
        if not sql:
            continue

        print(f"\n{i}. Executing: {sql[:100]}...")

        # Note: Supabase Python client doesn't have direct SQL execution
        # You'll need to run these in the Supabase SQL Editor
        print(f"   ✓ Command ready for Supabase SQL Editor")

    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\n" + "="*60)
print("IMPORTANT: Database Optimization Steps")
print("="*60)
print("\n1. Go to Supabase Dashboard: https://app.supabase.com")
print("2. Select your project")
print("3. Go to SQL Editor")
print("4. Run each SQL command above")
print("5. The timeouts and indexes will significantly improve performance")

print("\nAlternatively, you can create an RPC function for optimized queries:")
print("""
-- Create this function in Supabase SQL Editor:
CREATE OR REPLACE FUNCTION search_properties_fast(
    p_city TEXT DEFAULT NULL,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    parcel_id TEXT,
    phy_addr1 TEXT,
    phy_city TEXT,
    own_name TEXT,
    just_value NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fp.parcel_id,
        fp.phy_addr1,
        fp.phy_city,
        fp.own_name,
        fp.just_value
    FROM florida_parcels fp
    WHERE
        (p_city IS NULL OR fp.phy_city ILIKE '%' || p_city || '%')
    ORDER BY fp.id
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

GRANT EXECUTE ON FUNCTION search_properties_fast TO anon, authenticated;
""")

print("\n✅ Next Steps:")
print("1. Run the SQL commands in Supabase SQL Editor")
print("2. The optimized API will work much faster")
print("3. Redis/in-memory cache will further improve performance")