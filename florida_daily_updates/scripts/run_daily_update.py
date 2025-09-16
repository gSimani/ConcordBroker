#!/usr/bin/env python3
"""
Florida Daily Update Runner
Main entry point for running the Florida property data update system.
Can be run standalone or via scheduler.
"""

import asyncio
import sys
import os
import argparse
import logging
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import FloridaUpdateOrchestrator
from agents.monitor import FloridaDataMonitor
from agents.downloader import FloridaDataDownloader
from agents.processor import FloridaDataProcessor
from agents.database_updater import FloridaDatabaseUpdater

# Configure logging
def setup_logging(config: Dict[str, Any], log_level: str = None):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    level = log_level or log_config.get('level', 'INFO')
    
    # Create log directory
    log_dir = Path(log_config.get('file', {}).get('directory', 'florida_daily_updates/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup log filename with date
    log_filename = log_config.get('file', {}).get('filename', 'florida_updates_{date}.log')
    log_file = log_dir / log_filename.format(date=datetime.now().strftime('%Y%m%d'))
    
    # Configure logging
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handlers = []
    
    # File handler
    if log_config.get('file', {}).get('enabled', True):
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Console handler
    if log_config.get('console', {}).get('enabled', True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load environment-specific overrides
    env = os.getenv('ENVIRONMENT', config.get('system', {}).get('environment', 'production'))
    env_config_path = config_path.parent / f'config.{env}.yaml'
    
    if env_config_path.exists():
        with open(env_config_path, 'r') as f:
            env_config = yaml.safe_load(f)
            # Merge environment-specific config
            config = merge_configs(config, env_config)
    
    # Override with environment variables
    config = override_with_env_vars(config)
    
    return config

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def override_with_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Override configuration with environment variables"""
    # Supabase configuration
    supabase_config = config.get('supabase', {})
    supabase_config['url'] = os.getenv('SUPABASE_URL', supabase_config.get('url', ''))
    supabase_config['anon_key'] = os.getenv('SUPABASE_ANON_KEY', supabase_config.get('anon_key', ''))
    supabase_config['service_key'] = os.getenv('SUPABASE_SERVICE_KEY', supabase_config.get('service_key', ''))
    supabase_config['db_url'] = os.getenv('SUPABASE_DB_URL', supabase_config.get('db_url', ''))
    
    # Email configuration
    email_config = config.get('notifications', {}).get('email', {})
    email_config['username'] = os.getenv('EMAIL_USERNAME', email_config.get('username', ''))
    email_config['password'] = os.getenv('EMAIL_PASSWORD', email_config.get('password', ''))
    
    # Slack configuration
    slack_config = config.get('notifications', {}).get('slack', {})
    slack_config['webhook_url'] = os.getenv('SLACK_WEBHOOK_URL', slack_config.get('webhook_url', ''))
    
    # Other sensitive configurations
    security_config = config.get('security', {})
    security_config['encryption']['key'] = os.getenv('ENCRYPTION_KEY', security_config.get('encryption', {}).get('key', ''))
    
    return config

def get_agent_config(config: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """Get configuration for specific agent"""
    agent_config = config.get(agent_name, {}).copy()
    
    # Add common paths
    base_dir = Path('florida_daily_updates')
    agent_config.setdefault('state_db_path', str(base_dir / 'data' / f'{agent_name}_state.db'))
    
    return agent_config

async def run_full_update(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """Run complete daily update process"""
    try:
        logger.info("Starting Florida daily property data update")
        
        # Create orchestrator with configuration
        orchestrator_config = {
            'monitor': get_agent_config(config, 'monitor'),
            'downloader': get_agent_config(config, 'downloader'), 
            'processor': get_agent_config(config, 'processor'),
            'database': get_agent_config(config, 'database'),
            'max_concurrent_files': config.get('orchestrator', {}).get('max_concurrent_files', 3),
            'continue_on_error': config.get('orchestrator', {}).get('continue_on_error', True),
            'notifications': config.get('notifications', {}),
            'state_db_path': get_agent_config(config, 'orchestrator').get('state_db_path')
        }
        
        orchestrator = FloridaUpdateOrchestrator(orchestrator_config)
        
        # Run the update
        result = await orchestrator.run_daily_update()
        
        # Log results
        if result.success:
            logger.info(f"Update completed successfully:")
            logger.info(f"  Files monitored: {result.files_monitored}")
            logger.info(f"  Files downloaded: {result.files_downloaded}")
            logger.info(f"  Files processed: {result.files_processed}")
            logger.info(f"  Files updated: {result.files_updated}")
            logger.info(f"  Duration: {result.duration:.1f} seconds")
            logger.info(f"  Total records updated: {result.summary.get('total_records_updated', 0):,}")
        else:
            logger.error(f"Update failed:")
            logger.error(f"  Duration: {result.duration:.1f} seconds")
            logger.error(f"  Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Log first 5 errors
                logger.error(f"    {error}")
        
        return result.success
        
    except Exception as e:
        logger.error(f"Critical error in daily update: {e}")
        return False

async def run_monitor_only(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """Run monitoring check only"""
    try:
        logger.info("Running monitoring check only")
        
        monitor_config = get_agent_config(config, 'monitor')
        
        async with FloridaDataMonitor(monitor_config) as monitor:
            result = await monitor.check_for_updates()
        
        if result.success:
            logger.info(f"Monitoring check completed:")
            logger.info(f"  New files: {len(result.new_files)}")
            logger.info(f"  Updated files: {len(result.updated_files)}")
            logger.info(f"  Total files checked: {result.total_files_checked}")
            
            if result.new_files or result.updated_files:
                logger.info("Files available for download:")
                for file_info in result.new_files + result.updated_files:
                    logger.info(f"    {file_info.county} {file_info.file_type}: {file_info.filename}")
        else:
            logger.error("Monitoring check failed:")
            for error in result.errors:
                logger.error(f"  {error}")
        
        return result.success
        
    except Exception as e:
        logger.error(f"Error in monitoring check: {e}")
        return False

async def run_maintenance(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """Run maintenance tasks"""
    try:
        logger.info("Running maintenance tasks")
        
        # File cleanup
        downloader_config = get_agent_config(config, 'downloader')
        downloader = FloridaDataDownloader(downloader_config)
        
        # Clean up old files (default 30 days)
        retention_days = config.get('maintenance', {}).get('files', {}).get('retention_days', 30)
        cleaned_count, cleaned_size = downloader.cleanup_old_files(retention_days)
        logger.info(f"Cleaned up {cleaned_count} old files ({cleaned_size:,} bytes)")
        
        # Database maintenance
        database_config = get_agent_config(config, 'database')
        
        async with FloridaDatabaseUpdater(database_config) as db_updater:
            # Get table statistics
            tables = ['florida_nal_property_details', 'florida_nap_assessments', 'florida_sdf_sales']
            
            for table in tables:
                try:
                    stats = await db_updater.get_table_stats(table)
                    logger.info(f"Table {table}: {stats['total_records']:,} records")
                except Exception as e:
                    logger.warning(f"Could not get stats for {table}: {e}")
        
        logger.info("Maintenance tasks completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in maintenance tasks: {e}")
        return False

async def run_test(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """Run test with limited scope"""
    try:
        logger.info("Running test update")
        
        # Override config for testing
        test_config = config.copy()
        test_config['counties'] = {k: v for k, v in config['counties'].items() if k == 'broward'}
        test_config['file_types'] = {k: v for k, v in config['file_types'].items() if k == 'NAL'}
        test_config['processor']['batch_size'] = 1000
        test_config['database']['batch_size'] = 1000
        
        # Run with test configuration
        return await run_full_update(test_config, logger)
        
    except Exception as e:
        logger.error(f"Error in test update: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Florida Daily Property Data Update System')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--mode', '-m', 
                       choices=['full', 'monitor', 'maintenance', 'test'],
                       default='full',
                       help='Update mode (default: full)')
    parser.add_argument('--log-level', '-l',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run mode (no actual changes)')
    parser.add_argument('--counties',
                       help='Comma-separated list of counties to process')
    parser.add_argument('--file-types',
                       help='Comma-separated list of file types to process (NAL,NAP,SDF)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Setup logging
        logger = setup_logging(config, args.log_level)
        
        # Override counties if specified
        if args.counties:
            active_counties = [c.strip() for c in args.counties.split(',')]
            for county_name in config['counties']:
                config['counties'][county_name]['active'] = county_name in active_counties
        
        # Override file types if specified  
        if args.file_types:
            active_types = [t.strip() for t in args.file_types.split(',')]
            for type_name in config['file_types']:
                config['file_types'][type_name]['active'] = type_name in active_types
        
        # Set dry run mode
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
            config['dry_run'] = True
        
        # Run the appropriate mode
        if args.mode == 'full':
            success = asyncio.run(run_full_update(config, logger))
        elif args.mode == 'monitor':
            success = asyncio.run(run_monitor_only(config, logger))
        elif args.mode == 'maintenance':
            success = asyncio.run(run_maintenance(config, logger))
        elif args.mode == 'test':
            success = asyncio.run(run_test(config, logger))
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        # Exit with appropriate code
        if success:
            logger.info("Operation completed successfully")
            sys.exit(0)
        else:
            logger.error("Operation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()