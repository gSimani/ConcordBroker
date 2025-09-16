import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function analyzePropertyData() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Create screenshots directory
    const screenshotsDir = path.join(__dirname, 'ui_screenshots');
    if (!fs.existsSync(screenshotsDir)) {
        fs.mkdirSync(screenshotsDir, { recursive: true });
    }

    const propertyUrl = 'http://localhost:5174/properties/parkland/12681-nw-78-mnr';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    let analysis = {
        timestamp,
        propertyAddress: '12681 NW 78 MNR, PARKLAND, Florida 33076',
        url: propertyUrl,
        tabs: {},
        consoleErrors: [],
        networkErrors: [],
        dataComparison: {}
    };

    // Listen for console messages
    page.on('console', msg => {
        if (msg.type() === 'error') {
            analysis.consoleErrors.push({
                text: msg.text(),
                location: msg.location()
            });
        }
    });

    // Listen for network failures
    page.on('response', response => {
        if (!response.ok()) {
            analysis.networkErrors.push({
                url: response.url(),
                status: response.status(),
                statusText: response.statusText()
            });
        }
    });

    try {
        console.log(`Navigating to: ${propertyUrl}`);
        await page.goto(propertyUrl, { waitUntil: 'networkidle' });
        
        // Wait for the page to load
        await page.waitForTimeout(3000);

        // Take initial screenshot
        await page.screenshot({
            path: path.join(screenshotsDir, `property_comprehensive_${timestamp}.png`),
            fullPage: true
        });

        // Get all tab buttons
        const tabs = await page.locator('[role="tablist"] [role="tab"]').all();
        console.log(`Found ${tabs.length} tabs`);

        for (let i = 0; i < tabs.length; i++) {
            const tab = tabs[i];
            const tabText = await tab.textContent();
            const tabName = tabText.trim().replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
            
            console.log(`Analyzing tab: ${tabText}`);
            
            // Click the tab
            await tab.click();
            await page.waitForTimeout(2000);

            // Take screenshot of the tab
            await page.screenshot({
                path: path.join(screenshotsDir, `property_tab_${tabName}_${timestamp}.png`),
                fullPage: true
            });

            // Extract data from the tab
            const tabData = await extractTabData(page, tabText);
            analysis.tabs[tabName] = {
                displayName: tabText,
                data: tabData,
                screenshot: `property_tab_${tabName}_${timestamp}.png`
            };
        }

        // Perform data comparison with official sources
        analysis.dataComparison = compareWithOfficialSources(analysis.tabs);

    } catch (error) {
        console.error('Error during analysis:', error);
        analysis.error = error.message;
    } finally {
        // Save analysis to file
        const analysisPath = path.join(__dirname, `property_analysis_${timestamp}.json`);
        fs.writeFileSync(analysisPath, JSON.stringify(analysis, null, 2));
        
        console.log(`Analysis saved to: ${analysisPath}`);
        await browser.close();
    }

    return analysis;
}

async function extractTabData(page, tabName) {
    const data = {};
    
    try {
        // Extract all visible text content in a structured way
        const textElements = await page.locator('text').all();
        const labels = [];
        const values = [];
        
        for (const element of textElements) {
            const text = await element.textContent();
            if (text && text.trim()) {
                // Check if it looks like a label (ends with colon)
                if (text.trim().endsWith(':')) {
                    labels.push(text.trim().replace(':', ''));
                } else {
                    values.push(text.trim());
                }
            }
        }

        // Try to extract specific data patterns based on tab type
        switch (tabName.toLowerCase()) {
            case 'overview':
                data.overview = await extractOverviewData(page);
                break;
            case 'core property info':
                data.coreProperty = await extractCorePropertyData(page);
                break;
            case 'sunbiz info':
                data.sunbiz = await extractSunbizData(page);
                break;
            case 'property tax info':
                data.propertyTax = await extractPropertyTaxData(page);
                break;
            default:
                data.general = await extractGeneralData(page);
        }

        // Also capture all table data if present
        const tables = await page.locator('table').all();
        if (tables.length > 0) {
            data.tables = [];
            for (let i = 0; i < tables.length; i++) {
                const tableData = await extractTableData(tables[i]);
                data.tables.push(tableData);
            }
        }

        // Capture card data
        const cards = await page.locator('[class*="card"], [class*="Card"]').all();
        if (cards.length > 0) {
            data.cards = [];
            for (let i = 0; i < cards.length; i++) {
                const cardText = await cards[i].textContent();
                if (cardText && cardText.trim()) {
                    data.cards.push(cardText.trim());
                }
            }
        }

    } catch (error) {
        console.error(`Error extracting data from tab ${tabName}:`, error);
        data.error = error.message;
    }

    return data;
}

