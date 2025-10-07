import { test, expect } from '@playwright/test';

test('Quick Building SqFt Filter Test', async ({ page }) => {
  // Navigate to properties page
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });

  // Wait for page load
  await page.waitForTimeout(3000);

  console.log('Page loaded, looking for Advanced Filters button');

  // Click Advanced Filters button
  const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
  await advancedFiltersButton.click();

  console.log('Clicked Advanced Filters');
  await page.waitForTimeout(1000);

  // Find and fill Min Building SqFt input (by finding the label and then the input)
  const minBuildingSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
  const minInput = minBuildingSection.getByRole('textbox');
  await minInput.clear();
  await minInput.fill('10000');

  console.log('Filled min sqft: 10000');

  // Find and fill Max Building SqFt input (by finding the label and then the input)
  const maxBuildingSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
  const maxInput = maxBuildingSection.getByRole('textbox');
  await maxInput.clear();
  await maxInput.fill('20000');

  console.log('Filled max sqft: 20000');

  // Click Search button
  const searchButton = page.locator('button:has-text("Search")').or(page.locator('button:has-text("Apply")')).first();
  await searchButton.click();

  console.log('Clicked Search button');

  // Wait for results
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({ path: 'sqft-filter-quick-test.png', fullPage: true });

  console.log('✅ Test completed - screenshot saved');
});
