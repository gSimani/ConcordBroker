const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testPropertySearchComponent() {
    console.log('Testing PropertySearch Component Functionality...\n');

    const browser = await chromium.launch({
        headless: false,
        args: ['--start-maximized']
    });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });

    const screenshotDir = path.join(__dirname, 'property-search-test-results');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir);
    }

    const testResults = {
        timestamp: new Date().toISOString(),
        sites: {
            local: await testSite(context, 'http://localhost:5173/properties', 'local', screenshotDir),
            production: await testSite(context, 'https://www.concordbroker.com/properties', 'production', screenshotDir)
        }
    };

    // Generate comparison report
    generateTestReport(testResults, screenshotDir);

    await browser.close();
    console.log('\n✅ PropertySearch component testing completed!');
    console.log(`📁 Results saved in: ${screenshotDir}`);
}

async function testSite(context, url, siteName, screenshotDir) {
    console.log(`\n🧪 Testing ${siteName}: ${url}`);

    const page = await context.newPage();
    const results = {
        url,
        siteName,
        status: 'unknown',
        consoleErrors: [],
        networkErrors: [],
        componentTests: {},
        performance: {},
        screenshots: []
    };

    // Monitor console and network errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            results.consoleErrors.push(msg.text());
        }
    });

    page.on('response', response => {
        if (!response.ok() && response.status() >= 400) {
            results.networkErrors.push(`${response.status()} ${response.url()}`);
        }
    });

    try {
        const startTime = Date.now();

        // Navigate to page
        await page.goto(url, {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        results.performance.loadTime = Date.now() - startTime;
        results.status = 'loaded';

        console.log(`  ✅ Page loaded in ${results.performance.loadTime}ms`);

        // Test 1: Check if PropertySearch component exists
        console.log('  🔍 Testing PropertySearch component presence...');
        results.componentTests.propertySearchExists = await testComponentExists(page);

        // Test 2: Check search functionality
        console.log('  🔍 Testing search functionality...');
        results.componentTests.searchFunctionality = await testSearchFunctionality(page);

        // Test 3: Check filter functionality
        console.log('  🔍 Testing filter functionality...');
        results.componentTests.filterFunctionality = await testFilterFunctionality(page);

        // Test 4: Check property results display
        console.log('  🔍 Testing property results display...');
        results.componentTests.propertyResults = await testPropertyResults(page);

        // Test 5: Check responsive design
        console.log('  🔍 Testing responsive design...');
        results.componentTests.responsiveDesign = await testResponsiveDesign(page);

        // Take screenshots at different stages
        await takeTestScreenshots(page, siteName, screenshotDir, results);

        console.log(`  ✅ ${siteName} testing completed successfully`);

    } catch (error) {
        results.status = 'error';
        results.error = error.message;
        console.log(`  ❌ ${siteName} testing failed: ${error.message}`);

        // Take error screenshot
        const errorScreenshot = path.join(screenshotDir, `${siteName}-error.png`);
        await page.screenshot({ path: errorScreenshot, fullPage: true });
        results.screenshots.push(errorScreenshot);
    }

    await page.close();
    return results;
}

async function testComponentExists(page) {
    try {
        // Look for PropertySearch or FastPropertySearch component
        const selectors = [
            '[data-testid="property-search"]',
            '[data-testid="fast-property-search"]',
            '.property-search',
            '.search-container',
            'input[placeholder*="search" i]',
            'input[placeholder*="property" i]'
        ];

        let found = false;
        let foundSelector = null;

        for (const selector of selectors) {
            if (await page.locator(selector).isVisible()) {
                found = true;
                foundSelector = selector;
                break;
            }
        }

        return {
            passed: found,
            foundSelector,
            message: found ? `PropertySearch component found: ${foundSelector}` : 'PropertySearch component not found'
        };
    } catch (error) {
        return {
            passed: false,
            error: error.message,
            message: 'Error checking component existence'
        };
    }
}

async function testSearchFunctionality(page) {
    try {
        // Find search input
        const searchInput = page.locator('input[placeholder*="search" i], input[type="search"], input[name*="search"]').first();

        if (!(await searchInput.isVisible())) {
            return {
                passed: false,
                message: 'Search input not found'
            };
        }

        // Test typing in search
        await searchInput.fill('Miami');
        await page.waitForTimeout(1000);

        // Check if search triggered any response
        const hasResults = await page.locator('[data-testid*="property"], .property-card, .search-result').count() > 0;
        const hasLoading = await page.locator('[data-testid*="loading"], .loading, .spinner').isVisible();

        return {
            passed: hasResults || hasLoading,
            message: hasResults ? 'Search functionality working - results found' :
                    hasLoading ? 'Search functionality working - loading detected' :
                    'Search input present but no response detected'
        };
    } catch (error) {
        return {
            passed: false,
            error: error.message,
            message: 'Error testing search functionality'
        };
    }
}

async function testFilterFunctionality(page) {
    try {
        // Look for filter components
        const filterElements = await page.locator('[data-testid*="filter"], .filter, select, [role="combobox"]').count();

        if (filterElements === 0) {
            return {
                passed: false,
                message: 'No filter elements found'
            };
        }

        // Try to interact with first filter
        const firstFilter = page.locator('[data-testid*="filter"], .filter, select').first();
        if (await firstFilter.isVisible()) {
            // Try clicking/focusing the filter
            await firstFilter.click();
            await page.waitForTimeout(500);
        }

        return {
            passed: true,
            message: `Found ${filterElements} filter elements`
        };
    } catch (error) {
        return {
            passed: false,
            error: error.message,
            message: 'Error testing filter functionality'
        };
    }
}

async function testPropertyResults(page) {
    try {
        // Look for property cards or results
        const propertyCards = await page.locator('[data-testid*="property"], .property-card, .property-item').count();

        // Check for empty state or no results message
        const emptyState = await page.locator('[data-testid*="empty"], .no-results, .empty-state').isVisible();

        // Check for loading state
        const isLoading = await page.locator('[data-testid*="loading"], .loading, .spinner').isVisible();

        return {
            passed: propertyCards > 0 || emptyState || isLoading,
            propertyCount: propertyCards,
            message: propertyCards > 0 ? `Found ${propertyCards} property cards` :
                    emptyState ? 'Empty state displayed correctly' :
                    isLoading ? 'Loading state active' :
                    'No property results or appropriate messaging found'
        };
    } catch (error) {
        return {
            passed: false,
            error: error.message,
            message: 'Error testing property results'
        };
    }
}

async function testResponsiveDesign(page) {
    try {
        const results = {};

        // Test desktop (current)
        results.desktop = await page.locator('[data-testid="property-search"], .property-search').isVisible();

        // Test tablet
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(500);
        results.tablet = await page.locator('[data-testid="property-search"], .property-search').isVisible();

        // Test mobile
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
        results.mobile = await page.locator('[data-testid="property-search"], .property-search').isVisible();

        // Reset to desktop
        await page.setViewportSize({ width: 1920, height: 1080 });

        const allPassed = results.desktop && results.tablet && results.mobile;

        return {
            passed: allPassed,
            results,
            message: allPassed ? 'Responsive design working on all breakpoints' :
                    `Issues on: ${Object.entries(results).filter(([k,v]) => !v).map(([k,v]) => k).join(', ')}`
        };
    } catch (error) {
        return {
            passed: false,
            error: error.message,
            message: 'Error testing responsive design'
        };
    }
}

async function takeTestScreenshots(page, siteName, screenshotDir, results) {
    try {
        // Main page screenshot
        const mainScreenshot = path.join(screenshotDir, `${siteName}-main.png`);
        await page.screenshot({ path: mainScreenshot, fullPage: true });
        results.screenshots.push(mainScreenshot);

        // Mobile screenshot
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
        const mobileScreenshot = path.join(screenshotDir, `${siteName}-mobile.png`);
        await page.screenshot({ path: mobileScreenshot, fullPage: true });
        results.screenshots.push(mobileScreenshot);

        // Reset viewport
        await page.setViewportSize({ width: 1920, height: 1080 });
    } catch (error) {
        console.log(`    ⚠️ Screenshot error: ${error.message}`);
    }
}

function generateTestReport(testResults, screenshotDir) {
    const reportPath = path.join(screenshotDir, 'property-search-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));

    // Generate HTML report
    const htmlReport = generateHTMLReport(testResults);
    const htmlPath = path.join(screenshotDir, 'property-search-test-report.html');
    fs.writeFileSync(htmlPath, htmlReport);

    console.log('\n📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(50));

    for (const [siteName, siteResults] of Object.entries(testResults.sites)) {
        console.log(`\n${siteName.toUpperCase()} (${siteResults.url}):`);
        console.log(`  Status: ${siteResults.status}`);
        console.log(`  Console Errors: ${siteResults.consoleErrors.length}`);
        console.log(`  Network Errors: ${siteResults.networkErrors.length}`);

        if (siteResults.performance.loadTime) {
            console.log(`  Load Time: ${siteResults.performance.loadTime}ms`);
        }

        console.log('  Component Tests:');
        for (const [testName, testResult] of Object.entries(siteResults.componentTests)) {
            const status = testResult.passed ? '✅' : '❌';
            console.log(`    ${testName}: ${status} ${testResult.message}`);
        }
    }

    console.log(`\n📁 Full report: ${htmlPath}`);
    console.log(`📁 JSON data: ${reportPath}`);
}

function generateHTMLReport(testResults) {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>PropertySearch Component Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; margin-bottom: 20px; }
        .site-section { border: 1px solid #ddd; margin: 20px 0; padding: 20px; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .test-result { margin: 10px 0; padding: 10px; background: #f8f9fa; }
        .screenshots { display: flex; gap: 20px; margin: 20px 0; }
        .screenshot { max-width: 300px; }
        .screenshot img { width: 100%; border: 1px solid #ddd; }
        pre { background: #f8f9fa; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PropertySearch Component Test Report</h1>
        <p>Generated: ${testResults.timestamp}</p>
    </div>

    ${Object.entries(testResults.sites).map(([siteName, siteResults]) => `
        <div class="site-section">
            <h2>${siteName.toUpperCase()}: ${siteResults.url}</h2>

            <div class="test-result">
                <strong>Status:</strong> <span class="${siteResults.status === 'loaded' ? 'passed' : 'failed'}">${siteResults.status}</span>
            </div>

            ${siteResults.performance.loadTime ? `
                <div class="test-result">
                    <strong>Load Time:</strong> ${siteResults.performance.loadTime}ms
                </div>
            ` : ''}

            <h3>Component Tests</h3>
            ${Object.entries(siteResults.componentTests).map(([testName, testResult]) => `
                <div class="test-result">
                    <strong>${testName}:</strong>
                    <span class="${testResult.passed ? 'passed' : 'failed'}">
                        ${testResult.passed ? '✅ PASSED' : '❌ FAILED'}
                    </span>
                    <br>
                    ${testResult.message}
                    ${testResult.error ? `<br><small>Error: ${testResult.error}</small>` : ''}
                </div>
            `).join('')}

            ${siteResults.consoleErrors.length > 0 ? `
                <h3>Console Errors (${siteResults.consoleErrors.length})</h3>
                <pre>${siteResults.consoleErrors.join('\n')}</pre>
            ` : ''}

            ${siteResults.networkErrors.length > 0 ? `
                <h3>Network Errors (${siteResults.networkErrors.length})</h3>
                <pre>${siteResults.networkErrors.join('\n')}</pre>
            ` : ''}
        </div>
    `).join('')}

</body>
</html>
    `;
}

// Run the tests
testPropertySearchComponent().catch(console.error);