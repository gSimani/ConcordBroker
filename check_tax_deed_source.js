import { chromium } from 'playwright';
import { writeFileSync } from 'fs';

async function checkTaxDeedSource() {
    console.log('Starting tax deed source analysis...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        console.log('Navigating to Broward tax deed auction site...');
        await page.goto('https://broward.deedauction.net/auction/110', { 
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        // Wait for the page to load completely
        await page.waitForTimeout(5000);
        
        // Look for property listings - need to inspect the page structure
        const propertySelectors = [
            '.property-item',
            '.auction-item', 
            '.listing-item',
            '.property-row',
            '[data-property]',
            '.item-row',
            'tr[data-id]',
            'table tbody tr',
            '.property-listing'
        ];
        
        let propertyCount = 0;
        let foundSelector = null;
        
        for (const selector of propertySelectors) {
            try {
                const elements = await page.$$(selector);
                if (elements.length > 0) {
                    propertyCount = elements.length;
                    foundSelector = selector;
                    console.log(`Found ${propertyCount} properties using selector: ${selector}`);
                    break;
                }
            } catch (e) {
                // Continue to next selector
            }
        }
        
        // Take a screenshot for analysis
        await page.screenshot({ 
            path: 'tax_deed_source_screenshot.png',
            fullPage: true 
        });
        
        // Get page content for analysis
        const pageContent = await page.content();
        
        // Look for any text that might indicate property count
        const textContent = await page.textContent('body');
        const propertyCountRegex = /(\d+)\s*(properties|items|listings|auctions)/gi;
        const matches = textContent.match(propertyCountRegex);
        
        console.log('Property count matches found:', matches);
        
        // Get table data if available
        const tables = await page.$$('table');
        let tableData = [];
        
        for (let i = 0; i < tables.length; i++) {
            const rows = await tables[i].$$('tr');
            if (rows.length > 1) { // Has header + data rows
                console.log(`Table ${i + 1} has ${rows.length - 1} data rows`);
                tableData.push({
                    tableIndex: i + 1,
                    rowCount: rows.length - 1
                });
            }
        }
        
        // Try to get specific property data
        const propertyData = [];
        
        // Look for common property data patterns
        const propertyElements = await page.$$('tr');
        for (const element of propertyElements) {
            try {
                const text = await element.textContent();
                if (text && (text.includes('parcel') || text.includes('certificate') || text.includes('$'))) {
                    const cells = await element.$$('td');
                    if (cells.length > 3) { // Likely a data row
                        const cellTexts = [];
                        for (const cell of cells) {
                            cellTexts.push(await cell.textContent());
                        }
                        propertyData.push(cellTexts);
                    }
                }
            } catch (e) {
                // Skip problematic elements
            }
        }
        
        const result = {
            timestamp: new Date().toISOString(),
            url: 'https://broward.deedauction.net/auction/110',
            propertyCount: propertyCount,
            foundSelector: foundSelector,
            textMatches: matches,
            tableData: tableData,
            samplePropertyData: propertyData.slice(0, 5), // First 5 properties
            totalPropertiesFound: propertyData.length,
            pageTitle: await page.title(),
            hasTable: tables.length > 0,
            tableCount: tables.length
        };
        
        console.log('Analysis complete:', JSON.stringify(result, null, 2));
        
        // Save results
        writeFileSync('tax_deed_source_analysis.json', JSON.stringify(result, null, 2));
        
        return result;
        
    } catch (error) {
        console.error('Error analyzing tax deed source:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

checkTaxDeedSource()
    .then(result => {
        console.log('Tax deed source analysis completed successfully');
        process.exit(0);
    })
    .catch(error => {
        console.error('Failed to analyze tax deed source:', error);
        process.exit(1);
    });