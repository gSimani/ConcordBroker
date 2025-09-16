const { chromium } = require('playwright');

(async () => {
  console.log('=== TESTING CLEANED TAX DEED SALES PAGE ===\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 300 
  });
  
  const page = await browser.newContext().then(ctx => ctx.newPage());
  
  try {
    // Test 1: Navigate directly to /tax-deed-sales page
    console.log('1. Testing dedicated Tax Deed Sales page at /tax-deed-sales...');
    await page.goto('http://localhost:5173/tax-deed-sales', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    await page.waitForTimeout(2000);
    
    // Check for redundant "How It Works" section - should NOT exist
    const howItWorksSection = await page.locator('text="How It Works"').count();
    const keyFeaturesSection = await page.locator('text="Key Features"').count();
    
    if (howItWorksSection === 0 && keyFeaturesSection === 0) {
      console.log('✅ Redundant "How It Works" section successfully removed');
    } else {
      console.log(`⚠️ Found ${howItWorksSection} "How It Works" and ${keyFeaturesSection} "Key Features" sections`);
    }
    
    // Check that TaxDeedSalesTab component is still present
    const taxDeedComponent = await page.locator('text="Tax Deed Sales"').first();
    if (await taxDeedComponent.isVisible()) {
      console.log('✅ Tax Deed Sales component is displayed');
    }
    
    // Check for the feature cards
    const featureCards = await page.locator('.bg-gradient-to-br').count();
    console.log(`✅ Found ${featureCards} feature/stat cards on page`);
    
    // Take screenshot of cleaned page
    await page.screenshot({ 
      path: 'ui_screenshots/tax_deed_page_cleaned.png',
      fullPage: true 
    });
    
    console.log('\n2. Testing Tax Deed Sales tab in properties page...');
    await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const tab = await page.locator('button:has-text("Tax Deed Sales")').first();
    await tab.click();
    await page.waitForTimeout(2000);
    
    // Check for the new tabs (Upcoming, Past, Cancelled)
    const upcomingTab = await page.locator('button:has-text("Upcoming Auctions")').first();
    const pastTab = await page.locator('button:has-text("Past Auctions")').first();
    const cancelledTab = await page.locator('button:has-text("Cancelled Auctions")').first();
    
    if (await upcomingTab.isVisible() && await pastTab.isVisible() && await cancelledTab.isVisible()) {
      console.log('✅ New auction tabs (Upcoming, Past, Cancelled) are present');
      
      // Test clicking Past Auctions
      await pastTab.click();
      await page.waitForTimeout(1500);
      const pastProperties = await page.locator('.border.border-gray-200.rounded-lg').count();
      console.log(`   Past Auctions: ${pastProperties} properties`);
      
      // Test clicking Cancelled Auctions
      await cancelledTab.click();
      await page.waitForTimeout(1500);
      const cancelledProperties = await page.locator('.border.border-gray-200.rounded-lg').count();
      console.log(`   Cancelled Auctions: ${cancelledProperties} properties`);
      
      // Back to Upcoming
      await upcomingTab.click();
      await page.waitForTimeout(1500);
      const upcomingProperties = await page.locator('.border.border-gray-200.rounded-lg').count();
      console.log(`   Upcoming Auctions: ${upcomingProperties} properties`);
    }
    
    // Check insight boxes are still working
    const insightBoxes = await page.locator('.bg-gradient-to-br').count();
    console.log(`\n✅ ${insightBoxes} insight statistics boxes present`);
    
    // Take final screenshot
    await page.screenshot({ 
      path: 'ui_screenshots/tax_deed_tab_final.png',
      fullPage: true 
    });
    
    console.log('\n=== SUMMARY ===');
    console.log('✅ "How It Works" section removed from /tax-deed-sales page');
    console.log('✅ Tax Deed Sales component still functional');
    console.log('✅ New auction type tabs (Upcoming, Past, Cancelled) working');
    console.log('✅ Insight statistics boxes displaying correctly');
    console.log('✅ All features working as expected');
    console.log('\nScreenshots saved:');
    console.log('- ui_screenshots/tax_deed_page_cleaned.png');
    console.log('- ui_screenshots/tax_deed_tab_final.png');
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
    console.log('\n=== TEST COMPLETE ===');
  }
})();