import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runDiagnosticTest() {
    const browser = await chromium.launch({ 
        headless: false, // Run in visible mode to see what's happening
        slowMo: 1000    // Slow down actions for better observation
    });
    
    const context = await browser.newContext({
        // Enable developer tools and console logging
        viewport: { width: 1280, height: 720 }
    });
    
    const page = await context.newPage();
    
    // Arrays to capture different types of errors
    const consoleErrors = [];
    const networkErrors = [];
    const fetchErrors = [];
    
    // Listen for console messages
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push({
                type: msg.type(),
                text: msg.text(),
                location: msg.location()
            });
            console.log('❌ Console Error:', msg.text());
        } else if (msg.text().includes('fetch') || msg.text().includes('Error')) {
            fetchErrors.push({
                type: msg.type(),
                text: msg.text(),
                location: msg.location()
            });
            console.log('🔍 Fetch Related:', msg.text());
        }
    });
    
    // Listen for failed network requests
    page.on('response', response => {
        if (!response.ok()) {
            networkErrors.push({
                url: response.url(),
                status: response.status(),
                statusText: response.statusText(),
                headers: response.headers()
            });
            console.log(`🌐 Network Error: ${response.status()} ${response.statusText()} - ${response.url()}`);
        }
    });
    
    // Listen for page errors
    page.on('pageerror', error => {
        console.log('💥 Page Error:', error.message);
        consoleErrors.push({
            type: 'pageerror',
            text: error.message,
            stack: error.stack
        });
    });
    
    try {
        console.log('🚀 Starting diagnostic test...');
        console.log('📍 Navigating to: http://localhost:5174/properties/parkland/12681-nw-78-mnr');
        
        // Navigate to the specific property page
        await page.goto('http://localhost:5174/properties/parkland/12681-nw-78-mnr', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        console.log('✅ Page loaded, waiting for content...');
        
        // Wait for the page to fully load and try to load content
        await page.waitForTimeout(5000);
        
        // Check if the page title loaded
        const title = await page.title();
        console.log(`📄 Page Title: ${title}`);
        
        // Try to find property-related elements
        const propertyElements = await page.$$eval('[data-testid*="property"], [class*="property"], [id*="property"]', 
            elements => elements.map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className,
                text: el.textContent?.slice(0, 100) + '...'
            }))
        ).catch(() => []);
        
        console.log(`🏠 Found ${propertyElements.length} property-related elements`);
        
        // Check for error messages on the page
        const errorMessages = await page.$$eval('[class*="error"], [data-error], .text-red-500, .text-red-600', 
            elements => elements.map(el => el.textContent)
        ).catch(() => []);
        
        if (errorMessages.length > 0) {
            console.log('⚠️ Error messages found on page:');
            errorMessages.forEach(msg => console.log(`  - ${msg}`));
        }
        
        // Take screenshot of current state
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const screenshotPath = path.join(__dirname, `diagnostic_screenshot_${timestamp}.png`);
        await page.screenshot({ 
            path: screenshotPath, 
            fullPage: true 
        });
        console.log(`📸 Screenshot saved: ${screenshotPath}`);
        
        // Check the network tab for specific API calls
        console.log('\n🔍 Checking API endpoints...');
        
        // Wait a bit more for any async API calls
        await page.waitForTimeout(3000);
        
        // Try to manually trigger API calls by looking for buttons or elements that might trigger them
        const buttons = await page.$$eval('button', buttons => 
            buttons.map(btn => ({
                text: btn.textContent,
                className: btn.className,
                disabled: btn.disabled
            }))
        );
        
        console.log(`🔘 Found ${buttons.length} buttons on page`);
        
        // Check if there are any pending network requests
        await page.evaluate(() => {
            // Log fetch calls in the browser console
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                console.log('🌐 Fetch called with:', args[0], args[1]);
                return originalFetch.apply(this, args)
                    .then(response => {
                        console.log('✅ Fetch success:', args[0], response.status);
                        return response;
                    })
                    .catch(error => {
                        console.error('❌ Fetch error:', args[0], error.message);
                        throw error;
                    });
            };
            
            // Try to trigger any property data loading
            if (window.location.pathname.includes('properties/')) {
                console.log('🏠 Property page detected, checking for data loading...');
            }
        });
        
        // Wait for any additional network activity
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.log('💥 Test Error:', error.message);
        
        // Take error screenshot
        const errorTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const errorScreenshotPath = path.join(__dirname, `error_screenshot_${errorTimestamp}.png`);
        await page.screenshot({ 
            path: errorScreenshotPath, 
            fullPage: true 
        });
        console.log(`📸 Error screenshot saved: ${errorScreenshotPath}`);
    }
    
    // Generate diagnostic report
    const report = {
        timestamp: new Date().toISOString(),
        url: 'http://localhost:5174/properties/parkland/12681-nw-78-mnr',
        consoleErrors: consoleErrors,
        networkErrors: networkErrors,
        fetchErrors: fetchErrors,
        summary: {
            totalConsoleErrors: consoleErrors.length,
            totalNetworkErrors: networkErrors.length,
            totalFetchErrors: fetchErrors.length,
            commonIssues: []
        }
    };
    
    // Analyze common issues
    if (networkErrors.some(err => err.status === 404)) {
        report.summary.commonIssues.push('404 errors - API endpoints not found');
    }
    if (networkErrors.some(err => err.status === 500)) {
        report.summary.commonIssues.push('500 errors - Server errors');
    }
    if (fetchErrors.some(err => err.text.includes('Failed to fetch'))) {
        report.summary.commonIssues.push('Network connectivity issues');
    }
    if (networkErrors.some(err => err.url.includes('localhost:8000'))) {
        report.summary.commonIssues.push('Backend API (port 8000) connection issues');
    }
    
    // Save report
    const reportPath = path.join(__dirname, `api_diagnostic_report_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    console.log('\n📊 DIAGNOSTIC REPORT:');
    console.log('='.repeat(50));
    console.log(`Console Errors: ${report.summary.totalConsoleErrors}`);
    console.log(`Network Errors: ${report.summary.totalNetworkErrors}`);
    console.log(`Fetch Errors: ${report.summary.totalFetchErrors}`);
    
    if (report.summary.commonIssues.length > 0) {
        console.log('\n🔍 Common Issues Detected:');
        report.summary.commonIssues.forEach(issue => console.log(`  - ${issue}`));
    }
    
    if (networkErrors.length > 0) {
        console.log('\n🌐 Network Errors Details:');
        networkErrors.forEach(err => {
            console.log(`  ${err.status} ${err.statusText}: ${err.url}`);
        });
    }
    
    if (fetchErrors.length > 0) {
        console.log('\n🔍 Fetch Errors Details:');
        fetchErrors.forEach(err => {
            console.log(`  ${err.text}`);
        });
    }
    
    console.log(`\n📄 Full report saved: ${reportPath}`);
    
    await browser.close();
    
    return report;
}

// Check if Playwright is installed
async function checkPlaywright() {
    try {
        await import('playwright');
        return true;
    } catch (error) {
        console.log('❌ Playwright not found. Installing...');
        console.log('Run: npm install playwright');
        console.log('Then: npx playwright install');
        return false;
    }
}

// Main execution
async function main() {
    console.log('🎭 Property Profile API Diagnostic Test');
    console.log('=====================================\n');
    
    if (await checkPlaywright()) {
        try {
            const report = await runDiagnosticTest();
            
            // Provide specific recommendations based on findings
            console.log('\n💡 RECOMMENDATIONS:');
            console.log('='.repeat(50));
            
            if (report.networkErrors.some(err => err.url.includes('localhost:8000'))) {
                console.log('1. ✅ Check if backend API is running on http://localhost:8000');
                console.log('2. ✅ Verify API endpoints exist for parcel and sales data');
            }
            
            if (report.fetchErrors.some(err => err.text.includes('CORS'))) {
                console.log('3. ✅ Check CORS configuration on backend API');
            }
            
            if (report.networkErrors.some(err => err.status === 404)) {
                console.log('4. ✅ Verify API route configuration for the specific property');
            }
            
            console.log('5. ✅ Check backend logs for detailed error information');
            console.log('6. ✅ Verify property data exists in database for the given address');
            
        } catch (error) {
            console.error('Test execution failed:', error.message);
        }
    } else {
        console.log('Please install Playwright first:');
        console.log('npm install playwright');
        console.log('npx playwright install');
    }
}

main();