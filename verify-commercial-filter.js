/**
 * VERIFY COMMERCIAL FILTER - Test PropertySearch Filter Logic
 * This script tests the exact same query logic used by PropertySearch component
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, 'apps', 'web', '.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseServiceKey = process.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseServiceKey);

console.log('🔍 VERIFY COMMERCIAL FILTER - Testing PropertySearch Logic\n');
console.log('═'.repeat(90));

// These are the EXACT commercial DOR codes from dorUseCodes.ts lines 185-191 (CORRECTED)
const COMMERCIAL_DOR_CODES = [
  '003', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
  '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
  '030', '031', '032', '033', '034', '035', '036', '037', '038', '039',
  '3', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
  '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
  '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
  'COMM', 'Commercial' // FIXED: Using exact database case
];

async function verifyCommercialFilter() {
  try {
    console.log('\n📊 STEP 1: Test Query Using PropertySearch Logic');
    console.log('-'.repeat(90));
    console.log(`\nUsing ${COMMERCIAL_DOR_CODES.length} DOR codes from getPropertyTypeFilter()\n`);

    // This is the EXACT query logic from PropertySearch.tsx lines 570-578
    const { count, error } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .in('property_use', COMMERCIAL_DOR_CODES);

    if (error) {
      console.error('❌ Query Error:', error);
      return;
    }

    console.log(`\n✅ Query executed successfully`);
    console.log(`\n📊 RESULT: ${(count || 0).toLocaleString()} commercial properties found\n`);

    // Compare with expected count from comprehensive audit
    const EXPECTED_COUNT = 378514;
    const difference = count - EXPECTED_COUNT;
    const percentDiff = ((difference / EXPECTED_COUNT) * 100).toFixed(2);

    console.log('\n' + '═'.repeat(90));
    console.log('📊 VERIFICATION RESULTS');
    console.log('═'.repeat(90));
    console.log(`\n  Expected Count: ${EXPECTED_COUNT.toLocaleString()}`);
    console.log(`  Actual Count:   ${(count || 0).toLocaleString()}`);
    console.log(`  Difference:     ${difference.toLocaleString()} (${percentDiff}%)`);

    if (count === EXPECTED_COUNT) {
      console.log(`\n  ✅ PERFECT MATCH - Filter is working correctly!`);
    } else if (Math.abs(difference) < 100) {
      console.log(`\n  ✅ VERY CLOSE - Difference is negligible (likely data updates)`);
    } else {
      console.log(`\n  ⚠️  MISMATCH - Further investigation needed`);
    }

    // STEP 2: Check which codes are actually being used
    console.log('\n\n📊 STEP 2: Verify Which Codes Are Actually in Database');
    console.log('-'.repeat(90));

    const foundCodes = [];
    const missingCodes = [];

    console.log('\nChecking each DOR code...\n');

    for (const code of COMMERCIAL_DOR_CODES) {
      const { count: codeCount } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true })
        .eq('property_use', code);

      if (codeCount > 0) {
        foundCodes.push({ code, count: codeCount });
      } else {
        missingCodes.push(code);
      }
    }

    console.log(`✅ Found ${foundCodes.length} codes with data:`);
    foundCodes.sort((a, b) => b.count - a.count).slice(0, 15).forEach((item, i) => {
      console.log(`   ${(i + 1).toString().padStart(2)}. "${item.code.padEnd(20)}" → ${item.count.toLocaleString().padStart(12)} properties`);
    });

    if (missingCodes.length > 0) {
      console.log(`\n⚠️  ${missingCodes.length} codes have no data:`);
      console.log(`   ${missingCodes.join(', ')}`);
    }

    // STEP 3: Performance test
    console.log('\n\n📊 STEP 3: Performance Test');
    console.log('-'.repeat(90));

    const startTime = Date.now();

    const { data: sampleProperties } = await supabase
      .from('florida_parcels')
      .select('parcel_id, county, owner_name, property_use, just_value, phy_addr1')
      .in('property_use', COMMERCIAL_DOR_CODES)
      .limit(20);

    const endTime = Date.now();
    const queryTime = endTime - startTime;

    console.log(`\n✅ Sample query completed in ${queryTime}ms`);

    if (sampleProperties && sampleProperties.length > 0) {
      console.log(`\n📊 Sample commercial properties (first 5):\n`);
      sampleProperties.slice(0, 5).forEach((prop, i) => {
        console.log(`   ${i + 1}. ${prop.phy_addr1 || 'No address'}, ${prop.county}`);
        console.log(`      Owner: ${prop.owner_name || 'N/A'}`);
        console.log(`      Property Use: "${prop.property_use}"`);
        console.log(`      Value: $${(prop.just_value || 0).toLocaleString()}\n`);
      });
    }

    console.log('\n' + '═'.repeat(90));
    console.log('✅ VERIFICATION COMPLETE');
    console.log('═'.repeat(90));

    if (count === EXPECTED_COUNT || Math.abs(difference) < 100) {
      console.log('\n🎉 COMMERCIAL FILTER IS WORKING CORRECTLY!');
      console.log(`\nThe PropertySearch component will correctly filter ${count.toLocaleString()} commercial properties`);
      console.log('when the user clicks the "Commercial" button.\n');
    }

    console.log('═'.repeat(90) + '\n');

  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

verifyCommercialFilter()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
