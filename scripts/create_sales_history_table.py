"""
Create property_sales_history table in Supabase
"""

from supabase import create_client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to create the table
CREATE_TABLE_SQL = """
-- Create comprehensive property sales history table for Florida properties
CREATE TABLE IF NOT EXISTS property_sales_history (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    sale_date DATE,
    sale_year INTEGER,
    sale_month INTEGER,
    sale_day INTEGER,
    sale_price NUMERIC(12, 2),
    grantor VARCHAR(255),
    grantee VARCHAR(255),
    instrument_type VARCHAR(50),
    instrument_number VARCHAR(50),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    clerk_no VARCHAR(50),
    sale_qualification VARCHAR(50),
    quality_code VARCHAR(10),
    vi_code VARCHAR(10),
    reason VARCHAR(255),
    vacant_improved VARCHAR(20),
    property_use VARCHAR(50),
    qualified_sale BOOLEAN DEFAULT FALSE,
    arms_length BOOLEAN DEFAULT FALSE,
    multi_parcel BOOLEAN DEFAULT FALSE,
    foreclosure BOOLEAN DEFAULT FALSE,
    rea_sale BOOLEAN DEFAULT FALSE,
    short_sale BOOLEAN DEFAULT FALSE,
    distressed_sale BOOLEAN DEFAULT FALSE,
    data_source VARCHAR(50) DEFAULT 'SDF',
    import_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

# SQL to create indexes
CREATE_INDEXES_SQL = """
-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sales_parcel_id ON property_sales_history(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_county ON property_sales_history(county);
CREATE INDEX IF NOT EXISTS idx_sales_date ON property_sales_history(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_price ON property_sales_history(sale_price);
CREATE INDEX IF NOT EXISTS idx_sales_year ON property_sales_history(sale_year DESC);
CREATE INDEX IF NOT EXISTS idx_sales_qualified ON property_sales_history(qualified_sale);
CREATE INDEX IF NOT EXISTS idx_sales_parcel_date ON property_sales_history(parcel_id, sale_date DESC);
"""

def main():
    try:
        logger.info("Creating property_sales_history table...")

        # Note: Supabase client doesn't directly support raw SQL execution
        # You would need to use the Supabase dashboard or a direct PostgreSQL connection
        # For now, let's verify the table doesn't exist and provide instructions

        # Try to query the table to see if it exists
        try:
            result = supabase.table('property_sales_history').select('count', count='exact').limit(1).execute()
            logger.info(f"Table property_sales_history already exists with {result.count} records")
        except Exception as e:
            logger.info("Table property_sales_history does not exist yet")
            logger.info("\nTo create the table, please execute the following SQL in Supabase SQL Editor:")
            logger.info("=" * 80)
            print(CREATE_TABLE_SQL)
            print(CREATE_INDEXES_SQL)
            logger.info("=" * 80)
            logger.info("\n1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new")
            logger.info("2. Copy and paste the SQL above")
            logger.info("3. Click 'Run' to create the table and indexes")

            # Save SQL to file for convenience
            with open('create_sales_history_table.sql', 'w') as f:
                f.write(CREATE_TABLE_SQL)
                f.write("\n")
                f.write(CREATE_INDEXES_SQL)
            logger.info("\nSQL has been saved to: create_sales_history_table.sql")

    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()