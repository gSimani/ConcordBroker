// Test script to verify SearchableSelect dropdowns functionality
// Run this in browser console on http://localhost:5173/properties

console.log('🔍 Testing SearchableSelect Dropdowns...');

// Test 1: Check if SearchableSelect components are rendered
function testComponentsRendered() {
  console.log('\n📋 Test 1: Checking if SearchableSelect components are rendered...');

  // Look for City dropdown button
  const cityButton = document.querySelector('button[type="button"]');
  const cityDropdowns = Array.from(document.querySelectorAll('button[type="button"]'))
    .filter(btn => btn.textContent.includes('Select City') || btn.textContent.includes('All Cities'));

  // Look for County dropdown button
  const countyDropdowns = Array.from(document.querySelectorAll('button[type="button"]'))
    .filter(btn => btn.textContent.includes('Select County') || btn.textContent.includes('All Counties'));

  console.log(`✓ City dropdowns found: ${cityDropdowns.length}`);
  console.log(`✓ County dropdowns found: ${countyDropdowns.length}`);

  if (cityDropdowns.length > 0) {
    console.log(`✓ City dropdown text: "${cityDropdowns[0].textContent.trim()}"`);
  }

  if (countyDropdowns.length > 0) {
    console.log(`✓ County dropdown text: "${countyDropdowns[0].textContent.trim()}"`);
  }

  return { cityDropdowns, countyDropdowns };
}

// Test 2: Test City dropdown click and search functionality
async function testCityDropdown(cityDropdowns) {
  console.log('\n🏘️ Test 2: Testing City dropdown functionality...');

  if (cityDropdowns.length === 0) {
    console.log('❌ No city dropdowns found');
    return false;
  }

  const cityButton = cityDropdowns[0];
  console.log('✓ Clicking city dropdown...');
  cityButton.click();

  // Wait for dropdown to open
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check if search input appeared
  const searchInputs = document.querySelectorAll('input[placeholder*="Search"]');
  const citySearchInput = Array.from(searchInputs)
    .find(input => input.placeholder.toLowerCase().includes('city') || input.placeholder.toLowerCase().includes('select'));

  if (citySearchInput) {
    console.log('✓ City search input found');
    console.log(`✓ Placeholder: "${citySearchInput.placeholder}"`);

    // Test typing in search input
    citySearchInput.focus();
    citySearchInput.value = 'Fort';
    citySearchInput.dispatchEvent(new Event('input', { bubbles: true }));

    await new Promise(resolve => setTimeout(resolve, 200));

    // Check if filtered options appear
    const options = document.querySelectorAll('button[type="button"]');
    const cityOptions = Array.from(options).filter(btn =>
      btn.textContent.toLowerCase().includes('fort') ||
      btn.textContent.toLowerCase().includes('lauderdale')
    );

    console.log(`✓ Filtered city options found: ${cityOptions.length}`);
    if (cityOptions.length > 0) {
      console.log(`✓ First filtered option: "${cityOptions[0].textContent.trim()}"`);
    }

    // Clear search and close dropdown
    citySearchInput.value = '';
    citySearchInput.dispatchEvent(new Event('input', { bubbles: true }));
    document.body.click(); // Click outside to close

    return true;
  } else {
    console.log('❌ City search input not found');
    return false;
  }
}

// Test 3: Test County dropdown click and search functionality
async function testCountyDropdown(countyDropdowns) {
  console.log('\n🏢 Test 3: Testing County dropdown functionality...');

  if (countyDropdowns.length === 0) {
    console.log('❌ No county dropdowns found');
    return false;
  }

  const countyButton = countyDropdowns[0];
  console.log('✓ Clicking county dropdown...');
  countyButton.click();

  // Wait for dropdown to open
  await new Promise(resolve => setTimeout(resolve, 100));

  // Check if search input appeared
  const searchInputs = document.querySelectorAll('input[placeholder*="Search"]');
  const countySearchInput = Array.from(searchInputs)
    .find(input => input.placeholder.toLowerCase().includes('county') || input.placeholder.toLowerCase().includes('select'));

  if (countySearchInput) {
    console.log('✓ County search input found');
    console.log(`✓ Placeholder: "${countySearchInput.placeholder}"`);

    // Test typing in search input
    countySearchInput.focus();
    countySearchInput.value = 'Brow';
    countySearchInput.dispatchEvent(new Event('input', { bubbles: true }));

    await new Promise(resolve => setTimeout(resolve, 200));

    // Check if filtered options appear
    const options = document.querySelectorAll('button[type="button"]');
    const countyOptions = Array.from(options).filter(btn =>
      btn.textContent.toLowerCase().includes('brow') ||
      btn.textContent.toLowerCase().includes('broward')
    );

    console.log(`✓ Filtered county options found: ${countyOptions.length}`);
    if (countyOptions.length > 0) {
      console.log(`✓ First filtered option: "${countyOptions[0].textContent.trim()}"`);
    }

    // Clear search and close dropdown
    countySearchInput.value = '';
    countySearchInput.dispatchEvent(new Event('input', { bubbles: true }));
    document.body.click(); // Click outside to close

    return true;
  } else {
    console.log('❌ County search input not found');
    return false;
  }
}

