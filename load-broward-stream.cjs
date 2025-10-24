/**
 * Load Broward County Property Data into Supabase (Streaming Version)
 *
 * Uses streaming to handle large CSV files without running out of memory
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse');
require('dotenv').config({ path: '.env.mcp' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

console.log('🚀 Broward County Data Loader (Streaming)\n');
console.log('=' + '='.repeat(79));

if (!supabaseUrl || !supabaseKey) {
  console.error('\n❌ Missing Supabase credentials!');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

const CSV_FILE = path.join(__dirname, 'TEMP', 'DATABASE PROPERTY APP', 'BROWARD', 'NAL', 'NAL16P202501.csv');
const BATCH_SIZE = 500;
const MAX_RECORDS = 5000; // Test with 5000 records

async function loadBrowardData() {
  try {
    if (!fs.existsSync(CSV_FILE)) {
      console.error(`\n❌ CSV file not found: ${CSV_FILE}`);
      return;
    }

    const fileSize = fs.statSync(CSV_FILE).size;
    console.log(`\n📁 CSV File: ${CSV_FILE}`);
    console.log(`   Size: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`   Loading first ${MAX_RECORDS.toLocaleString()} records\n`);

    let recordsProcessed = 0;
    let totalInserted = 0;
    let totalErrors = 0;
    let batch = [];
    let batchNumber = 0;

    // Create streaming parser
    const parser = fs.createReadStream(CSV_FILE)
      .pipe(parse({
        columns: true,
        skip_empty_lines: true,
        relax_column_count: true,
        trim: true
      }));

    // Process records as they come in
    for await (const record of parser) {
      if (recordsProcessed >= MAX_RECORDS) {
        parser.destroy(); // Stop reading
        break;
      }

      recordsProcessed++;

      // Transform record
      const transformed = {
        parcel_id: record.PARCEL_ID || record.parcel_id || `BROWARD-${recordsProcessed}`,
        county: 'BROWARD',
        year: 2025,
        owner_name: record.OWN_NAME || record.owner_name || '',
        phy_addr1: record.PHY_ADDR1 || record.phy_addr1 || '',
        phy_addr2: record.PHY_ADDR2 || record.phy_addr2 || '',
        owner_addr1: record.OWN_ADDR1 || record.owner_addr1 || '',
        owner_addr2: record.OWN_ADDR2 || record.owner_addr2 || '',
        owner_city: record.OWN_CITY || record.owner_city || '',
        owner_state: (record.OWN_STATE || record.owner_state || '').substring(0, 2),
        owner_zip: record.OWN_ZIP || record.owner_zip || '',
        land_sqft: parseFloat(record.LND_SQFOOT || record.land_sqft || 0) || null,
        just_value: parseFloat(record.JV || record.just_value || 0) || null,
        land_value: parseFloat(record.LND_VAL || record.land_value || 0) || null,
        city: record.CITY || record.city || '',
        zip: record.ZIP || record.zip || '',
        updated_at: new Date().toISOString()
      };

      // Only add valid records
      if (transformed.parcel_id && transformed.parcel_id !== '') {
        batch.push(transformed);
      }

      // Insert batch when it reaches BATCH_SIZE
      if (batch.length >= BATCH_SIZE) {
        batchNumber++;
        const totalBatches = Math.ceil(MAX_RECORDS / BATCH_SIZE);

        process.stdout.write(`   Batch ${batchNumber}/${totalBatches} (${batch.length} records)... `);

        try {
          const { data, error, status, statusText } = await supabase
            .from('florida_parcels')
            .insert(batch); // Use insert instead of upsert for now

          if (error) {
            console.log(`❌ Error: ${error.message || JSON.stringify(error)}`);
            if (batchNumber === 1) {
              console.log(`   Details: ${JSON.stringify(error, null, 2)}`);
              console.log(`   Sample record: ${JSON.stringify(batch[0], null, 2)}`);
            }
            totalErrors += batch.length;
          } else {
            console.log(`✅`);
            totalInserted += batch.length;
          }
        } catch (err) {
          console.log(`❌ Exception: ${err.message}`);
          if (batchNumber === 1) {
            console.log(`   Stack: ${err.stack}`);
          }
          totalErrors += batch.length;
        }

        batch = []; // Clear batch

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 50));
      }
    }

    // Insert remaining records in batch
    if (batch.length > 0) {
      batchNumber++;
      process.stdout.write(`   Final batch (${batch.length} records)... `);

      try {
        const { data, error } = await supabase
          .from('florida_parcels')
          .insert(batch);

        if (error) {
          console.log(`❌ Error: ${error.message || JSON.stringify(error)}`);
          totalErrors += batch.length;
        } else {
          console.log(`✅`);
          totalInserted += batch.length;
        }
      } catch (err) {
        console.log(`❌ Exception: ${err.message}`);
        totalErrors += batch.length;
      }
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('\n📊 Load Summary:\n');
    console.log(`   Records Processed: ${recordsProcessed.toLocaleString()}`);
    console.log(`   Successfully Inserted: ${totalInserted.toLocaleString()}`);
    console.log(`   Errors: ${totalErrors.toLocaleString()}`);
    console.log(`   Success Rate: ${((totalInserted / recordsProcessed) * 100).toFixed(1)}%`);

    // Verify in database
    console.log('\n🔍 Verifying data in database...\n');
    const { count } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('county', 'BROWARD');

    console.log(`   ✅ Database contains ${(count || 0).toLocaleString()} Broward records`);

    // Get sample records
    const { data: sampleData } = await supabase
      .from('florida_parcels')
      .select('parcel_id, owner_name, phy_addr1, city, just_value')
      .eq('county', 'BROWARD')
      .order('just_value', { ascending: false })
      .limit(5);

    if (sampleData) {
      console.log('\n📋 Top 5 Properties by Value:');
      sampleData.forEach((record, i) => {
        const value = record.just_value ? `$${record.just_value.toLocaleString()}` : 'N/A';
        console.log(`   ${i + 1}. ${record.owner_name || 'Unknown'}`);
        console.log(`      ${record.phy_addr1 || 'No address'}, ${record.city || 'Unknown'}`);
        console.log(`      Value: ${value}`);
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
