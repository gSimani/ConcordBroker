const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const https = require('https');
const AdmZip = require('adm-zip');

// Base configuration
const BASE_URL = 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P';
const OUTPUT_BASE = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP';
const DOWNLOADS_FOLDER = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DOWNLOADS';

// All Florida counties
const ALL_COUNTIES = [
  'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN', 'CHARLOTTE',
  'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DADE', 'DESOTO', 'DIXIE', 'DUVAL',
  'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON',
  'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER', 'JACKSON',
  'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON',
  'MANATEE', 'MARION', 'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE',
  'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA',
  'SARASOTA', 'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION',
  'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
];

// Ensure directory exists
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Check which counties already have SDF data
function checkExistingSDF() {
  const existing = [];
  const missing = [];

  for (const county of ALL_COUNTIES) {
    const countyPath = path.join(OUTPUT_BASE, county, 'SDF');

    if (fs.existsSync(countyPath)) {
      const files = fs.readdirSync(countyPath);
      if (files.length > 0) {
        existing.push(county);
      } else {
        missing.push(county);
      }
    } else {
      missing.push(county);
    }
  }

  return { existing, missing };
}

// Extract zip file
async function extractZip(zipPath, extractTo) {
  console.log(`  Extracting ${path.basename(zipPath)}...`);

  try {
    const zip = new AdmZip(zipPath);
    zip.extractAllTo(extractTo, true);
    console.log(`  Extraction complete`);
    return true;
  } catch (error) {
    console.error(`  Failed to extract: ${error.message}`);
    return false;
  }
}

// Main function
async function main() {
  console.log('========================================');
  console.log('FLORIDA SDF DATA DOWNLOADER (PLAYWRIGHT)');
  console.log('========================================');

  // Check existing data
  const { existing, missing } = checkExistingSDF();

  console.log(`\nExisting counties with SDF data: ${existing.length}`);
  console.log(`Missing counties: ${missing.length}`);

  if (missing.length === 0) {
    console.log('\nAll counties already have SDF data!');
    return;
  }

  console.log('\nMissing counties:');
  missing.forEach(county => console.log(`  - ${county}`));

  // Ensure downloads folder exists
  ensureDir(DOWNLOADS_FOLDER);

  // Launch browser
  console.log('\nLaunching browser...');
  const browser = await chromium.launch({
    headless: false, // Show browser for visual feedback
    downloadsPath: DOWNLOADS_FOLDER
  });

  const context = await browser.newContext({
    acceptDownloads: true
  });

  const page = await context.newPage();

  try {
    // Navigate to the SDF 2025P folder
    console.log(`\nNavigating to: ${BASE_URL}`);
    await page.goto(BASE_URL, {
      waitUntil: 'networkidle',
      timeout: 60000
    });

    // Wait for the page to load
    await page.waitForTimeout(3000);

    // Look for SDF zip file links
    console.log('\nSearching for SDF zip files...');

    // Find all links that contain "SDF" and ".zip"
    const links = await page.$$eval('a[href*=".zip"]', elements =>
      elements
        .filter(el => el.textContent.includes('SDF'))
        .map(el => ({
          text: el.textContent.trim(),
          href: el.href
        }))
    );

    console.log(`Found ${links.length} SDF zip files`);

    // Download missing counties
    for (const link of links) {
      // Extract county name from link text
      const countyMatch = link.text.match(/^([A-Za-z\s\.\-]+)\s+\d+/);
      if (!countyMatch) continue;

      const countyName = countyMatch[1].trim().toUpperCase();

      // Check if this county is in our missing list
      if (!missing.includes(countyName)) {
        console.log(`Skipping ${countyName} (already exists)`);
        continue;
      }

      console.log(`\nDownloading ${countyName}...`);
      console.log(`  File: ${link.text}`);

      // Click the link to download
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        page.click(`a[href="${link.href}"]`)
      ]);

      // Wait for download to complete
      const downloadPath = await download.path();
      console.log(`  Downloaded to: ${downloadPath}`);

      // Extract the zip file
      const countyPath = path.join(OUTPUT_BASE, countyName, 'SDF');
      ensureDir(countyPath);

      await extractZip(downloadPath, countyPath);

      // Small delay between downloads
      await page.waitForTimeout(2000);
    }

    console.log('\n✅ Download complete!');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  } finally {
    // Close browser
    console.log('\nClosing browser...');
    await browser.close();
  }

  // Final check
  const finalCheck = checkExistingSDF();
  console.log('\n========================================');
  console.log('FINAL STATUS');
  console.log('========================================');
  console.log(`Counties with SDF data: ${finalCheck.existing.length}/67`);

  if (finalCheck.missing.length > 0) {
    console.log('\nStill missing:');
    finalCheck.missing.forEach(county => console.log(`  - ${county}`));
  } else {
    console.log('\n✅ All counties now have SDF data!');
  }
}

// Check for required packages
async function checkDependencies() {
  try {
    require('playwright');
    require('adm-zip');
  } catch (e) {
    console.log('Installing required packages...');
    require('child_process').execSync('npm install playwright adm-zip', { stdio: 'inherit' });
    console.log('Packages installed. Please run the script again.');
    process.exit(0);
  }
}

// Run the script
checkDependencies().then(() => {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
});