// Test script to verify county URLs are generated correctly

import { getPropertyAppraiserUrl, getTaxCollectorUrl } from './apps/web/src/utils/countyUrls.ts';

// Test properties from different Florida counties
const testProperties = [
  { county: 'MIAMI-DADE', parcelId: '3040190012860', name: 'Miami-Dade Property' },
  { county: 'BROWARD', parcelId: '494208020770', name: 'Broward Property' },
  { county: 'PALM BEACH', parcelId: '00424833150000070', name: 'Palm Beach Property' },
  { county: 'HILLSBOROUGH', parcelId: '193285.0100', name: 'Hillsborough Property' },
  { county: 'ORANGE', parcelId: '342317567900050', name: 'Orange County Property' },
  { county: 'DUVAL', parcelId: '1461080000', name: 'Duval County Property' },
  { county: 'LEE', parcelId: '10244950', name: 'Lee County Property' },
  { county: 'COLLIER', parcelId: '00061880008', name: 'Collier County Property' },
  { county: 'PINELLAS', parcelId: '182812200030000010', name: 'Pinellas County Property' }
];

console.log('=' .repeat(80));
console.log('FLORIDA COUNTY URL GENERATION TEST');
console.log('=' .repeat(80));
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

console.log('=' .repeat(80));
console.log('EXPECTED URLs FOR MIAMI-DADE PROPERTY 3040190012860:');
console.log('=' .repeat(80));
console.log();
console.log('Property Appraiser:');
console.log('  https://www.miamidade.gov/Apps/PA/propertysearch/#/property/3040190012860');
console.log();
console.log('Tax Collector:');
console.log('  https://www.miamidade.county-taxes.com/public/real_estate/parcels/3040190012860');
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
if (miamidadeAppraiserUrl.includes('miamidade.gov')) {
  console.log('[SUCCESS] Miami-Dade Property Appraiser URL is correct!');
} else {
  console.log('[ERROR] Miami-Dade Property Appraiser URL is incorrect!');
}

if (miamidadeTaxUrl.includes('miamidade.county-taxes.com')) {
  console.log('[SUCCESS] Miami-Dade Tax Collector URL is correct!');
} else {
  console.log('[ERROR] Miami-Dade Tax Collector URL is incorrect!');
}