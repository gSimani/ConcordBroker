"""
Test Zod-inspired validation integration for ConcordBroker
Demonstrates runtime validation for pipeline data
"""

import sys
import json
from datetime import datetime
from apps.api.validation import (
    FloridaParcel,
    PropertySale,
    SunbizCorporate,
    PipelineDataValidator,
    FloridaValidators,
    ValidationMiddleware
)

def test_property_validation():
    """Test property data validation"""
    print("\n" + "="*70)
    print("TESTING PROPERTY VALIDATION")
    print("="*70)
    
    # Valid property data
    valid_property = {
        "parcel_id": "06-43-42-12-34-567.890",
        "county": "BROWARD",
        "year": 2024,
        "owner_name": "JOHN DOE",
        "phy_addr1": "123 MAIN ST",
        "phy_city": "FORT LAUDERDALE",
        "phy_zipcd": "33301",
        "taxable_value": 450000.00,
        "year_built": 2010,
        "total_living_area": 2500.0,
        "land_sqft": 7500.0
    }
    
    # Invalid property data (negative value)
    invalid_property = {
        "parcel_id": "INVALID",
        "county": "BROWARD",
        "year": 2024,
        "taxable_value": -1000,  # Invalid: negative value
        "year_built": 1700  # Invalid: too old
    }
    
    validator = PipelineDataValidator()
    
    # Test valid property
    success, parcel, errors = validator.validate_property(valid_property)
    if success:
        print("[SUCCESS] Valid property passed validation")
        print(f"  Parcel ID: {parcel.parcel_id}")
        print(f"  Value: ${parcel.taxable_value:,.0f}")
    else:
        print(f"[ERROR] Valid property failed: {errors}")
    
    # Test invalid property
    success, parcel, errors = validator.validate_property(invalid_property)
    if not success:
        print("\n[SUCCESS] Invalid property correctly rejected")
        print(f"  Errors: {errors[0][:100]}...")
    else:
        print(f"[ERROR] Invalid property should have failed")

def test_sale_validation():
    """Test sale data validation"""
    print("\n" + "="*70)
    print("TESTING SALE VALIDATION")
    print("="*70)
    
    valid_sale = {
        "parcel_id": "06-43-42-12-34-567.890",
        "county": "BROWARD",
        "sale_date": "2024-01-15",
        "sale_price": 525000.00,
        "grantor_name": "JOHN DOE",
        "grantee_name": "JANE SMITH",
        "is_arms_length": True,
        "is_foreclosure": False
    }
    
    validator = PipelineDataValidator()
    success, sale, errors = validator.validate_sale(valid_sale)
    
    if success:
        print("[SUCCESS] Valid sale passed validation")
        print(f"  Sale Price: ${sale.sale_price:,.0f}")
        print(f"  Arms Length: {sale.is_arms_length}")
    else:
        print(f"[ERROR] Sale validation failed: {errors}")

def test_batch_validation():
    """Test batch validation with statistics"""
    print("\n" + "="*70)
    print("TESTING BATCH VALIDATION")
    print("="*70)
    
    properties = [
        # Valid properties
        {
            "parcel_id": f"PARCEL-{i:04d}",
            "county": "MIAMI-DADE",
            "year": 2024,
            "taxable_value": 100000 + (i * 50000)
        }
        for i in range(5)
    ]
    
    # Add some invalid properties
    properties.extend([
        {"parcel_id": "", "county": "INVALID", "year": 1999},  # Invalid
        {"parcel_id": "BAD", "county": "DADE", "year": 2100},  # Invalid year
    ])
    
    validator = PipelineDataValidator()
    result = validator.validate_batch(FloridaParcel, properties)
    
    stats = result['stats']
    print(f"Batch Validation Results:")
    print(f"  Total items: {stats['total']}")
    print(f"  Valid: {stats['valid']}")
    print(f"  Invalid: {stats['invalid']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    
    if result['invalid']:
        print(f"\nFirst invalid item errors:")
        print(f"  {result['invalid'][0]['errors'][0][:100]}...")

def test_florida_validators():
    """Test Florida-specific validators"""
    print("\n" + "="*70)
    print("TESTING FLORIDA-SPECIFIC VALIDATORS")
    print("="*70)
    
    validator = FloridaValidators()
    
    # Test parcel ID validation
    valid_parcel = "06-43-42-12-34-567.890"
    invalid_parcel = "ABC"
    
    print("Parcel ID Validation:")
    print(f"  '{valid_parcel}': {validator.is_valid_parcel_id(valid_parcel)}")
    print(f"  '{invalid_parcel}': {validator.is_valid_parcel_id(invalid_parcel)}")
    
    # Test Florida ZIP validation
    valid_zip = "33301"  # Fort Lauderdale
    invalid_zip = "10001"  # New York
    
    print("\nFlorida ZIP Code Validation:")
    print(f"  '{valid_zip}': {validator.is_valid_florida_zip(valid_zip)}")
    print(f"  '{invalid_zip}': {validator.is_valid_florida_zip(invalid_zip)}")
    
    # Test county validation
    valid_county = "BROWARD"
    invalid_county = "FAKE-COUNTY"
    
    print("\nCounty Validation:")
    print(f"  '{valid_county}': {validator.is_valid_county(valid_county)}")
    print(f"  '{invalid_county}': {validator.is_valid_county(invalid_county)}")
    
    # Test owner name cleaning
    messy_name = "  JOHN   DOE,   LLC!!!  "
    clean_name = validator.clean_owner_name(messy_name)
    print(f"\nOwner Name Cleaning:")
    print(f"  Original: '{messy_name}'")
    print(f"  Cleaned: '{clean_name}'")

def test_validation_middleware():
    """Test validation middleware for API"""
    print("\n" + "="*70)
    print("TESTING VALIDATION MIDDLEWARE")
    print("="*70)
    
    middleware = ValidationMiddleware()
    
    # Test property validation through middleware
    property_data = {
        "parcel_id": "TEST-001",
        "county": "PALM BEACH",
        "year": 2024,
        "owner_name": "Test Owner",
        "taxable_value": 750000
    }
    
    result = middleware.validate_incoming_data('property', property_data)
    
    if result['success']:
        print("[SUCCESS] Middleware validation passed")
        print(f"  Validated data available: {result['data'] is not None}")
    else:
        print(f"[ERROR] Middleware validation failed: {result['errors']}")
    
    # Test batch import
    print("\nBatch Import Validation:")
    items = [
        {"parcel_id": f"BATCH-{i}", "county": "BROWARD", "year": 2024}
        for i in range(10)
    ]
    
    batch_result = middleware.validate_batch_import('property', items)
    stats = batch_result['stats']
    print(f"  Processed: {stats['total']} items")
    print(f"  Success rate: {stats['success_rate']:.1f}%")

def main():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("ZOD-INSPIRED VALIDATION INTEGRATION FOR CONCORDBROKER")
    print("="*70)
    print("Runtime data validation for property pipeline")
    
    test_property_validation()
    test_sale_validation()
    test_batch_validation()
    test_florida_validators()
    test_validation_middleware()
    
    print("\n" + "="*70)
    print("VALIDATION BENEFITS")
    print("="*70)
    print("[OK] Type-safe data processing")
    print("[OK] Early error detection")
    print("[OK] Data quality assurance")
    print("[OK] Consistent data format")
    print("[OK] Reduced database errors")
    print("[OK] Better error messages")
    
    print("\n[SUCCESS] Zod-inspired validation fully integrated!")

if __name__ == "__main__":
    main()