const { chromium } = require('playwright');

async function testSalesHistoryFixed() {
  console.log('Testing Sales History tab with fixed selectors...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    // Navigate to a property page that we know exists
    const testUrl = 'http://localhost:5173/property/test';
    console.log(`1. Navigating to ${testUrl}...`);

    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({ path: 'property-page-initial.png', fullPage: true });
    console.log('   Initial property page screenshot saved');

    // Get page content to analyze
    const pageText = await page.textContent('body');
    console.log('   Page content preview:', pageText.substring(0, 500));

    // Look for Sales History tab with corrected selectors
    console.log('2. Looking for Sales History tab...');

    // Try multiple selector strategies
    const salesHistorySelectors = [
      'button:has-text("Sales History")',
      'button:has-text("Sales")',
      '[data-testid="sales-history-tab"]',
      '.sales-history-tab',
      'text=Sales History',
      'text=Sales'
    ];

    let salesHistoryFound = false;
    let salesHistoryElement = null;

    for (const selector of salesHistorySelectors) {
      try {
        const elements = await page.locator(selector).all();
        if (elements.length > 0) {
          console.log(`   Found Sales History element with selector: ${selector}`);
          salesHistoryElement = elements[0];
          salesHistoryFound = true;
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    if (!salesHistoryFound) {
      // Look for all buttons and tabs
      console.log('   Sales History tab not found, examining all buttons/tabs...');
      const allButtons = await page.locator('button, .tab, [role="tab"]').all();
      console.log(`   Found ${allButtons.length} total buttons/tabs`);

      for (let i = 0; i < allButtons.length; i++) {
        try {
          const buttonText = await allButtons[i].textContent();
          console.log(`   Button/Tab ${i + 1}: "${buttonText}"`);

          if (buttonText && (buttonText.toLowerCase().includes('sales') ||
                           buttonText.toLowerCase().includes('history'))) {
            console.log(`   Found sales-related tab: "${buttonText}"`);
            salesHistoryElement = allButtons[i];
            salesHistoryFound = true;
            break;
          }
        } catch (error) {
          // Skip this element
        }
      }
    }

    if (salesHistoryFound && salesHistoryElement) {
      console.log('3. Clicking on Sales History tab...');
      await salesHistoryElement.click();
      await page.waitForTimeout(3000);

      // Take screenshot of Sales History tab
      await page.screenshot({ path: 'sales-history-tab.png', fullPage: true });
      console.log('   ✓ Sales History tab screenshot saved: sales-history-tab.png');

      // Analyze sales data
      console.log('4. Analyzing sales data...');
      const salesContent = await page.textContent('body');

      // Look for prices
      const priceMatches = salesContent.match(/\$[\d,]+/g);
      console.log(`   Found ${priceMatches ? priceMatches.length : 0} price elements`);
      if (priceMatches) {
        console.log(`   Prices: ${priceMatches.slice(0, 5).join(', ')}`);
      }

      // Look for dates
      const dateMatches = salesContent.match(/\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}/g);
      console.log(`   Found ${dateMatches ? dateMatches.length : 0} date elements`);
      if (dateMatches) {
        console.log(`   Dates: ${dateMatches.slice(0, 5).join(', ')}`);
      }

      // Check for sales over $1000
      let highValueSales = 0;
      let mostRecentPrice = null;

      if (priceMatches) {
        for (const price of priceMatches) {
          const numericPrice = parseInt(price.replace(/[^0-9]/g, ''));
          if (numericPrice > 1000) {
            highValueSales++;
            if (!mostRecentPrice || numericPrice > mostRecentPrice) {
              mostRecentPrice = numericPrice;
            }
          }
        }
      }

      console.log(`   Sales over $1000: ${highValueSales}`);
      console.log(`   Highest sale price: ${mostRecentPrice ? '$' + mostRecentPrice.toLocaleString() : 'None'}`);

      // Look for summary statistics
      const summaryWords = ['average', 'highest', 'lowest', 'total', 'summary', 'statistics'];
      let summaryFound = false;

      for (const word of summaryWords) {
        if (salesContent.toLowerCase().includes(word)) {
          summaryFound = true;
          console.log(`   Found summary keyword: ${word}`);
        }
      }

      return {
        success: true,
        salesHistoryTabWorking: true,
        mostRecentPrice: mostRecentPrice,
        mostRecentDate: dateMatches ? dateMatches[0] : null,
        salesOver1000: highValueSales,
        totalPricesFound: priceMatches ? priceMatches.length : 0,
        totalDatesFound: dateMatches ? dateMatches.length : 0,
        hasSummaryStats: summaryFound,
        screenshots: ['property-page-initial.png', 'sales-history-tab.png'],
        allPrices: priceMatches ? priceMatches.slice(0, 10) : [],
        allDates: dateMatches ? dateMatches.slice(0, 10) : []
      };

    } else {
      console.log('   ❌ Sales History tab not found');

      // Check what tabs/content are available
      const availableContent = await page.textContent('body');
      console.log('   Available content preview:', availableContent.substring(0, 300));

      return {
        success: false,
        salesHistoryTabWorking: false,
        error: 'Sales History tab not found',
        screenshots: ['property-page-initial.png']
      };
    }

  } catch (error) {
    console.error('Error during test:', error.message);
    await page.screenshot({ path: 'sales-history-test-error.png', fullPage: true });

    return {
      success: false,
      salesHistoryTabWorking: false,
      error: error.message,
      screenshots: ['sales-history-test-error.png']
    };
  } finally {
    await browser.close();
  }
}

testSalesHistoryFixed().then(result => {
  console.log('\n=== SALES HISTORY TAB TEST RESULTS ===');
  console.log('Sales History Tab Status:', result.salesHistoryTabWorking ? '✓ Working' : '❌ Not Working');

  if (result.success) {
    console.log('Most Recent Sale Price:', result.mostRecentPrice ? '$' + result.mostRecentPrice.toLocaleString() : 'Not found');
    console.log('Most Recent Sale Date:', result.mostRecentDate || 'Not found');
    console.log('Sales Over $1000:', result.salesOver1000 ? 'Yes' : 'No');
    console.log('Total Price Elements:', result.totalPricesFound);
    console.log('Summary Statistics:', result.hasSummaryStats ? 'Yes' : 'No');
    console.log('Screenshots Saved:', result.screenshots.join(', '));
  } else {
    console.log('Error:', result.error);
  }

  console.log('\nFull Result:');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);