#!/usr/bin/env python3
"""
Complete Property Appraiser Infrastructure Setup
Creates all required tables and sets up the data pipeline
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.mcp')

# Database configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
POSTGRES_URL = os.getenv('POSTGRES_URL')

class PropertyAppraiserSetup:
    """Setup and manage Property Appraiser database infrastructure"""

    def __init__(self):
        """Initialize database connections"""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        # Create SQLAlchemy engine for advanced operations
        self.engine = create_engine(POSTGRES_URL.replace('%40', '@'))
        logger.info("Initialized database connections")

    def create_florida_parcels_table(self):
        """Create the main florida_parcels table"""
        sql = """
        CREATE TABLE IF NOT EXISTS florida_parcels (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) NOT NULL,
            county VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL DEFAULT 2025,

            -- Owner information (NAL)
            owner_name VARCHAR(255),
            owner_addr1 VARCHAR(255),
            owner_addr2 VARCHAR(255),
            owner_city VARCHAR(100),
            owner_state VARCHAR(2),
            owner_zip VARCHAR(10),

            -- Physical address (NAL)
            phy_addr1 VARCHAR(255),
            phy_addr2 VARCHAR(255),
            phy_city VARCHAR(100),
            phy_state VARCHAR(2) DEFAULT 'FL',
            phy_zipcd VARCHAR(10),

            -- Property characteristics
            property_use VARCHAR(10),
            property_use_desc VARCHAR(255),
            land_sqft FLOAT,  -- From LND_SQFOOT

            -- Valuations (NAL/NAV)
            just_value FLOAT,  -- From JV
            assessed_value FLOAT,
            taxable_value FLOAT,
            land_value FLOAT,
            building_value FLOAT,

            -- Sales information
            sale_date TIMESTAMP,  -- Built from SALE_YR1/SALE_MO1
            sale_price FLOAT,

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            -- Composite unique constraint
            CONSTRAINT unique_parcel_county_year UNIQUE (parcel_id, county, year)
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_parcels_county ON florida_parcels(county);
        CREATE INDEX IF NOT EXISTS idx_parcels_year ON florida_parcels(year);
        CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name);
        CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1, phy_city);
        CREATE INDEX IF NOT EXISTS idx_parcels_value ON florida_parcels(just_value);
        CREATE INDEX IF NOT EXISTS idx_parcels_county_year ON florida_parcels(county, year);

        -- Enable Row Level Security
        ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

        -- Create public read policy
        CREATE POLICY "public_read_florida_parcels" ON florida_parcels
            FOR SELECT USING (true);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created florida_parcels table with indexes")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating florida_parcels: {e}")
            return False

    def create_nav_assessments_table(self):
        """Create NAV assessments table for property values"""
        sql = """
        CREATE TABLE IF NOT EXISTS nav_assessments (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) NOT NULL,
            county VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL DEFAULT 2025,

            -- Assessment values
            just_value FLOAT,
            assessed_value FLOAT,
            taxable_value FLOAT,
            land_value FLOAT,
            building_value FLOAT,
            misc_value FLOAT,

            -- Exemptions
            homestead_exemption FLOAT,
            widow_exemption FLOAT,
            disability_exemption FLOAT,
            veteran_exemption FLOAT,
            senior_exemption FLOAT,
            other_exemptions FLOAT,

            -- Tax information
            millage_rate FLOAT,
            tax_amount FLOAT,

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            CONSTRAINT unique_nav_parcel_county_year UNIQUE (parcel_id, county, year)
        );

        CREATE INDEX IF NOT EXISTS idx_nav_parcel_id ON nav_assessments(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_nav_county ON nav_assessments(county);
        CREATE INDEX IF NOT EXISTS idx_nav_year ON nav_assessments(year);
        CREATE INDEX IF NOT EXISTS idx_nav_just_value ON nav_assessments(just_value);

        ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "public_read_nav" ON nav_assessments
            FOR SELECT USING (true);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created nav_assessments table")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating nav_assessments: {e}")
            return False

    def create_sdf_sales_table(self):
        """Create SDF sales history table"""
        sql = """
        CREATE TABLE IF NOT EXISTS sdf_sales (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) NOT NULL,
            county VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL DEFAULT 2025,

            -- Sale information
            sale_date DATE,
            sale_price FLOAT,
            sale_type VARCHAR(10),
            sale_qualification VARCHAR(10),
            deed_type VARCHAR(50),

            -- Parties
            grantor VARCHAR(255),  -- Seller
            grantee VARCHAR(255),  -- Buyer

            -- Document information
            doc_number VARCHAR(50),
            doc_stamps FLOAT,
            book_page VARCHAR(50),

            -- Validation
            verified_sale BOOLEAN DEFAULT FALSE,
            arms_length BOOLEAN,

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),

            CONSTRAINT unique_sale UNIQUE (parcel_id, county, sale_date, doc_number)
        );

        CREATE INDEX IF NOT EXISTS idx_sdf_parcel_id ON sdf_sales(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_sdf_county ON sdf_sales(county);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_date ON sdf_sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_price ON sdf_sales(sale_price);

        ALTER TABLE sdf_sales ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "public_read_sdf" ON sdf_sales
            FOR SELECT USING (true);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created sdf_sales table")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating sdf_sales: {e}")
            return False

    def create_nap_characteristics_table(self):
        """Create NAP property characteristics table"""
        sql = """
        CREATE TABLE IF NOT EXISTS nap_characteristics (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) NOT NULL,
            county VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL DEFAULT 2025,

            -- Land information
            land_use_code VARCHAR(10),
            land_use_desc VARCHAR(255),
            zoning VARCHAR(50),
            land_sqft FLOAT,
            lot_size FLOAT,

            -- Building information
            year_built INTEGER,
            effective_year_built INTEGER,
            building_sqft FLOAT,
            living_area FLOAT,
            adjusted_area FLOAT,

            -- Structure details
            stories FLOAT,
            bedrooms INTEGER,
            bathrooms FLOAT,
            half_bathrooms INTEGER,

            -- Construction
            construction_type VARCHAR(50),
            roof_type VARCHAR(50),
            roof_material VARCHAR(50),
            exterior_wall VARCHAR(50),
            foundation_type VARCHAR(50),

            -- Features
            pool BOOLEAN DEFAULT FALSE,
            garage_spaces INTEGER,
            fireplace_count INTEGER,

            -- Condition
            condition_rating VARCHAR(20),
            quality_rating VARCHAR(20),

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            CONSTRAINT unique_nap_parcel_county_year UNIQUE (parcel_id, county, year)
        );

        CREATE INDEX IF NOT EXISTS idx_nap_parcel_id ON nap_characteristics(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_nap_county ON nap_characteristics(county);
        CREATE INDEX IF NOT EXISTS idx_nap_year_built ON nap_characteristics(year_built);
        CREATE INDEX IF NOT EXISTS idx_nap_building_sqft ON nap_characteristics(building_sqft);

        ALTER TABLE nap_characteristics ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "public_read_nap" ON nap_characteristics
            FOR SELECT USING (true);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created nap_characteristics table")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating nap_characteristics: {e}")
            return False

    def create_tax_deed_auctions_table(self):
        """Create tax deed auctions table"""
        sql = """
        CREATE TABLE IF NOT EXISTS tax_deed_auctions (
            id BIGSERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            county VARCHAR(50),

            -- Auction information
            auction_date DATE,
            auction_number VARCHAR(50),
            auction_status VARCHAR(50),

            -- Financial details
            minimum_bid FLOAT,
            winning_bid FLOAT,
            deposit_amount FLOAT,

            -- Property details
            property_address VARCHAR(255),
            assessed_value FLOAT,

            -- Certificate info
            certificate_number VARCHAR(50),
            certificate_year INTEGER,
            certificate_face_value FLOAT,

            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_td_parcel_id ON tax_deed_auctions(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_td_auction_date ON tax_deed_auctions(auction_date);
        CREATE INDEX IF NOT EXISTS idx_td_county ON tax_deed_auctions(county);

        ALTER TABLE tax_deed_auctions ENABLE ROW LEVEL SECURITY;

        CREATE POLICY "public_read_tax_deeds" ON tax_deed_auctions
            FOR SELECT USING (true);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created tax_deed_auctions table")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating tax_deed_auctions: {e}")
            return False

    def create_monitoring_tables(self):
        """Create tables for monitoring and data quality"""
        sql = """
        -- Data load monitoring
        CREATE TABLE IF NOT EXISTS data_load_monitor (
            id BIGSERIAL PRIMARY KEY,
            county VARCHAR(50),
            file_type VARCHAR(10),  -- NAL, NAP, NAV, SDF
            file_name VARCHAR(255),
            file_size BIGINT,
            record_count INTEGER,
            load_status VARCHAR(50),
            load_started TIMESTAMP,
            load_completed TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- County coverage statistics
        CREATE TABLE IF NOT EXISTS county_statistics (
            id BIGSERIAL PRIMARY KEY,
            county VARCHAR(50) UNIQUE,
            total_parcels INTEGER,
            last_update DATE,
            nal_records INTEGER,
            nap_records INTEGER,
            nav_records INTEGER,
            sdf_records INTEGER,
            data_quality_score FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_monitor_county ON data_load_monitor(county);
        CREATE INDEX IF NOT EXISTS idx_monitor_status ON data_load_monitor(load_status);
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Created monitoring tables")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating monitoring tables: {e}")
            return False

    def apply_performance_optimizations(self):
        """Apply database optimizations for bulk loading"""
        sql = """
        -- Disable statement timeout for bulk operations
        ALTER DATABASE postgres SET statement_timeout = 0;

        -- Increase work memory for sorting
        SET work_mem = '256MB';

        -- Optimize for bulk inserts
        SET synchronous_commit = OFF;
        SET maintenance_work_mem = '1GB';

        -- Update table statistics
        ANALYZE florida_parcels;
        ANALYZE nav_assessments;
        ANALYZE sdf_sales;
        ANALYZE nap_characteristics;
        """

        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            logger.info("✅ Applied performance optimizations")
            return True
        except Exception as e:
            logger.error(f"❌ Error applying optimizations: {e}")
            return False

    def verify_tables_created(self):
        """Verify all tables were created successfully"""
        tables_to_check = [
            'florida_parcels',
            'nav_assessments',
            'sdf_sales',
            'nap_characteristics',
            'tax_deed_auctions',
            'data_load_monitor',
            'county_statistics'
        ]

        results = {}
        for table in tables_to_check:
            try:
                # Try to query the table
                response = self.supabase.table(table).select("*").limit(1).execute()
                results[table] = "✅ Created"
            except Exception as e:
                if 'does not exist' in str(e):
                    results[table] = "❌ Not created"
                else:
                    results[table] = f"⚠️ Error: {str(e)[:50]}"

        return results

    def create_all_tables(self):
        """Create all Property Appraiser tables"""
        logger.info("=" * 60)
        logger.info("CREATING PROPERTY APPRAISER INFRASTRUCTURE")
        logger.info("=" * 60)

        # Create tables in order
        steps = [
            ("Florida Parcels (NAL)", self.create_florida_parcels_table),
            ("NAV Assessments", self.create_nav_assessments_table),
            ("SDF Sales", self.create_sdf_sales_table),
            ("NAP Characteristics", self.create_nap_characteristics_table),
            ("Tax Deed Auctions", self.create_tax_deed_auctions_table),
            ("Monitoring Tables", self.create_monitoring_tables),
            ("Performance Optimizations", self.apply_performance_optimizations)
        ]

        success_count = 0
        for step_name, func in steps:
            logger.info(f"\nCreating {step_name}...")
            if func():
                success_count += 1
            else:
                logger.warning(f"Failed to create {step_name}")

        # Verify all tables
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION RESULTS")
        logger.info("=" * 60)

        results = self.verify_tables_created()
        for table, status in results.items():
            logger.info(f"{table}: {status}")

        logger.info("\n" + "=" * 60)
        logger.info(f"Setup complete: {success_count}/{len(steps)} steps successful")
        logger.info("=" * 60)

        return success_count == len(steps)

def main():
    """Main execution function"""
    setup = PropertyAppraiserSetup()

    # Create all tables
    success = setup.create_all_tables()

    if success:
        logger.info("\n✅ Property Appraiser infrastructure created successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Run the data pipeline to load Florida Revenue data")
        logger.info("2. Set up monitoring for daily updates")
        logger.info("3. Create API endpoints for data access")
    else:
        logger.error("\n❌ Some tables failed to create. Check the logs above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())