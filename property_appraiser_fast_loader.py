#!/usr/bin/env python3
"""
Fast COPY-based loader for Florida Property Appraiser data
Uses PostgreSQL COPY for maximum performance
"""

import os
import csv
import psycopg2
from psycopg2 import sql
from pathlib import Path
from datetime import datetime
import logging
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FastPropertyLoader:
    """High-performance loader using COPY command"""
    
    # County mapping
    COUNTY_CODES = {
        "11": "ALACHUA", "12": "BAKER", "13": "BAY", "14": "BRADFORD",
        "15": "BREVARD", "16": "BROWARD", "17": "CALHOUN", "18": "CHARLOTTE",
        "19": "CITRUS", "20": "CLAY", "21": "COLLIER", "22": "COLUMBIA",
        "23": "DADE", "24": "DESOTO", "25": "DIXIE", "26": "DUVAL",
        "27": "ESCAMBIA", "28": "FLAGLER", "29": "FRANKLIN", "30": "GADSDEN",
        "31": "GILCHRIST", "32": "GLADES", "33": "GULF", "34": "HAMILTON",
        "35": "HARDEE", "36": "HENDRY", "37": "HERNANDO", "38": "HIGHLANDS",
        "39": "HILLSBOROUGH", "40": "HOLMES", "41": "INDIAN RIVER", "42": "JACKSON",
        "43": "JEFFERSON", "44": "LAFAYETTE", "45": "LAKE", "46": "LEE",
        "47": "LEON", "48": "LEVY", "49": "LIBERTY", "50": "MADISON",
        "51": "MANATEE", "52": "MARION", "53": "MARTIN", "54": "MONROE",
        "55": "NASSAU", "56": "OKALOOSA", "57": "OKEECHOBEE", "58": "ORANGE",
        "59": "OSCEOLA", "60": "PALM BEACH", "61": "PASCO", "62": "PINELLAS",
        "63": "POLK", "64": "PUTNAM", "65": "SANTA ROSA", "66": "SARASOTA",
        "67": "SEMINOLE", "68": "ST. JOHNS", "69": "ST. LUCIE", "70": "SUMTER",
        "71": "SUWANNEE", "72": "TAYLOR", "73": "UNION", "74": "VOLUSIA",
        "75": "WAKULLA", "76": "WALTON", "77": "WASHINGTON"
    }
    
    def __init__(self):
        # Use pooler connection with explicit search path
        self.conn = psycopg2.connect(
            host='aws-1-us-east-1.pooler.supabase.com',
            port=5432,
            database='postgres',
            user='postgres.pmispwtdngkcmsrsjwbp',
            password='West@Boca613!',
            sslmode='require',
            options='-c search_path=public'
        )
        self.cur = self.conn.cursor()
        
        # Set search path and verify tables exist
        self.cur.execute("SET search_path TO public")
        self.cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'property_assessments'
        """)
        if self.cur.fetchone()[0] > 0:
            logger.info("Connected and property_assessments table found!")
        else:
            logger.error("Table property_assessments not found!")
            raise Exception("Required tables not found")
        
        self.data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
        self.stats = {
            'total_records': 0,
            'counties_processed': 0,
            'errors': 0
        }
    
    def load_nal_with_copy(self, csv_path: Path, county_code: str, county_name: str):
        """Load NAL file using COPY for maximum speed"""
        logger.info(f"  Loading {csv_path.name} using COPY...")
        
        try:
            # Read CSV and transform data
            buffer = io.StringIO()
            csv_writer = csv.writer(buffer)
            
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                row_count = 0
                
                for row in reader:
                    # Extract and transform key fields
                    csv_writer.writerow([
                        row.get('PARCEL_ID', '').strip(),  # parcel_id
                        county_code,  # county_code
                        county_name,  # county_name
                        row.get('OWN_NAME', '').strip()[:255],  # owner_name
                        row.get('OWN_ADDR1', '').strip()[:255],  # owner_address
                        row.get('OWN_CITY', '').strip()[:100],  # owner_city
                        row.get('OWN_STATE', 'FL')[:2],  # owner_state
                        row.get('OWN_ZIPCD', '').strip()[:10],  # owner_zip
                        row.get('PHY_ADDR1', '').strip()[:255],  # property_address
                        row.get('PHY_CITY', '').strip()[:100],  # property_city
                        row.get('PHY_ZIPCD', '').strip()[:10],  # property_zip
                        row.get('DOR_UC', '').strip()[:20],  # property_use_code
                        row.get('DISTR_CD', '').strip()[:50],  # tax_district
                        '',  # subdivision (not in this format)
                        self.safe_numeric(row.get('JV', 0)),  # just_value
                        self.safe_numeric(row.get('AV_SD', 0)),  # assessed_value
                        self.safe_numeric(row.get('TV_SD', 0)),  # taxable_value
                        self.safe_numeric(row.get('LND_VAL', 0)),  # land_value
                        0,  # building_value (calculate from JV - LND_VAL)
                        self.safe_int(row.get('LND_SQFOOT', 0)),  # total_sq_ft
                        self.safe_int(row.get('TOT_LVG_AREA', 0)),  # living_area
                        self.safe_int(row.get('ACT_YR_BLT', 0)),  # year_built
                        self.safe_int(row.get('NO_RES_UNTS', 0)),  # bedrooms (using units as proxy)
                        0,  # bathrooms (not in this format)
                        False,  # pool (would need special features)
                        2025  # tax_year
                    ])
                    row_count += 1
            
            # Reset buffer position
            buffer.seek(0)
            
            # Use COPY to load data
            self.cur.copy_expert(
                """
                COPY property_assessments (
                    parcel_id, county_code, county_name, owner_name, owner_address,
                    owner_city, owner_state, owner_zip, property_address, property_city,
                    property_zip, property_use_code, tax_district, subdivision,
                    just_value, assessed_value, taxable_value, land_value, building_value,
                    total_sq_ft, living_area, year_built, bedrooms, bathrooms, pool, tax_year
                ) FROM STDIN WITH (FORMAT CSV)
                """,
                buffer
            )
            
            self.conn.commit()
            self.stats['total_records'] += row_count
            logger.info(f"    ✅ Loaded {row_count:,} records via COPY")
            
        except Exception as e:
            logger.error(f"    ❌ Error loading {csv_path.name}: {e}")
            self.conn.rollback()
            self.stats['errors'] += 1
    
    def safe_numeric(self, value):
        """Safely convert to numeric"""
        try:
            return float(value) if value else 0
        except:
            return 0
    
    def safe_int(self, value):
        """Safely convert to int"""
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def process_all_counties(self):
        """Process all county NAL files"""
        logger.info("="*70)
        logger.info("FAST PROPERTY DATA LOADER (PostgreSQL COPY)")
        logger.info("="*70)
        
        # Find all NAL files
        nal_files = list(self.data_path.glob("*/NAL/NAL*.csv"))
        logger.info(f"Found {len(nal_files)} NAL files to process")
        
        for nal_file in nal_files[:5]:  # Process first 5 for testing
            # Extract county code from filename (NAL16P202501.csv -> 16)
            filename = nal_file.name
            county_code = filename[3:5]  # Characters 4-5
            county_name = self.COUNTY_CODES.get(county_code, "UNKNOWN")
            
            logger.info(f"\nProcessing {county_name} (Code: {county_code})")
            self.load_nal_with_copy(nal_file, county_code, county_name)
            self.stats['counties_processed'] += 1
        
        # Final report
        logger.info("\n" + "="*70)
        logger.info("LOAD COMPLETE")
        logger.info(f"Counties Processed: {self.stats['counties_processed']}")
        logger.info(f"Total Records: {self.stats['total_records']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*70)
        
        # Close connection
        self.cur.close()
        self.conn.close()
    
    def verify_load(self):
        """Quick verification query"""
        self.cur.execute("""
            SELECT county_name, COUNT(*) as records
            FROM property_assessments
            GROUP BY county_name
            ORDER BY records DESC
            LIMIT 10
        """)
        
        logger.info("\nTop counties by record count:")
        for county, count in self.cur.fetchall():
            logger.info(f"  {county}: {count:,}")

if __name__ == "__main__":
    loader = FastPropertyLoader()
    loader.process_all_counties()
    loader.verify_load()