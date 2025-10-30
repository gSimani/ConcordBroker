/**
 * Check what standardized_property_use values exist for Industrial DOR codes
 */

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
);

async function checkIndustrialStandardizedValues() {
  console.log('\n🔍 CHECKING INDUSTRIAL STANDARDIZED VALUES');
  console.log('==========================================\n');

  const industrialDORCodes = [
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',
    '040', '041', '042', '043', '044', '045', '046', '047', '048', '049'
  ];

  console.log('Industrial DOR codes:', industrialDORCodes.join(', '));
  console.log('');

  // Query for distinct standardized_property_use values for industrial DOR codes
  const { data, error } = await supabase
    .from('florida_parcels')
    .select('property_use, standardized_property_use')
    .in('property_use', industrialDORCodes)
    .limit(1000);

  if (error) {
    console.error('❌ Error:', error.message);
    return;
  }

  console.log(`📊 Sample of ${data.length} industrial properties:`);
  console.log('');

  // Count occurrences of each standardized_property_use value
  const standardizedCounts = {};
  data.forEach(row => {
    const val = row.standardized_property_use || 'NULL';
    standardizedCounts[val] = (standardizedCounts[val] || 0) + 1;
  });

  console.log('Standardized Property Use values found:');
  console.log('---------------------------------------');
  Object.entries(standardizedCounts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([value, count]) => {
      console.log(`  ${value}: ${count}`);
    });

  console.log('');
  console.log('Sample records:');
  console.log('----------------');
  data.slice(0, 10).forEach((row, i) => {
    console.log(`${i + 1}. property_use: "${row.property_use}" → standardized: "${row.standardized_property_use || 'NULL'}"`);
  });

  // Now check total count using .in() filter on standardized_property_use
  console.log('\n\n🔍 TESTING FILTER QUERY');
  console.log('=======================\n');

  console.log('Query 1: Filter by standardized_property_use = "Industrial"');
  const { count: count1, error: error1 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .eq('standardized_property_use', 'Industrial');

  if (error1) {
    console.error('❌ Error:', error1.message);
  } else {
    console.log(`✅ Result: ${count1} properties`);
  }

  console.log('\nQuery 2: Filter by property_use IN industrial DOR codes');
  const { count: count2, error: error2 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .in('property_use', industrialDORCodes);

  if (error2) {
    console.error('❌ Error:', error2.message);
  } else {
    console.log(`✅ Result: ${count2} properties`);
  }

  console.log('\n📋 CONCLUSION');
  console.log('=============');
  if (count1 === 0 && count2 > 0) {
    console.log('❌ PROBLEM: standardized_property_use does not contain "Industrial" for these DOR codes!');
    console.log('   The filter should use property_use (DOR codes), not standardized_property_use.');
  } else if (count1 === count2) {
    console.log('✅ Both filters work correctly!');
  } else {
    console.log(`⚠️  Mismatch: standardized (${count1}) vs DOR codes (${count2})`);
  }
}

checkIndustrialStandardizedValues().catch(console.error);
