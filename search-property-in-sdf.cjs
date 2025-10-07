const fs = require('fs');
const path = require('path');

// Base path to SDF files
const SDF_BASE_PATH = 'C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE PROPERTY APP';

// Property we're looking for
const TARGET_PROPERTY = '514124070600';

// Find all SDF files and search for the property
async function searchForProperty() {
  console.log('========================================');
  console.log('SEARCHING FOR PROPERTY IN SDF FILES');
  console.log('========================================');
  console.log(`Target Property: ${TARGET_PROPERTY}`);
  console.log('');

  // Find all SDF directories
  const counties = fs.readdirSync(SDF_BASE_PATH, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);

  let foundInCounties = [];
  let totalFilesSearched = 0;

  for (const county of counties) {
    const sdfDir = path.join(SDF_BASE_PATH, county, 'SDF');

    if (!fs.existsSync(sdfDir)) {
      continue;
    }

    const files = fs.readdirSync(sdfDir)
      .filter(file => file.toLowerCase().includes('sdf') && file.toLowerCase().endsWith('.csv'));

    for (const file of files) {
      const filePath = path.join(sdfDir, file);
      totalFilesSearched++;

      console.log(`Searching ${county}/${file}...`);

      try {
        // Read file and search for the property ID
        const content = fs.readFileSync(filePath, 'utf8');

        if (content.includes(TARGET_PROPERTY)) {
          foundInCounties.push({
            county: county,
            file: file,
            filePath: filePath
          });

          console.log(`  ✅ FOUND! Property ${TARGET_PROPERTY} exists in ${county}`);

          // Extract the specific lines
          const lines = content.split('\n');
          const matchingLines = lines.filter(line => line.includes(TARGET_PROPERTY));

          console.log(`  Found ${matchingLines.length} sales records:`);
          matchingLines.slice(0, 3).forEach((line, index) => {
            const fields = line.split(',');
            if (fields.length > 18) {
              const saleYear = fields[16]?.replace(/"/g, '');
              const saleMonth = fields[17]?.replace(/"/g, '');
              const salePrice = fields[18]?.replace(/"/g, '');
              console.log(`    ${index + 1}. ${saleYear}-${saleMonth}: $${salePrice}`);
            }
          });
        }
      } catch (error) {
        console.log(`  Error reading ${file}: ${error.message}`);
      }
    }
  }

  console.log('\n========================================');
  console.log('SEARCH RESULTS');
  console.log('========================================');
  console.log(`Files searched: ${totalFilesSearched}`);
  console.log(`Counties searched: ${counties.length}`);

  if (foundInCounties.length > 0) {
    console.log(`\n🎯 SUCCESS! Property ${TARGET_PROPERTY} found in ${foundInCounties.length} counties:`);
    foundInCounties.forEach(result => {
      console.log(`  - ${result.county}: ${result.file}`);
    });

    // Return the first match for import
    return foundInCounties[0];
  } else {
    console.log(`\n❌ Property ${TARGET_PROPERTY} not found in any SDF files`);

    // Let's also try searching without quotes
    console.log('\nTrying alternate search patterns...');

    for (const county of ['BROWARD', 'MIAMI-DADE', 'PALM BEACH'].slice(0, 3)) {
      const sdfDir = path.join(SDF_BASE_PATH, county, 'SDF');

      if (fs.existsSync(sdfDir)) {
        const files = fs.readdirSync(sdfDir);
        for (const file of files) {
          if (file.includes('SDF')) {
            const filePath = path.join(sdfDir, file);
            console.log(`\nChecking ${county}/${file} for similar properties...`);

            try {
              const content = fs.readFileSync(filePath, 'utf8');
              const lines = content.split('\n');

              // Look for properties starting with 5141
              const similarProperties = lines.filter(line => line.includes('5141')).slice(0, 5);

              if (similarProperties.length > 0) {
                console.log(`Found ${similarProperties.length} properties starting with '5141':`);
                similarProperties.forEach(line => {
                  const parcelMatch = line.match(/"(\d{15})"/);
                  if (parcelMatch) {
                    console.log(`  - ${parcelMatch[1]}`);
                  }
                });
              }
            } catch (error) {
              console.log(`Error: ${error.message}`);
            }
          }
        }
      }
    }

    return null;
  }
}

// Main execution
searchForProperty().then(result => {
  if (result) {
    console.log(`\n📁 Ready to import from: ${result.county}/${result.file}`);
    console.log('Next step: Run focused import script');
  } else {
    console.log('\nNo property found. Check if the parcel ID format is correct.');
  }
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});