const { chromium } = require('playwright');

(async () => {
  console.log('Starting detailed Tax Deed Sales verification...');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  
  const page = await context.newPage();
  
  // Listen for console messages
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ Console Error:', msg.text());
    }
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    console.log('❌ Page Error:', error.message);
  });
  
  try {
    // First go directly to Tax Deed Sales page
    console.log('\n1. Testing direct navigation to /tax-deed-sales...');
    await page.goto('http://localhost:5173/tax-deed-sales', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    await page.waitForTimeout(2000);
    
    // Check if page loaded
    const pageTitle = await page.title();
    console.log('Page title:', pageTitle);
    
    // Look for main heading
    const heading = await page.locator('h1').first();
    if (await heading.isVisible({ timeout: 5000 }).catch(() => false)) {
      const headingText = await heading.textContent();
      console.log('✓ Page heading found:', headingText);
    } else {
      console.log('✗ No h1 heading found');
    }
    
    // Check for Tax Deed Sales specific content
    const taxDeedContent = await page.locator('text=/Tax Deed|Auction|Certificate/').first();
    if (await taxDeedContent.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('✓ Tax Deed content found');
    } else {
      console.log('✗ Tax Deed content not found');
      
      // Get page text to debug
      const bodyText = await page.locator('body').textContent();
      if (bodyText.length < 100) {
        console.log('Page appears empty or minimal. Body text:', bodyText.substring(0, 200));
      }
    }
    
    // Take screenshot
    await page.screenshot({ 
      path: 'ui_screenshots/tax_deed_sales_direct.png',
      fullPage: true 
    });
    
    // Now test from properties page
    console.log('\n2. Testing navigation from properties page...');
    await page.goto('http://localhost:5173/properties', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    await page.waitForTimeout(2000);
    
    // Check for sidebar
    const sidebar = await page.locator('.sidebar, nav, [role="navigation"]').first();
    if (await sidebar.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('✓ Sidebar found');
      
      // Look for Tax Deed Sales link
      const taxDeedLink = await page.locator('a:has-text("Tax Deed Sales")').first();
      if (await taxDeedLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('✓ Tax Deed Sales link found in sidebar');
        
        // Click it
        await taxDeedLink.click();
        await page.waitForTimeout(2000);
        
        const newUrl = page.url();
        console.log('After clicking, URL is:', newUrl);
        
        // Check if content loaded
        const afterClickHeading = await page.locator('h1').first();
        if (await afterClickHeading.isVisible({ timeout: 3000 }).catch(() => false)) {
          const text = await afterClickHeading.textContent();
          console.log('✓ Page loaded with heading:', text);
        }
      } else {
        console.log('✗ Tax Deed Sales link not found in sidebar');
      }
    } else {
      console.log('✗ Sidebar not found');
    }
    
    // Test property profile tab
    console.log('\n3. Looking for a property to test tab integration...');
    
    // Try different selectors for property links
    const propertySelectors = [
      'a[href*="/property/"]',
      '.property-card a',
      'tr a[href*="/property"]',
      '[data-testid="property-link"]',
      '.MiniPropertyCard a',
      'a:has-text("View Details")'
    ];
    
    let propertyFound = false;
    for (const selector of propertySelectors) {
      const propertyLink = await page.locator(selector).first();
      if (await propertyLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log(`✓ Found property link with selector: ${selector}`);
        propertyFound = true;
        
        await propertyLink.click();
        await page.waitForTimeout(3000);
        
        // Look for tabs
        const tabsList = await page.locator('[role="tablist"], .tabs, .tab-triggers').first();
        if (await tabsList.isVisible({ timeout: 3000 }).catch(() => false)) {
          console.log('✓ Tabs container found');
          
          // Get all tab texts
          const tabs = await page.locator('[role="tab"], button.tab-trigger, .tab-button').allTextContents();
          console.log('Available tabs:', tabs);
          
          // Look for Tax Deed Sales tab
          const taxDeedTab = await page.locator('[role="tab"]:has-text("Tax Deed Sales"), button:has-text("Tax Deed Sales")').first();
          if (await taxDeedTab.isVisible({ timeout: 3000 }).catch(() => false)) {
            console.log('✓ Tax Deed Sales tab found!');
            
            await taxDeedTab.click();
            await page.waitForTimeout(2000);
            
            // Take screenshot
            await page.screenshot({ 
              path: 'ui_screenshots/tax_deed_tab_clicked.png',
              fullPage: true 
            });
            
            console.log('✓ Tax Deed Sales tab clicked, screenshot saved');
          } else {
            console.log('✗ Tax Deed Sales tab not found in property profile');
          }
        } else {
          console.log('✗ No tabs container found in property profile');
        }
        
        break;
      }
    }
    
    if (!propertyFound) {
      console.log('✗ No property links found on page');
      
      // Debug: Check what's on the page
      const pageContent = await page.locator('main, .content, body').first();
      const text = await pageContent.textContent();
      console.log('Page content preview:', text.substring(0, 300));
    }
    
    console.log('\n=== Summary ===');
    console.log('Check screenshots in ui_screenshots/ folder');
    console.log('- tax_deed_sales_direct.png: Direct navigation to /tax-deed-sales');
    console.log('- tax_deed_tab_clicked.png: Property profile with tab (if found)');
    
  } catch (error) {
    console.error('Error during test:', error);
  } finally {
    await browser.close();
    console.log('\nTest completed.');
  }
})();