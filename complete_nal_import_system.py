"""
Complete NAL Import System
Production-ready system to import all 165 NAL fields into optimized Supabase structure
"""

import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
import json
from datetime import datetime
import time
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class NALImportSystem:
    def __init__(self):
        self.url = os.getenv('VITE_SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase = create_client(self.url, self.key)
        self.stats = {
            'processed': 0,
            'successful': 0,
            'errors': 0,
            'start_time': None,
            'tables_created': False
        }
    
    def create_optimized_tables(self):
        """Create the optimized 7-table structure in Supabase"""
        logger.info("Creating optimized NAL database tables...")
        
        # Since Python client can't execute raw SQL, provide the SQL for manual execution
        schema_sql = """
-- Execute this SQL in your Supabase SQL Editor:

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Core properties table
CREATE TABLE IF NOT EXISTS florida_properties_core (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    co_no INTEGER,
    assessment_year INTEGER DEFAULT 2025,
    owner_name TEXT,
    owner_state VARCHAR(50),
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
    tax_authority_code VARCHAR(10),
    market_area VARCHAR(10),
    township VARCHAR(10),
    range_val VARCHAR(10),
    section_val VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Property valuations
CREATE TABLE IF NOT EXISTS property_valuations (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    just_value DECIMAL(15,2),
    just_value_change DECIMAL(15,2),
    assessed_value_sd DECIMAL(15,2),
    assessed_value_nsd DECIMAL(15,2),
    taxable_value_sd DECIMAL(15,2),
    taxable_value_nsd DECIMAL(15,2),
    just_value_homestead DECIMAL(15,2),
    assessed_value_homestead DECIMAL(15,2),
    just_value_non_homestead_res DECIMAL(15,2),
    assessed_value_non_homestead_res DECIMAL(15,2),
    just_value_conservation_land DECIMAL(15,2),
    assessed_value_conservation_land DECIMAL(15,2),
    land_value DECIMAL(15,2),
    new_construction_value DECIMAL(15,2),
    deleted_value DECIMAL(15,2),
    special_features_value DECIMAL(15,2),
    year_value_transferred INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Property exemptions (JSONB for flexibility)
CREATE TABLE IF NOT EXISTS property_exemptions (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    homestead_exemption DECIMAL(15,2),
    senior_exemption DECIMAL(15,2),
    disability_exemption DECIMAL(15,2),
    veteran_exemption DECIMAL(15,2),
    widow_exemption DECIMAL(15,2),
    all_exemptions JSONB,
    previous_homestead_owner VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Property characteristics
CREATE TABLE IF NOT EXISTS property_characteristics (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    actual_year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area INTEGER,
    land_units BIGINT,
    land_units_code VARCHAR(5),
    number_of_buildings INTEGER,
    number_of_residential_units INTEGER,
    improvement_quality VARCHAR(10),
    construction_class VARCHAR(10),
    public_land_code VARCHAR(5),
    census_block VARCHAR(20),
    inspection_date VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Sales history enhanced
CREATE TABLE IF NOT EXISTS property_sales_enhanced (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    sale_date_1 DATE,
    sale_price_1 DECIMAL(15,2),
    sale_year_1 INTEGER,
    sale_month_1 INTEGER,
    qualification_code_1 VARCHAR(10),
    validity_code_1 VARCHAR(5),
    clerk_number_1 BIGINT,
    multi_parcel_sale_1 VARCHAR(5),
    sale_date_2 DATE,
    sale_price_2 DECIMAL(15,2),
    sale_year_2 INTEGER,
    sale_month_2 INTEGER,
    qualification_code_2 VARCHAR(10),
    validity_code_2 VARCHAR(5),
    clerk_number_2 BIGINT,
    multi_parcel_sale_2 VARCHAR(5),
    latest_sale_date DATE,
    latest_sale_price DECIMAL(15,2),
    price_change_percent DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Property addresses
CREATE TABLE IF NOT EXISTS property_addresses (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    owner_address_1 TEXT,
    owner_address_2 TEXT,
    owner_city VARCHAR(100),
    owner_zipcode VARCHAR(10),
    fiduciary_name VARCHAR(255),
    fiduciary_address_1 TEXT,
    fiduciary_address_2 TEXT,
    fiduciary_city VARCHAR(100),
    fiduciary_zipcode VARCHAR(10),
    fiduciary_state VARCHAR(50),
    fiduciary_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Administrative data
CREATE TABLE IF NOT EXISTS property_admin_data (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) REFERENCES florida_properties_core(parcel_id),
    file_type VARCHAR(5),
    group_number DECIMAL(10,2),
    base_street INTEGER,
    active_street DECIMAL(8,2),
    parcel_split DECIMAL(10,2),
    special_assessment_code VARCHAR(10),
    district_code VARCHAR(10),
    district_year INTEGER,
    legal_description TEXT,
    sequence_number INTEGER,
    rs_id VARCHAR(10),
    mp_id VARCHAR(20),
    state_parcel_id VARCHAR(50),
    special_circumstance_year INTEGER,
    special_circumstance_text TEXT,
    application_status VARCHAR(10),
    county_application_status VARCHAR(10),
    assessment_transfer_flag VARCHAR(5),
    assessment_difference_transfer DECIMAL(15,2),
    alternate_key VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_properties_core_parcel_id ON florida_properties_core(parcel_id);
CREATE INDEX IF NOT EXISTS idx_properties_core_owner_name ON florida_properties_core USING GIN (owner_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_address ON florida_properties_core USING GIN (physical_address gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_core_city ON florida_properties_core(physical_city);
CREATE INDEX IF NOT EXISTS idx_properties_core_just_value ON florida_properties_core(just_value) WHERE just_value > 0;
CREATE INDEX IF NOT EXISTS idx_properties_core_use_code ON florida_properties_core(dor_use_code);
CREATE INDEX IF NOT EXISTS idx_properties_core_neighborhood ON florida_properties_core(neighborhood_code);

-- Valuation indexes
CREATE INDEX IF NOT EXISTS idx_valuations_parcel_id ON property_valuations(parcel_id);
CREATE INDEX IF NOT EXISTS idx_valuations_just_value ON property_valuations(just_value) WHERE just_value > 0;

-- Sales indexes
CREATE INDEX IF NOT EXISTS idx_sales_parcel_id ON property_sales_enhanced(parcel_id);
CREATE INDEX IF NOT EXISTS idx_sales_latest_date ON property_sales_enhanced(latest_sale_date) WHERE latest_sale_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sales_latest_price ON property_sales_enhanced(latest_sale_price) WHERE latest_sale_price > 0;

-- Exemption indexes
CREATE INDEX IF NOT EXISTS idx_exemptions_parcel_id ON property_exemptions(parcel_id);
CREATE INDEX IF NOT EXISTS idx_exemptions_homestead ON property_exemptions(homestead_exemption) WHERE homestead_exemption > 0;

-- Enable RLS
ALTER TABLE florida_properties_core ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_exemptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_characteristics ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_enhanced ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_admin_data ENABLE ROW LEVEL SECURITY;

-- Public read policies
CREATE POLICY IF NOT EXISTS "Public read access" ON florida_properties_core FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_valuations FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_exemptions FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_characteristics FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_sales_enhanced FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_addresses FOR SELECT USING (true);
CREATE POLICY IF NOT EXISTS "Public read access" ON property_admin_data FOR SELECT USING (true);
"""
        
        # Save schema to file for manual execution
        with open('supabase_nal_schema.sql', 'w') as f:
            f.write(schema_sql)
        
        logger.info("Schema SQL saved to 'supabase_nal_schema.sql'")
        logger.info("Please execute this SQL in your Supabase SQL Editor first")
        
        return schema_sql
    
    def map_nal_fields(self, row: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Map NAL fields to appropriate database tables"""
        
        # Helper function to safely convert values
        def safe_decimal(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return float(val)
            except:
                return None
        
        def safe_int(val):
            if pd.isna(val) or val == '' or val is None:
                return None
            try:
                return int(float(val))
            except:
                return None
        
        def safe_str(val):
            if pd.isna(val) or val is None:
                return None
            return str(val).strip() if str(val).strip() else None
        
        # Core properties
        core_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'co_no': safe_int(row.get('CO_NO')),
            'assessment_year': safe_int(row.get('ASMNT_YR', 2025)),
            'owner_name': safe_str(row.get('OWN_NAME')),
            'owner_state': safe_str(row.get('OWN_STATE')),
            'physical_address': safe_str(row.get('PHY_ADDR1')),
            'physical_city': safe_str(row.get('PHY_CITY')),
            'physical_zipcode': safe_str(row.get('PHY_ZIPCD')),
            'just_value': safe_decimal(row.get('JV')),
            'assessed_value_sd': safe_decimal(row.get('AV_SD')),
            'assessed_value_nsd': safe_decimal(row.get('AV_NSD')),
            'taxable_value_sd': safe_decimal(row.get('TV_SD')),
            'taxable_value_nsd': safe_decimal(row.get('TV_NSD')),
            'land_value': safe_decimal(row.get('LND_VAL')),
            'dor_use_code': safe_str(row.get('DOR_UC')),
            'pa_use_code': safe_str(row.get('PA_UC')),
            'neighborhood_code': safe_str(row.get('NBRHD_CD')),
            'land_sqft': safe_int(row.get('LND_SQFOOT')),
            'tax_authority_code': safe_str(row.get('TAX_AUTH_CD')),
            'market_area': safe_str(row.get('MKT_AR')),
            'township': safe_str(row.get('TWN')),
            'range_val': safe_str(row.get('RNG')),
            'section_val': safe_str(row.get('SEC'))
        }
        
        # Valuation data
        valuation_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'just_value': safe_decimal(row.get('JV')),
            'just_value_change': safe_decimal(row.get('JV_CHNG')),
            'assessed_value_sd': safe_decimal(row.get('AV_SD')),
            'assessed_value_nsd': safe_decimal(row.get('AV_NSD')),
            'taxable_value_sd': safe_decimal(row.get('TV_SD')),
            'taxable_value_nsd': safe_decimal(row.get('TV_NSD')),
            'just_value_homestead': safe_decimal(row.get('JV_HMSTD')),
            'assessed_value_homestead': safe_decimal(row.get('AV_HMSTD')),
            'just_value_non_homestead_res': safe_decimal(row.get('JV_NON_HMSTD_RESD')),
            'assessed_value_non_homestead_res': safe_decimal(row.get('AV_NON_HMSTD_RESD')),
            'just_value_conservation_land': safe_decimal(row.get('JV_CONSRV_LND')),
            'assessed_value_conservation_land': safe_decimal(row.get('AV_CONSRV_LND')),
            'land_value': safe_decimal(row.get('LND_VAL')),
            'new_construction_value': safe_decimal(row.get('NCONST_VAL')),
            'deleted_value': safe_decimal(row.get('DEL_VAL')),
            'special_features_value': safe_decimal(row.get('SPEC_FEAT_VAL')),
            'year_value_transferred': safe_int(row.get('YR_VAL_TRNSF'))
        }
        
        # Exemptions (collect all EXMPT fields)
        all_exemptions = {}
        common_exemptions = {
            'homestead_exemption': safe_decimal(row.get('EXMPT_05')),
            'senior_exemption': safe_decimal(row.get('EXMPT_06')),
            'disability_exemption': safe_decimal(row.get('EXMPT_07')),
            'veteran_exemption': safe_decimal(row.get('EXMPT_08')),
            'widow_exemption': safe_decimal(row.get('EXMPT_09'))
        }
        
        for i in range(1, 83):  # EXMPT_01 through EXMPT_82
            field_name = f'EXMPT_{i:02d}'
            if field_name in row:
                val = safe_decimal(row.get(field_name))
                if val and val > 0:
                    all_exemptions[field_name] = val
        
        exemption_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            **common_exemptions,
            'all_exemptions': all_exemptions if all_exemptions else None,
            'previous_homestead_owner': safe_str(row.get('PREV_HMSTD_OWN'))
        }
        
        # Characteristics
        characteristics_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'actual_year_built': safe_int(row.get('ACT_YR_BLT')),
            'effective_year_built': safe_int(row.get('EFF_YR_BLT')),
            'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
            'land_units': safe_int(row.get('NO_LND_UNTS')),
            'land_units_code': safe_str(row.get('LND_UNTS_CD')),
            'number_of_buildings': safe_int(row.get('NO_BULDNG')),
            'number_of_residential_units': safe_int(row.get('NO_RES_UNTS')),
            'improvement_quality': safe_str(row.get('IMP_QUAL')),
            'construction_class': safe_str(row.get('CONST_CLASS')),
            'public_land_code': safe_str(row.get('PUBLIC_LND')),
            'census_block': safe_str(row.get('CENSUS_BK')),
            'inspection_date': safe_str(row.get('DT_LAST_INSPT'))
        }
        
        # Sales data with computed fields
        sale_date_1 = None
        sale_date_2 = None
        latest_sale_date = None
        latest_sale_price = None
        
        try:
            if row.get('SALE_YR1') and row.get('SALE_MO1'):
                year1 = safe_int(row.get('SALE_YR1'))
                month1 = safe_int(row.get('SALE_MO1'))
                if year1 and month1:
                    sale_date_1 = f"{year1}-{month1:02d}-01"
                    latest_sale_date = sale_date_1
                    latest_sale_price = safe_decimal(row.get('SALE_PRC1'))
        except:
            pass
        
        try:
            if row.get('SALE_YR2') and row.get('SALE_MO2'):
                year2 = safe_int(row.get('SALE_YR2'))
                month2 = safe_int(row.get('SALE_MO2'))
                if year2 and month2:
                    sale_date_2 = f"{year2}-{month2:02d}-01"
                    # If sale 2 is more recent, use it as latest
                    if not latest_sale_date or (year2 > safe_int(row.get('SALE_YR1', 0))):
                        latest_sale_date = sale_date_2
                        latest_sale_price = safe_decimal(row.get('SALE_PRC2'))
        except:
            pass
        
        sales_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'sale_date_1': sale_date_1,
            'sale_price_1': safe_decimal(row.get('SALE_PRC1')),
            'sale_year_1': safe_int(row.get('SALE_YR1')),
            'sale_month_1': safe_int(row.get('SALE_MO1')),
            'qualification_code_1': safe_str(row.get('QUAL_CD1')),
            'validity_code_1': safe_str(row.get('VI_CD1')),
            'clerk_number_1': safe_int(row.get('CLERK_NO1')),
            'multi_parcel_sale_1': safe_str(row.get('MULTI_PAR_SAL1')),
            'sale_date_2': sale_date_2,
            'sale_price_2': safe_decimal(row.get('SALE_PRC2')),
            'sale_year_2': safe_int(row.get('SALE_YR2')),
            'sale_month_2': safe_int(row.get('SALE_MO2')),
            'qualification_code_2': safe_str(row.get('QUAL_CD2')),
            'validity_code_2': safe_str(row.get('VI_CD2')),
            'clerk_number_2': safe_int(row.get('CLERK_NO2')),
            'multi_parcel_sale_2': safe_str(row.get('MULTI_PAR_SAL2')),
            'latest_sale_date': latest_sale_date,
            'latest_sale_price': latest_sale_price
        }
        
        # Addresses
        address_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'owner_address_1': safe_str(row.get('OWN_ADDR1')),
            'owner_address_2': safe_str(row.get('OWN_ADDR2')),
            'owner_city': safe_str(row.get('OWN_CITY')),
            'owner_zipcode': safe_str(row.get('OWN_ZIPCD')),
            'fiduciary_name': safe_str(row.get('FIDU_NAME')),
            'fiduciary_address_1': safe_str(row.get('FIDU_ADDR1')),
            'fiduciary_address_2': safe_str(row.get('FIDU_ADDR2')),
            'fiduciary_city': safe_str(row.get('FIDU_CITY')),
            'fiduciary_zipcode': safe_str(row.get('FIDU_ZIPCD')),
            'fiduciary_state': safe_str(row.get('FIDU_STATE')),
            'fiduciary_code': safe_str(row.get('FIDU_CD'))
        }
        
        # Administrative data
        admin_data = {
            'parcel_id': safe_str(row.get('PARCEL_ID')),
            'file_type': safe_str(row.get('FILE_T')),
            'group_number': safe_decimal(row.get('GRP_NO')),
            'base_street': safe_int(row.get('BAS_STRT')),
            'active_street': safe_decimal(row.get('ATV_STRT')),
            'parcel_split': safe_decimal(row.get('PAR_SPLT')),
            'special_assessment_code': safe_str(row.get('SPASS_CD')),
            'district_code': safe_str(row.get('DISTR_CD')),
            'district_year': safe_int(row.get('DISTR_YR')),
            'legal_description': safe_str(row.get('S_LEGAL')),
            'sequence_number': safe_int(row.get('SEQ_NO')),
            'rs_id': safe_str(row.get('RS_ID')),
            'mp_id': safe_str(row.get('MP_ID')),
            'state_parcel_id': safe_str(row.get('STATE_PAR_ID')),
            'special_circumstance_year': safe_int(row.get('SPC_CIR_YR')),
            'special_circumstance_text': safe_str(row.get('SPC_CIR_TXT')),
            'application_status': safe_str(row.get('APP_STAT')),
            'county_application_status': safe_str(row.get('CO_APP_STAT')),
            'assessment_transfer_flag': safe_str(row.get('ASS_TRNSFR_FG')),
            'assessment_difference_transfer': safe_decimal(row.get('ASS_DIF_TRNS')),
            'alternate_key': safe_str(row.get('ALT_KEY'))
        }
        
        return {
            'core': core_data,
            'valuations': valuation_data,
            'exemptions': exemption_data,
            'characteristics': characteristics_data,
            'sales': sales_data,
            'addresses': address_data,
            'admin': admin_data
        }
    
    def import_nal_data(self, csv_file_path: str, batch_size: int = 1000):
        """Import NAL data into the optimized database structure"""
        logger.info(f"Starting NAL import from: {csv_file_path}")
        self.stats['start_time'] = time.time()
        
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"NAL file not found: {csv_file_path}")
        
        # Read CSV in chunks for memory efficiency
        chunk_iter = pd.read_csv(csv_file_path, chunksize=batch_size, low_memory=False)
        
        chunk_num = 0
        total_processed = 0
        
        for chunk in chunk_iter:
            chunk_num += 1
            logger.info(f"Processing chunk {chunk_num} ({len(chunk)} records)...")
            
            # Process each record in the chunk
            core_batch = []
            valuation_batch = []
            exemption_batch = []
            characteristic_batch = []
            sales_batch = []
            address_batch = []
            admin_batch = []
            
            for index, row in chunk.iterrows():
                try:
                    # Map NAL fields to database structure
                    mapped_data = self.map_nal_fields(row.to_dict())
                    
                    # Only add records with valid parcel_id
                    if mapped_data['core']['parcel_id']:
                        core_batch.append(mapped_data['core'])
                        valuation_batch.append(mapped_data['valuations'])
                        exemption_batch.append(mapped_data['exemptions'])
                        characteristic_batch.append(mapped_data['characteristics'])
                        sales_batch.append(mapped_data['sales'])
                        address_batch.append(mapped_data['addresses'])
                        admin_batch.append(mapped_data['admin'])
                    
                    self.stats['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    self.stats['errors'] += 1
            
            # Import batches to database
            try:
                self.import_batches({
                    'florida_properties_core': core_batch,
                    'property_valuations': valuation_batch,
                    'property_exemptions': exemption_batch,
                    'property_characteristics': characteristic_batch,
                    'property_sales_enhanced': sales_batch,
                    'property_addresses': address_batch,
                    'property_admin_data': admin_batch
                })
                
                total_processed += len(core_batch)
                logger.info(f"Successfully imported chunk {chunk_num} - Total: {total_processed} records")
                
            except Exception as e:
                logger.error(f"Error importing chunk {chunk_num}: {e}")
                self.stats['errors'] += len(core_batch)
        
        # Final statistics
        elapsed_time = time.time() - self.stats['start_time']
        logger.info(f"Import completed in {elapsed_time:.2f} seconds")
        logger.info(f"Processed: {self.stats['processed']}, Errors: {self.stats['errors']}")
        
        return self.stats
    
    def import_batches(self, batches: Dict[str, List[Dict]]):
        """Import batches to respective tables"""
        for table_name, batch in batches.items():
            if batch:  # Only import non-empty batches
                try:
                    # Use upsert for conflict resolution
                    response = self.supabase.table(table_name).upsert(batch).execute()
                    self.stats['successful'] += len(batch)
                except Exception as e:
                    logger.error(f"Error inserting to {table_name}: {e}")
                    # Try individual inserts for problematic records
                    for record in batch:
                        try:
                            self.supabase.table(table_name).upsert(record).execute()
                            self.stats['successful'] += 1
                        except Exception as e2:
                            logger.error(f"Error inserting individual record to {table_name}: {e2}")
                            self.stats['errors'] += 1

def main():
    """Main execution function"""
    print("=" * 80)
    print("COMPLETE NAL IMPORT SYSTEM")
    print("=" * 80)
    
    try:
        # Initialize import system
        import_system = NALImportSystem()
        
        # First, create database schema
        print("\n1. CREATING DATABASE SCHEMA:")
        schema_sql = import_system.create_optimized_tables()
        
        # Wait for user confirmation
        input("\nPlease execute the SQL in your Supabase SQL Editor, then press Enter to continue...")
        
        # Start import process
        print("\n2. STARTING NAL DATA IMPORT:")
        nal_file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAL16P202501.csv"
        
        if os.path.exists(nal_file_path):
            print(f"Found NAL file: {nal_file_path}")
            
            # Import with batch processing
            stats = import_system.import_nal_data(nal_file_path, batch_size=500)
            
            print(f"\n3. IMPORT COMPLETE:")
            print(f"   Processed: {stats['processed']} records")
            print(f"   Successful: {stats['successful']} records")
            print(f"   Errors: {stats['errors']} records")
            print(f"   Success Rate: {(stats['successful']/stats['processed']*100):.1f}%")
            
        else:
            print(f"NAL file not found: {nal_file_path}")
            print("Please ensure the NAL CSV file exists at the specified location")
            
    except Exception as e:
        logger.error(f"Import system error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()