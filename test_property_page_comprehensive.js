const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testPropertyPage() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();
    
    // Enable console logging
    const consoleMessages = [];
    page.on('console', msg => {
        const message = `[${msg.type()}] ${msg.text()}`;
        console.log(message);
        consoleMessages.push(message);
    });
    
    // Track network requests
    const networkRequests = [];
    page.on('request', request => {
        if (request.url().includes('supabase') || request.url().includes('api')) {
            networkRequests.push({
                url: request.url(),
                method: request.method(),
                timestamp: new Date().toISOString()
            });
        }
    });
    
    // Track network responses
    const networkResponses = [];
    page.on('response', response => {
        if (response.url().includes('supabase') || response.url().includes('api')) {
            networkResponses.push({
                url: response.url(),
                status: response.status(),
                timestamp: new Date().toISOString()
            });
        }
    });

    try {
        console.log('Navigating to property page...');
        await page.goto('http://localhost:5174/properties/parkland/10892-nw-72-pl', {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        // Wait for the page to load completely
        await page.waitForTimeout(3000);

        console.log('Taking initial screenshot...');
        await page.screenshot({
            path: 'ui_screenshots/property_page_comprehensive_initial.png',
            fullPage: true
        });

        // Get all tab elements
        const tabs = await page.$$('[role="tab"]');
        console.log(`Found ${tabs.length} tabs`);

        const tabData = {};
        
        // Test each tab
        for (let i = 0; i < tabs.length; i++) {
            const tab = tabs[i];
            const tabText = await tab.textContent();
            console.log(`\nTesting tab: ${tabText}`);
            
            await tab.click();
            await page.waitForTimeout(2000);
            
            // Take screenshot of each tab
            await page.screenshot({
                path: `ui_screenshots/property_tab_${tabText.toLowerCase().replace(/\s+/g, '_')}_comprehensive.png`,
                fullPage: true
            });
            
            // Get tab content
            const tabPanel = await page.$('[role="tabpanel"]');
            const tabContent = await tabPanel ? await tabPanel.textContent() : 'No content found';
            
            tabData[tabText] = {
                content: tabContent,
                screenshot: `property_tab_${tabText.toLowerCase().replace(/\s+/g, '_')}_comprehensive.png`
            };

            // Special checks for specific tabs
            if (tabText === 'Core Property Info') {
                console.log('Checking Core Property Info tab...');
                
                // Look for Sales History section
                const salesHistorySection = await page.$('text=Sales History');
                if (salesHistorySection) {
                    console.log('Sales History section found');
                    const salesData = await page.$$eval('.sales-history-item, [data-testid*="sales"], .sale-item', 
                        elements => elements.map(el => el.textContent));
                    tabData[tabText].salesHistory = salesData;
                } else {
                    console.log('Sales History section NOT found');
                }
                
                // Check for N/A values
                const naValues = await page.$$eval('text=N/A', elements => 
                    elements.map(el => ({
                        text: el.textContent,
                        parent: el.parentElement?.textContent || 'Unknown parent'
                    }))
                );
                tabData[tabText].naValues = naValues;
                
            } else if (tabText === 'Overview') {
                console.log('Checking Overview tab...');
                
                // Look for Most Recent Sale section
                const mostRecentSale = await page.$('text=Most Recent Sale');
                if (mostRecentSale) {
                    console.log('Most Recent Sale section found');
                    const saleData = await page.evaluate(() => {
                        const section = document.querySelector('text=Most Recent Sale')?.closest('.sale-section, .recent-sale, [data-testid*="recent-sale"]');
                        return section ? section.textContent : 'Section found but no data extracted';
                    });
                    tabData[tabText].mostRecentSale = saleData;
                } else {
                    console.log('Most Recent Sale section NOT found');
                }
                
                // Check for N/A values
                const naValues = await page.$$eval('text=N/A', elements => 
                    elements.map(el => ({
                        text: el.textContent,
                        parent: el.parentElement?.textContent || 'Unknown parent'
                    }))
                );
                tabData[tabText].naValues = naValues;
            }
        }

        // Check for specific data elements across the page
        console.log('\nChecking for specific data elements...');
        
        // Look for dollar amounts
        const dollarAmounts = await page.$$eval('text=/\\$[\\d,]+/', elements => 
            elements.map(el => el.textContent));
        
        // Look for dates
        const dates = await page.$$eval('text=/\\d{1,2}\\/\\d{1,2}\\/\\d{4}|\\d{4}-\\d{2}-\\d{2}/', elements => 
            elements.map(el => el.textContent));
        
        // Look for all N/A values
        const allNAValues = await page.$$eval('text=N/A', elements => 
            elements.map(el => ({
                text: el.textContent,
                parent: el.parentElement?.textContent || 'Unknown parent',
                grandparent: el.parentElement?.parentElement?.textContent || 'Unknown grandparent'
            }))
        );

        // Take final screenshot
        await page.screenshot({
            path: 'ui_screenshots/property_page_comprehensive_final.png',
            fullPage: true
        });

        // Generate comprehensive report
        const report = {
            timestamp: new Date().toISOString(),
            url: page.url(),
            tabData,
            dollarAmounts,
            dates,
            allNAValues,
            consoleMessages,
            networkRequests,
            networkResponses,
            recommendations: []
        };

        // Analyze and add recommendations
        if (allNAValues.length > 0) {
            report.recommendations.push(`Found ${allNAValues.length} N/A values that may need review`);
        }
        
        if (consoleMessages.some(msg => msg.includes('error') || msg.includes('Error'))) {
            report.recommendations.push('Console errors detected - check browser console for details');
        }
        
        if (networkRequests.length === 0) {
            report.recommendations.push('No Supabase/API requests detected - data may not be loading from backend');
        }

        // Save report to file
        fs.writeFileSync('property_page_comprehensive_report.json', JSON.stringify(report, null, 2));
        
        console.log('\n=== COMPREHENSIVE PROPERTY PAGE REPORT ===');
        console.log(`Total tabs tested: ${Object.keys(tabData).length}`);
        console.log(`Dollar amounts found: ${dollarAmounts.length}`);
        console.log(`Dates found: ${dates.length}`);
        console.log(`N/A values found: ${allNAValues.length}`);
        console.log(`Console messages: ${consoleMessages.length}`);
        console.log(`Network requests: ${networkRequests.length}`);
        console.log(`Network responses: ${networkResponses.length}`);
        
        if (allNAValues.length > 0) {
            console.log('\n=== N/A VALUES FOUND ===');
            allNAValues.forEach((na, index) => {
                console.log(`${index + 1}. Context: "${na.parent}"`);
            });
        }
        
        if (consoleMessages.some(msg => msg.includes('error') || msg.includes('Error'))) {
            console.log('\n=== CONSOLE ERRORS ===');
            consoleMessages.filter(msg => msg.includes('error') || msg.includes('Error')).forEach(error => {
                console.log(error);
            });
        }
        
        console.log('\n=== RECOMMENDATIONS ===');
        report.recommendations.forEach(rec => console.log(`• ${rec}`));
        
        console.log('\nReport saved to: property_page_comprehensive_report.json');
        console.log('Screenshots saved to ui_screenshots/ directory');

    } catch (error) {
        console.error('Error during testing:', error);
        await page.screenshot({
            path: 'ui_screenshots/property_page_error.png',
            fullPage: true
        });
    } finally {
        await browser.close();
    }
}

testPropertyPage().catch(console.error);