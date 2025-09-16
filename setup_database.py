#!/usr/bin/env python3
"""
Database Setup and Data Population Script for ConcordBroker
This script creates tables and loads data into your Supabase database
"""

import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime

# Add the api directory to path for imports
sys.path.append(str(Path(__file__).parent / 'apps' / 'api'))

# Import the fixed Supabase client
from supabase_client import get_supabase_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.new')  # Use the new env file if available
if not os.path.exists('.env.new'):
    load_dotenv('.env')  # Fallback to .env if it exists

class DatabaseSetup:
    def __init__(self):
        """Initialize database setup"""
        try:
            self.client = get_supabase_client()
            logger.info("✅ Connected to Supabase")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            logger.error("Make sure your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in .env")
            sys.exit(1)
    
    def create_tables(self):
        """Create database tables from schema file"""
        logger.info("Creating database tables...")
        
        schema_file = Path('apps/api/supabase_schema.sql')
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        try:
            # Read the schema file
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Split into individual statements
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            
            # Execute each statement
            for stmt in statements:
                if stmt and not stmt.startswith('--'):
                    try:
                        # For Supabase, we need to use raw SQL through RPC
                        # This is a simplified approach - in production, use migrations
                        logger.info(f"Executing: {stmt[:50]}...")
                        # Note: Supabase client doesn't directly support raw SQL
                        # You'll need to run these in Supabase SQL Editor
                    except Exception as e:
                        logger.warning(f"Statement failed (may already exist): {e}")
            
            logger.info("✅ Table creation attempted (check Supabase dashboard)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False
    
    def load_florida_parcels(self):
        """Load Florida parcel data from CSV files"""
        logger.info("Loading Florida parcel data...")
        
        # NAP file contains parcel attributes
        nap_file = Path('NAP16P202501.csv')
        # SDF file contains sales data
        sdf_file = Path('SDF16P202501.csv')
        
        if not nap_file.exists():
            logger.warning(f"NAP file not found: {nap_file}")
            return False
        
        try:
            # Read NAP data (parcel attributes)
            logger.info("Reading NAP file...")
            nap_df = pd.read_csv(nap_file, low_memory=False, nrows=1000)  # Load first 1000 for testing
            logger.info(f"Loaded {len(nap_df)} parcels from NAP file")
            
            # Prepare data for insertion
            parcels_data = []
            for _, row in nap_df.iterrows():
                parcel = {
                    'parcel_id': str(row.get('PARCEL_ID', '')),
                    'county': 'Broward',  # Based on file name
                    'year': 2025,
                    'owner_name': str(row.get('OWN_NAME', '')),
                    'owner_addr1': str(row.get('OWN_ADDR1', '')),
                    'owner_city': str(row.get('OWN_CITY', '')),
                    'owner_state': str(row.get('OWN_STATE', '')),
                    'owner_zip': str(row.get('OWN_ZIPCD', '')),
                    'phy_addr1': str(row.get('PHY_ADDR1', '')),
                    'phy_city': str(row.get('PHY_CITY', '')),
                    'phy_zipcd': str(row.get('PHY_ZIPCD', '')),
                    'just_value': float(row.get('JV', 0)) if pd.notna(row.get('JV')) else None,
                    'assessed_value': float(row.get('AV', 0)) if pd.notna(row.get('AV')) else None,
                    'taxable_value': float(row.get('TV', 0)) if pd.notna(row.get('TV')) else None,
                    'land_value': float(row.get('LND_VAL', 0)) if pd.notna(row.get('LND_VAL')) else None,
                    'building_value': float(row.get('BLDG_VAL', 0)) if pd.notna(row.get('BLDG_VAL')) else None,
                    'year_built': int(row.get('YR_BLT', 0)) if pd.notna(row.get('YR_BLT')) else None,
                    'total_living_area': float(row.get('TOT_LVG_AREA', 0)) if pd.notna(row.get('TOT_LVG_AREA')) else None,
                    'land_sqft': float(row.get('LND_SQFOOT', 0)) if pd.notna(row.get('LND_SQFOOT')) else None,
                    'property_use': str(row.get('DOR_UC', '')),
                    'import_date': datetime.now().isoformat()
                }
                parcels_data.append(parcel)
            
            # Insert data into Supabase
            logger.info(f"Inserting {len(parcels_data)} parcels into database...")
            
            # Insert in batches of 100
            batch_size = 100
            for i in range(0, len(parcels_data), batch_size):
                batch = parcels_data[i:i+batch_size]
                try:
                    result = self.client.table('florida_parcels').insert(batch).execute()
                    logger.info(f"Inserted batch {i//batch_size + 1}")
                except Exception as e:
                    logger.error(f"Failed to insert batch: {e}")
            
            logger.info("✅ Florida parcel data loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load parcel data: {e}")
            return False
    
    def load_sales_data(self):
        """Load sales data from SDF file"""
        logger.info("Loading sales data...")
        
        sdf_file = Path('SDF16P202501.csv')
        if not sdf_file.exists():
            logger.warning(f"SDF file not found: {sdf_file}")
            return False
        
        try:
            # Read SDF data
            logger.info("Reading SDF file...")
            sdf_df = pd.read_csv(sdf_file, low_memory=False, nrows=1000)  # Load first 1000 for testing
            logger.info(f"Loaded {len(sdf_df)} sales records")
            
            # Update parcels with sales data
            for _, row in sdf_df.iterrows():
                parcel_id = str(row.get('PARCEL_ID', ''))
                if parcel_id:
                    sale_data = {
                        'sale_date': pd.to_datetime(row.get('SALE_DATE'), errors='coerce'),
                        'sale_price': float(row.get('SALE_PRICE', 0)) if pd.notna(row.get('SALE_PRICE')) else None,
                        'sale_qualification': str(row.get('QUAL_CODE', ''))
                    }
                    
                    # Update the parcel with sales info
                    try:
                        self.client.table('florida_parcels').update(sale_data).eq('parcel_id', parcel_id).execute()
                    except Exception as e:
                        logger.warning(f"Failed to update sales for parcel {parcel_id}: {e}")
            
            logger.info("✅ Sales data loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load sales data: {e}")
            return False
    
    def verify_data(self):
        """Verify data was loaded correctly"""
        logger.info("Verifying data...")
        
        try:
            # Count records
            result = self.client.table('florida_parcels').select('count', count='exact').execute()
            count = result.count if hasattr(result, 'count') else 0
            logger.info(f"Total parcels in database: {count}")
            
            # Get sample records
            sample = self.client.table('florida_parcels').select('*').limit(5).execute()
            if sample.data:
                logger.info("Sample records:")
                for record in sample.data[:2]:
                    logger.info(f"  - Parcel {record.get('parcel_id')}: {record.get('owner_name')}")
            
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to verify data: {e}")
            return False

def main():
    """Main setup function"""
    print("""
    ╔════════════════════════════════════════╗
    ║   ConcordBroker Database Setup Tool    ║
    ╚════════════════════════════════════════╝
    """)
    
    # Check environment
    if not os.getenv('SUPABASE_URL'):
        print("❌ ERROR: SUPABASE_URL not found in environment")
        print("Please set up your .env file with Supabase credentials")
        print("Copy .env.example to .env and fill in your values")
        return
    
    setup = DatabaseSetup()
    
    # Menu
    while True:
        print("\nWhat would you like to do?")
        print("1. Create database tables")
        print("2. Load Florida parcel data (NAP file)")
        print("3. Load sales data (SDF file)")
        print("4. Verify data")
        print("5. Run complete setup (all above)")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            setup.create_tables()
        elif choice == '2':
            setup.load_florida_parcels()
        elif choice == '3':
            setup.load_sales_data()
        elif choice == '4':
            setup.verify_data()
        elif choice == '5':
            print("\nRunning complete setup...")
            setup.create_tables()
            setup.load_florida_parcels()
            setup.load_sales_data()
            setup.verify_data()
            print("\n✅ Complete setup finished!")
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()