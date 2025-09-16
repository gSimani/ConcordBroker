const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Testing with mock parcel ID: 064210010010');
  
  // Go directly to a property detail page using a mock property parcel ID
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Check if page loaded
  const title = await page.locator('h1').first().textContent();
  console.log('Page title:', title);
  
  // Click Core Property Info tab
  const coreTab = await page.locator('text=Core Property Info');
  if (await coreTab.count() > 0) {
    await coreTab.click();
    await page.waitForTimeout(1000);
    
    // Get text content from specific sections
    const propertyAssessment = await page.locator('text=Property Assessment Values').locator('..').locator('..').textContent();
    const salesHistory = await page.locator('text=Sales History').locator('..').locator('..').textContent();
    
    console.log('\nProperty Assessment Section includes:', propertyAssessment.substring(0, 300));
    console.log('\nSales History Section includes:', salesHistory.substring(0, 200));
    
    // Check if data is present
    const hasData = !propertyAssessment.includes('N/A') || propertyAssessment.includes('$');
    console.log('\nData populated:', hasData ? 'YES - Mock data is working' : 'NO - Fields show N/A');
    
    // Take screenshot
    await page.screenshot({ path: 'ui_screenshots/core_property_064210010010.png', fullPage: true });
    console.log('Screenshot saved to ui_screenshots/core_property_064210010010.png');
  } else {
    console.log('Core Property Info tab not found');
  }
  
  await browser.close();
})();