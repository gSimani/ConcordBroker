const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
);

const VALID_INDUSTRIAL_CODES = [
  '040', '041', '042', '043', '044', '045', '046', '047', '048', '049',
  '40', '41', '42', '43', '44', '45', '46', '47', '48', '49'
];

async function comprehensiveIndustrialSearch() {
  console.log('='.repeat(100));
  console.log('COMPREHENSIVE INDUSTRIAL PROPERTY SEARCH');
  console.log('='.repeat(100));
  console.log('');

  // Step 1: Check what columns exist in florida_parcels
  console.log('Step 1: Checking database schema for industrial-related fields...\n');

  const { data: sampleRow } = await supabase
    .from('florida_parcels')
    .select('*')
    .limit(1);

  if (sampleRow && sampleRow[0]) {
    const columns = Object.keys(sampleRow[0]);
    const industrialColumns = columns.filter(col =>
      col.toLowerCase().includes('use') ||
      col.toLowerCase().includes('category') ||
      col.toLowerCase().includes('type') ||
      col.toLowerCase().includes('class')
    );

    console.log('Found columns related to property classification:');
    industrialColumns.forEach(col => console.log(`  - ${col}`));
    console.log('');
  }

  // Step 2: Count properties by DOR industrial codes (040-049)
  console.log('Step 2: Counting properties with official DOR Industrial codes (040-049)...\n');

  const { count: dorCount } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .in('property_use', VALID_INDUSTRIAL_CODES);

  console.log(`Properties with DOR codes (040-049): ${(dorCount || 0).toLocaleString()}\n`);

  // Step 3: Search standardized_property_use for "Industrial"
  console.log('Step 3: Searching standardized_property_use field for "Industrial"...\n');

  const { data: standardizedData } = await supabase
    .from('florida_parcels')
    .select('property_use, standardized_property_use')
    .ilike('standardized_property_use', '%Industrial%')
    .limit(10000);

  const standardizedCounts = {};
  standardizedData?.forEach(row => {
    const key = `${row.property_use} -> ${row.standardized_property_use}`;
    standardizedCounts[key] = (standardizedCounts[key] || 0) + 1;
  });

  console.log('Top 20 combinations:');
  Object.entries(standardizedCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .forEach(([combo, count]) => {
      console.log(`  ${combo}: ${count.toLocaleString()}`);
    });
  console.log('');

  // Step 4: Check property_use_desc field
  console.log('Step 4: Checking property_use_desc field for industrial keywords...\n');

  const { data: descData } = await supabase
    .from('florida_parcels')
    .select('property_use, property_use_desc')
    .or('property_use_desc.ilike.%Industrial%,property_use_desc.ilike.%warehouse%,property_use_desc.ilike.%manufacturing%,property_use_desc.ilike.%factory%')
    .limit(1000);

  if (descData && descData.length > 0) {
    console.log(`Found ${descData.length} properties with industrial in description`);
    console.log('Sample:');
    descData.slice(0, 10).forEach(row => {
      console.log(`  ${row.property_use} -> "${row.property_use_desc}"`);
    });
  } else {
    console.log('No properties found with industrial in property_use_desc');
  }
  console.log('');

  // Step 5: Search ALL distinct property_use values to find any we missed
  console.log('Step 5: Getting ALL distinct property_use values...\n');

  const { data: allUses } = await supabase
    .from('florida_parcels')
    .select('property_use')
    .limit(100000);

  const useCounts = {};
  allUses?.forEach(row => {
    const code = row.property_use || 'NULL';
    useCounts[code] = (useCounts[code] || 0) + 1;
  });

  const sortedUses = Object.entries(useCounts).sort((a, b) => b[1] - a[1]);

  console.log('All distinct property_use codes (top 50):');
  console.log('Code'.padEnd(30) + 'Count'.padStart(12) + '  Industrial?');
  console.log('-'.repeat(60));

  sortedUses.slice(0, 50).forEach(([code, count]) => {
    const isIndustrial = VALID_INDUSTRIAL_CODES.includes(code) ||
                         code.toLowerCase().includes('ind') ||
                         code.toLowerCase().includes('warehouse') ||
                         code.toLowerCase().includes('factory') ||
                         code.toLowerCase().includes('manufact');
    const marker = isIndustrial ? '✅ INDUSTRIAL' : '';
    console.log(`${code.padEnd(30)}${count.toString().padStart(12)}  ${marker}`);
  });
  console.log('');

  // Step 6: Check for sub_use or subuse columns
  console.log('Step 6: Checking for SubUse/sub_use fields...\n');

  const columns = sampleRow && sampleRow[0] ? Object.keys(sampleRow[0]) : [];
  const subUseColumns = columns.filter(col =>
    col.toLowerCase().includes('sub') && col.toLowerCase().includes('use')
  );

  if (subUseColumns.length > 0) {
    console.log('Found SubUse columns:', subUseColumns.join(', '));

    for (const col of subUseColumns) {
      console.log(`\nAnalyzing column: ${col}`);

      const query = supabase.from('florida_parcels').select(col).limit(10000);
      const { data: subUseData } = await query;

      if (subUseData) {
        const subUseCounts = {};
        subUseData.forEach(row => {
          const value = row[col] || 'NULL';
          if (value && value.toString().toLowerCase().includes('ind')) {
            subUseCounts[value] = (subUseCounts[value] || 0) + 1;
          }
        });

        if (Object.keys(subUseCounts).length > 0) {
          console.log('Industrial-related SubUse values found:');
          Object.entries(subUseCounts)
            .sort((a, b) => b[1] - a[1])
            .forEach(([value, count]) => {
              console.log(`  ${value}: ${count.toLocaleString()}`);
            });
        } else {
          console.log('No industrial-related values found in this column');
        }
      }
    }
  } else {
    console.log('No SubUse columns found in database schema');
  }
  console.log('');

  // Step 7: Search land_use_code field
  console.log('Step 7: Checking land_use_code field for industrial codes...\n');

  const { data: landUseData } = await supabase
    .from('florida_parcels')
    .select('property_use, land_use_code')
    .in('land_use_code', VALID_INDUSTRIAL_CODES)
    .limit(1000);

  if (landUseData && landUseData.length > 0) {
    console.log(`Found ${landUseData.length} properties with industrial land_use_code`);

    const landUseCombos = {};
    landUseData.forEach(row => {
      const combo = `property_use: ${row.property_use}, land_use_code: ${row.land_use_code}`;
      landUseCombos[combo] = (landUseCombos[combo] || 0) + 1;
    });

    console.log('Top combinations:');
    Object.entries(landUseCombos)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .forEach(([combo, count]) => {
        console.log(`  ${combo}: ${count}`);
      });
  } else {
    console.log('No properties found with industrial land_use_code');
  }
  console.log('');

  // Step 8: Final comprehensive count
  console.log('='.repeat(100));
  console.log('FINAL COMPREHENSIVE INDUSTRIAL COUNT');
  console.log('='.repeat(100));
  console.log('');

  // Method 1: DOR codes in property_use
  const { count: method1 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .in('property_use', VALID_INDUSTRIAL_CODES);

  console.log(`Method 1 - DOR codes (property_use): ${(method1 || 0).toLocaleString()}`);

  // Method 2: DOR codes in land_use_code
  const { count: method2 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .in('land_use_code', VALID_INDUSTRIAL_CODES);

  console.log(`Method 2 - DOR codes (land_use_code): ${(method2 || 0).toLocaleString()}`);

  // Method 3: Standardized as Industrial
  const { count: method3 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .ilike('standardized_property_use', '%Industrial%');

  console.log(`Method 3 - Standardized "Industrial": ${(method3 || 0).toLocaleString()}`);

  // Method 4: Owner name patterns
  const { count: method4 } = await supabase
    .from('florida_parcels')
    .select('*', { count: 'exact', head: true })
    .or('owner_name.ilike.%INDUSTRIAL%,owner_name.ilike.%MANUFACTURING%,owner_name.ilike.%WAREHOUSE%,owner_name.ilike.%FACTORY%,owner_name.ilike.%PLANT%,owner_name.ilike.%DISTRIBUTION%,owner_name.ilike.%LOGISTICS%');

  console.log(`Method 4 - Owner name patterns: ${(method4 || 0).toLocaleString()}`);

  console.log('');
  console.log('='.repeat(100));
  console.log('RECOMMENDATION');
  console.log('='.repeat(100));
  console.log('');
  console.log(`The Industrial filter should use:`);
  console.log(`  PRIMARY: property_use IN (${VALID_INDUSTRIAL_CODES.slice(0, 5).join(', ')}, ...)`);

  if (method2 > 0) {
    console.log(`  OR: land_use_code IN (${VALID_INDUSTRIAL_CODES.slice(0, 5).join(', ')}, ...)`);
  }

  if (method3 > 0) {
    console.log(`  OR: standardized_property_use ILIKE '%Industrial%'`);
  }

  console.log(`  OR: owner_name ILIKE '%INDUSTRIAL|MANUFACTURING|WAREHOUSE|FACTORY|PLANT%'`);
  console.log('');
  console.log(`TOTAL POTENTIAL INDUSTRIAL PROPERTIES: ${Math.max(method1, method2, method3, method4).toLocaleString()}`);
  console.log('='.repeat(100));
}

comprehensiveIndustrialSearch().catch(console.error);
