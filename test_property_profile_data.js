import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  const page = await browser.newPage();
  
  console.log('Testing Property Profile: 6390 NW 95 LN, Parkland');
  console.log('=' + '='.repeat(59));
  
  // Navigate to the property profile
  const url = 'http://localhost:5174/properties/parkland/6390%20NW%2095%20LN';
  console.log(`\nNavigating to: ${url}`);
  
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    console.log('✓ Page loaded successfully');
  } catch (error) {
    console.log('✗ Failed to load page:', error.message);
    await browser.close();
    return;
  }
  
  // Wait for content to load
  await page.waitForTimeout(3000);
  
  // Take a screenshot
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ 
    path: `property_profile_${timestamp}.png`,
    fullPage: true 
  });
  console.log(`✓ Screenshot saved: property_profile_${timestamp}.png`);
  
  // Check if we're getting data from the API
  console.log('\n--- CHECKING API CALLS ---');
  
  // Set up request monitoring
  const apiCalls = [];
  page.on('response', response => {
    if (response.url().includes('/api/') || response.url().includes('supabase')) {
      apiCalls.push({
        url: response.url(),
        status: response.status(),
        ok: response.ok()
      });
    }
  });
  
  // Reload to capture API calls
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  console.log('API calls made:');
  apiCalls.forEach(call => {
    console.log(`  ${call.ok ? '✓' : '✗'} ${call.status} - ${call.url}`);
    if (!call.ok && call.url.includes('florida_parcels')) {
      console.log(`    ERROR URL: ${call.url}`);
    }
  });
  
  // Check for loading or error states
  console.log('\n--- CHECKING PAGE STATE ---');
  
  const isLoading = await page.locator('.animate-pulse').count();
  if (isLoading > 0) {
    console.log('⚠ Page is still in loading state (skeleton screens visible)');
  }
  
  const errorElements = await page.locator('text=/error|Error|failed|Failed/i').count();
  if (errorElements > 0) {
    console.log('✗ Error messages found on page');
    const errors = await page.locator('text=/error|Error|failed|Failed/i').allTextContents();
    errors.forEach(err => console.log(`  Error: ${err}`));
  }
  
  // Check Overview Tab data
  console.log('\n--- CHECKING OVERVIEW TAB ---');
  
  // Check if Overview tab is active
  const overviewTab = page.locator('[role="tab"]:has-text("Overview")');
  if (await overviewTab.count() > 0) {
    await overviewTab.click();
    await page.waitForTimeout(1000);
    console.log('✓ Overview tab clicked');
  }
  
  // Check for key data fields
  const dataChecks = [
    { selector: 'text=/Market Value|market value/i', field: 'Market Value' },
    { selector: 'text=/Assessed Value|assessed value/i', field: 'Assessed Value' },
    { selector: 'text=/Land Value|land value/i', field: 'Land Value' },
    { selector: 'text=/Building Value|building value/i', field: 'Building Value' },
    { selector: 'text=/Year Built|year built/i', field: 'Year Built' },
    { selector: 'text=/Living Area|living area/i', field: 'Living Area' },
    { selector: 'text=/Bedrooms|bedrooms/i', field: 'Bedrooms' },
    { selector: 'text=/Bathrooms|bathrooms/i', field: 'Bathrooms' },
    { selector: 'text=/Last Sale|last sale/i', field: 'Last Sale' }
  ];
  
  for (const check of dataChecks) {
    const elements = await page.locator(check.selector).count();
    if (elements > 0) {
      // Try to find the associated value
      const parentElement = page.locator(check.selector).first();
      const parent = await parentElement.locator('..').textContent().catch(() => '');
      
      // Check if it shows N/A or actual data
      if (parent.includes('N/A') || parent.includes('Unknown')) {
        console.log(`✗ ${check.field}: Shows N/A or Unknown`);
      } else if (parent.match(/\$[\d,]+/) || parent.match(/\d{4}/) || parent.match(/\d+/)) {
        console.log(`✓ ${check.field}: Has data (${parent.substring(0, 50)}...)`);
      } else {
        console.log(`? ${check.field}: Found but unclear if has data`);
      }
    } else {
      console.log(`✗ ${check.field}: Not found on page`);
    }
  }
  
  // Check Core Property Info Tab
  console.log('\n--- CHECKING CORE PROPERTY INFO TAB ---');
  
  const coreTab = page.locator('[role="tab"]:has-text("Core Property Info")');
  if (await coreTab.count() > 0) {
    await coreTab.click();
    await page.waitForTimeout(1000);
    console.log('✓ Core Property Info tab clicked');
    
    // Take screenshot of this tab
    await page.screenshot({ 
      path: `property_core_tab_${timestamp}.png`,
      fullPage: true 
    });
    
    // Check for subdivision, legal description, etc.
    const coreFields = ['Subdivision', 'Legal Description', 'Zoning', 'Stories'];
    for (const field of coreFields) {
      const hasField = await page.locator(`text=/${field}/i`).count();
      console.log(`  ${hasField > 0 ? '✓' : '✗'} ${field} ${hasField > 0 ? 'present' : 'missing'}`);
    }
  }
  
  // Check browser console for errors
  console.log('\n--- CHECKING CONSOLE ERRORS ---');
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`✗ Console error: ${msg.text()}`);
    }
  });
  
  // Check if Supabase data is being fetched
  console.log('\n--- CHECKING DATA HOOK ---');
  
  // Evaluate JavaScript in the page context
  const dataStatus = await page.evaluate(() => {
    // Check if React DevTools are available
    const hasReact = window.React || window._REACT_DEVTOOLS_GLOBAL_HOOK_;
    
    // Check localStorage for Supabase data
    const supabaseAuth = localStorage.getItem('sb-pmispwtdngkcmsrsjwbp-auth-token');
    
    // Check if any property data elements exist
    const hasPropertyData = document.body.textContent.includes('484104011450') || // parcel ID
                          document.body.textContent.includes('BESSELL') || // owner name
                          document.body.textContent.includes('6390 NW 95'); // address
    
    return {
      hasReact,
      hasSupabaseAuth: !!supabaseAuth,
      hasPropertyData,
      bodyText: document.body.textContent.substring(0, 500)
    };
  });
  
  console.log(`React detected: ${dataStatus.hasReact ? 'Yes' : 'No'}`);
  console.log(`Supabase auth: ${dataStatus.hasSupabaseAuth ? 'Yes' : 'No'}`);
  console.log(`Property data in page: ${dataStatus.hasPropertyData ? 'Yes' : 'No'}`);
  
  if (!dataStatus.hasPropertyData) {
    console.log('\n⚠ Page content preview (first 500 chars):');
    console.log(dataStatus.bodyText);
  }
  
  // Final summary
  console.log('\n' + '='.repeat(60));
  console.log('SUMMARY:');
  
  if (errorElements > 0) {
    console.log('✗ Page has errors - data fetch likely failed');
  } else if (isLoading > 0) {
    console.log('⚠ Page stuck in loading state');
  } else if (!dataStatus.hasPropertyData) {
    console.log('✗ No property data found on page - API/hook issue');
  } else {
    console.log('✓ Property data is displaying');
  }
  
  console.log(`\nScreenshots saved for visual inspection`);
  
  await browser.close();
})();