const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function testPropertyPage() {
    console.log('🚀 Starting visual test of Property Page...');
    
    let browser;
    try {
        browser = await puppeteer.launch({ 
            headless: false, // Set to true if you don't want to see the browser
            devtools: false,
            defaultViewport: { width: 1920, height: 1080 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        const page = await browser.newPage();
        
        // Navigate to the property page
        const url = 'http://localhost:5185/property/064210010010';
        console.log(`📍 Navigating to: ${url}`);
        
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
        console.log('✅ Page loaded successfully');
        
        // Wait for the page to fully render
        console.log('⏳ Waiting for page to fully render...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Create screenshots directory if it doesn't exist
        const screenshotDir = path.join(__dirname, 'ui_screenshots');
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }
        
        // Take initial screenshot
        console.log('📸 Taking initial full page screenshot...');
        await page.screenshot({
            path: path.join(screenshotDir, 'property_page_initial.png'),
            fullPage: true
        });
        
        // Check what tabs are visible
        console.log('🔍 Analyzing visible tabs...');
        const tabs = await page.evaluate(() => {
            const tabButtons = Array.from(document.querySelectorAll('button[role="tab"]'));
            return tabButtons.map(tab => ({
                text: tab.textContent.trim(),
                value: tab.getAttribute('data-value') || tab.getAttribute('value') || 'unknown',
                classList: Array.from(tab.classList),
                isSelected: tab.getAttribute('data-state') === 'active' || tab.getAttribute('aria-selected') === 'true'
            }));
        });
        
        console.log('📋 Found tabs:', tabs);
        
        // Take screenshot of current view
        await page.screenshot({
            path: path.join(screenshotDir, 'property_page_tabs_overview.png'),
            fullPage: true
        });
        
        // Test each tab
        for (let i = 0; i < tabs.length; i++) {
            const tab = tabs[i];
            console.log(`\n🖱️  Testing tab: "${tab.text}"`);
            
            try {
                // Click on the tab
                await page.evaluate((tabIndex) => {
                    const tabButtons = Array.from(document.querySelectorAll('button[role="tab"]'));
                    if (tabButtons[tabIndex]) {
                        tabButtons[tabIndex].click();
                    }
                }, i);
                
                // Wait for content to load
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                // Take screenshot of this tab
                const tabFileName = `property_page_tab_${tab.text.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}.png`;
                await page.screenshot({
                    path: path.join(screenshotDir, tabFileName),
                    fullPage: true
                });
                
                // Get tab content information
                const tabContent = await page.evaluate(() => {
                    const activePanel = document.querySelector('[data-state="active"][role="tabpanel"]');
                    if (activePanel) {
                        return {
                            hasContent: activePanel.textContent.trim().length > 0,
                            contentPreview: activePanel.textContent.trim().substring(0, 200) + '...',
                            containsExecutiveElements: activePanel.querySelector('.card-executive, .elegant-card-header, .gold-accent') !== null,
                            errorMessages: Array.from(activePanel.querySelectorAll('.error, .alert-error, [class*="error"]')).map(el => el.textContent.trim())
                        };
                    }
                    return { hasContent: false, contentPreview: 'No active panel found' };
                });
                
                console.log(`   Content loaded: ${tabContent.hasContent}`);
                console.log(`   Executive styling: ${tabContent.containsExecutiveElements}`);
                console.log(`   Content preview: ${tabContent.contentPreview}`);
                if (tabContent.errorMessages.length > 0) {
                    console.log(`   ⚠️  Error messages found: ${tabContent.errorMessages.join(', ')}`);
                }
                
            } catch (error) {
                console.error(`   ❌ Error testing tab "${tab.text}":`, error.message);
            }
        }
        
        // Check for specific elements we expect
        console.log('\n🔍 Checking for expected elements...');
        const expectedElements = await page.evaluate(() => {
            return {
                sunbizTab: !!Array.from(document.querySelectorAll('button[role="tab"]')).find(tab => 
                    tab.textContent.includes('Sunbiz') || tab.textContent.includes('Business')
                ),
                taxTab: !!Array.from(document.querySelectorAll('button[role="tab"]')).find(tab => 
                    tab.textContent.includes('Tax') || tab.textContent.includes('Property Tax')
                ),
                executiveCards: document.querySelectorAll('.card-executive').length,
                elegantHeaders: document.querySelectorAll('.elegant-card-header').length,
                goldAccents: document.querySelectorAll('.gold-accent').length,
                hasElegantPropertyCSS: !!Array.from(document.styleSheets).find(sheet => {
                    try {
                        return sheet.href && sheet.href.includes('elegant-property.css');
                    } catch(e) {
                        return false;
                    }
                })
            };
        });
        
        console.log('📊 Element Analysis:');
        console.log(`   Sunbiz Tab Present: ${expectedElements.sunbizTab ? '✅ YES' : '❌ NO'}`);
        console.log(`   Tax Tab Present: ${expectedElements.taxTab ? '✅ YES' : '❌ NO'}`);
        console.log(`   Executive Cards: ${expectedElements.executiveCards}`);
        console.log(`   Elegant Headers: ${expectedElements.elegantHeaders}`);
        console.log(`   Gold Accents: ${expectedElements.goldAccents}`);
        console.log(`   Elegant CSS Loaded: ${expectedElements.hasElegantPropertyCSS ? '✅ YES' : '❌ NO'}`);
        
        // Take final screenshot
        await page.screenshot({
            path: path.join(screenshotDir, 'property_page_final.png'),
            fullPage: true
        });
        
        // Console errors check
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        // Reload page to capture console errors
        console.log('\n🔄 Reloading page to check for console errors...');
        await page.reload({ waitUntil: 'networkidle2' });
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('\n📱 Taking mobile viewport screenshot...');
        await page.setViewport({ width: 375, height: 812 }); // iPhone X size
        await page.screenshot({
            path: path.join(screenshotDir, 'property_page_mobile.png'),
            fullPage: true
        });
        
        // Final summary
        console.log('\n📋 VISUAL TEST SUMMARY:');
        console.log('========================');
        console.log(`🌐 URL Tested: ${url}`);
        console.log(`📸 Screenshots saved to: ${screenshotDir}`);
        console.log(`📱 Tabs Found: ${tabs.length}`);
        console.log(`🎨 Executive Styling Elements: ${expectedElements.executiveCards + expectedElements.elegantHeaders + expectedElements.goldAccents}`);
        console.log(`⚠️  Console Errors: ${consoleErrors.length}`);
        
        if (consoleErrors.length > 0) {
            console.log('\n❌ Console Errors Found:');
            consoleErrors.forEach(error => console.log(`   - ${error}`));
        }
        
        console.log('\n✅ Visual testing complete! Check the screenshots folder for detailed results.');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run the test
testPropertyPage().catch(console.error);