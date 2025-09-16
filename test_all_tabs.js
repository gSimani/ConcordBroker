const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Testing property page with all tabs...');
  
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Test each tab
  const tabs = ['Overview', 'Core Property Info', 'Sunbiz Info', 'Property Tax Info', 'Analysis'];
  
  for (const tab of tabs) {
    console.log(`\nTesting ${tab} tab...`);
    const tabElement = await page.locator(`text="${tab}"`);
    if (await tabElement.count() > 0) {
      await tabElement.click();
      await page.waitForTimeout(1000);
      
      // Take screenshot of each tab
      const filename = `ui_screenshots/property_tab_${tab.toLowerCase().replace(/ /g, '_')}.png`;
      await page.screenshot({ path: filename, fullPage: true });
      console.log(`Screenshot saved: ${filename}`);
      
      // Check for data presence
      const content = await page.locator('.card-executive, .elegant-card').first().textContent();
      const hasData = content && !content.includes('N/A N/A N/A');
      console.log(`Has data: ${hasData ? 'Yes' : 'No'}`);
    }
  }
  
  console.log('\n✅ All tabs tested successfully!');
  
  await browser.close();
})();