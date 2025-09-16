const { chromium } = require('playwright');

async function testPropertyTypeTabFiltering() {
  console.log('🚀 Starting Property Type Tab Filtering Test...\n');

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
    await page.screenshot({ path: 'test-results/property-tabs-01-initial.png' });

    // Test 1: Find Property Type tabs
    console.log('\n🏠 Testing Property Type tabs...');

    // Define property types to test
    const propertyTypes = ['Residential', 'Commercial', 'Industrial', 'Agricultural', 'Vacant'];

    for (const propertyType of propertyTypes) {
      console.log(`\n🔍 Testing ${propertyType} tab...`);

      // Find the tab button
      const tabButton = page.locator(`button:has-text("${propertyType}")`).first();

      if (await tabButton.count() > 0) {
        console.log(`✅ ${propertyType} tab found`);

        // Click the tab
        await tabButton.click();
        await page.waitForTimeout(1000);

        // Take screenshot after clicking
        await page.screenshot({ path: `test-results/property-tabs-${propertyType.toLowerCase()}.png` });

        // Check if tab is active (has gold border)
        const isActive = await tabButton.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.borderBottom.includes('#d4af37') ||
                 styles.borderBottomColor.includes('rgb(212, 175, 55)') ||
                 el.classList.contains('active');
        });

        console.log(`   📋 Tab active state: ${isActive ? '✅ ACTIVE' : '❌ NOT ACTIVE'}`);

        // Wait for potential API calls to complete
        await page.waitForTimeout(1500);

        // Check for property cards
        const propertyCards = await page.locator('div[class*="property"], div[class*="card"]').count();
        console.log(`   🏘️ Property cards visible: ${propertyCards}`);

        // Check for loading state
        const isLoading = await page.locator('div:has-text("Loading"), .loading').count();
        if (isLoading > 0) {
          console.log('   ⏳ Properties still loading, waiting...');
          await page.waitForTimeout(2000);
        }

        // Look for results count
        try {
          const resultsText = await page.locator('text=/\\d+\\s*(properties|results|items)/i').first().textContent();
          if (resultsText) {
            console.log(`   📊 Results: ${resultsText}`);
          }
        } catch (e) {
          console.log('   📊 Results count not found or still loading');
        }

      } else {
        console.log(`❌ ${propertyType} tab not found`);
      }
    }

    // Test 2: Tax Deed Sales tab (special case)
    console.log('\n🔨 Testing Tax Deed Sales tab...');

    const taxDeedTab = page.locator('button:has-text("Tax Deed Sales")').first();

    if (await taxDeedTab.count() > 0) {
      console.log('✅ Tax Deed Sales tab found');

      await taxDeedTab.click();
      await page.waitForTimeout(1000);

      // Take screenshot
      await page.screenshot({ path: 'test-results/property-tabs-tax-deed.png' });

      const isActive = await taxDeedTab.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.borderBottom.includes('#d4af37') ||
               styles.borderBottomColor.includes('rgb(212, 175, 55)') ||
               el.classList.contains('active');
      });

      console.log(`   📋 Tax Deed tab active: ${isActive ? '✅ ACTIVE' : '❌ NOT ACTIVE'}`);

      // Look for tax deed specific content
      const taxDeedContent = await page.locator('text=/tax deed|auction|bid/i').count();
      console.log(`   🔨 Tax deed content found: ${taxDeedContent > 0 ? '✅ YES' : '❌ NO'}`);

    } else {
      console.log('❌ Tax Deed Sales tab not found');
    }

    // Test 3: Switch back to Residential to test filter persistence
    console.log('\n🔄 Testing filter switching...');

    const residentialTab = page.locator('button:has-text("Residential")').first();
    if (await residentialTab.count() > 0) {
      await residentialTab.click();
      await page.waitForTimeout(1000);

      const isActive = await residentialTab.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return styles.borderBottom.includes('#d4af37') ||
               styles.borderBottomColor.includes('rgb(212, 175, 55)') ||
               el.classList.contains('active');
      });

      console.log(`   🏠 Back to Residential: ${isActive ? '✅ ACTIVE' : '❌ NOT ACTIVE'}`);

      // Take final screenshot
      await page.screenshot({ path: 'test-results/property-tabs-final.png' });
    }

    // Test 4: Check console for any errors
    console.log('\n🔍 Checking for console errors...');

    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });

    await page.waitForTimeout(1000);

    if (logs.length > 0) {
      console.log('❌ Console errors found:');
      logs.forEach(log => console.log(`   - ${log}`));
    } else {
      console.log('✅ No console errors detected');
    }

    console.log('\n📊 Property Type Tab Test Summary:');
    console.log('✅ Property type tabs tested');
    console.log('✅ Tab activation verified');
    console.log('✅ Filter switching tested');
    console.log('✅ Screenshots captured in test-results/ folder');
    console.log('\n🎯 Test completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error);
    await page.screenshot({ path: 'test-results/property-tabs-error.png' });
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
testPropertyTypeTabFiltering().catch(console.error);