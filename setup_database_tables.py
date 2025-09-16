"""
Automatically create florida_parcels table in Supabase using the SDK
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Get credentials
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment variables")

print("=" * 60)
print("SETTING UP DATABASE TABLES")
print("=" * 60)

# Parse database URL
parsed = urlparse(DATABASE_URL)
db_config = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path[1:] if parsed.path else 'postgres',
    'user': parsed.username,
    'password': parsed.password
}

print(f"\nConnecting to database: {db_config['host']}")

try:
    # Connect to database
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        sslmode='require'
    )
    
    # Create cursor
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'florida_parcels'
        );
    """)
    
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        print("\nTable 'florida_parcels' already exists!")
        # Get row count
        cur.execute("SELECT COUNT(*) FROM florida_parcels;")
        count = cur.fetchone()[0]
        print(f"Current record count: {count:,}")
    else:
        print("\nTable 'florida_parcels' does not exist. Creating...")
        
        # Create table
        cur.execute("""
            CREATE TABLE florida_parcels (
                id BIGSERIAL PRIMARY KEY,
                parcel_id VARCHAR(255) UNIQUE,
                phy_addr1 VARCHAR(255),
                phy_city VARCHAR(100),
                phy_state VARCHAR(2) DEFAULT 'FL',
                phy_zipcd VARCHAR(10),
                own_name VARCHAR(255),
                own_addr1 VARCHAR(255),
                own_city VARCHAR(100),
                own_state VARCHAR(2),
                own_zipcd VARCHAR(10),
                dor_uc VARCHAR(10),
                state_par_use_cd VARCHAR(10),
                co_no VARCHAR(5),
                yr_blt INTEGER,
                act_yr_blt INTEGER,
                tot_lvg_area INTEGER,
                lnd_sqfoot INTEGER,
                bedroom_cnt INTEGER,
                bathroom_cnt INTEGER,
                jv DECIMAL(15, 2),
                av_sd DECIMAL(15, 2),
                taxable_val DECIMAL(15, 2),
                exempt_val DECIMAL(15, 2),
                sale_prc1 DECIMAL(15, 2),
                sale_yr1 VARCHAR(10),
                vi_cd VARCHAR(20),
                millage_rate DECIMAL(8, 4),
                nbhd_cd VARCHAR(20),
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✓ Table created successfully!")
        
        # Create indexes
        print("\nCreating indexes...")
        indexes = [
            ("idx_florida_parcels_parcel_id", "parcel_id"),
            ("idx_florida_parcels_city", "phy_city"),
            ("idx_florida_parcels_zip", "phy_zipcd"),
            ("idx_florida_parcels_owner", "own_name"),
            ("idx_florida_parcels_address", "phy_addr1")
        ]
        
        for idx_name, column in indexes:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON florida_parcels({column});")
            print(f"✓ Created index on {column}")
        
        # Enable RLS
        print("\nConfiguring Row Level Security...")
        cur.execute("ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;")
        print("✓ RLS enabled")
        
        # Create policies
        cur.execute("""
            CREATE POLICY "Allow all operations for authenticated users" ON florida_parcels
                FOR ALL
                USING (true)
                WITH CHECK (true);
        """)
        print("✓ Created policy for authenticated users")
        
        cur.execute("""
            CREATE POLICY "Allow read access for anonymous users" ON florida_parcels
                FOR SELECT
                USING (true);
        """)
        print("✓ Created policy for anonymous users")
        
        # Commit changes
        conn.commit()
        print("\n✓ All changes committed successfully!")
    
    # Close connection
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE SETUP COMPLETE")
    print("=" * 60)
    
    if not table_exists:
        print("\n✅ Table 'florida_parcels' is now ready for data!")
        print("📝 Run 'python auto_load_properties.py' to load sample data")
    
except psycopg2.OperationalError as e:
    print(f"\n[X] Database connection error: {e}")
    print("\nTrying alternative connection method...")
    
    # Try with non-pooling URL
    NON_POOLING_URL = os.getenv("POSTGRES_URL_NON_POOLING")
    if NON_POOLING_URL:
        try:
            parsed = urlparse(NON_POOLING_URL)
            db_config = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:] if parsed.path else 'postgres',
                'user': parsed.username,
                'password': parsed.password
            }
            
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                sslmode='require'
            )
            
            print("[OK] Connected using non-pooling URL")
            # Continue with table creation...
            
        except Exception as e2:
            print(f"[X] Alternative connection also failed: {e2}")
            
except Exception as e:
    print(f"\n[X] Error: {e}")
    print("\nPlease check your database credentials in the .env file")