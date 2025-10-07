"""
Simple Pagination Test - Agent 2 Analysis
Testing the specific pagination implementation and identifying hidden limitations
"""

import requests
import time
import json
from datetime import datetime

def test_pagination_limits():
    """Test pagination mechanics and limitations"""
    print("PAGINATION MECHANICS DEEP DIVE")
    print("=" * 50)

    # API endpoints to test
    endpoints = [
        ("Production", "https://concordbroker.up.railway.app"),
        ("Local", "http://localhost:8000")
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "total_dataset_size": 7312041,
        "tests": []
    }

    # Calculate theoretical limits
    total_properties = 7312041
    print(f"Total Properties: {total_properties:,}")
    print(f"Page size 50: {total_properties // 50:,} pages, max offset {(total_properties // 50) * 50:,}")
    print(f"Page size 100: {total_properties // 100:,} pages, max offset {(total_properties // 100) * 100:,}")
    print()

    for endpoint_name, base_url in endpoints:
        print(f"Testing {endpoint_name}: {base_url}")

        # Test API availability
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"  -> API unavailable (HTTP {response.status_code})")
                continue
        except Exception as e:
            print(f"  -> API unavailable ({str(e)[:50]})")
            continue

        print(f"  -> API available")

        # Test basic pagination
        test_cases = [
            {"limit": 50, "offset": 0, "desc": "Page 1"},
            {"limit": 50, "offset": 1000, "desc": "Page 21"},
            {"limit": 50, "offset": 10000, "desc": "Page 201"},
            {"limit": 50, "offset": 100000, "desc": "Page 2001"},
            {"limit": 50, "offset": 500000, "desc": "Page 10001"},
            {"limit": 50, "offset": 1000000, "desc": "Page 20001"},
            {"limit": 50, "offset": 2500000, "desc": "Page 50001"},
            {"limit": 50, "offset": 5000000, "desc": "Page 100001"},
            {"limit": 50, "offset": 7000000, "desc": "Page 140001"},
        ]

        endpoint_results = []

        for test in test_cases:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={
                        "limit": test["limit"],
                        "offset": test["offset"]
                    },
                    timeout=60
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    properties = data.get('properties', [])
                    total_reported = data.get('total', 0)

                    result = {
                        "test": test["desc"],
                        "offset": test["offset"],
                        "status": "SUCCESS",
                        "count": len(properties),
                        "total_reported": total_reported,
                        "response_time_ms": response_time,
                        "has_data": len(properties) > 0
                    }

                    print(f"    {test['desc']}: {len(properties)} results ({response_time:.0f}ms)")

                    # If no results, we've hit the end
                    if len(properties) == 0:
                        print(f"    -> END OF DATA at offset {test['offset']:,}")
                        result["note"] = "End of dataset"
                        endpoint_results.append(result)
                        break

                else:
                    result = {
                        "test": test["desc"],
                        "offset": test["offset"],
                        "status": "ERROR",
                        "status_code": response.status_code,
                        "response_time_ms": response_time
                    }
                    print(f"    {test['desc']}: ERROR HTTP {response.status_code}")

                endpoint_results.append(result)

            except Exception as e:
                result = {
                    "test": test["desc"],
                    "offset": test["offset"],
                    "status": "EXCEPTION",
                    "error": str(e)[:100]
                }
                endpoint_results.append(result)
                print(f"    {test['desc']}: EXCEPTION {str(e)[:50]}")

                # If timeout, we've hit a practical limit
                if "timeout" in str(e).lower():
                    print(f"    -> TIMEOUT LIMIT at offset {test['offset']:,}")
                    break

        results["tests"].append({
            "endpoint": endpoint_name,
            "url": base_url,
            "results": endpoint_results
        })

        print()

    # Test limit boundaries
    print("Testing Limit Boundaries")
    print("-" * 30)

    for endpoint_name, base_url in endpoints:
        if any(t["endpoint"] == endpoint_name for t in results["tests"]):
            print(f"{endpoint_name}:")

            # Test different limit values
            limit_tests = [50, 100, 200, 500, 1000, 2000]

            for limit_val in limit_tests:
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"{base_url}/api/properties/search",
                        params={"limit": limit_val, "offset": 0},
                        timeout=30
                    )
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        count = len(data.get('properties', []))
                        print(f"  Limit {limit_val}: {count} results ({response_time:.0f}ms)")

                        if count < limit_val:
                            print(f"    -> LIMIT RESTRICTION: requested {limit_val}, got {count}")
                    else:
                        print(f"  Limit {limit_val}: ERROR HTTP {response.status_code}")

                except Exception as e:
                    print(f"  Limit {limit_val}: EXCEPTION {str(e)[:50]}")

            print()

    # Analyze and report findings
    print("ANALYSIS OF PAGINATION LIMITATIONS")
    print("=" * 40)

    limitations = []

    for test_group in results["tests"]:
        endpoint = test_group["endpoint"]
        test_results = test_group["results"]

        # Find where queries fail
        successful_tests = [t for t in test_results if t["status"] == "SUCCESS" and t.get("has_data", False)]
        failed_tests = [t for t in test_results if t["status"] != "SUCCESS"]
        end_of_data = [t for t in test_results if t["status"] == "SUCCESS" and not t.get("has_data", False)]

        if successful_tests:
            last_successful = max(successful_tests, key=lambda x: x["offset"])
            print(f"{endpoint}: Last successful query at offset {last_successful['offset']:,}")

        if end_of_data:
            first_empty = min(end_of_data, key=lambda x: x["offset"])
            print(f"{endpoint}: Data ends at offset {first_empty['offset']:,}")
            limitations.append(f"{endpoint}: Data ends at offset {first_empty['offset']:,}")

        if failed_tests:
            first_failure = min(failed_tests, key=lambda x: x["offset"])
            print(f"{endpoint}: First failure at offset {first_failure['offset']:,}")
            limitations.append(f"{endpoint}: Query failures starting at {first_failure['offset']:,}")

        # Check for performance issues
        if len(successful_tests) >= 2:
            first_time = successful_tests[0]["response_time_ms"]
            last_time = successful_tests[-1]["response_time_ms"]

            if last_time > first_time * 3:  # 3x slower
                print(f"{endpoint}: Performance degrades significantly ({first_time:.0f}ms -> {last_time:.0f}ms)")
                limitations.append(f"{endpoint}: Performance degrades at large offsets")

    print(f"\nSUMMARY OF LIMITATIONS:")
    if limitations:
        for i, limitation in enumerate(limitations, 1):
            print(f"{i}. {limitation}")
    else:
        print("No major limitations found within tested ranges.")

    # Save results
    filename = f"pagination_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {filename}")
    except Exception as e:
        print(f"Could not save results: {e}")

if __name__ == "__main__":
    test_pagination_limits()