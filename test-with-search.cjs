const { chromium } = require('playwright');

async function testWithSearch() {
  console.log('Testing property search to find existing data...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  const page = await context.newPage();

  try {
    console.log('1. Navigating to http://localhost:5173/properties...');
    await page.goto('http://localhost:5173/properties');
    await page.waitForLoadState('networkidle');

    // Try clicking on suggested cities
    const cities = ['Fort Lauderdale', 'Hollywood', 'Pompano Beach'];

    for (const city of cities) {
      console.log(`2. Trying to click on ${city}...`);

      const cityButton = page.locator(`text="${city}"`);
      if (await cityButton.count() > 0) {
        await cityButton.click();
        console.log(`   Clicked on ${city}, waiting for results...`);

        await page.waitForTimeout(5000);

        // Check if properties loaded
        const propertiesCount = await page.locator('text=/\\d+ Properties Found/').textContent().catch(() => null);
        console.log(`   Properties found: ${propertiesCount || 'None'}`);

        if (propertiesCount && !propertiesCount.includes('0 Properties')) {
          console.log(`   Success! Found properties in ${city}`);

          // Take screenshot
          await page.screenshot({ path: `properties-${city.toLowerCase().replace(' ', '-')}.png`, fullPage: true });

          // Look for property cards
          await page.waitForTimeout(3000);
          const propertyCards = await page.locator('div[class*="card"], div[class*="property"], [data-testid*="property"]').all();
          console.log(`   Found ${propertyCards.length} potential property cards`);

          if (propertyCards.length > 0) {
            console.log('3. Clicking on first property...');
            await propertyCards[0].click();

            await page.waitForTimeout(3000);
            await page.screenshot({ path: 'property-details.png', fullPage: true });

            // Look for tabs
            const tabs = await page.locator('button, .tab, [role="tab"]').all();
            console.log(`   Found ${tabs.length} potential tabs`);

            for (let i = 0; i < tabs.length; i++) {
              const tabText = await tabs[i].textContent();
              console.log(`   Tab ${i}: "${tabText}"`);

              if (tabText && tabText.toLowerCase().includes('sales')) {
                console.log('   Found Sales History tab! Clicking...');
                await tabs[i].click();
                await page.waitForTimeout(3000);

                await page.screenshot({ path: 'sales-history-tab.png', fullPage: true });
                console.log('   Sales History tab screenshot saved');

                // Check for sales data
                const salesData = await page.textContent('body');
                console.log('   Sales data preview:', salesData.substring(0, 200));

                return { success: true, city, tabFound: true };
              }
            }
          }

          return { success: true, city, tabFound: false };
        }
      }
    }

    // Try using the search box
    console.log('3. Trying search box...');
    const searchBox = page.locator('input[placeholder*="search"], input[placeholder*="address"]');
    if (await searchBox.count() > 0) {
      console.log('   Found search box, trying "123 Main"...');
      await searchBox.fill('123 Main');
      await page.keyboard.press('Enter');

      await page.waitForTimeout(5000);
      await page.screenshot({ path: 'search-results.png', fullPage: true });

      const results = await page.textContent('body');
      console.log('   Search results:', results.substring(0, 200));
    }

    return { success: false, message: 'No properties found with any search method' };

  } catch (error) {
    console.error('Error during test:', error.message);
    await page.screenshot({ path: 'search-error.png', fullPage: true });
    return { success: false, error: error.message };
  } finally {
    await browser.close();
  }
}

testWithSearch().then(result => {
  console.log('\n=== SEARCH TEST RESULT ===');
  console.log(JSON.stringify(result, null, 2));
}).catch(console.error);