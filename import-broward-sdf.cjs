const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const csv = require('csv-parser');
require('dotenv').config({ path: '.env.mcp' });

// Supabase configuration
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// File path to Broward SDF data
const BROWARD_SDF_PATH = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP\\BROWARD\\SDF\\SDF16P202501.csv';

// Property we're looking for
const TARGET_PROPERTY = '514124070600';

// Parse SDF record
function parseSdfRecord(row) {
  // SDF file format (tab-delimited):
  // Columns: parcel_id, sale_yr1, sale_mo1, sale_price1, or_book1, or_page1, qual_code1, vi_code1, ...
  const fields = Object.values(row);

  // Parse the first sale (most recent)
  const record = {
    county_no: '06', // Broward County
    parcel_id: (fields[0] || '').toString().trim(),
    sale_year: parseInt(fields[1]) || null,
    sale_month: parseInt(fields[2]) || null,
    sale_price: parseFloat(fields[3]) || 0,
    or_book: (fields[4] || '').toString().trim(),
    or_page: (fields[5] || '').toString().trim(),
    quality_code: (fields[6] || '').toString().trim(),
    verification_code: (fields[7] || '').toString().trim()
  };

  return record;
}

// Import data to Supabase
async function importToSupabase(records) {
  const batchSize = 1000;
  let totalImported = 0;
  let targetPropertyFound = false;
  let targetPropertySales = [];

  // Process in batches
  for (let i = 0; i < records.length; i += batchSize) {
    const batch = records.slice(i, i + batchSize);

    // Check for target property in this batch
    const targetInBatch = batch.filter(r => r.parcel_id === TARGET_PROPERTY);
    if (targetInBatch.length > 0) {
      targetPropertyFound = true;
      targetPropertySales = targetPropertySales.concat(targetInBatch);
    }

    // Insert into fl_sdf table
    const { data, error } = await supabase
      .from('fl_sdf')
      .upsert(batch, {
        onConflict: 'parcel_id,county_no,sale_year,sale_month',
        ignoreDuplicates: true
      });

    if (error) {
      console.error(`Error importing batch ${i / batchSize + 1}:`, error.message);
    } else {
      totalImported += batch.length;
      process.stdout.write(`\rImported: ${totalImported} records`);
    }
  }

  console.log(`\nTotal imported: ${totalImported} records`);

  // Import to property_sales_history for better compatibility
  if (targetPropertySales.length > 0) {
    console.log(`\nImporting ${targetPropertySales.length} sales for property ${TARGET_PROPERTY} to property_sales_history...`);

    const salesHistoryRecords = targetPropertySales.map(sale => ({
      parcel_id: sale.parcel_id,
      county_no: sale.county_no,
      sale_year: sale.sale_year,
      sale_month: sale.sale_month,
      sale_price: sale.sale_price,
      or_book: sale.or_book,
      or_page: sale.or_page,
      quality_code: sale.quality_code,
      verification_code: sale.verification_code,
      deed_type: sale.quality_code === 'Q' ? 'WD' : 'QC'
    }));

    const { error: historyError } = await supabase
      .from('property_sales_history')
      .upsert(salesHistoryRecords, {
        onConflict: 'parcel_id,sale_year,sale_month',
        ignoreDuplicates: true
      });

    if (historyError) {
      console.error('Error importing to property_sales_history:', historyError.message);
    } else {
      console.log('✅ Successfully imported to property_sales_history');
    }
  }

  return { totalImported, targetPropertyFound, targetPropertySales };
}

// Main function
async function main() {
  console.log('========================================');
  console.log('BROWARD COUNTY SDF IMPORTER');
  console.log('========================================');
  console.log(`File: ${path.basename(BROWARD_SDF_PATH)}`);
  console.log(`Target Property: ${TARGET_PROPERTY}`);
  console.log('');

  // Check if file exists
  if (!fs.existsSync(BROWARD_SDF_PATH)) {
    console.error('❌ SDF file not found!');
    console.error(`Path: ${BROWARD_SDF_PATH}`);
    return;
  }

  const fileStats = fs.statSync(BROWARD_SDF_PATH);
  console.log(`File size: ${(fileStats.size / 1024 / 1024).toFixed(2)} MB`);
  console.log('');

  // Read and parse the CSV file
  console.log('Reading SDF file...');
  const records = [];
  let lineCount = 0;

  await new Promise((resolve, reject) => {
    fs.createReadStream(BROWARD_SDF_PATH)
      .pipe(csv({
        separator: '\t', // Tab-delimited
        headers: false   // No headers
      }))
      .on('data', (row) => {
        lineCount++;

        // Parse the record
        const record = parseSdfRecord(row);

        // Only include valid sales
        if (record.parcel_id && record.sale_year && record.sale_price > 0) {
          records.push(record);
        }

        // Progress indicator
        if (lineCount % 10000 === 0) {
          process.stdout.write(`\rProcessed: ${lineCount} lines, ${records.length} valid sales`);
        }
      })
      .on('end', () => {
        console.log(`\n\nTotal lines: ${lineCount}`);
        console.log(`Valid sales: ${records.length}`);
        resolve();
      })
      .on('error', reject);
  });

  // Check if target property is in the data
  const targetSales = records.filter(r => r.parcel_id === TARGET_PROPERTY);
  if (targetSales.length > 0) {
    console.log(`\n✅ Found ${targetSales.length} sales for property ${TARGET_PROPERTY}:`);
    targetSales.slice(0, 5).forEach(sale => {
      console.log(`  ${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}: $${sale.sale_price.toLocaleString()}`);
    });
  } else {
    console.log(`\n⚠️ Property ${TARGET_PROPERTY} not found in this file`);
  }

  // Import to Supabase
  console.log('\nImporting to Supabase...');
  const { totalImported, targetPropertyFound, targetPropertySales } = await importToSupabase(records);

  // Verify the import
  console.log('\nVerifying import...');
  const { data: verifyData, error: verifyError } = await supabase
    .from('property_sales_history')
    .select('*')
    .eq('parcel_id', TARGET_PROPERTY)
    .order('sale_year', { ascending: false })
    .order('sale_month', { ascending: false })
    .limit(5);

  if (verifyError) {
    console.error('Error verifying:', verifyError.message);
  } else if (verifyData && verifyData.length > 0) {
    console.log(`\n✅ SUCCESS! Property ${TARGET_PROPERTY} now has ${verifyData.length} sales in database:`);
    verifyData.forEach(sale => {
      const date = sale.sale_date || `${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}`;
      console.log(`  ${date}: $${sale.sale_price.toLocaleString()} (${sale.quality_code})`);
    });
  } else {
    console.log(`\n⚠️ No sales found for property ${TARGET_PROPERTY} after import`);
  }

  console.log('\n========================================');
  console.log('Import complete!');
  console.log('Next step: Check the property detail page');
  console.log('URL: http://localhost:5173/property/514124070600');
  console.log('========================================');
}

// Run the import
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});