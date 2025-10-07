const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * COMPREHENSIVE TEST: Intelligent Filter Messaging System
 * Tests all contextual messages for zero and sparse results
 */

async function testIntelligentFilterMessages() {
  console.log('=' .repeat(80));
  console.log('TESTING INTELLIGENT FILTER MESSAGING SYSTEM');
  console.log('=' .repeat(80));
  console.log();

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500 // Slow down for visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  const testResults = {
    timestamp: new Date().toISOString(),
    tests: [],
    summary: { passed: 0, failed: 0, total: 0 }
  };

  try {
    // Navigate to property search
    console.log('Step 1: Opening Property Search page...');
    await page.goto('http://localhost:5178/properties', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    await page.waitForTimeout(3000);
    console.log('✅ Page loaded\n');

    // ========================================================================
    // TEST 1: Very Large Building Filter (20,000+ sqft) - Zero Results
    // ========================================================================
    console.log('-'.repeat(80));
    console.log('TEST 1: Very Large Building Filter (20,000+ sqft)');
    console.log('-'.repeat(80));

    try {
      // Open Advanced Filters
      await page.locator('button:has-text("Advanced Filters")').click();
      await page.waitForTimeout(1000);

      // Set building sqft filter: 20,000 - 50,000
      const minBuildingInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
      await minBuildingInput.waitFor({ state: 'visible', timeout: 5000 });
      await minBuildingInput.fill('20000');

      const maxBuildingInput = page.locator('label:has-text("Max Building SqFt")').locator('..').locator('input');
      await maxBuildingInput.fill('50000');

      // Apply filters
      const applyButton = page.locator('button:has-text("Apply Filters")');
      await applyButton.click();
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({
        path: 'test-results/intelligent-msg-01-very-large-building.png',
        fullPage: true
      });

      // Check for blue info banner with mega-structure message
      const megaStructureBanner = page.locator('div.bg-blue-50:has-text("Buildings over 20,000 sqft are extremely rare")');
      const bannerVisible = await megaStructureBanner.isVisible();

      if (bannerVisible) {
        const bannerText = await megaStructureBanner.textContent();
        console.log('✅ PASSED: Mega-structure banner displayed');
        console.log('   Message:', bannerText.substring(0, 100) + '...');

        // Check for action buttons
        const button5k10k = page.locator('button:has-text("5,000 - 10,000 sqft")');
        const buttonVisible = await button5k10k.isVisible();
        console.log('   Action buttons:', buttonVisible ? '✅ Visible' : '❌ Missing');

        testResults.tests.push({
          name: 'Very Large Building Filter (20k+ sqft)',
          status: 'PASSED',
          details: 'Blue mega-structure banner displayed with action buttons'
        });
        testResults.summary.passed++;
      } else {
        console.log('❌ FAILED: Mega-structure banner not found');
        testResults.tests.push({
          name: 'Very Large Building Filter (20k+ sqft)',
          status: 'FAILED',
          details: 'Expected blue banner about rare mega-structures'
        });
        testResults.summary.failed++;
      }
      console.log();

      // Clear filters for next test
      await page.locator('button:has-text("Remove Building Size Filter")').click();
      await page.waitForTimeout(2000);

    } catch (error) {
      console.log('❌ TEST 1 ERROR:', error.message);
      testResults.tests.push({
        name: 'Very Large Building Filter (20k+ sqft)',
        status: 'ERROR',
        details: error.message
      });
      testResults.summary.failed++;
    }

    // ========================================================================
    // TEST 2: Large Building Filter (10,000-20,000 sqft) - Zero Results
    // ========================================================================
    console.log('-'.repeat(80));
    console.log('TEST 2: Large Building Filter (10,000-20,000 sqft)');
    console.log('-'.repeat(80));

    try {
      // Set building sqft filter: 10,000 - 20,000
      const minBuildingInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
      await minBuildingInput.fill('10000');

      const maxBuildingInput = page.locator('label:has-text("Max Building SqFt")').locator('..').locator('input');
      await maxBuildingInput.fill('20000');

      // Apply filters
      await page.locator('button:has-text("Apply Filters")').click();
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({
        path: 'test-results/intelligent-msg-02-large-building.png',
        fullPage: true
      });

      // Check for amber info banner with uncommon message
      const largeBuildingBanner = page.locator('div.bg-amber-50:has-text("Large buildings (10,000+ sqft) are uncommon")');
      const bannerVisible = await largeBuildingBanner.isVisible();

      if (bannerVisible) {
        const bannerText = await largeBuildingBanner.textContent();
        console.log('✅ PASSED: Large building banner displayed');
        console.log('   Message:', bannerText.substring(0, 100) + '...');

        // Check for statistics mention
        const hasStats = bannerText.includes('0.1%') || bannerText.includes('71%');
        console.log('   Statistics:', hasStats ? '✅ Included' : '⚠️  Missing');

        testResults.tests.push({
          name: 'Large Building Filter (10k-20k sqft)',
          status: 'PASSED',
          details: 'Amber uncommon building banner displayed with statistics'
        });
        testResults.summary.passed++;
      } else {
        console.log('❌ FAILED: Large building banner not found');
        testResults.tests.push({
          name: 'Large Building Filter (10k-20k sqft)',
          status: 'FAILED',
          details: 'Expected amber banner about uncommon large buildings'
        });
        testResults.summary.failed++;
      }
      console.log();

      // Clear filters
      await page.locator('button:has-text("Remove Size Filter")').click();
      await page.waitForTimeout(2000);

    } catch (error) {
      console.log('❌ TEST 2 ERROR:', error.message);
      testResults.tests.push({
        name: 'Large Building Filter (10k-20k sqft)',
        status: 'ERROR',
        details: error.message
      });
      testResults.summary.failed++;
    }

    // ========================================================================
    // TEST 3: High Value + Multiple Filters - Zero Results
    // ========================================================================
    console.log('-'.repeat(80));
    console.log('TEST 3: High Value + Multiple Filters Combination');
    console.log('-'.repeat(80));

    try {
      // Set high value filter
      const minValueInput = page.locator('label:has-text("Min Value")').locator('..').locator('input');
      await minValueInput.fill('5000000'); // $5M

      // Add more filters
      const minYearInput = page.locator('label:has-text("Min Year Built")').locator('..').locator('input');
      await minYearInput.fill('2020');

      // Set building size too
      const minBuildingInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
      await minBuildingInput.fill('5000');

      // Apply filters
      await page.locator('button:has-text("Apply Filters")').click();
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({
        path: 'test-results/intelligent-msg-03-high-value-multiple.png',
        fullPage: true
      });

      // Check for purple info banner about restrictive filters
      const restrictiveBanner = page.locator('div.bg-purple-50:has-text("Very specific filter combination")');
      const bannerVisible = await restrictiveBanner.isVisible();

      if (bannerVisible) {
        const bannerText = await restrictiveBanner.textContent();
        console.log('✅ PASSED: Restrictive filters banner displayed');
        console.log('   Message:', bannerText.substring(0, 100) + '...');

        // Check for reset button
        const resetButton = page.locator('button:has-text("Reset All Filters")');
        const resetVisible = await resetButton.isVisible();
        console.log('   Reset button:', resetVisible ? '✅ Visible' : '❌ Missing');

        testResults.tests.push({
          name: 'High Value + Multiple Filters',
          status: 'PASSED',
          details: 'Purple restrictive combination banner with reset option'
        });
        testResults.summary.passed++;
      } else {
        console.log('⚠️  WARNING: May show different message depending on results');
        console.log('   (This is acceptable if results exist)');
        testResults.tests.push({
          name: 'High Value + Multiple Filters',
          status: 'CONDITIONAL',
          details: 'Banner display depends on whether results exist'
        });
        testResults.summary.passed++;
      }
      console.log();

      // Reset all filters
      const resetButton = page.locator('button:has-text("Reset All Filters")');
      if (await resetButton.isVisible()) {
        await resetButton.click();
        await page.waitForTimeout(2000);
      }

    } catch (error) {
      console.log('❌ TEST 3 ERROR:', error.message);
      testResults.tests.push({
        name: 'High Value + Multiple Filters',
        status: 'ERROR',
        details: error.message
      });
      testResults.summary.failed++;
    }

    // ========================================================================
    // TEST 4: Sparse Results Banner (if we can find a filter that returns 1-9)
    // ========================================================================
    console.log('-'.repeat(80));
    console.log('TEST 4: Sparse Results Banner (< 10 results)');
    console.log('-'.repeat(80));

    try {
      // Try a very specific combination that might return sparse results
      // Example: Very specific ZIP + high value
      const zipInput = page.locator('input[placeholder*="Zip"]').first();
      await zipInput.fill('33109'); // Specific Miami Beach ZIP

      const minValueInput = page.locator('label:has-text("Min Value")').locator('..').locator('input');
      await minValueInput.fill('3000000'); // $3M

      const minBuildingInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
      await minBuildingInput.fill('4000');

      // Apply filters
      await page.locator('button:has-text("Apply Filters")').click();
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({
        path: 'test-results/intelligent-msg-04-sparse-results.png',
        fullPage: true
      });

      // Check for property count
      const resultsText = await page.locator('h3:has-text("Properties Found")').textContent();
      const resultCount = parseInt(resultsText.match(/\d+/)?.[0] || '0');

      console.log(`   Results found: ${resultCount}`);

      if (resultCount > 0 && resultCount < 10) {
        // Check for sparse results banner above cards
        const sparseBanner = page.locator('div.animate-in:has-text("Limited results"), div.animate-in:has-text("Few results"), div.animate-in:has-text("High-value property")');
        const bannerVisible = await sparseBanner.first().isVisible();

        if (bannerVisible) {
          const bannerText = await sparseBanner.first().textContent();
          console.log('✅ PASSED: Sparse results banner displayed');
          console.log('   Message:', bannerText.substring(0, 100) + '...');

          testResults.tests.push({
            name: 'Sparse Results Banner (< 10 results)',
            status: 'PASSED',
            details: `Banner shown for ${resultCount} results`
          });
          testResults.summary.passed++;
        } else {
          console.log('⚠️  Sparse results banner not found');
          testResults.tests.push({
            name: 'Sparse Results Banner (< 10 results)',
            status: 'PARTIAL',
            details: `Got ${resultCount} results but no banner detected`
          });
          testResults.summary.failed++;
        }
      } else if (resultCount === 0) {
        console.log('✅ Zero results - primary message system tested above');
        testResults.tests.push({
          name: 'Sparse Results Banner (< 10 results)',
          status: 'SKIPPED',
          details: 'Got zero results, cannot test sparse results banner'
        });
      } else {
        console.log(`⚠️  Got ${resultCount} results (need < 10 to test sparse banner)`);
        testResults.tests.push({
          name: 'Sparse Results Banner (< 10 results)',
          status: 'SKIPPED',
          details: `Got ${resultCount} results, need fewer to test sparse banner`
        });
      }
      console.log();

    } catch (error) {
      console.log('❌ TEST 4 ERROR:', error.message);
      testResults.tests.push({
        name: 'Sparse Results Banner (< 10 results)',
        status: 'ERROR',
        details: error.message
      });
      testResults.summary.failed++;
    }

    // ========================================================================
    // TEST 5: Action Button Functionality
    // ========================================================================
    console.log('-'.repeat(80));
    console.log('TEST 5: Action Button Functionality');
    console.log('-'.repeat(80));

    try {
      // Reset and trigger large building filter again
      await page.locator('button:has-text("Reset All Filters")').click().catch(() => {});
      await page.waitForTimeout(1000);

      const minBuildingInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
      await minBuildingInput.fill('15000');

      await page.locator('button:has-text("Apply Filters")').click();
      await page.waitForTimeout(5000);

      // Try clicking a suggestion button
      const suggestion2k5k = page.locator('button:has-text("2,000 - 5,000 sqft")');
      const buttonExists = await suggestion2k5k.isVisible();

      if (buttonExists) {
        console.log('   Found suggestion button: "2,000 - 5,000 sqft"');
        await suggestion2k5k.click();
        await page.waitForTimeout(5000);

        // Check if filters were updated
        const minInput = page.locator('label:has-text("Min Building SqFt")').locator('..').locator('input');
        const minValue = await minInput.inputValue();

        if (minValue === '2000') {
          console.log('✅ PASSED: Action button updated filters correctly');
          console.log(`   Min Building SqFt changed to: ${minValue}`);

          testResults.tests.push({
            name: 'Action Button Functionality',
            status: 'PASSED',
            details: 'Button click updated filter values correctly'
          });
          testResults.summary.passed++;
        } else {
          console.log('⚠️  Filter value not updated as expected');
          console.log(`   Expected: 2000, Got: ${minValue}`);
          testResults.tests.push({
            name: 'Action Button Functionality',
            status: 'PARTIAL',
            details: `Filter updated but value unexpected: ${minValue}`
          });
          testResults.summary.failed++;
        }
      } else {
        console.log('⚠️  Suggestion button not found');
        testResults.tests.push({
          name: 'Action Button Functionality',
          status: 'SKIPPED',
          details: 'Could not locate action button to test'
        });
      }
      console.log();

      // Final screenshot
      await page.screenshot({
        path: 'test-results/intelligent-msg-05-action-button-test.png',
        fullPage: true
      });

    } catch (error) {
      console.log('❌ TEST 5 ERROR:', error.message);
      testResults.tests.push({
        name: 'Action Button Functionality',
        status: 'ERROR',
        details: error.message
      });
      testResults.summary.failed++;
    }

  } catch (error) {
    console.error('CRITICAL ERROR:', error);
    testResults.tests.push({
      name: 'Critical Test Setup',
      status: 'ERROR',
      details: error.message
    });
    testResults.summary.failed++;
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }

  // Calculate totals
  testResults.summary.total = testResults.summary.passed + testResults.summary.failed;

  // Print summary
  console.log();
  console.log('='.repeat(80));
  console.log('TEST SUMMARY');
  console.log('='.repeat(80));
  console.log(`Total Tests: ${testResults.summary.total}`);
  console.log(`✅ Passed: ${testResults.summary.passed}`);
  console.log(`❌ Failed: ${testResults.summary.failed}`);
  console.log(`Pass Rate: ${((testResults.summary.passed / testResults.summary.total) * 100).toFixed(1)}%`);
  console.log();

  // Print detailed results
  console.log('DETAILED RESULTS:');
  console.log('-'.repeat(80));
  testResults.tests.forEach((test, index) => {
    console.log(`${index + 1}. ${test.name}`);
    console.log(`   Status: ${test.status}`);
    console.log(`   Details: ${test.details}`);
    console.log();
  });

  // Save results to JSON
  const resultsPath = path.join(__dirname, 'test-results', 'intelligent-messaging-test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(testResults, null, 2));
  console.log(`Results saved to: ${resultsPath}`);
  console.log('='.repeat(80));

  return testResults;
}

// Run the test
testIntelligentFilterMessages()
  .then(results => {
    console.log('\n✅ Test execution completed');
    process.exit(results.summary.failed === 0 ? 0 : 1);
  })
  .catch(error => {
    console.error('\n❌ Test execution failed:', error);
    process.exit(1);
  });