/**
 * Comprehensive Frontend UI Test for ConcordBroker
 * Tests all major functionality including navigation, search, property details, and error handling
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:5173';
const TEST_RESULTS_DIR = './test-results';
const SCREENSHOT_DIR = path.join(TEST_RESULTS_DIR, 'screenshots');

// Ensure test directories exist
if (!fs.existsSync(TEST_RESULTS_DIR)) {
    fs.mkdirSync(TEST_RESULTS_DIR, { recursive: true });
}
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

class FrontendTester {
    constructor() {
        this.browser = null;
        this.page = null;
        this.results = {
            testStart: new Date().toISOString(),
            tests: [],
            summary: {
                total: 0,
                passed: 0,
                failed: 0,
                warnings: 0
            },
            consoleErrors: [],
            performanceMetrics: {},
            screenshots: []
        };
    }

    async initialize() {
        console.log('🚀 Starting ConcordBroker Frontend UI Tests...');

        this.browser = await puppeteer.launch({
            headless: false, // Run in visible mode for debugging
            defaultViewport: { width: 1920, height: 1080 },
            args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
        });

        this.page = await this.browser.newPage();

        // Listen for console errors
        this.page.on('console', msg => {
            if (msg.type() === 'error') {
                this.results.consoleErrors.push({
                    timestamp: new Date().toISOString(),
                    message: msg.text(),
                    location: msg.location()
                });
            }
        });

        // Listen for page errors
        this.page.on('pageerror', error => {
            this.results.consoleErrors.push({
                timestamp: new Date().toISOString(),
                message: error.message,
                stack: error.stack,
                type: 'pageerror'
            });
        });
    }

    async takeScreenshot(name, description = '') {
        const filename = `${Date.now()}_${name}.png`;
        const filepath = path.join(SCREENSHOT_DIR, filename);
        await this.page.screenshot({ path: filepath, fullPage: true });

        this.results.screenshots.push({
            name,
            description,
            filename,
            filepath,
            timestamp: new Date().toISOString()
        });

        console.log(`📸 Screenshot saved: ${filename}`);
        return filepath;
    }

    async runTest(testName, testFunction, critical = false) {
        console.log(`\n🧪 Running test: ${testName}`);
        const testStart = Date.now();

        try {
            const result = await testFunction();
            const duration = Date.now() - testStart;

            this.results.tests.push({
                name: testName,
                status: 'passed',
                duration,
                result,
                critical,
                timestamp: new Date().toISOString()
            });

            this.results.summary.passed++;
            console.log(`✅ ${testName} - PASSED (${duration}ms)`);

        } catch (error) {
            const duration = Date.now() - testStart;

            this.results.tests.push({
                name: testName,
                status: 'failed',
                duration,
                error: error.message,
                stack: error.stack,
                critical,
                timestamp: new Date().toISOString()
            });

            this.results.summary.failed++;
            console.log(`❌ ${testName} - FAILED (${duration}ms)`);
            console.log(`   Error: ${error.message}`);

            // Take screenshot on failure
            await this.takeScreenshot(`error_${testName.replace(/\s+/g, '_')}`, `Error in ${testName}`);
        }

        this.results.summary.total++;
    }

    async testLandingPageLoad() {
        await this.page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 30000 });
        await this.takeScreenshot('landing_page_initial', 'Initial landing page load');

        // Check if page loaded
        const title = await this.page.title();
        if (!title.includes('ConcordBroker')) {
            throw new Error(`Expected title to include 'ConcordBroker', got: ${title}`);
        }

        // Check for critical elements
        await this.page.waitForSelector('#root', { timeout: 10000 });

        // Performance metrics
        const metrics = await this.page.metrics();
        this.results.performanceMetrics.landingPage = metrics;

        return { title, loaded: true };
    }

    async testResponsiveDesign() {
        const viewports = [
            { width: 1920, height: 1080, name: 'desktop' },
            { width: 768, height: 1024, name: 'tablet' },
            { width: 375, height: 667, name: 'mobile' }
        ];

        const results = {};

        for (const viewport of viewports) {
            await this.page.setViewport({ width: viewport.width, height: viewport.height });
            await this.page.waitForTimeout(1000); // Allow layout to settle

            await this.takeScreenshot(`responsive_${viewport.name}`, `${viewport.name} view`);

            // Check if page is still functional
            const isVisible = await this.page.evaluate(() => {
                const root = document.getElementById('root');
                return root && root.offsetHeight > 0;
            });

            results[viewport.name] = {
                viewport: viewport,
                functional: isVisible,
                screenshot: `responsive_${viewport.name}.png`
            };
        }

        // Reset to desktop
        await this.page.setViewport({ width: 1920, height: 1080 });

        return results;
    }

    async testNavigation() {
        // Look for common navigation elements
        const navigationTests = [
            { selector: 'nav', name: 'Navigation bar' },
            { selector: '[data-testid*="nav"]', name: 'Navigation test IDs' },
            { selector: 'a[href="/"]', name: 'Home link' },
            { selector: 'a[href*="property"]', name: 'Property links' },
            { selector: 'button', name: 'Interactive buttons' }
        ];

        const results = {};

        for (const test of navigationTests) {
            try {
                const elements = await this.page.$$(test.selector);
                results[test.name] = {
                    found: elements.length > 0,
                    count: elements.length,
                    selector: test.selector
                };

                if (elements.length > 0) {
                    console.log(`   ✓ Found ${elements.length} ${test.name}`);
                }
            } catch (error) {
                results[test.name] = {
                    found: false,
                    error: error.message,
                    selector: test.selector
                };
            }
        }

        await this.takeScreenshot('navigation_analysis', 'Navigation elements analysis');
        return results;
    }

    async testPropertySearch() {
        // Look for search functionality
        const searchSelectors = [
            'input[type="search"]',
            'input[placeholder*="search"]',
            'input[placeholder*="address"]',
            'input[placeholder*="property"]',
            '[data-testid*="search"]',
            '.search-input',
            '#search'
        ];

        let searchInput = null;

        for (const selector of searchSelectors) {
            try {
                searchInput = await this.page.$(selector);
                if (searchInput) {
                    console.log(`   ✓ Found search input with selector: ${selector}`);
                    break;
                }
            } catch (error) {
                continue;
            }
        }

        if (!searchInput) {
            throw new Error('No search input found on the page');
        }

        // Test search functionality
        await searchInput.click();
        await searchInput.type('Miami', { delay: 100 });
        await this.takeScreenshot('search_input_miami', 'Search input with Miami typed');

        // Wait for potential autocomplete/suggestions
        await this.page.waitForTimeout(2000);
        await this.takeScreenshot('search_suggestions', 'Search suggestions/autocomplete');

        // Look for search results or suggestions
        const suggestions = await this.page.$$('[role="option"], .suggestion, .autocomplete-item, [data-testid*="suggestion"]');

        return {
            searchInputFound: true,
            suggestionsCount: suggestions.length,
            searchTerm: 'Miami'
        };
    }

    async testAutocomplete() {
        // Test various search terms for autocomplete
        const testTerms = ['3930', 'Holly', 'Fort Lauderdale', 'LLC'];
        const results = {};

        for (const term of testTerms) {
            try {
                // Find search input
                const searchInput = await this.page.$('input[type="search"], input[placeholder*="search"], [data-testid*="search"]');

                if (searchInput) {
                    // Clear and type new term
                    await searchInput.click({ clickCount: 3 }); // Select all
                    await searchInput.type(term, { delay: 100 });

                    // Wait for autocomplete
                    await this.page.waitForTimeout(1500);
                    await this.takeScreenshot(`autocomplete_${term.replace(/\s+/g, '_')}`, `Autocomplete for ${term}`);

                    // Check for suggestions
                    const suggestions = await this.page.$$('[role="option"], .suggestion, .autocomplete-item, [data-testid*="suggestion"], .dropdown-item');

                    results[term] = {
                        searched: true,
                        suggestionsCount: suggestions.length,
                        hasAutocomplete: suggestions.length > 0
                    };

                    console.log(`   ✓ ${term}: ${suggestions.length} suggestions`);
                } else {
                    results[term] = { error: 'Search input not found' };
                }

            } catch (error) {
                results[term] = { error: error.message };
            }
        }

        return results;
    }

    async testPropertyDetailPages() {
        // Look for property links or cards
        const propertyLinks = await this.page.$$('a[href*="property"], .property-card, [data-testid*="property"]');

        if (propertyLinks.length === 0) {
            // Try to search for a property first
            try {
                const searchInput = await this.page.$('input[type="search"], input[placeholder*="search"]');
                if (searchInput) {
                    await searchInput.click();
                    await searchInput.type('3930', { delay: 100 });
                    await this.page.waitForTimeout(2000);

                    // Look for property results
                    const newPropertyLinks = await this.page.$$('a[href*="property"], .property-card, [data-testid*="property"]');

                    if (newPropertyLinks.length > 0) {
                        await newPropertyLinks[0].click();
                        await this.page.waitForTimeout(3000);
                        await this.takeScreenshot('property_detail_page', 'Property detail page');

                        return {
                            foundViaSearch: true,
                            propertyPageLoaded: true,
                            url: this.page.url()
                        };
                    }
                }
            } catch (error) {
                console.log('   Could not search for property:', error.message);
            }

            throw new Error('No property detail pages accessible');
        }

        // Click on first property
        await propertyLinks[0].click();
        await this.page.waitForTimeout(3000);
        await this.takeScreenshot('property_detail_direct', 'Property detail page (direct access)');

        return {
            propertyLinksFound: propertyLinks.length,
            propertyPageLoaded: true,
            url: this.page.url()
        };
    }

    async testMapIntegration() {
        // Look for map containers
        const mapSelectors = [
            '.map-container',
            '.google-map',
            '#map',
            '[data-testid*="map"]',
            '.leaflet-container',
            'iframe[src*="maps"]',
            'div[class*="map"]'
        ];

        let mapFound = false;
        let mapSelector = null;

        for (const selector of mapSelectors) {
            try {
                const mapElement = await this.page.$(selector);
                if (mapElement) {
                    mapFound = true;
                    mapSelector = selector;
                    console.log(`   ✓ Found map with selector: ${selector}`);
                    break;
                }
            } catch (error) {
                continue;
            }
        }

        await this.takeScreenshot('map_integration_test', 'Map integration test');

        if (!mapFound) {
            return { mapFound: false, message: 'No map elements detected' };
        }

        // Test map interaction if found
        try {
            const mapElement = await this.page.$(mapSelector);
            const boundingBox = await mapElement.boundingBox();

            if (boundingBox) {
                // Click on map to test interaction
                await this.page.click(mapSelector);
                await this.page.waitForTimeout(1000);
                await this.takeScreenshot('map_interaction', 'Map after interaction');
            }
        } catch (error) {
            console.log('   Map interaction test failed:', error.message);
        }

        return {
            mapFound: true,
            mapSelector,
            interactive: true
        };
    }

    async testFormValidation() {
        // Look for forms
        const forms = await this.page.$$('form');
        const inputs = await this.page.$$('input[required], input[type="email"], input[type="tel"]');

        if (forms.length === 0 && inputs.length === 0) {
            return { message: 'No forms or validation inputs found' };
        }

        const results = {
            formsFound: forms.length,
            validationInputsFound: inputs.length,
            validationTests: []
        };

        // Test validation on required inputs
        for (let i = 0; i < Math.min(inputs.length, 3); i++) {
            try {
                const input = inputs[i];
                const inputType = await input.evaluate(el => el.type);
                const isRequired = await input.evaluate(el => el.required);

                if (isRequired) {
                    // Try to submit empty required field
                    await input.focus();
                    await input.type('invalid', { delay: 100 });
                    await this.page.keyboard.press('Tab');
                    await this.page.waitForTimeout(500);

                    // Check for validation messages
                    const validationMessage = await this.page.$('.error, .invalid, [role="alert"]');

                    results.validationTests.push({
                        inputType,
                        hasValidation: !!validationMessage,
                        tested: true
                    });
                }
            } catch (error) {
                results.validationTests.push({
                    error: error.message,
                    tested: false
                });
            }
        }

        await this.takeScreenshot('form_validation_test', 'Form validation test');
        return results;
    }

    async testAPIIntegration() {
        // Monitor network requests
        const apiCalls = [];

        this.page.on('response', response => {
            const url = response.url();
            if (url.includes('api/') || url.includes('supabase') || url.includes('railway')) {
                apiCalls.push({
                    url,
                    status: response.status(),
                    statusText: response.statusText(),
                    timestamp: new Date().toISOString()
                });
            }
        });

        // Trigger actions that should make API calls
        try {
            // Refresh page to trigger initial API calls
            await this.page.reload({ waitUntil: 'networkidle0' });
            await this.page.waitForTimeout(3000);

            // Try searching to trigger search API
            const searchInput = await this.page.$('input[type="search"], input[placeholder*="search"]');
            if (searchInput) {
                await searchInput.click();
                await searchInput.type('test search', { delay: 100 });
                await this.page.waitForTimeout(2000);
            }

        } catch (error) {
            console.log('   API integration test actions failed:', error.message);
        }

        return {
            apiCallsDetected: apiCalls.length,
            apiCalls: apiCalls.slice(0, 10), // First 10 calls
            hasApiIntegration: apiCalls.length > 0
        };
    }

    async testPerformanceAndLoading() {
        // Measure page load performance
        const performanceMetrics = await this.page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime,
                firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime,
            };
        });

        // Check for loading indicators
        const loadingIndicators = await this.page.$$('.loading, .spinner, [data-testid*="loading"], .skeleton');

        // Test lazy loading by scrolling
        await this.page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });

        await this.page.waitForTimeout(2000);
        await this.takeScreenshot('performance_scroll_test', 'Page after scrolling for lazy loading test');

        return {
            performanceMetrics,
            loadingIndicatorsFound: loadingIndicators.length,
            lazyLoadingTested: true
        };
    }

    async checkConsoleErrors() {
        // Console errors are already being collected via event listeners
        const criticalErrors = this.results.consoleErrors.filter(error =>
            error.message.includes('Failed to fetch') ||
            error.message.includes('404') ||
            error.message.includes('500') ||
            error.message.includes('TypeError') ||
            error.message.includes('ReferenceError')
        );

        return {
            totalErrors: this.results.consoleErrors.length,
            criticalErrors: criticalErrors.length,
            errors: this.results.consoleErrors
        };
    }

    async runAllTests() {
        await this.initialize();

        // Test 1: Landing Page Load (Critical)
        await this.runTest('Landing Page Load', () => this.testLandingPageLoad(), true);

        // Test 2: Responsive Design
        await this.runTest('Responsive Design', () => this.testResponsiveDesign());

        // Test 3: Navigation
        await this.runTest('Navigation Elements', () => this.testNavigation());

        // Test 4: Property Search (Critical)
        await this.runTest('Property Search', () => this.testPropertySearch(), true);

        // Test 5: Autocomplete Functionality
        await this.runTest('Autocomplete Functionality', () => this.testAutocomplete());

        // Test 6: Property Detail Pages
        await this.runTest('Property Detail Pages', () => this.testPropertyDetailPages());

        // Test 7: Map Integration
        await this.runTest('Map Integration', () => this.testMapIntegration());

        // Test 8: Form Validation
        await this.runTest('Form Validation', () => this.testFormValidation());

        // Test 9: API Integration
        await this.runTest('API Integration', () => this.testAPIIntegration());

        // Test 10: Performance and Loading
        await this.runTest('Performance and Loading', () => this.testPerformanceAndLoading());

        // Test 11: Console Errors Check
        await this.runTest('Console Errors Check', () => this.checkConsoleErrors());

        // Final screenshot
        await this.takeScreenshot('final_state', 'Final state of the application');

        this.results.testEnd = new Date().toISOString();
        this.results.duration = new Date(this.results.testEnd) - new Date(this.results.testStart);

        return this.results;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
    }

    generateReport() {
        const reportPath = path.join(TEST_RESULTS_DIR, 'frontend_test_report.json');
        fs.writeFileSync(reportPath, JSON.stringify(this.results, null, 2));

        // Generate summary report
        const summaryPath = path.join(TEST_RESULTS_DIR, 'frontend_test_summary.md');
        const summary = this.generateMarkdownSummary();
        fs.writeFileSync(summaryPath, summary);

        console.log(`\n📊 Test Report Generated:`);
        console.log(`   JSON Report: ${reportPath}`);
        console.log(`   Summary: ${summaryPath}`);
        console.log(`   Screenshots: ${SCREENSHOT_DIR}`);

        return { reportPath, summaryPath };
    }

    generateMarkdownSummary() {
        const { summary, tests, consoleErrors } = this.results;
        const criticalFailures = tests.filter(t => t.critical && t.status === 'failed');

        let markdown = `# ConcordBroker Frontend UI Test Report\n\n`;
        markdown += `**Test Date:** ${this.results.testStart}\n`;
        markdown += `**Duration:** ${Math.round(this.results.duration / 1000)}s\n\n`;

        markdown += `## Summary\n\n`;
        markdown += `- **Total Tests:** ${summary.total}\n`;
        markdown += `- **Passed:** ${summary.passed} ✅\n`;
        markdown += `- **Failed:** ${summary.failed} ${summary.failed > 0 ? '❌' : ''}\n`;
        markdown += `- **Console Errors:** ${consoleErrors.length}\n`;
        markdown += `- **Critical Failures:** ${criticalFailures.length}\n\n`;

        if (criticalFailures.length > 0) {
            markdown += `## 🚨 Critical Issues\n\n`;
            criticalFailures.forEach(test => {
                markdown += `### ${test.name}\n`;
                markdown += `**Error:** ${test.error}\n\n`;
            });
        }

        markdown += `## Test Results\n\n`;
        tests.forEach(test => {
            const status = test.status === 'passed' ? '✅' : '❌';
            const critical = test.critical ? ' (Critical)' : '';
            markdown += `### ${status} ${test.name}${critical}\n`;
            markdown += `**Duration:** ${test.duration}ms\n`;

            if (test.status === 'failed') {
                markdown += `**Error:** ${test.error}\n`;
            }

            if (test.result && typeof test.result === 'object') {
                markdown += `**Details:** ${JSON.stringify(test.result, null, 2)}\n`;
            }

            markdown += `\n`;
        });

        if (consoleErrors.length > 0) {
            markdown += `## Console Errors\n\n`;
            consoleErrors.slice(0, 10).forEach((error, index) => {
                markdown += `${index + 1}. **${error.type || 'console'}:** ${error.message}\n`;
            });

            if (consoleErrors.length > 10) {
                markdown += `\n... and ${consoleErrors.length - 10} more errors\n`;
            }
        }

        markdown += `\n## Screenshots\n\n`;
        this.results.screenshots.forEach(screenshot => {
            markdown += `- **${screenshot.name}:** ${screenshot.description} (${screenshot.filename})\n`;
        });

        return markdown;
    }
}

// Main execution
async function main() {
    const tester = new FrontendTester();

    try {
        console.log('🧪 Starting comprehensive frontend UI tests...\n');

        const results = await tester.runAllTests();
        const reports = tester.generateReport();

        console.log('\n' + '='.repeat(60));
        console.log('📊 TEST SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total Tests: ${results.summary.total}`);
        console.log(`Passed: ${results.summary.passed} ✅`);
        console.log(`Failed: ${results.summary.failed} ${results.summary.failed > 0 ? '❌' : ''}`);
        console.log(`Console Errors: ${results.consoleErrors.length}`);
        console.log(`Duration: ${Math.round(results.duration / 1000)}s`);

        const criticalFailures = results.tests.filter(t => t.critical && t.status === 'failed');
        if (criticalFailures.length > 0) {
            console.log('\n🚨 CRITICAL ISSUES DETECTED:');
            criticalFailures.forEach(test => {
                console.log(`   - ${test.name}: ${test.error}`);
            });
        }

        console.log(`\nReports saved to: ${TEST_RESULTS_DIR}`);

    } catch (error) {
        console.error('❌ Test execution failed:', error);
        process.exit(1);
    } finally {
        await tester.cleanup();
    }
}

// Handle process termination
process.on('SIGINT', async () => {
    console.log('\n🛑 Tests interrupted. Cleaning up...');
    process.exit(0);
});

if (require.main === module) {
    main().catch(console.error);
}

module.exports = FrontendTester;