async function extractOverviewData(page) {
    const data = {};
    try {
        // Look for price/value information
        const priceElements = await page.locator('text=/\\$[0-9,]+/').all();
        for (const element of priceElements) {
            const text = await element.textContent();
            console.log('Found price:', text);
        }

        // Look for specific fields
        const fieldSelectors = [
            'text=Property Value',
            'text=Market Value',
            'text=Assessed Value',
            'text=Just Value',
            'text=Property Owner',
            'text=Property Type',
            'text=Year Built',
            'text=Square Feet',
            'text=Lot Size'
        ];

        for (const selector of fieldSelectors) {
            try {
                const element = await page.locator(selector).first();
                if (await element.isVisible()) {
                    data[selector.replace('text=', '')] = await element.textContent();
                }
            } catch (e) {
                // Field not found
            }
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

async function extractCorePropertyData(page) {
    const data = {};
    try {
        // Look for assessment values
        const assessmentKeywords = ['assessed', 'assessment', 'value', 'just value', 'market value'];
        
        // Extract sales history if present
        const salesElements = await page.locator('text=/sale|sold|price/i').all();
        if (salesElements.length > 0) {
            data.salesHistory = [];
            for (const element of salesElements) {
                const text = await element.textContent();
                data.salesHistory.push(text);
            }
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

async function extractSunbizData(page) {
    const data = {};
    try {
        // Look for business entity information
        const entityFields = [
            'Entity Name',
            'Document Number',
            'Status',
            'FEI/EIN',
            'Date Filed',
            'Principal Address',
            'Registered Agent'
        ];

        for (const field of entityFields) {
            try {
                const element = await page.locator(`text=${field}`).first();
                if (await element.isVisible()) {
                    // Try to get the value next to the label
                    const parent = await element.locator('xpath=..').first();
                    const text = await parent.textContent();
                    data[field] = text;
                }
            } catch (e) {
                // Field not found
            }
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

async function extractPropertyTaxData(page) {
    const data = {};
    try {
        // Look for tax amounts
        const taxElements = await page.locator('text=/tax|amount|due|paid/i').all();
        for (const element of taxElements) {
            const text = await element.textContent();
            console.log('Found tax info:', text);
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

async function extractGeneralData(page) {
    const data = {};
    try {
        // Extract any N/A values
        const naElements = await page.locator('text=/N\\/A|n\\/a|not available|no data/i').all();
        if (naElements.length > 0) {
            data.naValues = [];
            for (const element of naElements) {
                const text = await element.textContent();
                data.naValues.push(text);
            }
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

async function extractTableData(table) {
    const data = { headers: [], rows: [] };
    try {
        // Extract headers
        const headers = await table.locator('th, thead td').all();
        for (const header of headers) {
            const text = await header.textContent();
            data.headers.push(text?.trim() || '');
        }

        // Extract rows
        const rows = await table.locator('tbody tr, tr').all();
        for (const row of rows) {
            const cells = await row.locator('td, th').all();
            const rowData = [];
            for (const cell of cells) {
                const text = await cell.textContent();
                rowData.push(text?.trim() || '');
            }
            if (rowData.length > 0) {
                data.rows.push(rowData);
            }
        }

    } catch (error) {
        data.error = error.message;
    }
    return data;
}

function compareWithOfficialSources(extractedData) {
    // Official data from the images provided
    const officialData = {
        propertyOwner: 'IH3 PROPERTY FLORIDA LP',
        mailingAddress: '% INVITATION HOMES - TAX DEPT, 1717 MAIN ST #2000 DALLAS TX 75201',
        folio: '4741 31 03 1040',
        propertyUse: '01-01 (Single Family)',
        legal: 'HERON BAY CENTRAL 171-23 B LOT 10 BLK D',
        justValue2025: '$628,040',
        assessedValue2025: '$601,370',
        taxableValue2025: '$601,370',
        landValue2025: '$85,580',
        buildingValue2025: '$542,460',
        yearBuilt: '2003/2002',
        salesHistory: [
            { date: '11/6/2013', amount: '$375,000', type: 'WD-Q' },
            { date: '9/15/2010', amount: '$100', type: 'WD-T' },
            { date: '7/27/2009', amount: '$327,000', type: 'WD-Q' },
            { date: '11/16/2004', amount: '$432,000', type: 'WD' }
        ],
        taxBill2024: '$0.00 (paid)',
        lastPayment: '12/02/2024 - $11,674.59',
        adValoremTaxes2024: '$10,345.79',
        nonAdValorem2024: '$1,375.33',
        assessedValue2024: '$546,700',
        sunbizEntity: {
            name: 'IH3 PROPERTY FLORIDA LP',
            documentNumber: 'M13000005449',
            feiEin: '80-0945919',
            dateFiled: '08/28/2013',
            status: 'ACTIVE',
            principalAddress: '5420 Lyndon B Johnson Freeway, Suite 600, Dallas, TX 75240',
            registeredAgent: 'CORPORATION SERVICE COMPANY, 1201 HAYS STREET, TALLAHASSEE, FL 32301'
        }
    };

    const comparison = {
        discrepancies: [],
        missing: [],
        correct: []
    };

    // This is a placeholder - in the actual implementation, we would compare
    // the extracted data with the official data and categorize each field
    
    return comparison;
}

// Run the analysis
analyzePropertyData()
    .then(result => {
        console.log('Property analysis completed successfully');
        console.log(`Console errors: ${result.consoleErrors.length}`);
        console.log(`Network errors: ${result.networkErrors.length}`);
        console.log(`Tabs analyzed: ${Object.keys(result.tabs).length}`);
    })
    .catch(error => {
        console.error('Analysis failed:', error);
    });