"""
Complete pipeline for Broward County Daily Index data
Orchestrates download, parsing, and database loading
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from downloader import BrowardDailyIndexDownloader
from parser import BrowardIndexParser
from database import BrowardIndexDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowardDailyIndexPipeline:
    """Complete pipeline for processing Broward daily index data"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.downloader = BrowardDailyIndexDownloader()
        self.parser = BrowardIndexParser()
        self.database = BrowardIndexDatabase()
        
        self.stats = {
            'files_downloaded': 0,
            'files_parsed': 0,
            'records_processed': 0,
            'records_inserted': 0,
            'errors': []
        }
    
    def run_full_pipeline(self, days_back: int = 7) -> Dict:
        """
        Run the complete pipeline
        
        Args:
            days_back: Number of days to look back for files
            
        Returns:
            Pipeline execution summary
        """
        logger.info(f"Starting Broward Daily Index pipeline (last {days_back} days)")
        start_time = datetime.now()
        
        try:
            # Step 1: Download latest files
            logger.info("Step 1: Downloading files...")
            download_result = self.downloader.download_latest(days_back=days_back)
            self.stats['files_downloaded'] = download_result.get('downloaded', 0)
            
            if self.stats['files_downloaded'] == 0:
                logger.info("No new files to process")
                return self._get_summary(start_time)
            
            # Step 2: Parse downloaded files
            logger.info("Step 2: Parsing files...")
            all_records = []
            
            for file_path in download_result.get('files', []):
                # Extract any ZIP files first
                if file_path.endswith('.zip'):
                    extracted_files = self.downloader.extract_zip_file(file_path)
                    
                    # Parse each extracted file
                    for extracted_file in extracted_files:
                        records = self.parser.parse_file(extracted_file)
                        if records:
                            all_records.extend(records)
                            self.stats['files_parsed'] += 1
                            
                            # Add file metadata to records
                            file_name = os.path.basename(extracted_file)
                            for record in records:
                                record['file_name'] = file_name
                else:
                    # Parse non-ZIP files directly
                    records = self.parser.parse_file(file_path)
                    if records:
                        all_records.extend(records)
                        self.stats['files_parsed'] += 1
                        
                        # Add file metadata
                        file_name = os.path.basename(file_path)
                        for record in records:
                            record['file_name'] = file_name
            
            self.stats['records_processed'] = len(all_records)
            logger.info(f"Parsed {self.stats['records_processed']} records from {self.stats['files_parsed']} files")
            
            # Step 3: Insert records into database
            if all_records:
                logger.info("Step 3: Loading records into database...")
                insert_result = self.database.insert_records(all_records)
                self.stats['records_inserted'] = insert_result.get('inserted', 0)
                
                if insert_result.get('errors'):
                    self.stats['errors'].extend(insert_result['errors'])
                
                # Step 4: Update property links
                logger.info("Step 4: Linking records to properties...")
                link_result = self.database.update_property_links(all_records)
                
                # Step 5: Save metadata
                logger.info("Step 5: Saving metadata...")
                metadata = {
                    'pipeline_run': datetime.now().isoformat(),
                    'days_back': days_back,
                    'files_downloaded': self.stats['files_downloaded'],
                    'files_parsed': self.stats['files_parsed'],
                    'records_processed': self.stats['records_processed'],
                    'records_inserted': self.stats['records_inserted'],
                    'properties_linked': link_result.get('linked', 0)
                }
                self.database.save_metadata(metadata)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.stats['errors'].append(str(e))
        
        return self._get_summary(start_time)
    
    def run_monitoring(self, check_interval: int = 3600):
        """
        Run continuous monitoring
        
        Args:
            check_interval: Seconds between checks
        """
        logger.info(f"Starting continuous monitoring (interval: {check_interval} seconds)")
        
        while True:
            try:
                # Run pipeline for last day
                result = self.run_full_pipeline(days_back=1)
                
                logger.info(f"Pipeline run complete: {result['records_inserted']} records inserted")
                
                # Wait before next check
                logger.info(f"Next check in {check_interval} seconds...")
                import time
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                logger.info(f"Retrying in {check_interval} seconds...")
                import time
                time.sleep(check_interval)
    
    def _get_summary(self, start_time: datetime) -> Dict:
        """Get pipeline execution summary"""
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success' if not self.stats['errors'] else 'partial',
            'duration_seconds': duration,
            'files_downloaded': self.stats['files_downloaded'],
            'files_parsed': self.stats['files_parsed'],
            'records_processed': self.stats['records_processed'],
            'records_inserted': self.stats['records_inserted'],
            'errors': self.stats['errors'][:5],  # Limit errors
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            'downloader': self.downloader.get_download_status(),
            'parser': self.parser.get_stats(),
            'database': self.database.get_stats()
        }


if __name__ == "__main__":
    # Initialize pipeline
    pipeline = BrowardDailyIndexPipeline()
    
    # Run full pipeline for last 30 days
    result = pipeline.run_full_pipeline(days_back=30)
    
    print("\nPipeline Execution Summary:")
    print(json.dumps(result, indent=2))
    
    # Get status
    status = pipeline.get_status()
    print("\nPipeline Status:")
    print(json.dumps(status, indent=2, default=str))