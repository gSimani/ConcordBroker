import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import csv from 'csv-parser';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: 'apps/web/.env' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const COUNTIES = {
  'INDIAN_RIVER': '31',
  'ORANGE': '48',
  'PALM_BEACH': '50',
  'PINELLAS': '52',
  'SANTA_ROSA': '57',
  'ST_JOHNS': '55',
  'ST_LUCIE': '56'
};

async function importCountySales(countyName, countyNo) {
  const basePath = `C:\\TEMP\\DATABASE PROPERTY APP\\${countyName}`;

  // Look for SDF files (Sales Data Files)
  const possiblePaths = [
    path.join(basePath, 'SDF', `${countyName}_SDF.csv`),
    path.join(basePath, `${countyName}_SDF.csv`),
    path.join(basePath, 'SDF.csv')
  ];

  let sdfPath = null;
  for (const testPath of possiblePaths) {
    if (fs.existsSync(testPath)) {
      sdfPath = testPath;
      break;
    }
  }

  if (!sdfPath) {
    console.log(`❌ No SDF file found for ${countyName}`);
    return 0;
  }

  console.log(`📂 Found SDF file: ${sdfPath}`);

  return new Promise((resolve) => {
    const salesData = [];
    let count = 0;

    fs.createReadStream(sdfPath)
      .pipe(csv())
      .on('data', (row) => {
        // Map CSV columns to our database structure
        // Florida SDF standard columns
        const sale = {
          county_no: countyNo,
          parcel_id: row.PARCEL_ID || row.parcel_id || row['Parcel ID'],
          sale_year: parseInt(row.SALE_YR || row.sale_yr || row['Sale Year']) || null,
          sale_month: parseInt(row.SALE_MO || row.sale_mo || row['Sale Month']) || null,
          sale_price: parseFloat(row.SALE_PRC || row.sale_prc || row['Sale Price']) || 0,
          or_book: row.OR_BOOK || row.or_book || row['OR Book'],
          or_page: row.OR_PAGE || row.or_page || row['OR Page'],
          quality_code: row.QUAL_CD || row.qual_cd || row['Qual Code'] || 'Q',
          verification_code: row.VI_CD || row.vi_cd || row['VI Code'] || 'WD'
        };

        // Only import qualified sales with reasonable prices
        if (sale.sale_price > 1000 && sale.quality_code === 'Q') {
          salesData.push(sale);
          count++;

          // Batch insert every 100 records
          if (salesData.length >= 100) {
            insertBatch(salesData.splice(0, 100));
          }
        }
      })
      .on('end', async () => {
        // Insert remaining records
        if (salesData.length > 0) {
          await insertBatch(salesData);
        }
        console.log(`✅ Imported ${count} sales for ${countyName}`);
        resolve(count);
      })
      .on('error', (err) => {
        console.error(`❌ Error reading ${countyName}:`, err);
        resolve(0);
      });
  });
}

async function insertBatch(batch) {
  const { error } = await supabase
    .from('property_sales_history')
    .insert(batch);

  if (error) {
    console.error('Insert error:', error.message);
  }
}

async function main() {
  console.log('========================================');
  console.log('IMPORTING FLORIDA SALES DATA');
  console.log('========================================\n');

  let totalImported = 0;

  for (const [countyName, countyNo] of Object.entries(COUNTIES)) {
    console.log(`\nProcessing ${countyName} (County #${countyNo})...`);
    const count = await importCountySales(countyName, countyNo);
    totalImported += count;
  }

  console.log('\n========================================');
  console.log(`IMPORT COMPLETE: ${totalImported} total sales imported`);
  console.log('========================================');

  // Verify the import
  const { count } = await supabase
    .from('property_sales_history')
    .select('*', { count: 'exact', head: true });

  console.log(`\n📊 Total records in property_sales_history: ${count}`);
}

main();