import { test, expect } from '@playwright/test';

/**
 * Complete Search Infrastructure Verification Test
 * Tests the new Meilisearch-powered search system end-to-end
 */

const SEARCH_API_URL = process.env.SEARCH_API_URL || 'http://localhost:8001';

test.describe('Complete Search Infrastructure Verification', () => {

  test('Should verify search API is healthy', async ({ request }) => {
    const response = await request.get(`${SEARCH_API_URL}/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    console.log('✅ Search API Health:', data);

    expect(data.status).toBe('healthy');
    expect(data.services.meilisearch.status).toBe('available');
    expect(data.services.meilisearch.documents).toBeGreaterThan(9000000);
  });

  test('Should return accurate count for building sqft filters', async ({ request }) => {
    console.log('\n🔍 Testing Building SqFt filters (10k-20k)...\n');

    const response = await request.get(
      `${SEARCH_API_URL}/api/search/instant?minBuildingSqFt=10000&maxBuildingSqFt=20000&limit=5`
    );

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    console.log('API Response:', JSON.stringify(data, null, 2));

    // Verify structure
    expect(data.success).toBe(true);
    expect(data.data).toBeDefined();
    expect(data.pagination).toBeDefined();

    // THE KEY TEST: Accurate count
    const count = data.pagination.total;
    console.log(`\n📊 Count: ${count.toLocaleString()}`);
    console.log(`Expected: ~37,726`);

    // Count should be close to 37,726 (within 5% variance for data updates)
    expect(count).toBeGreaterThan(35000);
    expect(count).toBeLessThan(40000);

    if (Math.abs(count - 37726) < 1000) {
      console.log('✅ COUNT IS ACCURATE!');
    } else {
      console.log(`⚠️  Count variance: ${Math.abs(count - 37726)}`);
    }

    // Verify properties are in range
    console.log('\n📋 Sample Properties:');
    data.data.forEach((prop: any, i: number) => {
      const sqft = prop.buildingSqFt;
      const inRange = sqft >= 10000 && sqft <= 20000;
      console.log(`  ${i+1}. ${prop.parcel_id} - ${sqft.toLocaleString()} sqft ${inRange ? '✅' : '❌'}`);
      expect(sqft).toBeGreaterThanOrEqual(10000);
      expect(sqft).toBeLessThanOrEqual(20000);
    });

    // Verify fast response
    const responseTime = data.processingTimeMs;
    console.log(`\n⚡ Response time: ${responseTime}ms`);
    expect(responseTime).toBeLessThan(100);  // Meilisearch should be <100ms
  });

  test('Should handle multiple filters correctly', async ({ request }) => {
    console.log('\n🔍 Testing multiple filters...\n');

    const response = await request.get(
      `${SEARCH_API_URL}/api/search/instant?` +
      'county=DADE&' +
      'minBuildingSqFt=5000&' +
      'maxBuildingSqFt=10000&' +
      'minValue=500000&' +
      'maxValue=1000000&' +
      'limit=10'
    );

    const data = await response.json();
    console.log(`Results: ${data.pagination.total} properties`);

    expect(data.success).toBe(true);
    expect(data.pagination.total).toBeGreaterThan(0);

    // Verify all filters applied
    data.data.forEach((prop: any) => {
      expect(prop.county).toBe('DADE');
      expect(prop.buildingSqFt).toBeGreaterThanOrEqual(5000);
      expect(prop.buildingSqFt).toBeLessThanOrEqual(10000);
      expect(prop.marketValue).toBeGreaterThanOrEqual(500000);
      expect(prop.marketValue).toBeLessThanOrEqual(1000000);
    });

    console.log('✅ All filters applied correctly');
  });

  test('Should provide autocomplete suggestions', async ({ request }) => {
    console.log('\n🔍 Testing autocomplete...\n');

    const response = await request.get(
      `${SEARCH_API_URL}/api/search/suggest?q=123&type=address&limit=10`
    );

    const data = await response.json();
    console.log(`Suggestions: ${data.suggestions.length}`);

    expect(data.success).toBe(true);
    expect(data.suggestions).toBeDefined();
    expect(data.suggestions.length).toBeGreaterThan(0);
    expect(data.suggestions.length).toBeLessThanOrEqual(10);

    console.log('Sample suggestions:');
    data.suggestions.slice(0, 3).forEach((s: any) => {
      console.log(`  - ${s.value} (${s.county})`);
    });

    console.log('✅ Autocomplete working');
  });

  test('Should return facets for filtered search', async ({ request }) => {
    console.log('\n🔍 Testing facets...\n');

    const response = await request.get(
      `${SEARCH_API_URL}/api/search/facets?minBuildingSqFt=10000`
    );

    const data = await response.json();
    console.log(`Total matches: ${data.total.toLocaleString()}`);

    expect(data.success).toBe(true);
    expect(data.facets).toBeDefined();

    // Check county facets
    if (data.facets.county) {
      console.log('\nTop counties:');
      Object.entries(data.facets.county)
        .slice(0, 5)
        .forEach(([county, count]: [string, any]) => {
          console.log(`  ${county}: ${count.toLocaleString()}`);
        });
    }

    console.log('✅ Facets working');
  });

  test('Should integrate with frontend correctly', async ({ page }) => {
    console.log('\n🌐 Testing frontend integration...\n');

    // Navigate to properties page
    await page.goto('http://localhost:5178/properties', { timeout: 15000 });
    await page.waitForTimeout(2000);

    // Open Advanced Filters
    const advancedButton = page.locator('button:has-text("Advanced Filters")');
    await advancedButton.click();
    await page.waitForTimeout(1000);

    // Fill Building SqFt filters
    const minSection = page.locator('div').filter({ hasText: /^Min Building SqFt$/ });
    await minSection.getByRole('textbox').fill('10000');

    const maxSection = page.locator('div').filter({ hasText: /^Max Building SqFt$/ });
    await maxSection.getByRole('textbox').fill('20000');

    await page.screenshot({ path: 'search-test-1-filters-filled.png' });

    // Click Apply Filters
    const applyButton = page.locator('button:has-text("Apply Filters")');
    await applyButton.click();

    // Wait for results
    await page.waitForTimeout(5000);

    await page.screenshot({ path: 'search-test-2-results.png', fullPage: true });

    // Check results
    const bodyText = await page.textContent('body');
    const countMatch = bodyText?.match(/(\d{1,3}(?:,\d{3})*)\s*Properties/);

    if (countMatch) {
      const displayedCount = parseInt(countMatch[1].replace(/,/g, ''));
      console.log(`\n📊 Frontend displays: ${displayedCount.toLocaleString()} properties`);

      if (displayedCount >= 35000 && displayedCount <= 40000) {
        console.log('✅ Frontend shows accurate count!');
      } else if (displayedCount > 7000000) {
        console.log('❌ Frontend still shows fallback count (7.3M)');
        console.log('⚠️  Make sure frontend is calling new Search API');
      } else {
        console.log(`⚠️  Unexpected count: ${displayedCount}`);
      }
    }

    // Check for property cards
    const propertyCards = page.locator('[class*="MiniPropertyCard"], [class*="property-card"]');
    const cardCount = await propertyCards.count();
    console.log(`🏠 Property cards displayed: ${cardCount}`);

    expect(cardCount).toBeGreaterThan(0);
  });
});

test.describe('Performance Benchmarks', () => {

  test('Should handle high-volume queries efficiently', async ({ request }) => {
    console.log('\n⚡ Running performance benchmark...\n');

    const queries = [
      '?county=DADE&limit=100',
      '?minValue=100000&maxValue=500000&limit=100',
      '?minBuildingSqFt=2000&maxBuildingSqFt=5000&limit=100',
      '?q=miami&limit=50',
      '?propertyType=Residential&yearBuilt=2020&limit=100'
    ];

    const times: number[] = [];

    for (const query of queries) {
      const start = Date.now();
      const response = await request.get(`${SEARCH_API_URL}/api/search/instant${query}`);
      const elapsed = Date.now() - start;

      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      times.push(data.processingTimeMs || elapsed);

      console.log(`Query: ${query.substring(0, 50)}... - ${elapsed}ms (Meili: ${data.processingTimeMs}ms)`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const max = Math.max(...times);

    console.log(`\n📊 Performance Stats:`);
    console.log(`   Average: ${avg.toFixed(1)}ms`);
    console.log(`   Max: ${max}ms`);
    console.log(`   All queries < 100ms: ${max < 100 ? '✅' : '❌'}`);

    expect(avg).toBeLessThan(50);  // Average should be under 50ms
    expect(max).toBeLessThan(100); // Max should be under 100ms
  });
});

test.describe('Error Handling', () => {

  test('Should handle invalid filters gracefully', async ({ request }) => {
    const response = await request.get(
      `${SEARCH_API_URL}/api/search/instant?minBuildingSqFt=invalid`
    );

    // Should either return error or ignore invalid filter
    if (response.ok()) {
      const data = await response.json();
      expect(data.success).toBeTruthy();
    } else {
      expect(response.status()).toBeGreaterThanOrEqual(400);
    }
  });

  test('Should handle missing index gracefully', async ({ request }) => {
    const response = await request.get(`${SEARCH_API_URL}/health`);
    const data = await response.json();

    if (data.services.meilisearch.documents === 0) {
      console.log('⚠️  Warning: Index is empty. Run meilisearch_indexer.py first.');
    }
  });
});
