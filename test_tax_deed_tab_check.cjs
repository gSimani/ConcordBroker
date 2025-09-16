const { chromium } = require('playwright');

(async () => {
  console.log('Starting Tax Deed Sales tab verification...');
  
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
    console.log('Navigating to http://localhost:5173/properties...');
    await page.goto('http://localhost:5173/properties', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Take screenshot of initial properties page
    await page.screenshot({ 
      path: 'ui_screenshots/properties_page_initial_tax_deed.png',
      fullPage: true 
    });
    console.log('✓ Properties page loaded');
    
    // Look for Tax Deed Sales link in sidebar
    console.log('Looking for Tax Deed Sales in sidebar...');
    const sidebarLink = await page.locator('a[href="/tax-deed-sales"], nav a:has-text("Tax Deed Sales")').first();
    
    if (await sidebarLink.isVisible()) {
      console.log('✓ Found Tax Deed Sales link in sidebar');
      
      // Click the sidebar link
      await sidebarLink.click();
      await page.waitForTimeout(2000);
      
      // Check URL
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);
      
      // Take screenshot
      await page.screenshot({ 
        path: 'ui_screenshots/tax_deed_sales_page_from_sidebar.png',
        fullPage: true 
      });
      
      // Check for Tax Deed Sales content
      const pageTitle = await page.locator('h1:has-text("Tax Deed"), h1:has-text("Sales")').first();
      if (await pageTitle.isVisible()) {
        console.log('✓ Tax Deed Sales page loaded successfully');
        
        // Check for key elements
        const elements = [
          { selector: '.tax-deed-property-card, [data-testid="tax-deed-property"]', name: 'Property cards' },
          { selector: 'text=/Upcoming Auctions|Active Opportunities/', name: 'Auction information' },
          { selector: 'button:has-text("Filter"), button:has-text("Export")', name: 'Action buttons' }
        ];
        
        for (const element of elements) {
          const el = await page.locator(element.selector).first();
          if (await el.isVisible({ timeout: 5000 }).catch(() => false)) {
            console.log(`✓ ${element.name} found`);
          } else {
            console.log(`✗ ${element.name} not found`);
          }
        }
      } else {
        console.log('✗ Tax Deed Sales page content not found');
      }
      
      // Go back to properties
      await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
    } else {
      console.log('✗ Tax Deed Sales link not found in sidebar');
    }
    
    // Now check if there's a property to click on
    console.log('\nChecking property profiles for Tax Deed Sales tab...');
    
    // Look for a property card or link
    const propertyLink = await page.locator('a[href*="/property/"], .property-card, [data-testid="property-card"]').first();
    
    if (await propertyLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('✓ Found property link, clicking...');
      await propertyLink.click();
      await page.waitForTimeout(3000);
      
      // Take screenshot of property profile
      await page.screenshot({ 
        path: 'ui_screenshots/property_profile_page_tax_deed.png',
        fullPage: true 
      });
      
      // Look for Tax Deed Sales tab
      console.log('Looking for Tax Deed Sales tab in property profile...');
      const taxDeedTab = await page.locator('button:has-text("Tax Deed Sales"), [role="tab"]:has-text("Tax Deed Sales"), .tab-trigger:has-text("Tax Deed Sales")').first();
      
      if (await taxDeedTab.isVisible({ timeout: 5000 }).catch(() => false)) {
        console.log('✓ Found Tax Deed Sales tab');
        
        // Click the tab
        await taxDeedTab.click();
        await page.waitForTimeout(2000);
        
        // Take screenshot after clicking tab
        await page.screenshot({ 
          path: 'ui_screenshots/tax_deed_tab_content.png',
          fullPage: true 
        });
        
        // Check if content loaded
        const tabContent = await page.locator('.tax-deed-content, [role="tabpanel"], .tab-content').filter({ hasText: /tax deed|auction|applicant/i }).first();
        
        if (await tabContent.isVisible({ timeout: 5000 }).catch(() => false)) {
          console.log('✓ Tax Deed Sales tab content is visible');
          
          // Check for specific elements
          const contentChecks = [
            { selector: 'text=/Tax Deed|Auction|Certificate/', name: 'Auction details' },
            { selector: 'text=/Sunbiz|Entity|Applicant/', name: 'Sunbiz information' },
            { selector: 'input[placeholder*="phone"], input[placeholder*="Phone"]', name: 'Phone input field' },
            { selector: 'input[placeholder*="email"], input[placeholder*="Email"]', name: 'Email input field' },
            { selector: 'textarea[placeholder*="notes"], textarea[placeholder*="Notes"]', name: 'Notes field' }
          ];
          
          for (const check of contentChecks) {
            const element = await page.locator(check.selector).first();
            if (await element.isVisible({ timeout: 3000 }).catch(() => false)) {
              console.log(`  ✓ ${check.name} found`);
            } else {
              console.log(`  ✗ ${check.name} not found`);
            }
          }
        } else {
          console.log('✗ Tax Deed Sales tab content not visible');
          console.log('Checking page structure...');
          
          // Debug: Check what tabs are available
          const allTabs = await page.locator('button[role="tab"], .tab-trigger, [data-state="active"], [data-state="inactive"]').allTextContents();
          console.log('Available tabs:', allTabs);
          
          // Debug: Check current HTML structure
          const tabsContainer = await page.locator('.tabs, [role="tablist"]').first();
          if (await tabsContainer.isVisible()) {
            const tabsHTML = await tabsContainer.innerHTML();
            console.log('Tabs container found, checking structure...');
            if (tabsHTML.includes('Tax Deed')) {
              console.log('Tax Deed text found in tabs HTML');
            } else {
              console.log('Tax Deed text NOT found in tabs HTML');
            }
          }
        }
      } else {
        console.log('✗ Tax Deed Sales tab not found in property profile');
        
        // Debug: List all visible tabs
        const visibleTabs = await page.locator('button:visible, [role="tab"]:visible').allTextContents();
        console.log('Visible tabs/buttons:', visibleTabs);
      }
    } else {
      console.log('✗ No property links found on properties page');
      
      // Check if there's a different way to access properties
      const searchResults = await page.locator('.search-results, .property-list, table tbody tr').first();
      if (await searchResults.isVisible({ timeout: 3000 }).catch(() => false)) {
        console.log('Found search results/property list');
      }
    }
    
    console.log('\n=== Test Summary ===');
    console.log('1. Sidebar navigation to /tax-deed-sales: Check screenshots');
    console.log('2. Property profile Tax Deed Sales tab: Check implementation');
    console.log('3. Screenshots saved to ui_screenshots/');
    
  } catch (error) {
    console.error('Error during test:', error);
    await page.screenshot({ 
      path: 'ui_screenshots/tax_deed_error.png',
      fullPage: true 
    });
  } finally {
    await browser.close();
    console.log('\nTest completed.');
  }
})();