"""
Search Bar Verification System
Specifically tests the search functionality at http://localhost:5174/properties
Uses PySpark to generate test data and Playwright MCP + OpenCV to verify search results
"""

from playwright.async_api import async_playwright
import cv2
import numpy as np
import asyncio
import json
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import re
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchBarVerificationSystem:
    """
    Comprehensive search bar verification system that:
    1. Uses PySpark to analyze search data patterns
    2. Tests search functionality with Playwright MCP
    3. Verifies results accuracy with computer vision
    """

    def __init__(self):
        # Initialize Spark for data analysis
        self.spark = SparkSession.builder \
            .appName("SearchBar_Verification") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .getOrCreate()

        # Browser automation
        self.browser = None
        self.page = None

        # Search test configurations
        self.search_test_cases = []
        self.verification_results = []

    async def initialize_browser(self):
        """Initialize Playwright browser for search testing"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()

        # Add search result extraction script
        await self.page.add_init_script("""
            window.extractSearchResults = function() {
                const results = [];

                // Look for property cards or search result items
                const selectors = [
                    '[data-testid="property-card"]',
                    '.property-card',
                    '[class*="property"]',
                    '[class*="search-result"]',
                    '.search-result',
                    'div[role="listitem"]'
                ];

                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        elements.forEach((el, index) => {
                            const result = {
                                index: index,
                                text: el.textContent || '',
                                html: el.innerHTML || '',
                                classes: el.className || '',
                                position: el.getBoundingClientRect()
                            };

                            // Extract specific data fields
                            const address = el.querySelector('[data-field="address"], .address, .property-address');
                            const owner = el.querySelector('[data-field="owner"], .owner, .property-owner');
                            const city = el.querySelector('[data-field="city"], .city, .property-city');
                            const value = el.querySelector('[data-field="value"], .value, .property-value');

                            if (address) result.address = address.textContent.trim();
                            if (owner) result.owner = owner.textContent.trim();
                            if (city) result.city = city.textContent.trim();
                            if (value) result.value = value.textContent.trim();

                            results.push(result);
                        });
                        break; // Use first matching selector
                    }
                }

                return {
                    total_results: results.length,
                    results: results,
                    search_input_value: document.querySelector('input[placeholder*="Search"]')?.value || '',
                    timestamp: new Date().toISOString()
                };
            };

            window.getSearchBarInfo = function() {
                const searchInput = document.querySelector('input[placeholder*="Search"]');
                return {
                    exists: !!searchInput,
                    placeholder: searchInput?.placeholder || '',
                    value: searchInput?.value || '',
                    enabled: searchInput?.disabled === false,
                    visible: searchInput?.offsetParent !== null
                };
            };
        """)

    def generate_search_test_cases_with_pyspark(self) -> List[Dict]:
        """Generate comprehensive search test cases using PySpark data analysis"""
        logger.info("Generating search test cases with PySpark...")

        # Load Property Appraiser data
        property_df = self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://aws-0-us-east-1.pooler.supabase.com:6543/postgres") \
            .option("dbtable", "florida_parcels") \
            .option("user", "postgres.pmispwtdngkcmsrsjwbp") \
            .option("password", "vM4g2024$$Florida1") \
            .option("driver", "org.postgresql.Driver") \
            .option("fetchsize", "1000") \
            .load()

        # Generate test cases based on actual data patterns
        test_cases = []

        # 1. Address-based searches
        logger.info("Generating address-based test cases...")
        address_samples = property_df.select("phy_addr1", "phy_city", "parcel_id") \
            .filter(col("phy_addr1").isNotNull()) \
            .sample(fraction=0.001) \
            .limit(50) \
            .collect()

        for row in address_samples:
            # Full address search
            test_cases.append({
                "type": "address_full",
                "query": row["phy_addr1"],
                "expected_parcel": row["parcel_id"],
                "expected_city": row["phy_city"],
                "description": f"Full address search: {row['phy_addr1']}"
            })

            # Partial address search
            if row["phy_addr1"] and len(row["phy_addr1"]) > 10:
                partial_address = row["phy_addr1"][:10]
                test_cases.append({
                    "type": "address_partial",
                    "query": partial_address,
                    "expected_parcel": row["parcel_id"],
                    "expected_in_results": row["phy_addr1"],
                    "description": f"Partial address search: {partial_address}"
                })

        # 2. City-based searches
        logger.info("Generating city-based test cases...")
        city_stats = property_df.groupBy("phy_city") \
            .agg(count("*").alias("property_count")) \
            .filter(col("property_count") > 100) \
            .orderBy(col("property_count").desc()) \
            .limit(20) \
            .collect()

        for row in city_stats:
            test_cases.append({
                "type": "city",
                "query": row["phy_city"],
                "expected_count_min": min(100, row["property_count"]),
                "description": f"City search: {row['phy_city']} ({row['property_count']} properties)"
            })

        # 3. Owner name searches
        logger.info("Generating owner-based test cases...")
        owner_samples = property_df.select("owner_name", "parcel_id") \
            .filter(col("owner_name").isNotNull()) \
            .filter(length(col("owner_name")) > 5) \
            .sample(fraction=0.0005) \
            .limit(30) \
            .collect()

        for row in owner_samples:
            # Full owner name
            test_cases.append({
                "type": "owner_full",
                "query": row["owner_name"],
                "expected_parcel": row["parcel_id"],
                "description": f"Owner search: {row['owner_name']}"
            })

            # Partial owner name (first word)
            if row["owner_name"] and " " in row["owner_name"]:
                first_word = row["owner_name"].split()[0]
                if len(first_word) > 3:
                    test_cases.append({
                        "type": "owner_partial",
                        "query": first_word,
                        "expected_in_results": row["owner_name"],
                        "description": f"Partial owner search: {first_word}"
                    })

        # 4. Specific test cases for edge cases
        edge_cases = [
            {
                "type": "empty",
                "query": "",
                "expected_behavior": "show_all_or_placeholder",
                "description": "Empty search query"
            },
            {
                "type": "special_chars",
                "query": "123 Main St.",
                "expected_behavior": "handle_punctuation",
                "description": "Search with punctuation"
            },
            {
                "type": "case_insensitive",
                "query": "MIAMI",
                "expected_behavior": "case_insensitive_match",
                "description": "Uppercase city search"
            },
            {
                "type": "numeric",
                "query": "123",
                "expected_behavior": "numeric_address_search",
                "description": "Numeric address search"
            }
        ]

        test_cases.extend(edge_cases)

        logger.info(f"Generated {len(test_cases)} search test cases")
        return test_cases

    async def test_search_bar_functionality(self, test_case: Dict) -> Dict:
        """Test individual search functionality"""
        logger.info(f"Testing: {test_case['description']}")

        try:
            # Navigate to properties page
            await self.page.goto("http://localhost:5174/properties", wait_until='networkidle')

            # Verify search bar exists and is functional
            search_bar_info = await self.page.evaluate("() => window.getSearchBarInfo()")

            if not search_bar_info["exists"]:
                return {
                    "test_case": test_case,
                    "success": False,
                    "error": "Search bar not found",
                    "timestamp": datetime.now().isoformat()
                }

            # Clear any existing search
            search_input = await self.page.query_selector('input[placeholder*="Search"]')
            await search_input.clear()
            await self.page.wait_for_timeout(500)

            # Perform search
            query = test_case["query"]
            await search_input.fill(query)
            await self.page.wait_for_timeout(1000)  # Wait for autocomplete/suggestions

            # Trigger search (Enter key or search button)
            await search_input.press("Enter")
            await self.page.wait_for_timeout(3000)  # Wait for results

            # Take screenshot before analysis
            screenshot_path = f"search_test_{test_case['type']}_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)

            # Extract search results
            search_results = await self.page.evaluate("() => window.extractSearchResults()")

            # Verify results based on test case type
            verification_result = await self._verify_search_results(test_case, search_results, screenshot_path)

            return {
                "test_case": test_case,
                "success": verification_result["success"],
                "search_results": search_results,
                "verification": verification_result,
                "screenshot_path": screenshot_path,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Search test failed: {e}")
            return {
                "test_case": test_case,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _verify_search_results(self, test_case: Dict, search_results: Dict, screenshot_path: str) -> Dict:
        """Verify search results match expectations"""

        verification = {
            "success": False,
            "details": {},
            "visual_analysis": {}
        }

        try:
            results = search_results.get("results", [])
            total_results = search_results.get("total_results", 0)

            # Type-specific verification
            if test_case["type"] == "address_full":
                # Should find exact parcel
                expected_parcel = test_case.get("expected_parcel")
                found_parcel = any(expected_parcel in result.get("text", "") for result in results)
                verification["success"] = found_parcel
                verification["details"]["found_expected_parcel"] = found_parcel

            elif test_case["type"] == "address_partial":
                # Should find properties containing the address
                expected_address = test_case.get("expected_in_results")
                found_address = any(expected_address.lower() in result.get("text", "").lower() for result in results)
                verification["success"] = found_address
                verification["details"]["found_expected_address"] = found_address

            elif test_case["type"] == "city":
                # Should find multiple properties in the city
                expected_min = test_case.get("expected_count_min", 10)
                has_sufficient_results = total_results >= min(expected_min, 10)  # At least 10 or expected minimum
                verification["success"] = has_sufficient_results
                verification["details"]["result_count"] = total_results
                verification["details"]["expected_minimum"] = expected_min

            elif test_case["type"] == "owner_full":
                # Should find property with exact owner
                expected_parcel = test_case.get("expected_parcel")
                found_property = any(expected_parcel in result.get("text", "") for result in results)
                verification["success"] = found_property
                verification["details"]["found_owner_property"] = found_property

            elif test_case["type"] == "owner_partial":
                # Should find properties with matching owner names
                expected_owner = test_case.get("expected_in_results")
                found_owner = any(expected_owner.lower() in result.get("text", "").lower() for result in results)
                verification["success"] = found_owner
                verification["details"]["found_matching_owner"] = found_owner

            elif test_case["type"] == "empty":
                # Should handle empty search gracefully
                verification["success"] = True  # Any behavior is acceptable for empty search
                verification["details"]["empty_search_handled"] = True

            else:
                # General verification for other types
                verification["success"] = total_results > 0
                verification["details"]["has_results"] = total_results > 0

            # Visual verification using OpenCV
            visual_analysis = await self._analyze_search_results_visually(screenshot_path, test_case["query"])
            verification["visual_analysis"] = visual_analysis

            # Overall success combines logical and visual verification
            verification["success"] = verification["success"] and visual_analysis.get("search_ui_visible", True)

        except Exception as e:
            verification["error"] = str(e)
            verification["success"] = False

        return verification

    async def _analyze_search_results_visually(self, screenshot_path: str, query: str) -> Dict:
        """Analyze search results using OpenCV"""

        try:
            # Read screenshot
            img = cv2.imread(screenshot_path)
            if img is None:
                return {"error": "Could not load screenshot"}

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Check if search query appears in the interface
            import pytesseract

            # Extract text from entire image
            extracted_text = pytesseract.image_to_string(gray)

            # Check for search-related elements
            analysis = {
                "search_ui_visible": self._check_search_ui_visible(extracted_text),
                "query_in_input": query.lower() in extracted_text.lower() if query else True,
                "results_displayed": self._check_results_displayed(extracted_text),
                "no_results_message": "no results" in extracted_text.lower() or "not found" in extracted_text.lower(),
                "extracted_text_length": len(extracted_text)
            }

            # Detect search result cards using contour detection
            analysis["visual_result_count"] = self._count_result_cards(img)

            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _check_search_ui_visible(self, text: str) -> bool:
        """Check if search UI elements are visible"""
        search_indicators = [
            "search",
            "address",
            "properties",
            "owner",
            "city"
        ]

        return any(indicator in text.lower() for indicator in search_indicators)

    def _check_results_displayed(self, text: str) -> bool:
        """Check if results are displayed"""
        result_indicators = [
            "property",
            "parcel",
            "address",
            "owner",
            "value",
            "$"
        ]

        return any(indicator in text.lower() for indicator in result_indicators)

    def _count_result_cards(self, img: np.ndarray) -> int:
        """Count visual result cards using contour detection"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply threshold
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours that could be property cards
            card_count = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # Property cards are typically rectangular and reasonably sized
                if w > 200 and h > 100 and w < 800 and h < 400:
                    aspect_ratio = w / h
                    if 1.5 < aspect_ratio < 6:  # Reasonable aspect ratio for cards
                        card_count += 1

            return min(card_count, 50)  # Cap at reasonable number

        except Exception:
            return 0

    async def run_comprehensive_search_verification(self) -> Dict:
        """Run comprehensive search bar verification"""
        logger.info("="*60)
        logger.info("SEARCH BAR VERIFICATION SYSTEM")
        logger.info("="*60)

        try:
            # Initialize browser
            await self.initialize_browser()

            # Generate test cases with PySpark
            test_cases = self.generate_search_test_cases_with_pyspark()

            # Run tests
            all_results = []
            successful_tests = 0

            for i, test_case in enumerate(test_cases[:20], 1):  # Limit to 20 tests for efficiency
                logger.info(f"\nTest {i}/20: {test_case['type']}")
                result = await self.test_search_bar_functionality(test_case)
                all_results.append(result)

                if result["success"]:
                    successful_tests += 1
                    logger.info(f"✓ PASS: {test_case['description']}")
                else:
                    logger.warning(f"✗ FAIL: {test_case['description']}")

            # Generate comprehensive report
            report = self._generate_search_verification_report(all_results, test_cases)

            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f"search_verification_report_{timestamp}.json", 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"\n✓ Search verification completed")
            logger.info(f"  Tests passed: {successful_tests}/{len(test_cases[:20])}")
            logger.info(f"  Success rate: {(successful_tests/len(test_cases[:20]))*100:.1f}%")

            return report

        except Exception as e:
            logger.error(f"Search verification failed: {e}")
            return {"success": False, "error": str(e)}

        finally:
            if self.browser:
                await self.browser.close()
            self.spark.stop()

    def _generate_search_verification_report(self, results: List[Dict], test_cases: List[Dict]) -> Dict:
        """Generate comprehensive search verification report"""

        successful_tests = sum(1 for r in results if r.get("success", False))
        total_tests = len(results)

        # Analyze by test type
        type_analysis = {}
        for result in results:
            test_type = result["test_case"]["type"]
            if test_type not in type_analysis:
                type_analysis[test_type] = {"total": 0, "passed": 0}

            type_analysis[test_type]["total"] += 1
            if result.get("success", False):
                type_analysis[test_type]["passed"] += 1

        # Calculate success rates by type
        for test_type in type_analysis:
            stats = type_analysis[test_type]
            stats["success_rate"] = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "overall_success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            "test_type_analysis": type_analysis,
            "detailed_results": results,
            "recommendations": self._generate_search_recommendations(results),
            "search_functionality_assessment": self._assess_search_functionality(results)
        }

        return report

    def _generate_search_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        failed_results = [r for r in results if not r.get("success", False)]

        if len(failed_results) == 0:
            recommendations.append("Excellent! All search functionality tests passed.")
        else:
            # Analyze failure patterns
            address_failures = [r for r in failed_results if r["test_case"]["type"].startswith("address")]
            city_failures = [r for r in failed_results if r["test_case"]["type"] == "city"]
            owner_failures = [r for r in failed_results if r["test_case"]["type"].startswith("owner")]

            if address_failures:
                recommendations.append(f"Address search has {len(address_failures)} failures. Check address field indexing and search algorithm.")

            if city_failures:
                recommendations.append(f"City search has {len(city_failures)} failures. Verify city name matching and case sensitivity.")

            if owner_failures:
                recommendations.append(f"Owner search has {len(owner_failures)} failures. Review owner name search implementation.")

        # Visual analysis recommendations
        visual_issues = [r for r in results if not r.get("verification", {}).get("visual_analysis", {}).get("search_ui_visible", True)]
        if visual_issues:
            recommendations.append(f"UI visibility issues detected in {len(visual_issues)} tests. Check search interface rendering.")

        return recommendations

    def _assess_search_functionality(self, results: List[Dict]) -> str:
        """Assess overall search functionality"""
        success_rate = sum(1 for r in results if r.get("success", False)) / len(results) * 100 if results else 0

        if success_rate >= 95:
            return "EXCELLENT: Search functionality is working optimally"
        elif success_rate >= 85:
            return "GOOD: Search functionality is working well with minor issues"
        elif success_rate >= 70:
            return "FAIR: Search functionality has some issues that need attention"
        else:
            return "POOR: Search functionality has significant issues requiring immediate attention"


async def main():
    """Main execution function"""
    verifier = SearchBarVerificationSystem()
    report = await verifier.run_comprehensive_search_verification()

    print("\n" + "="*60)
    print("SEARCH BAR VERIFICATION SUMMARY")
    print("="*60)
    print(f"Overall Success Rate: {report['summary']['overall_success_rate']:.1f}%")
    print(f"Tests Passed: {report['summary']['successful_tests']}/{report['summary']['total_tests']}")
    print(f"Assessment: {report['search_functionality_assessment']}")
    print("\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")


if __name__ == "__main__":
    asyncio.run(main())