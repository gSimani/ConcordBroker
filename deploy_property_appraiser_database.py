#!/usr/bin/env python3
"""
Deploy Property Appraiser Database Tables to Supabase
This script creates all necessary tables and indexes for the Property Appraiser system
"""

import os
import sys
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import httpx

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

# Load environment variables
load_dotenv('.env.mcp')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing Supabase credentials in .env.mcp")
    sys.exit(1)

print("=" * 80)
print("PROPERTY APPRAISER DATABASE DEPLOYMENT")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Target: {SUPABASE_URL}")
print("=" * 80)

# Initialize Supabase client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def execute_sql_file(filename: str, description: str):
    """Execute SQL from a file"""
    print(f"\n{description}...")

    if not os.path.exists(filename):
        print(f"  [ERROR] File not found: {filename}")
        return False

    try:
        with open(filename, 'r') as f:
            sql_content = f.read()

        # Note: Direct SQL execution requires SUPABASE_ENABLE_SQL=true
        # For production, use Supabase Dashboard or migration tools
        print(f"  [INFO] SQL file ready: {filename}")
        print(f"  [INFO] Contains {len(sql_content)} characters")
        print(f"  [ACTION] Please execute this SQL in Supabase Dashboard SQL Editor")

        # Save to deployment folder for manual execution
        os.makedirs('deployment', exist_ok=True)
        deployment_file = f"deployment/{os.path.basename(filename)}"
        with open(deployment_file, 'w') as f:
            f.write(sql_content)
        print(f"  [SAVED] SQL saved to: {deployment_file}")

        return True

    except Exception as e:
        print(f"  [ERROR] Failed to process SQL: {e}")
        return False

def create_supporting_tables():
    """Create SQL for NAV, NAP, and SDF tables"""

    nav_sql = """
-- NAV (Assessed Values) Table
CREATE TABLE IF NOT EXISTS nav_assessments (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Values
    just_value BIGINT,
    assessed_value BIGINT,
    taxable_value BIGINT,
    land_value BIGINT,
    building_value BIGINT,

    -- Exemptions
    homestead_exemption BIGINT,
    other_exemptions BIGINT,
    total_exemptions BIGINT,

    -- Additional fields
    special_assessments BIGINT,
    tax_district TEXT,
    millage_rate DECIMAL(10,4),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year)
);

CREATE INDEX idx_nav_parcel_county_year ON nav_assessments(parcel_id, county, year);
CREATE INDEX idx_nav_county_year ON nav_assessments(county, year);
"""

    nap_sql = """
-- NAP (Property Characteristics) Table
CREATE TABLE IF NOT EXISTS nap_characteristics (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Building characteristics
    year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area INTEGER,
    heated_area INTEGER,
    gross_area INTEGER,
    adjusted_area INTEGER,

    -- Rooms
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    half_bathrooms INTEGER,
    full_bathrooms INTEGER,

    -- Structure
    stories DECIMAL(3,1),
    units INTEGER,
    buildings INTEGER,

    -- Construction
    construction_type TEXT,
    exterior_wall TEXT,
    roof_type TEXT,
    roof_material TEXT,
    foundation_type TEXT,

    -- Features
    pool BOOLEAN,
    garage_spaces INTEGER,
    carport_spaces INTEGER,
    fireplace_count INTEGER,

    -- Quality and condition
    quality_grade TEXT,
    condition_code TEXT,

    -- Land
    lot_size_sqft BIGINT,
    lot_size_acres DECIMAL(10,4),
    frontage INTEGER,
    depth INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year)
);

CREATE INDEX idx_nap_parcel_county_year ON nap_characteristics(parcel_id, county, year);
CREATE INDEX idx_nap_county_year ON nap_characteristics(county, year);
CREATE INDEX idx_nap_year_built ON nap_characteristics(year_built);
"""

    sdf_sql = """
-- SDF (Sales Data File) Table
CREATE TABLE IF NOT EXISTS sdf_sales (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Sale information
    sale_date DATE,
    sale_price BIGINT,
    sale_year INTEGER,
    sale_month INTEGER,

    -- Sale details
    sale_type TEXT,
    sale_qualification TEXT,
    deed_type TEXT,
    verified_sale BOOLEAN,

    -- Parties
    grantor_name TEXT,
    grantee_name TEXT,

    -- Recording info
    book_page TEXT,
    instrument_number TEXT,
    or_book TEXT,
    or_page TEXT,
    clerk_number TEXT,

    -- Multi-parcel sale
    multi_parcel_sale BOOLEAN,
    parcel_count INTEGER,

    -- Vacancy
    vacant_at_sale BOOLEAN,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year, sale_date)
);

CREATE INDEX idx_sdf_parcel_county_year ON sdf_sales(parcel_id, county, year);
CREATE INDEX idx_sdf_county_year ON sdf_sales(county, year);
CREATE INDEX idx_sdf_sale_date ON sdf_sales(sale_date);
CREATE INDEX idx_sdf_sale_price ON sdf_sales(sale_price);
"""

    # Save supporting table SQL
    tables = {
        'nav_assessments.sql': nav_sql,
        'nap_characteristics.sql': nap_sql,
        'sdf_sales.sql': sdf_sql
    }

    os.makedirs('deployment', exist_ok=True)
    for filename, sql in tables.items():
        filepath = f'deployment/{filename}'
        with open(filepath, 'w') as f:
            f.write(sql)
        print(f"  [CREATED] {filepath}")

    return True

