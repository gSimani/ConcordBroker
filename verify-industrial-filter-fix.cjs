/**
 * Verification Script: Industrial Filter Fix
 * Tests that Industrial property filter now returns correct results
 * after adding 3-digit padded DOR codes (040-049)
 */

const { chromium } = require('playwright');
const fs = require('fs');

const TEST_URL = 'http://localhost:5191/properties';
const SCREENSHOT_DIR = './test-screenshots';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function verifyIndustrialFilter() {
  console.log('\n🔧 INDUSTRIAL FILTER FIX VERIFICATION');
  console.log('=====================================\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    timestamp: new Date().toISOString(),
    testUrl: TEST_URL,
    fix: 'Added 3-digit padded DOR codes (040-049) to industrial array',
    tests: []
  };

  try {
    // Navigate to properties page
    console.log('📍 Navigating to:', TEST_URL);
    await page.goto(TEST_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000); // Wait for initial load

    // Take baseline screenshot
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/industrial-fix-baseline.png`,
      fullPage: false
    });
    console.log('✅ Baseline screenshot taken\n');

    // TEST 1: Click Industrial filter button
    console.log('🧪 TEST 1: Click Industrial Filter Button');
    console.log('------------------------------------------');

    // Find and click the Industrial button
    const industrialButton = await page.locator('button:has-text("Industrial")').first();

    if (await industrialButton.count() === 0) {
      throw new Error('Industrial button not found on page!');
    }

    console.log('✅ Industrial button found');

    // Take screenshot before click
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/industrial-before-click.png`,
      fullPage: false
    });

    // Click the button
    await industrialButton.click();
    console.log('✅ Industrial button clicked');

    // Wait for properties to load
    await page.waitForTimeout(5000); // Give time for filter to apply and data to load

    // Take screenshot after click
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/industrial-after-click.png`,
      fullPage: false
    });

    // TEST 2: Count MiniPropertyCards
    console.log('\n🧪 TEST 2: Count Industrial Properties');
    console.log('---------------------------------------');

    // Look for the property count display or property cards
    const propertyCards = await page.locator('[class*="MiniPropertyCard"], [class*="property-card"]').count();
    console.log(`📊 Property cards visible: ${propertyCards}`);

    // Look for any text showing property count
    const pageText = await page.textContent('body');
    const countMatches = pageText.match(/(\d+)\s+properties?/gi);

    if (countMatches) {
      console.log('📊 Found property count text:', countMatches);
    }

    // Check for "0 properties" or "No results" messages
    const noResultsText = await page.locator('text=/no results|0 properties|no industrial properties/i').count();

    if (noResultsText > 0) {
      console.log('❌ FAIL: Still showing "No results" or "0 properties"');
      results.tests.push({
        name: 'Industrial filter returns results',
        status: 'FAIL',
        reason: 'Still showing no results message',
        propertyCards: propertyCards
      });
    } else if (propertyCards > 0) {
      console.log(`✅ PASS: Found ${propertyCards} property cards`);
      results.tests.push({
        name: 'Industrial filter returns results',
        status: 'PASS',
        propertyCards: propertyCards,
        expected: '50,092 total (may show paginated results)'
      });
    } else {
      console.log('⚠️  WARNING: No property cards found, but no error message either');
      results.tests.push({
        name: 'Industrial filter returns results',
        status: 'WARNING',
        reason: 'No property cards or error messages found',
        note: 'May still be loading or pagination issue'
      });
    }

    // TEST 3: Check console for errors
    console.log('\n🧪 TEST 3: Console Error Check');
    console.log('-------------------------------');

    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text()
      });
    });

    // Reload to capture console messages
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Click Industrial again after reload
    await industrialButton.click();
    await page.waitForTimeout(3000);

    const errors = consoleLogs.filter(log => log.type === 'error');
    const warnings = consoleLogs.filter(log => log.type === 'warning');

    console.log(`📊 Console Errors: ${errors.length}`);
    console.log(`📊 Console Warnings: ${warnings.length}`);

    if (errors.length > 0) {
      console.log('\n⚠️  Console Errors Found:');
      errors.forEach((err, i) => {
        console.log(`  ${i + 1}. ${err.text.substring(0, 100)}`);
      });
    } else {
      console.log('✅ No console errors');
    }

    results.tests.push({
      name: 'Console error check',
      status: errors.length === 0 ? 'PASS' : 'WARNING',
      consoleErrors: errors.length,
      consoleWarnings: warnings.length
    });

    // TEST 4: Verify filter is highlighted/active
    console.log('\n🧪 TEST 4: Filter Active State');
    console.log('--------------------------------');

    const industrialButtonState = await industrialButton.evaluate(el => {
      const style = window.getComputedStyle(el);
      return {
        backgroundColor: style.backgroundColor,
        color: style.color,
        borderColor: style.borderColor
      };
    });

    console.log('🎨 Industrial button styles:', industrialButtonState);

    const isHighlighted = industrialButtonState.backgroundColor.includes('254, 215, 170') ||
                          industrialButtonState.backgroundColor.includes('#fed7aa');

    if (isHighlighted) {
      console.log('✅ Industrial filter is highlighted (active state)');
      results.tests.push({
        name: 'Filter active state',
        status: 'PASS',
        buttonStyle: industrialButtonState
      });
    } else {
      console.log('⚠️  Industrial filter may not be active');
      results.tests.push({
        name: 'Filter active state',
        status: 'WARNING',
        buttonStyle: industrialButtonState
      });
    }

    // Final screenshot
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/industrial-fix-final.png`,
      fullPage: false
    });

    // Summary
    console.log('\n📊 VERIFICATION SUMMARY');
    console.log('======================');
    const passedTests = results.tests.filter(t => t.status === 'PASS').length;
    const totalTests = results.tests.length;
    console.log(`Tests Passed: ${passedTests}/${totalTests}`);
    console.log(`Status: ${passedTests === totalTests ? '✅ ALL TESTS PASSED' : '⚠️  SOME TESTS NEED REVIEW'}`);

    results.tests.forEach((test, i) => {
      console.log(`\n${i + 1}. ${test.name}: ${test.status}`);
      if (test.reason) console.log(`   Reason: ${test.reason}`);
      if (test.propertyCards !== undefined) console.log(`   Property Cards: ${test.propertyCards}`);
    });

    console.log('\n📸 Screenshots saved to:', SCREENSHOT_DIR);
    console.log('   - industrial-fix-baseline.png');
    console.log('   - industrial-before-click.png');
    console.log('   - industrial-after-click.png');
    console.log('   - industrial-fix-final.png');

  } catch (error) {
    console.error('\n❌ TEST FAILED WITH ERROR:', error.message);
    results.error = error.message;

    // Take error screenshot
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/industrial-fix-error.png`,
      fullPage: true
    });
  } finally {
    // Save results to JSON
    fs.writeFileSync(
      './test-results/industrial-fix-verification.json',
      JSON.stringify(results, null, 2)
    );
    console.log('\n💾 Results saved to: test-results/industrial-fix-verification.json\n');

    await browser.close();
  }
}

// Run verification
verifyIndustrialFilter().catch(console.error);
