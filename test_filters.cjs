#!/usr/bin/env node

/**
 * Comprehensive Property Filter Testing Script
 * Tests all property filter buttons with updated mappings
 */

const https = require('https');
const http = require('http');

// Property use code mappings from the updated propertyCategories.ts
const FILTER_MAPPINGS = {
  'Residential': [1, 2, 9],      // Single Family, Mobile Homes, Misc Residential
  'Commercial': [11, 19, 28],    // Stores, Professional Services, Parking Lots
  'Industrial': [48, 52, 60],    // Warehousing, Other Industrial, Light Manufacturing
  'Agricultural': [80, 87],      // Undefined Agricultural, Citrus
  'Vacant Land': [0],            // Vacant Residential
  'Multi-Family': [8],           // Multi-Family (10+ units)
  'Condo': [4],                  // Condominiums
  'Government': [93, 96],        // Municipal Service, Federal
  'Religious': [71],             // Churches, Temples
  'Conservation': [],            // No properties expected (empty test)
  'Vacant/Special': []           // Legacy category - test for backward compatibility
};

// Test configuration
const API_BASE = 'http://localhost:3001';
const API_KEY = 'concordbroker-mcp-key-claude';
const TEST_COUNTY = 'Miami-Dade';
const LIMIT = 10;

/**
 * Make HTTP request with promise wrapper
 */
function makeRequest(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = http.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: parsed
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: data
          });
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

/**
 * Test a single filter category
 */
async function testFilter(category, propertyUseValues) {
  console.log(`\n🔍 Testing ${category} filter...`);
  console.log(`   Property use values: [${propertyUseValues.join(', ')}]`);

  const startTime = Date.now();

  try {
    // Build query parameters for property_use filter
    let queryParams = `county=eq.${TEST_COUNTY}&limit=${LIMIT}`;

    if (propertyUseValues.length > 0) {
      // Use Supabase 'in' operator for multiple values
      const useValuesStr = `(${propertyUseValues.join(',')})`;
      queryParams += `&property_use=in.${useValuesStr}`;
    }

    const url = `${API_BASE}/api/supabase/florida_parcels?${queryParams}`;
    console.log(`   API URL: ${url}`);

    const response = await makeRequest(url);
    const responseTime = Date.now() - startTime;

    console.log(`   Status: ${response.status}`);
    console.log(`   Response time: ${responseTime}ms`);

    if (response.status === 200 && response.data && Array.isArray(response.data)) {
      const results = response.data;
      console.log(`   ✅ SUCCESS: Found ${results.length} properties`);

      // Validate property categories in results
      let correctCategories = 0;
      let incorrectCategories = 0;

      results.forEach((property, index) => {
        const propertyUse = property.property_use;
        const expectedCategory = propertyUseValues.includes(propertyUse);

        if (expectedCategory) {
          correctCategories++;
        } else {
          incorrectCategories++;
          if (index < 3) { // Only log first few mismatches
            console.log(`   ⚠️  Property ${property.parcel_id}: expected use in [${propertyUseValues.join(',')}], got ${propertyUse}`);
          }
        }
      });

      console.log(`   📊 Category validation: ${correctCategories} correct, ${incorrectCategories} incorrect`);

      // Sample property details
      if (results.length > 0) {
        const sample = results[0];
        console.log(`   📄 Sample property:`);
        console.log(`      Parcel: ${sample.parcel_id}`);
        console.log(`      Use: ${sample.property_use} (${sample.property_use_desc || 'No description'})`);
        console.log(`      Owner: ${sample.owner_name || 'Unknown'}`);
        console.log(`      Address: ${sample.phy_addr1 || 'No address'}`);
        console.log(`      Value: $${sample.just_value || 0}`);
      }

      return {
        category,
        success: true,
        count: results.length,
        responseTime,
        correctCategories,
        incorrectCategories,
        sample: results[0] || null
      };

    } else if (response.status === 200 && response.data && response.data.success === false) {
      console.log(`   ❌ API ERROR: ${response.data.error}`);
      return {
        category,
        success: false,
        error: response.data.error,
        responseTime
      };

    } else {
      console.log(`   ❌ HTTP ERROR: Status ${response.status}`);
      console.log(`   Response: ${JSON.stringify(response.data).substring(0, 200)}...`);
      return {
        category,
        success: false,
        error: `HTTP ${response.status}`,
        responseTime
      };
    }

  } catch (error) {
    const responseTime = Date.now() - startTime;
    console.log(`   ❌ REQUEST FAILED: ${error.message}`);
    return {
      category,
      success: false,
      error: error.message,
      responseTime
    };
  }
}

