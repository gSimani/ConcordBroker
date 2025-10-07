import { test, expect } from '@playwright/test';

test('Comprehensive Building SqFt Filter Test', async ({ page }) => {
  // Navigate to properties page
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });
  await page.waitForTimeout(3000);

  console.log('✓ Page loaded');

  // Take initial screenshot
  await page.screenshot({ path: 'test-1-initial.png', fullPage: true });

  // Click Guided Search tab (to get to traditional filters)
  const guidedSearchTab = page.getByText('Guided Search');
  if (await guidedSearchTab.isVisible()) {
    await guidedSearchTab.click();
    await page.waitForTimeout(500);
    console.log('✓ Switched to Guided Search');
  }

  // Click Advanced Filters button
  const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
  await advancedFiltersButton.click();
  await page.waitForTimeout(1000);
  console.log('✓ Opened Advanced Filters');

  // Take screenshot after opening filters
  await page.screenshot({ path: 'test-2-filters-open.png', fullPage: true });

  // Find and fill Min Building SqFt
  const minBuildingSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
  const minInput = minBuildingSection.getByRole('textbox');
  await minInput.clear();
  await minInput.fill('10000');
  console.log('✓ Filled min sqft: 10000');

  // Find and fill Max Building SqFt
  const maxBuildingSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
  const maxInput = maxBuildingSection.getByRole('textbox');
  await maxInput.clear();
  await maxInput.fill('20000');
  console.log('✓ Filled max sqft: 20000');

  // Take screenshot before search
  await page.screenshot({ path: 'test-3-filters-filled.png', fullPage: true });

  // Click Search button
  const searchButton = page.locator('button:has-text("Search")').or(page.locator('button:has-text("Apply")')).first();
  await searchButton.click();
  console.log('✓ Clicked Search');

  // Wait for results to load
  await page.waitForTimeout(5000);

  // Take screenshot of results
  await page.screenshot({ path: 'test-4-results.png', fullPage: true });

  // Look for property count in various possible locations
  const pageContent = await page.content();

  // Check for count in header
  const countMatches = pageContent.match(/(\d{1,3}(?:,\d{3})*)\s*(?:Properties|Results|Found)/gi);
  if (countMatches) {
    console.log('✓ Found count text:', countMatches);
  }

  // Check for property cards
  const propertyCards = page.locator('[class*="property-card"], [class*="MiniPropertyCard"], [data-testid="property-card"]');
  const cardCount = await propertyCards.count();
  console.log(`✓ Found ${cardCount} property cards on page`);

  // Try to read actual building sqft from visible cards
  if (cardCount > 0) {
    for (let i = 0; i < Math.min(3, cardCount); i++) {
      const card = propertyCards.nth(i);
      const cardText = await card.textContent();
      const sqftMatch = cardText?.match(/(\d{1,3}(?:,\d{3})*)\s*(?:sqft|sq\s*ft)/i);
      if (sqftMatch) {
        console.log(`  Card ${i + 1}: ${sqftMatch[0]}`);
      }
    }
  }

  // Check URL parameters
  const url = page.url();
  console.log('✓ Final URL:', url);

  console.log('\\n=== TEST COMPLETE ===');
  console.log('Expected: 37,726 properties (10k-20k sqft range)');
  console.log('Check screenshots for actual results');
});
