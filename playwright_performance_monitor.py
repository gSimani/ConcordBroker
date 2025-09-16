"""
Playwright MCP Performance Monitor for ConcordBroker
Real-time monitoring of website performance using Playwright and computer vision
"""

from playwright.async_api import async_playwright
import asyncio
import cv2
import numpy as np
from datetime import datetime
import json
import time
from typing import Dict, List, Any
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightPerformanceMonitor:
    """
    Monitor website performance using Playwright MCP integration
    with OpenCV for visual analysis
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.metrics_history = []
        self.visual_analysis_results = []

    async def initialize(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--enable-precise-memory-info']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()

        # Enable performance monitoring
        await self.page.add_init_script("""
            window.performanceMetrics = {
                resourceTimings: [],
                navigationTiming: {},
                paintTimings: {},
                memory: {}
            };

            // Capture resource timings
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.performanceMetrics.resourceTimings.push({
                        name: entry.name,
                        duration: entry.duration,
                        startTime: entry.startTime,
                        type: entry.initiatorType
                    });
                }
            }).observe({ entryTypes: ['resource'] });

            // Capture paint timings
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.performanceMetrics.paintTimings[entry.name] = entry.startTime;
                }
            }).observe({ entryTypes: ['paint'] });
        """)

    async def monitor_page_load(self, url: str) -> Dict[str, Any]:
        """Monitor page load performance"""
        start_time = time.time()

        # Navigate to page
        await self.page.goto(url, wait_until='networkidle')

        # Get navigation timing
        navigation_timing = await self.page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    domainLookup: timing.domainLookupEnd - timing.domainLookupStart,
                    tcpConnection: timing.connectEnd - timing.connectStart,
                    request: timing.responseStart - timing.requestStart,
                    response: timing.responseEnd - timing.responseStart,
                    domProcessing: timing.domComplete - timing.domLoading,
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    loadComplete: timing.loadEventEnd - timing.navigationStart
                };
            }
        """)

        # Get resource metrics
        resources = await self.page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                return resources.map(r => ({
                    name: r.name.split('/').pop(),
                    duration: r.duration,
                    size: r.transferSize || 0,
                    type: r.initiatorType
                }));
            }
        """)

        # Get memory usage if available
        memory = await self.page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            }
        """)

        # Take screenshot for visual analysis
        screenshot_path = f"performance_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=screenshot_path, full_page=True)

        # Analyze visual rendering
        visual_metrics = await self.analyze_visual_rendering(screenshot_path)

        total_time = (time.time() - start_time) * 1000

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'total_load_time': total_time,
            'navigation_timing': navigation_timing,
            'resources': {
                'total_count': len(resources),
                'total_size': sum(r['size'] for r in resources),
                'by_type': self._group_resources_by_type(resources)
            },
            'memory': memory,
            'visual_metrics': visual_metrics
        }

        self.metrics_history.append(metrics)
        return metrics

    async def analyze_visual_rendering(self, screenshot_path: str) -> Dict[str, Any]:
        """Use OpenCV to analyze visual rendering quality"""
        img = cv2.imread(screenshot_path)

        if img is None:
            return {}

        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect blank areas (potential loading issues)
        _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        blank_percentage = (np.sum(binary == 255) / binary.size) * 100

        # Detect edges (content complexity)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = (np.sum(edges > 0) / edges.size) * 100

        # Check for loading spinners or placeholders
        # This would need actual spinner templates for template matching
        has_loading_indicators = blank_percentage > 20

        return {
            'blank_area_percentage': round(blank_percentage, 2),
            'content_complexity': round(edge_density, 2),
            'potentially_loading': has_loading_indicators,
            'image_dimensions': img.shape[:2]
        }

    async def monitor_api_calls(self) -> List[Dict]:
        """Monitor API calls made by the page"""
        api_calls = []

        def handle_request(request):
            if '/api/' in request.url:
                api_calls.append({
                    'timestamp': datetime.now().isoformat(),
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })

        def handle_response(response):
            for call in api_calls:
                if call['url'] == response.url:
                    call['status'] = response.status
                    call['duration'] = (datetime.now() - datetime.fromisoformat(call['timestamp'])).total_seconds() * 1000
                    break

        self.page.on('request', handle_request)
        self.page.on('response', handle_response)

        return api_calls

    async def test_search_performance(self) -> Dict[str, Any]:
        """Test search functionality performance"""
        await self.page.goto('http://localhost:5173/properties')

        search_tests = [
            {'query': 'Miami', 'type': 'city'},
            {'query': '33101', 'type': 'zipcode'},
            {'query': 'Smith', 'type': 'owner'},
            {'query': '123 Main St', 'type': 'address'}
        ]

        results = []
        for test in search_tests:
            # Clear search
            search_input = await self.page.query_selector('input[type="search"], input[placeholder*="Search"]')
            if search_input:
                await search_input.fill('')
                await self.page.wait_for_timeout(500)

                # Perform search
                start = time.time()
                await search_input.fill(test['query'])
                await search_input.press('Enter')

                # Wait for results
                await self.page.wait_for_selector('.property-card, [data-testid="property-result"]',
                                                 timeout=10000)

                search_time = (time.time() - start) * 1000

                # Count results
                results_elements = await self.page.query_selector_all('.property-card, [data-testid="property-result"]')

                results.append({
                    'query': test['query'],
                    'type': test['type'],
                    'response_time_ms': round(search_time, 2),
                    'results_count': len(results_elements)
                })

        return {
            'timestamp': datetime.now().isoformat(),
            'search_tests': results,
            'average_response_time': np.mean([r['response_time_ms'] for r in results])
        }

    async def test_filter_performance(self) -> Dict[str, Any]:
        """Test filter functionality performance"""
        await self.page.goto('http://localhost:5173/properties')

        filter_tests = [
            {'minValue': 100000, 'maxValue': 500000},
            {'propertyType': 'single_family'},
            {'yearBuilt': 2000}
        ]

        results = []
        for filters in filter_tests:
            start = time.time()

            # Apply filters (implementation depends on UI)
            # This is a placeholder - adjust based on actual UI
            for key, value in filters.items():
                filter_input = await self.page.query_selector(f'[data-filter="{key}"], [name="{key}"]')
                if filter_input:
                    await filter_input.fill(str(value))

            # Trigger filter application
            apply_button = await self.page.query_selector('button:has-text("Apply"), button:has-text("Search")')
            if apply_button:
                await apply_button.click()

            # Wait for results update
            await self.page.wait_for_timeout(1000)

            filter_time = (time.time() - start) * 1000

            results.append({
                'filters': filters,
                'response_time_ms': round(filter_time, 2)
            })

        return {
            'timestamp': datetime.now().isoformat(),
            'filter_tests': results,
            'average_response_time': np.mean([r['response_time_ms'] for r in results])
        }

    def _group_resources_by_type(self, resources: List[Dict]) -> Dict:
        """Group resources by type for analysis"""
        grouped = {}
        for resource in resources:
            resource_type = resource.get('type', 'other')
            if resource_type not in grouped:
                grouped[resource_type] = {
                    'count': 0,
                    'total_duration': 0,
                    'total_size': 0
                }
            grouped[resource_type]['count'] += 1
            grouped[resource_type]['total_duration'] += resource.get('duration', 0)
            grouped[resource_type]['total_size'] += resource.get('size', 0)
        return grouped

    async def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {'error': 'No metrics collected'}

        df = pd.DataFrame(self.metrics_history)

        report = {
            'summary': {
                'total_tests': len(self.metrics_history),
                'average_load_time': df['total_load_time'].mean(),
                'min_load_time': df['total_load_time'].min(),
                'max_load_time': df['total_load_time'].max(),
                'std_load_time': df['total_load_time'].std()
            },
            'recommendations': self._generate_recommendations(),
            'detailed_metrics': self.metrics_history[-5:]  # Last 5 measurements
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []

        if self.metrics_history:
            latest = self.metrics_history[-1]

            # Check load time
            if latest['total_load_time'] > 3000:
                recommendations.append("Page load time exceeds 3 seconds - implement lazy loading")

            # Check resources
            if latest['resources']['total_count'] > 100:
                recommendations.append("Too many resources - consider bundling and minification")

            # Check memory
            if latest.get('memory') and latest['memory']['usedJSHeapSize'] > 50 * 1024 * 1024:
                recommendations.append("High memory usage - optimize JavaScript and check for memory leaks")

            # Check visual metrics
            if latest.get('visual_metrics', {}).get('blank_area_percentage', 0) > 30:
                recommendations.append("High blank area percentage - check for rendering issues")

        return recommendations

    async def cleanup(self):
        """Clean up resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


async def run_performance_monitoring():
    """Run complete performance monitoring suite"""
    monitor = PlaywrightPerformanceMonitor()

    try:
        await monitor.initialize()
        logger.info("Performance monitor initialized")

        # Monitor main pages
        pages_to_test = [
            'http://localhost:5173',
            'http://localhost:5173/properties',
            'http://localhost:5173/dashboard'
        ]

        for url in pages_to_test:
            logger.info(f"Testing {url}")
            metrics = await monitor.monitor_page_load(url)
            logger.info(f"Load time: {metrics['total_load_time']:.2f}ms")

        # Test search performance
        search_results = await monitor.test_search_performance()
        logger.info(f"Search performance: {search_results['average_response_time']:.2f}ms average")

        # Test filter performance
        filter_results = await monitor.test_filter_performance()
        logger.info(f"Filter performance: {filter_results['average_response_time']:.2f}ms average")

        # Generate report
        report = await monitor.generate_performance_report()

        # Save report
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        logger.info("Performance report generated")
        print("\n" + "="*60)
        print("PERFORMANCE MONITORING REPORT")
        print("="*60)
        print(f"Average Load Time: {report['summary']['average_load_time']:.2f}ms")
        print(f"Min Load Time: {report['summary']['min_load_time']:.2f}ms")
        print(f"Max Load Time: {report['summary']['max_load_time']:.2f}ms")
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(run_performance_monitoring())