/**
 * Run comprehensive filter testing
 */
async function runFilterTests() {
  console.log('🚀 Starting Comprehensive Property Filter Testing');
  console.log(`📡 API Base: ${API_BASE}`);
  console.log(`🔑 API Key: ${API_KEY.substring(0, 20)}...`);
  console.log(`🏃 Test County: ${TEST_COUNTY}`);
  console.log(`📊 Results Limit: ${LIMIT}`);
  console.log('=' * 80);

  const results = [];

  // Test each filter category
  for (const [category, propertyUseValues] of Object.entries(FILTER_MAPPINGS)) {
    const result = await testFilter(category, propertyUseValues);
    results.push(result);

    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // Generate summary report
  console.log('\n' + '='.repeat(80));
  console.log('📊 COMPREHENSIVE TEST RESULTS SUMMARY');
  console.log('='.repeat(80));

  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);

  console.log(`✅ Successful filters: ${successful.length}/${results.length}`);
  console.log(`❌ Failed filters: ${failed.length}/${results.length}`);

  if (successful.length > 0) {
    console.log('\n🎯 WORKING FILTERS:');
    successful.forEach(result => {
      console.log(`   ✅ ${result.category}: ${result.count} properties (${result.responseTime}ms)`);
      if (result.correctCategories !== undefined) {
        const accuracy = result.correctCategories / (result.correctCategories + result.incorrectCategories) * 100;
        console.log(`      Category accuracy: ${accuracy.toFixed(1)}%`);
      }
    });
  }

  if (failed.length > 0) {
    console.log('\n❌ FAILED FILTERS:');
    failed.forEach(result => {
      console.log(`   ❌ ${result.category}: ${result.error} (${result.responseTime}ms)`);
    });
  }

  // Performance analysis
  const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;
  console.log(`\n⚡ Average response time: ${avgResponseTime.toFixed(0)}ms`);

  // Recommendations
  console.log('\n💡 RECOMMENDATIONS:');

  if (failed.length > 0) {
    console.log('   🔧 Fix failed filters by checking:');
    console.log('      - API endpoint availability');
    console.log('      - Authentication configuration');
    console.log('      - Database connectivity');
    console.log('      - Property use code mappings');
  }

  if (successful.length > 0) {
    const slowFilters = successful.filter(r => r.responseTime > 2000);
    if (slowFilters.length > 0) {
      console.log('   ⚡ Optimize slow filters:');
      slowFilters.forEach(r => {
        console.log(`      - ${r.category}: ${r.responseTime}ms`);
      });
    }
  }

  console.log('\n🎯 NEXT STEPS:');
  console.log('   1. Fix any failed filters');
  console.log('   2. Test frontend filter buttons in browser');
  console.log('   3. Verify filter results show correct property badges');
  console.log('   4. Test filter combinations');
  console.log('   5. Optimize performance if needed');

  return results;
}

// Run the tests
if (require.main === module) {
  runFilterTests()
    .then(results => {
      console.log('\n✅ Testing complete!');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Testing failed:', error);
      process.exit(1);
    });
}

module.exports = { runFilterTests, testFilter, FILTER_MAPPINGS };