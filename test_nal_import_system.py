#!/usr/bin/env python3
"""
NAL Import System Testing and Demonstration Script
=================================================
Comprehensive testing suite for the NAL data import pipeline system.

This script demonstrates all components of the NAL import system:
- CSV parsing and validation
- Field mapping and transformation
- Batch import processing
- Error handling and recovery
- Performance monitoring
- Complete end-to-end import

Usage:
    python test_nal_import_system.py [options]
    
Options:
    --csv-file: Path to NAL CSV file (default: TEMP/NAL16P202501.csv)
    --mode: Test mode (validate|preview|import|demo) (default: demo)
    --batch-size: Batch size for processing (default: 1000)
    --sample-size: Sample size for validation (default: 100)
    --dry-run: Run validation only, no import
"""

import asyncio
import logging
import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import NAL agents
try:
    from apps.agents import (
        NALImportOrchestrator, NALCSVParserAgent, NALMappingAgent,
        NALBatchImportAgent, NALErrorRecoveryAgent, NALValidationAgent,
        NALMonitoringAgent, AgentConfig, ImportStatus
    )
    print("✅ NAL Import Agent System loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import NAL agents: {e}")
    sys.exit(1)

# Configure logging
def setup_logging():
    """Configure comprehensive logging for testing"""
    
    # Create logs directory
    log_dir = Path("test_logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_file = log_dir / f"nal_import_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"NAL Import System Test Started")
    logger.info(f"Log file: {log_file}")
    
    return logger

async def test_csv_parser(csv_file_path: str, logger: logging.Logger):
    """Test CSV parser agent functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING CSV PARSER AGENT")
    logger.info("=" * 60)
    
    try:
        # Initialize parser
        parser = NALCSVParserAgent(csv_file_path, chunk_size=100)
        
        # Test format detection
        logger.info("Testing format detection...")
        format_info = await parser.detect_encoding_and_format()
        logger.info(f"Format detected: {format_info}")
        
        # Test header parsing
        logger.info("Testing header parsing...")
        header_info = await parser.parse_header()
        logger.info(f"Header parsed: {header_info.field_count} fields")
        logger.info(f"First 10 fields: {header_info.fields[:10]}")
        
        # Test record counting
        logger.info("Testing record counting...")
        record_count = await parser.get_record_count()
        logger.info(f"Total records: {record_count:,}")
        
        # Test structure validation
        logger.info("Testing CSV validation...")
        validation = await parser.validate_csv_structure(100)
        logger.info(f"Validation result: Valid={validation['is_valid']}")
        
        if validation['errors']:
            logger.warning(f"Validation errors: {validation['errors']}")
        if validation['warnings']:
            logger.warning(f"Validation warnings: {validation['warnings']}")
        
        # Test chunked reading
        logger.info("Testing chunked reading...")
        chunk_count = 0
        total_test_records = 0
        
        async for chunk in parser.read_chunks():
            chunk_count += 1
            total_test_records += len(chunk)
            logger.info(f"Processed chunk {chunk_count}: {len(chunk)} records")
            
            if chunk_count >= 3:  # Test first 3 chunks
                break
        
        logger.info(f"CSV Parser Test Completed: {chunk_count} chunks, {total_test_records} records processed")
        
        return {
            'success': True,
            'header_fields': header_info.field_count,
            'total_records': record_count,
            'validation_passed': validation['is_valid'],
            'chunks_tested': chunk_count
        }
        
    except Exception as e:
        logger.error(f"CSV Parser test failed: {e}")
        return {'success': False, 'error': str(e)}

async def test_field_mapping(logger: logging.Logger):
    """Test field mapping agent functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING FIELD MAPPING AGENT")
    logger.info("=" * 60)
    
    try:
        # Initialize mapping agent
        mapper = NALMappingAgent()
        
        # Test comprehensive mapping creation
        logger.info("Testing comprehensive field mapping...")
        
        # Simulate NAL fields (first 10 for testing)
        nal_fields = [
            'CO_NO', 'PARCEL_ID', 'FILE_T', 'ASMNT_YR', 'JV', 'AV_SD', 'TV_SD',
            'OWN_NAME', 'PHY_ADDR1', 'PHY_CITY', 'DOR_UC', 'LND_VAL', 'EXMPT_01'
        ]
        
        field_mapping = await mapper.create_comprehensive_mapping(nal_fields)
        
        logger.info("Field mapping created:")
        for table, fields in field_mapping.items():
            logger.info(f"  {table}: {len(fields)} fields")
        
        # Test mapping coverage
        logger.info("Testing mapping coverage...")
        coverage_report = await mapper.validate_mapping_coverage(nal_fields, field_mapping)
        logger.info(f"Coverage: {coverage_report['coverage_percentage']:.1f}%")
        
        if coverage_report['unmapped_fields']:
            logger.warning(f"Unmapped fields: {coverage_report['unmapped_fields']}")
        
        # Test data transformation
        logger.info("Testing data transformation...")
        sample_record = {
            'CO_NO': '016',
            'PARCEL_ID': '123456789',
            'FILE_T': 'R',
            'ASMNT_YR': '2025',
            'JV': '250000',
            'AV_SD': '245000',
            'TV_SD': '240000',
            'OWN_NAME': 'TEST OWNER',
            'PHY_ADDR1': '123 TEST ST',
            'PHY_CITY': 'FORT LAUDERDALE',
            'DOR_UC': '001',
            'LND_VAL': '100000',
            'EXMPT_01': '50000'
        }
        
        transformed_data = await mapper.transform_batch_data([sample_record], field_mapping)
        
        logger.info("Data transformation completed:")
        for table, records in transformed_data.items():
            logger.info(f"  {table}: {len(records)} records")
        
        logger.info("Field Mapping Test Completed")
        
        return {
            'success': True,
            'tables_mapped': len(field_mapping),
            'coverage_percentage': coverage_report['coverage_percentage'],
            'transformation_success': len(transformed_data) > 0
        }
        
    except Exception as e:
        logger.error(f"Field Mapping test failed: {e}")
        return {'success': False, 'error': str(e)}

