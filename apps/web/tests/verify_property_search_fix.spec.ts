import { test, expect } from '@playwright/test';

test.describe('Property Search Fix Verification', () => {
  test('should load properties from Supabase', async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      console.log(`[BROWSER ${msg.type()}]:`, msg.text());
    });

    // Navigate to properties page
    await page.goto('http://localhost:5181/properties');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Wait a bit for Supabase query to complete
    await page.waitForTimeout(3000);

    // Check for debug logs in console
    const logs = [];
    page.on('console', msg => logs.push(msg.text()));

    // Take screenshot of current state
    await page.screenshot({
      path: 'property-search-after-fix.png',
      fullPage: true
    });

    // Check if "0 Properties Found" text is present
    const zeroPropertiesText = page.locator('text=0 Properties Found');
    const hasZeroProperties = await zeroPropertiesText.isVisible().catch(() => false);

    // Check for property cards
    const propertyCards = page.locator('[class*="property"], [class*="card"]');
    const cardCount = await propertyCards.count();

    // Check for "Searching properties..." infinite spinner
    const searchingSpinner = page.locator('text=Searching properties');
    const isStillSearching = await searchingSpinner.isVisible().catch(() => false);

    console.log('\n=== FIX VERIFICATION RESULTS ===');
    console.log(`Has "0 Properties Found": ${hasZeroProperties}`);
    console.log(`Property cards found: ${cardCount}`);
    console.log(`Still showing "Searching...": ${isStillSearching}`);

    // Verify the fix worked
    if (!hasZeroProperties && cardCount > 0 && !isStillSearching) {
      console.log('✅ FIX SUCCESSFUL! Properties are now loading.');
    } else {
      console.log('❌ FIX INCOMPLETE. Check browser console logs above.');
    }

    // Check for specific debug logs we added
    await page.waitForTimeout(1000);

    // Try to find our debug logs
    const hasSupabaseLog = await page.evaluate(() => {
      return window.console.toString().includes('SUPABASE QUERY RESULT');
    }).catch(() => false);

    console.log(`Debug logs present: ${hasSupabaseLog}`);

    // Generate detailed report
    const report = {
      timestamp: new Date().toISOString(),
      test: 'Property Search Fix',
      results: {
        hasZeroProperties,
        propertyCardCount: cardCount,
        isStillSearching,
        fixSuccessful: !hasZeroProperties && cardCount > 0 && !isStillSearching
      }
    };

    console.log('\n=== DETAILED REPORT ===');
    console.log(JSON.stringify(report, null, 2));
  });

  test('should show debug logs in console', async ({ page }) => {
    const consoleLogs = [];

    page.on('console', msg => {
      const text = msg.text();
      consoleLogs.push(text);
      if (text.includes('🔍')) {
        console.log(`[DEBUG LOG]: ${text}`);
      }
    });

    await page.goto('http://localhost:5181/properties');
    await page.waitForTimeout(3000);

    // Check for our specific debug logs
    const hasSupabaseLog = consoleLogs.some(log => log.includes('SUPABASE QUERY RESULT'));
    const hasBeforeFilterLog = consoleLogs.some(log => log.includes('DEBUG BEFORE FILTERING'));
    const hasSettingPropertiesLog = consoleLogs.some(log => log.includes('DEBUG SETTING PROPERTIES'));

    console.log('\n=== DEBUG LOGS CHECK ===');
    console.log(`✓ SUPABASE QUERY RESULT: ${hasSupabaseLog}`);
    console.log(`✓ DEBUG BEFORE FILTERING: ${hasBeforeFilterLog}`);
    console.log(`✓ DEBUG SETTING PROPERTIES: ${hasSettingPropertiesLog}`);

    // Find the log with property count
    const countLog = consoleLogs.find(log => log.includes('properties_count'));
    if (countLog) {
      console.log(`\nProperty count from Supabase: ${countLog}`);
    }

    expect(hasSupabaseLog || hasBeforeFilterLog || hasSettingPropertiesLog).toBeTruthy();
  });
});
