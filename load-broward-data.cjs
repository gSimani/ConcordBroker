/**
 * Load Broward County Property Data into Supabase
 *
 * Loads NAL (names/addresses) data from CSV into florida_parcels table
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
require('dotenv').config({ path: '.env.mcp' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

console.log('🚀 Broward County Data Loader\n');
console.log('=' + '='.repeat(79));

if (!supabaseUrl || !supabaseKey) {
  console.error('\n❌ Missing Supabase credentials!');
  console.error('   SUPABASE_URL:', supabaseUrl ? 'SET' : 'MISSING');
  console.error('   SUPABASE_KEY:', supabaseKey ? 'SET' : 'MISSING');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

const CSV_FILE = path.join(__dirname, 'TEMP', 'DATABASE PROPERTY APP', 'BROWARD', 'NAL', 'NAL16P202501.csv');
const BATCH_SIZE = 100; // Start with small batches
const MAX_RECORDS = 1000; // Load only 1000 records for initial test

async function loadBrowardData() {
  try {
    // Check if file exists
    if (!fs.existsSync(CSV_FILE)) {
      console.error(`\n❌ CSV file not found: ${CSV_FILE}`);
      return;
    }

    const fileSize = fs.statSync(CSV_FILE).size;
    console.log(`\n📁 CSV File: ${CSV_FILE}`);
    console.log(`   Size: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);

    // Read CSV file
    console.log(`\n📖 Reading CSV file...`);
    const csvContent = fs.readFileSync(CSV_FILE, 'utf-8');

    // Parse CSV
    console.log(`   Parsing CSV data...`);
    const records = parse(csvContent, {
      columns: true,
      skip_empty_lines: true,
      relax_column_count: true,
      trim: true
    });

    console.log(`   ✅ Parsed ${records.length.toLocaleString()} total records`);
    console.log(`   📊 Loading first ${MAX_RECORDS} records for testing\n`);

    // Get first N records for testing
    const recordsToLoad = records.slice(0, MAX_RECORDS);

    // Transform records for database
    console.log(`🔄 Transforming records...`);
    const transformedRecords = recordsToLoad.map((record, index) => {
      // Map CSV columns to database columns
      // Based on CLAUDE.md column mapping rules
      return {
        parcel_id: record.PARCEL_ID || record.parcel_id || `BROWARD-${index}`,
        county: 'BROWARD',
        year: 2025,
        owner_name: record.OWN_NAME || record.owner_name || '',
        phy_addr1: record.PHY_ADDR1 || record.phy_addr1 || '',
        phy_addr2: record.PHY_ADDR2 || record.phy_addr2 || '',
        owner_addr1: record.OWN_ADDR1 || record.owner_addr1 || '',
        owner_addr2: record.OWN_ADDR2 || record.owner_addr2 || '',
        owner_city: record.OWN_CITY || record.owner_city || '',
        owner_state: (record.OWN_STATE || record.owner_state || '').substring(0, 2), // Truncate to 2 chars
        owner_zip: record.OWN_ZIP || record.owner_zip || '',
        land_sqft: parseFloat(record.LND_SQFOOT || record.land_sqft || 0) || null,
        just_value: parseFloat(record.JV || record.just_value || 0) || null,
        land_value: parseFloat(record.LND_VAL || record.land_value || 0) || null,
        building_value: null, // Will calculate if both values exist
        city: record.CITY || record.city || '',
        zip: record.ZIP || record.zip || '',
        updated_at: new Date().toISOString()
      };
    }).filter(r => r.parcel_id && r.parcel_id !== ''); // Filter out records without parcel_id

    console.log(`   ✅ Transformed ${transformedRecords.length} valid records\n`);

    if (transformedRecords.length === 0) {
      console.error('❌ No valid records to load!');
      return;
    }

    // Show sample record
    console.log('📋 Sample Record:');
    console.log(JSON.stringify(transformedRecords[0], null, 2));
    console.log('');

    // Load in batches
    console.log(`💾 Loading data in batches of ${BATCH_SIZE}...\n`);

    let totalInserted = 0;
    let totalErrors = 0;

    for (let i = 0; i < transformedRecords.length; i += BATCH_SIZE) {
      const batch = transformedRecords.slice(i, i + BATCH_SIZE);
      const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
      const totalBatches = Math.ceil(transformedRecords.length / BATCH_SIZE);

      process.stdout.write(`   Batch ${batchNumber}/${totalBatches} (${batch.length} records)... `);

      try {
        const { data, error } = await supabase
          .from('florida_parcels')
          .upsert(batch, {
            onConflict: 'parcel_id,county,year',
            ignoreDuplicates: false
          });

        if (error) {
          console.log(`❌ Error: ${error.message}`);
          totalErrors += batch.length;
        } else {
          console.log(`✅ Success`);
          totalInserted += batch.length;
        }
      } catch (err) {
        console.log(`❌ Exception: ${err.message}`);
        totalErrors += batch.length;
      }

      // Small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('\n📊 Load Summary:\n');
    console.log(`   Total Records Processed: ${transformedRecords.length.toLocaleString()}`);
    console.log(`   Successfully Inserted: ${totalInserted.toLocaleString()}`);
    console.log(`   Errors: ${totalErrors.toLocaleString()}`);
    console.log(`   Success Rate: ${((totalInserted / transformedRecords.length) * 100).toFixed(1)}%`);

    // Verify in database
    console.log('\n🔍 Verifying data in database...\n');
    const { count, error: countError } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('county', 'BROWARD');

    if (!countError) {
      console.log(`   ✅ Database contains ${(count || 0).toLocaleString()} Broward records`);
    } else {
      console.log(`   ❌ Could not verify: ${countError.message}`);
    }

    // Get sample records from database
    const { data: sampleData, error: sampleError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, owner_name, phy_addr1, city')
      .eq('county', 'BROWARD')
      .limit(5);

    if (!sampleError && sampleData) {
      console.log('\n📋 Sample records from database:');
      sampleData.forEach((record, i) => {
        console.log(`   ${i + 1}. ${record.owner_name} - ${record.phy_addr1}, ${record.city}`);
      });
    }

    console.log('\n✅ Data loading complete!\n');

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    console.error(error.stack);
  }
}

// Run the loader
loadBrowardData();
