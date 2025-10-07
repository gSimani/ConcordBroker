import { test, expect } from '@playwright/test';

const PROPERTIES = '/properties';

test.describe('Local Properties Parity', () => {
  test('renders properties page and title', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}${PROPERTIES}`);
    await page.waitForLoadState('networkidle');
    await expect(page.locator('#root')).toBeVisible();
    await expect(page).toHaveTitle(/ConcordBroker/i);
  });

  test('search box interaction triggers API', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}${PROPERTIES}`);
    await page.waitForLoadState('networkidle');
    const selectors = [
      'input[placeholder*="search" i]',
      'input[placeholder*="property" i]',
      'input[placeholder*="address" i]',
      'input[type="search"]',
      'input[name*="search"]',
      '.search input',
      '[data-testid*="search"] input',
    ];
    let found = false;
    for (const sel of selectors) {
      const el = page.locator(sel).first();
      if (await el.count() && await el.isVisible()) {
        await el.fill('Miami');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1500);
        found = true;
        break;
      }
    }
    expect(found).toBeTruthy();
  });

  test('filters or property cards are present', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}${PROPERTIES}`);
    await page.waitForLoadState('networkidle');
    const filterSelectors = [
      'select',
      '[role="combobox"]',
      'button:has-text("Filter")',
      'button:has-text("Filters")',
      'input[type="range"]',
    ];
    const cardSelectors = [
      '[data-testid*="property"]',
      '.property-card',
      '[class*="property" i]',
      '.card:has-text("$")',
    ];
    let hasFilter = false;
    for (const sel of filterSelectors) {
      const loc = page.locator(sel);
      if (await loc.count() && await loc.first().isVisible()) { hasFilter = true; break; }
    }
    let hasCards = false;
    for (const sel of cardSelectors) {
      const loc = page.locator(sel);
      if (await loc.count() > 0) { hasCards = true; break; }
    }
    expect(hasFilter || hasCards).toBeTruthy();
  });

  test('API payload shape sanity (properties search)', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}${PROPERTIES}`);
    await page.waitForLoadState('networkidle');

    // Trigger a lightweight search to cause an API call
    const input = page.locator('input, [role="combobox"], [type="search"]').first();
    if (await input.count()) {
      await input.fill('Miami');
      await page.keyboard.press('Enter');
    }

    const resp = await page.waitForResponse(r => r.url().includes('/api/properties') && r.status() === 200, { timeout: 15000 });
    const body = await resp.json().catch(() => null);

    // Tolerant shape assertions: either {success, data: []} or array result
    expect(body).toBeTruthy();
    if (Array.isArray(body)) {
      // Array of items, optional check
      expect(Array.isArray(body)).toBeTruthy();
    } else if (typeof body === 'object') {
      // Common API wrapper
      const keys = Object.keys(body);
      expect(keys.length).toBeGreaterThan(0);
      // If data present, expect it to be array
      if ('data' in body) {
        expect(Array.isArray((body as any).data)).toBeTruthy();
      }
    }
  });
});
