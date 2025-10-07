// Test Building SqFt filters after API restart

async function testBuildingSqFt() {
  console.log('🏠 Testing Building Square Footage Filters\n');
  console.log('⚠️  NOTE: Restart the API first with: cd apps/api && python property_live_api.py\n');

  // Test 1: Basic search to see what building sizes exist
  console.log('📍 Test 1: Sample properties with building sqft');
  const url1 = 'http://localhost:8000/api/properties/search?limit=20&offset=0';

  try {
    const response1 = await fetch(url1);
    const data1 = await response1.json();

    if (data1.data && data1.data.length > 0) {
      // Filter properties that have building sqft > 0
      const withBuildings = data1.data.filter(p => (p.buildingSqFt || p.total_living_area || 0) > 0);

      console.log(`   Found ${withBuildings.length} properties with buildings out of ${data1.data.length} total\n`);

      if (withBuildings.length > 0) {
        console.log('   Sample building sizes:');
        withBuildings.slice(0, 5).forEach((prop, i) => {
          const sqft = prop.buildingSqFt || prop.total_living_area || 0;
          console.log(`   ${i+1}. ${(prop.phy_addr1 || 'No Address').padEnd(30)} - ${sqft.toLocaleString()} sqft`);
        });
      } else {
        console.log('   ⚠️  No properties with building data in first 20 results');
        console.log('   This is common - many parcels are vacant land');
      }
    }
  } catch (e) {
    console.error('   ❌ Error:', e.message);
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // Test 2: Filter for buildings between 2000-5000 sqft
  console.log('📍 Test 2: Properties with 2,000-5,000 sqft buildings');
  const url2 = 'http://localhost:8000/api/properties/search?minBuildingSqFt=2000&maxBuildingSqFt=5000&limit=10';
  console.log('   URL:', url2);

  try {
    const response2 = await fetch(url2);
    const data2 = await response2.json();

    if (!data2.success) {
      console.error('   ❌ API Error:', data2.error);
      console.log('\n   🔧 This error means the API needs to be restarted to load the fixes!');
      console.log('   Run: cd apps/api && python property_live_api.py');
      return;
    }

    console.log('   Results:', data2.data?.length || 0, 'properties');
    console.log('   Total:', data2.pagination?.total || 0);

    if (data2.data && data2.data.length > 0) {
      console.log('\n   Building sizes:');
      data2.data.forEach((prop, i) => {
        const sqft = prop.buildingSqFt || prop.total_living_area || 0;
        const inRange = sqft >= 2000 && sqft <= 5000;
        console.log(`   ${i+1}. ${(prop.phy_addr1 || prop.phy_city || 'No Address').padEnd(30)} - ${sqft.toLocaleString().padStart(6)} sqft ${inRange ? '✅' : '❌'}`);
      });

      // Check if all are in range
      const allInRange = data2.data.every(prop => {
        const sqft = prop.buildingSqFt || prop.total_living_area || 0;
        return sqft >= 2000 && sqft <= 5000;
      });

      console.log('\n   ' + (allInRange ? '✅ ALL IN RANGE!' : '❌ SOME OUT OF RANGE'));
    } else {
      console.log('   ℹ️  No results - this may be expected if filters are too restrictive');
    }
  } catch (e) {
    console.error('   ❌ Error:', e.message);
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ Test Complete');
  console.log('='.repeat(60));
}

testBuildingSqFt();