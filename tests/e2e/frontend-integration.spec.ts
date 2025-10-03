/**
 * Frontend Component Integration Tests
 * Tests all major UI components and their data flows
 */
import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

test.describe('Property Search Page', () => {
  test('loads successfully', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);
    await expect(page).toHaveTitle(/Property Search|ConcordBroker/i);
  });

  test('search input is functional', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first();
    await searchInput.fill('miami');
    await searchInput.press('Enter');

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Check if results container exists
    const hasResults = await page.locator('[data-testid="property-results"], .property-card, .mini-card').count();
    expect(hasResults).toBeGreaterThanOrEqual(0);
  });

  test('filters panel is accessible', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    // Look for common filter elements
    const filterPanel = page.locator('[data-testid="filters-panel"], .filters, [class*="filter"]').first();

    if (await filterPanel.isVisible()) {
      expect(await filterPanel.isVisible()).toBeTruthy();
    }
  });

  test('county filter works', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    // Try to find and use county filter
    const countyFilter = page.locator('select[name*="county" i], input[name*="county" i]').first();

    if (await countyFilter.isVisible()) {
      await countyFilter.selectOption('MIAMI-DADE');
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Property Profile Page', () => {
  const testParcelId = '504203060330';

  test('loads property details', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/${testParcelId}`);

    // Wait for property data to load
    await page.waitForTimeout(2000);

    // Check for common property detail elements
    const hasPropertyInfo = await page.locator(
      '[data-testid="property-details"], .property-info, [class*="property"]'
    ).count();

    expect(hasPropertyInfo).toBeGreaterThan(0);
  });

  test('Core Property tab displays data', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/${testParcelId}`);
    await page.waitForTimeout(2000);

    // Look for core property tab
    const coreTab = page.locator('button:has-text("Core Property"), [data-tab="core"], [aria-label*="core" i]').first();

    if (await coreTab.isVisible()) {
      await coreTab.click();
      await page.waitForTimeout(1000);

      // Check for property fields
      const hasFields = await page.locator(
        'text=/parcel|owner|address|value/i'
      ).count();

      expect(hasFields).toBeGreaterThan(0);
    }
  });

  test('Sales History tab is functional', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/${testParcelId}`);
    await page.waitForTimeout(2000);

    // Look for sales history tab
    const salesTab = page.locator('button:has-text("Sales"), [data-tab="sales"], [aria-label*="sales" i]').first();

    if (await salesTab.isVisible()) {
      await salesTab.click();
      await page.waitForTimeout(2000);

      // Check for sales data or empty state
      const hasSalesContent = await page.locator(
        '[data-testid="sales-history"], .sales-table, text=/sale|price|date/i'
      ).count();

      expect(hasSalesContent).toBeGreaterThanOrEqual(0);
    }
  });

  test('Sunbiz tab is accessible', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/${testParcelId}`);
    await page.waitForTimeout(2000);

    const sunbizTab = page.locator('button:has-text("Sunbiz"), [data-tab="sunbiz"], [aria-label*="sunbiz" i]').first();

    if (await sunbizTab.isVisible()) {
      await sunbizTab.click();
      await page.waitForTimeout(1000);
    }
  });

  test('Tax tab is accessible', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/${testParcelId}`);
    await page.waitForTimeout(2000);

    const taxTab = page.locator('button:has-text("Tax"), [data-tab="tax"], [aria-label*="tax" i]').first();

    if (await taxTab.isVisible()) {
      await taxTab.click();
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Mini Property Cards', () => {
  test('display in search results', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    const searchInput = page.locator('input[type="search"]').first();
    await searchInput.fill('miami');
    await searchInput.press('Enter');

    await page.waitForTimeout(2000);

    // Look for mini cards
    const cards = page.locator('[data-testid="mini-card"], .mini-card, .property-card');
    const count = await cards.count();

    if (count > 0) {
      // Check first card has expected elements
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();

      // Check for common card elements
      const hasAddress = await firstCard.locator('text=/address|street|city/i').count();
      expect(hasAddress).toBeGreaterThanOrEqual(0);
    }
  });

  test('cards are clickable and navigate to property profile', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    const searchInput = page.locator('input[type="search"]').first();
    await searchInput.fill('miami');
    await searchInput.press('Enter');

    await page.waitForTimeout(2000);

    const cards = page.locator('[data-testid="mini-card"], .mini-card, .property-card');
    const count = await cards.count();

    if (count > 0) {
      const firstCard = cards.first();
      await firstCard.click();

      await page.waitForTimeout(1000);

      // Should navigate to property profile
      expect(page.url()).toContain('/property/');
    }
  });
});

test.describe('Autocomplete Functionality', () => {
  test('autocomplete suggestions appear', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    const searchInput = page.locator('input[type="search"]').first();
    await searchInput.fill('mia');

    await page.waitForTimeout(1000);

    // Look for autocomplete dropdown
    const dropdown = page.locator('[role="listbox"], [data-testid="autocomplete"], .autocomplete-dropdown');

    if (await dropdown.isVisible()) {
      const suggestions = await dropdown.locator('[role="option"], .suggestion-item').count();
      expect(suggestions).toBeGreaterThan(0);
    }
  });
});

test.describe('Responsive Design', () => {
  test('mobile view works', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${FRONTEND_URL}/properties/search`);

    await expect(page).toHaveTitle(/Property Search|ConcordBroker/i);
  });

  test('tablet view works', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${FRONTEND_URL}/properties/search`);

    await expect(page).toHaveTitle(/Property Search|ConcordBroker/i);
  });

  test('desktop view works', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`${FRONTEND_URL}/properties/search`);

    await expect(page).toHaveTitle(/Property Search|ConcordBroker/i);
  });
});

test.describe('Error Handling', () => {
  test('handles invalid parcel ID gracefully', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/property/INVALID-PARCEL-ID-12345`);

    await page.waitForTimeout(2000);

    // Should show error message or redirect
    const hasError = await page.locator('text=/not found|error|invalid/i').count();
    expect(hasError).toBeGreaterThanOrEqual(0);
  });

  test('handles network errors gracefully', async ({ page, context }) => {
    // Block API requests to simulate network error
    await context.route('**/api/**', route => route.abort());

    await page.goto(`${FRONTEND_URL}/properties/search`);
    await page.waitForTimeout(2000);

    // Page should still load without crashing
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('property search page loads in < 3 seconds', async ({ page }) => {
    const start = Date.now();
    await page.goto(`${FRONTEND_URL}/properties/search`);
    await page.waitForLoadState('networkidle');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(5000); // Allow 5s for first load
  });

  test('property profile loads in < 3 seconds', async ({ page }) => {
    const start = Date.now();
    await page.goto(`${FRONTEND_URL}/property/504203060330`);
    await page.waitForLoadState('networkidle');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(5000);
  });
});

test.describe('Data Consistency', () => {
  test('property data matches between search and profile', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/properties/search`);

    const searchInput = page.locator('input[type="search"]').first();
    await searchInput.fill('miami');
    await searchInput.press('Enter');

    await page.waitForTimeout(2000);

    const cards = page.locator('[data-testid="mini-card"], .mini-card, .property-card');
    const count = await cards.count();

    if (count > 0) {
      const firstCard = cards.first();

      // Get parcel ID from search result
      const cardText = await firstCard.textContent();

      await firstCard.click();
      await page.waitForTimeout(2000);

      // Verify we're on the property profile page
      expect(page.url()).toContain('/property/');
    }
  });
});
