const { chromium } = require('playwright');

async function testFiltersFixed() {
  console.log('🔧 Testing FIXED Min/Max Value Filters\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  try {
    // Navigate and open advanced filters
    console.log('📍 Step 1: Opening Advanced Filters...');
    await page.goto('http://localhost:5178/properties', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);

    const advancedFiltersButton = page.locator('button:has-text("Advanced Filters")');
    await advancedFiltersButton.click();
    await page.waitForTimeout(1000);
    console.log('✅ Advanced Filters opened\n');

    // Fill min and max values
    console.log('📍 Step 2: Setting filters...');
    const minValueInput = page.locator('label:has-text("Min Value")').locator('..').locator('input');
    await minValueInput.waitFor({ state: 'visible', timeout: 10000 });
    await minValueInput.fill('500000');

    const maxValueInput = page.locator('label:has-text("Max Value")').locator('..').locator('input');
    await maxValueInput.fill('1000000');
    console.log('✅ MIN: $500,000 | MAX: $1,000,000\n');

    await page.screenshot({ path: 'test-results/fixed-01-filters-set.png', fullPage: true });

    // Click Apply Filters
    console.log('📍 Step 3: Applying filters...');
    const applyButton = page.locator('button:has-text("Apply Filters")');
    await applyButton.click();
    await page.waitForTimeout(8000); // Wait longer for results
    console.log('✅ Filters applied\n');

    // Check results
    console.log('📍 Step 4: Checking results...');
    const propertyCards = await page.locator('.elegant-card').all();
    console.log(`📊 Found ${propertyCards.length} property cards\n`);

    if (propertyCards.length > 0) {
      console.log('📋 Analyzing property values:\n');
      const values = [];

      for (let i = 0; i < Math.min(10, propertyCards.length); i++) {
        const card = propertyCards[i];

        try {
          // Get the appraised value text
          const valueText = await card.locator('p:has-text("Appraised Value")').locator('..').locator('p.font-semibold').first().textContent();
          const match = valueText.match(/\$([0-9,]+)/);

          if (match) {
            const value = parseInt(match[1].replace(/,/g, ''));
            values.push(value);

            const inRange = value >= 500000 && value <= 1000000;
            console.log(`  ${i + 1}. $${value.toLocaleString().padStart(12)} ${inRange ? '✅ IN RANGE' : '❌ OUT OF RANGE'}`);
          }
        } catch (e) {
          console.log(`  ${i + 1}. Error reading value`);
        }
      }

      await page.screenshot({ path: 'test-results/fixed-02-results.png', fullPage: true });

      // Summary
      const allInRange = values.every(v => v >= 500000 && v <= 1000000);
      const minFound = Math.min(...values);
      const maxFound = Math.max(...values);

      console.log('\n' + '='.repeat(60));
      console.log('📊 RESULTS');
      console.log('='.repeat(60));
      console.log(`Properties displayed: ${propertyCards.length}`);
      console.log(`Values analyzed: ${values.length}`);
      console.log(`Min value found: $${minFound.toLocaleString()}`);
      console.log(`Max value found: $${maxFound.toLocaleString()}`);
      console.log(`All in range: ${allInRange ? '✅ YES' : '❌ NO'}`);
      console.log(`Filter Status: ${allInRange ? '✅ WORKING!' : '❌ NOT WORKING'}`);
      console.log('='.repeat(60));
    } else {
      console.log('❌ No property cards found - filters may have issue\n');
      await page.screenshot({ path: 'test-results/fixed-no-results.png', fullPage: true });
    }

  } catch (error) {
    console.error('❌ Test error:', error.message);
    await page.screenshot({ path: 'test-results/fixed-error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
    console.log('\n🏁 Test complete!');
  }
}

testFiltersFixed();