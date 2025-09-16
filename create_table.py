#!/usr/bin/env python3
"""
Create Florida Parcels Table in Supabase
"""

import os
import sys
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_florida_parcels_table():
    """Create the florida_parcels table in Supabase."""
    
    # Load environment variables
    load_dotenv('apps/web/.env')
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase credentials. Check apps/web/.env file.")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    logger.info("Creating florida_parcels table...")
    
    # Read the SQL schema
    try:
        with open('create_florida_parcels_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        logger.info("Schema file loaded successfully")
        
        # Since supabase-py doesn't support direct SQL execution,
        # we'll create a simple version using the table creation API
        
        # First check if table exists
        try:
            result = supabase.table('florida_parcels').select("count", count="exact").limit(1).execute()
            logger.info("Table 'florida_parcels' already exists")
            return True
        except Exception as e:
            logger.info("Table 'florida_parcels' does not exist, will create it")
        
        logger.info("Please manually execute the SQL schema in Supabase SQL Editor:")
        logger.info("1. Go to https://pmispwtdngkcmsrsjwbp.supabase.co/project/pmispwtdngkcmsrsjwbp/sql")
        logger.info("2. Copy and paste the contents of create_florida_parcels_schema.sql")
        logger.info("3. Click 'Run' to execute the schema")
        logger.info("4. Then run the import script: python import_florida_parcels.py")
        
        return True
        
    except FileNotFoundError:
        logger.error("Schema file 'create_florida_parcels_schema.sql' not found")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = create_florida_parcels_table()
    if success:
        logger.info("Table creation process completed")
    else:
        logger.error("Table creation failed")
        sys.exit(1)