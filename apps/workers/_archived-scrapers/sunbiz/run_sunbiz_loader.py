"""
Run Sunbiz Complete Loader - Non-interactive version
Loads all Sunbiz data into existing tables
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from root
root_env = Path(__file__).parent.parent.parent / '.env'
load_dotenv(root_env)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the loader components
from sunbiz_complete_loader import Corporation, FictitiousName, RegisteredAgent, SunbizCompleteLoader

class NonInteractiveSunbizLoader(SunbizCompleteLoader):
    """Non-interactive version of the Sunbiz loader"""
    
    async def run(self):
        """Main execution function without prompts"""
        logger.info("=" * 60)
        logger.info("SUNBIZ DATABASE LOADER - STARTING")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Check if tables exist
        logger.info("Checking existing tables...")
        try:
            # Test query to verify tables exist
            result = self.supabase.table('sunbiz_corporate').select('entity_id').limit(1).execute()
            logger.info("✅ Sunbiz tables exist, proceeding with data load")
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                logger.error("❌ Sunbiz tables don't exist! Please create them first using sunbiz_complete_schema.sql")
                return
            else:
                logger.warning(f"Table check warning: {e}")
        
        # Load all data types
        logger.info("\n📊 Starting data load from TEMP/DATABASE/doc...")
        
        await self.load_corporations()
        await self.load_fictitious_names()
        await self.load_registered_agents()
        
        # Build search index
        logger.info("\n🔍 Building search index...")
        await self.build_search_index()
        
        # Calculate total time
        duration = datetime.now() - start_time
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏱️  Duration: {duration}")
        logger.info(f"🏢 Corporations: {self.stats['corporations']:,}")
        logger.info(f"📝 Fictitious Names: {self.stats['fictitious_names']:,}")
        logger.info(f"👤 Registered Agents: {self.stats['agents']:,}")
        logger.info(f"📊 Total Records: {sum([self.stats['corporations'], self.stats['fictitious_names'], self.stats['agents']]):,}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        # Provide monitoring query
        logger.info("\n📈 Monitor progress with:")
        logger.info("SELECT tablename, n_live_tup FROM pg_stat_user_tables WHERE tablename LIKE 'sunbiz%';")

async def main():
    """Run the non-interactive loader"""
    # Use hardcoded credentials to avoid environment issues
    os.environ['SUPABASE_URL'] = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
    os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
    
    loader = NonInteractiveSunbizLoader()
    await loader.run()

if __name__ == "__main__":
    asyncio.run(main())