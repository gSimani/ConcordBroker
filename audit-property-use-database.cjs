/**
 * Audit Supabase Database - Property USE Values
 * Check what actual values exist in property_use column
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY
);

async function auditPropertyUseValues() {
  console.log('='.repeat(80));
  console.log('SUPABASE DATABASE AUDIT - property_use COLUMN');
  console.log('='.repeat(80));
  console.log();

  try {
    // Query 1: Get sample of property_use values from Broward County
    console.log('📊 QUERY 1: Sample property_use values from BROWARD county');
    console.log('-'.repeat(80));

    const { data: sampleData, error: sampleError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, property_use, phy_addr1, owner_name')
      .eq('county', 'BROWARD')
      .not('property_use', 'is', null)
      .limit(20);

    if (sampleError) {
      console.error('❌ Error:', sampleError.message);
    } else {
      console.log(`Found ${sampleData.length} sample records:`);
      sampleData.forEach((record, idx) => {
        console.log(`  ${idx + 1}. property_use: "${record.property_use}" | Type: ${typeof record.property_use} | Address: ${record.phy_addr1?.substring(0, 40)}`);
      });
    }
    console.log();

    // Query 2: Get DISTINCT property_use values (aggregated)
    console.log('📊 QUERY 2: Distinct property_use values (first 50)');
    console.log('-'.repeat(80));

    const { data: distinctData, error: distinctError } = await supabase
      .from('florida_parcels')
      .select('property_use')
      .eq('county', 'BROWARD')
      .not('property_use', 'is', null)
      .limit(1000); // Get 1000 records to find distinct values

    if (distinctError) {
      console.error('❌ Error:', distinctError.message);
    } else {
      // Get unique values
      const uniqueUses = [...new Set(distinctData.map(r => r.property_use))];
      console.log(`Found ${uniqueUses.length} distinct property_use values:`);
      uniqueUses.slice(0, 50).forEach((use, idx) => {
        console.log(`  ${idx + 1}. "${use}" (Type: ${typeof use})`);
      });
      if (uniqueUses.length > 50) {
        console.log(`  ... and ${uniqueUses.length - 50} more`);
      }
    }
    console.log();

    // Query 3: Check if values are numeric or text
    console.log('📊 QUERY 3: Analyze property_use data types');
    console.log('-'.repeat(80));

    if (!distinctError && distinctData) {
      const numericPattern = /^\d+$/;
      const textPattern = /^[A-Z_]+$/;

      let numericCount = 0;
      let textCount = 0;
      let mixedCount = 0;
      const samples = {
        numeric: [],
        text: [],
        mixed: []
      };

      distinctData.forEach(record => {
        const use = String(record.property_use);
        if (numericPattern.test(use)) {
          numericCount++;
          if (samples.numeric.length < 5) samples.numeric.push(use);
        } else if (textPattern.test(use)) {
          textCount++;
          if (samples.text.length < 5) samples.text.push(use);
        } else {
          mixedCount++;
          if (samples.mixed.length < 5) samples.mixed.push(use);
        }
      });

      console.log(`  Numeric codes (e.g., "1", "082"): ${numericCount} records`);
      console.log(`    Samples: ${samples.numeric.join(', ')}`);
      console.log(`  Text codes (e.g., "SFR", "COM"): ${textCount} records`);
      console.log(`    Samples: ${samples.text.join(', ')}`);
      console.log(`  Mixed/Other: ${mixedCount} records`);
      console.log(`    Samples: ${samples.mixed.join(', ')}`);
    }
    console.log();

    // Query 4: Check filtering - get Commercial properties
    console.log('📊 QUERY 4: Test filtering - Commercial properties (DOR codes 011-039)');
    console.log('-'.repeat(80));

    const commercialCodes = ['011', '012', '013', '014', '015', '016', '017', '018', '019',
                             '021', '022', '023', '024', '025', '026', '027', '028', '029',
                             '031', '032', '033', '034', '035', '036', '037', '038', '039'];

    const { data: commercialData, error: commercialError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, property_use, phy_addr1, owner_name')
      .eq('county', 'BROWARD')
      .in('property_use', commercialCodes)
      .limit(10);

    if (commercialError) {
      console.error('❌ Error:', commercialError.message);
    } else {
      console.log(`Found ${commercialData.length} commercial properties:`);
      commercialData.forEach((record, idx) => {
        console.log(`  ${idx + 1}. property_use: "${record.property_use}" | Address: ${record.phy_addr1?.substring(0, 40)}`);
      });
    }
    console.log();

    // Query 5: Try WITHOUT zero-padding (single digit codes)
    console.log('📊 QUERY 5: Test filtering - Single digit codes (1, 2, 3, 11, 17)');
    console.log('-'.repeat(80));

    const singleDigitCodes = ['1', '2', '3', '11', '17', '41', '50', '71', '82'];

    const { data: singleData, error: singleError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, property_use, phy_addr1, owner_name')
      .eq('county', 'BROWARD')
      .in('property_use', singleDigitCodes)
      .limit(10);

    if (singleError) {
      console.error('❌ Error:', singleError.message);
    } else {
      console.log(`Found ${singleData.length} properties with single-digit codes:`);
      singleData.forEach((record, idx) => {
        console.log(`  ${idx + 1}. property_use: "${record.property_use}" | Address: ${record.phy_addr1?.substring(0, 40)}`);
      });
    }
    console.log();

    // Query 6: Count by property_use value
    console.log('📊 QUERY 6: Count properties by property_use (top 20)');
    console.log('-'.repeat(80));

    if (!distinctError && distinctData) {
      const useCounts = {};
      distinctData.forEach(record => {
        const use = String(record.property_use);
        useCounts[use] = (useCounts[use] || 0) + 1;
      });

      const sorted = Object.entries(useCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 20);

      console.log('  Top 20 property_use values by frequency:');
      sorted.forEach(([use, count], idx) => {
        console.log(`    ${idx + 1}. "${use}": ${count} properties`);
      });
    }
    console.log();

    console.log('='.repeat(80));
    console.log('AUDIT COMPLETE');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

auditPropertyUseValues();
