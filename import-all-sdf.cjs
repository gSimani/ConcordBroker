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

// Base path to SDF files
const SDF_BASE_PATH = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP';

// Property we're looking for
const TARGET_PROPERTY = '514124070600';

// County code mapping
const COUNTY_CODES = {
  'ALACHUA': '01', 'BAKER': '02', 'BAY': '03', 'BRADFORD': '04', 'BREVARD': '05',
  'BROWARD': '06', 'CALHOUN': '07', 'CHARLOTTE': '08', 'CITRUS': '09', 'CLAY': '10',
  'COLLIER': '11', 'COLUMBIA': '12', 'DADE': '13', 'MIAMI-DADE': '13', 'DESOTO': '14',
  'DIXIE': '15', 'DUVAL': '16', 'ESCAMBIA': '17', 'FLAGLER': '18', 'FRANKLIN': '19',
  'GADSDEN': '20', 'GILCHRIST': '21', 'GLADES': '22', 'GULF': '23', 'HAMILTON': '24',
  'HARDEE': '25', 'HENDRY': '26', 'HERNANDO': '27', 'HIGHLANDS': '28', 'HILLSBOROUGH': '29',
  'HOLMES': '30', 'INDIAN RIVER': '31', 'JACKSON': '32', 'JEFFERSON': '33', 'LAFAYETTE': '34',
  'LAKE': '35', 'LEE': '36', 'LEON': '37', 'LEVY': '38', 'LIBERTY': '39', 'MADISON': '40',
  'MANATEE': '41', 'MARION': '42', 'MARTIN': '43', 'MONROE': '44', 'NASSAU': '45',
  'OKALOOSA': '46', 'OKEECHOBEE': '47', 'ORANGE': '48', 'OSCEOLA': '49', 'PALM BEACH': '50',
  'PASCO': '51', 'PINELLAS': '52', 'POLK': '53', 'PUTNAM': '54', 'SANTA ROSA': '57',
  'SARASOTA': '58', 'SEMINOLE': '59', 'ST. JOHNS': '55', 'ST. LUCIE': '56', 'SUMTER': '60',
  'SUWANNEE': '61', 'TAYLOR': '62', 'UNION': '63', 'VOLUSIA': '64', 'WAKULLA': '65',
  'WALTON': '66', 'WASHINGTON': '67'
};

