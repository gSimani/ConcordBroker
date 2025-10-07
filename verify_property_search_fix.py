#!/usr/bin/env python3
"""
Verification script for property search fix
Tests that building sqft filters now return correct count
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_building_sqft_filter():
    """Test that 10k-20k sqft filter returns 37,726 properties"""
    print("=" * 80)
    print("Testing Building Square Footage Filter Fix")
    print("=" * 80)

    # Test the exact filter that was showing only 7 properties
    params = {
        'minBuildingSqFt': 10000,
        'maxBuildingSqFt': 20000,
        'page': 1,
        'limit': 100
    }

    print(f"\nTesting with filters: {params}")
    print("Expected: 37,726 properties")
    print("Previous bug: 7 properties")

    try:
        response = requests.get(f"{API_BASE}/api/properties/search", params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                pagination = data.get('pagination', {})
                total = pagination.get('total', 0)
                returned = len(data.get('data', []))

                print(f"\n✅ API Response:")
                print(f"   Total properties matching filter: {total:,}")
                print(f"   Properties returned in page 1: {returned}")
                print(f"   Total pages: {pagination.get('pages', 0):,}")

                # Verify the count is correct
                if total == 37726:
                    print(f"\n✅ SUCCESS! Filter now returns correct count: {total:,}")
                    return True
                elif total == 7:
                    print(f"\n❌ BUG STILL EXISTS! Still showing only 7 properties")
                    return False
                else:
                    print(f"\n⚠️  UNEXPECTED COUNT! Got {total:,}, expected 37,726")
                    print(f"   (This might be due to data changes in the database)")
                    return None
            else:
                print(f"\n❌ API returned error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Cannot connect to {API_BASE}")
        print(f"   Make sure the API is running on port 8000")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_other_filters():
    """Test that other numeric filters also work correctly"""
    print("\n" + "=" * 80)
    print("Testing Other Numeric Filters")
    print("=" * 80)

    test_cases = [
        {
            'name': 'Value filter (500k-1M)',
            'params': {'minValue': 500000, 'maxValue': 1000000, 'limit': 10}
        },
        {
            'name': 'Year built filter (2010-2020)',
            'params': {'minYear': 2010, 'maxYear': 2020, 'limit': 10}
        },
        {
            'name': 'Land sqft filter (5000-10000)',
            'params': {'minLandSqFt': 5000, 'maxLandSqFt': 10000, 'limit': 10}
        }
    ]

    all_passed = True

    for test in test_cases:
        print(f"\n{test['name']}:")
        try:
            response = requests.get(f"{API_BASE}/api/properties/search", params=test['params'], timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    total = data.get('pagination', {}).get('total', 0)
                    print(f"   ✅ Total: {total:,}")
                else:
                    print(f"   ❌ API Error: {data.get('error', 'Unknown')}")
                    all_passed = False
            else:
                print(f"   ❌ HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_passed = False

    return all_passed

def main():
    print("\n" + "=" * 80)
    print("PROPERTY SEARCH FIX VERIFICATION")
    print("=" * 80)
    print("\nThis script verifies that the building sqft filter bug has been fixed.")
    print("The bug was: Count query was missing numeric filters, causing incorrect totals.")
    print("The fix: Added all numeric filters (value, year, building sqft, land sqft) to count query.")

    # Test the main fix
    main_test_result = test_building_sqft_filter()

    # Test other filters
    other_tests_result = test_other_filters()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if main_test_result:
        print("\n✅ Building sqft filter: FIXED!")
    elif main_test_result is False:
        print("\n❌ Building sqft filter: STILL BROKEN")
    else:
        print("\n⚠️  Building sqft filter: UNEXPECTED RESULT")

    if other_tests_result:
        print("✅ Other numeric filters: WORKING")
    else:
        print("⚠️  Other numeric filters: SOME ISSUES")

    print("\n" + "=" * 80)

    return main_test_result

if __name__ == "__main__":
    exit(0 if main() else 1)
