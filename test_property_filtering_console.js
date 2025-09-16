// Console test for property type filtering
// Open http://localhost:5173/properties and paste this in the browser console

console.log('🔍 Testing Property Type Filtering in Console...\n');

// Function to test property type filtering
async function testPropertyTypeFiltering() {
  console.log('1️⃣ Testing property type tab clicks and API calls...\n');

  // Monitor network requests
  const originalFetch = window.fetch;
  const apiCalls = [];

  window.fetch = function(...args) {
    const url = args[0];
    const options = args[1] || {};

    if (url.includes('/api/properties/search')) {
      console.log('📡 API Call detected:', url);
      if (options.method === 'POST' && options.body) {
        try {
          const body = JSON.parse(options.body);
          console.log('📝 API Request body:', body);
          apiCalls.push({ url, body, timestamp: Date.now() });
        } catch (e) {
          console.log('📝 API Request body (non-JSON):', options.body);
        }
      }
    }

    return originalFetch.apply(this, args);
  };

  // Test each property type
  const propertyTypes = ['Residential', 'Commercial', 'Industrial', 'Agricultural', 'Vacant'];

  for (const propertyType of propertyTypes) {
    console.log(`\n2️⃣ Testing ${propertyType} filtering...`);

    // Find and click the tab
    const tabButton = Array.from(document.querySelectorAll('button')).find(btn =>
      btn.textContent.includes(propertyType) && btn.classList.contains('tab-executive')
    );

    if (tabButton) {
      console.log(`   ✅ ${propertyType} tab found, clicking...`);

      // Clear previous API calls
      apiCalls.length = 0;

      // Click the tab
      tabButton.click();

      // Wait for potential API calls
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Check for API calls
      if (apiCalls.length > 0) {
        console.log(`   📡 ${apiCalls.length} API call(s) made`);
        apiCalls.forEach((call, index) => {
          console.log(`   📋 Call ${index + 1}:`, call.body);
        });
      } else {
        console.log(`   ❌ No API calls detected for ${propertyType}`);
      }

      // Check current filter state (if available in React DevTools)
      if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        console.log(`   🔧 React DevTools available - check component state`);
      }

      // Check for property count changes
      const resultsElements = Array.from(document.querySelectorAll('*')).filter(el =>
        el.textContent && el.textContent.match(/\d+\s*(properties|results)/i)
      );

      if (resultsElements.length > 0) {
        const resultsText = resultsElements[0].textContent;
        console.log(`   📊 Current results: ${resultsText}`);
      }

    } else {
      console.log(`   ❌ ${propertyType} tab not found`);
    }
  }

  // Restore original fetch
  window.fetch = originalFetch;

  console.log('\n📋 Filter Testing Summary:');
  console.log(`✅ Tabs tested: ${propertyTypes.length}`);
  console.log(`✅ API monitoring: ACTIVE`);
  console.log(`✅ Filter changes: TRACKED`);
  console.log('\n💡 Check the console output above for API calls and filter changes');
}

// Auto-run the test
testPropertyTypeFiltering().catch(console.error);

// Also provide manual test functions
window.testPropertyTypeFiltering = testPropertyTypeFiltering;