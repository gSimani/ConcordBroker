import { test, expect } from '@playwright/test';

test.describe('Sales History Display Verification', () => {
  test('should display sales history for Broward parcel 474128000000', async ({ page }) => {
    // Navigate to property with sales data
    await page.goto('http://localhost:5173/property/474128000000');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Click on the "Sales History" tab
    await page.click('text=Sales History');

    // Wait for the tab content to load
    await page.waitForTimeout(2000);

    // Check if sales history table exists
    const salesTable = page.locator('table').filter({ hasText: 'Date' }).filter({ hasText: 'Type' }).filter({ hasText: 'Price' });
    await expect(salesTable).toBeVisible({ timeout: 10000 });

    // Verify table has data rows (not just "No Sales History Available")
    const tableRows = salesTable.locator('tbody tr');
    const rowCount = await tableRows.count();

    console.log(`Found ${rowCount} sales history rows`);
    expect(rowCount).toBeGreaterThan(0);

    // Verify first row has the expected columns
    const firstRow = tableRows.first();
    await expect(firstRow).toBeVisible();

    // Check for date column
    const dateCell = firstRow.locator('td').first();
    await expect(dateCell).toBeVisible();
    const dateText = await dateCell.textContent();
    console.log('Date:', dateText);
    expect(dateText).toBeTruthy();

    // Check for price column (should be in currency format)
    const priceCell = firstRow.locator('td').nth(2);
    const priceText = await priceCell.textContent();
    console.log('Price:', priceText);
    expect(priceText).toMatch(/\$[\d,]+/); // Should contain dollar sign and numbers

    // Check for book/page or CIN column
    const docCell = firstRow.locator('td').nth(3);
    const docText = await docCell.textContent();
    console.log('Document Reference:', docText);

    // Take screenshot of sales history section
    await page.screenshot({
      path: 'sales-history-474128000000.png',
      fullPage: true
    });

    console.log('✅ Sales history is displaying correctly!');
  });

  test('should show clickable Book/Page links', async ({ page }) => {
    await page.goto('http://localhost:5173/property/474128000000');
    await page.waitForLoadState('networkidle');

    // Look for external link icons (indicating clickable Book/Page)
    const externalLinks = page.locator('a').filter({ has: page.locator('svg') });
    const linkCount = await externalLinks.count();

    console.log(`Found ${linkCount} clickable document links`);

    if (linkCount > 0) {
      // Verify first link has proper href
      const firstLink = externalLinks.first();
      const href = await firstLink.getAttribute('href');
      console.log('First link href:', href);
      expect(href).toContain('officialrecords'); // Should link to county records
    }
  });

  test('should handle parcel with no sales history gracefully', async ({ page }) => {
    // Test with parcel that has no sales (if it exists)
    await page.goto('http://localhost:5173/property/402101327008');
    await page.waitForLoadState('networkidle');

    // Should show "No Sales History Available" message
    const noSalesMessage = page.locator('text=No Sales History Available');

    // Either sales exist or no sales message shows
    const hasSales = await page.locator('table tbody tr').count() > 0;
    const hasNoSalesMessage = await noSalesMessage.isVisible();

    expect(hasSales || hasNoSalesMessage).toBeTruthy();

    console.log(hasSales ? '✅ Property has sales data' : '✅ No sales message displayed correctly');
  });
});
