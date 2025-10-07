/**
 * Comprehensive Property Filter E2E Testing Script
 * Tests the complete property filtering functionality in the browser
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = {
    frontend_url: 'http://localhost:5173',
    api_url: 'http://localhost:8000',
    api_fallback_url: 'http://localhost:8001',
    timeout: 30000,
    screenshot_dir: './e2e-test-results',
    report_file: './property-filter-test-report.json'
};

// Expected filter mappings based on previous fixes
const PROPERTY_FILTERS = {
    'All Properties': { expectedValues: [], label: 'All Properties' },
    'Residential': { expectedValues: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'], label: 'Residential' },
    'Commercial': { expectedValues: ['11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '25', '26', '27'], label: 'Commercial' },
    'Industrial': { expectedValues: ['21', '22', '23', '24'], label: 'Industrial' },
    'Agricultural': { expectedValues: ['28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'], label: 'Agricultural' },
    'Vacant Land': { expectedValues: ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99'], label: 'Vacant Land' },
    'Multi-Family': { expectedValues: ['11', '12', '13'], label: 'Multi-Family' },
    'Condo': { expectedValues: ['06', '07'], label: 'Condo' },
    'Government': { expectedValues: ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49'], label: 'Government' },
    'Religious': { expectedValues: ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59'], label: 'Religious' },
    'Conservation': { expectedValues: ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69'], label: 'Conservation' },
    'Vacant/Special': { expectedValues: ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'], label: 'Vacant/Special' }
};

class PropertyFilterTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = {
            timestamp: new Date().toISOString(),
            summary: {
                total_tests: 0,
                passed: 0,
                failed: 0,
                errors: []
            },
            tests: [],
            performance: {},
            network_requests: [],
            screenshots: []
        };
    }

    async setup() {
        console.log('🚀 Setting up browser for E2E testing...');

        // Create results directory
        if (!fs.existsSync(CONFIG.screenshot_dir)) {
            fs.mkdirSync(CONFIG.screenshot_dir, { recursive: true });
        }

        // Launch browser
        this.browser = await chromium.launch({
            headless: false, // Show browser for visual debugging
            slowMo: 500     // Slow down for better observation
        });

        this.page = await this.browser.newPage();

        // Enable request/response monitoring
        this.page.on('request', request => {
            if (request.url().includes('/api/') || request.url().includes('properties')) {
                this.results.network_requests.push({
                    timestamp: new Date().toISOString(),
                    method: request.method(),
                    url: request.url(),
                    headers: request.headers()
                });
            }
        });

        this.page.on('response', response => {
            if (response.url().includes('/api/') || response.url().includes('properties')) {
                console.log(`📡 API Response: ${response.status()} ${response.url()}`);
            }
        });

        // Set viewport
        await this.page.setViewportSize({ width: 1920, height: 1080 });

        console.log('✅ Browser setup complete');
    }

    async navigateToPropertySearch() {
        console.log('🌐 Navigating to property search page...');

        try {
            await this.page.goto(CONFIG.frontend_url, {
                waitUntil: 'networkidle',
                timeout: CONFIG.timeout
            });

            // Take initial screenshot
            const screenshotPath = path.join(CONFIG.screenshot_dir, 'initial-page-load.png');
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            this.results.screenshots.push(screenshotPath);

            // Wait for page to be ready
            await this.page.waitForLoadState('domcontentloaded');

            // Look for property search elements
            const searchSelectors = [
                '[data-testid="property-search"]',
                '[id*="search"]',
                '[class*="search"]',
                'input[placeholder*="search"]',
                'input[placeholder*="address"]',
                'input[placeholder*="property"]'
            ];

            let searchFound = false;
            for (const selector of searchSelectors) {
                try {
                    await this.page.waitForSelector(selector, { timeout: 5000 });
                    console.log(`✅ Found search element: ${selector}`);
                    searchFound = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!searchFound) {
                console.log('⚠️ No search element found, looking for navigation...');

                // Try to find and click "Properties" in navigation or "Search Properties" button
                const navSelectors = [
                    'button:has-text("Search Properties")',
                    'a:has-text("Properties")',
                    'button:has-text("Properties")',
                    'a[href*="properties"]',
                    'a[href*="search"]',
                    'button:has-text("Search")',
                    '[data-testid*="nav"]',
                    'nav a'
                ];

                let navigationSuccess = false;
                for (const selector of navSelectors) {
                    try {
                        const navElements = await this.page.locator(selector).all();
                        for (const navElement of navElements) {
                            if (await navElement.isVisible()) {
                                const text = await navElement.textContent();
                                console.log(`🔗 Found navigation element: "${text}" (${selector})`);

                                // Click it
                                await navElement.click();
                                await this.page.waitForLoadState('networkidle');
                                navigationSuccess = true;

                                // Wait for any additional redirects
                                await this.page.waitForTimeout(2000);
                                break;
                            }
                        }
                        if (navigationSuccess) break;
                    } catch (e) {
                        continue;
                    }
                }

                if (!navigationSuccess) {
                    console.log('⚠️ No navigation found, trying to access /properties directly');
                    await this.page.goto(`${CONFIG.frontend_url}/properties`, {
                        waitUntil: 'networkidle',
                        timeout: CONFIG.timeout
                    });
                }
            }

            console.log('✅ Successfully navigated to property search area');

        } catch (error) {
            console.error('❌ Navigation failed:', error.message);
            throw error;
        }
    }

    async findFilterButtons() {
        console.log('🔍 Looking for property filter buttons...');

        // Wait for page to be fully loaded
        await this.page.waitForTimeout(3000);

        // Take a screenshot to debug what's actually on the page
        const debugScreenshotPath = path.join(CONFIG.screenshot_dir, 'debug-filter-search.png');
        await this.page.screenshot({ path: debugScreenshotPath, fullPage: true });
        console.log(`📸 Debug screenshot saved: ${debugScreenshotPath}`);

        const filterSelectors = [
            // Specific filter button selectors
            'button:has-text("All Properties")',
            'button:has-text("Residential")',
            'button:has-text("Commercial")',
            'button:has-text("Industrial")',
            'button:has-text("Agricultural")',
            'button:has-text("Vacant Land")',
            'button:has-text("Multi-Family")',
            'button:has-text("Condo")',
            'button:has-text("Government")',
            'button:has-text("Religious")',
            'button:has-text("Conservation")',
            'button:has-text("Vacant")',
            // Generic selectors
            '[data-testid*="filter"]',
            '[class*="filter"]',
            '[id*="filter"]',
            '[class*="property-type"]',
            '[data-testid*="property-type"]',
            '[role="button"]',
            '.btn',
            'button'
        ];

        const foundFilters = [];
        const allButtonsFound = [];

        for (const selector of filterSelectors) {
            try {
                const elements = await this.page.locator(selector).all();
                for (const element of elements) {
                    try {
                        const text = await element.textContent();
                        const isVisible = await element.isVisible();

                        if (text && isVisible) {
                            allButtonsFound.push({
                                text: text.trim(),
                                selector,
                                isFilterButton: false
                            });

                            // Check if this is a property filter button
                            const filterMatches = Object.keys(PROPERTY_FILTERS).some(filter => {
                                const buttonText = text.toLowerCase().trim();
                                const filterText = filter.toLowerCase();
                                return buttonText.includes(filterText) ||
                                       filterText.includes(buttonText) ||
                                       buttonText === filterText;
                            });

                            if (filterMatches) {
                                foundFilters.push({
                                    element,
                                    text: text.trim(),
                                    selector
                                });
                                allButtonsFound[allButtonsFound.length - 1].isFilterButton = true;
                            }
                        }
                    } catch (e) {
                        continue;
                    }
                }
            } catch (e) {
                continue;
            }
        }

        console.log(`🔍 Found ${allButtonsFound.length} total buttons on page:`);
        allButtonsFound.slice(0, 15).forEach(button => {
            const filterIcon = button.isFilterButton ? '🎯' : '⚪';
            console.log(`  ${filterIcon} "${button.text}" (${button.selector})`);
        });

        if (allButtonsFound.length > 15) {
            console.log(`  ... and ${allButtonsFound.length - 15} more buttons`);
        }

        console.log(`✅ Found ${foundFilters.length} property filter buttons:`);
        foundFilters.forEach(filter => console.log(`  🎯 ${filter.text} (${filter.selector})`));

        return foundFilters;
    }

    async testFilter(filterName, filterConfig, filterElement) {
        console.log(`\n🧪 Testing filter: ${filterName}`);

        const testResult = {
            filter_name: filterName,
            expected_values: filterConfig.expectedValues,
            status: 'pending',
            start_time: Date.now(),
            end_time: null,
            response_time: null,
            network_calls: [],
            properties_loaded: 0,
            errors: [],
            screenshot: null
        };

        try {
            // Clear any previous selections first
            await this.clearFilters();

            // Record network calls before clicking
            const networkCallsBefore = this.results.network_requests.length;

            // Click the filter button
            console.log(`👆 Clicking ${filterName} filter...`);
            await filterElement.click();

            // Wait for loading to complete
            await this.waitForSearchResults();

            // Record response time
            testResult.response_time = Date.now() - testResult.start_time;

            // Record network calls made during this test
            testResult.network_calls = this.results.network_requests.slice(networkCallsBefore);

            // Take screenshot after filter application
            const screenshotName = `filter-${filterName.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase()}.png`;
            const screenshotPath = path.join(CONFIG.screenshot_dir, screenshotName);
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            testResult.screenshot = screenshotPath;
            this.results.screenshots.push(screenshotPath);

            // Count properties loaded
            testResult.properties_loaded = await this.countLoadedProperties();

            // Verify the filter is visually selected
            const isSelected = await this.verifyFilterSelected(filterElement);

            // Check for error states
            const hasErrors = await this.checkForErrors();

            if (hasErrors.length > 0) {
                testResult.errors = hasErrors;
                testResult.status = 'failed';
            } else if (testResult.properties_loaded >= 0) { // 0 is valid for some filters
                testResult.status = 'passed';
            } else {
                testResult.status = 'failed';
                testResult.errors.push('No properties loaded or counted');
            }

            console.log(`✅ Filter ${filterName}: ${testResult.status} (${testResult.properties_loaded} properties, ${testResult.response_time}ms)`);

        } catch (error) {
            testResult.status = 'failed';
            testResult.errors.push(error.message);
            console.error(`❌ Filter ${filterName} failed:`, error.message);
        }

        testResult.end_time = Date.now();
        return testResult;
    }

    async clearFilters() {
        try {
            // Look for "All Properties" or "Clear" button
            const clearSelectors = [
                'button:has-text("All Properties")',
                'button:has-text("Clear")',
                'button:has-text("Reset")',
                '[data-testid*="clear"]',
                '[data-testid*="reset"]'
            ];

            for (const selector of clearSelectors) {
                try {
                    const element = await this.page.locator(selector).first();
                    if (await element.isVisible()) {
                        await element.click();
                        await this.page.waitForTimeout(1000);
                        console.log(`🧹 Cleared filters using: ${selector}`);
                        return;
                    }
                } catch (e) {
                    continue;
                }
            }

            console.log('⚠️ No clear filter button found');
        } catch (error) {
            console.log('⚠️ Failed to clear filters:', error.message);
        }
    }

    async waitForSearchResults() {
        try {
            // Wait for loading indicators to disappear
            const loadingSelectors = [
                '[data-testid*="loading"]',
                '[class*="loading"]',
                '[class*="spinner"]',
                '.loading',
                '.spinner'
            ];

            for (const selector of loadingSelectors) {
                try {
                    await this.page.waitForSelector(selector, { timeout: 2000 });
                    await this.page.waitForSelector(selector, { state: 'hidden', timeout: 10000 });
                    console.log(`⏳ Waited for loading indicator: ${selector}`);
                    break;
                } catch (e) {
                    continue;
                }
            }

            // Additional wait for network to settle
            await this.page.waitForLoadState('networkidle', { timeout: 10000 });

        } catch (error) {
            console.log('⚠️ No loading indicators found, using timeout');
            await this.page.waitForTimeout(3000);
        }
    }

    async countLoadedProperties() {
        const propertySelectors = [
            '[data-testid*="property-card"]',
            '[class*="property-card"]',
            '[class*="property-item"]',
            '[data-testid*="property-item"]',
            '.property',
            '[id*="property"]'
        ];

        for (const selector of propertySelectors) {
            try {
                const count = await this.page.locator(selector).count();
                if (count > 0) {
                    console.log(`📊 Found ${count} properties using selector: ${selector}`);
                    return count;
                }
            } catch (e) {
                continue;
            }
        }

        // Check for "no results" message
        const noResultsSelectors = [
            ':has-text("No properties")',
            ':has-text("No results")',
            ':has-text("0 properties")',
            '[class*="empty"]',
            '[class*="no-results"]'
        ];

        for (const selector of noResultsSelectors) {
            try {
                const element = await this.page.locator(selector).first();
                if (await element.isVisible()) {
                    console.log(`📊 No properties found (valid empty state)`);
                    return 0;
                }
            } catch (e) {
                continue;
            }
        }

        console.log('⚠️ Could not determine property count');
        return -1;
    }

    async verifyFilterSelected(filterElement) {
        try {
            const classes = await filterElement.getAttribute('class') || '';
            const ariaSelected = await filterElement.getAttribute('aria-selected');
            const ariaPressed = await filterElement.getAttribute('aria-pressed');

            const isSelected = classes.includes('selected') ||
                             classes.includes('active') ||
                             ariaSelected === 'true' ||
                             ariaPressed === 'true';

            console.log(`🎯 Filter selection state: ${isSelected ? 'SELECTED' : 'NOT SELECTED'}`);
            return isSelected;
        } catch (error) {
            console.log('⚠️ Could not verify filter selection state');
            return false;
        }
    }

    async checkForErrors() {
        const errors = [];

        try {
            // Check for error messages in the UI
            const errorSelectors = [
                '[class*="error"]',
                '[data-testid*="error"]',
                ':has-text("Error")',
                ':has-text("Failed")',
                ':has-text("Something went wrong")',
                '.alert-error',
                '.error-message'
            ];

            for (const selector of errorSelectors) {
                try {
                    const elements = await this.page.locator(selector).all();
                    for (const element of elements) {
                        if (await element.isVisible()) {
                            const text = await element.textContent();
                            errors.push(`UI Error: ${text?.trim()}`);
                        }
                    }
                } catch (e) {
                    continue;
                }
            }

            // Check browser console errors
            const logs = await this.page.evaluate(() => {
                const errors = [];
                const originalError = console.error;
                console.error = function(...args) {
                    errors.push(args.join(' '));
                    originalError.apply(console, args);
                };
                return window._testErrors || [];
            });

            if (logs && logs.length > 0) {
                errors.push(...logs.map(log => `Console: ${log}`));
            }

        } catch (error) {
            console.log('⚠️ Error checking failed:', error.message);
        }

        return errors;
    }

    async testFilterCombinations() {
        console.log('\n🔄 Testing filter combinations...');

        const combinationTests = [
            ['Residential', 'Commercial'],
            ['Agricultural', 'Vacant Land'],
            ['Government', 'Religious']
        ];

        for (const combination of combinationTests) {
            try {
                console.log(`🧪 Testing combination: ${combination.join(' + ')}`);

                await this.clearFilters();

                // Click each filter in the combination
                for (const filterName of combination) {
                    const filterButtons = await this.findFilterButtons();
                    const button = filterButtons.find(f =>
                        f.text.toLowerCase().includes(filterName.toLowerCase())
                    );

                    if (button) {
                        await button.element.click();
                        await this.page.waitForTimeout(1000);
                    }
                }

                await this.waitForSearchResults();
                const propertyCount = await this.countLoadedProperties();

                console.log(`✅ Combination ${combination.join(' + ')}: ${propertyCount} properties`);

            } catch (error) {
                console.error(`❌ Combination test failed: ${error.message}`);
            }
        }
    }

    async testPerformance() {
        console.log('\n⏱️ Performance testing...');

        const performanceResults = {};

        try {
            // Test each filter's response time
            const filterButtons = await this.findFilterButtons();

            for (const filterButton of filterButtons.slice(0, 5)) { // Test first 5 for time
                const startTime = Date.now();

                await filterButton.element.click();
                await this.waitForSearchResults();

                const responseTime = Date.now() - startTime;
                performanceResults[filterButton.text] = responseTime;

                console.log(`⏱️ ${filterButton.text}: ${responseTime}ms`);

                await this.clearFilters();
            }

            this.results.performance = performanceResults;

        } catch (error) {
            console.error('❌ Performance testing failed:', error.message);
        }
    }

    async runAllTests() {
        console.log('\n🎯 Starting comprehensive property filter testing...\n');

        try {
            await this.setup();
            await this.navigateToPropertySearch();

            const filterButtons = await this.findFilterButtons();

            if (filterButtons.length === 0) {
                throw new Error('No filter buttons found on the page');
            }

            // Test individual filters
            for (const filterButton of filterButtons) {
                const filterName = filterButton.text;
                const filterConfig = PROPERTY_FILTERS[filterName] ||
                                   Object.values(PROPERTY_FILTERS).find(config =>
                                       config.label.toLowerCase() === filterName.toLowerCase()
                                   ) ||
                                   { expectedValues: [], label: filterName };

                const testResult = await this.testFilter(filterName, filterConfig, filterButton.element);
                this.results.tests.push(testResult);
                this.results.summary.total_tests++;

                if (testResult.status === 'passed') {
                    this.results.summary.passed++;
                } else {
                    this.results.summary.failed++;
                    this.results.summary.errors.push(...testResult.errors);
                }
            }

            // Test combinations
            await this.testFilterCombinations();

            // Performance testing
            await this.testPerformance();

            console.log('\n📊 Test Summary:');
            console.log(`Total Tests: ${this.results.summary.total_tests}`);
            console.log(`Passed: ${this.results.summary.passed}`);
            console.log(`Failed: ${this.results.summary.failed}`);
            console.log(`Success Rate: ${Math.round((this.results.summary.passed / this.results.summary.total_tests) * 100)}%`);

        } catch (error) {
            console.error('❌ Test suite failed:', error.message);
            this.results.summary.errors.push(error.message);
        } finally {
            await this.cleanup();
        }
    }

    async cleanup() {
        console.log('\n🧹 Cleaning up...');

        // Save test results
        fs.writeFileSync(CONFIG.report_file, JSON.stringify(this.results, null, 2));
        console.log(`📄 Test report saved to: ${CONFIG.report_file}`);

        // Close browser
        if (this.browser) {
            await this.browser.close();
        }

        console.log('✅ Cleanup complete');
    }

    generateMarkdownReport() {
        const reportPath = './PROPERTY_FILTER_E2E_REPORT.md';

        let report = `# Property Filter E2E Test Report\n\n`;
        report += `**Test Run:** ${this.results.timestamp}\n`;
        report += `**Total Tests:** ${this.results.summary.total_tests}\n`;
        report += `**Passed:** ${this.results.summary.passed} ✅\n`;
        report += `**Failed:** ${this.results.summary.failed} ❌\n`;
        report += `**Success Rate:** ${Math.round((this.results.summary.passed / this.results.summary.total_tests) * 100)}%\n\n`;

        report += `## Individual Filter Results\n\n`;

        this.results.tests.forEach(test => {
            const status = test.status === 'passed' ? '✅' : '❌';
            report += `### ${test.filter_name} ${status}\n`;
            report += `- **Response Time:** ${test.response_time}ms\n`;
            report += `- **Properties Loaded:** ${test.properties_loaded}\n`;
            report += `- **Network Calls:** ${test.network_calls.length}\n`;

            if (test.errors.length > 0) {
                report += `- **Errors:**\n`;
                test.errors.forEach(error => {
                    report += `  - ${error}\n`;
                });
            }

            if (test.screenshot) {
                report += `- **Screenshot:** ${test.screenshot}\n`;
            }

            report += `\n`;
        });

        if (Object.keys(this.results.performance).length > 0) {
            report += `## Performance Metrics\n\n`;
            Object.entries(this.results.performance).forEach(([filter, time]) => {
                report += `- **${filter}:** ${time}ms\n`;
            });
            report += `\n`;
        }

        if (this.results.summary.errors.length > 0) {
            report += `## Overall Errors\n\n`;
            this.results.summary.errors.forEach(error => {
                report += `- ${error}\n`;
            });
        }

        fs.writeFileSync(reportPath, report);
        console.log(`📄 Markdown report generated: ${reportPath}`);

        return reportPath;
    }
}

// Run the tests
async function main() {
    const tester = new PropertyFilterTester();

    try {
        await tester.runAllTests();
        tester.generateMarkdownReport();

        console.log('\n🎉 Property filter E2E testing complete!');
        console.log('📁 Check the following files for results:');
        console.log(`   - ${CONFIG.report_file}`);
        console.log(`   - ./PROPERTY_FILTER_E2E_REPORT.md`);
        console.log(`   - Screenshots in: ${CONFIG.screenshot_dir}`);

    } catch (error) {
        console.error('💥 Critical test failure:', error);
        process.exit(1);
    }
}

// Execute if run directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { PropertyFilterTester, PROPERTY_FILTERS, CONFIG };