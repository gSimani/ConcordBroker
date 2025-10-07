const { chromium } = require('playwright');

async function testDirectProperty() {
  console.log('Testing direct property URL access...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    // Try some potential property URLs based on common patterns
    const testUrls = [
      'http://localhost:5173/property/123456',
      'http://localhost:5173/property/123456789012',
      'http://localhost:5173/properties/123456',
      'http://localhost:5173/property/sample',
      'http://localhost:5173/property/test'
    ];

    for (const url of testUrls) {
      console.log(`Testing URL: ${url}`);

      try {
        await page.goto(url);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000);

        const pageText = await page.textContent('body');
        const title = await page.title();

        console.log(`   Title: ${title}`);
        console.log(`   Text preview: ${pageText.substring(0, 200)}`);

        // Check if it looks like a property page
        if (pageText.includes('Sales History') || pageText.includes('Property Details') ||
            pageText.includes('Tax Information') || pageText.includes('Assessment')) {

          console.log('   *** Found a property page! ***');
          await page.screenshot({ path: 'direct-property-found.png', fullPage: true });

          // Look for Sales History tab
          const salesHistoryElements = await page.locator('text=/Sales History/i, [data-testid*="sales"], button:has-text("Sales")').all();
          console.log(`   Found ${salesHistoryElements.length} sales history elements`);

          if (salesHistoryElements.length > 0) {
            console.log('   Clicking on Sales History...');
            await salesHistoryElements[0].click();
            await page.waitForTimeout(3000);

            await page.screenshot({ path: 'sales-history-tab.png', fullPage: true });
            console.log('   Sales History screenshot saved!');

            // Analyze the content
            const salesContent = await page.textContent('body');
            const hasPrices = salesContent.match(/\$[\d,]+/g);
            const hasDates = salesContent.match(/\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}/g);

            console.log(`   Found ${hasPrices ? hasPrices.length : 0} price elements`);
            console.log(`   Found ${hasDates ? hasDates.length : 0} date elements`);

            if (hasPrices) {
              console.log(`   Prices found: ${hasPrices.slice(0, 3).join(', ')}`);
            }
            if (hasDates) {
              console.log(`   Dates found: ${hasDates.slice(0, 3).join(', ')}`);
            }

            return {
              success: true,
              url: url,
              salesHistoryWorking: true,
              pricesFound: hasPrices ? hasPrices.length : 0,
              datesFound: hasDates ? hasDates.length : 0,
              mostRecentPrice: hasPrices ? hasPrices[0] : null,
              mostRecentDate: hasDates ? hasDates[0] : null
            };
          }

          return { success: true, url: url, salesHistoryWorking: false };
        }

      } catch (error) {
        console.log(`   Error with ${url}: ${error.message}`);
      }
    }

    // Also try navigating to a mock/demo property page
    console.log('\nChecking if there are any demo/sample property components...');

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Look for any links or paths that might lead to property details
    const allLinks = await page.locator('a[href*="property"]').all();
    console.log(`Found ${allLinks.length} property-related links`);

    for (let i = 0; i < Math.min(allLinks.length, 5); i++) {
      const href = await allLinks[i].getAttribute('href');
      console.log(`   Link ${i + 1}: ${href}`);
    }

    return { success: false, message: 'No accessible property pages found' };

  } catch (error) {
    console.error('Error during test:', error.message);
    await page.screenshot({ path: 'direct-property-error.png', fullPage: true });
    return { success: false, error: error.message };
  } finally {
    await browser.close();
  }
}

testDirectProperty().then(result => {
  console.log('\n=== DIRECT PROPERTY TEST RESULT ===');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);