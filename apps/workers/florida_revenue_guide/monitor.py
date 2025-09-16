"""
Monitor for Florida Revenue NAL/SDF/NAP Users Guide updates
Checks for updates and re-parses schema when changed
"""

import os
import sys
import json
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from guide_downloader import FloridaRevenueGuideDownloader
from guide_parser import FloridaRevenueGuideParser
from data_validator import FloridaRevenueDataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_revenue_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaRevenueMonitor:
    """Monitors and manages Florida Revenue Users Guide and data validation"""
    
    def __init__(self):
        """Initialize monitor components"""
        self.downloader = FloridaRevenueGuideDownloader()
        self.parser = FloridaRevenueGuideParser()
        self.validator = FloridaRevenueDataValidator()
        
        self.run_count = 0
        self.last_check = None
        self.last_update = None
        
        # Schema storage path
        self.schema_path = Path("data/florida_revenue_guide/extracted/schema.json")
        self.schema_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing schema if available
        if self.schema_path.exists():
            self.validator.load_schema(self.schema_path)
    
    def check_for_updates(self) -> Dict:
        """Check for PDF updates and process if found"""
        logger.info("Checking for Florida Revenue Users Guide updates")
        self.run_count += 1
        self.last_check = datetime.now()
        
        try:
            # Check for updates
            has_update = self.downloader.check_for_updates()
            
            if has_update:
                logger.info("Users Guide update detected, downloading new version")
                
                # Download updated PDF
                download_result = self.downloader.download_pdf()
                
                if download_result and download_result['status'] == 'downloaded':
                    # Parse the new PDF
                    pdf_path = self.downloader.get_latest_pdf_path()
                    if pdf_path:
                        logger.info("Parsing updated Users Guide")
                        schema = self.parser.parse_pdf(pdf_path)
                        
                        # Save new schema
                        self.parser.save_schema(schema, self.schema_path)
                        
                        # Reload validator with new schema
                        self.validator.load_schema(self.schema_path)
                        
                        self.last_update = datetime.now()
                        
                        # Log update
                        self._log_update(download_result, schema)
                        
                        # Validate sample files if available
                        self._validate_sample_files()
                        
                        return {
                            'status': 'updated',
                            'message': 'Users Guide updated and schema extracted',
                            'version_info': download_result.get('version_info'),
                            'schema_stats': schema.get('statistics')
                        }
            else:
                logger.info("No Users Guide updates found")
                return {
                    'status': 'no_update',
                    'message': 'Users Guide has not been updated',
                    'last_check': self.last_check.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'last_check': self.last_check.isoformat()
            }
    
    def _log_update(self, download_result: Dict, schema: Dict):
        """Log update information"""
        update_info = {
            'timestamp': datetime.now().isoformat(),
            'download_result': download_result,
            'schema_statistics': schema.get('statistics'),
            'run_count': self.run_count
        }
        
        log_file = Path("data/florida_revenue_guide/metadata/update_log.json")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing log
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {'updates': []}
        
        # Add new update
        log_data['updates'].append(update_info)
        
        # Save updated log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def _validate_sample_files(self):
        """Validate sample data files if available"""
        # Look for Florida Revenue data files in common locations
        data_patterns = [
            ('NAL*.csv', 'NAL'),
            ('SDF*.csv', 'SDF'),
            ('NAP*.csv', 'NAP'),
            ('*NAL*.txt', 'NAL'),
            ('*SDF*.txt', 'SDF')
        ]
        
        sample_results = []
        
        for pattern, file_type in data_patterns:
            files = list(Path('.').glob(pattern))
            if files:
                # Validate first matching file
                test_file = files[0]
                logger.info(f"Validating sample {file_type} file: {test_file}")
                
                result = self.validator.validate_file(test_file, file_type)
                sample_results.append({
                    'file': str(test_file),
                    'type': file_type,
                    'valid': result['valid'],
                    'errors': result.get('error_count', 0),
                    'warnings': result.get('warning_count', 0)
                })
        
        if sample_results:
            # Save validation results
            results_file = Path("data/florida_revenue_guide/metadata/sample_validation.json")
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': sample_results
                }, f, indent=2)
            
            logger.info(f"Validated {len(sample_results)} sample files")
    
    def validate_data_file(self, file_path: Path, file_type: Optional[str] = None) -> Dict:
        """Validate a data file against current schema"""
        if not self.schema_path.exists():
            # Try to load schema first
            logger.info("Schema not found, attempting to download and parse Users Guide")
            self.check_for_updates()
        
        # Ensure validator has schema loaded
        if not self.validator.schema:
            self.validator.load_schema(self.schema_path)
        
        # Validate file
        return self.validator.validate_file(file_path, file_type)
    
    def daily_check(self):
        """Perform daily check for updates"""
        logger.info(f"Running daily check #{self.run_count + 1}")
        
        result = self.check_for_updates()
        
        # Save status
        self._save_status(result)
        
        logger.info(f"Daily check completed: {result['status']}")
    
    def _save_status(self, result: Dict):
        """Save monitor status to file"""
        status = {
            'run_count': self.run_count,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'last_result': result,
            'current_version': self.downloader.get_current_version()
        }
        
        status_file = Path("florida_revenue_monitor_status.json")
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def start_monitoring(self, check_time: str = "04:00"):
        """
        Start daily monitoring for Users Guide updates
        
        Args:
            check_time: Time to run daily check (24-hour format)
        """
        logger.info(f"Starting Florida Revenue monitoring service")
        logger.info(f"Daily checks scheduled for {check_time}")
        
        # Schedule daily check
        schedule.every().day.at(check_time).do(self.daily_check)
        
        # Also check monthly for new year guides
        schedule.every().month.do(self.check_for_updates)
        
        # Run initial check
        logger.info("Running initial check...")
        self.daily_check()
        
        # Start monitoring loop
        logger.info("Monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {e}")
    
    def run_once(self):
        """Run check once and exit"""
        logger.info("Running one-time check for Users Guide updates")
        
        result = self.check_for_updates()
        
        print("\nCheck Result:")
        print(json.dumps(result, indent=2))
        
        # If schema exists, show statistics
        if self.schema_path.exists():
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            
            if 'statistics' in schema:
                print("\nCurrent Schema Statistics:")
                print(json.dumps(schema['statistics'], indent=2))
        
        # Show current version info
        current = self.downloader.get_current_version()
        if current:
            print("\nCurrent Version Info:")
            print(f"  Year: {current.get('year', 'Unknown')}")
            print(f"  Downloaded: {current.get('downloaded_at', 'Unknown')}")
            print(f"  Size: {current.get('size', 0):,} bytes")
        
        return result
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        return {
            'run_count': self.run_count,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'schema_exists': self.schema_path.exists(),
            'current_version': self.downloader.get_current_version()
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Revenue Users Guide Monitor')
    parser.add_argument('--mode', choices=['monitor', 'once', 'validate'],
                       default='once',
                       help='Run mode: monitor (continuous), once (single check), validate (test file)')
    parser.add_argument('--time', default="04:00",
                       help='Time for daily checks (24-hour format)')
    parser.add_argument('--file', help='File to validate (for validate mode)')
    parser.add_argument('--type', choices=['NAL', 'SDF', 'NAP', 'NAV', 'TPP'],
                       help='File type for validation')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = FloridaRevenueMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(check_time=args.time)
    elif args.mode == 'validate':
        # Validate a specific file
        if args.file:
            file_path = Path(args.file)
            if file_path.exists():
                result = monitor.validate_data_file(file_path, args.type)
                print(f"\nValidation Result for {file_path.name}:")
                print(f"  File Type: {result.get('file_type', 'Unknown')}")
                print(f"  Valid: {result.get('valid', False)}")
                print(f"  Errors: {result.get('error_count', 0)}")
                print(f"  Warnings: {result.get('warning_count', 0)}")
                
                if result.get('errors'):
                    print("\nFirst 5 errors:")
                    for error in result['errors'][:5]:
                        print(f"  - {error}")
            else:
                print(f"File not found: {args.file}")
        else:
            print("Please specify a file to validate with --file")
    else:
        # Run once
        monitor.run_once()