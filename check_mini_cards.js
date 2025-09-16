const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Opening properties page on port 5183...');
  
  try {
    await page.goto('http://localhost:5183/properties', { waitUntil: 'networkidle' });
    console.log('Page loaded successfully');
    
    // Wait for potential data loading
    await page.waitForTimeout(3000);
    
    // Check the property count display
    const propertyCount = await page.textContent('text=/\\d+ Properties Found/');
    console.log('Property count display:', propertyCount || 'Not found');
    
    // Look for parcel IDs
    const parcelElements = await page.locator('text=/Parcel:/').count();
    console.log(`Found ${parcelElements} elements with "Parcel:" text`);
    
    // Look for owner names in cards
    const ownerElements = await page.locator('text=/Owner/i').count();
    console.log(`Found ${ownerElements} elements with "Owner" text`);
    
    // Look for Fort Lauderdale addresses
    const ftLauderdaleElements = await page.locator('text=/Fort Lauderdale/').count();
    console.log(`Found ${ftLauderdaleElements} Fort Lauderdale addresses`);
    
    // Check for property values
    const valueElements = await page.locator('text=/$\\d+[KM]/').count();
    console.log(`Found ${valueElements} property value elements`);
    
    // Check for specific addresses from mock data
    const oceanBlvd = await page.locator('text=/1234 Ocean Boulevard/').count();
    console.log('Found "1234 Ocean Boulevard":', oceanBlvd > 0 ? 'Yes' : 'No');
    
    const lasOlas = await page.locator('text=/567 Las Olas Way/').count();
    console.log('Found "567 Las Olas Way":', lasOlas > 0 ? 'Yes' : 'No');
    
    // Take screenshot
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    await page.screenshot({ 
      path: `ui_screenshots/properties_check_${timestamp}.png`, 
      fullPage: true 
    });
    console.log('Screenshot saved');
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  console.log('\\nKeeping browser open for inspection...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();