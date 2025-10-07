const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function simplePropertySearchTest() {
    console.log('Starting Simple PropertySearch Test...\n');

    const browser = await chromium.launch({
        headless: false,
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    });

    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        ignoreHTTPSErrors: true
    });

    const screenshotDir = path.join(__dirname, 'simple-property-test');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir);
    }

    // Test Local Site
    console.log('📱 Testing Local Site: http://localhost:5173/properties');
    await testSiteSimple(context, 'http://localhost:5173/properties', 'local', screenshotDir);

    // Test Production Site
    console.log('\n📱 Testing Production Site: https://www.concordbroker.com/properties');
    await testSiteSimple(context, 'https://www.concordbroker.com/properties', 'production', screenshotDir);

    await browser.close();
    console.log('\n✅ Simple PropertySearch test completed!');
    console.log(`📁 Screenshots saved in: ${screenshotDir}`);
}

async function testSiteSimple(context, url, siteName, screenshotDir) {
    const page = await context.newPage();

    try {
        console.log(`  🌐 Loading ${siteName}...`);

        // Set a shorter timeout and try to load
        await page.goto(url, {
            waitUntil: 'domcontentloaded',
            timeout: 15000
        });

        // Wait a bit for any dynamic content
        await page.waitForTimeout(3000);

        console.log(`  ✅ ${siteName} page loaded`);

        // Take initial screenshot
        const initialScreenshot = path.join(screenshotDir, `${siteName}-initial.png`);
        await page.screenshot({ path: initialScreenshot, fullPage: true });
        console.log(`  📸 Initial screenshot: ${initialScreenshot}`);

        // Check for basic page elements
        const pageTitle = await page.title();
        console.log(`  📋 Page title: "${pageTitle}"`);

        // Look for any search-related elements
        const searchElements = await page.$$('input[type="search"], input[placeholder*="search" i], input[placeholder*="property" i], [data-testid*="search"]');
        console.log(`  🔍 Found ${searchElements.length} search-related elements`);

        // Look for any property-related elements
        const propertyElements = await page.$$('[data-testid*="property"], .property-card, .property-item, [class*="property"]');
        console.log(`  🏠 Found ${propertyElements.length} property-related elements`);

        // Check if the page seems to be working by looking for React root
        const reactRoot = await page.$('#root');
        console.log(`  ⚛️ React root element: ${reactRoot ? 'Found' : 'Not found'}`);

        // Look for error messages on page
        const errorElements = await page.$$('.error, [class*="error"], [data-testid*="error"]');
        console.log(`  ❌ Error elements found: ${errorElements.length}`);

        // Try to interact with search if found
        if (searchElements.length > 0) {
            try {
                console.log('  🔍 Attempting to interact with search...');
                await searchElements[0].fill('Miami');
                await page.waitForTimeout(2000);

                const afterSearchScreenshot = path.join(screenshotDir, `${siteName}-after-search.png`);
                await page.screenshot({ path: afterSearchScreenshot, fullPage: true });
                console.log(`  📸 After search screenshot: ${afterSearchScreenshot}`);
            } catch (error) {
                console.log(`  ⚠️ Search interaction failed: ${error.message}`);
            }
        }

        // Get page HTML for analysis (first 1000 chars)
        const pageContent = await page.content();
        const htmlPreview = pageContent.substring(0, 1000) + '...';
        const htmlFile = path.join(screenshotDir, `${siteName}-content.html`);
        fs.writeFileSync(htmlFile, pageContent);
        console.log(`  📄 Page content saved: ${htmlFile}`);
        console.log(`  📄 HTML preview: ${htmlPreview.substring(0, 200)}...`);

    } catch (error) {
        console.log(`  ❌ ${siteName} test failed: ${error.message}`);

        // Take error screenshot
        try {
            const errorScreenshot = path.join(screenshotDir, `${siteName}-error.png`);
            await page.screenshot({ path: errorScreenshot, fullPage: true });
            console.log(`  📸 Error screenshot: ${errorScreenshot}`);
        } catch (screenshotError) {
            console.log(`  ⚠️ Could not take error screenshot: ${screenshotError.message}`);
        }
    }

    await page.close();
}

// Run the test
simplePropertySearchTest().catch(console.error);