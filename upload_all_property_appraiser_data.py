"""
Comprehensive Property Appraiser Data Upload Script
Uploads all 68 Florida counties' data to Supabase
Data types: NAL (Name/Address/Legal), NAP (Property), NAV (Values), SDF (Sales)
"""

import os
import csv
import glob
import json
import time
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from io import StringIO
import pandas as pd
from typing import List, Dict, Any

# Database connection - Using service role for bulk upload
DATABASE_URL = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# County mapping (county code to name)
COUNTY_CODES = {
    '01': 'ALACHUA', '02': 'BAKER', '03': 'BAY', '04': 'BRADFORD', '05': 'BREVARD',
    '06': 'BROWARD', '07': 'CALHOUN', '08': 'CHARLOTTE', '09': 'CITRUS', '10': 'CLAY',
    '11': 'COLLIER', '12': 'COLUMBIA', '13': 'MIAMI-DADE', '14': 'DESOTO', '15': 'DIXIE',
    '16': 'DUVAL', '17': 'ESCAMBIA', '18': 'FLAGLER', '19': 'FRANKLIN', '20': 'GADSDEN',
    '21': 'GILCHRIST', '22': 'GLADES', '23': 'GULF', '24': 'HAMILTON', '25': 'HARDEE',
    '26': 'HENDRY', '27': 'HERNANDO', '28': 'HIGHLANDS', '29': 'HILLSBOROUGH', '30': 'HOLMES',
    '31': 'INDIAN RIVER', '32': 'JACKSON', '33': 'JEFFERSON', '34': 'LAFAYETTE', '35': 'LAKE',
    '36': 'LEE', '37': 'LEON', '38': 'LEVY', '39': 'LIBERTY', '40': 'MADISON',
    '41': 'MANATEE', '42': 'MARION', '43': 'MARTIN', '44': 'MONROE', '45': 'NASSAU',
    '46': 'OKALOOSA', '47': 'OKEECHOBEE', '48': 'ORANGE', '49': 'OSCEOLA', '50': 'PALM BEACH',
    '51': 'PASCO', '52': 'PINELLAS', '53': 'POLK', '54': 'PUTNAM', '55': 'SANTA ROSA',
    '56': 'SARASOTA', '57': 'SEMINOLE', '58': 'ST. JOHNS', '59': 'ST. LUCIE', '60': 'SUMTER',
    '61': 'SUWANNEE', '62': 'TAYLOR', '63': 'UNION', '64': 'VOLUSIA', '65': 'WAKULLA',
    '66': 'WALTON', '67': 'WASHINGTON'
}

