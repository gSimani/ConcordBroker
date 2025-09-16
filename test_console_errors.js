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
    if (type === 'error') {
      console.error('❌ Console Error:', text);
    } else if (type === 'warning') {
      console.warn('⚠️ Console Warning:', text);
    } else if (type === 'log' && (text.includes('mock') || text.includes('Mock') || text.includes('database'))) {
      console.log('📝 Console Log:', text);
    }
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.error('🔴 Page Error:', error.message);
  });
  
  console.log('Opening properties page...');
  
  try {
    await page.goto('http://localhost:5175/properties', { waitUntil: 'networkidle' });
    console.log('Page loaded successfully');
  } catch (error) {
    console.error('Failed to load page:', error.message);
  }
  
  // Wait for potential async operations
  await page.waitForTimeout(3000);
  
  // Check page content
  const pageContent = await page.content();
  
  // Check for specific elements
  console.log('\n📋 Checking page elements:');
  
  const hasLayout = await page.locator('header, nav, .sidebar').count();
  console.log(`- Layout components: ${hasLayout > 0 ? '✅ Found' : '❌ Not found'}`);
  
  const hasSearchBar = await page.locator('input[type="text"], input[placeholder*="search" i]').count();
  console.log(`- Search bar: ${hasSearchBar > 0 ? '✅ Found' : '❌ Not found'}`);
  
  const hasPropertyCards = await page.locator('[class*="card"], .property-card').count();
  console.log(`- Property cards: ${hasPropertyCards > 0 ? '✅ Found (' + hasPropertyCards + ')' : '❌ Not found'}`);
  
  const hasNoPropertiesMsg = await page.locator('text=/No Properties Found/i').count();
  console.log(`- "No Properties Found" message: ${hasNoPropertiesMsg > 0 ? '⚠️ Visible' : '✅ Not visible'}`);
  
  // Check if React app is mounted
  const hasReactRoot = await page.locator('#root, .App, [data-reactroot]').count();
  console.log(`- React app root: ${hasReactRoot > 0 ? '✅ Found' : '❌ Not found'}`);
  
  // Check for any visible text
  const visibleText = await page.locator('body').innerText();
  if (visibleText.trim().length < 50) {
    console.log('\n⚠️ Page appears to be mostly empty');
    console.log('Visible text:', visibleText.trim().substring(0, 200));
  }
  
  // Summary of console messages
  console.log('\n📊 Console Message Summary:');
  const errorCount = consoleMessages.filter(m => m.type === 'error').length;
  const warnCount = consoleMessages.filter(m => m.type === 'warning').length;
  console.log(`- Errors: ${errorCount}`);
  console.log(`- Warnings: ${warnCount}`);
  
  if (errorCount > 0) {
    console.log('\n🔴 All errors:');
    consoleMessages.filter(m => m.type === 'error').forEach(m => console.log('  -', m.text));
  }
  
  await page.screenshot({ path: `ui_screenshots/debug_properties_${Date.now()}.png`, fullPage: true });
  console.log('\nScreenshot saved for debugging');
  
  console.log('\nKeeping browser open for 5 seconds...');
  await page.waitForTimeout(5000);
  
  await browser.close();
})();