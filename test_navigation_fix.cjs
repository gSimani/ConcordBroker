const { chromium } = require('playwright');

(async () => {
  console.log('=== TESTING PROPERTY NAVIGATION FIX ===\n');

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    // Navigate to properties page
    console.log('1. Navigating to properties page...');
    await page.goto('http://localhost:5173/properties', {
      waitUntil: 'networkidle',
      timeout: 10000
    });

    await page.waitForTimeout(3000);

    // Find and click first property card
    console.log('2. Looking for property cards to click...');
    const propertyCards = await page.locator('.mini-property-card').count();
    console.log(`   Found ${propertyCards} property cards`);

    if (propertyCards > 0) {
      console.log('3. Clicking first property card...');

      // Get parcel ID before clicking
      const firstCard = await page.locator('.mini-property-card').first();

      // Click the card
      await firstCard.click();
      await page.waitForTimeout(3000);

      // Check if navigation happened
      const currentUrl = page.url();
      console.log(`   Current URL: ${currentUrl}`);

      if (currentUrl.includes('/property/')) {
        console.log('   ✅ SUCCESS: Navigation to property detail works!');

        // Check for content
        const hasContent = await page.locator('text=/property|address|owner|tax/i').count();
        const hasTabs = await page.locator('[role="tablist"], .tabs, text=/overview|sales|tax/i').count();

        console.log(`   Found ${hasContent} property content elements`);
        console.log(`   Found ${hasTabs} tab elements`);

        if (hasContent > 0 || hasTabs > 0) {
          console.log('   ✅ Property detail page is showing content');
        }

        await page.screenshot({ path: 'navigation_fixed.png' });
        console.log('   📸 Screenshot saved as navigation_fixed.png');
      } else {
        console.log('   ❌ Navigation did not work. Still on:', currentUrl);
      }
    } else {
      console.log('   ❌ No property cards found');
    }

    console.log('\n=== TEST COMPLETE ===');

  } catch (error) {
    console.error('Test failed:', error.message);
  } finally {
    await browser.close();
  }
})();