// Create table if it doesn't exist
async function createTables() {
  console.log('Creating tables...');

  // Create property_sales_history table
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS property_sales_history (
      id bigserial PRIMARY KEY,
      parcel_id varchar(50) NOT NULL,
      county_no varchar(3),
      county_name varchar(50),
      sale_year integer,
      sale_month integer,
      sale_day integer,
      sale_date date GENERATED ALWAYS AS (
        CASE
          WHEN sale_year IS NOT NULL AND sale_month IS NOT NULL THEN
            make_date(sale_year, sale_month, COALESCE(sale_day, 1))
          ELSE NULL
        END
      ) STORED,
      sale_price numeric(15,2),
      or_book varchar(20),
      or_page varchar(20),
      clerk_no varchar(50),
      quality_code varchar(5),
      verification_code varchar(10),
      deed_type varchar(10),
      multi_parcel_sale varchar(5),
      sale_id varchar(50),
      sale_change_code varchar(5),
      state_parcel_id varchar(100),
      created_at timestamp with time zone DEFAULT now(),
      UNIQUE(parcel_id, county_no, sale_year, sale_month, sale_id)
    );
  `;

  // Also create indexes
  const createIndexesSQL = `
    CREATE INDEX IF NOT EXISTS idx_property_sales_parcel_id ON property_sales_history(parcel_id);
    CREATE INDEX IF NOT EXISTS idx_property_sales_county ON property_sales_history(county_no);
    CREATE INDEX IF NOT EXISTS idx_property_sales_date ON property_sales_history(sale_date);
    CREATE INDEX IF NOT EXISTS idx_property_sales_price ON property_sales_history(sale_price);
  `;

  try {
    // Use the MCP API to execute SQL
    const response = await fetch('http://localhost:3001/api/supabase/execute-sql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'concordbroker-mcp-key'
      },
      body: JSON.stringify({
        sql: createTableSQL + createIndexesSQL
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    console.log('✅ Tables and indexes created successfully');
  } catch (error) {
    console.log('⚠️ Using direct Supabase query (SQL execution may be limited)');
    // Fallback - just continue, table might already exist
  }
}

// Find all SDF files
function findSdfFiles() {
  const sdfFiles = [];

  // Read all county directories
  const counties = fs.readdirSync(SDF_BASE_PATH, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  for (const county of counties) {
    const sdfDir = path.join(SDF_BASE_PATH, county, 'SDF');

    if (fs.existsSync(sdfDir)) {
      const files = fs.readdirSync(sdfDir)
        .filter(file => file.toLowerCase().includes('sdf') && file.toLowerCase().endsWith('.csv'));

      for (const file of files) {
        sdfFiles.push({
          county: county,
          countyCode: COUNTY_CODES[county] || '00',
          filePath: path.join(sdfDir, file),
          fileName: file
        });
      }
    }
  }

  return sdfFiles;
}

// Parse SDF record from CSV
function parseSdfRecord(row, countyCode, countyName) {
  const record = {
    parcel_id: (row.PARCEL_ID || '').toString().replace(/"/g, '').trim(),
    county_no: countyCode,
    county_name: countyName,
    sale_year: parseInt(row.SALE_YR) || null,
    sale_month: parseInt(row.SALE_MO) || null,
    sale_day: null, // Not provided in this format
    sale_price: parseFloat(row.SALE_PRC) || 0,
    or_book: (row.OR_BOOK || '').toString().trim(),
    or_page: (row.OR_PAGE || '').toString().trim(),
    clerk_no: (row.CLERK_NO || '').toString().trim(),
    quality_code: (row.QUAL_CD || '').toString().trim(),
    verification_code: (row.VI_CD || '').toString().trim(),
    deed_type: (row.QUAL_CD === 'Q') ? 'WD' : 'QC',
    multi_parcel_sale: (row.MULTI_PAR_SAL || '').toString().trim(),
    sale_id: (row.SALE_ID_CD || '').toString().trim(),
    sale_change_code: (row.SAL_CHG_CD || '').toString().trim(),
    state_parcel_id: (row.STATE_PARCEL_ID || '').toString().trim()
  };

  return record;
}

// Import a single file
async function importSdfFile(fileInfo) {
  console.log(`\n📁 Processing ${fileInfo.county} County...`);
  console.log(`   File: ${fileInfo.fileName}`);

  const fileStats = fs.statSync(fileInfo.filePath);
  console.log(`   Size: ${(fileStats.size / 1024 / 1024).toFixed(2)} MB`);

  const records = [];
  let lineCount = 0;
  let targetPropertySales = [];

  await new Promise((resolve, reject) => {
    fs.createReadStream(fileInfo.filePath)
      .pipe(csv())
      .on('data', (row) => {
        lineCount++;

        // Parse the record
        const record = parseSdfRecord(row, fileInfo.countyCode, fileInfo.county);

        // Only include valid sales
        if (record.parcel_id && record.sale_year && record.sale_price > 0) {
          records.push(record);

          // Check for target property
          if (record.parcel_id === TARGET_PROPERTY) {
            targetPropertySales.push(record);
          }
        }

        // Progress indicator
        if (lineCount % 10000 === 0) {
          process.stdout.write(`\r   Processed: ${lineCount} lines, ${records.length} valid sales`);
        }
      })
      .on('end', () => {
        console.log(`\n   Total lines: ${lineCount}`);
        console.log(`   Valid sales: ${records.length}`);
        resolve();
      })
      .on('error', reject);
  });

  // Import to Supabase
  if (records.length > 0) {
    console.log('   Importing to Supabase...');

    const batchSize = 1000;
    let totalImported = 0;

    for (let i = 0; i < records.length; i += batchSize) {
      const batch = records.slice(i, i + batchSize);

      const { error } = await supabase
        .from('property_sales_history')
        .upsert(batch, {
          onConflict: 'parcel_id,county_no,sale_year,sale_month,sale_id',
          ignoreDuplicates: true
        });

      if (error) {
        console.error(`   Error importing batch ${i / batchSize + 1}:`, error.message);
      } else {
        totalImported += batch.length;
        process.stdout.write(`\r   Imported: ${totalImported}/${records.length} records`);
      }
    }

    console.log(`\n   ✅ Import complete: ${totalImported} records`);
  }

  // Report target property finds
  if (targetPropertySales.length > 0) {
    console.log(`   🎯 FOUND TARGET PROPERTY! ${targetPropertySales.length} sales for ${TARGET_PROPERTY}`);
    targetPropertySales.slice(0, 3).forEach(sale => {
      console.log(`      ${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}: $${sale.sale_price.toLocaleString()}`);
    });
  }

  return { records: records.length, targetSales: targetPropertySales.length };
}

// Main function
async function main() {
  console.log('========================================');
  console.log('FLORIDA SDF DATA IMPORTER (ALL COUNTIES)');
  console.log('========================================');
  console.log(`Target Property: ${TARGET_PROPERTY}`);

  // Create tables
  await createTables();

  // Find all SDF files
  console.log('\nScanning for SDF files...');
  const sdfFiles = findSdfFiles();

  console.log(`Found ${sdfFiles.length} SDF files across ${new Set(sdfFiles.map(f => f.county)).size} counties`);

  if (sdfFiles.length === 0) {
    console.log('No SDF files found!');
    return;
  }

  // Process each file
  let totalRecords = 0;
  let totalTargetSales = 0;
  let countiesWithTarget = [];

  for (const fileInfo of sdfFiles) {
    const result = await importSdfFile(fileInfo);
    totalRecords += result.records;

    if (result.targetSales > 0) {
      totalTargetSales += result.targetSales;
      countiesWithTarget.push(fileInfo.county);
    }
  }

  // Final verification
  console.log('\n========================================');
  console.log('IMPORT SUMMARY');
  console.log('========================================');
  console.log(`Files processed: ${sdfFiles.length}`);
  console.log(`Total sales imported: ${totalRecords.toLocaleString()}`);

  if (totalTargetSales > 0) {
    console.log(`\n🎯 TARGET PROPERTY FOUND!`);
    console.log(`Property ${TARGET_PROPERTY} found in: ${countiesWithTarget.join(', ')}`);
    console.log(`Total sales for target property: ${totalTargetSales}`);

    // Query the database to verify
    console.log('\nVerifying database...');
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
      console.log(`\n✅ SUCCESS! Property ${TARGET_PROPERTY} now has ${verifyData.length} recent sales:`);
      verifyData.forEach(sale => {
        const date = sale.sale_date || `${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}`;
        console.log(`   ${date}: $${sale.sale_price.toLocaleString()} (${sale.quality_code}) - ${sale.county_name}`);
      });

      console.log('\n🌐 Check the property page:');
      console.log('   http://localhost:5173/property/514124070600');
    } else {
      console.log(`\n⚠️ No sales found in database for property ${TARGET_PROPERTY}`);
    }
  } else {
    console.log(`\n⚠️ Property ${TARGET_PROPERTY} not found in any county`);
  }

  console.log('\n========================================');
  console.log('Import complete!');
  console.log('========================================');
}

// Run the import
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});