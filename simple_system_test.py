"""
Simple System Test
Basic validation of the Florida SDF system components without requiring
database credentials or special Unicode characters.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime

# Import our modules
from florida_counties_manager import FloridaCountiesManager
from sdf_processor import SdfFileProcessor


def test_counties_manager():
    """Test Florida Counties Manager"""
    print("\nTesting Florida Counties Manager...")
    print("-" * 50)

    manager = FloridaCountiesManager()

    # Test basic functionality
    counties = manager.get_all_counties()
    assert len(counties) == 67, f"Expected 67 counties, got {len(counties)}"
    print(f"OK - Found {len(counties)} Florida counties")

    # Test URL formatting
    test_cases = {
        'MIAMI_DADE': 'MIAMI-DADE',
        'ST_JOHNS': 'ST.%20JOHNS',
        'PALM_BEACH': 'PALM%20BEACH',
        'BROWARD': 'BROWARD'
    }

    for county, expected_url in test_cases.items():
        actual_url = manager.format_county_for_url(county)
        assert actual_url == expected_url, f"URL formatting failed for {county}: {actual_url} != {expected_url}"
        print(f"OK - {county} -> {actual_url}")

    # Test download URL generation
    miami_info = manager.get_county_info('MIAMI_DADE')
    assert miami_info['valid'], "Miami-Dade info should be valid"
    assert 'MIAMI-DADE.zip' in miami_info['download_url'], "URL should contain MIAMI-DADE.zip"
    print(f"OK - Download URL: {miami_info['download_url']}")

    # Test priority counties
    priority = manager.get_priority_counties()
    assert len(priority) > 5, "Should have priority counties"
    assert 'MIAMI_DADE' in priority, "Miami-Dade should be priority"
    print(f"OK - Priority counties: {len(priority)} counties")

    print("PASS - Counties Manager tests completed successfully")
    return True


def test_sdf_processor():
    """Test SDF processor with sample data"""
    print("\nTesting SDF Processor...")
    print("-" * 50)

    # Create temporary directory
    test_dir = Path(tempfile.mkdtemp(prefix='sdf_test_'))
    print(f"Test directory: {test_dir}")

    processor = SdfFileProcessor(output_dir=str(test_dir / 'processed'))

    # Create sample CSV data
    sample_csv_content = """PARCEL_ID,SALE_PRC1,SALE_YR1,SALE_MO1,SALE_DAY1,GRANTOR1,GRANTEE1,VI_CD1,QUAL1
