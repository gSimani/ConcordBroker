/**
 * Comprehensive Audit - All Counties property_use Values
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY
);

async function comprehensiveAudit() {
  console.log('='.repeat(80));
  console.log('COMPREHENSIVE DATABASE AUDIT - ALL COUNTIES');
  console.log('='.repeat(80));
  console.log();

  try {
    // Query 1: Get sample with addresses
    console.log('📊 QUERY 1: Sample properties WITH addresses (Broward)');
    console.log('-'.repeat(80));

    const { data: withAddresses, error: addrError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, county, property_use, phy_addr1, owner_name, just_value')
      .eq('county', 'BROWARD')
      .not('phy_addr1', 'is', null)
      .neq('phy_addr1', '')
      .neq('phy_addr1', '-')
      .limit(20);

    if (addrError) {
      console.error('❌ Error:', addrError.message);
    } else {
      console.log(`Found ${withAddresses.length} properties with addresses:`);
      withAddresses.forEach((record, idx) => {
        console.log(`  ${idx + 1}. USE: "${record.property_use}" | Addr: ${record.phy_addr1?.substring(0, 35)} | Value: $${record.just_value?.toLocaleString()}`);
      });
    }
    console.log();

    // Query 2: Get distinct property_use values from LARGER sample
    console.log('📊 QUERY 2: Distinct property_use values (10,000 records)');
    console.log('-'.repeat(80));

    const { data: largeData, error: largeError } = await supabase
      .from('florida_parcels')
      .select('property_use, county')
      .not('property_use', 'is', null)
      .limit(10000);

    if (largeError) {
      console.error('❌ Error:', largeError.message);
    } else {
      const uniqueUses = [...new Set(largeData.map(r => r.property_use))].sort();
      console.log(`Found ${uniqueUses.length} distinct property_use values from 10K records:`);
      console.log('First 100 values:');
      uniqueUses.slice(0, 100).forEach((use, idx) => {
        console.log(`  ${idx + 1}. "${use}"`);
      });
    }
    console.log();

    // Query 3: Check specific commercial codes
    console.log('📊 QUERY 3: Search for specific USE codes across all data');
    console.log('-'.repeat(80));

    const testCodes = ['11', '011', '17', '017', '41', '041', 'COM', 'COMMERCIAL', 'STORE', 'OFFICE'];

    for (const code of testCodes) {
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, county, property_use, phy_addr1')
        .eq('property_use', code)
        .limit(5);

      if (!error && data && data.length > 0) {
        console.log(`  ✅ Found ${data.length} properties with property_use = "${code}"`);
        data.forEach(p => console.log(`     - ${p.phy_addr1?.substring(0, 40) || 'No address'} (${p.county})`));
      } else {
        console.log(`  ❌ No properties found with property_use = "${code}"`);
      }
    }
    console.log();

    // Query 4: Sample from different counties
    console.log('📊 QUERY 4: Sample from multiple counties');
    console.log('-'.repeat(80));

    const counties = ['MIAMI-DADE', 'PALM_BEACH', 'HILLSBOROUGH', 'ORANGE'];

    for (const county of counties) {
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('property_use')
        .eq('county', county)
        .not('property_use', 'is', null)
        .limit(100);

      if (!error && data) {
        const unique = [...new Set(data.map(r => r.property_use))];
        console.log(`  ${county}: ${unique.length} distinct values - ${unique.slice(0, 10).join(', ')}`);
      }
    }
    console.log();

    // Query 5: Count total properties by USE value
    console.log('📊 QUERY 5: Aggregate counts (from 10K sample)');
    console.log('-'.repeat(80));

    if (!largeError && largeData) {
      const counts = {};
      largeData.forEach(r => {
        counts[r.property_use] = (counts[r.property_use] || 0) + 1;
      });

      const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
      console.log('Top 30 property_use values:');
      sorted.slice(0, 30).forEach(([use, count], idx) => {
        const pct = ((count / largeData.length) * 100).toFixed(1);
        console.log(`  ${idx + 1}. "${use}": ${count} (${pct}%)`);
      });
    }
    console.log();

    console.log('='.repeat(80));
    console.log('COMPREHENSIVE AUDIT COMPLETE');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

comprehensiveAudit();
