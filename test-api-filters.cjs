// Test if the API properly filters by min_value and max_value

async function testAPIFilters() {
  console.log('🔍 Testing API Min/Max Value Filters\n');

  // Test 1: Query without filters
  console.log('📍 Test 1: Query ALL properties (no filters)');
  const url1 = 'http://localhost:8000/api/properties/search?limit=5&offset=0';
  console.log('   URL:', url1);

  try {
    const response1 = await fetch(url1);
    const data1 = await response1.json();
    console.log('   Results:', data1.data?.length || 0, 'properties');
    console.log('   Total:', data1.pagination?.total || 0);

    if (data1.data && data1.data.length > 0) {
      console.log('\n   Sample values:');
      data1.data.slice(0, 3).forEach((prop, i) => {
        console.log(`   ${i+1}. ${prop.phy_addr1} - $${(prop.just_value || prop.jv || 0).toLocaleString()}`);
      });
    }
  } catch (e) {
    console.error('   ❌ Error:', e.message);
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // Test 2: Query with MIN VALUE = 500,000
  console.log('📍 Test 2: Query with MIN VALUE = $500,000');
  const url2 = 'http://localhost:8000/api/properties/search?min_value=500000&limit=5&offset=0';
  console.log('   URL:', url2);

  try {
    const response2 = await fetch(url2);
    const data2 = await response2.json();
    console.log('   Results:', data2.data?.length || 0, 'properties');
    console.log('   Total:', data2.pagination?.total || 0);

    if (data2.data && data2.data.length > 0) {
      console.log('\n   Sample values:');
      data2.data.slice(0, 3).forEach((prop, i) => {
        const value = prop.just_value || prop.jv || 0;
        const inRange = value >= 500000;
        console.log(`   ${i+1}. ${prop.phy_addr1} - $${value.toLocaleString()} ${inRange ? '✅' : '❌'}`);
      });
    }
  } catch (e) {
    console.error('   ❌ Error:', e.message);
  }

  console.log('\n' + '='.repeat(60) + '\n');

  // Test 3: Query with MIN VALUE = 500,000 and MAX VALUE = 1,000,000
  console.log('📍 Test 3: Query with MIN VALUE = $500,000 and MAX VALUE = $1,000,000');
  const url3 = 'http://localhost:8000/api/properties/search?min_value=500000&max_value=1000000&limit=10&offset=0';
  console.log('   URL:', url3);

  try {
    const response3 = await fetch(url3);
    const data3 = await response3.json();
    console.log('   Results:', data3.data?.length || 0, 'properties');
    console.log('   Total:', data3.pagination?.total || 0);

    if (data3.data && data3.data.length > 0) {
      console.log('\n   Sample values:');
      data3.data.forEach((prop, i) => {
        const value = prop.just_value || prop.jv || 0;
        const inRange = value >= 500000 && value <= 1000000;
        console.log(`   ${i+1}. ${(prop.phy_addr1 || 'No Address').padEnd(30)} - $${value.toLocaleString().padStart(12)} ${inRange ? '✅' : '❌'}`);
      });

      // Check if all values are in range
      const allInRange = data3.data.every(prop => {
        const value = prop.just_value || prop.jv || 0;
        return value >= 500000 && value <= 1000000;
      });

      console.log('\n   ' + (allInRange ? '✅ ALL VALUES IN RANGE!' : '❌ SOME VALUES OUT OF RANGE'));
    }
  } catch (e) {
    console.error('   ❌ Error:', e.message);
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ API Filter Test Complete');
  console.log('='.repeat(60));
}

testAPIFilters();