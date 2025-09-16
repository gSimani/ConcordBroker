const { chromium } = require('playwright');

async function testPropertyTabs() {
    console.log('Starting Playwright test for property tabs...');
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000 // Add delay between actions for better visibility
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    try {
        console.log('1. Navigating to property page...');
        await page.goto('http://localhost:5185/property/064210010010');
        
        console.log('2. Waiting for page to fully load (3 seconds)...');
        await page.waitForTimeout(3000);
        
        console.log('3. Taking screenshot of initial page...');
        await page.screenshot({ 
            path: 'ui_screenshots/property_initial_page.png',
            fullPage: true 
        });
        
        console.log('4. Looking for Sunbiz Info tab...');
        // Wait for tabs to be available and click Sunbiz Info tab
        const sunbizTab = page.locator('text=Sunbiz Info').first();
        await sunbizTab.waitFor({ state: 'visible', timeout: 10000 });
        await sunbizTab.click();
        
        console.log('5. Waiting 2 seconds after clicking Sunbiz tab...');
        await page.waitForTimeout(2000);
        
        console.log('6. Taking screenshot of Sunbiz tab...');
        await page.screenshot({ 
            path: 'ui_screenshots/property_sunbiz_tab.png',
            fullPage: true 
        });
        
        console.log('7. Looking for Property Tax Info tab...');
        // Click Property Tax Info tab
        const taxTab = page.locator('text=Property Tax Info').first();
        await taxTab.waitFor({ state: 'visible', timeout: 10000 });
        await taxTab.click();
        
        console.log('8. Waiting 2 seconds after clicking Tax tab...');
        await page.waitForTimeout(2000);
        
        console.log('9. Taking screenshot of Property Tax tab...');
        await page.screenshot({ 
            path: 'ui_screenshots/property_tax_tab.png',
            fullPage: true 
        });
        
        // Also check what content is actually present
        console.log('10. Checking for expected content...');
        
        // Check for Sunbiz content
        await sunbizTab.click();
        await page.waitForTimeout(1000);
        
        const sunbizContent = await page.textContent('body');
        const hasSunbizData = sunbizContent.includes('Agent Matching Summary') || 
                             sunbizContent.includes('Detail by Entity Name') ||
                             sunbizContent.includes('Filing Information') ||
                             sunbizContent.includes('Corporate Addresses') ||
                             sunbizContent.includes('Officer/Director');
        
        console.log('Sunbiz tab has detailed content:', hasSunbizData);
        console.log('Sunbiz fallback detected:', sunbizContent.includes('No Sunbiz Information Found'));
        
        // Check for Tax content
        await taxTab.click();
        await page.waitForTimeout(1000);
        
        const taxContent = await page.textContent('body');
        const hasTaxData = taxContent.includes('Executive Tax Overview') || 
                          taxContent.includes('CAPITAL ONE') ||
                          taxContent.includes('TLGFY LLC') ||
                          taxContent.includes('Investment Impact Analysis');
        
        console.log('Tax tab has detailed content:', hasTaxData);
        console.log('Tax fallback detected:', taxContent.includes('Clean Tax Profile'));
        
        console.log('Test completed successfully!');
        
    } catch (error) {
        console.error('Test failed:', error);
        await page.screenshot({ 
            path: 'ui_screenshots/property_error.png',
            fullPage: true 
        });
    } finally {
        await browser.close();
    }
}

testPropertyTabs();