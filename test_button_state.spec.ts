import { test, expect } from '@playwright/test';

test('Check Apply Filters button state and handler', async ({ page }) => {
  console.log('Testing button state...');

  // Navigate
  await page.goto('http://localhost:5178/properties', { timeout: 15000 });
  await page.waitForTimeout(2000);

  // Open Advanced Filters
  const advancedButton = page.locator('button:has-text("Advanced Filters")');
  await advancedButton.click();
  await page.waitForTimeout(1000);

  // Check if Apply Filters button exists
  const applyButton = page.locator('button:has-text("Apply Filters")');
  const isVisible = await applyButton.isVisible();
  console.log(`Apply Filters button visible: ${isVisible}`);

  if (isVisible) {
    const isEnabled = await applyButton.isEnabled();
    console.log(`Apply Filters button enabled: ${isEnabled}`);

    const buttonText = await applyButton.textContent();
    console.log(`Button text: "${buttonText}"`);

    // Get button attributes
    const classList = await applyButton.getAttribute('class');
    console.log(`Button classes: ${classList}`);

    const disabled = await applyButton.getAttribute('disabled');
    console.log(`Disabled attribute: ${disabled}`);
  }

  // Also check for other possible buttons
  const searchButton = page.locator('button:has-text("Search")');
  const searchExists = await searchButton.count();
  console.log(`\\nButtons with "Search": ${searchExists}`);

  const applyButtons = page.locator('button:has-text("Apply")');
  const applyCount = await applyButtons.count();
  console.log(`Buttons with "Apply": ${applyCount}`);

  // Take screenshot of filter panel
  await page.screenshot({ path: 'button-state.png' });
});
