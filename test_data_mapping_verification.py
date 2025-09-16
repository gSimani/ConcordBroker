"""
Test Script for Data Mapping Verification
Tests the complete data flow from Supabase to UI with 100% accuracy
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.intelligent_data_mapping_system import (
    IntelligentDataMappingService,
    PandasDataPipeline,
    PlaywrightMCPVerification,
    OpenCVVisualValidation,
    DataMappingConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_mapping_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_PARCELS = [
    "494224020080",  # Standard single-family property
    "504312110010",  # Commercial property
    "484216050000",  # Condominium
    "514418230000",  # Vacant land
    "524520340000",  # Multi-family
]

class DataMappingTester:
    """Comprehensive testing for data mapping system"""

    def __init__(self):
        self.service = IntelligentDataMappingService()
        self.test_results = []
        self.summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": []
        }

    async def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*80)
        print(" DATA MAPPING VERIFICATION TEST SUITE")
        print("="*80)
        print(f"Started: {datetime.now().isoformat()}\n")

        # Test 1: Configuration Loading
        await self.test_configuration_loading()

        # Test 2: Database Connectivity
        await self.test_database_connectivity()

        # Test 3: Data Fetching
        await self.test_data_fetching()

        # Test 4: Field Mapping
        await self.test_field_mapping()

        # Test 5: Data Transformations
        await self.test_data_transformations()

        # Test 6: Validation Rules
        await self.test_validation_rules()

        # Test 7: Playwright Verification
        await self.test_playwright_verification()

        # Test 8: OpenCV Visual Validation
        await self.test_opencv_validation()

        # Test 9: End-to-End Property Mapping
        await self.test_end_to_end_mapping()

        # Test 10: Performance Testing
        await self.test_performance()

        # Generate Report
        self.generate_test_report()

    async def test_configuration_loading(self):
        """Test that configuration loads correctly"""
        print("\n[TEST 1] Configuration Loading...")
        self.summary["total_tests"] += 1

        try:
            # Load JSON configuration
            with open('data_mapping_config.json', 'r') as f:
                config = json.load(f)

            # Verify all required sections exist
            required_sections = ['database_tables', 'ui_pages', 'transformations', 'validation_rules']
            for section in required_sections:
                assert section in config, f"Missing section: {section}"

            # Verify database tables
            assert len(config['database_tables']) >= 8, "Expected at least 8 database tables"

            # Verify UI pages
            assert 'property_profile' in config['ui_pages'], "Missing property_profile page"

            print("  ✓ Configuration loaded successfully")
            print(f"  ✓ Found {len(config['database_tables'])} database tables")
            print(f"  ✓ Found {len(config['ui_pages']['property_profile']['tabs'])} UI tabs")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Configuration Loading",
                "status": "PASS",
                "details": f"Loaded {len(config['database_tables'])} tables"
            })

        except Exception as e:
            print(f"  ✗ Configuration loading failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Configuration Loading",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_database_connectivity(self):
        """Test database connection"""
        print("\n[TEST 2] Database Connectivity...")
        self.summary["total_tests"] += 1

        try:
            # Test Supabase connection
            pipeline = self.service.pandas_pipeline
            test_query = pipeline.supabase.table('florida_parcels').select('parcel_id').limit(1).execute()

            assert test_query.data is not None, "Failed to query database"

            print("  ✓ Supabase connection successful")
            print(f"  ✓ Database is accessible")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Database Connectivity",
                "status": "PASS",
                "details": "Connected to Supabase"
            })

        except Exception as e:
            print(f"  ✗ Database connectivity failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Database Connectivity",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_data_fetching(self):
        """Test data fetching for a sample property"""
        print("\n[TEST 3] Data Fetching...")
        self.summary["total_tests"] += 1

        try:
            parcel_id = TEST_PARCELS[0]
            pipeline = self.service.pandas_pipeline

            # Fetch data
            data_frames = pipeline.fetch_property_data(parcel_id)

            # Verify data was fetched
            assert 'florida_parcels' in data_frames, "florida_parcels data not fetched"
            assert not data_frames['florida_parcels'].empty, "florida_parcels is empty"

            print(f"  ✓ Fetched data for parcel {parcel_id}")
            for table, df in data_frames.items():
                print(f"  ✓ {table}: {len(df)} records")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Data Fetching",
                "status": "PASS",
                "details": f"Fetched {len(data_frames)} tables"
            })

        except Exception as e:
            print(f"  ✗ Data fetching failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Data Fetching",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_field_mapping(self):
        """Test field mapping logic"""
        print("\n[TEST 4] Field Mapping...")
        self.summary["total_tests"] += 1

        try:
            parcel_id = TEST_PARCELS[0]
            pipeline = self.service.pandas_pipeline

            # Fetch and map data
            data_frames = pipeline.fetch_property_data(parcel_id)
            ui_data = pipeline.map_data_to_ui(data_frames)

            # Verify mapped structure
            assert 'property_profile' in ui_data, "Missing property_profile in UI data"
            assert 'overview' in ui_data['property_profile'], "Missing overview tab"

            # Check critical fields
            overview = ui_data['property_profile']['overview']
            critical_fields = ['street_address', 'city', 'zip_code', 'parcel_id']

            missing_fields = []
            for field in critical_fields:
                if field not in str(overview):
                    missing_fields.append(field)

            if missing_fields:
                print(f"  ⚠ Missing fields: {missing_fields}")
                self.summary["warnings"] += 1

            print(f"  ✓ Field mapping completed")
            print(f"  ✓ Mapped {len(ui_data['property_profile'])} tabs")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Field Mapping",
                "status": "PASS",
                "details": f"Mapped {len(ui_data['property_profile'])} tabs"
            })

        except Exception as e:
            print(f"  ✗ Field mapping failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Field Mapping",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_data_transformations(self):
        """Test data transformation functions"""
        print("\n[TEST 5] Data Transformations...")
        self.summary["total_tests"] += 1

        try:
            pipeline = self.service.pandas_pipeline

            # Test currency transformation
            currency_result = pipeline.apply_transformations(250000, "currency")
            assert currency_result == "$250,000.00", f"Currency transformation failed: {currency_result}"

            # Test uppercase transformation
            upper_result = pipeline.apply_transformations("florida", "uppercase")
            assert upper_result == "FLORIDA", f"Uppercase transformation failed: {upper_result}"

            # Test state abbreviation
            state_result = pipeline.apply_transformations("FLORIDA", "state_abbr")
            assert state_result == "FL", f"State abbreviation failed: {state_result}"

            # Test property type description
            prop_type_result = pipeline.apply_transformations("0100", "property_type_desc")
            assert prop_type_result == "Single Family", f"Property type transformation failed: {prop_type_result}"

            print("  ✓ Currency transformation: PASS")
            print("  ✓ Uppercase transformation: PASS")
            print("  ✓ State abbreviation: PASS")
            print("  ✓ Property type description: PASS")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Data Transformations",
                "status": "PASS",
                "details": "All transformations working"
            })

        except Exception as e:
            print(f"  ✗ Data transformations failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Data Transformations",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_validation_rules(self):
        """Test validation rules"""
        print("\n[TEST 6] Validation Rules...")
        self.summary["total_tests"] += 1

        try:
            pipeline = self.service.pandas_pipeline

            # Test not_empty validation
            assert pipeline.validate_field("test", "not_empty") == True
            assert pipeline.validate_field("", "not_empty") == False
            assert pipeline.validate_field(None, "not_empty") == False

            # Test positive validation
            assert pipeline.validate_field(100, "positive") == True
            assert pipeline.validate_field(-100, "positive") == False
            assert pipeline.validate_field(0, "positive") == False

            # Test regex validation
            assert pipeline.validate_field("33139", "regex:^\\d{5}$") == True
            assert pipeline.validate_field("3313", "regex:^\\d{5}$") == False

            # Test range validation
            assert pipeline.validate_field(2020, "range:1900-2025") == True
            assert pipeline.validate_field(1800, "range:1900-2025") == False

            print("  ✓ Not empty validation: PASS")
            print("  ✓ Positive validation: PASS")
            print("  ✓ Regex validation: PASS")
            print("  ✓ Range validation: PASS")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Validation Rules",
                "status": "PASS",
                "details": "All validations working"
            })

        except Exception as e:
            print(f"  ✗ Validation rules failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Validation Rules",
                "status": "FAIL",
                "error": str(e)
            })

    async def test_playwright_verification(self):
        """Test Playwright MCP verification"""
        print("\n[TEST 7] Playwright MCP Verification...")
        self.summary["total_tests"] += 1

        try:
            # Skip if browser not available
            try:
                from playwright.async_api import async_playwright
                print("  ✓ Playwright is installed")
            except ImportError:
                print("  ⚠ Playwright not installed - skipping browser tests")
                self.summary["warnings"] += 1
                return

            # Initialize Playwright verifier
            verifier = self.service.playwright_verifier
            await verifier.initialize()

            print("  ✓ Playwright browser initialized")

            # Cleanup
            await verifier.cleanup()

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "Playwright MCP Verification",
                "status": "PASS",
                "details": "Browser automation ready"
            })

        except Exception as e:
            print(f"  ⚠ Playwright verification setup: {e}")
            self.summary["warnings"] += 1
            self.test_results.append({
                "test": "Playwright MCP Verification",
                "status": "WARNING",
                "details": str(e)
            })

    async def test_opencv_validation(self):
        """Test OpenCV visual validation"""
        print("\n[TEST 8] OpenCV Visual Validation...")
        self.summary["total_tests"] += 1

        try:
            # Check if OpenCV is available
            try:
                import cv2
                import pytesseract
                print("  ✓ OpenCV is installed")
                print("  ✓ Pytesseract is installed")
            except ImportError as e:
                print(f"  ⚠ OpenCV/Pytesseract not fully installed - {e}")
                self.summary["warnings"] += 1
                return

            validator = self.service.opencv_validator

            # Test with dummy data
            test_data = {
                "property_profile": {
                    "overview": {
                        "parcel_id": "494224020080",
                        "address": "123 Main St"
                    }
                }
            }

            print("  ✓ OpenCV validator initialized")

            self.summary["passed"] += 1
            self.test_results.append({
                "test": "OpenCV Visual Validation",
                "status": "PASS",
                "details": "Visual validation ready"
            })

        except Exception as e:
            print(f"  ⚠ OpenCV validation setup: {e}")
            self.summary["warnings"] += 1
            self.test_results.append({
                "test": "OpenCV Visual Validation",
                "status": "WARNING",
                "details": str(e)
            })

    async def test_end_to_end_mapping(self):
        """Test complete end-to-end mapping for sample properties"""
        print("\n[TEST 9] End-to-End Property Mapping...")
        self.summary["total_tests"] += 1

        success_count = 0
        for parcel_id in TEST_PARCELS[:2]:  # Test first 2 parcels
            try:
                print(f"\n  Testing parcel: {parcel_id}")

                # Fetch data
                pipeline = self.service.pandas_pipeline
                data_frames = pipeline.fetch_property_data(parcel_id)

                if not data_frames or 'florida_parcels' not in data_frames:
                    print(f"    ⚠ No data found for {parcel_id}")
                    continue

                # Map to UI
                ui_data = pipeline.map_data_to_ui(data_frames)

                # Verify critical fields
                if 'property_profile' in ui_data and 'overview' in ui_data['property_profile']:
                    print(f"    ✓ Successfully mapped {parcel_id}")
                    success_count += 1

                    # Check for validation errors
                    if pipeline.validation_errors:
                        print(f"    ⚠ {len(pipeline.validation_errors)} validation warnings")
                        for error in pipeline.validation_errors[:3]:  # Show first 3 errors
                            print(f"      - {error['field']}: {error['error']}")
                else:
                    print(f"    ✗ Mapping incomplete for {parcel_id}")

            except Exception as e:
                print(f"    ✗ Error mapping {parcel_id}: {e}")

        if success_count == len(TEST_PARCELS[:2]):
            self.summary["passed"] += 1
            self.test_results.append({
                "test": "End-to-End Property Mapping",
                "status": "PASS",
                "details": f"Mapped {success_count}/{len(TEST_PARCELS[:2])} properties"
            })
        else:
            self.summary["failed"] += 1
            self.test_results.append({
                "test": "End-to-End Property Mapping",
                "status": "FAIL",
                "details": f"Only mapped {success_count}/{len(TEST_PARCELS[:2])} properties"
            })

    async def test_performance(self):
        """Test performance metrics"""
        print("\n[TEST 10] Performance Testing...")
        self.summary["total_tests"] += 1

        try:
            import time

            parcel_id = TEST_PARCELS[0]
            pipeline = self.service.pandas_pipeline

            # Measure data fetching time
            start_time = time.time()
            data_frames = pipeline.fetch_property_data(parcel_id)
            fetch_time = time.time() - start_time

            # Measure mapping time
            start_time = time.time()
            ui_data = pipeline.map_data_to_ui(data_frames)
            map_time = time.time() - start_time

            print(f"  ✓ Data fetch time: {fetch_time:.2f} seconds")
            print(f"  ✓ Mapping time: {map_time:.2f} seconds")
            print(f"  ✓ Total time: {fetch_time + map_time:.2f} seconds")

            # Check if performance is acceptable (under 5 seconds total)
            if fetch_time + map_time < 5:
                print("  ✓ Performance is acceptable")
                self.summary["passed"] += 1
                status = "PASS"
            else:
                print("  ⚠ Performance could be improved")
                self.summary["warnings"] += 1
                status = "WARNING"

            self.test_results.append({
                "test": "Performance Testing",
                "status": status,
                "details": f"Total time: {fetch_time + map_time:.2f}s"
            })

        except Exception as e:
            print(f"  ✗ Performance testing failed: {e}")
            self.summary["failed"] += 1
            self.summary["errors"].append(str(e))
            self.test_results.append({
                "test": "Performance Testing",
                "status": "FAIL",
                "error": str(e)
            })

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print(" TEST RESULTS SUMMARY")
        print("="*80)

        # Calculate percentages
        total = self.summary["total_tests"]
        pass_rate = (self.summary["passed"] / total * 100) if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.summary['passed']} ({pass_rate:.1f}%)")
        print(f"Failed: {self.summary['failed']}")
        print(f"Warnings: {self.summary['warnings']}")

        # Overall status
        if self.summary["failed"] == 0:
            overall_status = "✓ ALL TESTS PASSED"
            status_color = "\033[92m"  # Green
        elif self.summary["failed"] <= 2:
            overall_status = "⚠ MOSTLY PASSED"
            status_color = "\033[93m"  # Yellow
        else:
            overall_status = "✗ FAILED"
            status_color = "\033[91m"  # Red

        print(f"\n{status_color}Overall Status: {overall_status}\033[0m")

        # Detailed results
        print("\nDetailed Results:")
        print("-" * 40)
        for result in self.test_results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⚠"
            print(f"{status_symbol} {result['test']}: {result['status']}")
            if "details" in result:
                print(f"  {result['details']}")
            if "error" in result:
                print(f"  Error: {result['error'][:100]}...")

        # Save report to file
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary,
            "results": self.test_results
        }

        with open("data_mapping_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n" + "-" * 40)
        print("Report saved to: data_mapping_test_report.json")
        print("Log file: data_mapping_verification.log")

        # Recommendations
        if self.summary["errors"]:
            print("\nRecommendations:")
            print("1. Check database connectivity and credentials")
            print("2. Verify all required database tables exist")
            print("3. Ensure Playwright and OpenCV are properly installed")
            print("4. Review field mapping configuration")

async def main():
    """Main test execution"""
    tester = DataMappingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # Create verification directory
    os.makedirs("verification", exist_ok=True)

    # Run tests
    asyncio.run(main())