async def test_validation_system(csv_file_path: str, logger: logging.Logger):
    """Test validation agent functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING VALIDATION AGENT")
    logger.info("=" * 60)
    
    try:
        # Initialize agents
        parser = NALCSVParserAgent(csv_file_path)
        validator = NALValidationAgent(sample_size=50)
        
        # Test data sample validation
        logger.info("Testing data sample validation...")
        validation_result = await validator.validate_data_sample(parser)
        
        logger.info(f"Validation completed:")
        logger.info(f"  Valid: {validation_result.is_valid}")
        logger.info(f"  Records validated: {validation_result.records_validated}")
        logger.info(f"  Passed: {validation_result.passed_validations}")
        logger.info(f"  Failed: {validation_result.failed_validations}")
        logger.info(f"  Processing time: {validation_result.processing_time:.2f}s")
        
        if validation_result.errors:
            logger.warning(f"Validation errors ({len(validation_result.errors)}):")
            for error in validation_result.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
        
        if validation_result.warnings:
            logger.info(f"Validation warnings ({len(validation_result.warnings)}):")
            for warning in validation_result.warnings[:3]:  # Show first 3 warnings
                logger.info(f"  - {warning}")
        
        # Test data integrity validation (placeholder)
        logger.info("Testing data integrity validation...")
        integrity_result = await validator.validate_data_integrity()
        
        logger.info(f"Data integrity check:")
        logger.info(f"  Valid: {integrity_result.is_valid}")
        logger.info(f"  Checks passed: {integrity_result.passed_validations}")
        logger.info(f"  Checks failed: {integrity_result.failed_validations}")
        
        logger.info("Validation System Test Completed")
        
        return {
            'success': True,
            'sample_validation_passed': validation_result.is_valid,
            'records_validated': validation_result.records_validated,
            'integrity_validation_passed': integrity_result.is_valid
        }
        
    except Exception as e:
        logger.error(f"Validation System test failed: {e}")
        return {'success': False, 'error': str(e)}

async def test_error_recovery_system(logger: logging.Logger):
    """Test error recovery agent functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING ERROR RECOVERY AGENT")
    logger.info("=" * 60)
    
    try:
        # Initialize error recovery agent
        recovery_agent = NALErrorRecoveryAgent(max_retries=2, retry_delay=0.1)
        
        # Test error classification and handling
        logger.info("Testing error classification...")
        
        # Simulate different types of errors
        test_errors = [
            (Exception("Database connection timeout"), {'component': 'database', 'operation': 'connect'}),
            (ValueError("Invalid CSV format"), {'component': 'parser', 'operation': 'parse_csv'}),
            (MemoryError("Out of memory"), {'component': 'system', 'operation': 'process_batch'})
        ]
        
        for error, context in test_errors:
            error_context = await recovery_agent.handle_error(error, context)
            logger.info(f"Error {error_context.error_id}:")
            logger.info(f"  Severity: {error_context.severity.value}")
            logger.info(f"  Component: {error_context.component}")
            logger.info(f"  Message: {error_context.error_message}")
        
        # Test batch failure recovery
        logger.info("Testing batch failure recovery...")
        
        sample_batch = [
            {'parcel_id': '123', 'owner_name': 'Test Owner 1'},
            {'parcel_id': '456', 'owner_name': 'Test Owner 2'}
        ]
        
        batch_error = Exception("Batch processing failed")
        recovery_result = await recovery_agent.handle_batch_failure(sample_batch, batch_error, 1)
        
        logger.info(f"Batch recovery result:")
        logger.info(f"  Success: {recovery_result.success}")
        logger.info(f"  Action taken: {recovery_result.action_taken.value}")
        logger.info(f"  Processing time: {recovery_result.processing_time:.2f}s")
        
        # Get recovery statistics
        stats = recovery_agent.get_recovery_stats()
        logger.info(f"Recovery statistics:")
        logger.info(f"  Total errors: {stats['recovery_stats']['total_errors']}")
        logger.info(f"  Recovered errors: {stats['recovery_stats']['recovered_errors']}")
        logger.info(f"  Success rate: {stats['recovery_success_rate']:.1f}%")
        
        logger.info("Error Recovery System Test Completed")
        
        return {
            'success': True,
            'errors_handled': len(test_errors),
            'batch_recovery_attempted': True,
            'recovery_success_rate': stats['recovery_success_rate']
        }
        
    except Exception as e:
        logger.error(f"Error Recovery System test failed: {e}")
        return {'success': False, 'error': str(e)}

