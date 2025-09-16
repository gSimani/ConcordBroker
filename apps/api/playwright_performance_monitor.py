"""
Playwright MCP Integration for Performance Monitoring and Testing
Automated testing and monitoring of database and UI performance
"""

from playwright.async_api import async_playwright, Page, Browser
import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics
import aiohttp
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightPerformanceMonitor:
    """
    Automated performance monitoring using Playwright
    Monitors both API endpoints and UI responsiveness
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.results: List[Dict] = []
        self.api_base_url = "http://localhost:8001"
        self.ui_base_url = "http://localhost:5173"
        self.mcp_url = "http://localhost:3001"

        # Performance thresholds
        self.thresholds = {
            'api_response_time': 1.0,  # seconds
            'ui_load_time': 3.0,  # seconds
            'search_time': 2.0,  # seconds
            'filter_apply_time': 1.0,  # seconds
            'image_load_time': 0.5,  # seconds
        }

        # Test scenarios
        self.test_scenarios = [
            'property_search',
            'property_details',
            'filter_application',
            'pagination',
            'map_interaction',
            'image_loading',
            'bulk_operations',
            'concurrent_requests'
        ]

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        logger.info("Playwright browser initialized")

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    async def monitor_api_performance(self) -> Dict[str, Any]:
        """Monitor API endpoint performance"""
        results = {}
        endpoints = [
            ('/api/properties/search/optimized?limit=50', 'GET'),
            ('/api/properties/064210010010/detailed', 'GET'),
            ('/api/analytics/market-trends', 'GET'),
            ('/api/properties/stats/overview', 'GET'),
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints:
                url = f"{self.api_base_url}{endpoint}"
                times = []

                # Test multiple times for average
                for _ in range(5):
                    start_time = time.time()

                    try:
                        if method == 'GET':
                            async with session.get(url) as response:
                                await response.json()
                                response_time = time.time() - start_time
                                times.append(response_time)

                    except Exception as e:
                        logger.error(f"API test failed for {endpoint}: {e}")
                        times.append(999)  # Penalty for failure

                    await asyncio.sleep(0.5)  # Avoid overwhelming

                avg_time = statistics.mean(times)
                results[endpoint] = {
                    'average_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'passed': avg_time < self.thresholds['api_response_time']
                }

        return results

    async def monitor_ui_performance(self) -> Dict[str, Any]:
        """Monitor UI performance and responsiveness"""
        page = await self.browser.new_page()
        results = {}

        try:
            # Test homepage load
            start_time = time.time()
            await page.goto(self.ui_base_url, wait_until='networkidle')
            homepage_load_time = time.time() - start_time

            results['homepage_load'] = {
                'time': homepage_load_time,
                'passed': homepage_load_time < self.thresholds['ui_load_time']
            }

            # Test property search
            search_results = await self.test_property_search(page)
            results['property_search'] = search_results

            # Test filtering
            filter_results = await self.test_filtering(page)
            results['filtering'] = filter_results

            # Test property details page
            details_results = await self.test_property_details(page)
            results['property_details'] = details_results

            # Capture performance metrics
            performance_metrics = await page.evaluate("""
                () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                        domInteractive: perfData.domInteractive - perfData.navigationStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0
                    };
                }
            """)

            results['browser_metrics'] = performance_metrics

        finally:
            await page.close()

        return results

    async def test_property_search(self, page: Page) -> Dict[str, Any]:
        """Test property search functionality"""
        results = {}

        try:
            # Navigate to properties page
            await page.goto(f"{self.ui_base_url}/properties", wait_until='networkidle')

            # Wait for search input
            search_input = await page.wait_for_selector('input[placeholder*="Search"]', timeout=5000)

            # Test search performance
            search_terms = ['Miami', '33139', 'Ocean Drive', 'Smith']

            for term in search_terms:
                await search_input.fill('')
                start_time = time.time()

                # Type search term
                await search_input.type(term, delay=50)

                # Wait for results to update
                await page.wait_for_selector('.property-card', timeout=5000)

                search_time = time.time() - start_time

                # Count results
                results_count = await page.locator('.property-card').count()

                results[term] = {
                    'search_time': search_time,
                    'results_count': results_count,
                    'passed': search_time < self.thresholds['search_time']
                }

                await asyncio.sleep(1)  # Pause between searches

        except Exception as e:
            logger.error(f"Property search test failed: {e}")
            results['error'] = str(e)

        return results

    async def test_filtering(self, page: Page) -> Dict[str, Any]:
        """Test filter application performance"""
        results = {}

        try:
            # Open filters if collapsed
            filter_button = await page.query_selector('button:has-text("Filters")')
            if filter_button:
                await filter_button.click()
                await page.wait_for_timeout(500)

            # Test different filter combinations
            filter_tests = [
                {'min_value': '100000', 'max_value': '500000'},
                {'property_type': 'single_family'},
                {'min_year': '2000', 'max_year': '2020'},
                {'min_sqft': '1500', 'max_sqft': '3000'}
            ]

            for filter_config in filter_tests:
                start_time = time.time()

                # Apply filters
                for field, value in filter_config.items():
                    input_selector = f'input[name="{field}"], select[name="{field}"]'
                    element = await page.query_selector(input_selector)

                    if element:
                        tag_name = await element.evaluate('el => el.tagName')

                        if tag_name == 'SELECT':
                            await element.select_option(value)
                        else:
                            await element.fill(value)

                # Apply filters
                apply_button = await page.query_selector('button:has-text("Apply")')
                if apply_button:
                    await apply_button.click()

                # Wait for results
                await page.wait_for_selector('.property-card', timeout=5000)

                filter_time = time.time() - start_time

                # Count filtered results
                results_count = await page.locator('.property-card').count()

                results[str(filter_config)] = {
                    'filter_time': filter_time,
                    'results_count': results_count,
                    'passed': filter_time < self.thresholds['filter_apply_time']
                }

                # Reset filters
                reset_button = await page.query_selector('button:has-text("Reset")')
                if reset_button:
                    await reset_button.click()
                    await page.wait_for_timeout(500)

        except Exception as e:
            logger.error(f"Filter test failed: {e}")
            results['error'] = str(e)

        return results

    async def test_property_details(self, page: Page) -> Dict[str, Any]:
        """Test property details page loading"""
        results = {}

        try:
            # Navigate to properties list
            await page.goto(f"{self.ui_base_url}/properties", wait_until='networkidle')

            # Wait for property cards
            await page.wait_for_selector('.property-card', timeout=5000)

            # Click first property
            first_property = await page.query_selector('.property-card')
            if first_property:
                start_time = time.time()

                await first_property.click()

                # Wait for details page
                await page.wait_for_selector('.property-details', timeout=5000)

                load_time = time.time() - start_time

                # Check for key elements
                elements_present = {
                    'address': await page.query_selector('.property-address') is not None,
                    'value': await page.query_selector('.property-value') is not None,
                    'owner': await page.query_selector('.property-owner') is not None,
                    'map': await page.query_selector('.property-map') is not None,
                    'tabs': await page.query_selector('.property-tabs') is not None,
                }

                results = {
                    'load_time': load_time,
                    'elements_present': elements_present,
                    'all_elements_loaded': all(elements_present.values()),
                    'passed': load_time < self.thresholds['ui_load_time']
                }

        except Exception as e:
            logger.error(f"Property details test failed: {e}")
            results['error'] = str(e)

        return results

    async def visual_regression_test(self, page: Page) -> Dict[str, Any]:
        """Perform visual regression testing using OpenCV"""
        results = {}

        try:
            # Take screenshots of key pages
            pages_to_test = [
                ('/', 'homepage'),
                ('/properties', 'properties_list'),
                ('/properties/064210010010', 'property_details')
            ]

            for path, name in pages_to_test:
                await page.goto(f"{self.ui_base_url}{path}", wait_until='networkidle')
                await page.wait_for_timeout(1000)  # Allow animations to complete

                # Take screenshot
                screenshot = await page.screenshot(full_page=True)

                # Save screenshot
                screenshot_path = Path(f'screenshots/current_{name}.png')
                screenshot_path.parent.mkdir(exist_ok=True)

                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot)

                # Compare with baseline if exists
                baseline_path = Path(f'screenshots/baseline_{name}.png')

                if baseline_path.exists():
                    diff_score = await self.compare_images(
                        str(baseline_path),
                        str(screenshot_path)
                    )

                    results[name] = {
                        'diff_score': diff_score,
                        'passed': diff_score < 0.1  # Less than 10% difference
                    }
                else:
                    # Save as new baseline
                    screenshot_path.rename(baseline_path)
                    results[name] = {
                        'status': 'baseline_created'
                    }

        except Exception as e:
            logger.error(f"Visual regression test failed: {e}")
            results['error'] = str(e)

        return results

    async def compare_images(self, baseline_path: str, current_path: str) -> float:
        """Compare two images using OpenCV"""
        # Read images
        baseline = cv2.imread(baseline_path)
        current = cv2.imread(current_path)

        # Resize current to match baseline if needed
        if baseline.shape != current.shape:
            current = cv2.resize(current, (baseline.shape[1], baseline.shape[0]))

        # Convert to grayscale
        baseline_gray = cv2.cvtColor(baseline, cv2.COLOR_BGR2GRAY)
        current_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

        # Calculate structural similarity
        score = cv2.matchTemplate(current_gray, baseline_gray, cv2.TM_CCOEFF_NORMED)

        return 1.0 - score.max()  # Return difference score

    async def stress_test_concurrent_requests(self) -> Dict[str, Any]:
        """Stress test with concurrent requests"""
        results = {}
        concurrent_levels = [10, 50, 100]

        for level in concurrent_levels:
            tasks = []
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                for i in range(level):
                    task = self.make_api_request(
                        session,
                        f"{self.api_base_url}/api/properties/search/optimized?page={i+1}&limit=10"
                    )
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = time.time() - start_time

            successful = sum(1 for r in responses if not isinstance(r, Exception))
            failed = sum(1 for r in responses if isinstance(r, Exception))

            results[f'concurrent_{level}'] = {
                'total_time': total_time,
                'successful': successful,
                'failed': failed,
                'avg_time_per_request': total_time / level,
                'success_rate': successful / level
            }

        return results

    async def make_api_request(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Make a single API request"""
        try:
            async with session.get(url) as response:
                return await response.json()
        except Exception as e:
            return {'error': str(e)}

    async def monitor_database_performance(self) -> Dict[str, Any]:
        """Monitor database query performance"""
        results = {}

        test_queries = [
            {
                'name': 'simple_select',
                'endpoint': '/api/properties/search/optimized?limit=10'
            },
            {
                'name': 'complex_filter',
                'endpoint': '/api/properties/search/optimized?min_value=100000&max_value=500000&property_type=single_family&has_tax_deed=true'
            },
            {
                'name': 'aggregation',
                'endpoint': '/api/analytics/market-trends?days=30'
            },
            {
                'name': 'bulk_operation',
                'endpoint': '/api/properties/bulk-search',
                'method': 'POST',
                'data': {'parcel_ids': ['064210010010', '064210010020', '064210010030']}
            }
        ]

        async with aiohttp.ClientSession() as session:
            for test in test_queries:
                url = f"{self.api_base_url}{test['endpoint']}"
                method = test.get('method', 'GET')

                start_time = time.time()

                try:
                    if method == 'GET':
                        async with session.get(url) as response:
                            data = await response.json()
                    else:
                        async with session.post(url, json=test.get('data', {})) as response:
                            data = await response.json()

                    query_time = time.time() - start_time

                    results[test['name']] = {
                        'query_time': query_time,
                        'cached': data.get('cached', False),
                        'actual_query_time': data.get('query_time', query_time),
                        'passed': query_time < self.thresholds['api_response_time']
                    }

                except Exception as e:
                    logger.error(f"Database test failed for {test['name']}: {e}")
                    results[test['name']] = {'error': str(e)}

        return results

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        logger.info("Starting comprehensive performance monitoring...")

        report = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }

        # Run all tests
        try:
            # API Performance
            logger.info("Testing API performance...")
            report['tests']['api'] = await self.monitor_api_performance()

            # UI Performance
            logger.info("Testing UI performance...")
            await self.initialize()
            report['tests']['ui'] = await self.monitor_ui_performance()

            # Visual Regression
            logger.info("Running visual regression tests...")
            page = await self.browser.new_page()
            report['tests']['visual'] = await self.visual_regression_test(page)
            await page.close()

            # Database Performance
            logger.info("Testing database performance...")
            report['tests']['database'] = await self.monitor_database_performance()

            # Stress Testing
            logger.info("Running stress tests...")
            report['tests']['stress'] = await self.stress_test_concurrent_requests()

        finally:
            await self.close()

        # Calculate summary
        all_passed = True
        for test_category, results in report['tests'].items():
            for test_name, test_result in results.items():
                if isinstance(test_result, dict) and 'passed' in test_result:
                    if not test_result['passed']:
                        all_passed = False

        report['summary'] = {
            'all_tests_passed': all_passed,
            'total_tests': sum(len(v) for v in report['tests'].values()),
            'recommendations': self.generate_recommendations(report)
        }

        # Save report
        report_path = Path(f'performance_reports/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Performance report saved to {report_path}")

        return report

    def generate_recommendations(self, report: Dict) -> List[str]:
        """Generate performance recommendations based on test results"""
        recommendations = []

        # Check API performance
        api_tests = report['tests'].get('api', {})
        for endpoint, result in api_tests.items():
            if isinstance(result, dict) and result.get('average_time', 0) > 1.0:
                recommendations.append(f"Optimize API endpoint {endpoint} - average response time {result['average_time']:.2f}s")

        # Check UI performance
        ui_tests = report['tests'].get('ui', {})
        if ui_tests.get('homepage_load', {}).get('time', 0) > 3.0:
            recommendations.append("Homepage load time exceeds 3 seconds - consider lazy loading and code splitting")

        # Check database performance
        db_tests = report['tests'].get('database', {})
        for query_name, result in db_tests.items():
            if isinstance(result, dict) and not result.get('cached', False):
                if result.get('query_time', 0) > 1.0:
                    recommendations.append(f"Database query '{query_name}' is slow - consider adding indexes or caching")

        # Check stress test results
        stress_tests = report['tests'].get('stress', {})
        for level, result in stress_tests.items():
            if isinstance(result, dict) and result.get('success_rate', 1) < 0.95:
                recommendations.append(f"System fails under {level} - improve connection pooling and rate limiting")

        return recommendations


async def main():
    """Run performance monitoring"""
    monitor = PlaywrightPerformanceMonitor()
    report = await monitor.generate_performance_report()

    # Print summary
    print("\n" + "="*50)
    print("PERFORMANCE MONITORING SUMMARY")
    print("="*50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"All Tests Passed: {report['summary']['all_tests_passed']}")
    print(f"Total Tests: {report['summary']['total_tests']}")

    if report['summary']['recommendations']:
        print("\nRecommendations:")
        for i, rec in enumerate(report['summary']['recommendations'], 1):
            print(f"{i}. {rec}")

    print("\nDetailed report saved to performance_reports/")


if __name__ == "__main__":
    asyncio.run(main())