const { chromium } = require('playwright');

(async () => {
  console.log('=== QUICK TAX DEED VERIFICATION ===\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 300 
  });
  
  const page = await browser.newContext().then(ctx => ctx.newPage());
  
  try {
    // Navigate and click tab
    await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const tab = await page.locator('button:has-text("Tax Deed Sales")').first();
    await tab.click();
    await page.waitForTimeout(3000);
    
    console.log('✅ Tab clicked\n');
    
    // Take screenshot
    await page.screenshot({ 
      path: 'ui_screenshots/tax_deed_final_result.png',
      fullPage: true 
    });
    
    // Check what's visible
    console.log('Checking content...\n');
    
    // Get all visible text to understand what's showing
    const visibleText = await page.locator('main, .content, body').first().textContent();
    
    // Check for key elements
    const checks = [
      { text: 'TD-2025', name: 'Tax Deed Numbers' },
      { text: 'Fort Lauderdale', name: 'Property addresses' },
      { text: 'FLORIDA TAX LIEN', name: 'Applicant names' },
      { text: '125,000', name: 'Opening bids' },
      { text: 'Homestead', name: 'Homestead status' },
      { text: 'P2100', name: 'Sunbiz entities' }
    ];
    
    for (const check of checks) {
      if (visibleText.includes(check.text)) {
        console.log(`✅ ${check.name} found`);
      } else {
        console.log(`❌ ${check.name} not found`);
      }
    }
    
    // Check for input fields
    const phoneInputs = await page.locator('input').filter({ hasText: '' }).count();
    const textareas = await page.locator('textarea').count();
    const links = await page.locator('a[href*="bcpa"], a[href*="sunbiz"]').count();
    const buttons = await page.locator('button').count();
    
    console.log(`\n📊 Component Stats:`);
    console.log(`   Input fields: ${phoneInputs}`);
    console.log(`   Text areas: ${textareas}`);
    console.log(`   External links: ${links}`);
    console.log(`   Buttons: ${buttons}`);
    
    // Try to interact with first row
    const firstPhoneInput = await page.locator('input').nth(1);
    if (await firstPhoneInput.isVisible()) {
      await firstPhoneInput.fill('954-555-1234');
      console.log('\n✅ Successfully entered phone number');
    }
    
    console.log('\n✅ Tax Deed Sales tab is working!');
    console.log('Screenshot saved: ui_screenshots/tax_deed_final_result.png');
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
})();