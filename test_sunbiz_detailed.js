const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Testing Sunbiz Info tab in detail...');
  
  // Go to property page
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Click Sunbiz Info tab
  await page.click('text=Sunbiz Info');
  await page.waitForTimeout(2000);
  
  // Extract specific field values
  const getFieldValue = async (label) => {
    try {
      const elements = await page.locator(`text="${label}"`).all();
      for (const element of elements) {
        const parent = await element.locator('..').locator('..').textContent();
        if (parent && !parent.includes('N/A')) {
          return parent.substring(0, 100); // Return first 100 chars
        }
      }
      return 'Not found';
    } catch {
      return 'Error';
    }
  };
  
  console.log('\n=== SUNBIZ DATA FIELDS ===');
  console.log('\n1. Entity Information:');
  console.log('   - Name of Company:', await getFieldValue('Name of Company'));
  console.log('   - Incorporation Type:', await getFieldValue('Incorporation Type'));
  console.log('   - Status:', await page.locator('.bg-green-100.text-green-800').first().textContent().catch(() => 'N/A'));
  
  console.log('\n2. Filing Information:');
  console.log('   - Document Number:', await getFieldValue('Document Number'));
  console.log('   - FEI/EIN Number:', await getFieldValue('FEI/EIN Number'));
  console.log('   - Date Filed:', await getFieldValue('Date Filed'));
  
  console.log('\n3. Address Matching:');
  const principalMatch = await page.locator('text=Principal Address Match').locator('..').textContent();
  const mailingMatch = await page.locator('text=Mailing Address Match').locator('..').textContent();
  console.log('   - Principal Address:', principalMatch.includes('MATCHES') ? 'MATCHES ✓' : 'NO MATCH');
  console.log('   - Mailing Address:', mailingMatch.includes('MATCHES') ? 'MATCHES ✓' : 'NO MATCH');
  
  console.log('\n4. Officers:');
  const officers = await page.locator('text=Officer/Director Detail').locator('..').locator('..').textContent();
  console.log('   - Has Officers:', officers.includes('Manager') ? 'Yes ✓' : 'No');
  
  console.log('\n5. Annual Reports:');
  const reports = await page.locator('text=Annual Reports').count();
  console.log('   - Has Annual Reports:', reports > 0 ? 'Yes ✓' : 'No');
  
  // Take final screenshot
  await page.screenshot({ path: 'ui_screenshots/sunbiz_tab_detailed.png', fullPage: true });
  console.log('\nDetailed screenshot saved to ui_screenshots/sunbiz_tab_detailed.png');
  
  await browser.close();
})();