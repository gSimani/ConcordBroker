"""
Pagination Mechanics Deep Dive Test
Agent 2: Testing the specific pagination implementation and identifying hidden limitations
"""

import requests
import time
import json
from datetime import datetime
import asyncio
from typing import Dict, Any, List

class PaginationTester:
    def __init__(self):
        # Production API endpoint
        self.api_base = "https://concordbroker.up.railway.app"
        # Local test endpoint (if available)
        self.local_api = "http://localhost:8000"

        # Test both endpoints
        self.endpoints = [
            ("Production", self.api_base),
            ("Local", self.local_api)
        ]

        # Results storage
        self.test_results = {}

    def test_api_availability(self, endpoint_name: str, base_url: str) -> bool:
        """Test if API endpoint is available"""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ {endpoint_name} API available: {base_url}")
                return True
            else:
                print(f"✗ {endpoint_name} API returned {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {endpoint_name} API unavailable: {e}")
            return False

    def test_basic_pagination(self, base_url: str) -> Dict[str, Any]:
        """Test basic pagination mechanics"""
        print(f"\n=== Testing Basic Pagination: {base_url} ===")
        results = {"endpoint": base_url, "tests": []}

        # Test 1: Small offset pagination
        test_cases = [
            {"limit": 50, "offset": 0, "description": "Page 1"},
            {"limit": 50, "offset": 50, "description": "Page 2"},
            {"limit": 50, "offset": 100, "description": "Page 3"},
            {"limit": 50, "offset": 1000, "description": "Page 21"},
            {"limit": 50, "offset": 10000, "description": "Page 201"},
        ]

        for test_case in test_cases:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={
                        "limit": test_case["limit"],
                        "offset": test_case["offset"]
                    },
                    timeout=30
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    properties = data.get('properties', [])
                    total = data.get('total', 0)

                    result = {
                        "test": test_case["description"],
                        "limit": test_case["limit"],
                        "offset": test_case["offset"],
                        "status": "SUCCESS",
                        "returned_count": len(properties),
                        "total_reported": total,
                        "response_time_ms": response_time,
                        "has_results": len(properties) > 0
                    }
                    print(f"✓ {test_case['description']}: {len(properties)} results in {response_time:.1f}ms")
                else:
                    result = {
                        "test": test_case["description"],
                        "status": "ERROR",
                        "status_code": response.status_code,
                        "error": response.text[:200],
                        "response_time_ms": response_time
                    }
                    print(f"✗ {test_case['description']}: HTTP {response.status_code}")

                results["tests"].append(result)

            except Exception as e:
                result = {
                    "test": test_case["description"],
                    "status": "EXCEPTION",
                    "error": str(e)[:200]
                }
                results["tests"].append(result)
                print(f"✗ {test_case['description']}: {str(e)[:100]}")

        return results

    def test_large_offset_pagination(self, base_url: str) -> Dict[str, Any]:
        """Test large offset values to find limits"""
        print(f"\n=== Testing Large Offset Pagination: {base_url} ===")
        results = {"endpoint": base_url, "large_offset_tests": []}

        # Test increasingly large offsets
        large_offsets = [
            50000,    # Page ~1001
            100000,   # Page ~2001
            500000,   # Page ~10001
            1000000,  # Page ~20001
            2500000,  # Page ~50001
            5000000,  # Page ~100001
            7000000,  # Near the total dataset size
            7300000,  # Very close to dataset limit
            7500000,  # Beyond dataset size
        ]

        for offset in large_offsets:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={
                        "limit": 50,
                        "offset": offset
                    },
                    timeout=60  # Longer timeout for large queries
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    properties = data.get('properties', [])

                    result = {
                        "offset": offset,
                        "page_equivalent": (offset // 50) + 1,
                        "status": "SUCCESS",
                        "returned_count": len(properties),
                        "response_time_ms": response_time,
                        "has_results": len(properties) > 0,
                        "timeout_occurred": response_time > 30000
                    }

                    print(f"✓ Offset {offset:,}: {len(properties)} results in {response_time:.1f}ms")
                else:
                    result = {
                        "offset": offset,
                        "status": "ERROR",
                        "status_code": response.status_code,
                        "error": response.text[:200],
                        "response_time_ms": response_time
                    }
                    print(f"✗ Offset {offset:,}: HTTP {response.status_code}")

                results["large_offset_tests"].append(result)

                # If we get zero results, we've likely hit the end
                if response.status_code == 200 and len(properties) == 0:
                    print(f"ℹ Found end of dataset at offset {offset:,}")
                    break

            except Exception as e:
                result = {
                    "offset": offset,
                    "status": "EXCEPTION",
                    "error": str(e)[:200]
                }
                results["large_offset_tests"].append(result)
                print(f"✗ Offset {offset:,}: {str(e)[:100]}")

                # If it's a timeout, we've found a practical limit
                if "timeout" in str(e).lower():
                    print(f"ℹ Timeout limit reached at offset {offset:,}")
                    break

        return results

    def test_performance_degradation(self, base_url: str) -> Dict[str, Any]:
        """Test how response time changes with increasing offset"""
        print(f"\n=== Testing Performance Degradation: {base_url} ===")
        results = {"endpoint": base_url, "performance_tests": []}

        # Test offsets at different scales to measure performance degradation
        performance_offsets = [0, 1000, 10000, 50000, 100000, 250000, 500000, 750000, 1000000]

        for offset in performance_offsets:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={
                        "limit": 50,
                        "offset": offset,
                        "county": "MIAMI-DADE"  # Add filter to make query more realistic
                    },
                    timeout=45
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    properties = data.get('properties', [])

                    result = {
                        "offset": offset,
                        "response_time_ms": response_time,
                        "returned_count": len(properties),
                        "has_results": len(properties) > 0
                    }

                    print(f"✓ Offset {offset:,}: {response_time:.1f}ms ({len(properties)} results)")

                else:
                    result = {
                        "offset": offset,
                        "status": "ERROR",
                        "status_code": response.status_code,
                        "response_time_ms": response_time
                    }
                    print(f"✗ Offset {offset:,}: HTTP {response.status_code}")

                results["performance_tests"].append(result)

            except Exception as e:
                result = {
                    "offset": offset,
                    "status": "EXCEPTION",
                    "error": str(e)[:200]
                }
                results["performance_tests"].append(result)
                print(f"✗ Offset {offset:,}: {str(e)[:100]}")

        return results

    def test_supabase_specific_limits(self, base_url: str) -> Dict[str, Any]:
        """Test Supabase-specific limitations"""
        print(f"\n=== Testing Supabase-Specific Limits: {base_url} ===")
        results = {"endpoint": base_url, "supabase_tests": []}

        # Test 1: Maximum range limit
        try:
            # Supabase PostgREST has a default limit of 1000 rows per request
            response = requests.get(
                f"{base_url}/api/properties/search",
                params={"limit": 1000},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                properties = data.get('properties', [])
                result = {
                    "test": "Max limit 1000",
                    "status": "SUCCESS",
                    "returned_count": len(properties)
                }
                print(f"✓ Max limit 1000: {len(properties)} results")
            else:
                result = {
                    "test": "Max limit 1000",
                    "status": "ERROR",
                    "status_code": response.status_code
                }
                print(f"✗ Max limit 1000: HTTP {response.status_code}")

            results["supabase_tests"].append(result)
        except Exception as e:
            print(f"✗ Max limit test failed: {e}")

        # Test 2: Very large limit (should fail)
        try:
            response = requests.get(
                f"{base_url}/api/properties/search",
                params={"limit": 5000},  # Exceeds typical PostgREST limits
                timeout=30
            )

            result = {
                "test": "Excessive limit 5000",
                "status": "SUCCESS" if response.status_code == 200 else "ERROR",
                "status_code": response.status_code,
                "response_text": response.text[:200] if response.status_code != 200 else "OK"
            }

            results["supabase_tests"].append(result)
            print(f"{'✓' if response.status_code == 200 else '✗'} Excessive limit 5000: HTTP {response.status_code}")

        except Exception as e:
            print(f"✗ Excessive limit test failed: {e}")

        return results

    def calculate_pagination_math(self) -> Dict[str, Any]:
        """Calculate theoretical pagination limits"""
        print(f"\n=== Calculating Pagination Mathematics ===")

        total_properties = 7312041

        calculations = {
            "total_properties": total_properties,
            "pagination_scenarios": []
        }

        page_sizes = [20, 50, 100, 200]

        for page_size in page_sizes:
            total_pages = (total_properties + page_size - 1) // page_size
            last_page_offset = (total_pages - 1) * page_size

            scenario = {
                "page_size": page_size,
                "total_pages": total_pages,
                "last_page_offset": last_page_offset,
                "max_page_number": total_pages,
                "last_page_items": total_properties - last_page_offset
            }

            calculations["pagination_scenarios"].append(scenario)

            print(f"Page size {page_size:3d}: {total_pages:,} pages, max offset {last_page_offset:,}")

        return calculations

    def run_full_test_suite(self):
        """Run complete pagination analysis"""
        print("PAGINATION MECHANICS DEEP DIVE")
        print("=" * 50)

        self.test_results["timestamp"] = datetime.now().isoformat()
        self.test_results["total_dataset_size"] = 7312041

        # Calculate theoretical limits
        self.test_results["pagination_math"] = self.calculate_pagination_math()

        # Test each available endpoint
        for endpoint_name, base_url in self.endpoints:
            if self.test_api_availability(endpoint_name, base_url):

                # Basic pagination tests
                basic_results = self.test_basic_pagination(base_url)
                self.test_results[f"{endpoint_name.lower()}_basic"] = basic_results

                # Large offset tests
                large_offset_results = self.test_large_offset_pagination(base_url)
                self.test_results[f"{endpoint_name.lower()}_large_offset"] = large_offset_results

                # Performance degradation tests
                performance_results = self.test_performance_degradation(base_url)
                self.test_results[f"{endpoint_name.lower()}_performance"] = performance_results

                # Supabase-specific tests
                supabase_results = self.test_supabase_specific_limits(base_url)
                self.test_results[f"{endpoint_name.lower()}_supabase"] = supabase_results

                # Small delay between endpoint tests
                time.sleep(2)

        self.analyze_results()
        self.save_results()

    def analyze_results(self):
        """Analyze test results to identify limitations"""
        print(f"\n=== ANALYSIS OF PAGINATION LIMITATIONS ===")

        limitations_found = []

        # Analyze basic pagination
        for endpoint_key in ["production_basic", "local_basic"]:
            if endpoint_key in self.test_results:
                basic_tests = self.test_results[endpoint_key]["tests"]

                # Check for failures
                failures = [t for t in basic_tests if t["status"] != "SUCCESS"]
                if failures:
                    limitations_found.append(f"Basic pagination failures in {endpoint_key}")

                # Check performance degradation
                successful_tests = [t for t in basic_tests if t["status"] == "SUCCESS"]
                if len(successful_tests) >= 2:
                    first_response = successful_tests[0]["response_time_ms"]
                    last_response = successful_tests[-1]["response_time_ms"]

                    if last_response > first_response * 2:
                        limitations_found.append(f"Performance degradation in {endpoint_key}: {first_response:.1f}ms -> {last_response:.1f}ms")

        # Analyze large offset tests
        for endpoint_key in ["production_large_offset", "local_large_offset"]:
            if endpoint_key in self.test_results:
                large_tests = self.test_results[endpoint_key]["large_offset_tests"]

                # Find where queries start failing or timing out
                last_successful_offset = 0
                first_failure_offset = None

                for test in large_tests:
                    if test["status"] == "SUCCESS" and test.get("has_results", False):
                        last_successful_offset = test["offset"]
                    elif test["status"] != "SUCCESS" and first_failure_offset is None:
                        first_failure_offset = test["offset"]
                        break
                    elif test["status"] == "SUCCESS" and not test.get("has_results", False):
                        # Found end of data
                        limitations_found.append(f"Data ends at offset {test['offset']:,} in {endpoint_key}")
                        break

                if first_failure_offset:
                    limitations_found.append(f"Queries fail starting at offset {first_failure_offset:,} in {endpoint_key}")

                # Check for timeout issues
                timeout_tests = [t for t in large_tests if t.get("timeout_occurred", False)]
                if timeout_tests:
                    limitations_found.append(f"Timeout issues at large offsets in {endpoint_key}")

        print("LIMITATIONS IDENTIFIED:")
        if limitations_found:
            for i, limitation in enumerate(limitations_found, 1):
                print(f"{i}. {limitation}")
        else:
            print("No major limitations identified within tested ranges.")

    def save_results(self):
        """Save detailed test results"""
        filename = f"pagination_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            print(f"\nDetailed results saved to: {filename}")
        except Exception as e:
            print(f"Could not save results: {e}")

if __name__ == "__main__":
    tester = PaginationTester()
    tester.run_full_test_suite()