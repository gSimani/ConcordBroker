// Debug script to test PropertyService data flow
console.log('=== Debug PropertyService Data Flow ===');

// Sample data structure from PropertyService
const sampleProperty = {
  parcel_id: '064210010010',
  phy_addr1: '123 Main Street',
  phy_city: 'Fort Lauderdale',
  phy_zipcd: '33301',
  own_name: 'John Smith',
  jv: 450000,
  lnd_val: 180000,
  tot_lvg_area: 2200,
  lnd_sqfoot: 8500,
  act_yr_blt: 2005,
  dor_uc: '001',
  county: 'BROWARD'
};

console.log('Sample property:', sampleProperty);
console.log('Sample property jv field:', sampleProperty.jv);

// Test the helper function logic from MiniPropertyCard
const getAppraisedValue = (data) => {
  const value = data.jv || data.just_value || data.appraised_value || data.market_value || data.assessed_value;
  console.log('getAppraisedValue checking fields:', {
    jv: data.jv,
    just_value: data.just_value,
    appraised_value: data.appraised_value,
    market_value: data.market_value,
    assessed_value: data.assessed_value,
    final_value: value
  });
  return value;
};

const formatCurrency = (value) => {
  console.log('formatCurrency called with value:', value, 'type:', typeof value);
  console.log('formatCurrency value is falsy:', !value);
  console.log('formatCurrency value == 0:', value == 0);
  console.log('formatCurrency value === 0:', value === 0);
  console.log('formatCurrency value === undefined:', value === undefined);
  console.log('formatCurrency value === null:', value === null);

  if (!value && value !== 0) return 'N/A';
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value}`;
};

console.log('\n=== Testing getAppraisedValue ===');
const appraisedValue = getAppraisedValue(sampleProperty);
console.log('Appraised value result:', appraisedValue);

console.log('\n=== Testing formatCurrency ===');
const formattedValue = formatCurrency(appraisedValue);
console.log('Formatted value result:', formattedValue);

console.log('\n=== Expected result ===');
console.log('Should show: $450K (since 450000 >= 1000)');
console.log('Actual result:', formattedValue);

console.log('\n=== Test completed ===');