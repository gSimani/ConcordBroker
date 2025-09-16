#!/usr/bin/env python3
"""
Tax Deed Real-Time Monitoring Startup Script
Deploys database schema and starts the real-time monitoring system
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "apps"))

from apps.workers.supabase_config import SupabaseConfig
from apps.workers.tax_deed_scheduler_integration import TaxDeedSchedulerIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tax_deed_monitoring.log')
    ]
)

logger = logging.getLogger(__name__)

async def deploy_database_schema():
    """Deploy the tax deed monitoring database schema"""
    try:
        logger.info("Deploying tax deed monitoring database schema...")
        
        supabase = SupabaseConfig().client
        
        # Read and execute schema file
        schema_file = current_dir / "tax_deed_changes_schema.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement.upper().startswith(('CREATE', 'INSERT', 'GRANT')):
                try:
                    result = await supabase.rpc('exec_sql', {'sql': statement}).execute()
                    logger.info(f"Executed: {statement[:50]}...")
                except Exception as e:
                    logger.warning(f"Statement failed (may already exist): {statement[:50]}... - {e}")
        
        logger.info("Database schema deployment completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to deploy database schema: {e}")
        return False

async def test_monitoring_system():
    """Test the monitoring system components"""
    try:
        logger.info("Testing monitoring system components...")
        
        # Initialize integration
        integration = TaxDeedSchedulerIntegration()
        await integration.initialize()
        
        # Test status check
        status = await integration.get_monitoring_status()
        logger.info(f"Monitoring system status: {status}")
        
        # Test a single quick check
        logger.info("Performing test quick check...")
        from apps.workers.tax_deed_monitor import TaxDeedMonitor
        
        monitor = TaxDeedMonitor()
        await monitor.initialize()
        
        # Perform quick status check
        await monitor._quick_status_check()
        
        logger.info("Monitoring system test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Monitoring system test failed: {e}")
        return False

async def start_monitoring_system():
    """Start the full monitoring system"""
    try:
        logger.info("🚀 Starting Tax Deed Real-Time Monitoring System...")
        
        # Initialize and start the integrated monitoring
        integration = TaxDeedSchedulerIntegration()
        await integration.initialize()
        
        logger.info("✅ Tax Deed Monitoring System initialized successfully")
        logger.info("📊 System will monitor the following:")
        logger.info("   • Broward County tax deed auctions every 30 seconds")
        logger.info("   • Deep content scans every 5 minutes") 
        logger.info("   • Full data scans daily at 2 AM")
        logger.info("   • Real-time alerts for cancellations and postponements")
        logger.info("   • Bid change notifications")
        logger.info("   • Performance monitoring and daily reports")
        
        # Start monitoring
        await integration.start_monitoring()
        
        # Keep running
        logger.info("🔄 Monitoring system is now running...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                await asyncio.sleep(300)  # 5 minutes
                
                # Get and log status every 5 minutes
                status = await integration.get_monitoring_status()
                logger.info(f"📈 Status Update: {status['active_monitors']}/{status['total_monitors']} monitors active, "
                           f"{status['recent_changes_24h']} changes in 24h, "
                           f"{status['critical_changes_24h']} critical")
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
        
        finally:
            await integration.stop_monitoring()
            logger.info("✅ Tax Deed Monitoring System stopped")
        
    except Exception as e:
        logger.error(f"❌ Failed to start monitoring system: {e}")
        raise

async def main():
    """Main startup function"""
    logger.info("=" * 80)
    logger.info("🏛️  TAX DEED REAL-TIME MONITORING SYSTEM")
    logger.info("=" * 80)
    logger.info("Critical investment data monitoring for tax deed auctions")
    logger.info("Tracks cancellations, postponements, bid changes in real-time")
    logger.info("=" * 80)
    
    # Step 1: Deploy database schema
    logger.info("📋 Step 1: Deploying database schema...")
    schema_success = await deploy_database_schema()
    
    if not schema_success:
        logger.error("❌ Database schema deployment failed - cannot continue")
        return
    
    # Step 2: Test monitoring system
    logger.info("🧪 Step 2: Testing monitoring system...")
    test_success = await test_monitoring_system()
    
    if not test_success:
        logger.error("❌ Monitoring system test failed - check configuration")
        return
    
    # Step 3: Start monitoring
    logger.info("🚀 Step 3: Starting real-time monitoring...")
    await start_monitoring_system()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Tax Deed Monitoring System shutdown complete")
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        sys.exit(1)