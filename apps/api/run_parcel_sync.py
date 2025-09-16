#!/usr/bin/env python3
"""
Florida Parcel Data Sync Runner
Executes the initial download and sets up continuous monitoring
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from supabase_parcel_setup import SupabaseParcelManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/parcel_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.supabase')

async def initial_setup():
    """
    Perform initial setup and data download
    """
    logger.info("=" * 60)
    logger.info("Florida Parcel Data Initial Setup")
    logger.info("=" * 60)
    
    # Get configuration from environment
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials. Please configure .env.supabase")
        return False
    
    # Create manager
    manager = SupabaseParcelManager(SUPABASE_URL, SUPABASE_KEY)
    
    # Step 1: Setup database schema
    logger.info("Step 1: Setting up database schema...")
    await manager.setup_database_schema()
    logger.info("✓ Database schema ready")
    
    # Step 2: Configure monitoring agents
    logger.info("Step 2: Configuring monitoring agents...")
    manager.setup_monitoring_agents()
    logger.info("✓ Monitoring agents configured")
    
    # Step 3: Download initial data
    logger.info("Step 3: Downloading parcel data...")
    logger.info("This may take several hours for all counties.")
    
    # Start with priority counties
    priority_counties = ["BROWARD", "MIAMI-DADE", "PALM BEACH"]
    logger.info(f"Priority counties: {', '.join(priority_counties)}")
    
    for county in priority_counties:
        logger.info(f"Downloading {county} county...")
        await manager.download_and_process_county(county)
        logger.info(f"✓ {county} complete")
    
    logger.info("✓ Priority counties downloaded")
    
    # Step 4: Verify data
    logger.info("Step 4: Verifying data...")
    
    # Check record counts
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for county in priority_counties:
        result = supabase.table('florida_parcels').select('count', count='exact').eq('county', county).execute()
        count = result.count if hasattr(result, 'count') else 0
        logger.info(f"  {county}: {count:,} parcels")
    
    logger.info("✓ Data verification complete")
    
    return True

async def start_monitoring():
    """
    Start continuous monitoring
    """
    logger.info("=" * 60)
    logger.info("Starting Continuous Monitoring")
    logger.info("=" * 60)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    manager = SupabaseParcelManager(SUPABASE_URL, SUPABASE_KEY)
    
    logger.info("Starting monitoring cycle...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            # Run monitoring cycle
            await manager.run_monitoring_cycle()
            
            # Wait before next cycle (1 hour)
            await asyncio.sleep(3600)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring error: {e}")

async def download_specific_county(county: str):
    """
    Download data for a specific county
    """
    logger.info(f"Downloading data for {county} county...")
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    manager = SupabaseParcelManager(SUPABASE_URL, SUPABASE_KEY)
    await manager.download_and_process_county(county.upper())
    
    logger.info(f"✓ {county} download complete")

def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Parcel Data Sync')
    parser.add_argument('command', choices=['setup', 'monitor', 'download', 'status'],
                       help='Command to run')
    parser.add_argument('--county', help='County name for download command')
    
    args = parser.parse_args()
    
    # Create logs directory
    Path('./logs').mkdir(exist_ok=True)
    
    if args.command == 'setup':
        # Run initial setup
        success = asyncio.run(initial_setup())
        if success:
            logger.info("✓ Setup complete! Run 'python run_parcel_sync.py monitor' to start monitoring")
        else:
            logger.error("✗ Setup failed. Check logs for details.")
            
    elif args.command == 'monitor':
        # Start monitoring
        asyncio.run(start_monitoring())
        
    elif args.command == 'download':
        # Download specific county
        if not args.county:
            logger.error("County name required. Use --county COUNTYNAME")
            return
        asyncio.run(download_specific_county(args.county))
        
    elif args.command == 'status':
        # Show status
        asyncio.run(show_status())

async def show_status():
    """
    Show current system status
    """
    logger.info("=" * 60)
    logger.info("Florida Parcel Data System Status")
    logger.info("=" * 60)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get monitoring agents status
    agents = supabase.table('monitoring_agents').select('*').execute()
    logger.info("\nMonitoring Agents:")
    for agent in agents.data:
        status = "✓ Active" if agent['enabled'] else "✗ Disabled"
        last_run = agent.get('last_run', 'Never')
        logger.info(f"  {agent['agent_name']}: {status} (Last run: {last_run})")
    
    # Get data statistics
    logger.info("\nData Statistics:")
    
    # Get county counts
    result = supabase.table('florida_parcels').select('county', count='exact').execute()
    
    if result.data:
        counties = {}
        for row in result.data:
            county = row['county']
            if county not in counties:
                counties[county] = 0
            counties[county] += 1
        
        for county, count in sorted(counties.items()):
            logger.info(f"  {county}: {count:,} parcels")
    
    # Get recent updates
    updates = supabase.table('parcel_update_history').select('*').order('update_date', desc=True).limit(5).execute()
    
    if updates.data:
        logger.info("\nRecent Updates:")
        for update in updates.data:
            status = "✓" if update['success'] else "✗"
            logger.info(f"  {status} {update['county']} - {update['update_type']} ({update['update_date']})")
    
    # Check for available updates
    monitor = supabase.table('data_source_monitor').select('*').eq('change_detected', True).execute()
    
    if monitor.data:
        logger.info(f"\n⚠ {len(monitor.data)} files have updates available")
        logger.info("Run 'python run_parcel_sync.py monitor' to download updates")
    else:
        logger.info("\n✓ All data sources are up to date")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()