def verify_table_creation():
    """Verify tables were created successfully"""
    print("\n4. VERIFYING TABLE CREATION")
    print("-" * 40)

    tables_to_check = [
        'florida_parcels',
        'nav_assessments',
        'nap_characteristics',
        'sdf_sales'
    ]

    results = {}
    for table_name in tables_to_check:
        try:
            # Try to select from table
            result = supabase.table(table_name).select('*').limit(1).execute()
            results[table_name] = True
            print(f"  [OK] {table_name} exists")
        except Exception as e:
            results[table_name] = False
            print(f"  [PENDING] {table_name} not yet created")

    return results

def generate_deployment_script():
    """Generate a combined SQL deployment script"""
    print("\n5. GENERATING COMBINED DEPLOYMENT SCRIPT")
    print("-" * 40)

    combined_sql = f"""
-- ============================================================================
-- PROPERTY APPRAISER DATABASE DEPLOYMENT SCRIPT
-- Generated: {datetime.now().isoformat()}
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

"""

    # Add florida_parcels schema
    if os.path.exists('create_florida_parcels_schema.sql'):
        with open('create_florida_parcels_schema.sql', 'r') as f:
            combined_sql += f.read() + "\n\n"

    # Add indexes
    if os.path.exists('CREATE_INDEXES.sql'):
        with open('CREATE_INDEXES.sql', 'r') as f:
            combined_sql += "-- Additional Indexes\n" + f.read() + "\n\n"

    # Add supporting tables
    for filename in ['nav_assessments.sql', 'nap_characteristics.sql', 'sdf_sales.sql']:
        filepath = f'deployment/{filename}'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                combined_sql += f"-- {filename}\n" + f.read() + "\n\n"

    # Add timeout configuration
    combined_sql += """
-- ============================================================================
-- PERFORMANCE CONFIGURATION
-- ============================================================================

-- For bulk uploads, temporarily disable timeouts:
-- ALTER ROLE authenticator SET statement_timeout = 0;
-- ALTER ROLE anon SET statement_timeout = 0;
-- ALTER ROLE service_role SET statement_timeout = 0;

-- After upload, restore timeouts:
-- ALTER ROLE authenticator SET statement_timeout = '10s';
-- ALTER ROLE anon SET statement_timeout = '10s';
-- ALTER ROLE service_role SET statement_timeout = '30s';

-- ============================================================================
-- DEPLOYMENT COMPLETE
-- ============================================================================
"""

    # Save combined script
    deployment_file = 'deployment/DEPLOY_ALL_PROPERTY_APPRAISER_TABLES.sql'
    with open(deployment_file, 'w') as f:
        f.write(combined_sql)

    print(f"  [CREATED] {deployment_file}")
    print(f"  [INFO] Total SQL size: {len(combined_sql)} characters")

    return deployment_file

def main():
    """Main deployment process"""

    # Step 1: Process florida_parcels schema
    print("\n1. PREPARING FLORIDA_PARCELS TABLE")
    print("-" * 40)
    execute_sql_file(
        'create_florida_parcels_schema.sql',
        'Processing florida_parcels schema'
    )

    # Step 2: Process indexes
    print("\n2. PREPARING INDEXES")
    print("-" * 40)
    execute_sql_file(
        'CREATE_INDEXES.sql',
        'Processing performance indexes'
    )

    # Step 3: Create supporting tables
    print("\n3. CREATING SUPPORTING TABLE SCHEMAS")
    print("-" * 40)
    create_supporting_tables()

    # Step 4: Verify tables (will show as pending until SQL is executed)
    verify_table_creation()

    # Step 5: Generate combined deployment script
    deployment_script = generate_deployment_script()

    # Final instructions
    print("\n" + "=" * 80)
    print("DEPLOYMENT INSTRUCTIONS")
    print("=" * 80)
    print("\n1. Open Supabase Dashboard: https://app.supabase.com")
    print("2. Navigate to SQL Editor")
    print("3. Create new query")
    print(f"4. Copy and paste content from: {deployment_script}")
    print("5. Execute the SQL")
    print("6. Verify all tables are created successfully")
    print("\n7. After tables are created, run:")
    print("   python test_property_appraiser_tables.py")
    print("\n8. Then load sample data with:")
    print("   python load_broward_sample_data.py")

    print("\n" + "=" * 80)
    print("DEPLOYMENT SCRIPT READY")
    print("=" * 80)

if __name__ == "__main__":
    main()