"""
Test script for Broward County 2025 NAL data processing
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from duckdb_processor import DORDuckDBProcessor
from file_manager import DORDataAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broward_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def test_direct_processing():
    """Test direct processing of Broward County data"""
    
    logger.info("=" * 60)
    logger.info("Starting Broward County 2025 NAL Data Test")
    logger.info("=" * 60)
    
    processor = DORDuckDBProcessor()
    
    try:
        # Initialize processor
        logger.info("Initializing DuckDB processor...")
        await processor.initialize()
        
        # Broward County URL
        broward_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Broward%2016%20Preliminary%20NAL%202025.zip"
        
        logger.info("Processing Broward County data...")
        logger.info(f"URL: {broward_url}")
        
        # Process the data
        start_time = datetime.now()
        
        result = await processor.process_county_data(
            url=broward_url,
            county="Broward",
            year=2025
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"County: {result['county']}")
        logger.info(f"Year: {result['year']}")
        logger.info(f"Properties Loaded: {result['properties']:,}")
        logger.info(f"Sales Loaded: {result['sales']:,}")
        logger.info(f"Processing Time: {duration:.2f} seconds")
        logger.info("=" * 60)
        
        # Test some queries
        logger.info("\nRunning test queries...")
        
        # Top 10 properties by value
        query_result = processor.conn.execute("""
            SELECT 
                folio,
                owner_name,
                situs_address_1,
                situs_city,
                just_value
            FROM dor_properties
            WHERE county = 'Broward' AND year = 2025
            ORDER BY just_value DESC
            LIMIT 10
        """).df()
        
        logger.info("\nTop 10 Properties by Value:")
        for idx, row in query_result.iterrows():
            logger.info(f"  {idx+1}. ${row['just_value']:,.0f} - {row['owner_name'][:50]}")
            logger.info(f"     {row['situs_address_1']}, {row['situs_city']}")
            
        # City summary
        city_summary = processor.conn.execute("""
            SELECT 
                situs_city,
                COUNT(*) as property_count,
                AVG(just_value) as avg_value,
                SUM(just_value) as total_value
            FROM dor_properties
            WHERE county = 'Broward' AND year = 2025
            GROUP BY situs_city
            ORDER BY total_value DESC
            LIMIT 10
        """).df()
        
        logger.info("\nTop 10 Cities by Total Property Value:")
        for idx, row in city_summary.iterrows():
            logger.info(
                f"  {idx+1}. {row['situs_city']}: "
                f"{row['property_count']:,} properties, "
                f"Avg: ${row['avg_value']:,.0f}, "
                f"Total: ${row['total_value']:,.0f}"
            )
            
        # Export summary to Excel
        output_file = processor.data_dir / f"Broward_2025_test_summary.xlsx"
        logger.info(f"\nExporting summary to: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            query_result.to_excel(writer, sheet_name='Top Properties', index=False)
            city_summary.to_excel(writer, sheet_name='City Summary', index=False)
            
        logger.info("Summary exported successfully!")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        raise
        
    finally:
        await processor.close()
        

async def test_agent_system():
    """Test the automated agent system"""
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Automated Agent System")
    logger.info("=" * 60)
    
    agent = DORDataAgent()
    
    try:
        # Start the agent
        await agent.start()
        
        # Manually trigger Broward download
        logger.info("Triggering Broward County download...")
        await agent.manual_download("Broward", 2025)
        
        # Wait for processing
        logger.info("Waiting for processing to complete...")
        await asyncio.sleep(10)
        
        # Check status
        pending = agent.manager.get_pending_files()
        processed = [f for f in agent.manager.file_registry.values() 
                    if f.status.value == 'processed']
        failed = agent.manager.get_failed_files()
        
        logger.info(f"\nFile Status:")
        logger.info(f"  Pending: {len(pending)}")
        logger.info(f"  Processed: {len(processed)}")
        logger.info(f"  Failed: {len(failed)}")
        
        if processed:
            logger.info("\nProcessed Files:")
            for f in processed:
                logger.info(f"  - {f.filename}: {f.record_count:,} records")
                
        if failed:
            logger.info("\nFailed Files:")
            for f in failed:
                logger.info(f"  - {f.filename}: {f.error_message}")
                
    finally:
        await agent.stop()
        

async def main():
    """Main test execution"""
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        return
        
    try:
        # Test direct processing
        await test_direct_processing()
        
        # Test agent system
        await test_agent_system()
        
        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import pandas as pd  # Import here for the Excel export
    asyncio.run(main())