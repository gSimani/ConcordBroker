const https = require('https');
const fs = require('fs');
const path = require('path');
const unzipper = require('unzipper');
const { createClient } = require('@supabase/supabase-js');
const csv = require('csv-parser');
require('dotenv').config({ path: '.env.mcp' });

// Supabase configuration
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Base configuration
const BASE_URL = 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/';
const OUTPUT_BASE = 'C:\\TEMP\\FLORIDA_SDF_DATA';
const EXTRACTED_BASE = 'C:\\TEMP\\FLORIDA_SDF_EXTRACTED';

// Priority counties to download (with correct names from URL)
const COUNTIES = [
  { code: '06', name: 'Broward' },        // Property 514124070600 location - PRIORITY
  { code: '13', name: 'Miami-Dade' },
  { code: '50', name: 'Palm Beach' },
  { code: '48', name: 'Orange' },
  { code: '29', name: 'Hillsborough' },
  { code: '52', name: 'Pinellas' },
  { code: '16', name: 'Duval' },
  { code: '36', name: 'Lee' },
  { code: '11', name: 'Collier' },
  { code: '58', name: 'Sarasota' },
  { code: '19', name: 'Citrus' }  // This one has final data
];

// Create directory if it doesn't exist
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Download a file
function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    console.log(`    Downloading from: ${url}`);

    const file = fs.createWriteStream(destPath);

    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        // Handle redirect
        const redirectUrl = response.headers.location;
        console.log(`    Redirected to: ${redirectUrl}`);
        https.get(redirectUrl, (redirectResponse) => {
          if (redirectResponse.statusCode !== 200) {
            reject(new Error(`Failed to download: ${redirectResponse.statusCode}`));
            return;
          }
          handleResponse(redirectResponse);
        }).on('error', reject);
      } else if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      } else {
        handleResponse(response);
      }
    }).on('error', reject);

    function handleResponse(response) {
      let downloaded = 0;
      const totalSize = parseInt(response.headers['content-length'] || '0', 10);

      response.on('data', (chunk) => {
        downloaded += chunk.length;
        if (totalSize > 0) {
          const percent = ((downloaded / totalSize) * 100).toFixed(1);
          process.stdout.write(`\r    Progress: ${percent}% (${(downloaded / 1024 / 1024).toFixed(2)} MB)`);
        }
      });

      response.pipe(file);

      file.on('finish', () => {
        file.close();
        const sizeMB = (fs.statSync(destPath).size / 1024 / 1024).toFixed(2);
        console.log(` - Complete (${sizeMB} MB)`);
        resolve(destPath);
      });

      file.on('error', (err) => {
        fs.unlink(destPath, () => {});
        reject(err);
      });
    }
  });
}

// Extract zip file
async function extractZip(zipPath, extractTo) {
  console.log(`    Extracting ${path.basename(zipPath)}...`);

  return new Promise((resolve, reject) => {
    fs.createReadStream(zipPath)
      .pipe(unzipper.Extract({ path: extractTo }))
      .on('close', () => {
        console.log(`    Extraction complete`);
        resolve(extractTo);
      })
      .on('error', reject);
  });
}

// Parse and import SDF data to Supabase
async function importSdfToSupabase(filePath, countyCode, countyName) {
  console.log(`    Importing ${countyName} SDF data to Supabase...`);

  const records = [];
  const batchSize = 1000;
  let totalImported = 0;

  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv({
        separator: '\t',  // SDF files are tab-delimited
        headers: false    // No headers in SDF files
      }))
      .on('data', (row) => {
        // SDF file structure (positions are fixed width)
        // We'll parse the essential fields for sales history
        const record = {
          county_no: countyCode,
          parcel_id: (row[0] || '').trim(),
          sale_year: parseInt(row[1]) || null,
          sale_month: parseInt(row[2]) || null,
          sale_day: parseInt(row[3]) || null,
          sale_price: parseFloat(row[4]) || 0,
          or_book: (row[5] || '').trim(),
          or_page: (row[6] || '').trim(),
          qual_cd: (row[7] || '').trim(),
          vi_cd: (row[8] || '').trim()
        };

        // Only include sales with valid data
        if (record.parcel_id && record.sale_year && record.sale_price > 0) {
          records.push(record);
        }

        // Batch insert when we reach batch size
        if (records.length >= batchSize) {
          const batch = [...records];
          records.length = 0;

          supabase
            .from('fl_sdf')
            .upsert(batch, { onConflict: 'parcel_id,county_no,sale_year,sale_month' })
            .then(({ error }) => {
              if (!error) {
                totalImported += batch.length;
                process.stdout.write(`\r    Imported: ${totalImported} records`);
              } else {
                console.error(`    Error importing batch: ${error.message}`);
              }
            });
        }
      })
      .on('end', async () => {
        // Import remaining records
        if (records.length > 0) {
          const { error } = await supabase
            .from('fl_sdf')
            .upsert(records, { onConflict: 'parcel_id,county_no,sale_year,sale_month' });

          if (!error) {
            totalImported += records.length;
          } else {
            console.error(`    Error importing final batch: ${error.message}`);
          }
        }

        console.log(`\n    Total imported: ${totalImported} records`);
        resolve(totalImported);
      })
      .on('error', reject);
  });
}

