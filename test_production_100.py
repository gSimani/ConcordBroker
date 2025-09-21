#!/usr/bin/env python3
"""Test production deployment with Redis - 100% verification"""

import requests
import time
import json
from datetime import datetime

# Production endpoints to test
ENDPOINTS = [
    "https://concordbroker-production.up.railway.app",
    "https://www.concordbroker.com"
]

def test_api():
    """Test API and Redis integration"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "api_status": "CHECKING",
        "redis_status": "CHECKING",
        "performance": {},
        "endpoints_tested": []
    }

    # Find working endpoint
    api_url = None
    for endpoint in ENDPOINTS:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{endpoint}/health", timeout=10)
            if response.status_code == 200:
                api_url = endpoint
                print(f"SUCCESS: API running at {endpoint}")
                results["api_status"] = "ONLINE"
                results["api_url"] = endpoint
                break
            else:
                print(f"  Status code: {response.status_code}")
        except Exception as e:
            print(f"  Failed: {str(e)[:50]}")

    if not api_url:
        # Try API path
        for endpoint in ENDPOINTS:
            try:
                test_url = f"{endpoint}/api/health"
                print(f"Testing {test_url}...")
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    api_url = endpoint
                    print(f"SUCCESS: API running at {endpoint}/api")
                    results["api_status"] = "ONLINE"
                    results["api_url"] = f"{endpoint}/api"
                    break
            except Exception as e:
                print(f"  Failed: {str(e)[:50]}")

    if not api_url:
        print("\nERROR: No working API endpoint found")
        results["api_status"] = "OFFLINE"
        return results

    # Test Redis cache status
    print("\n--- TESTING REDIS CACHE ---")
    try:
        cache_url = f"{api_url}/api/cache/status" if "/api" not in api_url else f"{api_url}/cache/status"
        response = requests.get(cache_url, timeout=10)
        if response.status_code == 200:
            cache_data = response.json()
            results["redis_status"] = "CONNECTED" if cache_data.get("connected") else "DISCONNECTED"
            print(f"Redis Status: {results['redis_status']}")
            if cache_data.get("host"):
                print(f"Redis Host: {cache_data['host']}")
        else:
            print(f"Cache status returned: {response.status_code}")
    except Exception as e:
        print(f"Cache check failed: {str(e)[:100]}")
        results["redis_status"] = "UNKNOWN"

    # Test search performance (with caching)
    print("\n--- TESTING SEARCH PERFORMANCE ---")
    search_queries = ["Miami", "3930 SW", "Broward", "LLC"]

    for query in search_queries:
        print(f"\nTesting search: {query}")

        # First request (cold cache)
        try:
            search_url = f"{api_url}/properties/search" if "/api" not in api_url else f"{api_url.replace('/api', '')}/api/properties/search"
            start = time.time()
            response = requests.get(search_url, params={"q": query, "limit": 10}, timeout=30)
            cold_time = time.time() - start

            # Second request (warm cache)
            start = time.time()
            response = requests.get(search_url, params={"q": query, "limit": 10}, timeout=30)
            warm_time = time.time() - start

            improvement = ((cold_time - warm_time) / cold_time) * 100 if cold_time > 0 else 0

            print(f"  Cold cache: {cold_time:.2f}s")
            print(f"  Warm cache: {warm_time:.2f}s")
            print(f"  Improvement: {improvement:.0f}%")

            results["performance"][query] = {
                "cold": round(cold_time, 2),
                "warm": round(warm_time, 2),
                "improvement": round(improvement, 0)
            }
            results["endpoints_tested"].append(search_url)

        except Exception as e:
            print(f"  Search failed: {str(e)[:100]}")
            results["performance"][query] = {"error": str(e)[:100]}

    # Calculate average improvement
    improvements = [p.get("improvement", 0) for p in results["performance"].values() if "improvement" in p]
    if improvements:
        avg_improvement = sum(improvements) / len(improvements)
        results["avg_improvement"] = round(avg_improvement, 0)
        print(f"\n--- AVERAGE PERFORMANCE IMPROVEMENT: {avg_improvement:.0f}% ---")

    # Test autocomplete
    print("\n--- TESTING AUTOCOMPLETE ---")
    try:
        auto_url = f"{api_url}/autocomplete" if "/api" not in api_url else f"{api_url.replace('/api', '')}/api/autocomplete"
        start = time.time()
        response = requests.get(auto_url, params={"q": "Mia"}, timeout=10)
        auto_time = time.time() - start
        print(f"Autocomplete response time: {auto_time:.3f}s")
        results["autocomplete_time"] = round(auto_time, 3)
        results["endpoints_tested"].append(auto_url)
    except Exception as e:
        print(f"Autocomplete failed: {str(e)[:100]}")

    # Final status
    print("\n" + "="*60)
    print("FINAL STATUS REPORT")
    print("="*60)

    # Determine if we're at 100%
    is_100_percent = (
        results["api_status"] == "ONLINE" and
        results.get("redis_status") == "CONNECTED" and
        results.get("avg_improvement", 0) > 50
    )

    if is_100_percent:
        print("\n*** SYSTEM IS AT 100% OPERATIONAL STATUS ***")
        print("- API: ONLINE")
        print("- Redis Cache: CONNECTED")
        print(f"- Performance Boost: {results.get('avg_improvement', 0):.0f}%")
        results["status"] = "100% OPERATIONAL"
    else:
        print("\n*** SYSTEM STATUS ***")
        print(f"- API: {results['api_status']}")
        print(f"- Redis: {results.get('redis_status', 'UNKNOWN')}")
        print(f"- Performance: {results.get('avg_improvement', 0):.0f}% improvement")
        results["status"] = "PARTIAL"

    # Save report
    with open("production_100_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nReport saved to: production_100_report.json")
    print("="*60)

    return results

if __name__ == "__main__":
    results = test_api()

    # Exit with proper code
    if results.get("status") == "100% OPERATIONAL":
        print("\nSUCCESS: Redis integration complete!")
        exit(0)
    else:
        print("\nWARNING: Check report for issues")
        exit(1)