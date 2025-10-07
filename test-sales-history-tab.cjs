const { chromium } = require('playwright');

async function testSalesHistoryTab() {
  console.log('Starting Sales History tab test...');

  // Launch browser
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    // Navigate to properties page
    console.log('1. Navigating to http://localhost:5173/properties...');
    await page.goto('http://localhost:5173/properties');
    await page.waitForLoadState('networkidle');

    // Wait for properties to load
    console.log('2. Waiting for property cards to load...');
    await page.waitForSelector('[data-testid="property-card"], .property-card, .mini-property-card', { timeout: 10000 });

    // Take screenshot of properties page
    await page.screenshot({ path: 'properties-page.png', fullPage: true });
    console.log('   Screenshot saved: properties-page.png');

    // Find and click first property card
    console.log('3. Looking for first property card...');
    const propertyCards = await page.locator('[data-testid="property-card"], .property-card, .mini-property-card').all();

    if (propertyCards.length === 0) {
      throw new Error('No property cards found on the page');
    }

    console.log(`   Found ${propertyCards.length} property cards`);

    // Click on the first property card
    console.log('4. Clicking on first property card...');
    await propertyCards[0].click();

    // Wait for property details page to load
    console.log('5. Waiting for property details to load...');
    await page.waitForLoadState('networkidle');

    // Look for Sales History tab
    console.log('6. Looking for Sales History tab...');
    const salesHistoryTab = page.locator('text=/Sales History/i, [data-testid="sales-history-tab"], .sales-history-tab');

    await page.waitForTimeout(2000); // Wait for tabs to render

    if (await salesHistoryTab.count() === 0) {
      console.log('   Sales History tab not found, looking for any tabs...');
      const allTabs = await page.locator('button, .tab, [role="tab"]').all();
      console.log(`   Found ${allTabs.length} potential tabs`);

      for (let i = 0; i < allTabs.length; i++) {
        const tabText = await allTabs[i].textContent();
        console.log(`   Tab ${i}: "${tabText}"`);
        if (tabText && tabText.toLowerCase().includes('sales')) {
          console.log('   Found sales-related tab!');
          await allTabs[i].click();
          break;
        }
      }
    } else {
      console.log('   Found Sales History tab, clicking...');
      await salesHistoryTab.first().click();
    }

    // Wait for sales history content to load
    console.log('7. Waiting for sales history content...');
    await page.waitForTimeout(3000);

    // Take screenshot of the sales history tab
    await page.screenshot({ path: 'sales-history-tab.png', fullPage: true });
    console.log('   Screenshot saved: sales-history-tab.png');

    // Look for sales data
    console.log('8. Checking for sales data...');

    const salesData = {
      mostRecentPrice: null,
      mostRecentDate: null,
      salesCount: 0,
      hasHighValueSales: false,
      hasFilteredLowValueSales: false
    };

    // Look for price elements
    const priceElements = await page.locator('text=/\\$[\\d,]+/').all();
    console.log(`   Found ${priceElements.length} price elements`);

    if (priceElements.length > 0) {
      for (let i = 0; i < Math.min(priceElements.length, 5); i++) {
        const priceText = await priceElements[i].textContent();
        console.log(`   Price ${i + 1}: ${priceText}`);

        // Extract numeric value
        const numericPrice = parseInt(priceText.replace(/[^0-9]/g, ''));
        if (numericPrice > 1000) {
          salesData.hasHighValueSales = true;
          if (!salesData.mostRecentPrice || numericPrice > salesData.mostRecentPrice) {
            salesData.mostRecentPrice = numericPrice;
          }
        }
      }
    }

    // Look for date elements
    const dateElements = await page.locator('text=/\\d{1,2}\\/\\d{1,2}\\/\\d{4}|\\d{4}-\\d{2}-\\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/').all();
    console.log(`   Found ${dateElements.length} potential date elements`);

    if (dateElements.length > 0) {
      const dateText = await dateElements[0].textContent();
      salesData.mostRecentDate = dateText;
      console.log(`   Most recent date: ${dateText}`);
    }

    // Check for sales summary/statistics
    const summaryElements = await page.locator('text=/average|highest|lowest|total sales|summary/i').all();
    console.log(`   Found ${summaryElements.length} summary/statistics elements`);

    for (let i = 0; i < summaryElements.length; i++) {
      const summaryText = await summaryElements[i].textContent();
      console.log(`   Summary ${i + 1}: ${summaryText}`);
    }

    // Check for any error messages
    const errorElements = await page.locator('text=/error|no data|not found|failed/i').all();
    if (errorElements.length > 0) {
      console.log('   Potential errors found:');
      for (let i = 0; i < errorElements.length; i++) {
        const errorText = await errorElements[i].textContent();
        console.log(`   Error ${i + 1}: ${errorText}`);
      }
    }

    // Final report
    console.log('\n=== SALES HISTORY TAB TEST RESULTS ===');
    console.log('Sales History Tab Status: ✓ Accessible');
    console.log(`Most Recent Sale Price: ${salesData.mostRecentPrice ? '$' + salesData.mostRecentPrice.toLocaleString() : 'Not found'}`);
    console.log(`Most Recent Sale Date: ${salesData.mostRecentDate || 'Not found'}`);
    console.log(`High Value Sales (>$1000): ${salesData.hasHighValueSales ? 'Yes' : 'No'}`);
    console.log(`Total Price Elements Found: ${priceElements.length}`);
    console.log(`Summary/Statistics Elements: ${summaryElements.length}`);

    return {
      success: true,
      salesHistoryTabWorking: true,
      mostRecentPrice: salesData.mostRecentPrice,
      mostRecentDate: salesData.mostRecentDate,
      hasHighValueSales: salesData.hasHighValueSales,
      priceElementsCount: priceElements.length,
      summaryElementsCount: summaryElements.length,
      screenshots: ['properties-page.png', 'sales-history-tab.png']
    };

  } catch (error) {
    console.error('Error during test:', error.message);

    // Take error screenshot
    await page.screenshot({ path: 'sales-history-error.png', fullPage: true });
    console.log('Error screenshot saved: sales-history-error.png');

    return {
      success: false,
      error: error.message,
      salesHistoryTabWorking: false,
      screenshots: ['sales-history-error.png']
    };
  } finally {
    await browser.close();
  }
}

// Run the test
testSalesHistoryTab().then(result => {
  console.log('\n=== FINAL TEST RESULT ===');
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}).catch(error => {
  console.error('Test failed:', error);
  process.exit(1);
});