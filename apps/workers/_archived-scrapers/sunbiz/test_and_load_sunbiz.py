"""
Test Supabase connection and load sample Sunbiz data
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from root directory
root_env = Path(__file__).parent.parent.parent / '.env'
load_dotenv(root_env)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Supabase connection"""
    logger.info("Testing Supabase connection...")
    
    # Use the correct Supabase URL
    supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
    
    if not supabase_key:
        logger.error("❌ SUPABASE_ANON_KEY not found")
        return None
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Test by trying to query a table
        result = supabase.table('florida_parcels').select('*').limit(1).execute()
        logger.info("✅ Supabase connection successful!")
        
        return supabase
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return None

def create_sunbiz_tables_if_needed(supabase: Client):
    """Check if Sunbiz tables exist"""
    logger.info("Checking for Sunbiz tables...")
    
    tables_to_check = [
        'sunbiz_corporations',
        'sunbiz_fictitious_names',
        'sunbiz_registered_agents',
        'sunbiz_entity_search'
    ]
    
    existing_tables = []
    missing_tables = []
    
    for table in tables_to_check:
        try:
            # Try to query the table
            result = supabase.table(table).select('*').limit(1).execute()
            existing_tables.append(table)
            logger.info(f"✅ Table exists: {table}")
        except:
            missing_tables.append(table)
            logger.warning(f"⚠️ Table missing: {table}")
    
    if missing_tables:
        logger.info("\n📋 Please create missing tables using the SQL from 'sunbiz_complete_schema.sql'")
        logger.info("   Run this in your Supabase SQL Editor:")
        logger.info("   https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new")
        return False
    
    return True

def load_sample_data(supabase: Client):
    """Load a sample of Sunbiz data"""
    logger.info("\n🔄 Loading sample Sunbiz data...")
    
    data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\cor")
    
    # Find a recent corporation file
    txt_files = list(data_path.glob("*2025*.txt"))
    if not txt_files:
        txt_files = list(data_path.glob("*.txt"))
    
    if not txt_files:
        logger.error("No corporation files found")
        return
    
    # Use the most recent file
    txt_files.sort(reverse=True)
    sample_file = txt_files[0]
    
    logger.info(f"Loading sample from: {sample_file.name}")
    
    sample_corps = []
    
    with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= 100:  # Load first 100 records as sample
                break
            
            if len(line.strip()) < 100:
                continue
            
            # Parse corporation data
            corp = {
                'entity_id': line[0:12].strip(),
                'entity_name': line[12:212].strip()[:255],  # Limit to 255 chars
                'status': line[212:218].strip(),
                'entity_type': line[218:228].strip(),
                'principal_address': line[238:338].strip(),
                'principal_city': line[338:388].strip(),
                'principal_state': line[388:390].strip(),
                'principal_zip': line[390:400].strip(),
            }
            
            # Only add if we have a valid entity_id
            if corp['entity_id'] and len(corp['entity_id']) >= 6:
                sample_corps.append(corp)
    
    logger.info(f"Parsed {len(sample_corps)} sample corporations")
    
    if sample_corps:
        try:
            # Insert sample data
            result = supabase.table('sunbiz_corporations').upsert(sample_corps).execute()
            logger.info(f"✅ Inserted {len(sample_corps)} sample corporations")
            
            # Show a few examples
            logger.info("\n📊 Sample data loaded:")
            for corp in sample_corps[:3]:
                logger.info(f"  • {corp['entity_id']}: {corp['entity_name'][:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inserting data: {e}")
            
            # If table doesn't exist, show the schema
            if "relation" in str(e) and "does not exist" in str(e):
                logger.info("\n📋 Tables don't exist. Please run this SQL in Supabase:")
                with open('sunbiz_complete_schema.sql', 'r') as f:
                    logger.info(f.read()[:1000] + "\n...")
            
            return False
    
    return False

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("SUNBIZ DATABASE LOADER - TEST & SAMPLE")
    logger.info("=" * 60)
    
    # Test connection
    supabase = test_connection()
    
    if not supabase:
        logger.error("\n❌ Cannot connect to Supabase. Please check your credentials.")
        return
    
    # Check tables
    tables_exist = create_sunbiz_tables_if_needed(supabase)
    
    if not tables_exist:
        logger.info("\n⏸️  Please create the tables first, then run this script again.")
        
        # Generate the schema file if it doesn't exist
        if not Path('sunbiz_complete_schema.sql').exists():
            logger.info("Generating schema file...")
            os.system('python sunbiz_complete_loader.py')
        
        return
    
    # Load sample data
    success = load_sample_data(supabase)
    
    if success:
        logger.info("\n✅ Sample data loaded successfully!")
        logger.info("📌 To load ALL data (16GB), run: python sunbiz_complete_loader.py")
    else:
        logger.info("\n⚠️ Sample data loading failed. Check the errors above.")

if __name__ == "__main__":
    main()