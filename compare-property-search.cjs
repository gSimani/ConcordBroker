const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function comparePropertySearch() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });

    // Create screenshots directory
    const screenshotDir = path.join(__dirname, 'property-search-comparison');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir);
    }

    const results = {
        timestamp: new Date().toISOString(),
        local: {
            url: 'http://localhost:5173/properties',
            status: 'unknown',
            errors: [],
            elements: {},
            screenshot: null
        },
        production: {
            url: 'https://www.concordbroker.com/properties',
            status: 'unknown',
            errors: [],
            elements: {},
            screenshot: null
        },
        comparison: {
            differences: [],
            summary: ''
        }
    };

    try {
        // Test Local Development Site
        console.log('Testing local development site...');
        const localPage = await context.newPage();

        // Monitor console errors
        localPage.on('console', msg => {
            if (msg.type() === 'error') {
                results.local.errors.push(msg.text());
                console.log('Local console error:', msg.text());
            }
        });

        try {
            await localPage.goto('http://localhost:5173/properties', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            results.local.status = 'loaded';

            // Wait for PropertySearch component to load
            console.log('Waiting for PropertySearch component on local...');
            await localPage.waitForSelector('[data-testid="property-search"]', { timeout: 10000 });

            // Check for key elements
            results.local.elements = await checkElements(localPage);

            // Take screenshot
            const localScreenshot = path.join(screenshotDir, 'local-property-search.png');
            await localPage.screenshot({ path: localScreenshot, fullPage: true });
            results.local.screenshot = localScreenshot;
            console.log('Local screenshot saved:', localScreenshot);

        } catch (error) {
            results.local.status = 'error';
            results.local.errors.push(error.message);
            console.error('Local site error:', error.message);
        }

        // Test Production Site
        console.log('\nTesting production site...');
        const prodPage = await context.newPage();

        // Monitor console errors
        prodPage.on('console', msg => {
            if (msg.type() === 'error') {
                results.production.errors.push(msg.text());
                console.log('Production console error:', msg.text());
            }
        });

        try {
            await prodPage.goto('https://www.concordbroker.com/properties', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            results.production.status = 'loaded';

            // Wait for PropertySearch component to load
            console.log('Waiting for PropertySearch component on production...');
            await prodPage.waitForSelector('[data-testid="property-search"]', { timeout: 10000 });

            // Check for key elements
            results.production.elements = await checkElements(prodPage);

            // Take screenshot
            const prodScreenshot = path.join(screenshotDir, 'production-property-search.png');
            await prodPage.screenshot({ path: prodScreenshot, fullPage: true });
            results.production.screenshot = prodScreenshot;
            console.log('Production screenshot saved:', prodScreenshot);

        } catch (error) {
            results.production.status = 'error';
            results.production.errors.push(error.message);
            console.error('Production site error:', error.message);
        }

        // Create side-by-side comparison screenshot
        if (results.local.status === 'loaded' && results.production.status === 'loaded') {
            console.log('\nCreating side-by-side comparison...');
            const comparisonPage = await context.newPage();
            await comparisonPage.setViewportSize({ width: 3840, height: 1080 });

            await comparisonPage.setContent(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>PropertySearch Comparison</title>
                    <style>
                        body { margin: 0; font-family: Arial, sans-serif; }
                        .container { display: flex; height: 100vh; }
                        .site { flex: 1; border-right: 2px solid #ccc; }
                        .site:last-child { border-right: none; }
                        iframe { width: 100%; height: calc(100vh - 40px); border: none; }
                        .header { background: #f0f0f0; padding: 10px; text-align: center; font-weight: bold; }
                        .local { background: #e8f5e8; }
                        .production { background: #e8f0ff; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="site">
                            <div class="header local">Local Development (localhost:5173)</div>
                            <iframe src="http://localhost:5173/properties"></iframe>
                        </div>
                        <div class="site">
                            <div class="header production">Production (concordbroker.com)</div>
                            <iframe src="https://www.concordbroker.com/properties"></iframe>
                        </div>
                    </div>
                </body>
                </html>
            `);

            // Wait for both iframes to load
            await comparisonPage.waitForTimeout(5000);
            const comparisonScreenshot = path.join(screenshotDir, 'side-by-side-comparison.png');
            await comparisonPage.screenshot({ path: comparisonScreenshot, fullPage: true });
            console.log('Side-by-side comparison saved:', comparisonScreenshot);
        }

        // Compare results
        compareResults(results);

        // Save detailed report
        const reportPath = path.join(screenshotDir, 'comparison-report.json');
        fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
        console.log('\nDetailed report saved:', reportPath);

        // Print summary
        printSummary(results);

    } catch (error) {
        console.error('Comparison failed:', error);
    } finally {
        await browser.close();
    }
}

async function checkElements(page) {
    const elements = {};

    try {
        // Check for PropertySearch container
        elements.propertySearchContainer = await page.locator('[data-testid="property-search"]').isVisible();

        // Check for search input
        elements.searchInput = await page.locator('input[placeholder*="search"], input[placeholder*="Search"]').isVisible();

        // Check for filter components
        elements.filters = await page.locator('[data-testid*="filter"], .filter').count();

        // Check for property cards/results
        elements.propertyCards = await page.locator('[data-testid*="property-card"], .property-card').count();

        // Check for loading states
        elements.loadingIndicator = await page.locator('[data-testid*="loading"], .loading, .spinner').isVisible();

        // Check for error states
        elements.errorMessage = await page.locator('[data-testid*="error"], .error').isVisible();

        // Check for navigation elements
        elements.navigation = await page.locator('nav, [role="navigation"]').isVisible();

        // Check for map component
        elements.mapComponent = await page.locator('[data-testid*="map"], .map-container').isVisible();

        // Check for pagination
        elements.pagination = await page.locator('[data-testid*="pagination"], .pagination').isVisible();

        // Get page title
        elements.pageTitle = await page.title();

        // Check for FastPropertySearch component specifically
        elements.fastPropertySearch = await page.locator('[data-testid="fast-property-search"]').isVisible();

    } catch (error) {
        elements.checkError = error.message;
    }

    return elements;
}

function compareResults(results) {
    const differences = [];

    // Compare status
    if (results.local.status !== results.production.status) {
        differences.push(`Status difference: Local=${results.local.status}, Production=${results.production.status}`);
    }

    // Compare errors
    if (results.local.errors.length !== results.production.errors.length) {
        differences.push(`Error count difference: Local=${results.local.errors.length}, Production=${results.production.errors.length}`);
    }

    // Compare elements
    const localElements = results.local.elements;
    const prodElements = results.production.elements;

    for (const [key, localValue] of Object.entries(localElements)) {
        const prodValue = prodElements[key];
        if (localValue !== prodValue) {
            differences.push(`Element '${key}' difference: Local=${localValue}, Production=${prodValue}`);
        }
    }

    results.comparison.differences = differences;

    // Generate summary
    if (differences.length === 0) {
        results.comparison.summary = 'No significant differences found between local and production';
    } else {
        results.comparison.summary = `Found ${differences.length} differences between local and production`;
    }
}

function printSummary(results) {
    console.log('\n' + '='.repeat(60));
    console.log('PROPERTY SEARCH COMPARISON SUMMARY');
    console.log('='.repeat(60));

    console.log(`\nLocal Development (${results.local.url}):`);
    console.log(`  Status: ${results.local.status}`);
    console.log(`  Errors: ${results.local.errors.length}`);
    if (results.local.errors.length > 0) {
        results.local.errors.forEach(error => console.log(`    - ${error}`));
    }

    console.log(`\nProduction (${results.production.url}):`);
    console.log(`  Status: ${results.production.status}`);
    console.log(`  Errors: ${results.production.errors.length}`);
    if (results.production.errors.length > 0) {
        results.production.errors.forEach(error => console.log(`    - ${error}`));
    }

    console.log(`\nComparison Results:`);
    console.log(`  ${results.comparison.summary}`);
    if (results.comparison.differences.length > 0) {
        console.log(`  Differences found:`);
        results.comparison.differences.forEach(diff => console.log(`    - ${diff}`));
    }

    console.log('\nKey Elements Check:');
    console.log('Local vs Production:');
    const localEl = results.local.elements;
    const prodEl = results.production.elements;

    const elementChecks = [
        'propertySearchContainer',
        'searchInput',
        'filters',
        'propertyCards',
        'fastPropertySearch',
        'mapComponent',
        'navigation'
    ];

    elementChecks.forEach(element => {
        const localVal = localEl[element] || 'N/A';
        const prodVal = prodEl[element] || 'N/A';
        const match = localVal === prodVal ? '✓' : '✗';
        console.log(`  ${element}: ${localVal} vs ${prodVal} ${match}`);
    });

    console.log('\nScreenshots saved in: property-search-comparison/');
    console.log('='.repeat(60));
}

// Run the comparison
comparePropertySearch().catch(console.error);