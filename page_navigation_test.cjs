const puppeteer = require('puppeteer');

async function testPageNavigation() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    const routes = [
        { path: '/', name: 'Home' },
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/properties', name: 'Properties' },
        { path: '/analytics', name: 'Analytics' }
    ];

    const results = {};

    try {
        for (const route of routes) {
            console.log(`\n🔍 Testing route: ${route.path}`);

            try {
                await page.goto(`http://localhost:5173${route.path}`, {
                    waitUntil: 'networkidle0',
                    timeout: 15000
                });

                // Wait for React to render
                await page.waitForSelector('#root', { timeout: 10000 });
                await new Promise(resolve => setTimeout(resolve, 2000));

                const title = await page.title();
                const url = page.url();

                // Check for search elements on this page
                const searchElements = await page.evaluate(() => {
                    const selectors = [
                        'input[type="search"]',
                        'input[placeholder*="search"]',
                        'input[placeholder*="address"]',
                        'input[placeholder*="property"]',
                        '[data-testid*="search"]',
                        '.search-input',
                        '#search'
                    ];

                    const elements = [];
                    selectors.forEach(selector => {
                        try {
                            const found = Array.from(document.querySelectorAll(selector));
                            found.forEach(el => {
                                elements.push({
                                    selector,
                                    type: el.type,
                                    placeholder: el.placeholder,
                                    id: el.id,
                                    className: el.className
                                });
                            });
                        } catch (e) {}
                    });
                    return elements;
                });

                // Check for property-related content
                const propertyElements = await page.evaluate(() => {
                    const selectors = [
                        '[data-testid*="property"]',
                        '.property-card',
                        '.property-item',
                        '[class*="property"]',
                        'table',
                        '.card'
                    ];

                    const elements = [];
                    selectors.forEach(selector => {
                        try {
                            const found = Array.from(document.querySelectorAll(selector));
                            elements.push({
                                selector,
                                count: found.length,
                                sample: found.slice(0, 3).map(el => ({
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    text: el.innerText ? el.innerText.substring(0, 100) : ''
                                }))
                            });
                        } catch (e) {}
                    });
                    return elements.filter(e => e.count > 0);
                });

                // Check for map elements
                const mapElements = await page.evaluate(() => {
                    const selectors = [
                        '.map-container',
                        '.google-map',
                        '#map',
                        '[data-testid*="map"]',
                        '.leaflet-container',
                        'iframe[src*="maps"]',
                        'div[class*="map"]'
                    ];

                    let found = false;
                    let foundSelector = null;

                    selectors.forEach(selector => {
                        try {
                            const elements = Array.from(document.querySelectorAll(selector));
                            if (elements.length > 0) {
                                found = true;
                                foundSelector = selector;
                            }
                        } catch (e) {}
                    });

                    return { found, selector: foundSelector };
                });

                // Check for forms
                const forms = await page.evaluate(() => {
                    const forms = Array.from(document.querySelectorAll('form'));
                    const inputs = Array.from(document.querySelectorAll('input'));

                    return {
                        formCount: forms.length,
                        inputCount: inputs.length,
                        inputTypes: inputs.map(input => input.type).filter((type, index, arr) => arr.indexOf(type) === index)
                    };
                });

                // Get page content overview
                const pageContent = await page.evaluate(() => {
                    return {
                        hasMainContent: !!document.querySelector('main'),
                        headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText).slice(0, 5),
                        buttonCount: document.querySelectorAll('button').length,
                        linkCount: document.querySelectorAll('a').length
                    };
                });

                // Take screenshot
                await page.screenshot({
                    path: `./test-results/screenshots/route_${route.name.toLowerCase()}.png`,
                    fullPage: true
                });

                results[route.path] = {
                    success: true,
                    title,
                    url,
                    searchElements,
                    propertyElements,
                    mapElements,
                    forms,
                    pageContent,
                    screenshot: `route_${route.name.toLowerCase()}.png`
                };

                console.log(`✅ ${route.name} - Loaded successfully`);
                console.log(`   Title: ${title}`);
                console.log(`   Search elements: ${searchElements.length}`);
                console.log(`   Property elements: ${propertyElements.length}`);
                console.log(`   Map found: ${mapElements.found}`);
                console.log(`   Forms: ${forms.formCount}, Inputs: ${forms.inputCount}`);

            } catch (error) {
                console.log(`❌ ${route.name} - Failed to load: ${error.message}`);
                results[route.path] = {
                    success: false,
                    error: error.message
                };
            }
        }

        // Test button navigation from home page
        console.log(`\n🔍 Testing button navigation from home page...`);
        await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Test "Go to Dashboard" button
        try {
            const dashboardButton = await page.$('button:contains("Go to Dashboard")');
            if (!dashboardButton) {
                // Try a different approach
                const buttons = await page.$$('button');
                let foundDashboardButton = false;

                for (const button of buttons) {
                    const text = await button.evaluate(el => el.innerText);
                    if (text.includes('Dashboard')) {
                        await button.click();
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        const newUrl = page.url();
                        console.log(`✅ Dashboard button clicked - navigated to: ${newUrl}`);
                        foundDashboardButton = true;
                        break;
                    }
                }

                if (!foundDashboardButton) {
                    console.log(`⚠️ Dashboard button not found or clickable`);
                }
            }
        } catch (error) {
            console.log(`❌ Dashboard button test failed: ${error.message}`);
        }

        // Test "Search Properties" button
        try {
            await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
            await new Promise(resolve => setTimeout(resolve, 2000));

            const buttons = await page.$$('button');
            let foundSearchButton = false;

            for (const button of buttons) {
                const text = await button.evaluate(el => el.innerText);
                if (text.includes('Search Properties')) {
                    await button.click();
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    const newUrl = page.url();
                    console.log(`✅ Search Properties button clicked - navigated to: ${newUrl}`);
                    foundSearchButton = true;
                    break;
                }
            }

            if (!foundSearchButton) {
                console.log(`⚠️ Search Properties button not found or clickable`);
            }
        } catch (error) {
            console.log(`❌ Search Properties button test failed: ${error.message}`);
        }

        console.log(`\n📊 Navigation Test Summary:`);
        console.log(`   Routes tested: ${routes.length}`);
        console.log(`   Successful: ${Object.values(results).filter(r => r.success).length}`);
        console.log(`   Failed: ${Object.values(results).filter(r => !r.success).length}`);

        return results;

    } catch (error) {
        console.error('❌ Navigation test failed:', error.message);
    } finally {
        await browser.close();
    }
}

testPageNavigation().catch(console.error);