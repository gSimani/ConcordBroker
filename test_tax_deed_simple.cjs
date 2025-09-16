const { chromium } = require('playwright');

(async () => {
  console.log('=== SIMPLE TAX DEED TEST ===\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  const page = await browser.newContext().then(ctx => ctx.newPage());
  
  try {
    // Go to properties page
    await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    console.log('✓ Page loaded');
    
    // Click Tax Deed Sales tab
    const tab = await page.locator('button:has-text("Tax Deed Sales")').first();
    if (await tab.isVisible()) {
      console.log('✓ Tab found');
      await tab.click();
      await page.waitForTimeout(3000);
      console.log('✓ Tab clicked');
      
      // Take screenshot
      await page.screenshot({ 
        path: 'ui_screenshots/tax_deed_simple_test.png',
        fullPage: true 
      });
      
      // Check what's visible
      const headings = await page.locator('h1, h2, h3').allTextContents();
      console.log('\nVisible headings:', headings.slice(0, 5));
      
      // Check for Tax Deed content
      const hasContent = await page.locator('*:has-text("Tax Deed")').count();
      console.log(`\nElements with "Tax Deed": ${hasContent}`);
      
      // Check for "No tax deed" message
      const noDataMsg = await page.locator('text=/No tax deed|No auction|No properties/i').first();
      if (await noDataMsg.isVisible({ timeout: 1000 }).catch(() => false)) {
        const msg = await noDataMsg.textContent();
        console.log(`\nNo data message: "${msg}"`);
      }
      
      // Check for any error messages
      const errorMsg = await page.locator('text=/error|failed|cannot/i').first();
      if (await errorMsg.isVisible({ timeout: 1000 }).catch(() => false)) {
        const msg = await errorMsg.textContent();
        console.log(`\nError message: "${msg}"`);
      }
      
      // Check for input fields
      const inputs = await page.locator('input, textarea').count();
      console.log(`\nInput fields found: ${inputs}`);
      
    } else {
      console.log('✗ Tab not found');
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
    console.log('\n=== DONE ===');
  }
})();