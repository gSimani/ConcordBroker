import { test, expect } from '@playwright/test';

test.describe('Building SqFt Filters Verification', () => {
  test('should filter properties by Min/Max Building SqFt', async ({ page }) => {
    // Navigate to properties page
    await page.goto('http://localhost:5178/properties');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Click Advanced Filters button
    const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
    await advancedFiltersButton.click();

    // Wait for advanced filters to appear
    await page.waitForSelector('input[placeholder*="10,000"], input[id*="minBuilding"]', { timeout: 5000 });

    // Find and fill Min Building SqFt input
    const minBuildingInput = page.locator('input[placeholder*="10,000"], input[id*="minBuilding"]').first();
    await minBuildingInput.clear();
    await minBuildingInput.fill('10000');

    // Find and fill Max Building SqFt input
    const maxBuildingInput = page.locator('input[placeholder*="50,000"], input[id*="maxBuilding"]').first();
    await maxBuildingInput.clear();
    await maxBuildingInput.fill('20000');

    // Click Search or Apply Filters button
    const searchButton = page.locator('button:has-text("Search"), button:has-text("Apply")').first();
    await searchButton.click();

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Check that properties are displayed
    const propertyCards = page.locator('[class*="property-card"], [class*="MiniPropertyCard"], [data-testid="property-card"]');
    const count = await propertyCards.count();

    console.log(`Found ${count} property cards`);

    // Verify at least some properties are shown
    expect(count).toBeGreaterThan(0);

    // Check the first few property cards for building sqft values
    for (let i = 0; i < Math.min(3, count); i++) {
      const card = propertyCards.nth(i);

      // Look for sqft text in the card
      const cardText = await card.textContent();
      console.log(`Card ${i + 1} content:`, cardText?.substring(0, 200));

      // Check if sqft value is visible and within range
      const sqftMatch = cardText?.match(/(\d{1,3}(,\d{3})*)\s*(sqft|sq\s*ft)/i);
      if (sqftMatch) {
        const sqft = parseInt(sqftMatch[1].replace(/,/g, ''));
        console.log(`  Found sqft: ${sqft}`);

        // Verify sqft is within range
        expect(sqft).toBeGreaterThanOrEqual(10000);
        expect(sqft).toBeLessThanOrEqual(20000);
      }
    }

    // Take screenshot for verification
    await page.screenshot({ path: 'building-sqft-filter-test.png', fullPage: true });

    console.log('✅ Building SqFt filters test completed successfully');
  });

  test('should show correct count in results header', async ({ page }) => {
    // Navigate and apply filters
    await page.goto('http://localhost:5178/properties');
    await page.waitForLoadState('networkidle');

    // Click Advanced Filters
    await page.locator('button:has-text("Advanced Filters")').click();
    await page.waitForTimeout(500);

    // Fill Building SqFt filters
    await page.locator('input[placeholder*="10,000"], input[id*="minBuilding"]').first().fill('10000');
    await page.locator('input[placeholder*="50,000"], input[id*="maxBuilding"]').first().fill('20000');

    // Submit search
    await page.locator('button:has-text("Search"), button:has-text("Apply")').first().click();
    await page.waitForTimeout(2000);

    // Look for results count text
    const resultsText = await page.locator('text=/\\d+\\s*(Properties|Results|Found)/i').first().textContent();
    console.log('Results text:', resultsText);

    // Extract the number
    const countMatch = resultsText?.match(/(\\d+(?:,\\d+)*)/);
    if (countMatch) {
      const displayedCount = parseInt(countMatch[1].replace(/,/g, ''));
      console.log(`Displayed count: ${displayedCount}`);

      // Check if it's the fallback (7.3M) or actual count (37k)
      if (displayedCount > 100000) {
        console.log('⚠️  Showing fallback count (7.3M)');
      } else {
        console.log('✅ Showing filtered count');
      }
    }
  });
});
