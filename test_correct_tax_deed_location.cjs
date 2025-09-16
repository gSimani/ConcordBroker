const { chromium } = require('playwright');

(async () => {
  console.log('=== CHECKING TAX DEED SALES TAB ON PROPERTIES PAGE ===\n');
  
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
    
    // Take initial screenshot
    await page.screenshot({ 
      path: 'ui_screenshots/properties_page_initial.png',
      fullPage: true 
    });
    
    console.log('✓ Properties page loaded\n');
    
    // Look for Tax Deed Sales tab button
    console.log('2. Looking for Tax Deed Sales tab button...');
    
    // Try multiple selectors for the tab
    const tabSelectors = [
      'button.tab-executive:has-text("Tax Deed Sales")',
      'button:has-text("Tax Deed Sales")',
      'button:has(svg.lucide-gavel)',
      '.tab-executive:has-text("Tax Deed Sales")',
      'text="Tax Deed Sales"'
    ];
    
    let tabFound = false;
    let taxDeedTab = null;
    
    for (const selector of tabSelectors) {
      console.log(`   Trying selector: ${selector}`);
      const element = await page.locator(selector).first();
      if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log(`   ✓ Found with selector: ${selector}`);
        taxDeedTab = element;
        tabFound = true;
        break;
      }
    }
    
    if (!tabFound) {
      console.log('\n✗ Tax Deed Sales tab NOT FOUND');
      
      // Debug: List all visible tabs
      console.log('\nDebug: Looking for all tab-executive buttons...');
      const allTabs = await page.locator('.tab-executive, button.tab-executive').allTextContents();
      console.log('Found tabs:', allTabs);
      
      // Check page structure
      console.log('\nDebug: Checking page HTML for "Tax Deed" text...');
      const pageText = await page.content();
      if (pageText.includes('Tax Deed Sales')) {
        console.log('✓ "Tax Deed Sales" text exists in HTML');
        
        // Find where it is
        const taxDeedElements = await page.locator('*:has-text("Tax Deed Sales")').all();
        console.log(`Found ${taxDeedElements.length} elements with "Tax Deed Sales" text`);
        
        for (let i = 0; i < Math.min(3, taxDeedElements.length); i++) {
          const tagName = await taxDeedElements[i].evaluate(el => el.tagName);
          const className = await taxDeedElements[i].evaluate(el => el.className);
          console.log(`  Element ${i+1}: <${tagName} class="${className}">`);
        }
      } else {
        console.log('✗ "Tax Deed Sales" text NOT found in HTML');
      }
    } else {
      console.log('\n✓✓✓ TAX DEED SALES TAB FOUND!\n');
      
      // Click the tab
      console.log('3. Clicking Tax Deed Sales tab...');
      await taxDeedTab.click();
      await page.waitForTimeout(3000);
      
      // Take screenshot after clicking
      await page.screenshot({ 
        path: 'ui_screenshots/tax_deed_tab_clicked.png',
        fullPage: true 
      });
      
      console.log('✓ Tab clicked\n');
      
      // Check what loaded
      console.log('4. Checking content after clicking tab...');
      
      // Check if we navigated to a new page
      const currentUrl = page.url();
      console.log(`   Current URL: ${currentUrl}`);
      
      if (currentUrl.includes('/tax-deed-sales')) {
        console.log('   ✓ Navigated to Tax Deed Sales page\n');
        
        // Check for required elements
        console.log('5. Verifying required elements:');
        
        const requiredElements = [
          { selector: 'h1, h2', name: 'Page heading' },
          { selector: 'text=/Tax Deed.*Number|Parcel.*Number|Certificate/', name: 'Tax Deed/Parcel info' },
          { selector: 'text=/Sunbiz|Entity|Applicant/', name: 'Sunbiz matching' },
          { selector: 'a[href*="bcpa"], a[href*="property"]', name: 'Property Appraiser links' },
          { selector: 'input[placeholder*="phone"], input[type="tel"]', name: 'Phone number input' },
          { selector: 'input[placeholder*="email"], input[type="email"]', name: 'Email input' },
          { selector: 'textarea, input[placeholder*="notes"]', name: 'Notes field' },
          { selector: 'table, .property-card, .auction-item', name: 'Property/auction listings' }
        ];
        
        for (const item of requiredElements) {
          const element = await page.locator(item.selector).first();
          if (await element.isVisible({ timeout: 2000 }).catch(() => false)) {
            console.log(`   ✓ ${item.name} found`);
          } else {
            console.log(`   ✗ ${item.name} NOT found`);
          }
        }
        
        // Check design consistency
        console.log('\n6. Checking design consistency:');
        
        // Check for executive styling classes
        const designElements = [
          { selector: '.executive-header, .elegant-heading', name: 'Executive header styling' },
          { selector: '.card-executive, .glass-card', name: 'Card styling' },
          { selector: '.btn-executive, .btn-outline-executive', name: 'Button styling' },
          { selector: '.gold, .text-gold, .gold-accent', name: 'Gold accent colors' },
          { selector: '.navy, .text-navy', name: 'Navy colors' }
        ];
        
        for (const item of designElements) {
          const element = await page.locator(item.selector).first();
          if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
            console.log(`   ✓ ${item.name} present`);
          } else {
            console.log(`   ⚠ ${item.name} not found`);
          }
        }
        
      } else {
        console.log('   ✗ Did NOT navigate to Tax Deed Sales page');
        console.log('   ✗ Tab may not be properly configured\n');
        
        // Check if content loaded in place
        const tabContent = await page.locator('.tab-content, [role="tabpanel"]').first();
        if (await tabContent.isVisible()) {
          const contentText = await tabContent.textContent();
          console.log('   Tab content preview:', contentText.substring(0, 200));
        }
      }
    }
    
    console.log('\n=== SUMMARY ===');
    if (tabFound && currentUrl.includes('/tax-deed-sales')) {
      console.log('✅ Tax Deed Sales tab EXISTS and WORKS');
      console.log('✅ Navigates to dedicated page');
    } else if (tabFound) {
      console.log('⚠️ Tax Deed Sales tab found but may not be working correctly');
    } else {
      console.log('❌ Tax Deed Sales tab NOT FOUND on properties page');
      console.log('❌ Need to add tab to the properties page');
    }
    
    console.log('\nScreenshots saved:');
    console.log('- ui_screenshots/properties_page_initial.png');
    console.log('- ui_screenshots/tax_deed_tab_clicked.png');
    
  } catch (error) {
    console.error('Error during test:', error.message);
    await page.screenshot({ 
      path: 'ui_screenshots/error_screenshot.png',
      fullPage: true 
    });
  } finally {
    await browser.close();
    console.log('\n=== TEST COMPLETE ===');
  }
})();