12345678,250000,2024,1,15,SMITH JOHN,JONES MARY,01,Q
87654321,180000,2024,2,20,DOE JANE,WILLIAMS BOB,02,Q
11111111,350000,2023,12,5,BROWN ALICE,DAVIS CHARLIE,03,Q
22222222,0,2024,3,10,INVALID RECORD,BUYER NAME,05,Q
33333333,450000,INVALID,4,15,SELLER NAME,BUYER NAME,01,Q"""

    # Create temporary CSV file
    csv_file = test_dir / 'sample_sdf.csv'
    with open(csv_file, 'w') as f:
        f.write(sample_csv_content)

    print(f"Created sample CSV: {csv_file}")

    # Test column mapping
    columns = ['PARCEL_ID', 'SALE_PRC1', 'SALE_YR1', 'SALE_MO1', 'GRANTOR1', 'VI_CD1']
    mapping = processor.map_columns(columns)

    expected_mappings = {
        'PARCEL_ID': 'parcel_id',
        'SALE_PRC1': 'sale_price',
        'SALE_YR1': 'sale_year',
        'SALE_MO1': 'sale_month',
        'GRANTOR1': 'grantor',
        'VI_CD1': 'quality_code'
    }

    for col, expected in expected_mappings.items():
        assert mapping[col] == expected, f"Column mapping failed for {col}: {mapping[col]} != {expected}"

    print(f"OK - Column mapping: {len(mapping)} columns mapped correctly")

    # Test record processing
    valid_records = 0
    total_records = 0

    for chunk_idx, records in enumerate(processor.process_sdf_file(csv_file, 'TEST_COUNTY')):
        total_records += len(records)
        valid_records += len([r for r in records if r.get('sale_price', 0) > 0])

        # Validate a sample record
        if records:
            sample_record = records[0]
            required_fields = ['parcel_id', 'county', 'sale_date', 'sale_price']
            for field in required_fields:
                assert field in sample_record, f"Missing required field: {field}"

        print(f"OK - Processed chunk {chunk_idx}: {len(records)} records")

    print(f"OK - Processing summary: {valid_records}/{total_records} valid records")

    # Check statistics
    stats = processor.get_processing_summary()
    assert stats['total_rows'] > 0, "Should have processed some rows"
    print(f"OK - Processing stats: {stats['total_rows']} rows, {stats['total_valid_rows']} valid")

    print("PASS - SDF Processor tests completed successfully")
    return True


def test_url_validation():
    """Test URL generation and validation"""
    print("\nTesting URL Validation...")
    print("-" * 50)

    manager = FloridaCountiesManager()

    # Test URL generation
    test_counties = ['LAFAYETTE', 'LIBERTY', 'DIXIE']

    for county in test_counties:
        county_info = manager.get_county_info(county)
        url = county_info['download_url']

        # Validate URL structure
        assert url.startswith('https://'), f"URL should start with https: {url}"
        assert 'floridarevenue.com' in url, f"URL should contain floridarevenue.com: {url}"
        assert 'SDF' in url, f"URL should contain SDF: {url}"
        assert '2025' in url, f"URL should contain 2025: {url}"
        assert url.endswith('.zip'), f"URL should end with .zip: {url}"

        print(f"OK - {county}: {url}")

    print("PASS - URL Validation tests completed successfully")
    return True


def test_data_validation():
    """Test data validation functions"""
    print("\nTesting Data Validation...")
    print("-" * 50)

    processor = SdfFileProcessor()

    # Test parcel ID validation
    valid_parcels = ['12345678', '501234567890', 'ABC123DEF456']
    invalid_parcels = ['', '123', None, 'ABC']

    for parcel in valid_parcels:
        assert processor.validate_parcel_id(parcel), f"Should be valid parcel: {parcel}"

    for parcel in invalid_parcels:
        assert not processor.validate_parcel_id(parcel), f"Should be invalid parcel: {parcel}"

    print("OK - Parcel ID validation working correctly")

    # Test sale date parsing
    date_tests = [
        (2024, 1, 15, '2024-01-15'),
        (2023, 12, 31, '2023-12-31'),
        ('2024', '6', '20', '2024-06-20'),
        (None, 5, 10, None),
        (2024, 13, 5, None),  # Invalid month
        (1800, 1, 1, None),   # Invalid year
    ]

    for year, month, day, expected in date_tests:
        result = processor.parse_sale_date(year, month, day)
        assert result == expected, f"Date parsing failed for {year}/{month}/{day}: {result} != {expected}"

    print("OK - Sale date parsing working correctly")

    # Test sale price parsing
    price_tests = [
        (100000, 100000.0),
        ('250,000', 250000.0),
        ('$150000', 150000.0),
        ('0', None),
        ('', None),
        (None, None),
        (-1000, None),  # Negative price
    ]

    for price_input, expected in price_tests:
        result = processor.parse_sale_price(price_input)
        assert result == expected, f"Price parsing failed for {price_input}: {result} != {expected}"

    print("OK - Sale price parsing working correctly")

    # Test qualification determination
    qual_tests = [
        ('01', True),   # Valid sale
        ('02', True),   # Valid sale
        ('15', False),  # Foreclosure
        ('08', False),  # REA sale
        ('99', False),  # Invalid code
    ]

    for code, expected_qualified in qual_tests:
        result = processor.determine_sale_qualification(code)
        assert result['qualified_sale'] == expected_qualified, f"Qualification failed for {code}"

    print("OK - Sale qualification working correctly")

    print("PASS - Data Validation tests completed successfully")
    return True


def run_integration_test():
    """Run a complete integration test"""
    print("\nRunning Integration Test...")
    print("-" * 50)

    test_dir = Path(tempfile.mkdtemp(prefix='sdf_integration_'))
    print(f"Integration test directory: {test_dir}")

    try:
        # Create sample SDF data file
        sample_data = """PARCEL_ID,SALE_PRC1,SALE_YR1,SALE_MO1,SALE_DAY1,GRANTOR1,GRANTEE1,VI_CD1,QUAL1,VAC_IMP1,USE_CD1
50010001,125000,2024,6,15,SAMPLE SELLER LLC,SAMPLE BUYER TRUST,01,Q,I,0100
50010002,85000,2024,7,20,ANOTHER SELLER,FIRST TIME BUYER,02,Q,V,0000
50010003,245000,2023,12,31,ESTATE OF SOMEONE,INVESTMENT GROUP,01,Q,I,0200"""

        # Create test CSV file
        csv_file = test_dir / 'SAMPLE_SDF.csv'
        with open(csv_file, 'w') as f:
            f.write(sample_data)

        print(f"OK - Created sample SDF file: {csv_file}")

        # Test processor
        processor = SdfFileProcessor(output_dir=str(test_dir / 'processed'))

        processed_records = []
        for chunk in processor.process_sdf_file(csv_file, 'SAMPLE_COUNTY'):
            processed_records.extend(chunk)

        print(f"OK - Processed {len(processed_records)} records")

        # Validate processed records
        for i, record in enumerate(processed_records):
            required_fields = ['parcel_id', 'county', 'sale_date', 'sale_price', 'qualified_sale']
            for field in required_fields:
                assert field in record, f"Record {i} missing field: {field}"

            print(f"  Record {i+1}: {record['parcel_id']} - ${record['sale_price']:,.2f} on {record['sale_date']}")

        print("PASS - Integration test completed successfully")
        return True

    except Exception as e:
        print(f"FAIL - Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("=" * 80)
    print("Florida SDF System - Simple Test Suite")
    print("=" * 80)

    tests = [
        ("Counties Manager", test_counties_manager),
        ("URL Validation", test_url_validation),
        ("SDF Processor", test_sdf_processor),
        ("Data Validation", test_data_validation),
        ("Integration Test", run_integration_test),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"FAIL - {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = 0
    failed = 0

    for test_name, success in results:
        if success:
            print(f"PASS - {test_name}")
            passed += 1
        else:
            print(f"FAIL - {test_name}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("\nSUCCESS - All tests passed! System is ready for use.")
        return True
    else:
        print(f"\nFAILED - {failed} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)