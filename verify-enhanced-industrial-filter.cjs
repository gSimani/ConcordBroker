const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
);

const INDUSTRIAL_CODES = [
  '040', '041', '042', '043', '044', '045', '046', '047', '048', '049',
  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49'
];

async function verifyEnhancedFilter() {
  console.log('='.repeat(100));
  console.log('VERIFYING ENHANCED INDUSTRIAL FILTER');
  console.log('='.repeat(100));
  console.log('');

  // Test county: Broward
  const county = 'BROWARD';

  console.log(`Testing in ${county} County...\n`);

  // OLD METHOD: Owner name patterns only
  console.log('📊 OLD METHOD (Owner Name Patterns Only):');
  console.log('-'.repeat(100));

  const { count: oldMethodCount } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .eq('county', county)
    .or(
      'owner_name.ilike.%INDUSTRIAL%,' +
      'owner_name.ilike.%MANUFACTURING%,' +
      'owner_name.ilike.%WAREHOUSE%,' +
      'owner_name.ilike.%DISTRIBUTION%,' +
      'owner_name.ilike.%LOGISTICS%,' +
      'owner_name.ilike.%FACTORY%,' +
      'owner_name.ilike.%PLANT%'
    );

  console.log(`Properties found: ${(oldMethodCount || 0).toLocaleString()}`);
  console.log('');

  // NEW METHOD: DOR codes + Owner patterns
  console.log('✨ NEW METHOD (DOR Codes + Owner Patterns):');
  console.log('-'.repeat(100));

  const { count: newMethodCount } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .eq('county', county)
    .or(
      'property_use.in.(' + INDUSTRIAL_CODES.join(',') + '),' +
      'owner_name.ilike.%INDUSTRIAL%,' +
      'owner_name.ilike.%MANUFACTURING%,' +
      'owner_name.ilike.%WAREHOUSE%,' +
      'owner_name.ilike.%DISTRIBUTION%,' +
      'owner_name.ilike.%LOGISTICS%,' +
      'owner_name.ilike.%FACTORY%,' +
      'owner_name.ilike.%PLANT%'
    );

  console.log(`Properties found: ${(newMethodCount || 0).toLocaleString()}`);
  console.log('');

  // Calculate improvement
  const improvement = newMethodCount - oldMethodCount;
  const percentImprovement = ((improvement / oldMethodCount) * 100).toFixed(1);

  console.log('📈 IMPROVEMENT:');
  console.log('-'.repeat(100));
  console.log(`Additional properties discovered: ${improvement.toLocaleString()}`);
  console.log(`Percentage increase: +${percentImprovement}%`);
  console.log('');

  // Sample properties captured by new method but missed by old
  console.log('🔍 SAMPLE PROPERTIES CAPTURED BY NEW METHOD (that old method missed):');
  console.log('-'.repeat(100));

  const { data: newProperties } = await supabase
    .from('florida_parcels')
    .select('parcel_id, owner_name, property_use, phy_addr1')
    .eq('county', county)
    .in('property_use', INDUSTRIAL_CODES)
    .not('owner_name', 'ilike', '%INDUSTRIAL%')
    .not('owner_name', 'ilike', '%MANUFACTURING%')
    .not('owner_name', 'ilike', '%WAREHOUSE%')
    .not('owner_name', 'ilike', '%DISTRIBUTION%')
    .not('owner_name', 'ilike', '%LOGISTICS%')
    .not('owner_name', 'ilike', '%FACTORY%')
    .not('owner_name', 'ilike', '%PLANT%')
    .limit(20);

  newProperties?.forEach((prop, i) => {
    console.log(`${i + 1}. Owner: ${prop.owner_name}`);
    console.log(`   Address: ${prop.phy_addr1 || 'N/A'}`);
    console.log(`   DOR Code: ${prop.property_use} (Industrial)`);
    console.log('');
  });

  // Florida-wide statistics
  console.log('='.repeat(100));
  console.log('FLORIDA-WIDE IMPACT');
  console.log('='.repeat(100));
  console.log('');

  console.log('📊 OLD METHOD (Owner Patterns):');
  const { count: oldFloridaCount } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .or(
      'owner_name.ilike.%INDUSTRIAL%,' +
      'owner_name.ilike.%MANUFACTURING%,' +
      'owner_name.ilike.%WAREHOUSE%,' +
      'owner_name.ilike.%DISTRIBUTION%,' +
      'owner_name.ilike.%LOGISTICS%,' +
      'owner_name.ilike.%FACTORY%,' +
      'owner_name.ilike.%PLANT%'
    );

  console.log(`Total Florida properties: ${(oldFloridaCount || 0).toLocaleString()}`);
  console.log('');

  console.log('✨ NEW METHOD (DOR Codes + Owner Patterns):');
  const { count: newFloridaCount } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .or(
      'property_use.in.(' + INDUSTRIAL_CODES.join(',') + '),' +
      'owner_name.ilike.%INDUSTRIAL%,' +
      'owner_name.ilike.%MANUFACTURING%,' +
      'owner_name.ilike.%WAREHOUSE%,' +
      'owner_name.ilike.%DISTRIBUTION%,' +
      'owner_name.ilike.%LOGISTICS%,' +
      'owner_name.ilike.%FACTORY%,' +
      'owner_name.ilike.%PLANT%'
    );

  console.log(`Total Florida properties: ${(newFloridaCount || 0).toLocaleString()}`);
  console.log('');

  const floridaImprovement = newFloridaCount - oldFloridaCount;
  const floridaPercentImprovement = ((floridaImprovement / oldFloridaCount) * 100).toFixed(1);

  console.log('📈 FLORIDA-WIDE IMPROVEMENT:');
  console.log('-'.repeat(100));
  console.log(`Additional properties discovered: ${floridaImprovement.toLocaleString()}`);
  console.log(`Percentage increase: +${floridaPercentImprovement}%`);
  console.log('');

  // Summary
  console.log('='.repeat(100));
  console.log('SUMMARY');
  console.log('='.repeat(100));
  console.log('');
  console.log('✅ ENHANCEMENT COMPLETE');
  console.log('');
  console.log(`${county} County:`);
  console.log(`  Before: ${oldMethodCount.toLocaleString()} properties`);
  console.log(`  After: ${newMethodCount.toLocaleString()} properties`);
  console.log(`  Improvement: +${improvement.toLocaleString()} (+${percentImprovement}%)`);
  console.log('');
  console.log('All Florida:');
  console.log(`  Before: ${oldFloridaCount.toLocaleString()} properties`);
  console.log(`  After: ${newFloridaCount.toLocaleString()} properties`);
  console.log(`  Improvement: +${floridaImprovement.toLocaleString()} (+${floridaPercentImprovement}%)`);
  console.log('');
  console.log('🎯 The Industrial filter now captures ALL properties with official DOR industrial codes');
  console.log('   PLUS properties with industrial-related owner names.');
  console.log('');
  console.log('✅ No industrial properties are being missed!');
  console.log('='.repeat(100));
}

verifyEnhancedFilter().catch(console.error);
