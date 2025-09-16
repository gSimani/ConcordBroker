#!/usr/bin/env python3
"""Create florida_parcels table in Supabase"""

from supabase import create_client
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("DATABASE_URL not found in .env")
    exit(1)

# Parse the database URL
url = urlparse(database_url)
db_config = {
    'host': url.hostname,
    'port': url.port,
    'database': url.path[1:],
    'user': url.username,
    'password': url.password
}

# Connect to the database
print("Connecting to database...")
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# Create the florida_parcels table
create_table_sql = """
CREATE TABLE IF NOT EXISTS florida_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50),
    year INTEGER,
    
    -- Owner info
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Physical address
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Property details
    property_use VARCHAR(10),
    property_use_desc VARCHAR(255),
    year_built INTEGER,
    total_living_area FLOAT,
    bedrooms INTEGER,
    bathrooms FLOAT,
    
    -- Valuations
    just_value FLOAT,
    assessed_value FLOAT,
    taxable_value FLOAT,
    land_value FLOAT,
    building_value FLOAT,
    
    -- Sales info
    sale_date TIMESTAMP,
    sale_price FLOAT,
    
    -- Data flags
    is_redacted BOOLEAN DEFAULT FALSE,
    import_date TIMESTAMP DEFAULT NOW()
);
"""

try:
    cur.execute(create_table_sql)
    conn.commit()
    print("✓ florida_parcels table created successfully")
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);",
        "CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);",
        "CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1, phy_city);",
        "CREATE INDEX IF NOT EXISTS idx_parcels_value ON florida_parcels(taxable_value);"
    ]
    
    for idx_sql in indexes:
        cur.execute(idx_sql)
    conn.commit()
    print("✓ Indexes created")
    
except Exception as e:
    print(f"Error creating table: {e}")
    conn.rollback()

# Check if table was created
cur.execute("SELECT COUNT(*) FROM florida_parcels;")
count = cur.fetchone()[0]
print(f"✓ Table has {count} records")

# Close connection
cur.close()
conn.close()
print("Done!")