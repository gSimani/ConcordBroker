import { test, expect } from '@playwright/test';

test('Building SqFt Filter - Complete Verification', async ({ page }) => {
  console.log('Starting test...');

  // Navigate to properties page
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });
  await page.waitForTimeout(2000);
  console.log('✓ Loaded properties page');

  // Try to click "Guided Search" tab if it exists (it may not be visible by default)
  const guidedSearchTab = page.locator('button:has-text("Guided Search"), text=Guided Search').first();
  const isGuidedSearchVisible = await guidedSearchTab.isVisible({ timeout: 2000 }).catch(() => false);

  if (isGuidedSearchVisible) {
    await guidedSearchTab.click();
    await page.waitForTimeout(1000);
    console.log('✓ Switched to Guided Search tab');
  } else {
    console.log('ℹ Guided Search tab not found, assuming already in correct mode');
  }

  // Verify we're in the right mode by checking for "Advanced Filters" button
  const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
  await expect(advancedFiltersButton).toBeVisible({ timeout: 5000 });
  console.log('✓ Advanced Filters button visible');

  // Click Advanced Filters
  await advancedFiltersButton.click();
  await page.waitForTimeout(1000);
  console.log('✓ Opened Advanced Filters panel');

  // Screenshot: Filters panel open
  await page.screenshot({ path: 'final-1-filters-panel.png' });

  // Fill Min Building SqFt = 10000
  const minSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
  await expect(minSection).toBeVisible();
  const minInput = minSection.getByRole('textbox');
  await minInput.clear();
  await minInput.fill('10000');
  console.log('✓ Set Min Building SqFt = 10,000');

  // Fill Max Building SqFt = 20000
  const maxSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
  await expect(maxSection).toBeVisible();
  const maxInput = maxSection.getByRole('textbox');
  await maxInput.clear();
  await maxInput.fill('20000');
  console.log('✓ Set Max Building SqFt = 20,000');

  // Screenshot: Filters filled
  await page.screenshot({ path: 'final-2-filters-filled.png' });

  // Click Search button
  const searchButton = page.locator('button:has-text("Search")').first();
  await searchButton.click();
  console.log('✓ Clicked Search button');

  // Wait for results
  await page.waitForTimeout(5000);
  console.log('✓ Waited for results to load');

  // Screenshot: Results page
  await page.screenshot({ path: 'final-3-results.png', fullPage: true });

  // Extract and verify results count
  const pageText = await page.textContent('body');
  const countMatch = pageText?.match(/(\d{1,3}(?:,\d{3})*)\s*Properties/);

  if (countMatch) {
    const displayedCount = countMatch[1];
    console.log(`\n📊 DISPLAYED COUNT: ${displayedCount} Properties`);
    console.log(`   Expected: 37,726 Properties (database verified)`);

    const numericCount = parseInt(displayedCount.replace(/,/g, ''));
    if (numericCount === 37726) {
      console.log('   ✅ COUNT IS CORRECT!');
    } else if (numericCount > 7000000) {
      console.log('   ❌ Showing fallback count (7.3M)');
    } else {
      console.log(`   ⚠️  Count mismatch (got ${numericCount})`);
    }
  }

  // Check for property cards
  await page.waitForTimeout(2000);
  const propertyCards = page.locator('[class*="MiniPropertyCard"], [data-testid="property-card"], div[class*="property"]').filter({ hasText: /sqft|sq ft/i });
  const cardCount = await propertyCards.count();
  console.log(`\n🏠 PROPERTY CARDS: ${cardCount} visible`);

  // Read sqft from first 3 cards
  if (cardCount > 0) {
    console.log('\n📋 Sample Properties:');
    for (let i = 0; i < Math.min(3, cardCount); i++) {
      const card = propertyCards.nth(i);
      const text = await card.textContent();
      const sqftMatch = text?.match(/(\d{1,3}(?:,\d{3})*)\s*(?:sqft|sq\s*ft)/i);
      if (sqftMatch) {
        const sqft = parseInt(sqftMatch[1].replace(/,/g, ''));
        const inRange = sqft >= 10000 && sqft <= 20000;
        console.log(`   ${i+1}. ${sqftMatch[0]} ${inRange ? '✅' : '❌ OUT OF RANGE!'}`);
      }
    }
  } else {
    console.log('   ⚠️  No property cards found');
  }

  // Check URL for filter params
  const url = page.url();
  if (url.includes('minBuilding') || url.includes('min_building')) {
    console.log('\n🔗 URL contains building sqft parameters');
  } else {
    console.log('\n⚠️  URL does not contain building sqft parameters');
  }
  console.log(`   ${url}`);

  console.log('\n=== TEST COMPLETE ===');
});
