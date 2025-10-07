#!/usr/bin/env python3
"""
Production Testing Script for ConcordBroker
Tests all API endpoints with real Supabase data
"""

import requests
import time
import json
from typing import Dict, List, Any

# Production URLs
PRODUCTION_URL = "https://www.concordbroker.com"
LOCALHOST_URL = "http://localhost:5173"

def test_endpoint(url: str, endpoint: str, params: Dict = None) -> Dict:
    """Test a single endpoint and return results"""
    full_url = f"{url}{endpoint}"
    start_time = time.time()

    try:
        response = requests.get(full_url, params=params, timeout=5)
        elapsed = (time.time() - start_time) * 1000

        return {
            "url": full_url,
            "status": response.status_code,
            "success": response.status_code == 200,
            "response_time_ms": round(elapsed, 2),
            "data_sample": response.json() if response.status_code == 200 else None
        }
    except requests.exceptions.Timeout:
        return {
            "url": full_url,
            "status": 0,
            "success": False,
            "error": "Timeout after 5 seconds"
        }
    except Exception as e:
        return {
            "url": full_url,
            "status": 0,
            "success": False,
            "error": str(e)
        }

def test_production():
    """Run all production tests"""
    print("=" * 60)
    print(" ConcordBroker Production Testing Suite")
    print(" Testing live endpoints at concordbroker.com")
    print("=" * 60)
    print()

    # Define test cases
    tests = [
        {
            "name": "Autocomplete - Address Search",
            "endpoint": "/api/autocomplete/addresses",
            "params": {"q": "123", "limit": 5}
        },
        {
            "name": "Autocomplete - Owner Search",
            "endpoint": "/api/autocomplete/owners",
            "params": {"q": "smith", "limit": 5}
        },
        {
            "name": "Property Search",
            "endpoint": "/api/properties/search",
            "params": {"limit": 10}
        },
        {
            "name": "Property Stats",
            "endpoint": "/api/properties/stats",
            "params": {}
        },
        {
            "name": "City Statistics",
            "endpoint": "/api/properties/cities",
            "params": {}
        },
        {
            "name": "Property Detail",
            "endpoint": "/api/properties/3040190012860",
            "params": {}
        }
    ]

    # Test each endpoint
    results = []
    total_tests = len(tests)
    passed = 0
    failed = 0

    for i, test in enumerate(tests, 1):
        print(f"[{i}/{total_tests}] Testing {test['name']}...")
        result = test_endpoint(PRODUCTION_URL, test['endpoint'], test.get('params'))
        results.append(result)

        if result['success']:
            print(f"  [OK] Success - {result['response_time_ms']}ms")
            passed += 1

            # Show sample data
            if result.get('data_sample'):
                data = result['data_sample']
                if isinstance(data, dict):
                    if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                        print(f"    Found {len(data['data'])} results")
                    elif 'property' in data:
                        print(f"    Property: {data['property'].get('address', 'N/A')}")
                    elif 'stats' in data:
                        stats = data['stats']
                        print(f"    Total Properties: {stats.get('total_properties', 'N/A'):,}")
        else:
            print(f"  [FAIL] Failed - {result.get('error', f'Status {result.get('status')}')}")
            failed += 1

        print()

    # Summary
    print("=" * 60)
    print(" Test Summary")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ({passed/total_tests*100:.0f}%)")
    print(f"Failed: {failed} ({failed/total_tests*100:.0f}%)")

    avg_response_time = sum(r.get('response_time_ms', 0) for r in results if r.get('success')) / max(passed, 1)
    print(f"Avg Response Time: {avg_response_time:.2f}ms")

    # Performance assessment
    print()
    print("Performance Assessment:")
    if avg_response_time < 100:
        print("  [EXCELLENT] Sub-100ms average response")
    elif avg_response_time < 300:
        print("  [GOOD] Sub-300ms average response")
    elif avg_response_time < 500:
        print("  [WARNING] ACCEPTABLE - Consider optimization")
    else:
        print("  [SLOW] Optimization needed")

    # Database check
    print()
    print("Database Status:")
    for result in results:
        if result.get('success') and 'stats' in str(result.get('data_sample', {})):
            data = result['data_sample']
            if 'stats' in data:
                stats = data['stats']
                print(f"  Properties: {stats.get('total_properties', 0):,}")
                print(f"  Counties: {stats.get('total_counties', 0)}")
                break

    print()
    print("=" * 60)

    return passed == total_tests

def test_localhost():
    """Quick localhost test"""
    print("\nTesting localhost endpoints...")

    try:
        response = requests.get(f"{LOCALHOST_URL}/api/autocomplete/addresses?q=123", timeout=2)
        if response.status_code == 200:
            print("[OK] Localhost is running and responding")
            return True
    except:
        pass

    print("[X] Localhost is not running or not responding")
    return False

if __name__ == "__main__":
    # Test production
    production_ok = test_production()

    # Test localhost
    localhost_ok = test_localhost()

    # Final status
    print()
    if production_ok:
        print("PRODUCTION IS READY!")
        print("Visit: https://www.concordbroker.com")
    else:
        print("WARNING: Some production tests failed. Check the logs above.")

    if localhost_ok:
        print("[OK] Localhost is also running")
    else:
        print("[INFO] Localhost is not running (expected if testing production only)")