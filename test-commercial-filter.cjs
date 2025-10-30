/**
 * Test Commercial Filter - Verify filtering works with all three formats
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.VITE_SUPABASE_URL || process.env.SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY || process.env.SUPABASE_ANON_KEY
);

// Import the filter codes (simulating the frontend logic)
const COMMERCIAL_CODES = [
  // Zero-padded
  '003', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
  '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
  '030', '031', '032', '033', '034', '035', '036', '037', '038', '039',
  // Non-padded
  '3', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
  '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
  '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
  // TEXT codes
  'COMM', 'COMMERCIAL', 'STORE', 'RETAIL', 'OFFICE', 'RESTAURANT', 'REST',
  'HOTEL', 'MOTEL', 'BANK', 'PARKING', 'MALL', 'SHOPPING_CENTER'
];

async function testCommercialFilter() {
  console.log('='.repeat(80));
  console.log('COMMERCIAL FILTER TEST');
  console.log('='.repeat(80));
  console.log();

  try {
    // Test 1: Query with commercial filter (Broward County)
    console.log('📊 TEST 1: Filter commercial properties in BROWARD');
    console.log('-'.repeat(80));

    const { data: browardCommercial, error: browardError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, property_use, phy_addr1, owner_name, just_value')
      .eq('county', 'BROWARD')
      .in('property_use', COMMERCIAL_CODES)
      .limit(20);

    if (browardError) {
      console.error('❌ Error:', browardError.message);
    } else {
      console.log(`✅ Found ${browardCommercial.length} commercial properties in Broward:`);
      browardCommercial.forEach((prop, idx) => {
        console.log(`  ${idx + 1}. USE: "${prop.property_use}" | ${prop.phy_addr1?.substring(0, 40)} | Value: $${prop.just_value?.toLocaleString()}`);
      });
    }
    console.log();

    // Test 2: Count by format type
    console.log('📊 TEST 2: Count commercial properties by format type');
    console.log('-'.repeat(80));

    const textCodes = ['COMM', 'COMMERCIAL', 'STORE', 'RETAIL', 'OFFICE', 'RESTAURANT', 'REST', 'HOTEL', 'MOTEL', 'BANK', 'PARKING', 'MALL', 'SHOPPING_CENTER'];
    const zeroPadded = ['011', '012', '013', '014', '015', '016', '017', '018', '019', '021', '022', '023'];
    const nonPadded = ['11', '12', '13', '14', '15', '16', '17', '18', '19', '21', '22', '23'];

    const { data: textData } = await supabase
      .from('florida_parcels')
      .select('parcel_id')
      .eq('county', 'BROWARD')
      .in('property_use', textCodes)
      .limit(1000);

    const { data: paddedData } = await supabase
      .from('florida_parcels')
      .select('parcel_id')
      .eq('county', 'BROWARD')
      .in('property_use', zeroPadded)
      .limit(1000);

    const { data: nonPaddedData } = await supabase
      .from('florida_parcels')
      .select('parcel_id')
      .eq('county', 'BROWARD')
      .in('property_use', nonPadded)
      .limit(1000);

    console.log(`  TEXT codes (COMM, RETAIL, etc.): ${textData?.length || 0} properties`);
    console.log(`  Zero-padded (011, 017, etc.): ${paddedData?.length || 0} properties`);
    console.log(`  Non-padded (11, 17, etc.): ${nonPaddedData?.length || 0} properties`);
    console.log(`  TOTAL Commercial (all formats): ${(textData?.length || 0) + (paddedData?.length || 0) + (nonPaddedData?.length || 0)}`);
    console.log();

    // Test 3: Verify filter would work (simulate frontend query)
    console.log('📊 TEST 3: Simulate frontend commercial filter query');
    console.log('-'.repeat(80));

    const { data: filterTest, error: filterError, count } = await supabase
      .from('florida_parcels')
      .select('parcel_id, property_use, phy_addr1', { count: 'exact' })
      .eq('county', 'BROWARD')
      .in('property_use', COMMERCIAL_CODES)
      .range(0, 9)
      .limit(10);

    if (filterError) {
      console.error('❌ Filter query error:', filterError.message);
    } else {
      console.log(`✅ Filter query successful`);
      console.log(`   Total commercial properties: ${count}`);
      console.log(`   First 10 results:`);
      filterTest?.forEach((prop, idx) => {
        console.log(`     ${idx + 1}. USE: "${prop.property_use}" | ${prop.phy_addr1?.substring(0, 40)}`);
      });
    }
    console.log();

    // Test 4: Check if any properties would be excluded
    console.log('📊 TEST 4: Check for commercial properties we might miss');
    console.log('-'.repeat(80));

    // Get all distinct commercial-looking property_use values
    const { data: allData } = await supabase
      .from('florida_parcels')
      .select('property_use')
      .eq('county', 'BROWARD')
      .not('property_use', 'is', null)
      .limit(5000);

    if (allData) {
      const uniqueUses = [...new Set(allData.map(r => r.property_use))];
      const commercialLooking = uniqueUses.filter(use => {
        const u = String(use).toUpperCase();
        return u.includes('COMM') || u.includes('STORE') || u.includes('OFFICE') ||
               u.includes('RETAIL') || u.includes('HOTEL') || u.includes('BANK') ||
               (u >= '10' && u <= '39' && /^\d+$/.test(u));
      });

      const notIncluded = commercialLooking.filter(use => !COMMERCIAL_CODES.includes(String(use).toUpperCase()));

      if (notIncluded.length > 0) {
        console.log(`⚠️  Found ${notIncluded.length} commercial-looking codes NOT in filter:`);
        notIncluded.forEach(code => console.log(`     "${code}"`));
      } else {
        console.log(`✅ All commercial-looking codes are included in filter`);
      }
    }
    console.log();

    console.log('='.repeat(80));
    console.log('TEST COMPLETE');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

testCommercialFilter();
