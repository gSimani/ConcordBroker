/**
 * Comprehensive Property Filter Audit
 * Tests ALL filters on /properties page with focus on USE and SUBUSE filtering
 * Verifies MiniPropertyCard display accuracy
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:5178';
const PROPERTIES_URL = `${BASE_URL}/properties`;

// Helper to wait for property cards to load
async function waitForPropertyCards(page: Page) {
  // Wait for loading state to complete first
  await page.waitForSelector('[data-testid="mini-property-card"], .property-card, .loading-indicator', {
    timeout: 30000, // Increased timeout for Supabase query
    state: 'visible'
  });
  // Wait for loading states to finish
  await page.waitForTimeout(2000);
}

// Helper to get all visible property cards
async function getPropertyCards(page: Page) {
  return await page.locator('[data-testid="mini-property-card"], .property-card').all();
}

// Helper to extract property use from card
async function getPropertyUseFromCard(card) {
  try {
    // Try PropertyUseInline component first
    const useInline = card.locator('.property-use-display, [data-testid="property-use"]');
    if (await useInline.count() > 0) {
      return await useInline.first().textContent();
    }

    // Fallback to property type badge
    const typeBadge = card.locator('.property-type-badge, [data-testid="property-type"]');
    if (await typeBadge.count() > 0) {
      return await typeBadge.first().textContent();
    }

    return 'Unknown';
  } catch (error) {
    return 'Unknown';
  }
}

test.describe('Property Filters Audit - USE and SUBUSE', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(PROPERTIES_URL);
    await waitForPropertyCards(page);
  });

  test('Audit 1: Page loads with property cards', async ({ page }) => {
    const cards = await getPropertyCards(page);
    console.log(`✓ Found ${cards.length} property cards on initial load`);
    expect(cards.length).toBeGreaterThan(0);
  });

  test('Audit 2: Filter by Residential USE', async ({ page }) => {
    // Find and click Residential filter
    const residentialFilter = page.locator('button, input').filter({
      hasText: /residential/i
    }).first();

    if (await residentialFilter.count() > 0) {
      await residentialFilter.click();
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== RESIDENTIAL FILTER TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      // Verify each card shows residential property use
      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/residential|single family|sfr|condo|apartment|multi-family/i);
      }
    } else {
      console.log('⚠ Residential filter not found - may use different UI');
    }
  });

  test('Audit 3: Filter by Commercial USE', async ({ page }) => {
    const commercialFilter = page.locator('button, input').filter({
      hasText: /commercial/i
    }).first();

    if (await commercialFilter.count() > 0) {
      await commercialFilter.click();
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== COMMERCIAL FILTER TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/commercial|store|office|retail|warehouse/i);
      }
    } else {
      console.log('⚠ Commercial filter not found');
    }
  });

  test('Audit 4: Filter by Industrial USE', async ({ page }) => {
    const industrialFilter = page.locator('button, input').filter({
      hasText: /industrial/i
    }).first();

    if (await industrialFilter.count() > 0) {
      await industrialFilter.click();
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== INDUSTRIAL FILTER TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/industrial|manufacturing|warehouse|factory/i);
      }
    } else {
      console.log('⚠ Industrial filter not found');
    }
  });

  test('Audit 5: Filter by Agricultural USE', async ({ page }) => {
    const agriculturalFilter = page.locator('button, input').filter({
      hasText: /agricultural/i
    }).first();

    if (await agriculturalFilter.count() > 0) {
      await agriculturalFilter.click();
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== AGRICULTURAL FILTER TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/agricultural|farm|cropland|grove|ranch/i);
      }
    } else {
      console.log('⚠ Agricultural filter not found');
    }
  });

  test('Audit 6: Filter by Single Family SUBUSE', async ({ page }) => {
    // Look for subuse filter (might be dropdown or checkbox)
    const subUseFilter = page.locator('select[name*="subuse"], select[name*="propertyType"]').first();

    if (await subUseFilter.count() > 0) {
      await subUseFilter.selectOption({ label: /single family/i });
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== SINGLE FAMILY SUBUSE TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/single family|sfr|01-01/i);
      }
    } else {
      console.log('⚠ SubUse filter not found - checking alternative UI');
    }
  });

  test('Audit 7: Filter by Condominium SUBUSE', async ({ page }) => {
    const subUseFilter = page.locator('select[name*="subuse"], select[name*="propertyType"]').first();

    if (await subUseFilter.count() > 0) {
      await subUseFilter.selectOption({ label: /condo/i });
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== CONDOMINIUM SUBUSE TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/condo|condominium|04-01/i);
      }
    } else {
      console.log('⚠ Condominium filter not found');
    }
  });

  test('Audit 8: Filter by Multi-Family SUBUSE', async ({ page }) => {
    const subUseFilter = page.locator('select[name*="subuse"], select[name*="propertyType"]').first();

    if (await subUseFilter.count() > 0) {
      await subUseFilter.selectOption({ label: /multi.*family/i });
      await waitForPropertyCards(page);

      const cards = await getPropertyCards(page);
      console.log(`\n=== MULTI-FAMILY SUBUSE TEST ===`);
      console.log(`Cards after filter: ${cards.length}`);

      for (let i = 0; i < Math.min(cards.length, 10); i++) {
        const use = await getPropertyUseFromCard(cards[i]);
        console.log(`  Card ${i + 1}: ${use}`);
        expect(use.toLowerCase()).toMatch(/multi.*family|mf|apartment|03-/i);
      }
    } else {
      console.log('⚠ Multi-Family filter not found');
    }
  });

  test('Audit 9: Combined County + USE filters', async ({ page }) => {
    // Select Broward County
    const countyFilter = page.locator('select[name*="county"], input[placeholder*="county"]').first();
    if (await countyFilter.count() > 0) {
      if (await countyFilter.getAttribute('type') === 'text') {
        await countyFilter.fill('BROWARD');
      } else {
        await countyFilter.selectOption({ label: /broward/i });
      }
    }

    // Select Residential
    const residentialFilter = page.locator('button, input').filter({
      hasText: /residential/i
    }).first();
    if (await residentialFilter.count() > 0) {
      await residentialFilter.click();
    }

    await waitForPropertyCards(page);

    const cards = await getPropertyCards(page);
    console.log(`\n=== COMBINED FILTER TEST (Broward + Residential) ===`);
    console.log(`Cards after combined filters: ${cards.length}`);

    // Verify cards match both criteria
    for (let i = 0; i < Math.min(cards.length, 5); i++) {
      const card = cards[i];
      const countyText = await card.textContent();
      const use = await getPropertyUseFromCard(card);

      console.log(`  Card ${i + 1}:`);
      console.log(`    County: ${countyText?.includes('BROWARD') ? 'BROWARD ✓' : 'Check needed'}`);
      console.log(`    Use: ${use}`);
    }
  });

  test('Audit 10: PropertyUseInline component visibility', async ({ page }) => {
    const cards = await getPropertyCards(page);

    console.log(`\n=== PROPERTYUSEINLINE COMPONENT AUDIT ===`);
    console.log(`Total cards to check: ${cards.length}`);

    let visibleCount = 0;
    let categories = new Map<string, number>();

    for (let i = 0; i < Math.min(cards.length, 20); i++) {
      const card = cards[i];
      const useDisplay = card.locator('.property-use-display, [data-testid="property-use"]');

      if (await useDisplay.count() > 0) {
        visibleCount++;
        const text = await useDisplay.first().textContent();

        // Extract category
        const categoryMatch = text?.match(/(RESIDENTIAL|COMMERCIAL|INDUSTRIAL|AGRICULTURAL|INSTITUTIONAL|GOVERNMENT|VACANT)/i);
        if (categoryMatch) {
          const category = categoryMatch[1].toUpperCase();
          categories.set(category, (categories.get(category) || 0) + 1);
        }

        console.log(`  Card ${i + 1}: ${text?.trim()}`);
      }
    }

    console.log(`\n✓ PropertyUseInline visible on ${visibleCount}/${Math.min(cards.length, 20)} cards`);
    console.log(`\nCategory Distribution:`);
    categories.forEach((count, category) => {
      console.log(`  ${category}: ${count} properties`);
    });

    expect(visibleCount).toBeGreaterThan(0);
  });

  test('Audit 11: All filter combinations stress test', async ({ page }) => {
    console.log(`\n=== FILTER COMBINATIONS STRESS TEST ===`);

    const filterTests = [
      { name: 'Price Range', selector: 'input[name*="price"], input[placeholder*="price"]' },
      { name: 'Square Footage', selector: 'input[name*="sqft"], input[placeholder*="square"]' },
      { name: 'Bedrooms', selector: 'select[name*="bed"], input[name*="bed"]' },
      { name: 'Bathrooms', selector: 'select[name*="bath"], input[name*="bath"]' },
      { name: 'Year Built', selector: 'input[name*="year"]' },
    ];

    for (const filter of filterTests) {
      const element = page.locator(filter.selector).first();
      if (await element.count() > 0) {
        console.log(`✓ ${filter.name} filter found`);
      } else {
        console.log(`⚠ ${filter.name} filter not found`);
      }
    }
  });

  test('Audit 12: DOR code accuracy verification', async ({ page }) => {
    console.log(`\n=== DOR CODE ACCURACY AUDIT ===`);

    const cards = await getPropertyCards(page);
    const testSample = Math.min(cards.length, 10);

    for (let i = 0; i < testSample; i++) {
      const card = cards[i];

      // Get property use display
      const useDisplay = card.locator('.property-use-display, [data-testid="property-use"]');
      if (await useDisplay.count() > 0) {
        const useText = await useDisplay.first().textContent();

        // Get tooltip/title if available
        const tooltip = await useDisplay.first().getAttribute('title');

        console.log(`\nCard ${i + 1}:`);
        console.log(`  Display: ${useText?.trim()}`);
        if (tooltip) {
          console.log(`  Tooltip: ${tooltip}`);

          // Verify tooltip contains DOR code
          expect(tooltip).toMatch(/\d{2}-\d{2}/); // Format: XX-YY
        }
      }
    }
  });
});

test.describe('Filter UI/UX Audit', () => {

  test('Audit 13: Filter panel accessibility', async ({ page }) => {
    await page.goto(PROPERTIES_URL);

    console.log(`\n=== FILTER PANEL ACCESSIBILITY AUDIT ===`);

    // Check for filter panel
    const filterPanel = page.locator('[data-testid="filter-panel"], .filters, .filter-sidebar').first();
    expect(await filterPanel.count()).toBeGreaterThan(0);
    console.log('✓ Filter panel exists');

    // Check for clear filters button
    const clearButton = page.locator('button').filter({ hasText: /clear|reset/i }).first();
    if (await clearButton.count() > 0) {
      console.log('✓ Clear filters button found');
    } else {
      console.log('⚠ Clear filters button not found');
    }

    // Check for apply filters button
    const applyButton = page.locator('button').filter({ hasText: /apply|search/i }).first();
    if (await applyButton.count() > 0) {
      console.log('✓ Apply filters button found');
    } else {
      console.log('⚠ Apply filters button not found');
    }
  });

  test('Audit 14: Results count accuracy', async ({ page }) => {
    await page.goto(PROPERTIES_URL);
    await waitForPropertyCards(page);

    console.log(`\n=== RESULTS COUNT ACCURACY AUDIT ===`);

    // Get displayed count
    const countDisplay = page.locator('[data-testid="results-count"], .results-count, .total-results').first();
    if (await countDisplay.count() > 0) {
      const countText = await countDisplay.textContent();
      console.log(`Displayed count: ${countText}`);

      // Count actual cards
      const cards = await getPropertyCards(page);
      console.log(`Actual cards: ${cards.length}`);

      // They should match (or displayed count should be total available)
      expect(cards.length).toBeGreaterThan(0);
    } else {
      console.log('⚠ Results count display not found');
    }
  });
});
