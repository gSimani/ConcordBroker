const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Capture console messages
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('mock')) {
      console.log(`[${msg.type()}] ${msg.text()}`);
    }
  });
  
  console.log('Testing property profile page...');
  
  try {
    // First go to properties page
    console.log('1. Opening properties page...');
    await page.goto('http://localhost:5183/properties', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Check if property cards are present
    const propertyCards = await page.locator('text=/Parcel:/').count();
    console.log(`   Found ${propertyCards} property cards`);
    
    // Try to click on the first property card
    if (propertyCards > 0) {
      console.log('2. Clicking on first property card...');
      const firstCard = page.locator('text=/Parcel:/').first().locator('..').locator('..');
      await firstCard.click();
      await page.waitForTimeout(2000);
      
      // Check if we navigated to property profile
      const currentUrl = page.url();
      console.log(`   Navigated to: ${currentUrl}`);
      
      // Check for profile elements
      const hasProfile = await page.locator('text=/Property Profile|Property Details|Overview/i').count();
      console.log(`   Profile elements found: ${hasProfile > 0 ? 'Yes' : 'No'}`);
      
      // Check for property data
      const hasAddress = await page.locator('text=/Fort Lauderdale|Hollywood|Pompano/').count();
      console.log(`   Property address found: ${hasAddress > 0 ? 'Yes' : 'No'}`);
      
      // Take screenshot
      await page.screenshot({ 
        path: `ui_screenshots/property_profile_${new Date().toISOString().replace(/:/g, '-')}.png`, 
        fullPage: true 
      });
      console.log('   Screenshot saved');
    }
    
    // Also test direct navigation
    console.log('\\n3. Testing direct navigation to property profile...');
    await page.goto('http://localhost:5183/property/064210010010', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Check page content
    const pageText = await page.textContent('body');
    if (pageText.includes('Ocean Boulevard') || pageText.includes('064210010010')) {
      console.log('   ✅ Property data loaded successfully');
    } else if (pageText.includes('Loading')) {
      console.log('   ⏳ Page is still loading');
    } else if (pageText.includes('Error')) {
      console.log('   ❌ Error loading property');
    } else {
      console.log('   ⚠️ Unknown state - check screenshot');
    }
    
    // Final screenshot
    await page.screenshot({ 
      path: `ui_screenshots/property_direct_${new Date().toISOString().replace(/:/g, '-')}.png`, 
      fullPage: true 
    });
    
  } catch (error) {
    console.error('Test error:', error.message);
  }
  
  console.log('\\nTest complete. Keeping browser open...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();