const puppeteer = require('puppeteer');

async function testPropertiesPage() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    try {
        console.log('🔍 Loading Properties page...');
        await page.goto('http://localhost:5173/properties', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for React to render
        await page.waitForSelector('#root', { timeout: 10000 });
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait longer for dynamic content

        // Take initial screenshot
        await page.screenshot({
            path: './properties_page_detailed.png',
            fullPage: true
        });

        console.log('📊 Analyzing Properties page in detail...');

        // Get all the content
        const pageAnalysis = await page.evaluate(() => {
            // Get all text content
            const bodyText = document.body.innerText;

            // Look for any input elements with different selectors
            const allInputs = Array.from(document.querySelectorAll('input, textarea, select, [contenteditable]'));
            const inputsInfo = allInputs.map(input => ({
                tagName: input.tagName,
                type: input.type || 'N/A',
                placeholder: input.placeholder || '',
                id: input.id || '',
                className: input.className || '',
                name: input.name || '',
                value: input.value || '',
                role: input.getAttribute('role') || '',
                ariaLabel: input.getAttribute('aria-label') || '',
                visible: input.offsetHeight > 0 && input.offsetWidth > 0,
                text: input.innerText || ''
            }));

            // Look for any searchable elements
            const searchableElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = (el.className + ' ' + el.id + ' ' + (el.placeholder || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
                return text.includes('search') || text.includes('filter') || text.includes('find');
            }).map(el => ({
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                placeholder: el.placeholder || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                text: el.innerText ? el.innerText.substring(0, 100) : '',
                visible: el.offsetHeight > 0 && el.offsetWidth > 0
            }));

            // Look for property-related elements
            const propertyElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = (el.className + ' ' + el.id + ' ' + el.innerText).toLowerCase();
                return text.includes('property') || text.includes('address') || text.includes('parcel');
            }).slice(0, 10).map(el => ({
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                text: el.innerText ? el.innerText.substring(0, 100) : '',
                visible: el.offsetHeight > 0 && el.offsetWidth > 0
            }));

            // Look for React components (elements with React-like class names)
            const reactElements = Array.from(document.querySelectorAll('[class*="react"], [class*="component"], [data-reactroot], [data-react]'));
            const reactInfo = reactElements.map(el => ({
                tagName: el.tagName,
                className: el.className,
                id: el.id,
                dataAttributes: Array.from(el.attributes).filter(attr => attr.name.startsWith('data-')).map(attr => `${attr.name}="${attr.value}"`),
                text: el.innerText ? el.innerText.substring(0, 50) : ''
            }));

            // Get all divs with specific IDs (following HTML standards)
            const divsWithIds = Array.from(document.querySelectorAll('div[id]')).map(div => ({
                id: div.id,
                className: div.className,
                text: div.innerText ? div.innerText.substring(0, 100) : '',
                visible: div.offsetHeight > 0 && div.offsetWidth > 0,
                hasChildren: div.children.length > 0
            }));

            // Check for loading states
            const loadingElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = (el.className + ' ' + el.innerText).toLowerCase();
                return text.includes('loading') || text.includes('spinner') || text.includes('skeleton');
            });

            // Check for error states
            const errorElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = (el.className + ' ' + el.innerText).toLowerCase();
                return text.includes('error') || text.includes('failed') || text.includes('retry');
            });

            return {
                bodyText: bodyText.substring(0, 2000),
                allInputs: inputsInfo,
                searchableElements,
                propertyElements,
                reactInfo,
                divsWithIds,
                loadingElements: loadingElements.length,
                errorElements: errorElements.length,
                totalElements: document.querySelectorAll('*').length
            };
        });

        console.log(`\n📊 Properties Page Analysis:`);
        console.log(`   Total DOM elements: ${pageAnalysis.totalElements}`);
        console.log(`   Input elements found: ${pageAnalysis.allInputs.length}`);
        console.log(`   Searchable elements: ${pageAnalysis.searchableElements.length}`);
        console.log(`   Property-related elements: ${pageAnalysis.propertyElements.length}`);
        console.log(`   Divs with IDs: ${pageAnalysis.divsWithIds.length}`);
        console.log(`   Loading elements: ${pageAnalysis.loadingElements}`);
        console.log(`   Error elements: ${pageAnalysis.errorElements}`);

        console.log(`\n📝 Body text preview:`);
        console.log(pageAnalysis.bodyText);

        if (pageAnalysis.allInputs.length > 0) {
            console.log(`\n🔍 Input elements details:`);
            pageAnalysis.allInputs.forEach((input, i) => {
                console.log(`   ${i + 1}. ${input.tagName} - Type: ${input.type}, Placeholder: "${input.placeholder}", ID: "${input.id}", Visible: ${input.visible}`);
            });
        }

        if (pageAnalysis.searchableElements.length > 0) {
            console.log(`\n🔍 Searchable elements:`);
            pageAnalysis.searchableElements.forEach((el, i) => {
                console.log(`   ${i + 1}. ${el.tagName} - Class: "${el.className}", ID: "${el.id}", Visible: ${el.visible}`);
            });
        }

        if (pageAnalysis.divsWithIds.length > 0) {
            console.log(`\n🆔 Divs with IDs (first 10):`);
            pageAnalysis.divsWithIds.slice(0, 10).forEach((div, i) => {
                console.log(`   ${i + 1}. ID: "${div.id}", Class: "${div.className}", Visible: ${div.visible}, Has children: ${div.hasChildren}`);
            });
        }

        // Try to interact with any found input elements
        if (pageAnalysis.allInputs.length > 0) {
            console.log(`\n🧪 Testing input interactions...`);

            for (let i = 0; i < Math.min(pageAnalysis.allInputs.length, 3); i++) {
                const input = pageAnalysis.allInputs[i];
                try {
                    // Try to find and interact with this input
                    let selector = '';
                    if (input.id) {
                        selector = `#${input.id}`;
                    } else if (input.className) {
                        selector = `.${input.className.split(' ')[0]}`;
                    } else {
                        selector = input.tagName.toLowerCase();
                    }

                    const element = await page.$(selector);
                    if (element) {
                        await element.click();
                        await element.type('test input', { delay: 100 });
                        console.log(`   ✅ Successfully typed into: ${selector}`);

                        // Take screenshot after interaction
                        await page.screenshot({
                            path: `./properties_page_input_test_${i}.png`,
                            fullPage: true
                        });
                    }
                } catch (error) {
                    console.log(`   ❌ Failed to interact with input ${i + 1}: ${error.message}`);
                }
            }
        }

        // Check for async content loading by waiting and checking again
        console.log(`\n⏳ Waiting for potential async content...`);
        await new Promise(resolve => setTimeout(resolve, 5000));

        const secondAnalysis = await page.evaluate(() => {
            const allInputs = Array.from(document.querySelectorAll('input, textarea, select, [contenteditable]'));
            return {
                inputCount: allInputs.length,
                bodyText: document.body.innerText.substring(0, 1000),
                hasNewContent: document.querySelectorAll('*').length
            };
        });

        console.log(`\n🔄 After waiting (potential async load):`);
        console.log(`   Input elements: ${secondAnalysis.inputCount} (was ${pageAnalysis.allInputs.length})`);
        console.log(`   Total elements: ${secondAnalysis.hasNewContent} (was ${pageAnalysis.totalElements})`);

        if (secondAnalysis.inputCount !== pageAnalysis.allInputs.length) {
            console.log(`   📈 Content changed! New inputs detected.`);
            // Take another screenshot
            await page.screenshot({
                path: './properties_page_after_wait.png',
                fullPage: true
            });
        }

        // Try navigation within the page (scrolling)
        console.log(`\n📜 Testing page scrolling...`);
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Check if scrolling revealed new content
        const afterScrollAnalysis = await page.evaluate(() => {
            const allInputs = Array.from(document.querySelectorAll('input, textarea, select, [contenteditable]'));
            return {
                inputCount: allInputs.length,
                visibleInputs: allInputs.filter(input => input.offsetHeight > 0 && input.offsetWidth > 0).length
            };
        });

        console.log(`   After scrolling: ${afterScrollAnalysis.inputCount} inputs, ${afterScrollAnalysis.visibleInputs} visible`);

        await page.screenshot({
            path: './properties_page_after_scroll.png',
            fullPage: true
        });

        return pageAnalysis;

    } catch (error) {
        console.error('❌ Properties page test failed:', error.message);
        await page.screenshot({
            path: './properties_page_error.png',
            fullPage: true
        });
    } finally {
        await browser.close();
    }
}

testPropertiesPage().catch(console.error);