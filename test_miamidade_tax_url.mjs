// Test Miami-Dade Tax Collector URL formatting

function formatMiamiDadeParcelId(parcelId) {
  // Convert 3040190012860 to 30-4019-001-2860
  const cleaned = parcelId.replace(/[^0-9]/g, '');
  if (cleaned.length === 13) {
    return `${cleaned.slice(0, 2)}-${cleaned.slice(2, 6)}-${cleaned.slice(6, 9)}-${cleaned.slice(9)}`;
  }
  return parcelId;
}

function getTaxCollectorUrl(county, parcelId) {
  const countyUpper = county?.toUpperCase().trim();

  // Format parcel ID based on county requirements
  let formattedParcelId = parcelId;

  // Miami-Dade requires hyphenated format: 30-4019-001-2860
  if (countyUpper === 'MIAMI-DADE' && parcelId) {
    formattedParcelId = formatMiamiDadeParcelId(parcelId);
  }

  if (countyUpper === 'MIAMI-DADE') {
    return `https://miamidade.county-taxes.com/public/real_estate/parcels/${formattedParcelId}`;
  }

  return `https://${county.toLowerCase()}.county-taxes.com/public/real_estate/parcels/${parcelId}`;
}

console.log('=' .repeat(80));
console.log('MIAMI-DADE TAX COLLECTOR URL TEST');
console.log('=' .repeat(80));
console.log();

const testParcels = [
  '3040190012860',
  '30-4019-001-2860',
  '3040190012860',
  '01-4108-001-0010',
  '0141080010010'
];

console.log('Testing parcel ID formatting:');
console.log('-'.repeat(60));

testParcels.forEach(parcel => {
  const formatted = formatMiamiDadeParcelId(parcel);
  console.log(`Input:  ${parcel}`);
  console.log(`Output: ${formatted}`);
  console.log();
});

console.log('=' .repeat(80));
console.log('GENERATED TAX COLLECTOR URLs:');
console.log('=' .repeat(80));
console.log();

const miamiDadeParcel = '3040190012860';
const url = getTaxCollectorUrl('MIAMI-DADE', miamiDadeParcel);

console.log('Property: 3040190012860');
console.log('County: Miami-Dade');
console.log();
console.log('Generated URL:');
console.log(`  ${url}`);
console.log();

const expectedUrl = 'https://miamidade.county-taxes.com/public/real_estate/parcels/30-4019-001-2860';

if (url === expectedUrl) {
  console.log('[SUCCESS] Miami-Dade Tax Collector URL is correctly formatted with hyphens!');
} else {
  console.log('[ERROR] URL format mismatch:');
  console.log(`  Expected: ${expectedUrl}`);
  console.log(`  Got: ${url}`);
}

console.log();
console.log('The correct Miami-Dade Tax Collector URL format is:');
console.log('https://miamidade.county-taxes.com/public/real_estate/parcels/30-4019-001-2860');
console.log();
console.log('Note: Miami-Dade uses hyphenated format (30-4019-001-2860) not plain format (3040190012860)');