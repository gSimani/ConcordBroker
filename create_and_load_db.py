#!/usr/bin/env python3
"""
Automated script to create tables and load data into Supabase
This will get your database ready for localhost immediately
"""

import os
import sys
import pandas as pd
import psycopg2
from urllib.parse import urlparse
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.new' if os.path.exists('.env.new') else '.env')

# Add the api directory to path
sys.path.append(str(Path(__file__).parent / 'apps' / 'api'))

def get_db_connection():
    """Get direct PostgreSQL connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment")
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    # Handle special characters in password
    password = parsed.password
    if password:
        password = password.replace('%40', '@')
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        user=parsed.username,
        password=password,
        sslmode='require'
    )
    return conn

def create_tables():
    """Create all necessary tables"""
    logger.info("Creating database tables...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create main parcels table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS florida_parcels (
                id BIGSERIAL PRIMARY KEY,
                parcel_id VARCHAR(50),
                county VARCHAR(50),
                year INTEGER,
                owner_name VARCHAR(255),
                owner_addr1 VARCHAR(255),
                owner_city VARCHAR(100),
                owner_state VARCHAR(2),
                owner_zip VARCHAR(10),
                phy_addr1 VARCHAR(255),
                phy_city VARCHAR(100),
                phy_state VARCHAR(2) DEFAULT 'FL',
                phy_zipcd VARCHAR(10),
                just_value FLOAT,
                assessed_value FLOAT,
                taxable_value FLOAT,
                land_value FLOAT,
                building_value FLOAT,
                year_built INTEGER,
                total_living_area FLOAT,
                bedrooms INTEGER,
                bathrooms FLOAT,
                land_sqft FLOAT,
                land_acres FLOAT,
                sale_date TIMESTAMP,
                sale_price FLOAT,
                property_use VARCHAR(10),
                property_use_desc VARCHAR(255),
                import_date TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_parcel_id ON florida_parcels(parcel_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_county ON florida_parcels(county)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_owner ON florida_parcels(owner_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_parcels_address ON florida_parcels(phy_addr1)")
        
        # Create properties view for API
        cur.execute("""
            CREATE OR REPLACE VIEW properties AS
            SELECT 
                id,
                parcel_id,
                owner_name,
                phy_addr1 as address,
                phy_city as city,
                phy_zipcd as zip_code,
                just_value,
                assessed_value,
                taxable_value,
                year_built,
                total_living_area as square_feet,
                bedrooms,
                bathrooms,
                sale_date,
                sale_price,
                property_use
            FROM florida_parcels
        """)
        
        conn.commit()
        logger.info("✅ Tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def load_parcel_data(limit=1000):
    """Load parcel data from CSV"""
    logger.info(f"Loading parcel data (limit: {limit})...")
    
    nap_file = Path('NAP16P202501.csv')
    if not nap_file.exists():
        logger.error(f"NAP file not found: {nap_file}")
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Read CSV
        logger.info("Reading NAP file...")
        nap_df = pd.read_csv(nap_file, low_memory=False, nrows=limit)
        logger.info(f"Loaded {len(nap_df)} records from CSV")
        
        # Clear existing data
        cur.execute("TRUNCATE TABLE florida_parcels")
        
        # Insert data
        inserted = 0
        for _, row in nap_df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO florida_parcels (
                        parcel_id, county, year,
                        owner_name, owner_addr1, owner_city, owner_state, owner_zip,
                        phy_addr1, phy_city, phy_zipcd,
                        just_value, assessed_value, taxable_value,
                        land_value, building_value,
                        year_built, total_living_area,
                        land_sqft, property_use
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    str(row.get('PARCEL_ID', '')),
                    'Broward',
                    2025,
                    str(row.get('OWN_NAME', ''))[:255],
                    str(row.get('OWN_ADDR1', ''))[:255],
                    str(row.get('OWN_CITY', ''))[:100],
                    str(row.get('OWN_STATE', ''))[:2],
                    str(row.get('OWN_ZIPCD', ''))[:10],
                    str(row.get('PHY_ADDR1', ''))[:255],
                    str(row.get('PHY_CITY', ''))[:100],
                    str(row.get('PHY_ZIPCD', ''))[:10],
                    float(row.get('JV', 0)) if pd.notna(row.get('JV')) else None,
                    float(row.get('AV', 0)) if pd.notna(row.get('AV')) else None,
                    float(row.get('TV', 0)) if pd.notna(row.get('TV')) else None,
                    float(row.get('LND_VAL', 0)) if pd.notna(row.get('LND_VAL')) else None,
                    float(row.get('BLDG_VAL', 0)) if pd.notna(row.get('BLDG_VAL')) else None,
                    int(row.get('YR_BLT', 0)) if pd.notna(row.get('YR_BLT')) and row.get('YR_BLT') > 0 else None,
                    float(row.get('TOT_LVG_AREA', 0)) if pd.notna(row.get('TOT_LVG_AREA')) else None,
                    float(row.get('LND_SQFOOT', 0)) if pd.notna(row.get('LND_SQFOOT')) else None,
                    str(row.get('DOR_UC', ''))[:10]
                ))
                inserted += 1
                
                if inserted % 100 == 0:
                    logger.info(f"  Inserted {inserted} records...")
                    conn.commit()
                    
            except Exception as e:
                logger.warning(f"Failed to insert record: {e}")
                continue
        
        conn.commit()
        logger.info(f"✅ Successfully loaded {inserted} parcels")
        return True
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def verify_data():
    """Verify data was loaded"""
    logger.info("Verifying data...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Count records
        cur.execute("SELECT COUNT(*) FROM florida_parcels")
        count = cur.fetchone()[0]
        logger.info(f"Total parcels in database: {count}")
        
        # Get sample
        cur.execute("""
            SELECT parcel_id, owner_name, phy_addr1, just_value 
            FROM florida_parcels 
            LIMIT 5
        """)
        
        logger.info("Sample records:")
        for row in cur.fetchall():
            logger.info(f"  {row[0]}: {row[1]} - {row[2]} (${row[3]:,.0f})" if row[3] else f"  {row[0]}: {row[1]} - {row[2]}")
        
        return count > 0
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    print("""
    ========================================
    Quick Database Setup for Localhost
    ========================================
    """)
    
    # Check environment
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL not found in environment")
        print("Please ensure your .env file is configured")
        return
    
    print("This will:")
    print("1. Create database tables")
    print("2. Load 1000 sample records")
    print("3. Make data available on localhost")
    print()
    
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled")
        return
    
    # Run setup
    print("\nStep 1: Creating tables...")
    if create_tables():
        print("✅ Tables created")
    else:
        print("❌ Failed to create tables")
        return
    
    print("\nStep 2: Loading data...")
    if load_parcel_data(limit=1000):
        print("✅ Data loaded")
    else:
        print("❌ Failed to load data")
        return
    
    print("\nStep 3: Verifying...")
    if verify_data():
        print("✅ Data verified")
    else:
        print("❌ Verification failed")
        return
    
    print("""
    ========================================
    ✅ Database Ready for Localhost!
    ========================================
    
    Next steps:
    1. Start the API: cd apps/api && python -m uvicorn main:app --reload
    2. Start the web: cd apps/web && npm run dev
    3. Open: http://localhost:5173
    
    Or run: .\\start-localhost.ps1
    """)

if __name__ == "__main__":
    main()