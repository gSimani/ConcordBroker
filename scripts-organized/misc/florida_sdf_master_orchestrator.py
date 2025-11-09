"""
Florida SDF Master Orchestrator
Comprehensive system to download, process, and upload all Florida Sales Data Files (SDF)
for all 67 counties with complete recovery mechanisms and progress tracking.
"""

import os
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback
from contextlib import contextmanager
import signal
import sys

# Import our custom modules
from florida_counties_manager import FloridaCountiesManager
from sdf_downloader import SdfFileDownloader
from sdf_processor import SdfFileProcessor
from supabase_uploader import SupabaseBatchUploader


@dataclass
class OrchestrationStats:
    """Track orchestration statistics"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    total_counties: int = 0
    counties_completed: int = 0
    counties_failed: int = 0
    counties_skipped: int = 0
    total_records_processed: int = 0
    total_records_uploaded: int = 0
    total_errors: int = 0
    processing_time_hours: float = 0.0
    current_phase: str = 'initializing'
    failed_counties: List[str] = None
    recovery_attempts: int = 0

    def __post_init__(self):
        if self.failed_counties is None:
            self.failed_counties = []


class FloridaSdfMasterOrchestrator:
    """
    Master orchestrator for the complete Florida SDF data pipeline
    """

    def __init__(self,
                 working_dir: str = None,
                 max_concurrent_counties: int = 2,
                 enable_recovery: bool = True,
                 test_mode: bool = False):
        """
        Initialize the master orchestrator

        Args:
            working_dir: Working directory for all operations
            max_concurrent_counties: Maximum counties to process concurrently
            enable_recovery: Enable automatic recovery mechanisms
            test_mode: Run in test mode with limited counties
        """
        self.working_dir = Path(working_dir or "C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/FLORIDA_SDF")
        self.max_concurrent_counties = max_concurrent_counties
        self.enable_recovery = enable_recovery
        self.test_mode = test_mode

        # Create session ID
        self.session_id = f"sdf_orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Setup logging
        self.setup_logging()

        # Initialize components
        self.counties_manager = FloridaCountiesManager()
        self.downloader = SdfFileDownloader(
            download_dir=str(self.working_dir / 'downloads'),
            max_workers=max_concurrent_counties
        )
        self.processor = SdfFileProcessor(
            output_dir=str(self.working_dir / 'processed')
        )
        self.uploader = SupabaseBatchUploader(
            max_workers=max_concurrent_counties
        )

        # Orchestration state
        self.stats = OrchestrationStats(
            session_id=self.session_id,
            start_time=datetime.now().isoformat()
        )
        self.state_file = self.working_dir / f'orchestration_state_{self.session_id}.json'
        self.progress_file = self.working_dir / 'orchestration_progress.json'

        # Recovery state
        self.completed_counties: Set[str] = set()
        self.failed_counties: Set[str] = set()
        self.recovery_lock = threading.Lock()

        # Graceful shutdown handling
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Create working directory structure
        self.setup_directories()

        # Load any existing state
        self.load_existing_state()

    def setup_logging(self):
        """Setup comprehensive logging for orchestration"""
        log_dir = self.working_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s'
        )

        # Main orchestrator log
        main_handler = logging.FileHandler(
            log_dir / f'orchestrator_{self.session_id}.log'
        )
        main_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Setup logger
        self.logger = logging.getLogger('FloridaSdfOrchestrator')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(main_handler)
        self.logger.addHandler(console_handler)

    def setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.working_dir,
            self.working_dir / 'downloads',
            self.working_dir / 'processed',
            self.working_dir / 'logs',
            self.working_dir / 'state',
            self.working_dir / 'reports'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Working directory structure created: {self.working_dir}")

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown signals"""
        self.logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def save_state(self):
        """Save current orchestration state"""
        try:
            state_data = {
                'stats': asdict(self.stats),
                'completed_counties': list(self.completed_counties),
                'failed_counties': list(self.failed_counties),
                'session_id': self.session_id,
                'last_save': datetime.now().isoformat()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)

            # Also save as latest progress
            with open(self.progress_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def load_existing_state(self):
        """Load existing orchestration state for recovery"""
        if self.progress_file.exists() and self.enable_recovery:
            try:
                with open(self.progress_file, 'r') as f:
                    state_data = json.load(f)

                # Restore completed counties
                self.completed_counties = set(state_data.get('completed_counties', []))
                self.failed_counties = set(state_data.get('failed_counties', []))

                self.logger.info(
                    f"Loaded existing state: {len(self.completed_counties)} completed, "
                    f"{len(self.failed_counties)} failed counties"
                )

            except Exception as e:
                self.logger.warning(f"Could not load existing state: {e}")

    def get_counties_to_process(self) -> List[str]:
        """Get list of counties to process based on mode and existing state"""
        if self.test_mode:
            # Use test counties in test mode
            all_counties = self.counties_manager.get_test_counties()[:3]
        else:
            # Use all counties in production mode
            all_counties = self.counties_manager.get_all_counties()

        # Filter out already completed counties if recovery is enabled
        if self.enable_recovery:
            counties_to_process = [
                county for county in all_counties
                if county not in self.completed_counties
            ]
        else:
            counties_to_process = all_counties

        self.stats.total_counties = len(counties_to_process)

        self.logger.info(
            f"Counties to process: {len(counties_to_process)} "
            f"(Total: {len(all_counties)}, Completed: {len(self.completed_counties)})"
        )

        return counties_to_process

    def process_single_county(self, county: str) -> Dict[str, Any]:
        """
        Process a single county through the complete pipeline

        Args:
            county: County name

        Returns:
            Processing results
        """
        county_start_time = datetime.now()

        result = {
            'county': county,
            'status': 'pending',
            'download_status': 'pending',
            'processing_status': 'pending',
            'upload_status': 'pending',
            'records_processed': 0,
            'records_uploaded': 0,
            'errors': [],
            'processing_time': 0.0,
            'start_time': county_start_time.isoformat()
        }

        try:
            self.logger.info(f"Starting pipeline for {county}")

            # Check for shutdown request
            if self.shutdown_requested:
                result['status'] = 'cancelled'
                return result

            # Phase 1: Download
            self.logger.info(f"{county}: Phase 1 - Downloading SDF file")
            download_status = self.downloader.download_county_sdf(county)

            if download_status.status == 'completed':
                result['download_status'] = 'completed'

                # Extract files
                if self.downloader.extract_sdf_files(county):
                    self.logger.info(f"{county}: SDF files extracted successfully")
                else:
                    raise Exception("Failed to extract SDF files")
            else:
                raise Exception(f"Download failed: {download_status.error_message}")

            # Check for shutdown request
            if self.shutdown_requested:
                result['status'] = 'cancelled'
                return result

            # Phase 2: Process CSV files
            self.logger.info(f"{county}: Phase 2 - Processing CSV data")

            # Find CSV files to process
            csv_files = download_status.csv_files or []
            if not csv_files:
                # Look for extracted files
                extract_dir = self.working_dir / 'downloads' / 'extracted' / county
                csv_files = list(extract_dir.glob('*.csv')) + list(extract_dir.glob('*.txt'))
                csv_files = [str(f) for f in csv_files]

            if not csv_files:
                raise Exception("No CSV files found for processing")

            # Process each CSV file
            all_processed_records = []
            for csv_file in csv_files:
                csv_path = Path(csv_file)

                self.logger.info(f"{county}: Processing {csv_path.name}")

                for chunk_idx, records_chunk in enumerate(self.processor.process_sdf_file(csv_path, county)):
                    all_processed_records.extend(records_chunk)
                    result['records_processed'] += len(records_chunk)

                    # Check for shutdown request
                    if self.shutdown_requested:
                        result['status'] = 'cancelled'
                        return result

            result['processing_status'] = 'completed'
            self.logger.info(f"{county}: Processed {result['records_processed']} records")

            # Check for shutdown request
            if self.shutdown_requested:
                result['status'] = 'cancelled'
                return result

            # Phase 3: Upload to Supabase
            self.logger.info(f"{county}: Phase 3 - Uploading to Supabase")

            if all_processed_records:
                upload_stats = self.uploader.upload_county_data(county, all_processed_records)

                result['upload_status'] = 'completed'
                result['records_uploaded'] = upload_stats.successful_inserts

                if upload_stats.errors > 0:
                    result['errors'].extend([
                        f"Upload errors: {upload_stats.errors}"
                    ])

                self.logger.info(
                    f"{county}: Uploaded {result['records_uploaded']}/{result['records_processed']} records"
                )
            else:
                result['errors'].append("No records to upload")

            # Mark as completed
            result['status'] = 'completed'

            # Update completed counties
            with self.recovery_lock:
                self.completed_counties.add(county)
                if county in self.failed_counties:
                    self.failed_counties.remove(county)

        except Exception as e:
            error_msg = f"Error processing {county}: {str(e)}"
            result['status'] = 'failed'
            result['errors'].append(error_msg)

            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())

            # Add to failed counties
            with self.recovery_lock:
                self.failed_counties.add(county)

        finally:
            # Calculate processing time
            result['processing_time'] = (datetime.now() - county_start_time).total_seconds()
            result['end_time'] = datetime.now().isoformat()

            # Update statistics
            if result['status'] == 'completed':
                self.stats.counties_completed += 1
                self.stats.total_records_processed += result['records_processed']
                self.stats.total_records_uploaded += result['records_uploaded']
            elif result['status'] == 'failed':
                self.stats.counties_failed += 1

            self.stats.total_errors += len(result['errors'])

            # Save state periodically
            self.save_state()

        return result

    def process_all_counties(self, counties: List[str]) -> Dict[str, Any]:
        """
        Process all counties with controlled concurrency

        Args:
            counties: List of counties to process

        Returns:
            Overall processing results
        """
        self.logger.info(f"Starting processing of {len(counties)} counties with {self.max_concurrent_counties} workers")

        self.stats.current_phase = 'processing'
        overall_results = {}

        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=self.max_concurrent_counties) as executor:
            # Submit all county processing tasks
            future_to_county = {
                executor.submit(self.process_single_county, county): county
                for county in counties
            }

            # Process completed counties
            for future in as_completed(future_to_county):
                if self.shutdown_requested:
                    self.logger.warning("Shutdown requested, cancelling remaining tasks")
                    break

                county = future_to_county[future]
                try:
                    result = future.result()
                    overall_results[county] = result

                    # Log progress
                    total_processed = self.stats.counties_completed + self.stats.counties_failed
                    progress_pct = (total_processed / self.stats.total_counties) * 100

                    self.logger.info(
                        f"Progress: {total_processed}/{self.stats.total_counties} counties "
                        f"({progress_pct:.1f}%) - {county}: {result['status']}"
                    )

                except Exception as e:
                    self.logger.error(f"Failed to get result for {county}: {e}")
                    overall_results[county] = {
                        'county': county,
                        'status': 'failed',
                        'errors': [str(e)]
                    }

        return overall_results

    def retry_failed_counties(self, max_retries: int = 2) -> Dict[str, Any]:
        """
        Retry processing failed counties

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            Retry results
        """
        if not self.failed_counties:
            self.logger.info("No failed counties to retry")
            return {}

        retry_results = {}

        for attempt in range(max_retries):
            if not self.failed_counties or self.shutdown_requested:
                break

            failed_list = list(self.failed_counties.copy())
            self.stats.recovery_attempts += 1

            self.logger.info(
                f"Retry attempt {attempt + 1}/{max_retries} for {len(failed_list)} failed counties"
            )

            # Process failed counties
            attempt_results = self.process_all_counties(failed_list)
            retry_results[f"attempt_{attempt + 1}"] = attempt_results

            # Count successes
            successes = sum(1 for r in attempt_results.values() if r.get('status') == 'completed')
            self.logger.info(f"Retry attempt {attempt + 1} completed: {successes} successes")

            if not self.failed_counties:
                self.logger.info("All counties processed successfully after retry")
                break

        return retry_results

    def generate_final_report(self, processing_results: Dict, retry_results: Dict = None) -> Dict:
        """
        Generate comprehensive final report

        Args:
            processing_results: Main processing results
            retry_results: Retry processing results

        Returns:
            Final report
        """
        self.stats.end_time = datetime.now().isoformat()
        start_dt = datetime.fromisoformat(self.stats.start_time)
        end_dt = datetime.fromisoformat(self.stats.end_time)
        self.stats.processing_time_hours = (end_dt - start_dt).total_seconds() / 3600

        # Calculate success rates
        total_attempted = self.stats.counties_completed + self.stats.counties_failed
        success_rate = (self.stats.counties_completed / total_attempted) * 100 if total_attempted > 0 else 0

        upload_rate = (
            (self.stats.total_records_uploaded / self.stats.total_records_processed) * 100
            if self.stats.total_records_processed > 0 else 0
        )

        final_report = {
            'session_info': {
                'session_id': self.session_id,
                'test_mode': self.test_mode,
                'start_time': self.stats.start_time,
                'end_time': self.stats.end_time,
                'processing_time_hours': self.stats.processing_time_hours
            },
            'summary': {
                'total_counties': self.stats.total_counties,
                'counties_completed': self.stats.counties_completed,
                'counties_failed': self.stats.counties_failed,
                'success_rate_percent': success_rate,
                'total_records_processed': self.stats.total_records_processed,
                'total_records_uploaded': self.stats.total_records_uploaded,
                'upload_success_rate_percent': upload_rate,
                'total_errors': self.stats.total_errors,
                'recovery_attempts': self.stats.recovery_attempts
            },
            'performance': {
                'records_per_hour': (
                    self.stats.total_records_processed / self.stats.processing_time_hours
                    if self.stats.processing_time_hours > 0 else 0
                ),
                'uploads_per_hour': (
                    self.stats.total_records_uploaded / self.stats.processing_time_hours
                    if self.stats.processing_time_hours > 0 else 0
                ),
                'counties_per_hour': (
                    self.stats.counties_completed / self.stats.processing_time_hours
                    if self.stats.processing_time_hours > 0 else 0
                )
            },
            'failed_counties': list(self.failed_counties),
            'completed_counties': list(self.completed_counties),
            'detailed_results': processing_results,
            'retry_results': retry_results or {},
            'statistics': asdict(self.stats)
        }

        # Save report
        report_file = self.working_dir / 'reports' / f'final_report_{self.session_id}.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)
            self.logger.info(f"Final report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"Error saving final report: {e}")

        return final_report

    def run_complete_pipeline(self) -> Dict:
        """
        Run the complete Florida SDF pipeline

        Returns:
            Final processing report
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info("FLORIDA SDF MASTER ORCHESTRATOR - STARTING")
            self.logger.info("=" * 80)
            self.logger.info(f"Session ID: {self.session_id}")
            self.logger.info(f"Test Mode: {self.test_mode}")
            self.logger.info(f"Recovery Enabled: {self.enable_recovery}")
            self.logger.info(f"Max Concurrent Counties: {self.max_concurrent_counties}")

            # Get counties to process
            counties_to_process = self.get_counties_to_process()

            if not counties_to_process:
                self.logger.info("No counties to process")
                return self.generate_final_report({})

            # Process all counties
            self.stats.current_phase = 'processing'
            processing_results = self.process_all_counties(counties_to_process)

            # Retry failed counties if enabled
            retry_results = None
            if self.enable_recovery and self.failed_counties and not self.shutdown_requested:
                self.stats.current_phase = 'recovery'
                retry_results = self.retry_failed_counties()

            # Generate final report
            self.stats.current_phase = 'completed'
            final_report = self.generate_final_report(processing_results, retry_results)

            # Log summary
            self.logger.info("=" * 80)
            self.logger.info("FLORIDA SDF MASTER ORCHESTRATOR - COMPLETED")
            self.logger.info("=" * 80)
            self.logger.info(f"Counties Completed: {self.stats.counties_completed}/{self.stats.total_counties}")
            self.logger.info(f"Records Processed: {self.stats.total_records_processed:,}")
            self.logger.info(f"Records Uploaded: {self.stats.total_records_uploaded:,}")
            self.logger.info(f"Processing Time: {self.stats.processing_time_hours:.2f} hours")
            self.logger.info(f"Success Rate: {final_report['summary']['success_rate_percent']:.1f}%")

            if self.failed_counties:
                self.logger.warning(f"Failed Counties: {list(self.failed_counties)}")

            return final_report

        except Exception as e:
            self.logger.error(f"Critical error in orchestrator: {e}")
            self.logger.debug(traceback.format_exc())

            # Generate error report
            return self.generate_final_report({}, {
                'critical_error': str(e),
                'traceback': traceback.format_exc()
            })

        finally:
            # Final state save
            self.save_state()


def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Florida SDF Master Orchestrator')

    parser.add_argument('--working-dir', type=str,
                       default="C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/FLORIDA_SDF",
                       help='Working directory for all operations')

    parser.add_argument('--max-concurrent', type=int, default=2,
                       help='Maximum concurrent counties to process')

    parser.add_argument('--no-recovery', action='store_true',
                       help='Disable recovery mechanisms')

    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with limited counties')

    parser.add_argument('--counties', nargs='+',
                       help='Specific counties to process (overrides other modes)')

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = FloridaSdfMasterOrchestrator(
        working_dir=args.working_dir,
        max_concurrent_counties=args.max_concurrent,
        enable_recovery=not args.no_recovery,
        test_mode=args.test_mode
    )

    # Run the pipeline
    if args.counties:
        # Process specific counties
        orchestrator.logger.info(f"Processing specific counties: {args.counties}")
        results = orchestrator.process_all_counties(args.counties)
        final_report = orchestrator.generate_final_report(results)
    else:
        # Run complete pipeline
        final_report = orchestrator.run_complete_pipeline()

    # Exit with appropriate code
    if final_report['summary']['counties_failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()