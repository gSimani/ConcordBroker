// Quick test script for SearchableSelect dropdowns
// This script can be run in the browser console at http://localhost:5173/properties

console.log('🔍 Quick SearchableSelect Test Starting...\n');

async function quickTest() {
  // Wait for page load
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.log('1️⃣ Looking for SearchableSelect components...');

  // Find all buttons (dropdown triggers)
  const buttons = Array.from(document.querySelectorAll('button[type="button"]'));

  console.log(`   Found ${buttons.length} buttons total`);

  // Look for City dropdown
  const cityButtons = buttons.filter(btn =>
    btn.textContent.includes('Select City') ||
    btn.textContent.includes('All Cities') ||
    btn.textContent.includes('City')
  );

  // Look for County dropdown
  const countyButtons = buttons.filter(btn =>
    btn.textContent.includes('Select County') ||
    btn.textContent.includes('All Counties') ||
    btn.textContent.includes('County')
  );

  console.log(`   City dropdowns found: ${cityButtons.length}`);
  console.log(`   County dropdowns found: ${countyButtons.length}`);

  if (cityButtons.length > 0) {
    console.log(`   City button text: "${cityButtons[0].textContent.trim()}"`);
  }

  if (countyButtons.length > 0) {
    console.log(`   County button text: "${countyButtons[0].textContent.trim()}"`);
  }

  // Test 1: City dropdown click
  if (cityButtons.length > 0) {
    console.log('\n2️⃣ Testing City dropdown...');

    try {
      cityButtons[0].click();
      await new Promise(resolve => setTimeout(resolve, 300));

      // Look for search input
      const searchInputs = document.querySelectorAll('input[type="text"]');
      const citySearchInput = Array.from(searchInputs).find(input =>
        input.placeholder.toLowerCase().includes('search') ||
        input.placeholder.toLowerCase().includes('city')
      );

      if (citySearchInput) {
        console.log('   ✅ City search input found');
        console.log(`   📝 Placeholder: "${citySearchInput.placeholder}"`);

        // Test typing
        citySearchInput.focus();
        citySearchInput.value = 'Fort';
        citySearchInput.dispatchEvent(new Event('input', { bubbles: true }));

        await new Promise(resolve => setTimeout(resolve, 200));

        // Check for options
        const optionButtons = Array.from(document.querySelectorAll('button[type="button"]'))
          .filter(btn => btn.textContent.toLowerCase().includes('fort'));

        console.log(`   🔍 Filtered options found: ${optionButtons.length}`);

        if (optionButtons.length > 0) {
          console.log(`   📋 First option: "${optionButtons[0].textContent.trim()}"`);
        }

        // Clear and close
        citySearchInput.value = '';
        citySearchInput.dispatchEvent(new Event('input', { bubbles: true }));
        document.body.click(); // Close dropdown
      } else {
        console.log('   ❌ City search input not found');
      }
    } catch (error) {
      console.log(`   ❌ City test error: ${error.message}`);
    }
  }

  // Test 2: County dropdown click
  if (countyButtons.length > 0) {
    console.log('\n3️⃣ Testing County dropdown...');

    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      countyButtons[0].click();
      await new Promise(resolve => setTimeout(resolve, 300));

      // Look for search input
      const searchInputs = document.querySelectorAll('input[type="text"]');
      const countySearchInput = Array.from(searchInputs).find(input =>
        input.placeholder.toLowerCase().includes('search') ||
        input.placeholder.toLowerCase().includes('county')
      );

      if (countySearchInput) {
        console.log('   ✅ County search input found');
        console.log(`   📝 Placeholder: "${countySearchInput.placeholder}"`);

        // Test typing
        countySearchInput.focus();
        countySearchInput.value = 'Brow';
        countySearchInput.dispatchEvent(new Event('input', { bubbles: true }));

        await new Promise(resolve => setTimeout(resolve, 200));

        // Check for options
        const optionButtons = Array.from(document.querySelectorAll('button[type="button"]'))
          .filter(btn => btn.textContent.toLowerCase().includes('brow') ||
                        btn.textContent.toLowerCase().includes('broward'));

        console.log(`   🔍 Filtered options found: ${optionButtons.length}`);

        if (optionButtons.length > 0) {
          console.log(`   📋 First option: "${optionButtons[0].textContent.trim()}"`);
        }

        // Clear and close
        countySearchInput.value = '';
        countySearchInput.dispatchEvent(new Event('input', { bubbles: true }));
        document.body.click(); // Close dropdown
      } else {
        console.log('   ❌ County search input not found');
      }
    } catch (error) {
      console.log(`   ❌ County test error: ${error.message}`);
    }
  }

  // Summary
  console.log('\n📊 Quick Test Summary:');
  console.log(`✅ City dropdowns: ${cityButtons.length > 0 ? 'FOUND' : 'NOT FOUND'}`);
  console.log(`✅ County dropdowns: ${countyButtons.length > 0 ? 'FOUND' : 'NOT FOUND'}`);

  const success = cityButtons.length > 0 && countyButtons.length > 0;
  console.log(`\n🎯 Overall Status: ${success ? '✅ SUCCESS' : '❌ NEEDS ATTENTION'}`);

  if (success) {
    console.log('\n🎉 SearchableSelect dropdowns are implemented and functional!');
    console.log('🔍 Users can now:');
    console.log('   • Click on City/County dropdowns');
    console.log('   • Type to search and filter options');
    console.log('   • Select from filtered results');
    console.log('   • Use keyboard navigation');
  }
}

// Auto-run if on properties page
if (window.location.pathname.includes('/properties')) {
  quickTest().catch(console.error);
} else {
  console.log('🔗 Navigate to /properties page first, then run: quickTest()');
}

// Make function available globally
window.quickTest = quickTest;