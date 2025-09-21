"""
Comprehensive data flow verification for ConcordBroker
Ensures all real data is flowing correctly before deployment
"""

import requests
import json
from supabase import create_client
import time
from typing import Dict, List, Any
from datetime import datetime
from colorama import init, Fore, Style

init()  # Initialize colorama for colored output

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class DataFlowVerifier:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.results = {
            "database": {},
            "api": {},
            "frontend": {},
            "search": {},
            "autocomplete": {}
        }
        self.passed_tests = 0
        self.failed_tests = 0

    def print_section(self, title: str):
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

    def print_test(self, test_name: str, passed: bool, details: str = ""):
        if passed:
            self.passed_tests += 1
            status = f"{Fore.GREEN}[PASSED]{Style.RESET_ALL}"
        else:
            self.failed_tests += 1
            status = f"{Fore.RED}[FAILED]{Style.RESET_ALL}"

        print(f"  {status} - {test_name}")
        if details:
            print(f"    {Fore.YELLOW}{details}{Style.RESET_ALL}")

    def verify_database(self):
        """Verify database has real data"""
        self.print_section("1. DATABASE VERIFICATION")

        try:
            # Check total property count
            count_result = self.supabase.table('florida_parcels').select('*', count='exact', head=True).execute()
            total_count = count_result.count
            self.results["database"]["total_properties"] = total_count

            self.print_test(
                "Database property count",
                total_count > 1000000,
                f"Total properties: {total_count:,}"
            )

            # Check sample data
            sample = self.supabase.table('florida_parcels').select('*').limit(10).execute()
            has_data = len(sample.data) > 0
            self.results["database"]["has_sample_data"] = has_data

            self.print_test(
                "Sample data retrieval",
                has_data,
                f"Retrieved {len(sample.data)} sample properties"
            )

            # Verify key fields are populated
            if sample.data:
                first = sample.data[0]
                required_fields = ['parcel_id', 'owner_name', 'phy_addr1']
                missing_fields = [f for f in required_fields if not first.get(f)]

                self.print_test(
                    "Required fields populated",
                    len(missing_fields) == 0,
                    f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
                )

            # Check data diversity (counties)
            counties_result = self.supabase.table('florida_parcels').select('county').execute()
            unique_counties = len(set([p.get('county') for p in counties_result.data[:1000] if p.get('county')]))

            self.print_test(
                "County diversity",
                unique_counties > 5,
                f"Found {unique_counties} unique counties"
            )

        except Exception as e:
            self.print_test("Database connection", False, str(e))

    def verify_api(self):
        """Verify API endpoints are working"""
        self.print_section("2. API VERIFICATION")

        # Test health endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/")
            self.print_test(
                "API health check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("API health check", False, str(e))

        # Test search endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/api/properties/search?limit=10")
            data = response.json()

            has_results = data.get("success") and len(data.get("data", [])) > 0
            self.results["api"]["search_working"] = has_results

            self.print_test(
                "Property search endpoint",
                has_results,
                f"Retrieved {len(data.get('data', []))} properties"
            )

            # Verify data structure
            if has_results:
                first_property = data["data"][0]
                expected_fields = ['parcel_id', 'owner', 'address', 'marketValue']
                missing = [f for f in expected_fields if f not in first_property]

                self.print_test(
                    "API response structure",
                    len(missing) == 0,
                    f"Missing fields: {missing}" if missing else "All expected fields present"
                )

        except Exception as e:
            self.print_test("Property search endpoint", False, str(e))

        # Test autocomplete endpoints
        endpoints = [
            ("/api/autocomplete/addresses", {"query": "100"}),
            ("/api/autocomplete/cities", {"query": "Miami"}),
            ("/api/autocomplete/owners", {"query": "Smith"})
        ]

        for endpoint, params in endpoints:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
                data = response.json()

                success = response.status_code == 200 and len(data) > 0
                endpoint_name = endpoint.split('/')[-1]

                self.print_test(
                    f"Autocomplete {endpoint_name}",
                    success,
                    f"Retrieved {len(data)} suggestions" if success else "No results"
                )

            except Exception as e:
                self.print_test(f"Autocomplete {endpoint_name}", False, str(e))

    def verify_search_functionality(self):
        """Test various search scenarios"""
        self.print_section("3. SEARCH FUNCTIONALITY")

        test_cases = [
            {
                "name": "Search by city",
                "params": {"city": "Miami", "limit": 10},
                "min_results": 1
            },
            {
                "name": "Search by address",
                "params": {"address": "100", "limit": 10},
                "min_results": 1
            },
            {
                "name": "Search by owner",
                "params": {"owner": "LLC", "limit": 10},
                "min_results": 1
            },
            {
                "name": "Search with pagination",
                "params": {"limit": 20, "offset": 0},
                "min_results": 20
            },
            {
                "name": "Search high value properties",
                "params": {"minValue": 1000000, "limit": 10},
                "min_results": 1
            }
        ]

        for test in test_cases:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/properties/search",
                    params=test["params"]
                )
                data = response.json()

                if data.get("success"):
                    result_count = len(data.get("data", []))
                    passed = result_count >= test["min_results"]

                    self.print_test(
                        test["name"],
                        passed,
                        f"Found {result_count} results (expected min: {test['min_results']})"
                    )
                else:
                    self.print_test(test["name"], False, "API returned error")

            except Exception as e:
                self.print_test(test["name"], False, str(e))

    def verify_frontend_integration(self):
        """Verify frontend can access the API"""
        self.print_section("4. FRONTEND INTEGRATION")

        try:
            # Check if frontend is running
            response = requests.get(FRONTEND_URL)
            frontend_running = response.status_code == 200

            self.print_test(
                "Frontend server running",
                frontend_running,
                f"Status: {response.status_code}"
            )

            # Test CORS by simulating frontend request
            headers = {
                "Origin": FRONTEND_URL,
                "Referer": f"{FRONTEND_URL}/properties"
            }

            response = requests.get(
                f"{API_BASE_URL}/api/properties/search?limit=5",
                headers=headers
            )

            cors_working = response.status_code == 200
            self.print_test(
                "CORS configuration",
                cors_working,
                "Frontend can access API" if cors_working else "CORS issue detected"
            )

            # Check API response format matches frontend expectations
            if cors_working:
                data = response.json()
                expected_structure = data.get("success") is not None and "data" in data

                self.print_test(
                    "API response format",
                    expected_structure,
                    "Response structure matches frontend expectations"
                )

        except Exception as e:
            self.print_test("Frontend integration", False, str(e))

    def generate_summary(self):
        """Generate final summary"""
        self.print_section("VERIFICATION SUMMARY")

        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{Fore.WHITE}Total Tests: {total_tests}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {self.passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed_tests}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Pass Rate: {pass_rate:.1f}%{Style.RESET_ALL}")

        if self.failed_tests == 0:
            print(f"\n{Fore.GREEN}[SUCCESS] ALL TESTS PASSED - READY FOR DEPLOYMENT{Style.RESET_ALL}")
            return True
        else:
            print(f"\n{Fore.RED}[FAILED] SOME TESTS FAILED - FIX ISSUES BEFORE DEPLOYMENT{Style.RESET_ALL}")
            return False

    def save_report(self):
        """Save verification report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": {
                "total_tests": self.passed_tests + self.failed_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "pass_rate": (self.passed_tests / (self.passed_tests + self.failed_tests) * 100)
                           if (self.passed_tests + self.failed_tests) > 0 else 0
            }
        }

        with open("verification_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n{Fore.CYAN}Report saved to verification_report.json{Style.RESET_ALL}")

def main():
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}CONCORDBROKER DATA FLOW VERIFICATION{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")

    verifier = DataFlowVerifier()

    # Run all verifications
    verifier.verify_database()
    verifier.verify_api()
    verifier.verify_search_functionality()
    verifier.verify_frontend_integration()

    # Generate summary
    ready_for_deployment = verifier.generate_summary()

    # Save report
    verifier.save_report()

    return ready_for_deployment

if __name__ == "__main__":
    ready = main()
    exit(0 if ready else 1)