"""
Quick test script for DOR processor with Broward County data
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root .env
root_dir = Path(__file__).parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Add dor_processor to path
sys.path.append(str(root_dir / 'apps' / 'workers' / 'dor_processor'))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from duckdb_processor import DORDuckDBProcessor

async def main():
    """Test Broward County data processing"""
    
    # Check environment
    logger.info("Environment Check:")
    logger.info(f"SUPABASE_URL: {'✓' if os.getenv('SUPABASE_URL') else '✗'}")
    logger.info(f"SUPABASE_KEY: {'✓' if os.getenv('SUPABASE_KEY') else '✗'}")
    logger.info(f"DATABASE_URL: {'✓' if os.getenv('DATABASE_URL') else '✗'}")
    
    if not all([os.getenv('SUPABASE_URL'), os.getenv('DATABASE_URL')]):
        logger.error("Missing required environment variables!")
        return
    
    processor = DORDuckDBProcessor()
    
    try:
        logger.info("\n" + "="*60)
        logger.info("Starting Broward County NAL Data Processing")
        logger.info("="*60)
        
        await processor.initialize()
        
        # Broward County 2025 Preliminary NAL
        broward_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Broward%2016%20Preliminary%20NAL%202025.zip"
        
        logger.info(f"\nDownloading from: {broward_url}")
        logger.info("This may take a few minutes for the large file...")
        
        result = await processor.process_county_data(
            url=broward_url,
            county="Broward",
            year=2025
        )
        
        logger.info("\n" + "="*60)
        logger.info("PROCESSING COMPLETE!")
        logger.info("="*60)
        logger.info(f"County: {result['county']}")
        logger.info(f"Year: {result['year']}")
        logger.info(f"Properties Loaded: {result['properties']:,}")
        logger.info(f"Sales Loaded: {result['sales']:,}")
        
        # Quick verification query
        if processor.conn:
            check = processor.conn.execute("""
                SELECT COUNT(*) as count FROM properties_clean
            """).fetchone()
            
            if check:
                logger.info(f"\nVerified {check[0]:,} records in processing buffer")
        
        logger.info("\n✓ Data successfully loaded to Supabase!")
        logger.info("Check your Supabase dashboard to see the dor_properties table")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await processor.close()

if __name__ == "__main__":
    asyncio.run(main())