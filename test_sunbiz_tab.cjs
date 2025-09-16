const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('Testing Sunbiz Info tab...');
  
  // Go to property page
  await page.goto('http://localhost:5174/property/064210010010');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(2000);
  
  // Click Sunbiz Info tab
  const sunbizTab = await page.locator('text=Sunbiz Info');
  if (await sunbizTab.count() > 0) {
    await sunbizTab.click();
    await page.waitForTimeout(2000);
    
    // Check for key sections
    const agentMatching = await page.locator('text=AGENT MATCHING SUMMARY').count();
    const entityName = await page.locator('text=Detail by Entity Name').count();
    const filingInfo = await page.locator('text=Filing Information').count();
    const corporateAddresses = await page.locator('text=Corporate Addresses').count();
    const officers = await page.locator('text=Officer/Director Detail').count();
    
    console.log('\nSunbiz Tab Content Check:');
    console.log('- Agent Matching Summary:', agentMatching > 0 ? 'Present ✓' : 'Missing ✗');
    console.log('- Detail by Entity Name:', entityName > 0 ? 'Present ✓' : 'Missing ✗');
    console.log('- Filing Information:', filingInfo > 0 ? 'Present ✓' : 'Missing ✗');
    console.log('- Corporate Addresses:', corporateAddresses > 0 ? 'Present ✓' : 'Missing ✗');
    console.log('- Officer/Director Detail:', officers > 0 ? 'Present ✓' : 'Missing ✗');
    
    // Check for actual data (not N/A)
    const content = await page.locator('.card-executive').first().textContent();
    const hasData = content && !content.includes('No Sunbiz Information Found');
    console.log('\nData Status:', hasData ? 'Showing Data ✓' : 'No Data ✗');
    
    // Check for company name
    const companyName = await page.locator('text=Ocean Properties LLC').count();
    console.log('Company Name (Ocean Properties LLC):', companyName > 0 ? 'Present ✓' : 'Missing ✗');
    
    // Take screenshot
    await page.screenshot({ path: 'ui_screenshots/sunbiz_tab_test.png', fullPage: true });
    console.log('\nScreenshot saved to ui_screenshots/sunbiz_tab_test.png');
  } else {
    console.log('Sunbiz Info tab not found');
  }
  
  await browser.close();
})();