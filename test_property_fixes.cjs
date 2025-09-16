const { chromium } = require('playwright');
const fs = require('fs');

async function testPropertyFixes() {
    console.log('Starting property fixes verification...');
    
    const browser = await chromium.launch({ 
        headless: false, // Keep browser visible to see what's happening
        devtools: false 
    });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    // Capture console logs and errors
    const consoleLogs = [];
    const consoleErrors = [];
    
    page.on('console', (msg) => {
        const text = msg.text();
        consoleLogs.push(`[${msg.type().toUpperCase()}] ${text}`);
        console.log(`Console: ${text}`);
    });
    
    page.on('pageerror', (error) => {
        consoleErrors.push(error.message);
        console.error('Page Error:', error.message);
    });

    try {
        // Navigate to the test property
        console.log('\n1. Navigating to property page...');
        const url = 'http://localhost:5174/properties/parkland/10892-nw-72-pl';
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        
        // Wait a bit for the page to fully load
        await page.waitForTimeout(3000);

        console.log('\n2. Testing TaxesTab Infinite Loop Fix...');
        
        // Take initial screenshot
        await page.screenshot({ 
            path: 'ui_screenshots/property_test_initial.png', 
            fullPage: true 
        });

        // Click on Property Tax Info tab and monitor for infinite loops
        console.log('Clicking Property Tax Info tab...');
        const taxTabSelector = '[data-value="tax"], button:has-text("Property Tax Info"), .tab-trigger:has-text("Property Tax Info")';
        
        // Wait for tab to be available
        await page.waitForSelector('button', { timeout: 10000 });
        
        // Try multiple selectors to find the tax tab
        const taxTab = await page.locator('button').filter({ hasText: 'Property Tax Info' }).first();
        
        if (await taxTab.count() > 0) {
            await taxTab.click();
            console.log('Tax tab clicked successfully');
            
            // Wait and check for infinite loop indicators
            await page.waitForTimeout(5000);
            
            // Take screenshot of tax tab
            await page.screenshot({ 
                path: 'ui_screenshots/property_tax_tab_test.png', 
                fullPage: true 
            });
            
            // Check if page is still responsive
            const tabContent = await page.locator('[role="tabpanel"][data-state="active"]').first();
            const isResponsive = await tabContent.isVisible();
            console.log(`Tax tab responsive: ${isResponsive}`);
        } else {
            console.log('Could not find Property Tax Info tab');
        }

        console.log('\n3. Testing Core Property Info and Sales History...');
        
        // Click on Core Property Info tab
        const coreTab = await page.locator('button').filter({ hasText: 'Core Property Info' }).first();
        
        if (await coreTab.count() > 0) {
            await coreTab.click();
            console.log('Core Property Info tab clicked');
            
            await page.waitForTimeout(3000);
            
            // Take screenshot of core property tab
            await page.screenshot({ 
                path: 'ui_screenshots/core_property_tab_test.png', 
                fullPage: true 
            });
            
            // Check for Sales History section
            const salesHistorySection = page.locator('text=Sales History').first();
            const hasSalesHistory = await salesHistorySection.isVisible();
            console.log(`Sales History section visible: ${hasSalesHistory}`);
            
            // Look for specific sale amount ($425,000)
            const saleAmount = page.locator('text=$425,000').first();
            const hasSaleAmount = await saleAmount.isVisible();
            console.log(`$425,000 sale visible: ${hasSaleAmount}`);
            
            // Check for $/sq ft text size (should be text-sm not text-xs)
            const sqftElements = await page.locator('text=/\\$\\d+.*sq ft/').all();
            console.log(`Found ${sqftElements.length} $/sq ft elements`);
            
            // Check for clickable hyperlinks in sales data
            const bookPageLinks = await page.locator('a[href*="book"], a[href*="page"], a[href*="cin"]').all();
            console.log(`Found ${bookPageLinks.length} clickable book/page/cin links`);
            
        } else {
            console.log('Could not find Core Property Info tab');
        }

        console.log('\n4. Testing Overview Tab Property Details...');
        
        // Click on Overview tab
        const overviewTab = await page.locator('button').filter({ hasText: 'Overview' }).first();
        
        if (await overviewTab.count() > 0) {
            await overviewTab.click();
            console.log('Overview tab clicked');
            
            await page.waitForTimeout(3000);
            
            // Take screenshot of overview tab
            await page.screenshot({ 
                path: 'ui_screenshots/overview_tab_test.png', 
                fullPage: true 
            });
            
            // Check for property details that should not show N/A
            const livingAreaText = await page.textContent('body');
            const hasLivingAreaData = livingAreaText && !livingAreaText.includes('Living Area: N/A');
            console.log(`Living Area shows data (not N/A): ${hasLivingAreaData}`);
            
            const hasYearBuiltData = livingAreaText && !livingAreaText.includes('Year Built: N/A');
            console.log(`Year Built shows data (not N/A): ${hasYearBuiltData}`);
            
            const hasLotSizeData = livingAreaText && !livingAreaText.includes('Lot Size: N/A');
            console.log(`Lot Size shows data (not N/A): ${hasLotSizeData}`);
            
            // Check for Most Recent Sale section
            const mostRecentSale = page.locator('text=Most Recent Sale').first();
            const hasMostRecentSale = await mostRecentSale.isVisible();
            console.log(`Most Recent Sale section visible: ${hasMostRecentSale}`);
            
        } else {
            console.log('Could not find Overview tab');
        }

        console.log('\n5. Analyzing Console Logs...');
        
        // Filter for specific debug logs we're looking for
        const debugLogs = consoleLogs.filter(log => 
            log.includes('CorePropertyTab - propertyData:') ||
            log.includes('CorePropertyTab - bcpaData:') ||
            log.includes('Fetching sales history for parcel:')
        );
        
        console.log(`Found ${debugLogs.length} relevant debug logs:`);
        debugLogs.forEach(log => console.log(`  ${log}`));
        
        // Check for the specific error we're looking for
        const infiniteLoopErrors = consoleErrors.filter(error => 
            error.includes('Maximum update depth exceeded') ||
            error.includes('Too many re-renders')
        );
        
        console.log(`\nInfinite loop errors found: ${infiniteLoopErrors.length}`);
        infiniteLoopErrors.forEach(error => console.log(`  ERROR: ${error}`));

        console.log('\n6. Final Summary Report...');
        
        const report = {
            timestamp: new Date().toISOString(),
            url: url,
            tests: {
                taxTabInfiniteLoop: {
                    status: infiniteLoopErrors.length === 0 ? 'PASSED' : 'FAILED',
                    errors: infiniteLoopErrors
                },
                salesHistoryDisplay: {
                    status: 'NEEDS_MANUAL_VERIFICATION',
                    notes: 'Check screenshots for sales history data'
                },
                propertyDetailsNA: {
                    status: 'NEEDS_MANUAL_VERIFICATION', 
                    notes: 'Check screenshots for N/A values'
                },
                consoleLogging: {
                    status: debugLogs.length > 0 ? 'PASSED' : 'FAILED',
                    debugLogsFound: debugLogs.length,
                    logs: debugLogs
                }
            },
            allConsoleLogs: consoleLogs,
            allErrors: consoleErrors,
            screenshots: [
                'ui_screenshots/property_test_initial.png',
                'ui_screenshots/property_tax_tab_test.png', 
                'ui_screenshots/core_property_tab_test.png',
                'ui_screenshots/overview_tab_test.png'
            ]
        };
        
        // Save detailed report
        fs.writeFileSync('property_fixes_test_report.json', JSON.stringify(report, null, 2));
        console.log('\nDetailed report saved to property_fixes_test_report.json');
        
        // Print summary
        console.log('\n=== TEST RESULTS SUMMARY ===');
        console.log(`Tax Tab Infinite Loop Fix: ${report.tests.taxTabInfiniteLoop.status}`);
        console.log(`Sales History Display: ${report.tests.salesHistoryDisplay.status}`);
        console.log(`Property Details N/A Fix: ${report.tests.propertyDetailsNA.status}`);
        console.log(`Console Logging: ${report.tests.consoleLogging.status} (${debugLogs.length} debug logs found)`);
        console.log(`Total Console Errors: ${consoleErrors.length}`);
        console.log(`Screenshots taken: ${report.screenshots.length}`);
        
    } catch (error) {
        console.error('Test failed with error:', error);
        await page.screenshot({ 
            path: 'ui_screenshots/property_test_error.png', 
            fullPage: true 
        });
    } finally {
        await browser.close();
    }
}

// Run the test
testPropertyFixes().catch(console.error);