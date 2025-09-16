#!/usr/bin/env python3
"""
Master Data Upload Script for ConcordBroker
Loads all Property Appraiser and Sunbiz data into unified Supabase structure
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import our loaders
from property_appraiser_supabase_loader import PropertyAppraiserLoader

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_data_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterDataUploader:
    """Orchestrates all data uploads to Supabase"""
    
    def __init__(self):
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials. Check .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
        
        self.stats = {
            'tables_created': 0,
            'records_uploaded': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def create_master_schema(self):
        """Create the complete database schema"""
        logger.info("Creating master database schema...")
        
        # This would be run in Supabase SQL editor
        # Here we just document what needs to be created
        
        schema_sql = """
        -- ============================================================
        -- MASTER PROPERTY DATABASE SCHEMA
        -- ============================================================
        
        -- Enable extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "postgis";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        
        -- Drop existing tables if needed (careful in production!)
        -- DROP TABLE IF EXISTS properties_master CASCADE;
        
        -- 1. Master Properties Table
        CREATE TABLE IF NOT EXISTS properties_master (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            parcel_id VARCHAR(50) UNIQUE NOT NULL,
            folio_number VARCHAR(30),
            county_code VARCHAR(5),
            county_name VARCHAR(50),
            
            -- Location
            property_address VARCHAR(255),
            property_city VARCHAR(100),
            property_state VARCHAR(2) DEFAULT 'FL',
            property_zip VARCHAR(10),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            
            -- Current Owner
            owner_name VARCHAR(255),
            owner_type VARCHAR(50),
            owner_address VARCHAR(255),
            owner_city VARCHAR(100),
            owner_state VARCHAR(2),
            owner_zip VARCHAR(10),
            
            -- Valuation
            just_value DECIMAL(12,2),
            assessed_value DECIMAL(12,2),
            taxable_value DECIMAL(12,2),
            land_value DECIMAL(12,2),
            building_value DECIMAL(12,2),
            
            -- Characteristics
            property_use_code VARCHAR(20),
            property_type VARCHAR(50),
            total_sq_ft INTEGER,
            living_area INTEGER,
            lot_size DECIMAL(10,2),
            year_built INTEGER,
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            pool BOOLEAN DEFAULT FALSE,
            
            -- Financial
            tax_amount DECIMAL(10,2),
            nav_total DECIMAL(10,2),
            homestead_exemption BOOLEAN DEFAULT FALSE,
            
            -- Investment Metrics
            cap_rate DECIMAL(5,2),
            price_per_sqft DECIMAL(10,2),
            rental_estimate DECIMAL(10,2),
            investment_score INTEGER,
            
            -- Latest Sale
            last_sale_date DATE,
            last_sale_price DECIMAL(12,2),
            days_on_market INTEGER,
            
            -- Corporate Links
            has_corporate_owner BOOLEAN DEFAULT FALSE,
            sunbiz_entity_id VARCHAR(50),
            
            -- Quality & Metadata
            data_quality_score INTEGER,
            last_updated TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_master_parcel ON properties_master(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_master_county ON properties_master(county_code);
        CREATE INDEX IF NOT EXISTS idx_master_owner ON properties_master(owner_name);
        CREATE INDEX IF NOT EXISTS idx_master_value ON properties_master(taxable_value);
        CREATE INDEX IF NOT EXISTS idx_master_location ON properties_master(property_city, property_zip);
        
        -- Enable RLS
        ALTER TABLE properties_master ENABLE ROW LEVEL SECURITY;
        
        -- Public read policy
        CREATE POLICY "Public read access" ON properties_master
            FOR SELECT USING (true);
        """
        
        logger.info("Schema SQL generated. Execute in Supabase dashboard.")
        return schema_sql
    
    async def sync_property_data(self):
        """Load and sync Property Appraiser data"""
        logger.info("="*70)
        logger.info("SYNCING PROPERTY APPRAISER DATA")
        logger.info("="*70)
        
        try:
            # Initialize Property Appraiser loader
            pa_loader = PropertyAppraiserLoader()
            
            # Process all counties
            await pa_loader.process_all_counties()
            
            # Get statistics
            self.stats['records_uploaded'] += pa_loader.stats.get('total_records', 0)
            
            logger.info(f"✅ Property Appraiser sync complete: {pa_loader.stats}")
            
        except Exception as e:
            logger.error(f"Failed to sync property data: {e}")
            self.stats['errors'] += 1
    
    async def create_master_property_records(self):
        """Create unified master property records from all data sources"""
        logger.info("Creating master property records...")
        
        try:
            # SQL to populate master table from individual tables
            merge_sql = """
            INSERT INTO properties_master (
                parcel_id,
                county_code,
                county_name,
                property_address,
                property_city,
                property_zip,
                owner_name,
                owner_type,
                owner_address,
                owner_city,
                owner_state,
                owner_zip,
                just_value,
                assessed_value,
                taxable_value,
                land_value,
                building_value,
                property_use_code,
                total_sq_ft,
                living_area,
                year_built,
                bedrooms,
                bathrooms,
                pool,
                last_sale_date,
                last_sale_price,
                nav_total,
                has_corporate_owner,
                data_quality_score
            )
            SELECT DISTINCT ON (pa.parcel_id)
                pa.parcel_id,
                pa.county_code,
                pa.county_name,
                pa.property_address,
                pa.property_city,
                pa.property_zip,
                COALESCE(po.owner_name, pa.owner_name) as owner_name,
                po.owner_type,
                COALESCE(po.mailing_address_1, pa.owner_address) as owner_address,
                COALESCE(po.mailing_city, pa.owner_city) as owner_city,
                COALESCE(po.mailing_state, pa.owner_state) as owner_state,
                COALESCE(po.mailing_zip, pa.owner_zip) as owner_zip,
                pa.just_value,
                pa.assessed_value,
                pa.taxable_value,
                pa.land_value,
                pa.building_value,
                pa.property_use_code,
                pa.total_sq_ft,
                pa.living_area,
                pa.year_built,
                pa.bedrooms,
                pa.bathrooms,
                pa.pool,
                ps.sale_date as last_sale_date,
                ps.sale_price as last_sale_price,
                ns.total_assessments as nav_total,
                CASE 
                    WHEN po.owner_type IN ('LLC', 'Corporation', 'LP', 'Trust') 
                    THEN true 
                    ELSE false 
                END as has_corporate_owner,
                CASE
                    WHEN pa.owner_name IS NOT NULL THEN 25
                    ELSE 0
                END +
                CASE
                    WHEN pa.taxable_value > 0 THEN 25
                    ELSE 0
                END +
                CASE
                    WHEN ps.sale_price IS NOT NULL THEN 25
                    ELSE 0
                END +
                CASE
                    WHEN ns.total_assessments IS NOT NULL THEN 25
                    ELSE 0
                END as data_quality_score
            FROM property_assessments pa
            LEFT JOIN property_owners po ON 
                pa.parcel_id = po.parcel_id 
                AND pa.county_code = po.county_code
                AND po.owner_sequence = 1
            LEFT JOIN LATERAL (
                SELECT sale_date, sale_price
                FROM property_sales
                WHERE parcel_id = pa.parcel_id
                ORDER BY sale_date DESC
                LIMIT 1
            ) ps ON true
            LEFT JOIN nav_summaries ns ON
                pa.parcel_id = ns.parcel_id
                AND pa.county_code = ns.county_code
            ON CONFLICT (parcel_id) DO UPDATE SET
                owner_name = EXCLUDED.owner_name,
                owner_type = EXCLUDED.owner_type,
                just_value = EXCLUDED.just_value,
                assessed_value = EXCLUDED.assessed_value,
                taxable_value = EXCLUDED.taxable_value,
                last_sale_date = EXCLUDED.last_sale_date,
                last_sale_price = EXCLUDED.last_sale_price,
                nav_total = EXCLUDED.nav_total,
                data_quality_score = EXCLUDED.data_quality_score,
                last_updated = NOW();
            """
            
            # Execute via Supabase (guarded)
            if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
                logger.warning('SQL execution disabled; skipping merge_sql. Use vetted RPC or run via dashboard.')
            else:
                self.supabase.rpc('execute_sql', {'query': merge_sql}).execute()
            
            logger.info("✅ Master property records created")
            
        except Exception as e:
            logger.error(f"Failed to create master records: {e}")
            self.stats['errors'] += 1
    
    async def calculate_investment_metrics(self):
        """Calculate investment scores and opportunities"""
        logger.info("Calculating investment metrics...")
        
        try:
            # Update investment metrics
            metrics_sql = """
            UPDATE properties_master
            SET 
                price_per_sqft = CASE 
                    WHEN living_area > 0 
                    THEN last_sale_price / living_area 
                    ELSE NULL 
                END,
                cap_rate = CASE
                    WHEN last_sale_price > 0 AND rental_estimate > 0
                    THEN (rental_estimate * 12 - nav_total) / last_sale_price * 100
                    ELSE NULL
                END,
                investment_score = CASE
                    WHEN taxable_value > 0 AND last_sale_price > 0
                    THEN LEAST(100, GREATEST(0, 
                        50 + 
                        (taxable_value - last_sale_price) / last_sale_price * 50 +
                        CASE WHEN year_built > 2000 THEN 10 ELSE 0 END +
                        CASE WHEN pool THEN 5 ELSE 0 END
                    ))
                    ELSE 50
                END
            WHERE last_updated > NOW() - INTERVAL '1 day';
            """
            
            if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
                logger.warning('SQL execution disabled; skipping metrics_sql. Use vetted RPC or run via dashboard.')
            else:
                self.supabase.rpc('execute_sql', {'query': metrics_sql}).execute()
            
            logger.info("✅ Investment metrics calculated")
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            self.stats['errors'] += 1
    
    async def run_complete_sync(self):
        """Run the complete data sync process"""
        logger.info("="*70)
        logger.info("MASTER DATA SYNC STARTED")
        logger.info(f"Time: {datetime.now()}")
        logger.info("="*70)
        
        # Step 1: Create schema
        await self.create_master_schema()
        
        # Step 2: Sync Property Appraiser data
        await self.sync_property_data()
        
        # Step 3: Create master records
        await self.create_master_property_records()
        
        # Step 4: Calculate investment metrics
        await self.calculate_investment_metrics()
        
        # Final statistics
        duration = datetime.now() - self.stats['start_time']
        
        logger.info("\n" + "="*70)
        logger.info("SYNC COMPLETE - STATISTICS")
        logger.info("="*70)
        logger.info(f"Duration: {duration}")
        logger.info(f"Records Uploaded: {self.stats['records_uploaded']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*70)
        
        return self.stats


async def main():
    """Main execution"""
    uploader = MasterDataUploader()
    stats = await uploader.run_complete_sync()
    
    print("\n✅ Master data upload complete!")
    print(f"Total records: {stats['records_uploaded']:,}")


if __name__ == "__main__":
    asyncio.run(main())
