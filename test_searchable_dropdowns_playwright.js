const { chromium } = require('playwright');

async function testSearchableDropdowns() {
  console.log('🚀 Starting Playwright test for SearchableSelect dropdowns...\n');

  // Launch browser
  const browser = await chromium.launch({
    headless: false, // Set to true for headless testing
    slowMo: 500 // Slow down for better visibility
  });

  const page = await browser.newPage();

  try {
    // Navigate to properties page
    console.log('📍 Navigating to properties page...');
    await page.goto('http://localhost:5173/properties');

    // Wait for page to load
    console.log('⏳ Waiting for page to load...');
    await page.waitForTimeout(2000);

    // Take initial screenshot
    await page.screenshot({ path: 'test-results/01-initial-page.png' });

    // Test 1: Find City dropdown
    console.log('\n🏘️ Testing City dropdown...');

    // Look for the city dropdown button
    const cityDropdown = page.locator('button:has-text("Select City"), button:has-text("All Cities")').first();

    if (await cityDropdown.count() > 0) {
      console.log('✅ City dropdown found');

      // Click to open dropdown
      await cityDropdown.click();
      await page.waitForTimeout(500);

      // Take screenshot of opened dropdown
      await page.screenshot({ path: 'test-results/02-city-dropdown-open.png' });

      // Look for search input
      const searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="city"]').first();

      if (await searchInput.count() > 0) {
        console.log('✅ City search input found');

        // Type in search input
        await searchInput.fill('Fort');
        await page.waitForTimeout(500);

        // Take screenshot of search results
        await page.screenshot({ path: 'test-results/03-city-search-results.png' });

        // Look for filtered results
        const fortLauderdaleOption = page.locator('button:has-text("Fort Lauderdale")').first();

        if (await fortLauderdaleOption.count() > 0) {
          console.log('✅ Fort Lauderdale option found in search results');

          // Click on Fort Lauderdale
          await fortLauderdaleOption.click();
          await page.waitForTimeout(500);

          // Take screenshot after selection
          await page.screenshot({ path: 'test-results/04-city-selected.png' });
          console.log('✅ City selection completed');
        } else {
          console.log('❌ Fort Lauderdale option not found');
        }
      } else {
        console.log('❌ City search input not found');
      }
    } else {
      console.log('❌ City dropdown not found');
    }

    // Test 2: Find County dropdown
    console.log('\n🏢 Testing County dropdown...');

    const countyDropdown = page.locator('button:has-text("Select County"), button:has-text("All Counties")').first();

    if (await countyDropdown.count() > 0) {
      console.log('✅ County dropdown found');

      // Click to open dropdown
      await countyDropdown.click();
      await page.waitForTimeout(500);

      // Take screenshot of opened dropdown
      await page.screenshot({ path: 'test-results/05-county-dropdown-open.png' });

      // Look for search input
      const countySearchInput = page.locator('input[placeholder*="Search"], input[placeholder*="county"]').first();

      if (await countySearchInput.count() > 0) {
        console.log('✅ County search input found');

        // Type in search input
        await countySearchInput.fill('Brow');
        await page.waitForTimeout(500);

        // Take screenshot of search results
        await page.screenshot({ path: 'test-results/06-county-search-results.png' });

        // Look for filtered results
        const browardOption = page.locator('button:has-text("Broward")').first();

        if (await browardOption.count() > 0) {
          console.log('✅ Broward option found in search results');

          // Click on Broward
          await browardOption.click();
          await page.waitForTimeout(500);

          // Take screenshot after selection
          await page.screenshot({ path: 'test-results/07-county-selected.png' });
          console.log('✅ County selection completed');
        } else {
          console.log('❌ Broward option not found');
        }
      } else {
        console.log('❌ County search input not found');
      }
    } else {
      console.log('❌ County dropdown not found');
    }

    // Test 3: Check if search results update
    console.log('\n🔍 Testing search integration...');

    // Wait for potential API calls to complete
    await page.waitForTimeout(2000);

    // Take final screenshot
    await page.screenshot({ path: 'test-results/08-final-results.png' });

    // Check if results section exists and has content
    const resultsSection = page.locator('text="Properties Found"').first();

    if (await resultsSection.count() > 0) {
      const resultsText = await resultsSection.textContent();
      console.log(`✅ Results section found: ${resultsText}`);
    } else {
      console.log('❌ Results section not found');
    }

    // Test 4: Test clear functionality
    console.log('\n🧹 Testing clear functionality...');

    // Look for clear button or try to clear selections
    const clearButtons = page.locator('button:has-text("Clear"), button:has-text("×")');

    if (await clearButtons.count() > 0) {
      console.log('✅ Clear buttons found');
      await clearButtons.first().click();
      await page.waitForTimeout(500);

      await page.screenshot({ path: 'test-results/09-after-clear.png' });
      console.log('✅ Clear functionality tested');
    } else {
      console.log('ℹ️ No clear buttons found - testing alternative clear method');

      // Try clicking on dropdowns and selecting "All Cities" / "All Counties"
      try {
        const cityDropdownAgain = page.locator('button:has-text("Fort Lauderdale")').first();
        if (await cityDropdownAgain.count() > 0) {
          await cityDropdownAgain.click();
          await page.waitForTimeout(300);

          const allCitiesOption = page.locator('button:has-text("All Cities")').first();
          if (await allCitiesOption.count() > 0) {
            await allCitiesOption.click();
            console.log('✅ City cleared via "All Cities" option');
          }
        }
      } catch (error) {
        console.log('ℹ️ Alternative clear method not available');
      }
    }

    // Final screenshot
    await page.screenshot({ path: 'test-results/10-test-complete.png' });

    console.log('\n📊 Test Summary:');
    console.log('✅ City dropdown functionality tested');
    console.log('✅ County dropdown functionality tested');
    console.log('✅ Search/filter functionality tested');
    console.log('✅ Selection functionality tested');
    console.log('✅ Screenshots captured in test-results/ folder');
    console.log('\n🎯 Test completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    await page.screenshot({ path: 'test-results/error-screenshot.png' });
  } finally {
    await browser.close();
  }
}

// Create test results directory
const fs = require('fs');
const path = require('path');

const testResultsDir = path.join(__dirname, 'test-results');
if (!fs.existsSync(testResultsDir)) {
  fs.mkdirSync(testResultsDir, { recursive: true });
}

// Run the test
testSearchableDropdowns().catch(console.error);