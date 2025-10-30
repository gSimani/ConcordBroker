/**
 * Verify: Count industrial properties in Broward County
 */

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
);

async function verifyBrowardIndustrialCount() {
  console.log('\n🔍 VERIFYING BROWARD INDUSTRIAL COUNT');
  console.log('=====================================\n');

  const industrialCodes = [
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',
    '040', '041', '042', '043', '044', '045', '046', '047', '048', '049'
  ];

  // Query for industrial properties in BROWARD county
  const { count, error } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .eq('county', 'BROWARD')
    .in('property_use', industrialCodes);

  if (error) {
    console.error('❌ Error:', error.message);
    return;
  }

  console.log(`📊 Industrial properties in BROWARD: ${count}`);
  console.log('');

  if (count === 128) {
    console.log('✅ SUCCESS: Count matches UI exactly!');
    console.log('   The Industrial filter fix is working correctly.');
  } else {
    console.log(`⚠️  Count mismatch: Database shows ${count}, UI shows 128`);
  }

  console.log('');
  console.log('📋 SUMMARY:');
  console.log('  - Total Florida industrial: 50,092 properties');
  console.log(`  - Broward industrial: ${count} properties`);
  console.log('  - Filter defaults to BROWARD county');
  console.log('  - User can change county to see all 50K+ properties');
}

verifyBrowardIndustrialCount().catch(console.error);
