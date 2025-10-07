/**
 * Debug script to test URL generation
 */

// Test the correct URL pattern
const county = 'BROWARD';
const countyCode = '16';
const fileType = 'SDF';

const baseUrl = `https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/${fileType}/2025P`;

// Convert county name to proper format for URLs
let countyName = county;
if (county === 'MIAMI-DADE') countyName = 'Miami-Dade';
else if (county === 'ST. JOHNS') countyName = 'St.%20Johns';
else if (county === 'ST. LUCIE') countyName = 'St.%20Lucie';
else if (county === 'SANTA ROSA') countyName = 'Santa%20Rosa';
else if (county === 'INDIAN RIVER') countyName = 'Indian%20River';
else {
  // Convert to proper case for other counties
  countyName = county.charAt(0).toUpperCase() + county.slice(1).toLowerCase();
}

// URL encode spaces as %20
const encodedCountyName = countyName.replace(/ /g, '%20');

// Correct Florida DOR filename pattern
const filename = `${encodedCountyName}%20${countyCode}%20Preliminary%20${fileType}%202025.zip`;

const url = `${baseUrl}/${filename}`;

console.log('=== URL Generation Test ===');
console.log(`County: ${county}`);
console.log(`County Code: ${countyCode}`);
console.log(`County Name: ${countyName}`);
console.log(`Encoded: ${encodedCountyName}`);
console.log(`Filename: ${filename}`);
console.log(`Full URL: ${url}`);
console.log('===========================');

// Test the download with curl
const https = require('https');

console.log('\nTesting download...');

https.get(url, (response) => {
  console.log(`Status: ${response.statusCode}`);
  console.log(`Content-Type: ${response.headers['content-type']}`);
  console.log(`Content-Length: ${response.headers['content-length']}`);

  if (response.statusCode === 200) {
    console.log('✅ SUCCESS: File exists and can be downloaded!');
  } else {
    console.log('❌ FAILED: File not found or error occurred');
  }
}).on('error', (err) => {
  console.error('❌ ERROR:', err.message);
});