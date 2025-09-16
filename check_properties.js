const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Opening properties page on port 5183...');
  
  try {
    await page.goto('http://localhost:5183/properties', { waitUntil: 'networkidle' });
    console.log('Page loaded successfully');
    
    // Wait for property cards to load
    await page.waitForTimeout(2000);
    
    // Check for MiniPropertyCard elements
    const propertyCards = await page.locator('.elegant-card').count();
    console.log(`Found ${propertyCards} property cards`);
    
    // Check if cards have content
    if (propertyCards > 0) {
      const firstCardText = await page.locator('.elegant-card').first().textContent();
      console.log('First card content preview:', firstCardText.substring(0, 200));
    }
    
    // Take screenshot
    await page.screenshot({ 
      path: `ui_screenshots/properties_current_${new Date().toISOString().replace(/:/g, '-')}.png`, 
      fullPage: true 
    });
    console.log('Screenshot saved');
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  console.log('Keeping browser open for inspection...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();