const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Opening properties page...');
  await page.goto('http://localhost:5175/properties');
  
  // Wait for the page to load
  await page.waitForTimeout(3000);
  
  // Take a screenshot
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ path: `ui_screenshots/properties_with_data_${timestamp}.png`, fullPage: true });
  console.log('Screenshot saved to ui_screenshots/properties_with_data_' + timestamp + '.png');
  
  // Check if properties are displayed
  try {
    // Look for property cards
    const propertyCards = await page.locator('.property-card, [class*="card"]').count();
    console.log(`Found ${propertyCards} property cards on the page`);
    
    // Check for "No Properties Found" message
    const noPropertiesMsg = await page.locator('text=/No Properties Found/i').count();
    if (noPropertiesMsg > 0) {
      console.log('⚠️ "No Properties Found" message is still visible');
    } else {
      console.log('✅ Properties are being displayed!');
    }
    
    // Try to get some property addresses
    const addresses = await page.locator('[class*="address"], h3, h4').allTextContents();
    if (addresses.length > 0) {
      console.log('\nProperty addresses found:');
      addresses.slice(0, 5).forEach(addr => {
        if (addr && addr.trim()) {
          console.log(`  - ${addr.trim()}`);
        }
      });
    }
    
    // Check if mock data is being used
    const consoleMessages = [];
    page.on('console', msg => consoleMessages.push(msg.text()));
    
    // Try a search
    console.log('\nTrying a search for "Ocean"...');
    await page.fill('input[placeholder*="Search"]', 'Ocean');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);
    
    const resultsAfterSearch = await page.locator('.property-card, [class*="card"]').count();
    console.log(`Found ${resultsAfterSearch} results after search`);
    
  } catch (error) {
    console.error('Error checking for properties:', error);
  }
  
  // Keep browser open for manual inspection
  console.log('\nBrowser will stay open for 10 seconds for manual inspection...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();