// Process a county
async function processCounty(county) {
  console.log(`\nProcessing ${county.name} County (${county.code}):`);

  ensureDir(OUTPUT_BASE);
  ensureDir(EXTRACTED_BASE);

  const countyExtractPath = path.join(EXTRACTED_BASE, county.name);
  ensureDir(countyExtractPath);

  try {
    // Try 2025F (Final) first
    let url = `${BASE_URL}2025F/${encodeURIComponent(county.name)}%20${county.code}%20Final%20SDF%202025.zip`;
    let zipPath = path.join(OUTPUT_BASE, `${county.name}_${county.code}_Final_SDF_2025.zip`);

    // Check if already downloaded
    if (fs.existsSync(zipPath)) {
      console.log(`  Zip already exists: ${path.basename(zipPath)}`);
    } else {
      try {
        console.log(`  Trying Final (2025F) data...`);
        await downloadFile(url, zipPath);
      } catch (error) {
        // If final doesn't exist, try preliminary
        console.log(`  Final not available, trying Preliminary (2025P)...`);
        url = `${BASE_URL}2025P/${encodeURIComponent(county.name)}%20${county.code}%20Preliminary%20SDF%202025.zip`;
        zipPath = path.join(OUTPUT_BASE, `${county.name}_${county.code}_Preliminary_SDF_2025.zip`);

        if (fs.existsSync(zipPath)) {
          console.log(`  Zip already exists: ${path.basename(zipPath)}`);
        } else {
          await downloadFile(url, zipPath);
        }
      }
    }

    // Extract the zip
    await extractZip(zipPath, countyExtractPath);

    // Find the SDF file in extracted content
    const files = fs.readdirSync(countyExtractPath);
    const sdfFile = files.find(f => f.includes('SDF') && (f.endsWith('.txt') || f.endsWith('.csv')));

    if (sdfFile) {
      const sdfPath = path.join(countyExtractPath, sdfFile);
      console.log(`  Found SDF file: ${sdfFile}`);

      // Import to Supabase
      const imported = await importSdfToSupabase(sdfPath, county.code, county.name);

      return { success: true, imported };
    } else {
      console.log(`  No SDF file found in extracted content`);
      return { success: false, error: 'No SDF file found' };
    }

  } catch (error) {
    console.log(`  Error: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// Check for specific property
async function checkPropertySales(parcelId) {
  console.log(`\nChecking sales for property ${parcelId}...`);

  const { data, error } = await supabase
    .from('fl_sdf')
    .select('*')
    .eq('parcel_id', parcelId)
    .order('sale_year', { ascending: false })
    .order('sale_month', { ascending: false });

  if (error) {
    console.log(`  Error: ${error.message}`);
  } else if (data && data.length > 0) {
    console.log(`  Found ${data.length} sales:`);
    data.slice(0, 5).forEach(sale => {
      console.log(`    ${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}: $${sale.sale_price.toLocaleString()}`);
    });
  } else {
    console.log(`  No sales found`);
  }
}

// Main execution
async function main() {
  console.log('========================================');
  console.log('FLORIDA SDF DATA DOWNLOADER & IMPORTER');
  console.log('========================================');
  console.log(`Output: ${OUTPUT_BASE}`);
  console.log(`Counties: ${COUNTIES.length}`);
  console.log('========================================');

  // Check for required packages
  try {
    require('unzipper');
    require('@supabase/supabase-js');
    require('csv-parser');
  } catch (e) {
    console.log('\nInstalling required packages...');
    require('child_process').execSync('npm install unzipper @supabase/supabase-js csv-parser dotenv', { stdio: 'inherit' });
    console.log('Packages installed. Please run the script again.');
    process.exit(0);
  }

  let totalSuccess = 0;
  let totalFail = 0;
  let totalImported = 0;

  // Process Broward first (priority for property 514124070600)
  const broward = COUNTIES.find(c => c.code === '06');
  if (broward) {
    console.log('\nPRIORITY: Processing Broward County first...');
    const result = await processCounty(broward);
    if (result.success) {
      totalSuccess++;
      totalImported += result.imported || 0;

      // Check for our specific property
      await checkPropertySales('514124070600');
    } else {
      totalFail++;
    }
  }

  // Process remaining counties
  for (const county of COUNTIES.filter(c => c.code !== '06')) {
    const result = await processCounty(county);
    if (result.success) {
      totalSuccess++;
      totalImported += result.imported || 0;
    } else {
      totalFail++;
    }
  }

  // Summary
  console.log('\n========================================');
  console.log('IMPORT SUMMARY');
  console.log('========================================');
  console.log(`Counties processed: ${totalSuccess}/${COUNTIES.length}`);
  console.log(`Total records imported: ${totalImported}`);
  console.log(`Failed: ${totalFail}`);

  // Final check for property 514124070600
  console.log('\nFinal check for property 514124070600:');
  await checkPropertySales('514124070600');

  console.log('\n✨ Process complete!');
}

// Run the script
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});