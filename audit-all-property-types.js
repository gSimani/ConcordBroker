/**
 * COMPREHENSIVE PROPERTY TYPE AUDIT
 * Test ALL property type filter buttons to verify they match database counts
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

console.log('🔍 COMPREHENSIVE PROPERTY TYPE AUDIT - ALL CATEGORIES\n');
console.log('═'.repeat(100));

// Property type definitions from dorUseCodes.ts
const PROPERTY_TYPES = {
  'RESIDENTIAL': [
    '000', '001', '002', '004', '005', '006', '007', '008', '009',
    '0', '1', '2', '4', '5', '6', '7', '8', '9',
    'SFR', 'SINGLE_FAMILY', 'CONDO', 'CONDOMINIUM', 'MF_2-9', 'MF_10PLUS',
    'MOBILE', 'MOBILE_HOME', 'TIMESHARE', 'APARTMENT', 'DUPLEX', 'RES'
  ],
  'COMMERCIAL': [
    '003', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
    '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
    '030', '031', '032', '033', '034', '035', '036', '037', '038', '039',
    '3', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
    '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
    'COMM', 'Commercial' // Fixed case sensitivity
  ],
  'INDUSTRIAL': [
    '040', '041', '042', '043', '044', '045', '046', '047', '048', '049',
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',
    'IND', 'INDUSTRIAL', 'FACTORY', 'MANUFACTURING', 'WAREHOUSE', 'DISTRIBUTION'
  ],
  'AGRICULTURAL': [
    '050', '051', '052', '053', '054', '055', '056', '057', '058', '059',
    '060', '061', '062', '063', '064', '065', '066', '067', '068', '069',
    '50', '51', '52', '53', '54', '55', '56', '57', '58', '59',
    '60', '61', '62', '63', '64', '65', '66', '67', '68', '69',
    'AG', 'AGR', 'AGRICULTURAL', 'FARM', 'GROVE', 'RANCH', 'TIMBER'
  ]
};

async function auditPropertyType(typeName, dorCodes) {
  console.log(`\n${'='.repeat(100)}`);
  console.log(`📊 AUDITING: ${typeName}`);
  console.log('='.repeat(100));

  // Step 1: Test filter query (what PropertySearch component will do)
  console.log(`\n📊 STEP 1: Test Filter Query (${dorCodes.length} codes)`);
  console.log('-'.repeat(100));

  const { count: filterCount, error: filterError } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .in('property_use', dorCodes);

  if (filterError) {
    console.error(`❌ Filter Error:`, filterError);
    return null;
  }

  console.log(`✅ Filter query returned: ${(filterCount || 0).toLocaleString()} properties`);

  // Step 2: Discover actual codes in database
  console.log(`\n📊 STEP 2: Discover Actual Codes in Database`);
  console.log('-'.repeat(100));

  const foundCodes = [];
  const missingCodes = [];
  let actualTotal = 0;

  for (const code of dorCodes) {
    const { count: codeCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('property_use', code);

    if (codeCount > 0) {
      foundCodes.push({ code, count: codeCount });
      actualTotal += codeCount;
    } else {
      missingCodes.push(code);
    }
  }

  // Sort by count
  foundCodes.sort((a, b) => b.count - a.count);

  console.log(`\n✅ Found ${foundCodes.length} codes with data:`);
  foundCodes.slice(0, 10).forEach((item, i) => {
    const percentage = ((item.count / actualTotal) * 100).toFixed(2);
    console.log(`   ${(i + 1).toString().padStart(2)}. "${item.code.padEnd(20)}" → ${item.count.toLocaleString().padStart(12)} (${percentage.padStart(6)}%)`);
  });

  if (foundCodes.length > 10) {
    console.log(`   ... and ${foundCodes.length - 10} more codes`);
  }

  if (missingCodes.length > 0) {
    console.log(`\n⚠️  ${missingCodes.length} codes have no data:`);
    console.log(`   ${missingCodes.join(', ')}`);
  }

  // Step 3: Comparison
  console.log(`\n📊 STEP 3: Comparison`);
  console.log('-'.repeat(100));

  const difference = filterCount - actualTotal;
  const percentDiff = actualTotal > 0 ? ((difference / actualTotal) * 100).toFixed(2) : 0;

  console.log(`\n  Filter Count: ${(filterCount || 0).toLocaleString()}`);
  console.log(`  Actual Total: ${actualTotal.toLocaleString()}`);
  console.log(`  Difference:   ${difference.toLocaleString()} (${percentDiff}%)`);

  let status = '✅ MATCH';
  if (difference === 0) {
    status = '✅ PERFECT MATCH';
  } else if (Math.abs(difference) < 100) {
    status = '✅ VERY CLOSE';
  } else if (Math.abs(percentDiff) > 5) {
    status = '⚠️  SIGNIFICANT MISMATCH - NEEDS FIX';
  } else {
    status = '⚠️  MINOR VARIANCE';
  }

  console.log(`\n  Status: ${status}`);

  // Step 4: Sample properties
  console.log(`\n📊 STEP 4: Sample Properties`);
  console.log('-'.repeat(100));

  const { data: sampleProps } = await supabase
    .from('florida_parcels')
    .select('parcel_id, county, owner_name, property_use, just_value, phy_addr1')
    .in('property_use', dorCodes)
    .limit(3);

  if (sampleProps && sampleProps.length > 0) {
    sampleProps.forEach((prop, i) => {
      console.log(`\n   ${i + 1}. ${prop.phy_addr1 || 'No address'}, ${prop.county}`);
      console.log(`      Property Use: "${prop.property_use}"`);
      console.log(`      Owner: ${prop.owner_name || 'N/A'}`);
      console.log(`      Value: $${(prop.just_value || 0).toLocaleString()}`);
    });
  }

  return {
    typeName,
    filterCount,
    actualTotal,
    difference,
    percentDiff,
    status,
    foundCodes: foundCodes.length,
    missingCodes: missingCodes.length,
    topCodes: foundCodes.slice(0, 5)
  };
}

async function runComprehensiveAudit() {
  try {
    const results = [];

    // Audit all property types
    for (const [typeName, dorCodes] of Object.entries(PROPERTY_TYPES)) {
      const result = await auditPropertyType(typeName, dorCodes);
      if (result) {
        results.push(result);
      }

      // Pause between queries to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Final Summary
    console.log(`\n\n${'═'.repeat(100)}`);
    console.log('📊 FINAL SUMMARY - ALL PROPERTY TYPES');
    console.log('═'.repeat(100));

    console.log(`\n${'Property Type'.padEnd(20)} | ${'Filter Count'.padStart(15)} | ${'Actual Count'.padStart(15)} | ${'Difference'.padStart(12)} | ${'Status'.padEnd(30)}`);
    console.log('-'.repeat(100));

    let totalFilter = 0;
    let totalActual = 0;
    let totalIssues = 0;

    results.forEach(result => {
      totalFilter += result.filterCount;
      totalActual += result.actualTotal;

      if (result.status.includes('MISMATCH')) {
        totalIssues++;
      }

      console.log(
        `${result.typeName.padEnd(20)} | ` +
        `${result.filterCount.toLocaleString().padStart(15)} | ` +
        `${result.actualTotal.toLocaleString().padStart(15)} | ` +
        `${result.difference.toLocaleString().padStart(12)} | ` +
        `${result.status}`
      );
    });

    console.log('-'.repeat(100));
    console.log(
      `${'TOTAL'.padEnd(20)} | ` +
      `${totalFilter.toLocaleString().padStart(15)} | ` +
      `${totalActual.toLocaleString().padStart(15)} | ` +
      `${(totalFilter - totalActual).toLocaleString().padStart(12)} |`
    );

    console.log(`\n📊 Results:`);
    console.log(`   ✅ Property types tested: ${results.length}`);
    console.log(`   ${totalIssues === 0 ? '✅' : '⚠️ '} Issues found: ${totalIssues}`);

    if (totalIssues > 0) {
      console.log(`\n⚠️  ACTION REQUIRED: ${totalIssues} property type(s) need fixing`);
      results.forEach(result => {
        if (result.status.includes('MISMATCH')) {
          console.log(`\n   ${result.typeName}:`);
          console.log(`   - Expected: ${result.actualTotal.toLocaleString()}`);
          console.log(`   - Got: ${result.filterCount.toLocaleString()}`);
          console.log(`   - Difference: ${result.difference.toLocaleString()} (${result.percentDiff}%)`);
        }
      });
    } else {
      console.log(`\n🎉 ALL PROPERTY TYPE FILTERS ARE WORKING CORRECTLY!`);
    }

    console.log(`\n${'═'.repeat(100)}\n`);

  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

runComprehensiveAudit()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
