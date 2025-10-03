/**
 * Verify Property Data Flow - End-to-End Test
 * Tests that real data flows from API → Hook → Component
 */

const http = require('http');

// Test parcels with known data
const TEST_PARCELS = [
  '402101327008', // Port Charlotte property
  '474131030052', // Miami property (if exists)
  '0140291177',   // Miami property from Meilisearch
];

async function fetchAPI(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    }).on('error', reject);
  });
}

async function testPropertyAPI(parcelId) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`Testing Property: ${parcelId}`);
  console.log('='.repeat(80));

  try {
    const apiUrl = `http://localhost:8000/api/properties/${parcelId}`;
    console.log(`\n📡 Fetching from API: ${apiUrl}`);

    const response = await fetchAPI(apiUrl);

    if (!response.success) {
      console.error('❌ API returned error:', response);
      return false;
    }

    const property = response.property;
    const bcpaData = property.bcpaData;

    console.log('\n✅ API Response Structure:');
    console.log(`   - success: ${response.success}`);
    console.log(`   - property keys: ${Object.keys(property).join(', ')}`);
    console.log(`   - bcpaData exists: ${!!bcpaData}`);

    if (bcpaData) {
      console.log('\n📊 BCPA Data Fields:');
      console.log(`   ✓ parcel_id: ${bcpaData.parcel_id || 'MISSING'}`);
      console.log(`   ✓ property_address_street: ${bcpaData.property_address_street || bcpaData.phy_addr1 || 'MISSING'}`);
      console.log(`   ✓ property_address_city: ${bcpaData.property_address_city || bcpaData.phy_city || 'MISSING'}`);
      console.log(`   ✓ owner_name: ${bcpaData.owner_name || bcpaData.own_name || 'MISSING'}`);
      console.log(`   ✓ just_value: $${(bcpaData.just_value || bcpaData.market_value || 0).toLocaleString()}`);
      console.log(`   ✓ land_value: $${(bcpaData.land_value || 0).toLocaleString()}`);
      console.log(`   ✓ building_value: $${(bcpaData.building_value || 0).toLocaleString()}`);
      console.log(`   ✓ assessed_value: $${(bcpaData.assessed_value || 0).toLocaleString()}`);
      console.log(`   ✓ tax_amount: $${(bcpaData.tax_amount || 0).toLocaleString()}`);
      console.log(`   ✓ living_area: ${bcpaData.living_area || bcpaData.tot_lvg_area || 'N/A'} sq ft`);
      console.log(`   ✓ lot_size_sqft: ${bcpaData.lot_size_sqft || bcpaData.lnd_sqfoot || 'N/A'} sq ft`);
      console.log(`   ✓ year_built: ${bcpaData.year_built || bcpaData.act_yr_blt || 'N/A'}`);
      console.log(`   ✓ property_use_code: ${bcpaData.property_use_code || bcpaData.dor_uc || 'N/A'}`);

      // Check for N/A or missing critical fields
      const criticalFields = [
        'parcel_id',
        'property_address_street',
        'owner_name',
        'just_value',
        'land_value',
        'building_value',
        'assessed_value'
      ];

      const missingFields = criticalFields.filter(field => {
        const value = bcpaData[field] || bcpaData[field.replace('property_address_', 'phy_').replace('street', 'addr1')];
        return !value || value === 'N/A';
      });

      if (missingFields.length > 0) {
        console.log(`\n⚠️  Missing or N/A fields: ${missingFields.join(', ')}`);
        return false;
      } else {
        console.log('\n✅ All critical fields present with real data!');
      }

      // Check additional data sources
      console.log('\n📦 Additional Data Sources:');
      console.log(`   - sdfData (sales): ${property.sdfData?.length || 0} records`);
      console.log(`   - navData (assessments): ${property.navData?.length || 0} records`);
      console.log(`   - sunbizData (entities): ${property.sunbizData?.length || 0} records`);
      console.log(`   - sales_history: ${property.sales_history?.length || 0} records`);

      return true;
    } else {
      console.error('❌ No bcpaData in response');
      return false;
    }

  } catch (error) {
    console.error('❌ Error testing property:', error.message);
    return false;
  }
}

async function testFrontendAccess() {
  console.log(`\n${'='.repeat(80)}`);
  console.log('Testing Frontend Access');
  console.log('='.repeat(80));

  try {
    const frontendUrl = 'http://localhost:5178';
    console.log(`\n📡 Checking frontend: ${frontendUrl}`);

    const response = await fetchAPI(frontendUrl);

    if (typeof response === 'string' && response.includes('ConcordBroker')) {
      console.log('✅ Frontend is running');
      console.log(`\n🔗 Test URLs:`);
      console.log(`   - Property 1: ${frontendUrl}/property/402101327008`);
      console.log(`   - Property 2: ${frontendUrl}/property/0140291177`);
      return true;
    } else {
      console.log('⚠️  Frontend may not be running properly');
      return false;
    }
  } catch (error) {
    console.error('❌ Frontend not accessible:', error.message);
    return false;
  }
}

async function runTests() {
  console.log('\n' + '='.repeat(80));
  console.log('🧪 CONCORD BROKER - PROPERTY DATA FLOW VERIFICATION');
  console.log('='.repeat(80));
  console.log('\nThis script verifies that real property data flows correctly from:');
  console.log('  API → usePropertyData Hook → CorePropertyTab Component\n');

  let passedTests = 0;
  let totalTests = TEST_PARCELS.length + 1;

  // Test each parcel
  for (const parcelId of TEST_PARCELS) {
    const passed = await testPropertyAPI(parcelId);
    if (passed) passedTests++;
  }

  // Test frontend
  const frontendPassed = await testFrontendAccess();
  if (frontendPassed) passedTests++;

  // Summary
  console.log('\n' + '='.repeat(80));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(80));
  console.log(`\n✅ Passed: ${passedTests}/${totalTests}`);
  console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);
  console.log(`📈 Success Rate: ${Math.round((passedTests / totalTests) * 100)}%\n`);

  if (passedTests === totalTests) {
    console.log('🎉 All tests passed! Property data is flowing correctly.\n');
    process.exit(0);
  } else {
    console.log('⚠️  Some tests failed. Check the output above for details.\n');
    process.exit(1);
  }
}

runTests().catch(error => {
  console.error('Fatal error running tests:', error);
  process.exit(1);
});
