const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runComprehensiveTest() {
    console.log('🚀 Starting comprehensive Playwright test...\n');
    
    // Create screenshots directory if it doesn't exist
    const screenshotsDir = path.join(__dirname, 'ui_screenshots');
    if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir);
    }

    const browser = await chromium.launch({ 
        headless: false, // Set to true for headless mode
        devtools: false
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    // Arrays to collect findings
    const consoleMessages = [];
    const networkRequests = [];
    const errors = [];
    const findings = [];

    // Set up console monitoring
    page.on('console', (msg) => {
        const message = {
            type: msg.type(),
            text: msg.text(),
            timestamp: new Date().toISOString()
        };
        consoleMessages.push(message);
        console.log(`📋 Console [${msg.type()}]: ${msg.text()}`);
    });

    // Set up error monitoring
    page.on('pageerror', (error) => {
        const errorInfo = {
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        };
        errors.push(errorInfo);
        console.log(`❌ Page Error: ${error.message}`);
    });

    // Set up network monitoring
    page.on('request', (request) => {
        const requestInfo = {
            method: request.method(),
            url: request.url(),
            timestamp: new Date().toISOString(),
            headers: request.headers()
        };
        networkRequests.push(requestInfo);
        
        if (request.url().includes('localhost:8000')) {
            console.log(`🌐 API Request: ${request.method()} ${request.url()}`);
        }
    });

    page.on('response', async (response) => {
        if (response.url().includes('localhost:8000')) {
            const status = response.status();
            const statusText = response.statusText();
            console.log(`📡 API Response: ${status} ${statusText} - ${response.url()}`);
            
            if (status >= 400) {
                try {
                    const responseText = await response.text();
                    errors.push({
                        type: 'API Error',
                        status: status,
                        url: response.url(),
                        response: responseText,
                        timestamp: new Date().toISOString()
                    });
                } catch (e) {
                    console.log('Could not read response body');
                }
            }
        }
    });

    try {
        console.log('🔍 Navigating to http://localhost:5175/properties...\n');
        
        // Navigate to the properties page
        await page.goto('http://localhost:5175/properties', { 
            waitUntil: 'networkidle',
            timeout: 30000 
        });

        // Wait a bit for any dynamic content to load
        await page.waitForTimeout(3000);

        console.log('📸 Taking initial screenshot...\n');
        
        // Take initial screenshot
        await page.screenshot({ 
            path: path.join(screenshotsDir, 'properties_page_initial.png'),
            fullPage: true 
        });

        // Check page title
        const title = await page.title();
        console.log(`📄 Page Title: ${title}\n`);

        // Check if the page loaded properly
        const bodyText = await page.textContent('body');
        if (bodyText.includes('Something went wrong') || bodyText.includes('Error')) {
            findings.push('⚠️ Page shows error content');
        }

        // Look for key elements on the properties page
        console.log('🔍 Inspecting page elements...\n');
        
        const elements = [
            { selector: 'h1', name: 'Main heading' },
            { selector: 'input[type="text"], input[type="search"]', name: 'Search input' },
            { selector: 'button', name: 'Buttons' },
            { selector: 'table', name: 'Data table' },
            { selector: '[data-testid]', name: 'Test elements' },
            { selector: '.property-card, .property-item', name: 'Property items' },
            { selector: 'nav', name: 'Navigation' },
            { selector: '.error, .alert-error', name: 'Error messages' },
            { selector: '.loading, .spinner', name: 'Loading indicators' }
        ];

        for (const element of elements) {
            try {
                const count = await page.locator(element.selector).count();
                if (count > 0) {
                    console.log(`✅ Found ${count} ${element.name} element(s)`);
                    findings.push(`✅ Found ${count} ${element.name} element(s)`);
                } else {
                    console.log(`❌ No ${element.name} elements found`);
                    findings.push(`❌ No ${element.name} elements found`);
                }
            } catch (e) {
                console.log(`⚠️ Error checking ${element.name}: ${e.message}`);
            }
        }

        // Check for React/JavaScript errors in the console
        const jsErrors = consoleMessages.filter(msg => msg.type === 'error');
        if (jsErrors.length > 0) {
            findings.push(`❌ Found ${jsErrors.length} JavaScript errors in console`);
        } else {
            findings.push('✅ No JavaScript errors found in console');
        }

        // Check API calls
        const apiCalls = networkRequests.filter(req => req.url.includes('localhost:8000'));
        if (apiCalls.length > 0) {
            findings.push(`✅ Found ${apiCalls.length} API calls to localhost:8000`);
            console.log(`\n📊 API Calls Made:`);
            apiCalls.forEach(call => {
                console.log(`   ${call.method} ${call.url}`);
            });
        } else {
            findings.push('❌ No API calls detected to localhost:8000');
        }

        // Try to interact with search if present
        try {
            const searchInput = page.locator('input[type="text"], input[type="search"]').first();
            if (await searchInput.count() > 0) {
                console.log('\n🔎 Testing search functionality...');
                await searchInput.fill('Miami');
                await page.waitForTimeout(1000);
                
                // Take screenshot after search
                await page.screenshot({ 
                    path: path.join(screenshotsDir, 'properties_page_with_search.png'),
                    fullPage: true 
                });
                
                findings.push('✅ Search input interaction successful');
            }
        } catch (e) {
            findings.push(`⚠️ Search interaction failed: ${e.message}`);
        }

        // Check for responsive design by changing viewport
        console.log('\n📱 Testing mobile responsiveness...');
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        
        await page.screenshot({ 
            path: path.join(screenshotsDir, 'properties_page_mobile.png'),
            fullPage: true 
        });

        // Reset to desktop
        await page.setViewportSize({ width: 1920, height: 1080 });

        // Final screenshot
        await page.screenshot({ 
            path: path.join(screenshotsDir, 'properties_page_final.png'),
            fullPage: true 
        });

    } catch (error) {
        console.log(`❌ Test failed: ${error.message}`);
        errors.push({
            type: 'Test Error',
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        
        // Take error screenshot
        try {
            await page.screenshot({ 
                path: path.join(screenshotsDir, 'properties_page_error.png'),
                fullPage: true 
            });
        } catch (screenshotError) {
            console.log('Could not take error screenshot');
        }
    }

    await browser.close();

    // Generate comprehensive report
    console.log('\n' + '='.repeat(80));
    console.log('📋 COMPREHENSIVE TEST REPORT');
    console.log('='.repeat(80));

    console.log('\n🎯 KEY FINDINGS:');
    findings.forEach(finding => console.log(`   ${finding}`));

    console.log('\n📋 CONSOLE MESSAGES:');
    if (consoleMessages.length === 0) {
        console.log('   ✅ No console messages captured');
    } else {
        consoleMessages.slice(-10).forEach(msg => {
            console.log(`   [${msg.type}] ${msg.text}`);
        });
        if (consoleMessages.length > 10) {
            console.log(`   ... and ${consoleMessages.length - 10} more messages`);
        }
    }

    console.log('\n🌐 NETWORK ACTIVITY:');
    const apiRequests = networkRequests.filter(req => req.url.includes('localhost:8000'));
    if (apiRequests.length === 0) {
        console.log('   ❌ No API requests to localhost:8000 detected');
    } else {
        console.log(`   ✅ ${apiRequests.length} API requests made:`);
        apiRequests.forEach(req => {
            console.log(`      ${req.method} ${req.url}`);
        });
    }

    console.log('\n❌ ERRORS:');
    if (errors.length === 0) {
        console.log('   ✅ No errors detected');
    } else {
        errors.forEach(error => {
            console.log(`   [${error.type}] ${error.message}`);
        });
    }

    console.log('\n📸 SCREENSHOTS:');
    console.log(`   Screenshots saved to: ${screenshotsDir}`);
    
    const screenshotFiles = fs.readdirSync(screenshotsDir)
        .filter(file => file.endsWith('.png') && file.includes('properties_page'));
    screenshotFiles.forEach(file => {
        console.log(`   📷 ${file}`);
    });

    console.log('\n' + '='.repeat(80));
    console.log('✅ Test completed!');
    console.log('='.repeat(80));
}

// Run the test
if (require.main === module) {
    runComprehensiveTest().catch(console.error);
}

module.exports = { runComprehensiveTest };