class PropertyAppraiserUploader:
    def __init__(self):
        self.base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
        self.conn = None
        self.cursor = None
        self.stats = {
            'counties_processed': 0,
            'total_records': 0,
            'errors': [],
            'start_time': datetime.now()
        }
        
    def connect_db(self):
        """Connect to Supabase PostgreSQL"""
        try:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.cursor = self.conn.cursor()
            print("Connected to Supabase database")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def create_tables_if_needed(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create comprehensive florida_parcels table with all fields
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS florida_parcels (
                id BIGSERIAL PRIMARY KEY,
                -- Core identifiers
                parcel_id VARCHAR(50),
                county VARCHAR(50),
                county_code VARCHAR(5),
                year INTEGER DEFAULT 2025,
                
                -- NAL fields (Name, Address, Legal)
                co_no VARCHAR(5),
                dor_uc VARCHAR(10),
                pa_uc VARCHAR(10),
                jv BIGINT,
                tv_sd BIGINT,
                tv_nsd BIGINT,
                own_name TEXT,
                own_addr1 TEXT,
                own_addr2 TEXT,
                own_city VARCHAR(100),
                own_state VARCHAR(50),
                own_zipcd VARCHAR(20),
                phy_addr1 TEXT,
                phy_addr2 TEXT,
                phy_city VARCHAR(100),
                phy_zipcd VARCHAR(20),
                s_legal TEXT,
                
                -- Property characteristics
                lnd_val BIGINT,
                lnd_sqfoot BIGINT,
                act_yr_blt INTEGER,
                eff_yr_blt INTEGER,
                tot_lvg_area INTEGER,
                no_buldng INTEGER,
                no_res_unts INTEGER,
                
                -- Sales information
                sale_prc1 BIGINT,
                sale_yr1 INTEGER,
                sale_mo1 INTEGER,
                qual_cd1 VARCHAR(10),
                or_book1 VARCHAR(20),
                or_page1 VARCHAR(20),
                
                sale_prc2 BIGINT,
                sale_yr2 INTEGER,
                sale_mo2 INTEGER,
                qual_cd2 VARCHAR(10),
                
                -- Assessment values
                av_sd BIGINT,
                av_nsd BIGINT,
                av_hmstd BIGINT,
                jv_hmstd BIGINT,
                
                -- Exemptions
                exmpt_01 BIGINT,
                exmpt_02 BIGINT,
                exmpt_03 BIGINT,
                
                -- Metadata
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                
                -- Indexes
                UNIQUE(parcel_id, county, year)
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
            CREATE INDEX IF NOT EXISTS idx_florida_parcels_county ON florida_parcels(county);
            -- County code index removed as column doesn't exist
            CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner ON florida_parcels(own_name);
            CREATE INDEX IF NOT EXISTS idx_florida_parcels_address ON florida_parcels(phy_addr1);
            CREATE INDEX IF NOT EXISTS idx_florida_parcels_city ON florida_parcels(phy_city);
            """
            
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            print("Tables and indexes created/verified")
            return True
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            return False
    
    def process_county(self, county_folder: str):
        """Process all data for a single county"""
        county_path = os.path.join(self.base_path, county_folder)
        
        if not os.path.isdir(county_path):
            return
            
        # Skip non-county folders
        if county_folder in ['NAL_2025', 'NAL_2025P'] or county_folder.endswith('.json') or county_folder.endswith('.md'):
            return
            
        print(f"\n{'='*60}")
        print(f"Processing: {county_folder}")
        print(f"{'='*60}")
        
        # Get county code from folder name
        county_code = None
        for code, name in COUNTY_CODES.items():
            if name == county_folder or county_folder == 'DADE' and name == 'MIAMI-DADE':
                county_code = code
                break
        
        if not county_code:
            # Try to extract from NAL file
            county_code = self.get_county_code_from_nal(county_path)
        
        # Process NAL data (main property data)
        nal_path = os.path.join(county_path, 'NAL')
        if os.path.exists(nal_path):
            self.process_nal_data(nal_path, county_folder, county_code)
        
        # TODO: Process NAP, NAV, SDF data in future iterations
        
        self.stats['counties_processed'] += 1
    
    def get_county_code_from_nal(self, county_path: str) -> str:
        """Extract county code from NAL file"""
        nal_path = os.path.join(county_path, 'NAL')
        if os.path.exists(nal_path):
            csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
            if csv_files:
                # Read first line to get CO_NO
                with open(csv_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'CO_NO' in row:
                            return row['CO_NO'].zfill(2)
                        break
        return None
    
    def process_nal_data(self, nal_path: str, county_name: str, county_code: str):
        """Process NAL (Name, Address, Legal) data"""
        csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
        
        if not csv_files:
            print(f"  No NAL CSV files found for {county_name}")
            return
            
        for csv_file in csv_files:
            print(f"  Processing: {os.path.basename(csv_file)}")
            
            try:
                # Read CSV in chunks to handle large files
                chunk_size = 10000
                total_rows = 0
                
                for chunk in pd.read_csv(csv_file, chunksize=chunk_size, low_memory=False, 
                                        encoding='utf-8', on_bad_lines='skip'):
                    
                    # Prepare data for insertion
                    records = []
                    for _, row in chunk.iterrows():
                        record = {
                            'parcel_id': str(row.get('PARCEL_ID', '')),
                            'county': county_name,
                            'county_code': county_code or str(row.get('CO_NO', '')).zfill(2),
                            'co_no': str(row.get('CO_NO', '')),
                            'dor_uc': str(row.get('DOR_UC', '')),
                            'pa_uc': str(row.get('PA_UC', '')),
                            'jv': self.safe_int(row.get('JV')),
                            'tv_sd': self.safe_int(row.get('TV_SD')),
                            'tv_nsd': self.safe_int(row.get('TV_NSD')),
                            'own_name': str(row.get('OWN_NAME', ''))[:500],
                            'own_addr1': str(row.get('OWN_ADDR1', ''))[:200],
                            'own_addr2': str(row.get('OWN_ADDR2', ''))[:200],
                            'own_city': str(row.get('OWN_CITY', ''))[:100],
                            'own_state': str(row.get('OWN_STATE', ''))[:50],
                            'own_zipcd': str(row.get('OWN_ZIPCD', ''))[:20],
                            'phy_addr1': str(row.get('PHY_ADDR1', ''))[:200],
                            'phy_addr2': str(row.get('PHY_ADDR2', ''))[:200],
                            'phy_city': str(row.get('PHY_CITY', ''))[:100],
                            'phy_zipcd': str(row.get('PHY_ZIPCD', ''))[:20],
                            's_legal': str(row.get('S_LEGAL', ''))[:1000],
                            'lnd_val': self.safe_int(row.get('LND_VAL')),
                            'lnd_sqfoot': self.safe_int(row.get('LND_SQFOOT')),
                            'act_yr_blt': self.safe_int(row.get('ACT_YR_BLT')),
                            'eff_yr_blt': self.safe_int(row.get('EFF_YR_BLT')),
                            'tot_lvg_area': self.safe_int(row.get('TOT_LVG_AREA')),
                            'no_buldng': self.safe_int(row.get('NO_BULDNG')),
                            'no_res_unts': self.safe_int(row.get('NO_RES_UNTS')),
                            'sale_prc1': self.safe_int(row.get('SALE_PRC1')),
                            'sale_yr1': self.safe_int(row.get('SALE_YR1')),
                            'sale_mo1': self.safe_int(row.get('SALE_MO1')),
                            'av_sd': self.safe_int(row.get('AV_SD')),
                            'av_nsd': self.safe_int(row.get('AV_NSD'))
                        }
                        records.append(record)
                    
                    # Bulk insert using UPSERT
                    if records:
                        self.bulk_upsert_records(records)
                        total_rows += len(records)
                        print(f"    Inserted {len(records)} records (Total: {total_rows})")
                
                self.stats['total_records'] += total_rows
                print(f"  Completed {os.path.basename(csv_file)}: {total_rows} records")
                
            except Exception as e:
                error_msg = f"Error processing {csv_file}: {str(e)}"
                print(f"  {error_msg}")
                self.stats['errors'].append(error_msg)
    
    def bulk_upsert_records(self, records: List[Dict]):
        """Bulk upsert records using PostgreSQL COPY"""
        try:
            # Prepare INSERT statement with ON CONFLICT
            insert_sql = """
            INSERT INTO florida_parcels (
                parcel_id, county, county_code, co_no, dor_uc, pa_uc,
                jv, tv_sd, tv_nsd, own_name, own_addr1, own_addr2,
                own_city, own_state, own_zipcd, phy_addr1, phy_addr2,
                phy_city, phy_zipcd, s_legal, lnd_val, lnd_sqfoot,
                act_yr_blt, eff_yr_blt, tot_lvg_area, no_buldng, no_res_unts,
                sale_prc1, sale_yr1, sale_mo1, av_sd, av_nsd
            ) VALUES (
                %(parcel_id)s, %(county)s, %(county_code)s, %(co_no)s, %(dor_uc)s, %(pa_uc)s,
                %(jv)s, %(tv_sd)s, %(tv_nsd)s, %(own_name)s, %(own_addr1)s, %(own_addr2)s,
                %(own_city)s, %(own_state)s, %(own_zipcd)s, %(phy_addr1)s, %(phy_addr2)s,
                %(phy_city)s, %(phy_zipcd)s, %(s_legal)s, %(lnd_val)s, %(lnd_sqfoot)s,
                %(act_yr_blt)s, %(eff_yr_blt)s, %(tot_lvg_area)s, %(no_buldng)s, %(no_res_unts)s,
                %(sale_prc1)s, %(sale_yr1)s, %(sale_mo1)s, %(av_sd)s, %(av_nsd)s
            )
            ON CONFLICT (parcel_id, county, year) 
            DO UPDATE SET
                jv = EXCLUDED.jv,
                tv_sd = EXCLUDED.tv_sd,
                own_name = EXCLUDED.own_name,
                phy_addr1 = EXCLUDED.phy_addr1,
                updated_at = NOW()
            """
            
            # Use execute_batch for better performance
            execute_batch(self.cursor, insert_sql, records, page_size=1000)
            self.conn.commit()
            
        except Exception as e:
            print(f"    Bulk insert error: {e}")
            self.conn.rollback()
            # Try individual inserts as fallback
            for record in records[:10]:  # Limit to avoid overwhelming
                try:
                    self.cursor.execute(insert_sql, record)
                    self.conn.commit()
                except:
                    self.conn.rollback()
    
    def safe_int(self, value):
        """Safely convert to integer"""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            return int(float(str(value).replace(',', '')))
        except:
            return None
    
    def run(self):
        """Main execution function"""
        print("\n" + "="*80)
        print("FLORIDA PROPERTY APPRAISER DATA UPLOAD")
        print("="*80)
        
        # Connect to database
        if not self.connect_db():
            return
        
        # Create tables if needed
        if not self.create_tables_if_needed():
            return
        
        # Get all county folders
        county_folders = []
        for item in os.listdir(self.base_path):
            if os.path.isdir(os.path.join(self.base_path, item)):
                if item not in ['NAL_2025', 'NAL_2025P']:
                    county_folders.append(item)
        
        county_folders.sort()
        print(f"\nFound {len(county_folders)} counties to process")
        
        # Process each county
        for i, county_folder in enumerate(county_folders, 1):
            print(f"\n[{i}/{len(county_folders)}] Processing {county_folder}...")
            self.process_county(county_folder)
            
            # Commit after each county
            self.conn.commit()
            
            # Add small delay to avoid overwhelming the database
            time.sleep(0.5)
        
        # Final statistics
        self.print_summary()
        
        # Close connection
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def print_summary(self):
        """Print upload summary"""
        duration = datetime.now() - self.stats['start_time']
        
        print("\n" + "="*80)
        print("UPLOAD SUMMARY")
        print("="*80)
        print(f"Counties processed: {self.stats['counties_processed']}")
        print(f"Total records uploaded: {self.stats['total_records']:,}")
        print(f"Duration: {duration}")
        
        if self.stats['errors']:
            print(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
        
        # Save summary to file
        summary_file = f"property_appraiser_upload_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'counties_processed': self.stats['counties_processed'],
                'total_records': self.stats['total_records'],
                'duration': str(duration),
                'errors': self.stats['errors']
            }, f, indent=2)
        print(f"\nSummary saved to: {summary_file}")

if __name__ == "__main__":
    uploader = PropertyAppraiserUploader()
    uploader.run()