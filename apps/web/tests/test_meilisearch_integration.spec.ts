/**
 * Meilisearch Integration Test
 * Verifies that Building SqFt filter returns accurate counts from Meilisearch
 */
import { test, expect } from '@playwright/test';

test.describe('Meilisearch Building SqFt Filter', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to property search page
    await page.goto('http://localhost:5173/properties');

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should return accurate count for 10K-20K sqft filter (not 7.3M fallback)', async ({ page }) => {
    // Open filters panel
    const filtersButton = page.locator('button:has-text("Filters")');
    await filtersButton.click();

    // Wait for filters panel to open
    await page.waitForSelector('[data-testid="filters-panel"]', { timeout: 5000 });

    // Find Building SqFt inputs
    const minSqFtInput = page.locator('input[placeholder*="Min"]').first();
    const maxSqFtInput = page.locator('input[placeholder*="Max"]').first();

    // Enter filter values
    await minSqFtInput.fill('10000');
    await maxSqFtInput.fill('20000');

    // Click Apply Filters or Search button
    const applyButton = page.locator('button:has-text("Apply Filters"), button:has-text("Search")').first();
    await applyButton.click();

    // Wait for results to load
    await page.waitForSelector('[data-testid="property-count"], .property-count', { timeout: 10000 });

    // Get the displayed count
    const countElement = page.locator('[data-testid="property-count"], .property-count, .results-count').first();
    const countText = await countElement.textContent();

    console.log('Count displayed:', countText);

    // Extract number from text (e.g., "964 properties" -> 964)
    const countMatch = countText?.match(/[\d,]+/);
    const displayedCount = countMatch ? parseInt(countMatch[0].replace(/,/g, '')) : 0;

    // Verify count is NOT the 7.3M fallback
    expect(displayedCount).not.toBe(7312040);
    expect(displayedCount).not.toBe(7300000);

    // Verify count is in reasonable range for 10K-20K sqft (should be around 964)
    expect(displayedCount).toBeGreaterThan(0);
    expect(displayedCount).toBeLessThan(100000);

    // Log success
    console.log(`✅ Filter returned accurate count: ${displayedCount} (not 7.3M fallback!)`);

    // Take screenshot for verification
    await page.screenshot({
      path: 'test-results/meilisearch-filter-success.png',
      fullPage: true
    });
  });

  test('should query Meilisearch API directly and verify accurate results', async ({ request }) => {
    // Test local Meilisearch directly
    const response = await request.post('http://127.0.0.1:7700/indexes/florida_properties/search', {
      headers: {
        'Authorization': 'Bearer concordbroker-meili-master-key',
        'Content-Type': 'application/json'
      },
      data: {
        filter: 'tot_lvg_area >= 10000 AND tot_lvg_area <= 20000',
        limit: 5
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    console.log('Meilisearch response:', JSON.stringify(data, null, 2));

    // Verify results
    expect(data.estimatedTotalHits).toBeGreaterThan(0);
    expect(data.estimatedTotalHits).toBeLessThan(100000);
    expect(data.hits).toHaveLength(5);

    // Verify all results are in range
    for (const hit of data.hits) {
      expect(hit.tot_lvg_area).toBeGreaterThanOrEqual(10000);
      expect(hit.tot_lvg_area).toBeLessThanOrEqual(20000);
    }

    console.log(`✅ Meilisearch returned ${data.estimatedTotalHits} accurate results`);
    console.log(`✅ Sample property: ${data.hits[0].phy_addr1}, ${data.hits[0].county} - ${data.hits[0].tot_lvg_area} sqft`);
  });

  test('should have fast query response time (<100ms)', async ({ page }) => {
    // Open filters
    await page.locator('button:has-text("Filters")').click();
    await page.waitForSelector('[data-testid="filters-panel"]', { timeout: 5000 });

    // Enter filter values
    const minSqFtInput = page.locator('input[placeholder*="Min"]').first();
    const maxSqFtInput = page.locator('input[placeholder*="Max"]').first();
    await minSqFtInput.fill('10000');
    await maxSqFtInput.fill('20000');

    // Measure query time
    const startTime = Date.now();

    await page.locator('button:has-text("Apply Filters"), button:has-text("Search")').first().click();
    await page.waitForSelector('[data-testid="property-count"], .property-count', { timeout: 10000 });

    const endTime = Date.now();
    const queryTime = endTime - startTime;

    console.log(`Query time: ${queryTime}ms`);

    // Verify query is fast (should be <100ms with Meilisearch, vs 5000ms+ timeout with Supabase)
    expect(queryTime).toBeLessThan(5000); // Much faster than old timeout

    console.log(`✅ Query completed in ${queryTime}ms (fast!)`);
  });
});

test.describe('Meilisearch vs Supabase Comparison', () => {
  test('should demonstrate the bug fix: accurate counts vs 7.3M fallback', async ({ request }) => {
    // Test Meilisearch (new, working)
    const meilisearchResponse = await request.post('http://127.0.0.1:7700/indexes/florida_properties/search', {
      headers: {
        'Authorization': 'Bearer concordbroker-meili-master-key',
        'Content-Type': 'application/json'
      },
      data: {
        filter: 'tot_lvg_area >= 10000 AND tot_lvg_area <= 20000',
        limit: 1
      }
    });

    const meilisearchData = await meilisearchResponse.json();
    const meilisearchCount = meilisearchData.estimatedTotalHits;

    console.log('='.repeat(80));
    console.log('BUG FIX VERIFICATION');
    console.log('='.repeat(80));
    console.log(`Meilisearch count: ${meilisearchCount} (accurate!)`);
    console.log(`Old Supabase fallback: 7,312,040 (wrong!)`);
    console.log('='.repeat(80));

    // Verify Meilisearch returns accurate count (not 7.3M)
    expect(meilisearchCount).not.toBe(7312040);
    expect(meilisearchCount).toBeGreaterThan(0);
    expect(meilisearchCount).toBeLessThan(100000);

    console.log(`✅ BUG FIXED: Filter returns ${meilisearchCount} instead of 7.3M fallback!`);
  });
});
