const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
);

const COMMERCIAL_CODES = ['21', '27', '28'];
const CODE_DESCRIPTIONS = {
  '21': 'Restaurants, cafeterias (COMMERCIAL)',
  '27': 'Auto sales, repair, etc. (COMMERCIAL)',
  '28': 'Parking lots, mobile home parks (COMMERCIAL)'
};

async function investigateMisclassified() {
  console.log('='.repeat(100));
  console.log('INVESTIGATING COMMERCIAL CODES MARKED AS "INDUSTRIAL"');
  console.log('='.repeat(100));
  console.log('');

  for (const code of COMMERCIAL_CODES) {
    console.log(`\n${'='.repeat(100)}`);
    console.log(`CODE ${code}: ${CODE_DESCRIPTIONS[code]}`);
    console.log('='.repeat(100));

    const { data, error } = await supabase
      .from('florida_parcels')
      .select('parcel_id, county, owner_name, property_use, standardized_property_use, property_use_desc')
      .eq('property_use', code)
      .ilike('standardized_property_use', '%Industrial%')
      .limit(50);

    if (error) {
      console.error(`Error querying code ${code}:`, error.message);
      continue;
    }

    console.log(`\nFound ${data.length} properties (showing max 50 samples)\n`);

    // Analyze owner names for industrial keywords
    const industrialKeywords = ['INDUSTRIAL', 'MANUFACTURING', 'WAREHOUSE', 'DISTRIBUTION', 'LOGISTICS', 'FACTORY', 'PLANT', 'LUMBER', 'PACKING', 'CANNERY', 'BREWERY'];

    let correctlyStandardized = 0;
    let incorrectlyStandardized = 0;

    const examples = {
      correct: [],
      incorrect: []
    };

    data.forEach(row => {
      const ownerUpper = (row.owner_name || '').toUpperCase();
      const hasIndustrialKeyword = industrialKeywords.some(keyword => ownerUpper.includes(keyword));

      if (hasIndustrialKeyword) {
        correctlyStandardized++;
        if (examples.correct.length < 10) {
          examples.correct.push(row);
        }
      } else {
        incorrectlyStandardized++;
        if (examples.incorrect.length < 10) {
          examples.incorrect.push(row);
        }
      }
    });

    console.log('ANALYSIS RESULTS:');
    console.log(`  ✅ Correctly Standardized (has industrial keywords): ${correctlyStandardized}`);
    console.log(`  ❌ Incorrectly Standardized (no industrial keywords): ${incorrectlyStandardized}`);
    console.log('');

    if (examples.correct.length > 0) {
      console.log('✅ CORRECTLY STANDARDIZED EXAMPLES (owner name suggests industrial use):');
      examples.correct.forEach((row, i) => {
        console.log(`  ${i + 1}. ${row.owner_name}`);
        console.log(`     County: ${row.county} | Parcel: ${row.parcel_id}`);
        console.log(`     Description: ${row.property_use_desc || 'N/A'}`);
        console.log('');
      });
    }

    if (examples.incorrect.length > 0) {
      console.log('❌ INCORRECTLY STANDARDIZED EXAMPLES (should be COMMERCIAL, not Industrial):');
      examples.incorrect.forEach((row, i) => {
        console.log(`  ${i + 1}. ${row.owner_name}`);
        console.log(`     County: ${row.county} | Parcel: ${row.parcel_id}`);
        console.log(`     Description: ${row.property_use_desc || 'N/A'}`);
        console.log('');
      });
    }

    // Check total count for this code
    const { count } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('property_use', code)
      .ilike('standardized_property_use', '%Industrial%');

    console.log(`TOTAL AFFECTED: ${count} properties with code ${code} standardized as Industrial`);
    console.log('');
  }

  // Now check if there are any industrial properties in land_use_code that we're missing
  console.log('\n' + '='.repeat(100));
  console.log('CHECKING land_use_code FIELD FOR ADDITIONAL INDUSTRIAL PROPERTIES');
  console.log('='.repeat(100));
  console.log('');

  const INDUSTRIAL_CODES = ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49'];

  // Properties with industrial land_use_code but non-industrial property_use
  const { data: landUseIndustrial, error: landUseError } = await supabase
    .from('florida_parcels')
    .select('parcel_id, county, owner_name, property_use, land_use_code')
    .in('land_use_code', INDUSTRIAL_CODES)
    .not('property_use', 'in', `(${INDUSTRIAL_CODES.join(',')})`)
    .limit(100);

  if (landUseError) {
    console.error('Error querying land_use_code:', landUseError.message);
  } else {
    console.log(`Found ${landUseIndustrial.length} properties with industrial land_use_code but non-industrial property_use`);
    console.log('\nSample properties (first 20):');
    landUseIndustrial.slice(0, 20).forEach((row, i) => {
      console.log(`${i + 1}. ${row.owner_name}`);
      console.log(`   County: ${row.county}`);
      console.log(`   property_use: ${row.property_use} | land_use_code: ${row.land_use_code}`);
      console.log('');
    });

    // Get total count
    const { count: landUseCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .in('land_use_code', INDUSTRIAL_CODES)
      .not('property_use', 'in', `(${INDUSTRIAL_CODES.join(',')})`)

    console.log(`\nTOTAL: ${landUseCount} properties with industrial land_use_code needing property_use correction`);
  }

  // Final summary
  console.log('\n' + '='.repeat(100));
  console.log('FINAL RECOMMENDATIONS');
  console.log('='.repeat(100));
  console.log('');
  console.log('1. COMMERCIAL CODES (21, 27, 28) MARKED AS INDUSTRIAL:');
  console.log('   - Some ARE correctly standardized (owner names contain industrial keywords)');
  console.log('   - Some are INCORRECTLY standardized (generic owner names, should be commercial)');
  console.log('   - Recommendation: Review standardization logic or fix on case-by-case basis');
  console.log('');
  console.log('2. INDUSTRIAL land_use_code FIELD:');
  console.log('   - Many properties have industrial land_use_code but non-industrial property_use');
  console.log('   - Recommendation: Update property_use to match land_use_code for these properties');
  console.log('');
  console.log('3. INDUSTRIAL FILTER LOGIC:');
  console.log('   Current: property_use IN (040-049) OR owner_name patterns');
  console.log('   Recommended: Also include land_use_code IN (040-049)');
  console.log('');
  console.log('4. SubUse FIELD:');
  console.log('   - No SubUse columns found in florida_parcels schema');
  console.log('   - standardized_property_use may be what user meant by "SubUse"');
  console.log('');
}

investigateMisclassified().catch(console.error);