async def test_monitoring_system(logger: logging.Logger):
    """Test monitoring agent functionality"""
    
    logger.info("=" * 60)
    logger.info("TESTING MONITORING AGENT")
    logger.info("=" * 60)
    
    try:
        # Initialize monitoring agent
        monitor = NALMonitoringAgent()
        
        # Test monitoring startup
        logger.info("Testing monitoring system startup...")
        await monitor.start_monitoring()
        
        # Wait for some metrics to be collected
        await asyncio.sleep(2)
        
        # Test metrics collection
        current_metrics = monitor.get_current_metrics()
        if current_metrics:
            logger.info(f"Current metrics collected:")
            logger.info(f"  Memory usage: {current_metrics.memory_usage_mb:.1f} MB")
            logger.info(f"  CPU usage: {current_metrics.cpu_usage_percent:.1f}%")
            logger.info(f"  Records processed: {current_metrics.records_processed}")
        else:
            logger.info("No metrics collected yet")
        
        # Test metrics summary
        logger.info("Testing metrics summary...")
        summary = monitor.get_metrics_summary(1)  # Last 1 minute
        
        if summary:
            logger.info(f"Metrics summary:")
            logger.info(f"  Data points: {summary.get('data_points', 0)}")
            perf = summary.get('performance', {})
            if perf:
                logger.info(f"  Avg records/sec: {perf.get('avg_records_per_second', 0):.1f}")
        
        # Test performance report
        logger.info("Testing performance report generation...")
        report = monitor.generate_performance_report()
        
        logger.info(f"Performance report generated:")
        logger.info(f"  Report timestamp: {report['report_timestamp']}")
        logger.info(f"  System info: {report['system_info']}")
        logger.info(f"  Recommendations: {len(report.get('recommendations', []))}")
        
        # Test alerts summary
        alerts_summary = monitor.get_alerts_summary()
        logger.info(f"Alerts summary: {alerts_summary['total_alerts']} total alerts")
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        logger.info("Monitoring System Test Completed")
        
        return {
            'success': True,
            'monitoring_started': True,
            'metrics_collected': current_metrics is not None,
            'report_generated': bool(report)
        }
        
    except Exception as e:
        logger.error(f"Monitoring System test failed: {e}")
        return {'success': False, 'error': str(e)}

