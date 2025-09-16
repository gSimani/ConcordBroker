const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('🔍 Testing Property Search at http://localhost:5174/properties');
  
  // Navigate to properties page
  await page.goto('http://localhost:5174/properties');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Wait for property count or error message
  await page.waitForTimeout(3000);
  
  // Check for property count
  const propertyCountElement = await page.locator('text=/\\d+ properties found/i').first();
  const hasCount = await propertyCountElement.isVisible().catch(() => false);
  
  if (hasCount) {
    const countText = await propertyCountElement.textContent();
    console.log('✅ Property count found:', countText);
    
    // Check if it's more than just mock data
    const match = countText.match(/(\d+)/);
    if (match) {
      const count = parseInt(match[1]);
      if (count > 100) {
        console.log('✅ SUCCESS: Found', count, 'properties - Database is connected!');
      } else if (count <= 6) {
        console.log('⚠️ WARNING: Only', count, 'properties found - May be using mock data');
      } else {
        console.log('ℹ️ Found', count, 'properties');
      }
    }
  } else {
    console.log('❌ No property count found on page');
  }
  
  // Check for property cards
  const propertyCards = await page.locator('.property-card, [class*="card"]').count();
  console.log('📦 Property cards visible:', propertyCards);
  
  // Check API response
  const apiResponse = await page.evaluate(async () => {
    try {
      const response = await fetch('http://localhost:8001/api/properties/search?limit=5');
      const data = await response.json();
      return {
        success: true,
        total: data.total,
        properties: data.properties?.length || 0
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  });
  
  if (apiResponse.success) {
    console.log('🔌 API Response:', {
      total: apiResponse.total,
      returned: apiResponse.properties
    });
    
    if (apiResponse.total > 100000) {
      console.log('🎉 EXCELLENT: API reports', apiResponse.total, 'total properties!');
    }
  } else {
    console.log('❌ API Error:', apiResponse.error);
  }
  
  // Take screenshot
  await page.screenshot({ path: 'property_search_test.png', fullPage: true });
  console.log('📸 Screenshot saved as property_search_test.png');
  
  // Keep browser open for manual inspection
  console.log('\n👀 Browser will stay open for 10 seconds for manual inspection...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();