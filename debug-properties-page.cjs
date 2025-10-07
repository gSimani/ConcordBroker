const { chromium } = require('playwright');

async function debugPropertiesPage() {
    console.log('🔍 Starting Properties Page Debug Analysis...\n');

    const browser = await chromium.launch({
        headless: false,
        devtools: true,
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    });

    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        recordVideo: { dir: './debug-videos/' }
    });

    const page = await context.newPage();

    // Arrays to collect errors and network issues
    const consoleErrors = [];
    const networkErrors = [];
    const apiCalls = [];

    // Listen to console events
    page.on('console', (msg) => {
        const type = msg.type();
        const text = msg.text();

        if (type === 'error' || type === 'warning') {
            consoleErrors.push({
                type,
                message: text,
                timestamp: new Date().toISOString()
            });
            console.log(`🚨 Console ${type.toUpperCase()}: ${text}`);
        }
    });

    // Listen to page errors
    page.on('pageerror', (error) => {
        consoleErrors.push({
            type: 'pageerror',
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        console.log(`💥 Page Error: ${error.message}`);
    });

    // Monitor network requests
    page.on('response', async (response) => {
        const url = response.url();
        const status = response.status();
        const method = response.request().method();

        // Track API calls and errors
        if (url.includes('api') || url.includes('supabase') || status >= 400) {
            const requestData = {
                url,
                method,
                status,
                statusText: response.statusText(),
                timestamp: new Date().toISOString(),
                headers: await response.allHeaders()
            };

            if (status >= 400) {
                try {
                    const responseBody = await response.text();
                    requestData.body = responseBody;
                    networkErrors.push(requestData);
                    console.log(`❌ Network Error: ${method} ${url} - ${status} ${response.statusText()}`);
                } catch (e) {
                    requestData.body = 'Could not read response body';
                    networkErrors.push(requestData);
                }
            } else {
                apiCalls.push(requestData);
                console.log(`✅ API Call: ${method} ${url} - ${status}`);
            }
        }
    });

    // Monitor request failures
    page.on('requestfailed', (request) => {
        const failure = {
            url: request.url(),
            method: request.method(),
            failure: request.failure()?.errorText || 'Unknown failure',
            timestamp: new Date().toISOString()
        };
        networkErrors.push(failure);
        console.log(`🔥 Request Failed: ${request.method()} ${request.url()} - ${failure.failure}`);
    });

    try {
        console.log('📍 Navigating to http://localhost:5173/properties...');

        // Navigate to the properties page
        await page.goto('http://localhost:5173/properties', {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        console.log('✅ Page loaded successfully');

        // Wait for potential async operations
        await page.waitForTimeout(3000);

        // Check if the page has rendered properly
        const pageTitle = await page.title();
        console.log(`📄 Page Title: ${pageTitle}`);

        // Look for key elements
        const hasPropertyGrid = await page.locator('[data-testid="property-grid"], .property-grid, .properties-container').count() > 0;
        const hasErrorMessage = await page.locator('.error, [data-testid="error"]').count() > 0;
        const hasLoadingIndicator = await page.locator('.loading, [data-testid="loading"]').count() > 0;

        console.log(`🏠 Property Grid Present: ${hasPropertyGrid}`);
        console.log(`⚠️  Error Message Present: ${hasErrorMessage}`);
        console.log(`⏳ Loading Indicator Present: ${hasLoadingIndicator}`);

        // Check for specific text content
        const pageContent = await page.textContent('body');
        const has0Properties = pageContent.includes('0 Properties Found') || pageContent.includes('No properties found');
        const hasProperties = pageContent.includes('properties') || pageContent.includes('Properties');

        console.log(`🔍 Contains "0 Properties Found": ${has0Properties}`);
        console.log(`🏘️  Contains properties content: ${hasProperties}`);

        // Take a screenshot for visual inspection
        await page.screenshot({
            path: 'debug-properties-page.png',
            fullPage: true
        });
        console.log('📸 Screenshot saved as debug-properties-page.png');

        // Check local storage and session storage
        const localStorage = await page.evaluate(() => {
            const ls = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                ls[key] = localStorage.getItem(key);
            }
            return ls;
        });

        const sessionStorage = await page.evaluate(() => {
            const ss = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                ss[key] = sessionStorage.getItem(key);
            }
            return ss;
        });

        console.log('\n💾 Local Storage:', JSON.stringify(localStorage, null, 2));
        console.log('\n🗂️  Session Storage:', JSON.stringify(sessionStorage, null, 2));

        // Wait a bit more to catch any delayed requests
        await page.waitForTimeout(5000);

    } catch (error) {
        console.error('❌ Navigation Error:', error.message);
        consoleErrors.push({
            type: 'navigation-error',
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
    }

    // Generate comprehensive report
    const report = {
        timestamp: new Date().toISOString(),
        summary: {
            totalConsoleErrors: consoleErrors.length,
            totalNetworkErrors: networkErrors.length,
            totalApiCalls: apiCalls.length
        },
        consoleErrors,
        networkErrors,
        apiCalls,
        recommendations: []
    };

    // Add recommendations based on findings
    if (networkErrors.length > 0) {
        report.recommendations.push('Check API endpoints and authentication');
    }
    if (consoleErrors.length > 0) {
        report.recommendations.push('Review JavaScript errors for component issues');
    }
    if (apiCalls.length === 0) {
        report.recommendations.push('No API calls detected - check if data fetching is working');
    }

    // Save detailed report
    const fs = require('fs');
    fs.writeFileSync('properties-debug-report.json', JSON.stringify(report, null, 2));

    console.log('\n📊 FINAL REPORT:');
    console.log('=================');
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);
    console.log(`API Calls: ${apiCalls.length}`);

    if (consoleErrors.length > 0) {
        console.log('\n🚨 Console Errors:');
        consoleErrors.forEach((error, i) => {
            console.log(`${i + 1}. [${error.type}] ${error.message}`);
        });
    }

    if (networkErrors.length > 0) {
        console.log('\n❌ Network Errors:');
        networkErrors.forEach((error, i) => {
            console.log(`${i + 1}. ${error.method || 'REQUEST'} ${error.url} - ${error.status || error.failure}`);
        });
    }

    if (apiCalls.length > 0) {
        console.log('\n✅ Successful API Calls:');
        apiCalls.forEach((call, i) => {
            console.log(`${i + 1}. ${call.method} ${call.url} - ${call.status}`);
        });
    }

    console.log('\n📄 Full report saved to: properties-debug-report.json');

    await browser.close();
    return report;
}

// Run the debug analysis
debugPropertiesPage().catch(console.error);