async def run_demo_import(csv_file_path: str, logger: logging.Logger, dry_run: bool = True):
    """Run demonstration import pipeline"""
    
    logger.info("=" * 60)
    logger.info("RUNNING DEMO IMPORT PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Configuration for demo
        config = AgentConfig(
            batch_size=500,  # Small batch size for demo
            max_workers=2,   # Limited workers for demo
            chunk_size=1000,
            enable_parallel_tables=False  # Sequential for demo clarity
        )
        
        # Initialize orchestrator
        orchestrator = NALImportOrchestrator(csv_file_path, config)
        
        if dry_run:
            logger.info("DRY RUN MODE - No actual import to database")
            
            # Initialize agents for dry run testing
            await orchestrator.initialize_agents()
            
            # Test each step without database operations
            logger.info("Step 1: Parse and validate CSV...")
            await orchestrator._step_1_parse_and_validate()
            
            logger.info("Step 2: Create field mapping...")
            await orchestrator._step_2_create_field_mapping()
            
            logger.info("Demo completed successfully (dry run)")
            
            return {
                'success': True,
                'mode': 'dry_run',
                'total_records': orchestrator.status.total_records,
                'total_batches': orchestrator.status.total_batches
            }
        
        else:
            logger.info("FULL IMPORT MODE - This would import to database")
            logger.warning("Full import disabled in demo mode for safety")
            
            # For actual import, uncomment the following:
            # result = await orchestrator.run_import_pipeline()
            # return asdict(result)
            
            return {
                'success': True,
                'mode': 'demo_only',
                'message': 'Full import disabled for safety in demo'
            }
        
    except Exception as e:
        logger.error(f"Demo import failed: {e}")
        return {'success': False, 'error': str(e)}

async def generate_test_report(test_results: dict, logger: logging.Logger):
    """Generate comprehensive test report"""
    
    logger.info("=" * 60)
    logger.info("GENERATING TEST REPORT")
    logger.info("=" * 60)
    
    # Calculate overall success
    successful_tests = sum(1 for result in test_results.values() if result.get('success', False))
    total_tests = len(test_results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Create report
    report = {
        'test_timestamp': datetime.now().isoformat(),
        'test_summary': {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate_percent': success_rate
        },
        'test_results': test_results,
        'system_info': {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform
        },
        'recommendations': []
    }
    
    # Add recommendations based on results
    if success_rate == 100:
        report['recommendations'].append("All tests passed! System is ready for production use.")
    elif success_rate >= 80:
        report['recommendations'].append("Most tests passed. Review failed tests before production.")
    else:
        report['recommendations'].append("Multiple test failures detected. System requires fixes before use.")
    
    # Save report to file
    report_file = f"nal_import_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved to: {report_file}")
    except Exception as e:
        logger.error(f"Failed to save test report: {e}")
    
    # Log summary
    logger.info(f"TEST RESULTS SUMMARY:")
    logger.info(f"  Total tests: {total_tests}")
    logger.info(f"  Successful: {successful_tests}")
    logger.info(f"  Failed: {total_tests - successful_tests}")
    logger.info(f"  Success rate: {success_rate:.1f}%")
    
    # Log individual test results
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not result.get('success', False) and 'error' in result:
            logger.info(f"    Error: {result['error']}")
    
    return report

async def main():
    """Main test execution function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NAL Import System Testing")
    parser.add_argument('--csv-file', default='TEMP/NAL16P202501.csv', help='Path to NAL CSV file')
    parser.add_argument('--mode', choices=['validate', 'preview', 'import', 'demo'], default='demo', help='Test mode')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parser.add_argument('--sample-size', type=int, default=100, help='Sample size for validation')
    parser.add_argument('--dry-run', action='store_true', help='Run validation only, no import')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Validate CSV file path
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    logger.info(f"Starting NAL Import System Test")
    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Dry run: {args.dry_run}")
    
    start_time = time.time()
    test_results = {}
    
    try:
        if args.mode in ['demo', 'validate']:
            # Test CSV Parser
            logger.info("Testing CSV Parser Agent...")
            test_results['csv_parser'] = await test_csv_parser(str(csv_path), logger)
            
            # Test Field Mapping
            logger.info("Testing Field Mapping Agent...")
            test_results['field_mapping'] = await test_field_mapping(logger)
            
            # Test Validation System
            logger.info("Testing Validation System...")
            test_results['validation'] = await test_validation_system(str(csv_path), logger)
            
            # Test Error Recovery System
            logger.info("Testing Error Recovery System...")
            test_results['error_recovery'] = await test_error_recovery_system(logger)
            
            # Test Monitoring System
            logger.info("Testing Monitoring System...")
            test_results['monitoring'] = await test_monitoring_system(logger)
        
        if args.mode in ['demo', 'import']:
            # Run Demo Import
            logger.info("Running Demo Import...")
            test_results['demo_import'] = await run_demo_import(str(csv_path), logger, args.dry_run)
        
        # Generate test report
        total_time = time.time() - start_time
        logger.info(f"All tests completed in {total_time:.2f} seconds")
        
        await generate_test_report(test_results, logger)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the main test function
    asyncio.run(main())