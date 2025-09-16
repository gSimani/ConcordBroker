const { chromium } = require('playwright');

(async () => {
  console.log('=== FINAL TAX DEED SALES TAB TEST ===\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  
  const page = await context.newPage();
  
  try {
    // Navigate to properties page
    console.log('1. Navigating to http://localhost:5173/properties...');
    await page.goto('http://localhost:5173/properties', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    await page.waitForTimeout(2000);
    console.log('✓ Properties page loaded\n');
    
    // Take initial screenshot
    await page.screenshot({ 
      path: 'ui_screenshots/properties_before_tax_deed.png',
      fullPage: true 
    });
    
    // Find and click Tax Deed Sales tab
    console.log('2. Looking for Tax Deed Sales tab button...');
    const taxDeedTab = await page.locator('button:has-text("Tax Deed Sales")').first();
    
    if (await taxDeedTab.isVisible()) {
      console.log('✓ Tax Deed Sales tab found\n');
      
      // Check initial state
      const isActive = await taxDeedTab.evaluate(el => el.classList.contains('active'));
      console.log(`   Initial state: ${isActive ? 'Active' : 'Inactive'}`);
      
      // Click the tab
      console.log('3. Clicking Tax Deed Sales tab...');
      await taxDeedTab.click();
      await page.waitForTimeout(3000);
      console.log('✓ Tab clicked\n');
      
      // Take screenshot after clicking
      await page.screenshot({ 
        path: 'ui_screenshots/tax_deed_tab_active.png',
        fullPage: true 
      });
      
      // Check if tab is now active
      const isActiveAfter = await taxDeedTab.evaluate(el => el.classList.contains('active'));
      console.log(`   After click state: ${isActiveAfter ? 'Active' : 'Inactive'}`);
      
      // Check what content is showing
      console.log('4. Checking displayed content...\n');
      
      // Check if TaxDeedSalesTab component rendered
      const taxDeedContent = await page.locator('text=/Tax Deed|Auction|Certificate|Applicant/').first();
      if (await taxDeedContent.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('✅ Tax Deed Sales content is displaying!\n');
        
        // Check for required features
        console.log('5. Verifying required features:');
        
        const features = [
          { selector: 'h2, h3', name: 'Section headings' },
          { selector: 'text=/Tax Deed.*Sale|Upcoming.*Auction/', name: 'Auction information' },
          { selector: 'text=/Sunbiz|Entity|Applicant/', name: 'Sunbiz matching' },
          { selector: 'a[href*="bcpa"], a[href*="property"], a[href*="sunbiz"]', name: 'External links' },
          { selector: 'input[placeholder*="phone"], input[placeholder*="Phone"]', name: 'Phone input' },
          { selector: 'input[placeholder*="email"], input[placeholder*="Email"]', name: 'Email input' },
          { selector: 'textarea[placeholder*="notes"], textarea[placeholder*="Notes"]', name: 'Notes field' },
          { selector: 'table, .property-card, .auction-list', name: 'Property listings' },
          { selector: 'button:has-text("Save"), button:has-text("Export")' , name: 'Action buttons' }
        ];
        
        for (const feature of features) {
          const element = await page.locator(feature.selector).first();
          if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
            console.log(`   ✓ ${feature.name}`);
          } else {
            console.log(`   ✗ ${feature.name} not found`);
          }
        }
        
        // Check design consistency
        console.log('\n6. Checking design consistency:');
        const designChecks = [
          { selector: '.elegant-card, .card-executive', name: 'Card styling' },
          { selector: '.gold, .text-gold, [style*="d4af37"]', name: 'Gold accents' },
          { selector: '.navy, .text-navy, [style*="2c3e50"]', name: 'Navy colors' },
          { selector: '.hover-lift, .animate-in', name: 'Animations' }
        ];
        
        for (const check of designChecks) {
          const element = await page.locator(check.selector).first();
          if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
            console.log(`   ✓ ${check.name}`);
          } else {
            console.log(`   ⚠ ${check.name} not found`);
          }
        }
        
        // Check if we can interact with the content
        console.log('\n7. Testing interactivity:');
        
        // Try to find and interact with a phone input
        const phoneInput = await page.locator('input[placeholder*="phone" i], input[type="tel"]').first();
        if (await phoneInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          await phoneInput.fill('555-123-4567');
          console.log('   ✓ Phone input is functional');
        }
        
        // Try to find and interact with email input
        const emailInput = await page.locator('input[placeholder*="email" i], input[type="email"]').first();
        if (await emailInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          await emailInput.fill('test@example.com');
          console.log('   ✓ Email input is functional');
        }
        
        // Take final screenshot with interactions
        await page.screenshot({ 
          path: 'ui_screenshots/tax_deed_tab_with_data.png',
          fullPage: true 
        });
        
      } else {
        console.log('❌ Tax Deed Sales content NOT displaying');
        console.log('   The tab may be active but content is not rendering\n');
        
        // Debug: Check what's visible on the page
        const pageText = await page.locator('body').textContent();
        if (pageText.includes('No tax deed sales')) {
          console.log('   ℹ️ "No tax deed sales" message found - component loaded but no data');
        } else if (pageText.includes('Loading')) {
          console.log('   ℹ️ Loading message found - data may be fetching');
        } else {
          console.log('   ℹ️ Component may not be rendering properly');
        }
      }
      
      // Test toggling back
      console.log('\n8. Testing tab toggle (clicking again)...');
      await taxDeedTab.click();
      await page.waitForTimeout(2000);
      
      const regularContent = await page.locator('.MiniPropertyCard, text="Search Results"').first();
      if (await regularContent.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('   ✓ Toggle works - regular content restored');
      }
      
    } else {
      console.log('❌ Tax Deed Sales tab NOT found on properties page');
    }
    
    console.log('\n=== TEST SUMMARY ===');
    console.log('Screenshots saved:');
    console.log('- ui_screenshots/properties_before_tax_deed.png');
    console.log('- ui_screenshots/tax_deed_tab_active.png');
    console.log('- ui_screenshots/tax_deed_tab_with_data.png');
    
  } catch (error) {
    console.error('\nError during test:', error.message);
    await page.screenshot({ 
      path: 'ui_screenshots/error_state.png',
      fullPage: true 
    });
  } finally {
    await browser.close();
    console.log('\n=== TEST COMPLETE ===');
  }
})();