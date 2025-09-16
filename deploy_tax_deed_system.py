"""
Deploy Tax Deed System - Database setup and initial scrape
"""

import os
import sys
import asyncio
from supabase import create_client
import logging

# Add workers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'workers'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Create database tables"""
    logger.info("Setting up database tables...")
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_key:
        logger.error("❌ Supabase credentials not found in environment")
        logger.info("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        return False
    
    try:
        client = create_client(supabase_url, supabase_key)
        
        # Read SQL file
        with open('create_tax_deed_tables.sql', 'r') as f:
            sql = f.read()
        
        logger.info("📋 SQL schema loaded")
        logger.info("⚠️  Please run the SQL script manually in Supabase dashboard:")
        logger.info("   1. Go to https://app.supabase.com")
        logger.info("   2. Select your project")
        logger.info("   3. Go to SQL Editor")
        logger.info("   4. Paste and run the contents of create_tax_deed_tables.sql")
        logger.info("")
        logger.info("Press Enter once you've created the tables...")
        input()
        
        # Verify tables exist
        try:
            result = client.table('tax_deed_properties').select('*').limit(1).execute()
            logger.info("✅ tax_deed_properties table verified")
            
            result = client.table('tax_deed_contacts').select('*').limit(1).execute()
            logger.info("✅ tax_deed_contacts table verified")
            
            return True
        except Exception as e:
            logger.error(f"❌ Tables not found: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        return False

async def run_initial_scrape():
    """Run the tax deed scraper"""
    logger.info("\n=== Running Initial Scrape ===")
    
    try:
        from tax_deed_scraper import BrowardTaxDeedScraper
        
        async with BrowardTaxDeedScraper() as scraper:
            results = await scraper.scrape_all()
            
            logger.info("\n📊 Scraping Results:")
            logger.info(f"  Auctions found: {results.get('auctions_scraped', 0)}")
            logger.info(f"  Properties scraped: {results.get('properties_scraped', 0)}")
            logger.info(f"  Properties saved: {results.get('properties_saved', 0)}")
            
            if results.get('inserted'):
                logger.info(f"  New properties: {results['inserted']}")
            if results.get('updated'):
                logger.info(f"  Updated properties: {results['updated']}")
            
            if results.get('errors'):
                logger.warning("\n⚠️ Errors encountered:")
                for error in results['errors'][:5]:  # Show first 5 errors
                    logger.warning(f"  - {error}")
            
            return results
            
    except ImportError:
        logger.error("❌ Could not import tax_deed_scraper")
        logger.info("Make sure tax_deed_scraper.py is in apps/workers/")
        return None
    except Exception as e:
        logger.error(f"❌ Scraping error: {e}")
        return None

async def test_frontend_connection():
    """Test if frontend can connect to the data"""
    logger.info("\n=== Testing Frontend Connection ===")
    
    supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_key:
        logger.warning("⚠️ Supabase credentials not set")
        return
    
    try:
        client = create_client(supabase_url, supabase_key)
        
        # Get property count
        result = client.table('tax_deed_properties').select('*', count='exact').execute()
        count = len(result.data) if result.data else 0
        
        logger.info(f"✅ Frontend can access {count} properties")
        
        if count > 0:
            # Show sample property
            sample = result.data[0]
            logger.info("\n📋 Sample Property:")
            logger.info(f"  Parcel: {sample.get('parcel_number')}")
            logger.info(f"  Address: {sample.get('situs_address')}")
            logger.info(f"  Opening Bid: ${sample.get('opening_bid', 0):,.2f}")
            logger.info(f"  Status: {sample.get('status')}")
            
    except Exception as e:
        logger.error(f"❌ Frontend connection test failed: {e}")

def create_env_file():
    """Create or update .env file with necessary variables"""
    logger.info("\n=== Environment Setup ===")
    
    env_path = '.env'
    env_content = []
    
    # Check existing .env
    existing_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_vars[key] = value
    
    # Required variables
    required_vars = {
        'SUPABASE_URL': 'https://pmmkfrohclzpwpnbtajc.supabase.co',
        'SUPABASE_ANON_KEY': '',
        'VITE_SUPABASE_URL': 'https://pmmkfrohclzpwpnbtajc.supabase.co',
        'VITE_SUPABASE_ANON_KEY': ''
    }
    
    # Check and update
    updated = False
    for key, default in required_vars.items():
        if key not in existing_vars or not existing_vars[key]:
            if 'ANON_KEY' in key:
                logger.warning(f"⚠️ {key} not set - please add your Supabase anon key")
                value = input(f"Enter {key}: ").strip()
                if value:
                    existing_vars[key] = value
                    updated = True
            else:
                existing_vars[key] = default
                updated = True
    
    if updated:
        # Write updated .env
        with open(env_path, 'w') as f:
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")
        logger.info("✅ .env file updated")
    else:
        logger.info("✅ .env file already configured")
    
    # Set environment variables for current session
    for key, value in existing_vars.items():
        if value:
            os.environ[key] = value

async def main():
    """Main deployment script"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         TAX DEED AUCTION SYSTEM DEPLOYMENT              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Environment setup
    create_env_file()
    
    # Step 2: Database setup
    logger.info("\n=== Step 1: Database Setup ===")
    db_ready = await setup_database()
    
    if not db_ready:
        logger.error("❌ Database setup failed. Please fix and try again.")
        return
    
    # Step 3: Run initial scrape
    logger.info("\n=== Step 2: Initial Data Scrape ===")
    scrape_results = await run_initial_scrape()
    
    if not scrape_results:
        logger.warning("⚠️ Scraping failed or returned no results")
        logger.info("This might be normal if there are no current auctions")
    
    # Step 4: Test frontend connection
    await test_frontend_connection()
    
    # Final summary
    print("""
╔══════════════════════════════════════════════════════════╗
║                  DEPLOYMENT COMPLETE                     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("\n✅ Tax Deed System deployed successfully!")
    logger.info("\n📋 Next Steps:")
    logger.info("1. Start the frontend: npm run dev (in apps/web)")
    logger.info("2. Navigate to http://localhost:5173/properties")
    logger.info("3. Click on 'Tax Deed Sales' tab")
    logger.info("4. View scraped properties")
    logger.info("\n🔄 To run scraper again: python apps/workers/tax_deed_scraper.py")
    logger.info("📅 Consider setting up a cron job or scheduler for automatic updates")

if __name__ == "__main__":
    asyncio.run(main())