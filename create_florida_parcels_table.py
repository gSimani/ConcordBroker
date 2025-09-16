"""
Create florida_parcels table in Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import requests

# Load environment variables
load_dotenv()

# Get credentials - use service role key for admin operations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials")

print(f"Connecting to Supabase: {SUPABASE_URL}")

# Create the table using Supabase API
headers = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json'
}

# SQL command to create the table
sql_command = """
CREATE TABLE IF NOT EXISTS florida_parcels (
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_zip ON florida_parcels(phy_zipcd);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON florida_parcels(own_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON florida_parcels(phy_addr1);

-- Enable Row Level Security
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow all operations for authenticated users
CREATE POLICY "Allow all operations for authenticated users" ON florida_parcels
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Create a policy to allow read access for anonymous users
CREATE POLICY "Allow read access for anonymous users" ON florida_parcels
    FOR SELECT
    USING (true);
"""

# Execute SQL via Supabase API
api_url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

try:
    # First, let's use the client to check if the table exists
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Try to query the table
    try:
        response = supabase.table('florida_parcels').select('id').limit(1).execute()
        print("Table 'florida_parcels' already exists!")
        
        # Get count
        count_response = supabase.table('florida_parcels').select('*', count='exact', head=True).execute()
        print(f"Current record count: {count_response.count if hasattr(count_response, 'count') else 'Unknown'}")
        
    except Exception as e:
        error_str = str(e)
        if "relation" in error_str and "does not exist" in error_str:
            print("Table 'florida_parcels' does not exist. Please create it manually in Supabase dashboard.")
            print("\nSQL to create the table:")
            print("=" * 60)
            print(sql_command)
            print("=" * 60)
            print("\nSteps to create the table:")
            print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
            print("2. Select your project")
            print("3. Go to SQL Editor")
            print("4. Copy and paste the SQL above")
            print("5. Click 'Run'")
        else:
            print(f"Error checking table: {error_str}")

except Exception as e:
    print(f"Error connecting to Supabase: {e}")