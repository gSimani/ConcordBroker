#!/usr/bin/env python3
"""
NAL Data Import Orchestrator Agent
==================================
Master coordination agent for importing 753,242+ Broward County NAL records
with all 165 fields into optimized 7-table Supabase architecture.

Performance Target: Import complete dataset within 30-60 minutes
Architecture: Agent-based pipeline with parallel processing and error recovery
"""

import asyncio
import logging
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nal_import_orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ImportStatus:
    """Track import pipeline status"""
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_batch: int = 0
    total_batches: int = 0
    errors: List[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Calculate elapsed time"""
        if self.start_time is None:
            return None
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate time remaining based on current progress"""
        if self.processed_records == 0 or self.total_records == 0:
            return None
        
        elapsed = self.elapsed_time
        if elapsed is None:
            return None
        
        remaining_records = self.total_records - self.processed_records
        time_per_record = elapsed.total_seconds() / self.processed_records
        estimated_seconds = remaining_records * time_per_record
        
        return timedelta(seconds=estimated_seconds)

@dataclass
class AgentConfig:
    """Configuration for import agents"""
    batch_size: int = 2000
    max_workers: int = mp.cpu_count()
    max_retries: int = 3
    retry_delay: float = 1.0
    chunk_size: int = 10000
    memory_limit_mb: int = 1024
    enable_parallel_tables: bool = True
    validation_sample_size: int = 100

class NALImportOrchestrator:
    """
    Master orchestrator for NAL data import pipeline
    
    Coordinates all import agents and manages the complete import process
    from CSV parsing through final database insertion with error handling
    and performance monitoring.
    """
    
    def __init__(self, csv_file_path: str, config: AgentConfig = None):
        self.csv_file_path = Path(csv_file_path)
        self.config = config or AgentConfig()
        self.status = ImportStatus()
        
        # Validate file exists
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"NAL CSV file not found: {csv_file_path}")
        
        # Initialize agent references
        self.csv_parser_agent = None
        self.validation_agent = None
        self.mapping_agent = None
        self.batch_import_agent = None
        self.error_recovery_agent = None
        self.monitoring_agent = None
        
        # Performance tracking
        self.performance_metrics = {
            'parsing_time': 0,
            'validation_time': 0,
            'transformation_time': 0,
            'import_time': 0,
            'total_time': 0,
            'throughput_records_per_second': 0,
            'memory_usage_peak_mb': 0
        }
        
        # Import state management
        self.checkpoint_dir = Path("nal_import_checkpoints")
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        logger.info(f"NAL Import Orchestrator initialized")
        logger.info(f"Source file: {self.csv_file_path}")
        logger.info(f"Configuration: {asdict(self.config)}")
    
    async def initialize_agents(self):
        """Initialize all specialized import agents"""
        try:
            logger.info("Initializing import agents...")
            
            # Import agent modules dynamically
            from .nal_csv_parser_agent import NALCSVParserAgent
            from .nal_validation_agent import NALValidationAgent
            from .nal_mapping_agent import NALMappingAgent
            from .nal_batch_import_agent import NALBatchImportAgent
            from .nal_error_recovery_agent import NALErrorRecoveryAgent
            from .nal_monitoring_agent import NALMonitoringAgent
            
            # Initialize agents
            self.csv_parser_agent = NALCSVParserAgent(
                csv_file_path=str(self.csv_file_path),
                chunk_size=self.config.chunk_size
            )
            
            self.validation_agent = NALValidationAgent(
                sample_size=self.config.validation_sample_size
            )
            
            self.mapping_agent = NALMappingAgent()
            
            self.batch_import_agent = NALBatchImportAgent(
                batch_size=self.config.batch_size,
                max_workers=self.config.max_workers,
                enable_parallel_tables=self.config.enable_parallel_tables
            )
            
            self.error_recovery_agent = NALErrorRecoveryAgent(
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay
            )
            
            self.monitoring_agent = NALMonitoringAgent()
            
            logger.info("All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def run_import_pipeline(self) -> ImportStatus:
        """
        Execute the complete NAL import pipeline
        
        Returns:
            ImportStatus with complete import results and metrics
        """
        self.status.start_time = datetime.now()
        
        try:
            logger.info("=" * 60)
            logger.info("STARTING NAL DATA IMPORT PIPELINE")
            logger.info("=" * 60)
            
            # Initialize all agents
            await self.initialize_agents()
            
            # Step 1: Parse and validate CSV structure
            await self._step_1_parse_and_validate()
            
            # Step 2: Create comprehensive field mapping
            await self._step_2_create_field_mapping()
            
            # Step 3: Deploy database schema
            await self._step_3_deploy_schema()
            
            # Step 4: Process data in optimized batches
            await self._step_4_batch_processing()
            
            # Step 5: Validate import results
            await self._step_5_validate_results()
            
            # Step 6: Generate final report
            await self._step_6_generate_report()
            
            self.status.end_time = datetime.now()
            logger.info("NAL import pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Import pipeline failed: {e}")
            self.status.errors.append(str(e))
            
            # Attempt recovery
            try:
                await self.error_recovery_agent.handle_critical_failure(e, self.status)
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
                self.status.errors.append(f"Recovery failed: {recovery_error}")
            
            raise
        
        finally:
            if self.status.end_time is None:
                self.status.end_time = datetime.now()
            
            # Save final checkpoint
            await self._save_checkpoint()
            
            return self.status
    
    async def _step_1_parse_and_validate(self):
        """Step 1: Parse CSV and validate data structure"""
        logger.info("Step 1: Parsing and validating NAL CSV data...")
        start_time = time.time()
        
        try:
            # Parse CSV header to understand structure
            header_info = await self.csv_parser_agent.parse_header()
            logger.info(f"CSV contains {header_info['field_count']} fields")
            
            # Get total record count
            self.status.total_records = await self.csv_parser_agent.get_record_count()
            logger.info(f"Total records to import: {self.status.total_records:,}")
            
            # Calculate total batches
            self.status.total_batches = (self.status.total_records + self.config.batch_size - 1) // self.config.batch_size
            logger.info(f"Will process {self.status.total_batches} batches of {self.config.batch_size} records")
            
            # Validate data sample
            sample_validation = await self.validation_agent.validate_data_sample(
                self.csv_parser_agent
            )
            
            if not sample_validation['is_valid']:
                raise ValueError(f"Data validation failed: {sample_validation['errors']}")
            
            logger.info(f"Data validation passed: {sample_validation['summary']}")
            
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            raise
        
        finally:
            self.performance_metrics['parsing_time'] = time.time() - start_time
    
    async def _step_2_create_field_mapping(self):
        """Step 2: Create comprehensive field mapping for all 165 NAL fields"""
        logger.info("Step 2: Creating NAL field mapping to database tables...")
        start_time = time.time()
        
        try:
            # Get CSV header fields
            header_info = await self.csv_parser_agent.parse_header()
            nal_fields = header_info['fields']
            
            # Create comprehensive mapping
            field_mapping = await self.mapping_agent.create_comprehensive_mapping(nal_fields)
            
            # Validate mapping coverage
            coverage_report = await self.mapping_agent.validate_mapping_coverage(
                nal_fields, field_mapping
            )
            
            if coverage_report['unmapped_fields']:
                logger.warning(f"Unmapped fields: {coverage_report['unmapped_fields']}")
            
            logger.info(f"Field mapping created successfully:")
            logger.info(f"- Core properties: {len(field_mapping['florida_properties_core'])} fields")
            logger.info(f"- Valuations: {len(field_mapping['property_valuations'])} fields")
            logger.info(f"- Exemptions: {len(field_mapping['property_exemptions'])} fields")
            logger.info(f"- Characteristics: {len(field_mapping['property_characteristics'])} fields")
            logger.info(f"- Sales: {len(field_mapping['property_sales_enhanced'])} fields")
            logger.info(f"- Addresses: {len(field_mapping['property_addresses'])} fields")
            logger.info(f"- Admin data: {len(field_mapping['property_admin_data'])} fields")
            
            # Save mapping for other agents
            self.field_mapping = field_mapping
            
        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            raise
        
        finally:
            self.performance_metrics['validation_time'] = time.time() - start_time
    
    async def _step_3_deploy_schema(self):
        """Step 3: Deploy optimized database schema"""
        logger.info("Step 3: Deploying database schema...")
        
        try:
            # Deploy schema using batch import agent
            await self.batch_import_agent.deploy_database_schema()
            logger.info("Database schema deployed successfully")
            
        except Exception as e:
            logger.error(f"Step 3 failed: {e}")
            raise
    
    async def _step_4_batch_processing(self):
        """Step 4: Process data in optimized batches with parallel execution"""
        logger.info("Step 4: Processing data in optimized batches...")
        start_time = time.time()
        
        try:
            batch_number = 0
            
            # Process data in chunks
            async for data_chunk in self.csv_parser_agent.read_chunks():
                batch_number += 1
                self.status.current_batch = batch_number
                
                logger.info(f"Processing batch {batch_number}/{self.status.total_batches}")
                
                # Transform data using mapping agent
                transformed_data = await self.mapping_agent.transform_batch_data(
                    data_chunk, self.field_mapping
                )
                
                # Import batch with error handling
                try:
                    batch_result = await self.batch_import_agent.import_batch(
                        transformed_data, batch_number
                    )
                    
                    # Update status
                    self.status.processed_records += batch_result['processed']
                    self.status.successful_records += batch_result['successful']
                    self.status.failed_records += batch_result['failed']
                    
                    if batch_result['errors']:
                        self.status.errors.extend(batch_result['errors'])
                    
                    # Log progress
                    progress_pct = (self.status.processed_records / self.status.total_records) * 100
                    logger.info(f"Progress: {progress_pct:.1f}% - Batch {batch_number} completed")
                    logger.info(f"Success rate: {self.status.success_rate:.1f}%")
                    
                    if self.status.estimated_time_remaining:
                        logger.info(f"Estimated time remaining: {self.status.estimated_time_remaining}")
                    
                except Exception as batch_error:
                    logger.error(f"Batch {batch_number} failed: {batch_error}")
                    
                    # Try error recovery
                    recovery_result = await self.error_recovery_agent.handle_batch_failure(
                        data_chunk, batch_error, batch_number
                    )
                    
                    if recovery_result['recovered']:
                        logger.info(f"Batch {batch_number} recovered successfully")
                        self.status.processed_records += recovery_result['processed']
                        self.status.successful_records += recovery_result['successful']
                    else:
                        logger.error(f"Batch {batch_number} recovery failed")
                        self.status.failed_records += len(data_chunk)
                        self.status.errors.append(f"Batch {batch_number} failed and recovery unsuccessful")
                
                # Save checkpoint every 10 batches
                if batch_number % 10 == 0:
                    await self._save_checkpoint()
                
                # Memory management - force garbage collection
                import gc
                gc.collect()
        
        except Exception as e:
            logger.error(f"Step 4 failed: {e}")
            raise
        
        finally:
            self.performance_metrics['import_time'] = time.time() - start_time
    
    async def _step_5_validate_results(self):
        """Step 5: Validate import results and data integrity"""
        logger.info("Step 5: Validating import results...")
        
        try:
            # Validate record counts
            validation_result = await self.batch_import_agent.validate_import_results()
            
            logger.info(f"Import validation results:")
            logger.info(f"- Expected records: {self.status.total_records:,}")
            logger.info(f"- Successfully imported: {self.status.successful_records:,}")
            logger.info(f"- Failed records: {self.status.failed_records:,}")
            logger.info(f"- Success rate: {self.status.success_rate:.1f}%")
            
            # Perform data integrity checks
            integrity_result = await self.validation_agent.validate_data_integrity()
            
            if not integrity_result['is_valid']:
                logger.warning(f"Data integrity issues found: {integrity_result['issues']}")
            else:
                logger.info("Data integrity validation passed")
            
        except Exception as e:
            logger.error(f"Step 5 failed: {e}")
            raise
    
    async def _step_6_generate_report(self):
        """Step 6: Generate comprehensive import report"""
        logger.info("Step 6: Generating final import report...")
        
        try:
            # Calculate final performance metrics
            total_time = self.status.elapsed_time.total_seconds()
            self.performance_metrics['total_time'] = total_time
            self.performance_metrics['throughput_records_per_second'] = (
                self.status.successful_records / total_time if total_time > 0 else 0
            )
            
            # Generate comprehensive report
            report = {
                'import_summary': {
                    'source_file': str(self.csv_file_path),
                    'total_records': self.status.total_records,
                    'successful_records': self.status.successful_records,
                    'failed_records': self.status.failed_records,
                    'success_rate_pct': self.status.success_rate,
                    'total_time_seconds': total_time,
                    'start_time': self.status.start_time.isoformat(),
                    'end_time': self.status.end_time.isoformat()
                },
                'performance_metrics': self.performance_metrics,
                'configuration': asdict(self.config),
                'errors': self.status.errors,
                'field_mapping_summary': {
                    table: len(fields) for table, fields in self.field_mapping.items()
                } if hasattr(self, 'field_mapping') else {}
            }
            
            # Save report to file
            report_file = self.checkpoint_dir / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Import report saved to: {report_file}")
            
            # Log summary
            logger.info("=" * 60)
            logger.info("NAL IMPORT PIPELINE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total records processed: {self.status.total_records:,}")
            logger.info(f"Successfully imported: {self.status.successful_records:,}")
            logger.info(f"Failed records: {self.status.failed_records:,}")
            logger.info(f"Success rate: {self.status.success_rate:.1f}%")
            logger.info(f"Total time: {timedelta(seconds=total_time)}")
            logger.info(f"Throughput: {self.performance_metrics['throughput_records_per_second']:.0f} records/second")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Step 6 failed: {e}")
            # Don't raise - report generation failure shouldn't fail the import
    
    async def _save_checkpoint(self):
        """Save import progress checkpoint"""
        try:
            checkpoint = {
                'status': asdict(self.status),
                'performance_metrics': self.performance_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.status.current_batch:06d}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2, default=str)
            
            logger.debug(f"Checkpoint saved: {checkpoint_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
    
    async def resume_from_checkpoint(self, checkpoint_file: str) -> bool:
        """Resume import from saved checkpoint"""
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            # Restore status
            status_data = checkpoint['status']
            self.status = ImportStatus(**{
                k: v for k, v in status_data.items()
                if k in ImportStatus.__dataclass_fields__
            })
            
            # Restore performance metrics
            self.performance_metrics.update(checkpoint['performance_metrics'])
            
            logger.info(f"Resumed from checkpoint: {checkpoint_file}")
            logger.info(f"Progress: {self.status.current_batch}/{self.status.total_batches} batches")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume from checkpoint: {e}")
            return False

# CLI Interface
async def main():
    """Main entry point for NAL import orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NAL Data Import Orchestrator")
    parser.add_argument("csv_file", help="Path to NAL CSV file")
    parser.add_argument("--batch-size", type=int, default=2000, help="Batch size for processing")
    parser.add_argument("--max-workers", type=int, default=mp.cpu_count(), help="Maximum worker threads")
    parser.add_argument("--resume", help="Resume from checkpoint file")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without importing")
    
    args = parser.parse_args()
    
    # Create configuration
    config = AgentConfig(
        batch_size=args.batch_size,
        max_workers=args.max_workers
    )
    
    # Initialize orchestrator
    orchestrator = NALImportOrchestrator(args.csv_file, config)
    
    try:
        if args.resume:
            await orchestrator.resume_from_checkpoint(args.resume)
        
        if args.dry_run:
            logger.info("Dry run mode - validating configuration only")
            await orchestrator.initialize_agents()
            logger.info("Configuration validation successful")
        else:
            # Run full import pipeline
            status = await orchestrator.run_import_pipeline()
            
            # Exit with error code if import failed
            if status.success_rate < 95.0:
                logger.error(f"Import success rate below threshold: {status.success_rate:.1f}%")
                sys.exit(1)
            
            logger.info("NAL import completed successfully!")
    
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())