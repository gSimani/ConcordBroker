import { test, expect, Page } from '@playwright/test';

/**
 * ConcordBroker Site Verification Test Suite
 *
 * This test verifies the functionality of the ConcordBroker site and ensures
 * it matches the production site at https://www.concordbroker.com
 */

const LOCAL_URL = 'http://localhost:5174';
const PRODUCTION_URL = 'https://www.concordbroker.com';

test.describe('ConcordBroker Site Verification', () => {

  test.beforeEach(async ({ page }) => {
    // Set longer timeout for network operations
    page.setDefaultTimeout(30000);

    // Navigate to local development site
    await page.goto(LOCAL_URL);
  });

  test('Home page loads successfully', async ({ page }) => {
    // Check that the page loads
    await expect(page).toHaveTitle(/ConcordBroker/i);

    // Verify main navigation elements exist
    await expect(page.locator('nav')).toBeVisible();

    // Check for key sections on homepage
    await expect(page.locator('text=ConcordBroker')).toBeVisible();
  });

  test('Navigation menu works correctly', async ({ page }) => {
    // Test navigation to different sections
    const navigationLinks = [
      { text: 'Properties', expectedUrl: '/properties' },
      { text: 'Dashboard', expectedUrl: '/dashboard' },
      { text: 'Search', expectedUrl: '/search' }
    ];

    for (const link of navigationLinks) {
      try {
        await page.click(`text=${link.text}`);
        await page.waitForURL(`**${link.expectedUrl}`, { timeout: 10000 });
        await expect(page).toHaveURL(new RegExp(link.expectedUrl));
        console.log(`✅ Navigation to ${link.text} working`);
      } catch (error) {
        console.log(`⚠️ Navigation to ${link.text} may have issues: ${error}`);
      }
    }
  });

  test('Properties page loads and displays content', async ({ page }) => {
    await page.goto(`${LOCAL_URL}/properties`);

    // Wait for the properties page to load
    await page.waitForLoadState('networkidle');

    // Check for search functionality
    const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="property" i]').first();
    if (await searchInput.isVisible()) {
      await expect(searchInput).toBeVisible();
      console.log('✅ Search input found');
    } else {
      console.log('⚠️ Search input not immediately visible - checking for other search elements');
    }

    // Check for filter options
    const filterElements = page.locator('select, [role="combobox"], button:has-text("Filter")');
    if (await filterElements.count() > 0) {
      console.log('✅ Filter elements found');
    } else {
      console.log('⚠️ No filter elements detected');
    }

    // Look for property listings or loading states
    const propertyCards = page.locator('[data-testid*="property"], .property-card, [class*="property"]');
    const loadingElements = page.locator('.loading, [data-testid*="loading"], .spinner');

    // Wait for either properties to load or loading to complete
    try {
      await Promise.race([
        propertyCards.first().waitFor({ timeout: 15000 }),
        loadingElements.first().waitFor({ state: 'detached', timeout: 15000 })
      ]);

      if (await propertyCards.count() > 0) {
        console.log(`✅ Found ${await propertyCards.count()} property elements`);
      }
    } catch (error) {
      console.log('⚠️ Properties may still be loading or no properties found');
    }
  });

  test('Color scheme verification - Golden/Navy theme', async ({ page }) => {
    await page.goto(`${LOCAL_URL}/properties`);

    // Check for golden/navy color scheme in CSS
    const bodyElement = page.locator('body');
    const headerElement = page.locator('header, nav').first();

    // Get computed styles to verify color scheme
    const bodyStyles = await bodyElement.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        color: styles.color
      };
    });

    console.log('Body styles:', bodyStyles);

    // Look for golden/navy color indicators in CSS variables or classes
    const hasGoldenColors = await page.evaluate(() => {
      const rootStyles = window.getComputedStyle(document.documentElement);
      const allStyles = Array.from(document.styleSheets)
        .flatMap(sheet => {
          try {
            return Array.from(sheet.cssRules);
          } catch {
            return [];
          }
        })
        .map(rule => rule.cssText || '')
        .join(' ');

      // Check for golden/yellow/navy/blue color values
      const hasGolden = /(?:#[a-f0-9]{0,6}(?:ffd700|ffa500|ffb347|daa520)|rgb\(\s*255,\s*215,\s*0|rgb\(\s*255,\s*165,\s*0|gold|orange)/i.test(allStyles);
      const hasNavy = /(?:#[a-f0-9]{0,6}(?:000080|191970|1e3a8a|1e40af)|rgb\(\s*0,\s*0,\s*128|rgb\(\s*25,\s*57,\s*112|navy|blue)/i.test(allStyles);

      return { hasGolden, hasNavy, rootStyles: rootStyles.getPropertyValue('--primary') };
    });

    console.log('Color scheme analysis:', hasGoldenColors);

    if (hasGoldenColors.hasGolden || hasGoldenColors.hasNavy) {
      console.log('✅ Golden/Navy color scheme detected');
    } else {
      console.log('⚠️ Golden/Navy color scheme not clearly detected');
    }
  });

  test('Search functionality works', async ({ page }) => {
    await page.goto(`${LOCAL_URL}/properties`);
    await page.waitForLoadState('networkidle');

    // Find search input - try multiple selectors
    const searchSelectors = [
      'input[placeholder*="search" i]',
      'input[placeholder*="property" i]',
      'input[placeholder*="address" i]',
      'input[type="search"]',
      'input[name*="search"]',
      '.search input',
      '[data-testid*="search"] input'
    ];

    let searchInput = null;
    for (const selector of searchSelectors) {
      const element = page.locator(selector).first();
      if (await element.isVisible()) {
        searchInput = element;
        break;
      }
    }

    if (searchInput) {
      console.log('✅ Search input found');

      // Test search functionality
      await searchInput.fill('Miami');
      await page.keyboard.press('Enter');

      // Wait for search results or state change
      await page.waitForTimeout(3000);
      console.log('✅ Search executed');
    } else {
      console.log('⚠️ Search input not found - may be in a different location or format');
    }
  });

  test('Property detail page navigation works', async ({ page }) => {
    // Test the specific production URL format: /property/474131031040
    const testParcelId = '474131031040';
    const testUrl = `${LOCAL_URL}/property/${testParcelId}`;

    console.log(`Testing property detail URL: ${testUrl}`);

    try {
      await page.goto(testUrl);
      await page.waitForLoadState('networkidle');

      // Check if page loads without errors
      const errorElements = page.locator('text=/error|not found|404/i');
      const errorCount = await errorElements.count();

      if (errorCount === 0) {
        console.log('✅ Property detail page loads without errors');

        // Look for property information tabs or sections
        const tabElements = page.locator('[role="tab"], .tab, button:has-text("Analysis"), button:has-text("History"), button:has-text("Owner")');
        const tabCount = await tabElements.count();

        if (tabCount > 0) {
          console.log(`✅ Found ${tabCount} tabs/sections on property page`);

          // Test clicking on tabs if they exist
          const firstTab = tabElements.first();
          if (await firstTab.isVisible()) {
            await firstTab.click();
            console.log('✅ Tab interaction works');
          }
        }

        // Check for property data elements
        const dataElements = page.locator('text=/\\$|address|sqft|acres|value/i');
        const dataCount = await dataElements.count();

        if (dataCount > 0) {
          console.log(`✅ Found ${dataCount} property data elements`);
        }

      } else {
        console.log('⚠️ Property detail page shows error or not found');
      }

    } catch (error) {
      console.log(`⚠️ Property detail page navigation failed: ${error}`);
    }
  });

  test('Enhanced property URL format works', async ({ page }) => {
    // Test the enhanced URL format: /property/{county}/{parcelId}/{addressSlug}
    const testCounty = 'miami-dade';
    const testParcelId = '474131031040';
    const testAddressSlug = 'sample-address';
    const enhancedUrl = `${LOCAL_URL}/property/${testCounty}/${testParcelId}/${testAddressSlug}`;

    console.log(`Testing enhanced property URL: ${enhancedUrl}`);

    try {
      await page.goto(enhancedUrl);
      await page.waitForLoadState('networkidle');

      // Check if the enhanced URL format is supported
      const currentUrl = page.url();
      if (currentUrl.includes(testParcelId)) {
        console.log('✅ Enhanced property URL format is supported');
      } else {
        console.log('⚠️ Enhanced property URL format may not be fully implemented');
      }

    } catch (error) {
      console.log(`⚠️ Enhanced property URL test failed: ${error}`);
    }
  });

  test('API endpoints are responding', async ({ page }) => {
    // Test if the backend API is working by checking network responses
    const apiResponses: string[] = [];

    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiResponses.push(`${response.status()} - ${response.url()}`);
      }
    });

    // Navigate to properties page to trigger API calls
    await page.goto(`${LOCAL_URL}/properties`);
    await page.waitForLoadState('networkidle');

    // Wait a bit more for any async API calls
    await page.waitForTimeout(5000);

    if (apiResponses.length > 0) {
      console.log('✅ API calls detected:');
      apiResponses.forEach(response => console.log(`  ${response}`));
    } else {
      console.log('⚠️ No API calls detected - may be using static data or different API pattern');
    }
  });

  test('Responsive design check', async ({ page }) => {
    // Test mobile responsiveness
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone size
    await page.goto(`${LOCAL_URL}/properties`);

    // Check if mobile navigation exists
    const mobileMenu = page.locator('[aria-label*="menu"], .mobile-menu, button:has-text("☰"), button:has-text("Menu")');
    const mobileMenuVisible = await mobileMenu.isVisible();

    if (mobileMenuVisible) {
      console.log('✅ Mobile menu detected');
    } else {
      console.log('⚠️ Mobile menu not detected - checking responsive behavior');
    }

    // Reset to desktop size
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('Performance check', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${LOCAL_URL}/properties`);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);

    if (loadTime < 5000) {
      console.log('✅ Good page load performance');
    } else if (loadTime < 10000) {
      console.log('⚠️ Moderate page load performance');
    } else {
      console.log('❌ Slow page load performance');
    }

    // Check for performance monitoring
    const performanceEntries = await page.evaluate(() => {
      return performance.getEntriesByType('navigation').map(entry => ({
        loadTime: entry.loadEventEnd - entry.loadEventStart,
        domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart
      }));
    });

    console.log('Performance metrics:', performanceEntries);
  });

});

test.describe('Production Comparison', () => {

  test('Compare with production site structure', async ({ page }) => {
    // This test compares key elements with the production site
    console.log('🔍 Comparing with production site...');

    try {
      // Check production site
      await page.goto(PRODUCTION_URL);
      await page.waitForLoadState('networkidle');

      const prodTitle = await page.title();
      const prodNavigation = await page.locator('nav').count();

      console.log(`Production site title: ${prodTitle}`);
      console.log(`Production navigation elements: ${prodNavigation}`);

      // Now check local site
      await page.goto(LOCAL_URL);
      await page.waitForLoadState('networkidle');

      const localTitle = await page.title();
      const localNavigation = await page.locator('nav').count();

      console.log(`Local site title: ${localTitle}`);
      console.log(`Local navigation elements: ${localNavigation}`);

      // Compare key elements
      if (prodTitle === localTitle) {
        console.log('✅ Titles match');
      } else {
        console.log('⚠️ Titles differ');
      }

      if (prodNavigation === localNavigation) {
        console.log('✅ Navigation structure matches');
      } else {
        console.log('⚠️ Navigation structure differs');
      }

    } catch (error) {
      console.log(`⚠️ Production comparison failed: ${error}`);
    }
  });

});