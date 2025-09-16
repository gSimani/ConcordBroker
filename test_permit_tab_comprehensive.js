const { chromium } = require('playwright');

async function testPermitTab() {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  const page = await browser.newPage();
  
  console.log('COMPREHENSIVE PERMIT TAB TESTING');
  console.log('=' * 60);
  
  // Test properties with different addresses
  const testProperties = [
    '3930 SW 53 CT',
    '123 Main St',
    '456 Ocean Dr',
    '789 Las Olas',
    '1000 Biscayne'
  ];
  
  for (const address of testProperties) {
    console.log(`\nTesting property: ${address}`);
    console.log('-'.repeat(40));
    
    try {
      // Navigate to properties page
      await page.goto('http://localhost:5174/properties');
      await page.waitForTimeout(2000);
      
      // Search for property
      const searchInput = await page.locator('input[placeholder*="Search"]').first();
      await searchInput.fill(address);
      await page.waitForTimeout(1500);
      
      // Click on first property result if available
      const propertyCard = await page.locator('.property-card, [class*="card"]').first();
      if (await propertyCard.isVisible()) {
        await propertyCard.click();
        await page.waitForTimeout(2000);
        
        // Wait for property page to load
        await page.waitForSelector('[class*="tab"], button:has-text("Permit")', { timeout: 10000 });
        
        // Click on Permit tab
        const permitTab = await page.locator('button:has-text("Permit"), [role="tab"]:has-text("Permit")').first();
        if (await permitTab.isVisible()) {
          console.log('  ✓ Permit tab found');
          await permitTab.click();
          await page.waitForTimeout(2000);
          
          // Check what's displayed in the Permit tab
          const permitContent = await page.locator('[role="tabpanel"], .permit-content, [class*="permit"]').first();
          
          // Check for permit data
          const hasPermitData = await page.locator('text=/permit.*number|building.*permit|permit.*type/i').count() > 0;
          const hasEmptyState = await page.locator('text=/no.*permit|permit.*data.*not|no.*building.*permit/i').count() > 0;
          const hasLoadingState = await page.locator('.animate-pulse, [class*="loading"], [class*="skeleton"]').count() > 0;
          
          if (hasLoadingState) {
            console.log('  ⏳ Loading state detected');
            await page.waitForTimeout(3000);
          }
          
          // Check for permit fields
          const permitFields = [
            'Permit Number',
            'Permit Type',
            'Status',
            'Issue Date',
            'Applicant',
            'Contractor',
            'Job Value',
            'Description'
          ];
          
          let fieldsFound = [];
          let fieldsMissing = [];
          
          for (const field of permitFields) {
            const fieldExists = await page.locator(`text=/${field}/i`).count() > 0;
            if (fieldExists) {
              fieldsFound.push(field);
            } else {
              fieldsMissing.push(field);
            }
          }
          
          // Report findings
          if (hasPermitData && fieldsFound.length > 0) {
            console.log(`  ✅ Permit data found with ${fieldsFound.length} fields`);
            console.log(`     Fields present: ${fieldsFound.join(', ')}`);
            
            // Check for actual permit records
            const permitNumbers = await page.locator('text=/B\\d+-\\d+|BRO-\\d+|FTL-\\d+|PB-\\d+/').allTextContents();
            if (permitNumbers.length > 0) {
              console.log(`     Permit records: ${permitNumbers.slice(0, 3).join(', ')}`);
            }
          } else if (hasEmptyState) {
            console.log('  ℹ️  Empty state displayed - no permit data');
            
            // Check if it shows the data source message
            const hasDataSourceMsg = await page.locator('text=/Hollywood.*Accela|Broward.*BCS|ENVIROS/i').count() > 0;
            if (hasDataSourceMsg) {
              console.log('     Shows data source information');
            }
          } else {
            console.log(`  ⚠️  Unexpected state - fields missing`);
            if (fieldsMissing.length > 0) {
              console.log(`     Missing fields: ${fieldsMissing.join(', ')}`);
            }
          }
          
          // Take screenshot for debugging
          await page.screenshot({ 
            path: `ui_screenshots/permit_tab_${address.replace(/\s+/g, '_')}_${Date.now()}.png`,
            fullPage: false 
          });
          
          // Check console errors
          page.on('console', msg => {
            if (msg.type() === 'error') {
              console.log(`  ❌ Console error: ${msg.text()}`);
            }
          });
          
        } else {
          console.log('  ❌ Permit tab not found');
        }
        
      } else {
        console.log('  ⚠️  No property found for this address');
      }
      
    } catch (error) {
      console.log(`  ❌ Error testing ${address}: ${error.message}`);
    }
  }
  
  // Test specific property page directly
  console.log('\n\nDirect Property Page Test');
  console.log('=' * 60);
  
  try {
    // Try to navigate to a specific property page
    await page.goto('http://localhost:5174/property/5142-29-03-0170');
    await page.waitForTimeout(3000);
    
    // Check if Permit tab exists
    const permitTab = await page.locator('button:has-text("Permit"), [role="tab"]:has-text("Permit")').first();
    if (await permitTab.isVisible()) {
      await permitTab.click();
      await page.waitForTimeout(2000);
      
      // Detailed field check
      console.log('\nDetailed Field Analysis:');
      const detailedFields = {
        'Summary Stats': ['Total Permits', 'Active Permits', 'Total Project Value', 'Total Fees'],
        'Permit Details': ['Permit Number', 'Job Name', 'Application Type', 'Film Number'],
        'Timeline': ['Application Date', 'Permit Date', 'CO/CC Date', 'Expiration Date'],
        'Financial': ['Job Value', 'Square Footage', 'Total Fees', 'Balance'],
        'Parties': ['Applicant Name', 'Contractor Name', 'Contractor License']
      };
      
      for (const [section, fields] of Object.entries(detailedFields)) {
        console.log(`\n  ${section}:`);
        for (const field of fields) {
          const exists = await page.locator(`text=/${field}/i`).count() > 0;
          console.log(`    ${exists ? '✓' : '✗'} ${field}`);
        }
      }
    }
    
  } catch (error) {
    console.log(`Direct navigation error: ${error.message}`);
  }
  
  // Final summary
  console.log('\n\nTEST SUMMARY');
  console.log('=' * 60);
  console.log('Check ui_screenshots folder for visual verification');
  console.log('Review console output above for field presence');
  
  await browser.close();
}

testPermitTab().catch(console.error);