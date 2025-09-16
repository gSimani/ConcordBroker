const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture console messages
  const messages = [];
  page.on('console', msg => {
    if (msg.text().includes('mock') || msg.text().includes('database') || msg.text().includes('No') || msg.text().includes('Error')) {
      messages.push(msg.text());
    }
  });
  
  console.log('Testing properties page for database data...');
  
  await page.goto('http://localhost:5174/properties');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);
  
  console.log('\n=== Console Messages ===');
  messages.forEach(msg => console.log(msg));
  
  // Check if properties are displayed
  const propertyCards = await page.locator('.mini-property-card').count();
  const errorMessage = await page.locator('text=No properties found').count();
  const oceanProperties = await page.locator('text=Ocean Properties').count();
  
  console.log('\n=== Page Status ===');
  console.log('Property cards found:', propertyCards);
  console.log('Error message shown:', errorMessage > 0 ? 'Yes' : 'No');
  console.log('Ocean Properties (mock data) found:', oceanProperties > 0 ? 'YES - Still using mock!' : 'No - Good!');
  
  if (propertyCards === 0) {
    console.log('\n⚠️ NO PROPERTIES DISPLAYED');
    console.log('This means either:');
    console.log('1. Database is empty (run load_data_minimal.py)');
    console.log('2. Database permissions need fixing (run fix_database.sql)');
    console.log('3. Supabase connection issue');
  } else {
    console.log('\n✅ Properties are being displayed');
  }
  
  // Take screenshot
  await page.screenshot({ path: 'ui_screenshots/properties_database_test.png', fullPage: true });
  console.log('\nScreenshot saved to ui_screenshots/properties_database_test.png');
  
  await browser.close();
})();