const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Testing property detail pages...');

  try {
    // Test 1: Navigate to properties page
    console.log('1. Navigating to properties page...');
    await page.goto('http://localhost:5178/properties', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Test 2: Click on first property card
    console.log('2. Looking for property cards...');
    const firstCard = await page.locator('.mini-property-card').first();

    if (await firstCard.isVisible()) {
      console.log('3. Found property card, clicking...');
      await firstCard.click();
      await page.waitForTimeout(3000);

      // Test 3: Check if we're on a property detail page
      const currentUrl = page.url();
      console.log(`4. Current URL: ${currentUrl}`);

      if (currentUrl.includes('/property/')) {
        console.log('✅ SUCCESS: Navigated to property detail page');

        // Test 4: Check for property detail elements
        const hasPropertyInfo = await page.locator('text=/Property Information|Property Details|Overview/i').isVisible();
        const hasTabs = await page.locator('[role="tablist"], .tabs-container, text=/Overview|Sales|Tax|Financial/i').isVisible();

        if (hasPropertyInfo || hasTabs) {
          console.log('✅ SUCCESS: Property detail page is showing content');
          console.log('Elements found:');
          if (hasPropertyInfo) console.log('  - Property information section');
          if (hasTabs) console.log('  - Tab navigation');
        } else {
          console.log('⚠️ WARNING: Property detail page loaded but content may be missing');
        }

        // Take screenshot for verification
        await page.screenshot({ path: 'property_detail_test.png' });
        console.log('Screenshot saved as property_detail_test.png');

      } else {
        console.log('❌ ERROR: Did not navigate to property detail page');
        console.log(`Expected URL to contain '/property/', got: ${currentUrl}`);
      }
    } else {
      console.log('❌ ERROR: No property cards found on the page');
      console.log('Checking for any clickable elements...');

      const anyClickable = await page.locator('[onClick], [href*="property"], button:has-text("View")').first();
      if (await anyClickable.isVisible()) {
        console.log('Found alternative clickable element, trying...');
        await anyClickable.click();
        await page.waitForTimeout(2000);
        console.log(`Navigated to: ${page.url()}`);
      }
    }

    // Test 5: Direct navigation test
    console.log('\n5. Testing direct navigation to property detail...');
    await page.goto('http://localhost:5178/property/474131031040', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const directNavSuccess = await page.locator('text=/Property|Details|Overview|474131031040/i').isVisible();
    if (directNavSuccess) {
      console.log('✅ SUCCESS: Direct navigation to property detail works');
    } else {
      console.log('⚠️ Direct navigation loaded but content may be loading...');
      // Check console for errors
      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.log('Browser console error:', msg.text());
        }
      });
    }

    await page.screenshot({ path: 'direct_property_navigation.png' });
    console.log('Screenshot saved as direct_property_navigation.png');

  } catch (error) {
    console.error('Test failed:', error.message);
  } finally {
    await browser.close();
    console.log('\nTest completed.');
  }
})();