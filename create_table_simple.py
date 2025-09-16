"""
Simple script to create florida_parcels table using correct Supabase credentials
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
from urllib.parse import urlparse, unquote

# Load environment variables
load_dotenv()

print("=" * 60)
print("CREATING FLORIDA_PARCELS TABLE")  
print("=" * 60)

# Try different connection strings
connection_strings = [
    os.getenv("DATABASE_URL"),
    os.getenv("POSTGRES_URL_NON_POOLING"),
    os.getenv("POSTGRES_URL")
]

# Try to connect with different URLs
for conn_str in connection_strings:
    if not conn_str:
        continue
        
    print(f"\nTrying connection: {conn_str[:50]}...")
    
    try:
        # Parse and clean the URL
        parsed = urlparse(conn_str)
        
        # Decode password if URL encoded
        password = unquote(parsed.password) if parsed.password else None
        
        # Connect directly
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:] if parsed.path else 'postgres',
            user=parsed.username,
            password=password,
            sslmode='require'
        )
        
        print("[OK] Connected successfully!")
        
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
            cur.execute("SELECT COUNT(*) FROM florida_parcels;")
            count = cur.fetchone()[0]
            print(f"Current record count: {count:,}")
        else:
            print("\nCreating table 'florida_parcels'...")
            
            # Simple table creation
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
            
            # Commit the table creation
            conn.commit()
            print("[OK] Table created successfully!")
            
            # Create basic index on parcel_id
            cur.execute("CREATE INDEX idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);")
            conn.commit()
            print("[OK] Index created on parcel_id")
        
        # Close connection
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        
        if not table_exists:
            print("\nTable 'florida_parcels' is now ready for data!")
            print("Run 'python auto_load_properties.py' to load sample data")
        
        break  # Success, exit loop
        
    except Exception as e:
        print(f"[X] Connection failed: {str(e)[:100]}")
        continue

else:
    print("\n[X] Could not connect to database with any connection string")
    print("\nPlease check your .env file has valid database credentials")