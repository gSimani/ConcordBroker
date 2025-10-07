const { chromium } = require('playwright');

(async () => {
  console.log('=== VERIFYING PROPERTY DETAIL FIX ===\n');

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  try {
    // Test 1: Direct navigation to property detail
    console.log('1. Testing direct navigation to property detail page...');
    await page.goto('http://localhost:5179/property/474131031040', {
      waitUntil: 'networkidle',
      timeout: 10000
    });

    await page.waitForTimeout(2000);

    // Check URL
    const url = page.url();
    console.log(`   Current URL: ${url}`);

    // Check for any error messages
    const errorMessages = await page.locator('text=/error|failed|cannot|undefined/i').count();

    if (errorMessages > 0) {
      console.log(`   ⚠️  Found ${errorMessages} potential error messages`);

      // Try to get the actual error text
      const errorText = await page.locator('text=/error|failed/i').first().textContent().catch(() => null);
      if (errorText) {
        console.log(`   Error text: ${errorText.substring(0, 100)}...`);
      }
    } else {
      console.log('   ✅ No error messages found');
    }

    // Check for property detail elements
    const hasPropertyContent = await page.locator('text=/property|address|owner|value|tax/i').count();
    const hasTabs = await page.locator('[role="tablist"], .tabs, text=/overview|sales|analysis/i').count();

    console.log(`   Found ${hasPropertyContent} property-related text elements`);
    console.log(`   Found ${hasTabs} tab-related elements`);

    if (hasPropertyContent > 0 || hasTabs > 0) {
      console.log('   ✅ Property detail page appears to be loading content');
    } else {
      console.log('   ⚠️  Property detail page may not be showing content');
    }

    // Take screenshot
    await page.screenshot({ path: 'property_detail_verification.png', fullPage: false });
    console.log('   📸 Screenshot saved as property_detail_verification.png');

    // Test 2: Navigate from properties list
    console.log('\n2. Testing navigation from properties list...');
    await page.goto('http://localhost:5179/properties', {
      waitUntil: 'networkidle',
      timeout: 10000
    });

    await page.waitForTimeout(2000);

    // Look for clickable property cards or links
    const propertyLinks = await page.locator('a[href*="/property/"], [onClick*="property"], .cursor-pointer').count();
    console.log(`   Found ${propertyLinks} clickable property elements`);

    if (propertyLinks > 0) {
      // Click the first one
      const firstLink = await page.locator('a[href*="/property/"], [onClick*="property"], .cursor-pointer').first();
      console.log('   Clicking first property...');
      await firstLink.click();
      await page.waitForTimeout(3000);

      const newUrl = page.url();
      if (newUrl.includes('/property/')) {
        console.log(`   ✅ Successfully navigated to: ${newUrl}`);
      } else {
        console.log(`   ⚠️  Navigation did not go to property detail. Current URL: ${newUrl}`);
      }
    } else {
      console.log('   ⚠️  No clickable property elements found on properties page');
    }

    console.log('\n=== VERIFICATION COMPLETE ===');
    console.log('\nSUMMARY:');

    if (url.includes('/property/') && (hasPropertyContent > 0 || hasTabs > 0) && errorMessages === 0) {
      console.log('✅ Property detail pages are working correctly!');
      console.log('   - Direct navigation works');
      console.log('   - No errors detected');
      console.log('   - Content is displaying');
    } else {
      console.log('⚠️  Property detail pages may need further fixes:');
      if (!url.includes('/property/')) console.log('   - URL routing issue');
      if (errorMessages > 0) console.log('   - Error messages detected');
      if (hasPropertyContent === 0 && hasTabs === 0) console.log('   - Content not displaying');
    }

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  } finally {
    await browser.close();
  }
})();