const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    consoleMessages.push({ type, text });
    console.log(`[${type}] ${text}`);
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.error('Page Error:', error.message);
  });
  
  console.log('Opening properties page on port 5183...');
  
  try {
    await page.goto('http://localhost:5183/properties', { waitUntil: 'networkidle' });
    console.log('Page loaded successfully');
    
    // Wait for potential data loading
    await page.waitForTimeout(3000);
    
    // Check what's in the properties state
    const result = await page.evaluate(() => {
      // Try to get React DevTools data if available
      const rootElement = document.querySelector('#root');
      if (rootElement && rootElement._reactRootContainer) {
        return 'React root found';
      }
      
      // Check for any property-related elements
      const propertyCards = document.querySelectorAll('[class*="card"]');
      const propertyCount = document.querySelector('h2')?.textContent;
      
      return {
        cardsFound: propertyCards.length,
        propertyCountText: propertyCount,
        bodyText: document.body.textContent.substring(0, 500)
      };
    });
    
    console.log('Page evaluation result:', result);
    
    // Take screenshot
    await page.screenshot({ 
      path: `ui_screenshots/debug_${new Date().toISOString().replace(/:/g, '-')}.png`, 
      fullPage: true 
    });
    console.log('Screenshot saved');
    
    // Summary of console messages
    console.log('\\nConsole messages related to mock/database:');
    consoleMessages.filter(m => 
      m.text.includes('mock') || 
      m.text.includes('Mock') || 
      m.text.includes('database') ||
      m.text.includes('Database') ||
      m.text.includes('properties')
    ).forEach(m => console.log(`  [${m.type}] ${m.text}`));
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  console.log('\\nKeeping browser open for inspection...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();