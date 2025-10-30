/**
 * VERIFY ICON FIX - Check that React icon warnings are gone
 * Tests the MiniPropertyCard icon rendering after applying ICON_MAP fix
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5191';

async function verifyIconFix() {
  console.log('🔍 VERIFYING ICON FIX\n');
  console.log('═'.repeat(100));

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    iconWarnings: [],
    allConsoleMessages: [],
    testPassed: false
  };

  try {
    // Capture all console messages
    page.on('console', msg => {
      const text = msg.text();
      results.allConsoleMessages.push({
        type: msg.type(),
        text
      });

      // Look for icon-related warnings
      if (msg.type() === 'warning' || msg.type() === 'error') {
        const lowerText = text.toLowerCase();
        if (lowerText.includes('icon') ||
            lowerText.includes('component') ||
            lowerText.includes('tag') ||
            lowerText.includes('home') ||
            lowerText.includes('building') ||
            lowerText.includes('store')) {
          results.iconWarnings.push(text);
        }
      }
    });

    // Navigate to properties page
    console.log('\n📊 STEP 1: Navigate to Properties Page');
    console.log('-'.repeat(100));

    const startNav = Date.now();
    await page.goto(`${BASE_URL}/properties`, { waitUntil: 'networkidle', timeout: 60000 });
    const navTime = Date.now() - startNav;

    console.log(`✅ Page loaded in ${navTime}ms`);

    // Wait for page to fully load
    await page.waitForTimeout(3000);

    // Click Commercial filter to trigger property cards
    console.log('\n📊 STEP 2: Click Commercial Filter to Load Properties');
    console.log('-'.repeat(100));

    const commercialButton = await page.locator('button:has-text("Commercial")').first();
    if (await commercialButton.isVisible()) {
      await commercialButton.click();
      console.log('✅ Clicked Commercial filter');

      // Wait for cards to potentially load
      await page.waitForTimeout(2000);
    }

    // Take screenshot
    await page.screenshot({
      path: 'test-screenshots/icon-fix-verification.png',
      fullPage: false
    });
    console.log('📸 Screenshot saved');

    // Analyze results
    console.log(`\n\n${'═'.repeat(100)}`);
    console.log('📊 ICON FIX VERIFICATION RESULTS');
    console.log('═'.repeat(100));

    console.log(`\n📊 Total Console Messages: ${results.allConsoleMessages.length}`);
    console.log(`📊 Icon-Related Warnings: ${results.iconWarnings.length}`);

    if (results.iconWarnings.length === 0) {
      console.log('\n✅ SUCCESS - NO ICON WARNINGS FOUND!');
      console.log('The ICON_MAP fix has successfully resolved all React icon warnings.');
      results.testPassed = true;
    } else {
      console.log('\n❌ FAILURE - ICON WARNINGS STILL PRESENT:');
      results.iconWarnings.forEach((warning, i) => {
        console.log(`   ${i + 1}. ${warning}`);
      });
    }

    // Show summary of all console messages by type
    const messagesByType = results.allConsoleMessages.reduce((acc, msg) => {
      acc[msg.type] = (acc[msg.type] || 0) + 1;
      return acc;
    }, {});

    console.log('\n📊 Console Message Summary:');
    Object.entries(messagesByType).forEach(([type, count]) => {
      console.log(`   ${type}: ${count}`);
    });

    console.log(`\n${'═'.repeat(100)}\n`);

    // Save results
    const fs = require('fs');
    fs.writeFileSync('test-results/icon-fix-verification.json', JSON.stringify(results, null, 2));
    console.log('📄 Results saved to test-results/icon-fix-verification.json\n');

  } catch (error) {
    console.error('\n❌ Fatal error during testing:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
  }

  return results.testPassed;
}

// Run the verification
verifyIconFix()
  .then((passed) => {
    if (passed) {
      console.log('🎉 ICON FIX VERIFIED - ALL TESTS PASSED');
      process.exit(0);
    } else {
      console.log('⚠️ ICON FIX VERIFICATION FAILED - SEE DETAILS ABOVE');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
