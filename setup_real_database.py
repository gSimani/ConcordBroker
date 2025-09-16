import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

# We need the service key to bypass RLS - let's check if it's available
SUPABASE_SERVICE_KEY = os.getenv('VITE_SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found in .env file")
    exit(1)

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Using {'service' if SUPABASE_SERVICE_KEY else 'anon'} key")

# Use service key if available, otherwise use anon key
API_KEY = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

# Headers for API requests
headers = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def check_table(table_name):
    """Check if a table exists and count records"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=1"
    
    # Use count header to get total count
    count_headers = headers.copy()
    count_headers['Prefer'] = 'count=exact'
    
    response = requests.get(url, headers=count_headers)
    
    if response.status_code == 200:
        # Get count from header
        count = response.headers.get('content-range', '').split('/')[-1]
        if count == '*':
            count = len(response.json())
        return True, int(count) if count.isdigit() else 0
    else:
        return False, 0

def create_tables_sql():
    """Generate SQL to create necessary tables"""
    return """
-- Florida Parcels table (main property data)
CREATE TABLE IF NOT EXISTS florida_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    year INTEGER,
    
    -- Property location
    phy_addr1 VARCHAR(255),
    phy_addr2 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2),
    phy_zipcd VARCHAR(10),
    
    -- Owner information
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_addr2 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Property characteristics
    property_use VARCHAR(10),
    property_use_desc VARCHAR(100),
    usage_code VARCHAR(10),
    year_built INTEGER,
    eff_year_built INTEGER,
    total_living_area INTEGER,
    heated_area INTEGER,
    land_sqft INTEGER,
    lot_size INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    units INTEGER,
    
    -- Values
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    improvement_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    
    -- Tax information
    tax_amount DECIMAL(12,2),
    homestead_exemption VARCHAR(1),
    other_exemptions VARCHAR(255),
    
    -- Sale information
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(parcel_id, county, year)
);

-- Sales history table
CREATE TABLE IF NOT EXISTS fl_sdf_sales (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    year INTEGER,
    
    sale_date DATE,
    sale_price DECIMAL(15,2),
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    qualification_code VARCHAR(10),
    is_qualified VARCHAR(1),
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    
    grantor_name VARCHAR(255),
    grantee_name VARCHAR(255),
    
    book_page VARCHAR(50),
    cin VARCHAR(50),
    recording_date DATE,
    record_link VARCHAR(500),
    
    property_address_full VARCHAR(500),
    property_address_street_name VARCHAR(255),
    property_address_city VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_parcel_sales (parcel_id),
    INDEX idx_sale_date (sale_date DESC)
);

-- Non-ad valorem assessments
CREATE TABLE IF NOT EXISTS fl_nav_assessment_detail (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    year INTEGER,
    
    assessment_type VARCHAR(100),
    assessment_amount DECIMAL(12,2),
    total_assessment DECIMAL(12,2),
    
    levying_authority VARCHAR(255),
    description VARCHAR(500),
    
    property_address VARCHAR(500),
    street_name VARCHAR(255),
    city_name VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_parcel_nav (parcel_id)
);

-- Tangible personal property
CREATE TABLE IF NOT EXISTS fl_tpp_accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(50),
    parcel_id VARCHAR(50),
    county VARCHAR(50),
    year INTEGER,
    
    owner_name VARCHAR(255),
    business_name VARCHAR(255),
    
    property_address VARCHAR(500),
    street_address VARCHAR(255),
    city VARCHAR(100),
    
    just_value DECIMAL(15,2),
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_parcel_tpp (parcel_id)
);

-- Sunbiz corporate filings
CREATE TABLE IF NOT EXISTS sunbiz_corporate_filings (
    id SERIAL PRIMARY KEY,
    
    entity_name VARCHAR(255),
    entity_type VARCHAR(100),
    status VARCHAR(50),
    state VARCHAR(2),
    
    document_number VARCHAR(50) UNIQUE,
    fei_ein_number VARCHAR(20),
    
    date_filed DATE,
    effective_date DATE,
    last_event_date DATE,
    
    principal_address VARCHAR(500),
    mailing_address VARCHAR(500),
    
    registered_agent_name VARCHAR(255),
    registered_agent_address VARCHAR(500),
    
    officers JSONB,
    annual_reports JSONB,
    filing_history JSONB,
    
    aggregate_id VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_entity_name (entity_name),
    INDEX idx_principal_addr (principal_address)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1);
CREATE INDEX IF NOT EXISTS idx_parcels_city ON florida_parcels(phy_city);

-- Enable Row Level Security (but allow all for now)
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_sdf_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_nav_assessment_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE fl_tpp_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate_filings ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public access (for now)
CREATE POLICY "Allow public read access" ON florida_parcels FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON florida_parcels FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update" ON florida_parcels FOR UPDATE USING (true);

CREATE POLICY "Allow public read access" ON fl_sdf_sales FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON fl_sdf_sales FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access" ON fl_nav_assessment_detail FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON fl_nav_assessment_detail FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access" ON fl_tpp_accounts FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON fl_tpp_accounts FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public read access" ON sunbiz_corporate_filings FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON sunbiz_corporate_filings FOR INSERT WITH CHECK (true);
"""

# Check existing tables
print("\nChecking existing tables:")
print("-" * 50)

tables_to_check = [
    'florida_parcels',
    'fl_sdf_sales',
    'fl_nav_assessment_detail', 
    'fl_tpp_accounts',
    'sunbiz_corporate_filings'
]

all_tables_exist = True
for table in tables_to_check:
    exists, count = check_table(table)
    if exists:
        print(f"[OK] {table}: {count} records")
    else:
        print(f"[MISSING] {table}: Does not exist")
        all_tables_exist = False

if not all_tables_exist:
    print("\n" + "=" * 50)
    print("Some tables are missing. To create them:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the SQL script saved in: create_tables.sql")
    
    # Save SQL to file
    with open('create_tables.sql', 'w') as f:
        f.write(create_tables_sql())
    print("\nSQL script saved to: create_tables.sql")
    
else:
    print("\n" + "=" * 50)
    print("All tables exist! Now we need to load real data.")
    print("\nNext step: Run load_florida_data.py to populate the database")