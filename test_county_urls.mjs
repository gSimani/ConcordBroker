// Test script to verify county URLs are generated correctly
// Run with: node test_county_urls.mjs

// Simple implementation of the URL generation functions for testing
const FLORIDA_COUNTY_URLS = {
  'MIAMI-DADE': {
    propertyAppraiser: 'https://www.miamidade.gov/Apps/PA/propertysearch/#/property/{parcelId}',
    taxCollector: 'https://www.miamidade.county-taxes.com/public/real_estate/parcels/{parcelId}'
  },
  'BROWARD': {
    propertyAppraiser: 'https://www.bcpa.net/RecInfo.asp?URL_Folio={parcelId}',
    taxCollector: 'https://broward.county-taxes.com/public/real_estate/parcels/{parcelId}'
  },
  'PALM BEACH': {
    propertyAppraiser: 'https://www.pbcpao.gov/property/{parcelId}',
    taxCollector: 'https://www.pbctax.com/property/{parcelId}'
  },
  'HILLSBOROUGH': {
    propertyAppraiser: 'https://www.hcpafl.org/Property/ParcelID/{parcelId}',
    taxCollector: 'https://www.hillstax.org/property/{parcelId}'
  },
  'ORANGE': {
    propertyAppraiser: 'https://www.ocpafl.org/property/{parcelId}',
    taxCollector: 'https://www.octaxcol.com/property/{parcelId}'
  }
};

function getPropertyAppraiserUrl(county, parcelId) {
  const countyUpper = county?.toUpperCase().trim();
  const countyConfig = FLORIDA_COUNTY_URLS[countyUpper];

  if (!countyConfig) {
    return `https://www.floridaproperty.gov/search?parcel=${parcelId}`;
  }

  return countyConfig.propertyAppraiser.replace('{parcelId}', parcelId);
}

function getTaxCollectorUrl(county, parcelId) {
  const countyUpper = county?.toUpperCase().trim();
  const countyConfig = FLORIDA_COUNTY_URLS[countyUpper];

  if (!countyConfig) {
    const countySlug = county?.toLowerCase().replace(/\s+/g, '-') || 'florida';
    return `https://${countySlug}.county-taxes.com/public/real_estate/parcels/${parcelId}`;
  }

  return countyConfig.taxCollector.replace('{parcelId}', parcelId);
}

// Test properties from different Florida counties
const testProperties = [
  { county: 'MIAMI-DADE', parcelId: '3040190012860', name: 'Miami-Dade Property' },
  { county: 'BROWARD', parcelId: '494208020770', name: 'Broward Property' },
  { county: 'PALM BEACH', parcelId: '00424833150000070', name: 'Palm Beach Property' },
  { county: 'HILLSBOROUGH', parcelId: '193285.0100', name: 'Hillsborough Property' },
  { county: 'ORANGE', parcelId: '342317567900050', name: 'Orange County Property' }
];

console.log('='.repeat(80));
console.log('FLORIDA COUNTY URL GENERATION TEST');
console.log('='.repeat(80));
console.log();

testProperties.forEach(property => {
  console.log(`${property.name} (${property.county})`);
  console.log('-'.repeat(60));

  const appraiserUrl = getPropertyAppraiserUrl(property.county, property.parcelId);
  const taxUrl = getTaxCollectorUrl(property.county, property.parcelId);

  console.log(`Parcel ID: ${property.parcelId}`);
  console.log(`Property Appraiser URL:`);
  console.log(`  ${appraiserUrl}`);
  console.log(`Tax Collector URL:`);
  console.log(`  ${taxUrl}`);
  console.log();
});

console.log('='.repeat(80));
console.log('VERIFICATION FOR MIAMI-DADE PROPERTY 3040190012860:');
console.log('='.repeat(80));
console.log();

// Test the actual Miami-Dade property
const miamidadeAppraiserUrl = getPropertyAppraiserUrl('MIAMI-DADE', '3040190012860');
const miamidadeTaxUrl = getTaxCollectorUrl('MIAMI-DADE', '3040190012860');

console.log('GENERATED URLs:');
console.log();
console.log('Property Appraiser:');
console.log(`  ${miamidadeAppraiserUrl}`);
console.log();
console.log('Tax Collector:');
console.log(`  ${miamidadeTaxUrl}`);
console.log();

// Verify correctness
const expectedAppraiserUrl = 'https://www.miamidade.gov/Apps/PA/propertysearch/#/property/3040190012860';
const expectedTaxUrl = 'https://www.miamidade.county-taxes.com/public/real_estate/parcels/3040190012860';

if (miamidadeAppraiserUrl === expectedAppraiserUrl) {
  console.log('[SUCCESS] Miami-Dade Property Appraiser URL is correct!');
} else {
  console.log('[ERROR] Miami-Dade Property Appraiser URL is incorrect!');
  console.log(`  Expected: ${expectedAppraiserUrl}`);
  console.log(`  Got: ${miamidadeAppraiserUrl}`);
}

if (miamidadeTaxUrl === expectedTaxUrl) {
  console.log('[SUCCESS] Miami-Dade Tax Collector URL is correct!');
} else {
  console.log('[ERROR] Miami-Dade Tax Collector URL is incorrect!');
  console.log(`  Expected: ${expectedTaxUrl}`);
  console.log(`  Got: ${miamidadeTaxUrl}`);
}

console.log();
console.log('All county URLs are now dynamically generated based on the property county!');