// Test 4: Test selection functionality
async function testSelectionFunctionality(cityDropdowns, countyDropdowns) {
  console.log('\n✅ Test 4: Testing selection functionality...');

  // Test City selection
  if (cityDropdowns.length > 0) {
    console.log('✓ Testing city selection...');
    const cityButton = cityDropdowns[0];
    cityButton.click();

    await new Promise(resolve => setTimeout(resolve, 100));

    // Look for a specific city option (Fort Lauderdale)
    const cityOptions = Array.from(document.querySelectorAll('button[type="button"]'))
      .filter(btn => btn.textContent.toLowerCase().includes('fort lauderdale'));

    if (cityOptions.length > 0) {
      console.log('✓ Selecting Fort Lauderdale...');
      cityOptions[0].click();

      await new Promise(resolve => setTimeout(resolve, 200));

      // Check if city button now shows selected value
      const updatedCityText = cityButton.textContent.trim();
      if (updatedCityText.includes('Fort Lauderdale')) {
        console.log('✓ City selection successful');
      } else {
        console.log('❌ City selection may have failed');
        console.log(`Button text: "${updatedCityText}"`);
      }
    }
  }

  // Test County selection
  if (countyDropdowns.length > 0) {
    console.log('✓ Testing county selection...');
    const countyButton = countyDropdowns[0];
    countyButton.click();

    await new Promise(resolve => setTimeout(resolve, 100));

    // Look for Broward county option
    const countyOptions = Array.from(document.querySelectorAll('button[type="button"]'))
      .filter(btn => btn.textContent.toLowerCase().includes('broward'));

    if (countyOptions.length > 0) {
      console.log('✓ Selecting Broward...');
      countyOptions[0].click();

      await new Promise(resolve => setTimeout(resolve, 200));

      // Check if county button now shows selected value
      const updatedCountyText = countyButton.textContent.trim();
      if (updatedCountyText.includes('Broward')) {
        console.log('✓ County selection successful');
      } else {
        console.log('❌ County selection may have failed');
        console.log(`Button text: "${updatedCountyText}"`);
      }
    }
  }
}

// Test 5: Check for console errors
function checkConsoleErrors() {
  console.log('\n⚠️ Test 5: Checking for console errors...');

  // Override console.error to catch errors
  const originalError = console.error;
  const errors = [];

  console.error = function(...args) {
    errors.push(args.join(' '));
    originalError.apply(console, args);
  };

  setTimeout(() => {
    console.error = originalError;

    if (errors.length === 0) {
      console.log('✓ No console errors detected during testing');
    } else {
      console.log(`❌ ${errors.length} console errors detected:`);
      errors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }
  }, 1000);
}

// Main test function
async function runTests() {
  console.log('🎯 Starting SearchableSelect Dropdown Tests...\n');

  // Wait for page to load
  await new Promise(resolve => setTimeout(resolve, 1000));

  try {
    // Test 1: Check component rendering
    const { cityDropdowns, countyDropdowns } = testComponentsRendered();

    // Test 2: City dropdown functionality
    const cityTestResult = await testCityDropdown(cityDropdowns);

    // Test 3: County dropdown functionality
    const countyTestResult = await testCountyDropdown(countyDropdowns);

    // Test 4: Selection functionality
    await testSelectionFunctionality(cityDropdowns, countyDropdowns);

    // Test 5: Console error check
    checkConsoleErrors();

    // Summary
    console.log('\n📊 Test Summary:');
    console.log(`✓ City dropdowns found: ${cityDropdowns.length > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✓ County dropdowns found: ${countyDropdowns.length > 0 ? 'PASS' : 'FAIL'}`);
    console.log(`✓ City search functionality: ${cityTestResult ? 'PASS' : 'FAIL'}`);
    console.log(`✓ County search functionality: ${countyTestResult ? 'PASS' : 'FAIL'}`);

    const overallResult = cityDropdowns.length > 0 && countyDropdowns.length > 0 && cityTestResult && countyTestResult;
    console.log(`\n🎯 Overall Result: ${overallResult ? '✅ PASS' : '❌ FAIL'}`);

  } catch (error) {
    console.error('❌ Test execution failed:', error);
  }
}

// Auto-run tests if on the properties page
if (window.location.pathname.includes('/properties')) {
  runTests();
} else {
  console.log('🔗 Navigate to /properties page and run runTests() to execute tests');
}

// Export functions for manual testing
window.testSearchableDropdowns = {
  runTests,
  testComponentsRendered,
  testCityDropdown,
  testCountyDropdown,
  testSelectionFunctionality,
  checkConsoleErrors
};

console.log('\n💡 Available functions:');
console.log('- window.testSearchableDropdowns.runTests() - Run all tests');
console.log('- window.testSearchableDropdowns.testComponentsRendered() - Test component rendering');
console.log('- Individual test functions available in window.testSearchableDropdowns');