const puppeteer = require('puppeteer');

async function inspectPage() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    try {
        console.log('🔍 Loading page...');
        await page.goto('http://localhost:5173', { waitUntil: 'networkidle0', timeout: 30000 });

        // Wait for React to render
        await page.waitForSelector('#root', { timeout: 10000 });
        await new Promise(resolve => setTimeout(resolve, 3000));

        console.log('📊 Analyzing page structure...');

        // Get page title
        const title = await page.title();
        console.log(`Title: ${title}`);

        // Get all text content
        const bodyText = await page.evaluate(() => {
            return document.body.innerText.substring(0, 1000);
        });
        console.log(`\nBody text preview:\n${bodyText}`);

        // Get all input elements
        const inputs = await page.evaluate(() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.map(input => ({
                type: input.type,
                placeholder: input.placeholder,
                id: input.id,
                className: input.className,
                name: input.name
            }));
        });
        console.log(`\n🔍 Found ${inputs.length} input elements:`);
        inputs.forEach((input, i) => {
            console.log(`  ${i + 1}. Type: ${input.type}, Placeholder: "${input.placeholder}", ID: "${input.id}", Class: "${input.className}"`);
        });

        // Get all buttons
        const buttons = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.map(button => ({
                text: button.innerText,
                id: button.id,
                className: button.className,
                type: button.type
            }));
        });
        console.log(`\n🔘 Found ${buttons.length} button elements:`);
        buttons.forEach((button, i) => {
            console.log(`  ${i + 1}. Text: "${button.text}", ID: "${button.id}", Class: "${button.className}"`);
        });

        // Get all links
        const links = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => ({
                text: link.innerText,
                href: link.href,
                id: link.id,
                className: link.className
            }));
        });
        console.log(`\n🔗 Found ${links.length} link elements:`);
        links.forEach((link, i) => {
            console.log(`  ${i + 1}. Text: "${link.text}", Href: "${link.href}", ID: "${link.id}"`);
        });

        // Check for React Router content
        const routes = await page.evaluate(() => {
            const routeElements = Array.from(document.querySelectorAll('[data-testid], [class*="page"], [class*="route"], main, section'));
            return routeElements.map(el => ({
                tagName: el.tagName,
                className: el.className,
                testId: el.getAttribute('data-testid'),
                id: el.id,
                text: el.innerText ? el.innerText.substring(0, 100) : ''
            }));
        });
        console.log(`\n🗺️ Found ${routes.length} potential route/page elements:`);
        routes.slice(0, 10).forEach((route, i) => {
            console.log(`  ${i + 1}. ${route.tagName} - Class: "${route.className}", TestID: "${route.testId}", Text: "${route.text}"`);
        });

        // Check for specific ConcordBroker elements
        const concordElements = await page.evaluate(() => {
            const selectors = [
                '[class*="property"]',
                '[class*="search"]',
                '[class*="broker"]',
                '[class*="real-estate"]',
                '[data-testid*="property"]',
                '[data-testid*="search"]'
            ];

            const elements = [];
            selectors.forEach(selector => {
                try {
                    const found = Array.from(document.querySelectorAll(selector));
                    found.forEach(el => {
                        elements.push({
                            selector,
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            text: el.innerText ? el.innerText.substring(0, 50) : '',
                            testId: el.getAttribute('data-testid')
                        });
                    });
                } catch (e) {
                    // Ignore selector errors
                }
            });
            return elements;
        });

        console.log(`\n🏠 Found ${concordElements.length} ConcordBroker-specific elements:`);
        concordElements.forEach((el, i) => {
            console.log(`  ${i + 1}. ${el.tagName} - Selector: ${el.selector}, Class: "${el.className}", Text: "${el.text}"`);
        });

        // Get current URL and check if it's a SPA
        const currentUrl = page.url();
        console.log(`\n🌐 Current URL: ${currentUrl}`);

        // Check console errors
        const errors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                errors.push(msg.text());
            }
        });

        // Reload to catch any console errors
        await page.reload({ waitUntil: 'networkidle0' });
        await new Promise(resolve => setTimeout(resolve, 2000));

        console.log(`\n❌ Console errors (${errors.length}):`);
        errors.forEach((error, i) => {
            console.log(`  ${i + 1}. ${error}`);
        });

        // Take a screenshot
        await page.screenshot({ path: './current_page_inspection.png', fullPage: true });
        console.log('\n📸 Screenshot saved as current_page_inspection.png');

    } catch (error) {
        console.error('❌ Error inspecting page:', error.message);
    } finally {
        await browser.close();
    }
}

inspectPage().catch(console.error);