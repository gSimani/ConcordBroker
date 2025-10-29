/**
 * Performance Baseline Test Script
 *
 * This script establishes current performance metrics before optimization.
 * Run this before making any changes, then run again after each phase.
 *
 * Usage: node scripts/test-performance-baseline.js
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

// Initialize Supabase client
const supabase = createClient(
  process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY
);

/**
 * Measure query execution time
 */
async function measureQuery(name, queryFn) {
  const start = Date.now();
  try {
    const result = await queryFn();
    const duration = Date.now() - start;

    const resultCount = Array.isArray(result?.data) ? result.data.length : (result?.data ? 1 : 0);

    console.log(`✅ ${name}`);
    console.log(`   Duration: ${duration}ms`);
    console.log(`   Results: ${resultCount} records`);

    return {
      name,
      duration,
      resultCount,
      success: true,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.log(`❌ ${name}`);
    console.log(`   Error: ${error.message}`);

    return {
      name,
      duration: null,
      resultCount: 0,
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * Main baseline test suite
 */
async function runBaseline() {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('🔍 PERFORMANCE BASELINE TEST SUITE');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`Started: ${new Date().toISOString()}\n`);

  const results = {
    metadata: {
      testDate: new Date().toISOString(),
      supabaseUrl: process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL,
      phase: 'baseline'
    },
    tests: {}
  };

  // =========================================
  // TEST 1: Autocomplete (Current - 4 parallel queries)
  // =========================================
  console.log('\n📝 TEST 1: Autocomplete (4 Parallel Queries)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.autocomplete = await measureQuery(
    'Autocomplete (4 parallel queries)',
    async () => {
      return await Promise.all([
        supabase
          .from('florida_parcels')
          .select('parcel_id,phy_addr1,phy_city,owner_name,just_value')
          .ilike('phy_addr1', 'main%')
          .limit(5),
        supabase
          .from('florida_parcels')
          .select('parcel_id,phy_addr1,phy_city,owner_name,just_value')
          .ilike('owner_name', 'main%')
          .limit(5),
        supabase
          .from('florida_parcels')
          .select('parcel_id,phy_addr1,phy_city,owner_name,just_value')
          .ilike('phy_city', 'main%')
          .limit(5),
        supabase
          .from('florida_parcels')
          .select('parcel_id,phy_addr1,phy_city,owner_name,just_value')
          .eq('county', 'BROWARD')
          .limit(5)
      ]);
    }
  );

  // =========================================
  // TEST 2: Property Search (County Filter)
  // =========================================
  console.log('\n📝 TEST 2: Property Search (County Filter)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.propertySearch = await measureQuery(
    'Property search with county filter',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('*')
        .eq('county', 'BROWARD')
        .eq('year', 2025)
        .limit(100);
    }
  );

  // =========================================
  // TEST 3: Property Detail (Single Parcel)
  // =========================================
  console.log('\n📝 TEST 3: Property Detail (Single Parcel)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.propertyDetail = await measureQuery(
    'Property detail lookup',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('*')
        .eq('county', 'BROWARD')
        .eq('year', 2025)
        .limit(1)
        .single();
    }
  );

  // =========================================
  // TEST 4: Sales History
  // =========================================
  console.log('\n📝 TEST 4: Sales History');
  console.log('─────────────────────────────────────────────────────────');

  // First get a parcel_id that exists
  const { data: sampleParcel } = await supabase
    .from('florida_parcels')
    .select('parcel_id')
    .eq('county', 'BROWARD')
    .limit(1)
    .single();

  if (sampleParcel) {
    results.tests.salesHistory = await measureQuery(
      'Sales history for parcel',
      async () => {
        return await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', sampleParcel.parcel_id);
      }
    );
  } else {
    console.log('⚠️  No sample parcel found, skipping sales history test');
    results.tests.salesHistory = { name: 'Sales History', duration: null, success: false, error: 'No sample data' };
  }

  // =========================================
  // TEST 5: Owner Search (ILIKE - Expensive)
  // =========================================
  console.log('\n📝 TEST 5: Owner Search (ILIKE)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.ownerSearch = await measureQuery(
    'Owner name search with ILIKE',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('parcel_id,phy_addr1,owner_name,just_value')
        .ilike('owner_name', '%LLC%')
        .eq('county', 'BROWARD')
        .limit(50);
    }
  );

  // =========================================
  // TEST 6: Address Search (ILIKE - Expensive)
  // =========================================
  console.log('\n📝 TEST 6: Address Search (ILIKE)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.addressSearch = await measureQuery(
    'Address search with ILIKE',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('parcel_id,phy_addr1,phy_city,just_value')
        .ilike('phy_addr1', '%MAIN%')
        .eq('county', 'BROWARD')
        .limit(50);
    }
  );

  // =========================================
  // TEST 7: Value Range Query
  // =========================================
  console.log('\n📝 TEST 7: Value Range Query');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.valueRangeQuery = await measureQuery(
    'Property value range query',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('parcel_id,phy_addr1,just_value')
        .eq('county', 'BROWARD')
        .gte('just_value', 500000)
        .lte('just_value', 1000000)
        .limit(100);
    }
  );

  // =========================================
  // TEST 8: Year Built Range
  // =========================================
  console.log('\n📝 TEST 8: Year Built Range Query');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.yearBuiltRange = await measureQuery(
    'Year built range query',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('parcel_id,phy_addr1,year_built')
        .eq('county', 'BROWARD')
        .gte('year_built', 2000)
        .lte('year_built', 2010)
        .limit(100);
    }
  );

  // =========================================
  // TEST 9: Multi-Filter Query (Complex)
  // =========================================
  console.log('\n📝 TEST 9: Multi-Filter Query (Complex)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.multiFilter = await measureQuery(
    'Multi-filter complex query',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('parcel_id,phy_addr1,phy_city,owner_name,just_value,year_built')
        .eq('county', 'BROWARD')
        .eq('year', 2025)
        .gte('just_value', 300000)
        .lte('just_value', 800000)
        .gte('year_built', 1990)
        .limit(100);
    }
  );

  // =========================================
  // TEST 10: Count Query (Aggregation)
  // =========================================
  console.log('\n📝 TEST 10: Count Query (Aggregation)');
  console.log('─────────────────────────────────────────────────────────');

  results.tests.countQuery = await measureQuery(
    'Count query with filter',
    async () => {
      return await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true })
        .eq('county', 'BROWARD')
        .eq('year', 2025);
    }
  );

  // =========================================
  // SUMMARY
  // =========================================
  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('📊 BASELINE RESULTS SUMMARY');
  console.log('═══════════════════════════════════════════════════════════\n');

  const successfulTests = Object.values(results.tests).filter(t => t.success);
  const failedTests = Object.values(results.tests).filter(t => !t.success);

  console.log(`✅ Successful Tests: ${successfulTests.length}`);
  console.log(`❌ Failed Tests: ${failedTests.length}`);
  console.log(`📈 Total Tests: ${Object.keys(results.tests).length}\n`);

  if (successfulTests.length > 0) {
    console.log('Performance Summary (Successful Tests):');
    console.log('─────────────────────────────────────────────────────────');

    successfulTests.forEach(test => {
      const emoji = test.duration < 500 ? '🟢' : test.duration < 2000 ? '🟡' : '🔴';
      console.log(`${emoji} ${test.name}: ${test.duration}ms (${test.resultCount} records)`);
    });
  }

  if (failedTests.length > 0) {
    console.log('\nFailed Tests:');
    console.log('─────────────────────────────────────────────────────────');
    failedTests.forEach(test => {
      console.log(`❌ ${test.name}: ${test.error}`);
    });
  }

  // Calculate statistics
  const durations = successfulTests.map(t => t.duration);
  const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
  const maxDuration = Math.max(...durations);
  const minDuration = Math.min(...durations);

  console.log('\n═══════════════════════════════════════════════════════════');
  console.log('📈 STATISTICS');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`Average Duration: ${Math.round(avgDuration)}ms`);
  console.log(`Fastest Query: ${minDuration}ms`);
  console.log(`Slowest Query: ${maxDuration}ms`);
  console.log(`Completed: ${new Date().toISOString()}`);
  console.log('═══════════════════════════════════════════════════════════\n');

  // Save results to file
  const fs = require('fs');
  const outputFile = 'BASELINE_PERFORMANCE.json';
  fs.writeFileSync(outputFile, JSON.stringify(results, null, 2));
  console.log(`💾 Results saved to: ${outputFile}\n`);

  return results;
}

// Run the baseline tests
if (require.main === module) {
  runBaseline()
    .then(() => {
      console.log('✅ Baseline testing complete!');
      process.exit(0);
    })
    .catch(error => {
      console.error('❌ Baseline testing failed:', error);
      process.exit(1);
    });
}

module.exports = { runBaseline, measureQuery };
