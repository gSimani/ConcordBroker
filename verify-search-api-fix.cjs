/**
 * VERIFY SEARCH API FIX - Check that 404 error is gone
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5191';

async function verifySearchAPIFix() {
  console.log('🔍 VERIFYING SEARCH API FIX\n');
  console.log('═'.repeat(100));

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    searchAPIErrors: [],
    allErrors: [],
    testPassed: false
  };

  try {
    // Capture console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        results.allErrors.push(text);

        // Look for search API errors
        if (text.includes('Search failed') || text.includes('404')) {
          results.searchAPIErrors.push(text);
        }
      }
    });

    // Navigate to properties page
    console.log('\n📊 STEP 1: Navigate to Properties Page');
    console.log('-'.repeat(100));

    await page.goto(`${BASE_URL}/properties`, { waitUntil: 'networkidle', timeout: 60000 });
    console.log('✅ Page loaded');

    // Wait for initial load
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-screenshots/search-api-fix-verification.png', fullPage: false });
    console.log('📸 Screenshot saved');

    // Analyze results
    console.log(`\n\n${'═'.repeat(100)}`);
    console.log('📊 SEARCH API FIX VERIFICATION RESULTS');
    console.log('═'.repeat(100));

    console.log(`\n📊 Total Errors: ${results.allErrors.length}`);
    console.log(`📊 Search API 404 Errors: ${results.searchAPIErrors.length}`);

    if (results.searchAPIErrors.length === 0) {
      console.log('\n✅ SUCCESS - NO SEARCH API 404 ERRORS!');
      console.log('The endpoint fix has successfully resolved the Search API 404 error.');
      results.testPassed = true;
    } else {
      console.log('\n❌ FAILURE - SEARCH API ERRORS STILL PRESENT:');
      results.searchAPIErrors.forEach((error, i) => {
        console.log(`   ${i + 1}. ${error}`);
      });
    }

    if (results.allErrors.length > 0) {
      console.log('\n📊 Other console errors present:');
      results.allErrors.slice(0, 5).forEach((error, i) => {
        console.log(`   ${i + 1}. ${error.substring(0, 100)}...`);
      });
      if (results.allErrors.length > 5) {
        console.log(`   ... and ${results.allErrors.length - 5} more`);
      }
    }

    console.log(`\n${'═'.repeat(100)}\n`);

    // Save results
    const fs = require('fs');
    fs.writeFileSync('test-results/search-api-fix-verification.json', JSON.stringify(results, null, 2));
    console.log('📄 Results saved to test-results/search-api-fix-verification.json\n');

  } catch (error) {
    console.error('\n❌ Fatal error during testing:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
  }

  return results.testPassed;
}

// Run the verification
verifySearchAPIFix()
  .then((passed) => {
    if (passed) {
      console.log('🎉 SEARCH API FIX VERIFIED - TEST PASSED');
      process.exit(0);
    } else {
      console.log('⚠️ SEARCH API FIX VERIFICATION FAILED - SEE DETAILS ABOVE');
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
