const { chromium } = require('playwright');

async function verifyPropertyFixes() {
    console.log('🔍 Starting Property Fixes Verification...');
    
    const browser = await chromium.launch({ 
        headless: false, 
        slowMo: 1000 // Add delay to see actions
    });
    const page = await browser.newPage();
    
    try {
        // Set viewport for consistent screenshots
        await page.setViewportSize({ width: 1200, height: 800 });
        
        console.log('📍 Navigating to property page...');
        await page.goto('http://localhost:5174/properties/parkland/12681-nw-78-mnr', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        // Wait for page to load completely
        await page.waitForTimeout(3000);
        
        console.log('📸 Taking initial full page screenshot...');
        await page.screenshot({ 
            path: 'ui_screenshots/property_fixes_verification_full.png',
            fullPage: true
        });
        
        // Check for console errors
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        console.log('✅ VERIFICATION 1: Owner Name Check');
        let ownerName = 'Not Found';
        try {
            // Look for owner name in multiple possible locations
            const ownerSelectors = [
                'text=IH3 PROPERTY FL LP',
                '[data-testid="owner-name"]',
                '.owner-name',
                'text=INVITATION HOMES' // Check if old value still exists
            ];
            
            for (const selector of ownerSelectors) {
                const element = await page.locator(selector).first();
                if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
                    ownerName = await element.textContent();
                    console.log(`   Found owner: "${ownerName}" with selector: ${selector}`);
                    break;
                }
            }
            
            // Take screenshot of owner section
            const ownerSection = await page.locator('text=Owner').first();
            if (await ownerSection.isVisible().catch(() => false)) {
                await ownerSection.screenshot({ path: 'ui_screenshots/owner_section_verification.png' });
            }
        } catch (error) {
            console.log('   ❌ Error checking owner name:', error.message);
        }
        
        console.log('✅ VERIFICATION 2: Assessed Value Check');
        let assessedValue = 'Not Found';
        try {
            // Look for assessed value in multiple locations
            const valueSelectors = [
                'text=$601,370',
                'text=601370',
                'text=601,370',
                '[data-testid="assessed-value"]',
                '.assessed-value',
                'text=$180' // Check if old incorrect value still exists
            ];
            
            for (const selector of valueSelectors) {
                const element = await page.locator(selector).first();
                if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
                    assessedValue = await element.textContent();
                    console.log(`   Found assessed value: "${assessedValue}" with selector: ${selector}`);
                    break;
                }
            }
        } catch (error) {
            console.log('   ❌ Error checking assessed value:', error.message);
        }
        
        console.log('✅ VERIFICATION 3: Overview Tab Check');
        try {
            // Click on Overview tab if it exists
            const overviewTab = page.locator('text=Overview').first();
            if (await overviewTab.isVisible({ timeout: 2000 }).catch(() => false)) {
                await overviewTab.click();
                await page.waitForTimeout(2000);
                
                console.log('📸 Taking Overview tab screenshot...');
                await page.screenshot({ 
                    path: 'ui_screenshots/overview_tab_verification.png',
                    fullPage: true
                });
                
                // Check for Most Recent Sale section
                const mostRecentSale = page.locator('text=Most Recent Sale');
                if (await mostRecentSale.isVisible().catch(() => false)) {
                    console.log('   ✅ Most Recent Sale section found');
                    await mostRecentSale.screenshot({ path: 'ui_screenshots/most_recent_sale_section.png' });
                } else {
                    console.log('   ❌ Most Recent Sale section not found');
                }
            }
        } catch (error) {
            console.log('   ❌ Error checking Overview tab:', error.message);
        }
        
        console.log('✅ VERIFICATION 4: Core Property Info Tab Check');
        try {
            // Click on Core Property Info tab
            const corePropertyTab = page.locator('text=Core Property Info').first();
            if (await corePropertyTab.isVisible({ timeout: 2000 }).catch(() => false)) {
                await corePropertyTab.click();
                await page.waitForTimeout(2000);
                
                console.log('📸 Taking Core Property Info tab screenshot...');
                await page.screenshot({ 
                    path: 'ui_screenshots/core_property_info_verification.png',
                    fullPage: true
                });
                
                // Count N/A values
                const naElements = await page.locator('text=N/A').count();
                console.log(`   Found ${naElements} "N/A" values in Core Property Info tab`);
                
            }
        } catch (error) {
            console.log('   ❌ Error checking Core Property Info tab:', error.message);
        }
        
        console.log('✅ VERIFICATION 5: All Tabs Data Check');
        const tabs = ['Overview', 'Core Property Info', 'Property Tax Info', 'Building Permits', 'Sunbiz Info'];
        
        for (const tabName of tabs) {
            try {
                console.log(`   Checking ${tabName} tab...`);
                const tab = page.locator(`text=${tabName}`).first();
                if (await tab.isVisible({ timeout: 2000 }).catch(() => false)) {
                    await tab.click();
                    await page.waitForTimeout(1500);
                    
                    // Count N/A values in this tab
                    const naCount = await page.locator('text=N/A').count();
                    console.log(`     ${tabName}: ${naCount} N/A values found`);
                    
                    // Take screenshot of tab
                    await page.screenshot({ 
                        path: `ui_screenshots/${tabName.toLowerCase().replace(/ /g, '_')}_tab_verification.png`
                    });
                }
            } catch (error) {
                console.log(`   ❌ Error checking ${tabName} tab:`, error.message);
            }
        }
        
        console.log('✅ VERIFICATION 6: Property Tax Status Check');
        try {
            const propertyTaxTab = page.locator('text=Property Tax Info').first();
            if (await propertyTaxTab.isVisible({ timeout: 2000 }).catch(() => false)) {
                await propertyTaxTab.click();
                await page.waitForTimeout(2000);
                
                // Check for delinquency status
                const delinquent = page.locator('text=Delinquent');
                const isDelinquent = await delinquent.isVisible().catch(() => false);
                console.log(`   Property tax delinquency status: ${isDelinquent ? 'DELINQUENT' : 'CURRENT'}`);
            }
        } catch (error) {
            console.log('   ❌ Error checking property tax status:', error.message);
        }
        
        // Final comprehensive report
        console.log('\n📊 COMPREHENSIVE VERIFICATION REPORT');
        console.log('=====================================');
        console.log(`🏠 Property: 12681 NW 78 MNR, Parkland`);
        console.log(`👤 Owner Name: ${ownerName}`);
        console.log(`💰 Assessed Value: ${assessedValue}`);
        console.log(`🚨 Console Errors: ${consoleErrors.length} found`);
        
        if (consoleErrors.length > 0) {
            console.log('\n🚨 Console Errors Found:');
            consoleErrors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error}`);
            });
        }
        
        // Status summary
        const ownerFixed = ownerName.includes('IH3 PROPERTY FL LP');
        const assessedFixed = assessedValue.includes('601') && !assessedValue.includes('180');
        
        console.log('\n✅ FIX STATUS SUMMARY:');
        console.log(`   Owner Name Fix: ${ownerFixed ? '✅ SUCCESS' : '❌ FAILED'}`);
        console.log(`   Assessed Value Fix: ${assessedFixed ? '✅ SUCCESS' : '❌ FAILED'}`);
        console.log(`   Console Errors: ${consoleErrors.length === 0 ? '✅ CLEAN' : '❌ ' + consoleErrors.length + ' ERRORS'}`);
        
        console.log('\n📸 Screenshots saved to ui_screenshots/ directory');
        console.log('   - property_fixes_verification_full.png');
        console.log('   - overview_tab_verification.png');
        console.log('   - core_property_info_verification.png');
        console.log('   - [tab_name]_tab_verification.png for each tab');
        
    } catch (error) {
        console.error('❌ Test failed with error:', error);
        
        // Take error screenshot
        await page.screenshot({ 
            path: 'ui_screenshots/property_verification_error.png',
            fullPage: true
        });
    } finally {
        await browser.close();
        console.log('\n🏁 Property fixes verification completed!');
    }
}

// Run the verification
verifyPropertyFixes().catch(console.error);