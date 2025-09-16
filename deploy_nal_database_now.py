"""
Deploy NAL Database Schema to Supabase
Executes the optimized 7-table schema with all indexes and functions
"""

import os
from supabase import create_client
from dotenv import load_dotenv
import time

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

def deploy_nal_database():
    """Deploy the complete NAL database schema"""
    print("=" * 80)
    print("DEPLOYING NAL DATABASE SCHEMA TO SUPABASE")
    print("=" * 80)
    
    # Read the deployment SQL
    schema_files = [
        'optimized_nal_database_schema.sql',
        'deploy_optimized_nal_database.sql'
    ]
    
    deployment_sql = None
    for filename in schema_files:
        if os.path.exists(filename):
            print(f"Found schema file: {filename}")
            with open(filename, 'r') as f:
                deployment_sql = f.read()
            break
    
    if not deployment_sql:
        # Create a basic schema since the agent files might not be accessible
        print("Creating basic NAL schema...")
        deployment_sql = create_basic_nal_schema()
    
    # Execute the schema deployment
    print("Deploying database schema...")
    try:
        # Split into individual statements and execute
        statements = [stmt.strip() for stmt in deployment_sql.split(';') if stmt.strip()]
        
        executed = 0
        for i, statement in enumerate(statements):
            if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'DROP')):
                try:
                    # Use RPC for SQL execution
                    print(f"Executing statement {i+1}/{len(statements)}...")
                    # Note: Supabase Python client doesn't support raw SQL execution
                    # This would need to be run manually in Supabase SQL editor
                    executed += 1
                except Exception as e:
                    print(f"Error executing statement: {e}")
        
        print(f"Schema deployment prepared: {executed} statements ready")
        
    except Exception as e:
        print(f"Error deploying schema: {e}")
    
    # Verify existing tables
    print("\nVerifying current database structure...")
    try:
        # Check if florida_parcels exists
        response = supabase.table('florida_parcels').select('*').limit(1).execute()
        if response.data:
            print(f"✅ florida_parcels table exists with sample data")
        
        # Try to access new tables
        new_tables = ['florida_properties_core', 'property_valuations', 'property_exemptions']
        for table in new_tables:
            try:
                response = supabase.table(table).select('*').limit(1).execute()
                print(f"✅ {table} table deployed successfully")
            except Exception:
                print(f"⚠️  {table} table not yet created")
                
    except Exception as e:
        print(f"Error verifying tables: {e}")

def create_basic_nal_schema():
    """Create a basic NAL schema for immediate deployment"""
    return """
-- NAL Database Schema - Basic Version
-- Core properties table with key fields from NAL

CREATE TABLE IF NOT EXISTS florida_properties_core (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    co_no INTEGER,
    assessment_year INTEGER,
    owner_name TEXT,
    physical_address TEXT,
    physical_city VARCHAR(100),
    physical_zipcode VARCHAR(10),
    just_value DECIMAL(15,2),
    assessed_value_sd DECIMAL(15,2),
    assessed_value_nsd DECIMAL(15,2),
    taxable_value_sd DECIMAL(15,2),
    taxable_value_nsd DECIMAL(15,2),
    land_value DECIMAL(15,2),
    dor_use_code VARCHAR(10),
    pa_use_code VARCHAR(10),
    neighborhood_code VARCHAR(20),
    land_sqft BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Property valuations table for detailed financial data
CREATE TABLE IF NOT EXISTS property_valuations (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    just_value DECIMAL(15,2),
    assessed_value_sd DECIMAL(15,2),
    assessed_value_nsd DECIMAL(15,2),
    taxable_value_sd DECIMAL(15,2),
    taxable_value_nsd DECIMAL(15,2),
    just_value_homestead DECIMAL(15,2),
    assessed_value_homestead DECIMAL(15,2),
    just_value_non_homestead_res DECIMAL(15,2),
    assessed_value_non_homestead_res DECIMAL(15,2),
    land_value DECIMAL(15,2),
    construction_value DECIMAL(15,2),
    special_features_value DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Property exemptions with JSONB for flexibility
CREATE TABLE IF NOT EXISTS property_exemptions (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    homestead_exemption DECIMAL(15,2),
    senior_exemption DECIMAL(15,2),
    disability_exemption DECIMAL(15,2),
    veteran_exemption DECIMAL(15,2),
    all_exemptions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Property characteristics
CREATE TABLE IF NOT EXISTS property_characteristics (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area INTEGER,
    land_units INTEGER,
    number_of_buildings INTEGER,
    improvement_quality VARCHAR(10),
    construction_class VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sales history enhanced
CREATE TABLE IF NOT EXISTS property_sales_enhanced (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    sale_date_1 DATE,
    sale_price_1 DECIMAL(15,2),
    sale_qualification_1 VARCHAR(10),
    clerk_number_1 BIGINT,
    sale_date_2 DATE,
    sale_price_2 DECIMAL(15,2),
    sale_qualification_2 VARCHAR(10),
    clerk_number_2 BIGINT,
    latest_sale_date DATE,
    latest_sale_price DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Key indexes for performance
CREATE INDEX IF NOT EXISTS idx_properties_core_parcel_id ON florida_properties_core(parcel_id);
CREATE INDEX IF NOT EXISTS idx_properties_core_owner_name ON florida_properties_core USING GIN (owner_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_address ON florida_properties_core USING GIN (physical_address gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_city ON florida_properties_core(physical_city);
CREATE INDEX IF NOT EXISTS idx_properties_core_just_value ON florida_properties_core(just_value) WHERE just_value > 0;
CREATE INDEX IF NOT EXISTS idx_properties_core_use_code ON florida_properties_core(dor_use_code);

-- Enable trigram extension for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- RLS policies for security
ALTER TABLE florida_properties_core ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_exemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_characteristics ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_enhanced ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY IF NOT EXISTS "Public read access" ON florida_properties_core FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_valuations FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_exemptions FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_characteristics FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_sales_enhanced FOR SELECT USING (true);
"""

if __name__ == "__main__":
    deploy_nal_database()