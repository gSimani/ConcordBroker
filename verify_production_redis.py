#!/usr/bin/env python3
"""
Production Redis Integration Verification
Comprehensive test suite to verify 100% functionality
"""

import time
import json
import statistics
import requests
from datetime import datetime
from typing import Dict, List, Tuple
import concurrent.futures

# Production API endpoint
API_URL = "https://concordbroker-production.up.railway.app"
BACKUP_URL = "https://www.concordbroker.com"

class ProductionVerifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "performance": {},
            "redis_status": {},
            "overall_status": "PENDING"
        }

    def test_health_check(self) -> bool:
        """Test if API is running"""
        print("🔍 Testing API health...")
        try:
            # Try primary URL first
            response = requests.get(f"{API_URL}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Primary API is healthy")
                self.results["api_url"] = API_URL
                return True
        except:
            pass

        # Try backup URL
        try:
            response = requests.get(f"{BACKUP_URL}/api/health", timeout=10)
            if response.status_code == 200:
                print("✅ Backup API is healthy")
                self.results["api_url"] = BACKUP_URL
                return True
        except:
            pass

        print("❌ API health check failed")
        return False

    def test_redis_connection(self) -> bool:
        """Test if Redis is connected"""
        print("\n🔍 Testing Redis connection...")
        try:
            base_url = self.results.get("api_url", API_URL)
            response = requests.get(f"{base_url}/api/cache/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.results["redis_status"] = data
                if data.get("connected"):
                    print("✅ Redis is connected")
                    print(f"   - Host: {data.get('host', 'N/A')}")
                    print(f"   - Memory: {data.get('memory_usage', 'N/A')}")
                    return True
        except Exception as e:
            print(f"⚠️ Redis status check error: {e}")

        print("❌ Redis connection test failed")
        return False

    def test_search_performance(self) -> Dict:
        """Test search endpoint performance with caching"""
        print("\n📊 Testing search performance...")
        base_url = self.results.get("api_url", API_URL)

        test_queries = [
            "Miami",
            "3930 SW",
            "Fort Lauderdale",
            "LLC",
            "Broward",
            "beach"
        ]

        results = {
            "cold_cache": [],
            "warm_cache": [],
            "improvement": 0
        }

        # Test each query twice (cold then warm cache)
        for query in test_queries:
            print(f"   Testing: {query}")

            # Cold cache test
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={"q": query, "limit": 20},
                    timeout=30
                )
                cold_time = time.time() - start
                results["cold_cache"].append(cold_time)
                print(f"     Cold: {cold_time:.2f}s")
            except Exception as e:
                print(f"     Cold: Failed - {e}")
                cold_time = 30
                results["cold_cache"].append(cold_time)

            # Warm cache test (immediate retry)
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={"q": query, "limit": 20},
                    timeout=30
                )
                warm_time = time.time() - start
                results["warm_cache"].append(warm_time)
                print(f"     Warm: {warm_time:.2f}s (↓{((1-warm_time/cold_time)*100):.0f}%)")
            except Exception as e:
                print(f"     Warm: Failed - {e}")
                results["warm_cache"].append(30)

        # Calculate improvement
        avg_cold = statistics.mean(results["cold_cache"])
        avg_warm = statistics.mean(results["warm_cache"])
        improvement = ((avg_cold - avg_warm) / avg_cold) * 100

        results["avg_cold_time"] = avg_cold
        results["avg_warm_time"] = avg_warm
        results["improvement"] = improvement

        print(f"\n   📈 Average Performance:")
        print(f"      Cold cache: {avg_cold:.2f}s")
        print(f"      Warm cache: {avg_warm:.2f}s")
        print(f"      Improvement: {improvement:.0f}%")

        return results

    def test_autocomplete_performance(self) -> Dict:
        """Test autocomplete endpoint performance"""
        print("\n🔤 Testing autocomplete performance...")
        base_url = self.results.get("api_url", API_URL)

        test_inputs = ["Mia", "Fort", "Brow", "3930", "LLC"]
        results = {
            "times": [],
            "avg_time": 0
        }

        for input_text in test_inputs:
            print(f"   Testing: {input_text}")
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/autocomplete",
                    params={"q": input_text},
                    timeout=10
                )
                elapsed = time.time() - start
                results["times"].append(elapsed)
                print(f"     Time: {elapsed:.3f}s")
            except Exception as e:
                print(f"     Failed: {e}")
                results["times"].append(10)

        results["avg_time"] = statistics.mean(results["times"])
        print(f"\n   📈 Average autocomplete: {results['avg_time']:.3f}s")

        return results

    def test_property_details(self) -> Dict:
        """Test property details endpoint with caching"""
        print("\n🏠 Testing property details...")
        base_url = self.results.get("api_url", API_URL)

        # Test property IDs
        property_ids = [
            "514310500860",
            "474131031040",
            "514212350330"
        ]

        results = {
            "cold_times": [],
            "warm_times": [],
            "cached_count": 0
        }

        for prop_id in property_ids:
            print(f"   Property: {prop_id}")

            # Cold request
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/properties/{prop_id}",
                    timeout=15
                )
                cold_time = time.time() - start
                results["cold_times"].append(cold_time)

                # Check cache header
                if "X-Cache-Hit" in response.headers:
                    cache_status = "HIT" if response.headers["X-Cache-Hit"] == "true" else "MISS"
                else:
                    cache_status = "UNKNOWN"

                print(f"     Cold: {cold_time:.2f}s (Cache: {cache_status})")
            except Exception as e:
                print(f"     Cold: Failed - {e}")
                results["cold_times"].append(15)

            # Warm request
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/properties/{prop_id}",
                    timeout=15
                )
                warm_time = time.time() - start
                results["warm_times"].append(warm_time)

                # Check cache header
                if "X-Cache-Hit" in response.headers and response.headers["X-Cache-Hit"] == "true":
                    results["cached_count"] += 1
                    cache_status = "HIT"
                else:
                    cache_status = "MISS"

                print(f"     Warm: {warm_time:.2f}s (Cache: {cache_status})")
            except Exception as e:
                print(f"     Warm: Failed - {e}")
                results["warm_times"].append(15)

        results["cache_hit_rate"] = (results["cached_count"] / len(property_ids)) * 100
        print(f"\n   📈 Cache hit rate: {results['cache_hit_rate']:.0f}%")

        return results

    def test_concurrent_load(self) -> Dict:
        """Test system under concurrent load"""
        print("\n⚡ Testing concurrent load...")
        base_url = self.results.get("api_url", API_URL)

        def make_request(query):
            start = time.time()
            try:
                response = requests.get(
                    f"{base_url}/api/properties/search",
                    params={"q": query, "limit": 10},
                    timeout=30
                )
                return time.time() - start, response.status_code == 200
            except:
                return 30, False

        # Simulate 10 concurrent requests
        queries = ["Miami", "Broward", "LLC", "3930", "Fort"] * 2

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        times = [r[0] for r in results]
        successes = [r[1] for r in results]

        stats = {
            "total_requests": len(queries),
            "successful": sum(successes),
            "avg_time": statistics.mean(times),
            "max_time": max(times),
            "min_time": min(times),
            "success_rate": (sum(successes) / len(queries)) * 100
        }

        print(f"   Requests: {stats['total_requests']}")
        print(f"   Success rate: {stats['success_rate']:.0f}%")
        print(f"   Avg time: {stats['avg_time']:.2f}s")
        print(f"   Min/Max: {stats['min_time']:.2f}s / {stats['max_time']:.2f}s")

        return stats

    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "="*60)
        print("📋 PRODUCTION REDIS INTEGRATION REPORT")
        print("="*60)

        # Overall status
        all_passed = all([
            self.results.get("health_passed", False),
            self.results.get("redis_connected", False),
            self.results.get("performance", {}).get("improvement", 0) > 50,
            self.results.get("concurrent", {}).get("success_rate", 0) > 90
        ])

        self.results["overall_status"] = "✅ FULLY OPERATIONAL" if all_passed else "⚠️ PARTIAL SUCCESS"

        print(f"\nSTATUS: {self.results['overall_status']}")

        # Performance summary
        perf = self.results.get("performance", {})
        if perf.get("improvement"):
            print(f"\n🚀 PERFORMANCE IMPROVEMENTS:")
            print(f"   Search caching: {perf['improvement']:.0f}% faster")
            print(f"   Cold cache avg: {perf.get('avg_cold_time', 0):.2f}s")
            print(f"   Warm cache avg: {perf.get('avg_warm_time', 0):.2f}s")

        # Redis status
        redis = self.results.get("redis_status", {})
        if redis.get("connected"):
            print(f"\n💾 REDIS STATUS:")
            print(f"   Connected: ✅")
            print(f"   Host: {redis.get('host', 'N/A')}")
            print(f"   Memory: {redis.get('memory_usage', 'N/A')}")

        # Concurrent load
        concurrent = self.results.get("concurrent", {})
        if concurrent:
            print(f"\n⚡ LOAD TESTING:")
            print(f"   Success rate: {concurrent['success_rate']:.0f}%")
            print(f"   Avg response: {concurrent['avg_time']:.2f}s")

        # Save report
        with open("redis_verification_report.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n✅ Report saved to: redis_verification_report.json")
        print("="*60)

        return all_passed

def main():
    print("🚀 Starting Production Redis Verification...")
    print("="*60)

    verifier = ProductionVerifier()

    # Run tests
    verifier.results["health_passed"] = verifier.test_health_check()

    if verifier.results["health_passed"]:
        verifier.results["redis_connected"] = verifier.test_redis_connection()
        verifier.results["performance"] = verifier.test_search_performance()
        verifier.results["autocomplete"] = verifier.test_autocomplete_performance()
        verifier.results["property_details"] = verifier.test_property_details()
        verifier.results["concurrent"] = verifier.test_concurrent_load()

    # Generate report
    success = verifier.generate_report()

    if success:
        print("\n🎉 VERIFICATION COMPLETE - SYSTEM AT 100%!")
    else:
        print("\n⚠️ VERIFICATION INCOMPLETE - CHECK REPORT FOR ISSUES")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())