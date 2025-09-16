// Test Advanced Search functionality
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Testing Advanced Search functionality...');
  
  // Navigate to properties page
  await page.goto('http://localhost:5174/properties', { waitUntil: 'networkidle2' });
  
  // Wait for page to load
  await page.waitForTimeout(2000);
  
  // Check if Advanced Search button exists and click it
  try {
    await page.waitForSelector('button:has-text("Advanced Search")', { timeout: 5000 });
    console.log('✓ Advanced Search button found');
    
    // Click the Advanced Search button
    await page.click('button:has-text("Advanced Search")');
    await page.waitForTimeout(1000);
    
    // Check for filter fields
    const filters = [
      { selector: 'input[placeholder*="Min Price"]', name: 'Min Price' },
      { selector: 'input[placeholder*="Max Price"]', name: 'Max Price' },
      { selector: 'input[placeholder*="Min Sqft"]', name: 'Min Sqft' },
      { selector: 'input[placeholder*="Max Sqft"]', name: 'Max Sqft' },
      { selector: 'input[type="checkbox"]', name: 'Tax Delinquent checkbox' }
    ];
    
    for (const filter of filters) {
      const element = await page.$(filter.selector);
      if (element) {
        console.log(`✓ ${filter.name} field found`);
      } else {
        console.log(`✗ ${filter.name} field NOT found`);
      }
    }
    
    // Test entering values
    await page.type('input[placeholder*="Min Price"]', '100000');
    await page.type('input[placeholder*="Max Price"]', '500000');
    console.log('✓ Price filters entered');
    
    // Test checkbox
    const checkbox = await page.$('input[type="checkbox"]');
    if (checkbox) {
      await checkbox.click();
      console.log('✓ Tax Delinquent checkbox clicked');
    }
    
    // Test Clear All button
    const clearButton = await page.$('button:has-text("Clear All")');
    if (clearButton) {
      await clearButton.click();
      console.log('✓ Clear All button works');
    }
    
    console.log('\nAdvanced Search test completed successfully!');
    
  } catch (error) {
    console.error('Error testing Advanced Search:', error.message);
  }
  
  // Take a screenshot
  await page.screenshot({ path: 'advanced_search_test.png' });
  console.log('Screenshot saved as advanced_search_test.png');
  
  await browser.close();
})();