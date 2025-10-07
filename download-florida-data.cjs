const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'https://floridarevenue.com/property/dataportal/DataPortal_Files/2025/';
const OUTPUT_BASE = 'C:\\TEMP\\DATABASE PROPERTY APP';
const YEAR = '2025';

// Priority counties to download
const COUNTIES = [
  { code: '06', name: 'BROWARD' },        // Property 514124070600 location
  { code: '13', name: 'MIAMI-DADE' },
  { code: '50', name: 'PALM_BEACH' },
  { code: '48', name: 'ORANGE' },
  { code: '29', name: 'HILLSBOROUGH' },
  { code: '52', name: 'PINELLAS' },
  { code: '16', name: 'DUVAL' },
  { code: '36', name: 'LEE' },
  { code: '11', name: 'COLLIER' },
  { code: '58', name: 'SARASOTA' }
];

// File types to download
const FILE_TYPES = ['NAL', 'NAP', 'NAV', 'SDF'];

// Create directory if it doesn't exist
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Download a file
function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destPath);

    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      }

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
        resolve(sizeMB);
      });
    }).on('error', (err) => {
      fs.unlink(destPath, () => {}); // Delete partial file
      reject(err);
    });
  });
}

// Main download function
async function downloadCountyData(county) {
  console.log(`\n📍 ${county.name} County (${county.code}):`);

  const countyPath = path.join(OUTPUT_BASE, county.name);
  let successCount = 0;
  let failCount = 0;

  for (const fileType of FILE_TYPES) {
    const typePath = path.join(countyPath, fileType);
    ensureDir(typePath);

    const fileName = `${county.code}_${fileType}_${YEAR}.txt`;
    const url = BASE_URL + fileName;
    const destPath = path.join(typePath, `${county.name}_${fileType}_${YEAR}.txt`);

    // Check if file already exists
    if (fs.existsSync(destPath)) {
      const sizeMB = (fs.statSync(destPath).size / 1024 / 1024).toFixed(2);
      console.log(`  ${fileType}: Already exists (${sizeMB} MB)`);
      successCount++;
      continue;
    }

    console.log(`  ${fileType}: Downloading...`);

    try {
      await downloadFile(url, destPath);
      successCount++;

      // Special note for SDF files
      if (fileType === 'SDF') {
        console.log(`    ✅ Sales data downloaded successfully!`);
      }
    } catch (error) {
      console.log(`    ❌ Failed: ${error.message}`);
      failCount++;
    }
  }

  return { successCount, failCount };
}

// Main execution
async function main() {
  console.log('========================================');
  console.log('FLORIDA PROPERTY DATA DOWNLOADER');
  console.log('========================================');
  console.log(`Output: ${OUTPUT_BASE}`);
  console.log(`Counties: ${COUNTIES.length}`);
  console.log(`File types: ${FILE_TYPES.join(', ')}`);
  console.log('========================================');

  // Ensure base directory exists
  ensureDir(OUTPUT_BASE);

  let totalSuccess = 0;
  let totalFail = 0;

  // Download each county
  for (const county of COUNTIES) {
    const result = await downloadCountyData(county);
    totalSuccess += result.successCount;
    totalFail += result.failCount;
  }

  // Summary
  console.log('\n========================================');
  console.log('DOWNLOAD SUMMARY');
  console.log('========================================');
  console.log(`✅ Successfully downloaded: ${totalSuccess} files`);
  console.log(`❌ Failed: ${totalFail} files`);

  // Check for Broward specifically
  const browardSDF = path.join(OUTPUT_BASE, 'BROWARD', 'SDF', 'BROWARD_SDF_2025.txt');
  if (fs.existsSync(browardSDF)) {
    console.log('\n✅ BROWARD COUNTY SALES DATA AVAILABLE!');
    console.log('Property 514124070600 sales history can now be imported.');
  } else {
    console.log('\n⚠️  Broward County sales data not found.');
    console.log('You may need to download it manually from:');
    console.log('https://floridarevenue.com/property/dataportal/DataPortal_Files/2025/06_SDF_2025.txt');
  }

  console.log('\n✨ Process complete!');
  console.log('Next step: Run import script to load data into Supabase');
}

// Run the download
console.log('Starting download process...\n');
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});