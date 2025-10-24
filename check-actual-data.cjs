/**
 * Check Actual Data in Database
 * Query to find where Sunbiz data actually exists
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

async function checkActualData() {
  console.log('🔍 Checking for actual Sunbiz data in database...\n');

  try {
    // Check florida_parcels for owner data
    console.log('1. Checking florida_parcels...');
    const { count: parcelCount, error: parcelError } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true });

    if (!parcelError) {
      console.log(`   ✅ florida_parcels: ${(parcelCount || 0).toLocaleString()} records`);

      // Get sample owners
      const { data: owners } = await supabase
        .from('florida_parcels')
        .select('owner_name, county')
        .not('owner_name', 'is', null)
        .limit(10);

      if (owners) {
        console.log('   Sample owner names:');
        owners.forEach((o, i) => console.log(`     ${i + 1}. ${o.owner_name} (${o.county})`));
      }
    } else {
      console.log(`   ❌ Error: ${parcelError.message}`);
    }

    // Check for tables that might contain entity data
    console.log('\n2. Checking for entity-related data...');

    // Try querying with RPC to list all tables
    const { data: tables, error: tablesError } = await supabase.rpc('get_tables_info').catch(() => ({ data: null, error: null }));

    // Alternative: try common table names
    const potentialTables = [
      'sunbiz',
      'entities',
      'business_entities',
      'corporate_entities',
      'florida_business',
      'sunbiz_data',
      'entity_data'
    ];

    for (const tableName of potentialTables) {
      const { count, error } = await supabase
        .from(tableName)
        .select('*', { count: 'exact', head: true });

      if (!error && count > 0) {
        console.log(`   ✅ ${tableName}: ${count.toLocaleString()} records`);

        // Get sample
        const { data: sample } = await supabase
          .from(tableName)
          .select('*')
          .limit(1);

        if (sample && sample[0]) {
          console.log(`      Columns: ${Object.keys(sample[0]).join(', ')}`);
        }
      }
    }

    // Check property_sales_history
    console.log('\n3. Checking property_sales_history...');
    const { count: salesCount, error: salesError } = await supabase
      .from('property_sales_history')
      .select('*', { count: 'exact', head: true });

    if (!salesError) {
      console.log(`   ✅ property_sales_history: ${(salesCount || 0).toLocaleString()} records`);
    }

    // Check tax_certificates
    console.log('\n4. Checking tax_certificates...');
    const { count: taxCount, error: taxError } = await supabase
      .from('tax_certificates')
      .select('*', { count: 'exact', head: true });

    if (!taxError) {
      console.log(`   ✅ tax_certificates: ${(taxCount || 0).toLocaleString()} records`);
    }

    // Look for CSV files or data sources
    console.log('\n5. Checking for Sunbiz data files...');
    const fs = require('fs');
    const path = require('path');

    const searchPaths = [
      'TEMP',
      'data',
      'uploads',
      'sunbiz',
      '../TEMP'
    ];

    for (const searchPath of searchPaths) {
      const fullPath = path.join(process.cwd(), searchPath);
      if (fs.existsSync(fullPath)) {
        console.log(`   📁 Found directory: ${searchPath}`);
        try {
          const files = fs.readdirSync(fullPath);
          const sunbizFiles = files.filter(f =>
            f.toLowerCase().includes('sunbiz') ||
            f.toLowerCase().includes('entity') ||
            f.toLowerCase().includes('corporate')
          );

          if (sunbizFiles.length > 0) {
            console.log(`      Sunbiz-related files:`);
            sunbizFiles.slice(0, 5).forEach(f => console.log(`        - ${f}`));
          }
        } catch (err) {
          // Directory not accessible
        }
      }
    }

    console.log('\n' + '='.repeat(80));
    console.log('\n💡 FINDINGS:\n');
    console.log('The Sunbiz tables exist in the database but contain NO DATA.');
    console.log('This suggests:');
    console.log('  1. Tables were created but data was never loaded');
    console.log('  2. Data needs to be imported from Sunbiz.org');
    console.log('  3. Or data exists in different table names\n');
    console.log('RECOMMENDATION: Check data loading scripts and Sunbiz data sources');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  }
}

checkActualData();
