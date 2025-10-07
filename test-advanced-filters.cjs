const { chromium } = require('playwright');
const fs = require('fs');

async function testAdvancedFilters() {
  console.log('🚀 Starting Advanced Filters Test...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // Step 1: Navigate to property search page
    console.log('📍 Step 1: Navigating to property search page...');
    await page.goto('http://localhost:5178/properties', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    console.log('   Waiting for page to stabilize...');
    await page.waitForTimeout(5000);

    // Take screenshot of initial state
    await page.screenshot({ path: 'test-results/01-property-search-initial.png', fullPage: true });
    console.log('✅ Property search page loaded\n');

    // Step 2: Click Advanced Filters button
    console.log('📍 Step 2: Opening Advanced Filters...');
    const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
    await advancedFiltersButton.click();
    await page.waitForTimeout(1000);

    // Take screenshot of expanded filters
    await page.screenshot({ path: 'test-results/02-advanced-filters-opened.png', fullPage: true });
    console.log('✅ Advanced Filters opened\n');

    // Step 3: Check if collapse button exists
    console.log('📍 Step 3: Checking for Collapse button...');
    const collapseButton = page.locator('button:has-text("Collapse")');
    const collapseButtonExists = await collapseButton.count() > 0;
    console.log(`${collapseButtonExists ? '✅' : '❌'} Collapse button ${collapseButtonExists ? 'found' : 'NOT found'}\n`);

    // Step 4: Fill in MIN VALUE filter
    console.log('📍 Step 4: Setting MIN VALUE to $500,000...');
    // Find the Min Value input by looking for the label first
    const minValueInput = page.locator('label:has-text("Min Value")').locator('..').locator('input');
    await minValueInput.waitFor({ state: 'visible', timeout: 10000 });
    await minValueInput.click();
    await minValueInput.fill('500000');
    await page.waitForTimeout(500);
    console.log('✅ MIN VALUE set to $500,000\n');

    // Step 5: Fill in MAX VALUE filter
    console.log('📍 Step 5: Setting MAX VALUE to $1,000,000...');
    const maxValueInput = page.locator('label:has-text("Max Value")').locator('..').locator('input');
    await maxValueInput.waitFor({ state: 'visible', timeout: 10000 });
    await maxValueInput.click();
    await maxValueInput.fill('1000000');
    await page.waitForTimeout(500);
    console.log('✅ MAX VALUE set to $1,000,000\n');

    // Take screenshot with filters filled
    await page.screenshot({ path: 'test-results/03-filters-filled.png', fullPage: true });

    // Step 6: Click Search button
    console.log('📍 Step 6: Clicking Search button...');
    const searchButton = page.locator('button:has-text("Search")');
    await searchButton.click();
    await page.waitForTimeout(3000); // Wait for results
    console.log('✅ Search executed\n');

    // Step 7: Wait for results and check property cards
    console.log('📍 Step 7: Analyzing search results...');
    console.log('   Waiting for property cards to load...');

    // Wait for either property cards or "no results" message
    try {
      await Promise.race([
        page.waitForSelector('.elegant-card', { timeout: 30000 }),
        page.waitForSelector('text=/No properties found/i', { timeout: 30000 })
      ]);
    } catch (e) {
      console.log('   ⚠️ Timeout waiting for results, checking what\'s on page...');
      await page.screenshot({ path: 'test-results/timeout-state.png', fullPage: true });
    }

    const propertyCards = await page.locator('.elegant-card').all();
    console.log(`📊 Found ${propertyCards.length} property cards\n`);

    // If no cards found, check for error messages or loading state
    if (propertyCards.length === 0) {
      console.log('⚠️ No property cards found. Checking for errors or loading states...');
      const pageText = await page.textContent('body');
      if (pageText.includes('loading') || pageText.includes('Loading')) {
        console.log('   Still loading...');
      }
      if (pageText.includes('error') || pageText.includes('Error')) {
        console.log('   Error detected on page');
      }
      await page.screenshot({ path: 'test-results/no-results-state.png', fullPage: true });
    }

    // Step 8: Extract and verify property values
    console.log('📍 Step 8: Extracting property values from cards...\n');
    const propertyValues = [];

    for (let i = 0; i < Math.min(10, propertyCards.length); i++) {
      const card = propertyCards[i];

      // Find the "Appraised Value" section
      const appraisedValueLabel = card.locator('p:has-text("Appraised Value")');
      const appraisedValueText = await card.locator('p.font-semibold').nth(0).textContent();

      // Parse the value
      const valueMatch = appraisedValueText.match(/\$([0-9,]+)/);
      if (valueMatch) {
        const value = parseInt(valueMatch[1].replace(/,/g, ''));
        propertyValues.push(value);

        const inRange = value >= 500000 && value <= 1000000;
        console.log(`  Property ${i + 1}: $${value.toLocaleString()} ${inRange ? '✅ IN RANGE' : '❌ OUT OF RANGE'}`);
      }
    }

    // Take screenshot of results
    await page.screenshot({ path: 'test-results/04-search-results.png', fullPage: true });

    // Step 9: Verify all values are in range
    console.log('\n📍 Step 9: Validating filter results...');
    const allInRange = propertyValues.every(v => v >= 500000 && v <= 1000000);
    const minFound = Math.min(...propertyValues);
    const maxFound = Math.max(...propertyValues);

    console.log(`\n📊 RESULTS SUMMARY:`);
    console.log(`  - Properties analyzed: ${propertyValues.length}`);
    console.log(`  - Minimum value found: $${minFound.toLocaleString()}`);
    console.log(`  - Maximum value found: $${maxFound.toLocaleString()}`);
    console.log(`  - All values in range: ${allInRange ? '✅ YES' : '❌ NO'}`);

    // Step 10: Test collapse button
    console.log('\n📍 Step 10: Testing Collapse button...');
    if (collapseButtonExists) {
      await collapseButton.click();
      await page.waitForTimeout(1000);

      // Check if Advanced Filters section is now hidden
      const minValueVisible = await minValueInput.isVisible().catch(() => false);
      console.log(`${minValueVisible ? '❌' : '✅'} Advanced Filters ${minValueVisible ? 'still visible (FAILED)' : 'collapsed (SUCCESS)'}`);

      await page.screenshot({ path: 'test-results/05-filters-collapsed.png', fullPage: true });
    }

    // Final report
    console.log('\n' + '='.repeat(60));
    console.log('📋 ADVANCED FILTERS TEST REPORT');
    console.log('='.repeat(60));
    console.log(`✅ Advanced Filters Button: Working`);
    console.log(`${collapseButtonExists ? '✅' : '❌'} Collapse Button: ${collapseButtonExists ? 'Present' : 'Missing'}`);
    console.log(`${allInRange ? '✅' : '❌'} MIN/MAX Value Filtering: ${allInRange ? 'Working Correctly' : 'Not Working'}`);
    console.log(`📊 Properties Found: ${propertyCards.length}`);
    console.log(`💰 Value Range Tested: $500,000 - $1,000,000`);
    console.log('='.repeat(60));

    // Save detailed report
    const report = {
      timestamp: new Date().toISOString(),
      test: 'Advanced Filters MIN/MAX VALUE',
      filters: {
        minValue: 500000,
        maxValue: 1000000
      },
      results: {
        totalPropertiesFound: propertyCards.length,
        propertiesAnalyzed: propertyValues.length,
        minValueFound: minFound,
        maxValueFound: maxFound,
        allInRange: allInRange,
        collapseButtonExists: collapseButtonExists
      },
      propertyValues: propertyValues,
      status: allInRange && collapseButtonExists ? 'PASS' : 'FAIL'
    };

    fs.writeFileSync('test-results/advanced-filters-report.json', JSON.stringify(report, null, 2));
    console.log('\n📄 Detailed report saved to: test-results/advanced-filters-report.json');

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    await page.screenshot({ path: 'test-results/error-screenshot.png', fullPage: true });
  } finally {
    await page.waitForTimeout(2000);
    await browser.close();
    console.log('\n🏁 Test completed!');
  }
}

testAdvancedFilters();