const { chromium } = require('playwright');

async function testHomepage() {
    console.log('🏠 Testing homepage navigation...\n');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Monitor console messages
    page.on('console', (msg) => {
        console.log(`📋 Console [${msg.type()}]: ${msg.text()}`);
    });

    page.on('pageerror', (error) => {
        console.log(`❌ Page Error: ${error.message}`);
    });

    try {
        console.log('🔍 Navigating to http://localhost:5175/...\n');
        
        await page.goto('http://localhost:5175/', { 
            waitUntil: 'networkidle',
            timeout: 30000 
        });

        await page.waitForTimeout(3000);

        const title = await page.title();
        console.log(`📄 Homepage Title: ${title}\n`);

        // Take screenshot
        await page.screenshot({ 
            path: 'ui_screenshots/homepage_test.png',
            fullPage: true 
        });

        // Check if page has content
        const bodyText = await page.textContent('body');
        console.log(`📝 Page content preview: ${bodyText.substring(0, 200)}...\n`);

        // Try to navigate to properties
        console.log('🔗 Attempting to click properties link...');
        const propertiesLink = page.locator('a[href*="properties"], button:has-text("Properties")').first();
        
        if (await propertiesLink.count() > 0) {
            await propertiesLink.click();
            await page.waitForTimeout(2000);
            
            const currentUrl = page.url();
            console.log(`📍 Current URL after click: ${currentUrl}`);
            
            await page.screenshot({ 
                path: 'ui_screenshots/properties_via_navigation.png',
                fullPage: true 
            });
        } else {
            console.log('❌ No properties navigation link found');
        }

    } catch (error) {
        console.log(`❌ Test failed: ${error.message}`);
    }

    await browser.close();
}

testHomepage().catch(console.error);