const { chromium } = require('playwright');

async function testPropertiesPage() {
  console.log('Starting Playwright test for properties page...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000 // Slow down actions for visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Listen for console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text, timestamp: new Date().toISOString() });
    console.log(`[${type.toUpperCase()}] ${text}`);
  });

  // Listen for network errors
  page.on('response', response => {
    if (!response.ok()) {
      console.log(`[NETWORK ERROR] ${response.status()} ${response.url()}`);
    }
  });

  try {
    console.log('Navigating to http://localhost:5173/properties');
    await page.goto('http://localhost:5173/properties', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('Page loaded, waiting 10 seconds for full initialization...');
    await page.waitForTimeout(10000);

    // Take initial screenshot
    console.log('Taking screenshot...');
    await page.screenshot({
      path: 'local-properties-fixed.png',
      fullPage: true
    });

    // Check for property count indicators
    let propertyCount = 0;
    let propertiesVisible = false;

    // Look for various indicators of property count
    const countSelectors = [
      '[data-testid="property-count"]',
      '.property-count',
      'text=properties found',
      'text=Properties Found',
      'text=Total:',
      '[class*="total"]',
      '[class*="count"]'
    ];

    for (const selector of countSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible()) {
          const text = await element.textContent();
          console.log(`Found count element: ${selector} - "${text}"`);

          // Extract numbers from text
          const numbers = text.match(/\d+/g);
          if (numbers && numbers.length > 0) {
            propertyCount = Math.max(propertyCount, parseInt(numbers[0]));
          }
        }
      } catch (e) {
        // Selector not found, continue
      }
    }

    // Check for property cards/items
    const propertySelectors = [
      '[data-testid="property-card"]',
      '.property-card',
      '[class*="property-item"]',
      '[class*="PropertyCard"]',
      '.MiniPropertyCard'
    ];

    for (const selector of propertySelectors) {
      try {
        const elements = await page.locator(selector);
        const count = await elements.count();
        if (count > 0) {
          console.log(`Found ${count} property elements using selector: ${selector}`);
          propertyCount = Math.max(propertyCount, count);
          propertiesVisible = true;
        }
      } catch (e) {
        // Selector not found, continue
      }
    }

    // Check for empty state or loading indicators
    const emptyStateSelectors = [
      'text=No properties found',
      'text=0 properties',
      'text=Loading',
      '[data-testid="loading"]',
      '.loading',
      '.spinner'
    ];

    let hasEmptyState = false;
    for (const selector of emptyStateSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible()) {
          const text = await element.textContent();
          console.log(`Found empty/loading state: ${selector} - "${text}"`);
          hasEmptyState = true;
        }
      } catch (e) {
        // Selector not found, continue
      }
    }

    // Get page title and URL for verification
    const pageTitle = await page.title();
    const currentUrl = page.url();

    console.log('\n=== TEST RESULTS ===');
    console.log(`Page Title: ${pageTitle}`);
    console.log(`Current URL: ${currentUrl}`);
    console.log(`Property Count: ${propertyCount}`);
    console.log(`Properties Visible: ${propertiesVisible}`);
    console.log(`Has Empty State: ${hasEmptyState}`);
    console.log(`Screenshot saved: local-properties-fixed.png`);

    // Filter console errors
    const errors = consoleMessages.filter(msg => msg.type === 'error');
    const warnings = consoleMessages.filter(msg => msg.type === 'warning');

    console.log(`\nConsole Errors (${errors.length}):`);
    errors.forEach(err => {
      console.log(`  - ${err.text}`);
    });

    console.log(`\nConsole Warnings (${warnings.length}):`);
    warnings.forEach(warn => {
      console.log(`  - ${warn.text}`);
    });

    // Get page content summary
    const bodyText = await page.locator('body').textContent();
    const hasPropertiesText = bodyText.toLowerCase().includes('properties') ||
                             bodyText.toLowerCase().includes('property');

    console.log(`\nPage contains property-related text: ${hasPropertiesText}`);

    return {
      propertyCount,
      propertiesVisible,
      hasEmptyState,
      errors: errors.length,
      warnings: warnings.length,
      consoleMessages,
      pageTitle,
      currentUrl,
      screenshotSaved: true
    };

  } catch (error) {
    console.error('Test failed:', error);
    await page.screenshot({ path: 'local-properties-error.png' });
    throw error;
  } finally {
    await browser.close();
  }
}

// Run the test
testPropertiesPage()
  .then(results => {
    console.log('\n=== FINAL SUMMARY ===');
    console.log(JSON.stringify(results, null, 2));
    process.exit(0);
  })
  .catch(error => {
    console.error('Test suite failed:', error);
    process.exit(1);
  });