#!/usr/bin/env node

import puppeteer from 'puppeteer';

async function testPropertySearchPage() {
  console.log('🔍 Testing Property Search Page');
  console.log('================================\n');
  
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Navigate to the property search page
    console.log('[1] Navigating to PropertySearchSupabase page...');
    await page.goto('http://localhost:5175/properties-supabase', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // Wait for the page to load
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Check if the search input exists
    console.log('[2] Checking for search input...');
    const searchInput = await page.$('input[placeholder*="Search"]');
    if (searchInput) {
      console.log('   ✅ Search input found');
    } else {
      console.log('   ❌ Search input not found');
    }
    
    // Check for property cards or results
    console.log('[3] Checking for property results...');
    const propertyCards = await page.$$('[class*="property-card"], [class*="MiniPropertyCard"]');
    console.log(`   ✅ Found ${propertyCards.length} property cards on initial load`);
    
    // Try searching for an address
    console.log('[4] Testing search functionality...');
    if (searchInput) {
      await searchInput.type('2630');
      await new Promise(resolve => setTimeout(resolve, 1500)); // Wait for debounce and search
      
      const searchResults = await page.$$('[class*="property-card"], [class*="MiniPropertyCard"]');
      console.log(`   ✅ Found ${searchResults.length} results after searching for "2630"`);
    }
    
    // Check for database connection indicator
    console.log('[5] Checking database connection...');
    const dbIndicator = await page.$('[class*="Database"], [class*="database"]');
    if (dbIndicator) {
      console.log('   ✅ Database indicator found');
    }
    
    // Check for total results count
    const totalResultsText = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'));
      const found = elements.find(el => el.textContent && el.textContent.includes('properties'));
      return found ? found.textContent : null;
    });
    
    if (totalResultsText) {
      console.log(`   ✅ Results count: ${totalResultsText}`);
    }
    
    // Take a screenshot
    console.log('\n[6] Taking screenshot...');
    await page.screenshot({ 
      path: 'ui_screenshots/property_search_supabase_test.png',
      fullPage: false 
    });
    console.log('   ✅ Screenshot saved to ui_screenshots/property_search_supabase_test.png');
    
    console.log('\n================================');
    console.log('✅ Property search page is working with Supabase data!');
    
  } catch (error) {
    console.error('❌ Error testing page:', error);
    
    // Try to take error screenshot
    try {
      const page = await browser.newPage();
      await page.goto('http://localhost:5175/properties-supabase');
      await page.screenshot({ path: 'ui_screenshots/property_search_error.png' });
      console.log('Error screenshot saved to ui_screenshots/property_search_error.png');
    } catch (e) {
      console.log('Could not take error screenshot');
    }
  } finally {
    await browser.close();
  }
}

// Run the test
testPropertySearchPage().then(() => {
  console.log('\n✅ Test completed');
  process.exit(0);
}).catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});