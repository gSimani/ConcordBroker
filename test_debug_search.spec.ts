import { test, expect } from '@playwright/test';

test('Debug Building SqFt Search - Console Logs', async ({ page }) => {
  // Capture all console messages
  const consoleLogs: string[] = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleLogs.push(`[${msg.type()}] ${text}`);
    console.log(`BROWSER: [${msg.type()}] ${text}`);
  });

  // Capture network requests
  page.on('request', request => {
    if (request.url().includes('/api/properties')) {
      console.log(`REQUEST: ${request.method()} ${request.url()}`);
    }
  });

  page.on('response', async response => {
    if (response.url().includes('/api/properties')) {
      console.log(`RESPONSE: ${response.status()} ${response.url()}`);
      try {
        const body = await response.json();
        console.log(`RESPONSE BODY:`, JSON.stringify(body).substring(0, 200));
      } catch(e) {
        // Not JSON
      }
    }
  });

  console.log('\\n=== Starting Debug Test ===\\n');

  // Navigate
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });
  await page.waitForTimeout(2000);
  console.log('✓ Page loaded');

  // Open Advanced Filters
  const advancedButton = page.locator('button:has-text("Advanced Filters")');
  await advancedButton.click();
  await page.waitForTimeout(1000);
  console.log('✓ Advanced Filters opened');

  // Fill filters
  const minSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
  await minSection.getByRole('textbox').fill('10000');
  console.log('✓ Filled min: 10000');

  const maxSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
  await maxSection.getByRole('textbox').fill('20000');
  console.log('✓ Filled max: 20000');

  await page.screenshot({ path: 'debug-1-before-search.png' });

  // Click Apply Filters
  console.log('\\n=== Clicking Apply Filters ===\\n');
  const applyButton = page.locator('button:has-text("Apply Filters")');
  await applyButton.click();

  // Wait and observe
  await page.waitForTimeout(6000);
  console.log('\\n=== 6 seconds after click ===\\n');

  await page.screenshot({ path: 'debug-2-after-search.png', fullPage: true });

  // Check what's on screen
  const bodyText = await page.textContent('body');

  const propertyCountMatch = bodyText?.match(/(\\d{1,3}(?:,\\d{3})*) Properties/);
  if (propertyCountMatch) {
    console.log(`\\nProperty Count Displayed: ${propertyCountMatch[1]}`);
  }

  const propertyCards = page.locator('[class*="MiniPropertyCard"], [class*="property-card"]');
  const cardCount = await propertyCards.count();
  console.log(`Property Cards Found: ${cardCount}`);

  // Check URL
  console.log(`Final URL: ${page.url()}`);

  // Print console logs summary
  console.log('\\n=== Console Logs Summary ===');
  const searchRelatedLogs = consoleLogs.filter(log =>
    log.includes('searchProperties') ||
    log.includes('Fast pipeline') ||
    log.includes('Fetching from') ||
    log.includes('API response')
  );

  if (searchRelatedLogs.length > 0) {
    console.log('Search-related logs found:');
    searchRelatedLogs.forEach(log => console.log(`  ${log}`));
  } else {
    console.log('⚠️  NO search-related console logs found!');
  }

  console.log('\\n=== Test Complete ===');
});
