// Test DOR Use Codes Frontend Integration
import { getDORUseCode } from './apps/web/src/utils/dorUseCodes.js';

console.log('Testing DOR Use Codes Frontend Integration\n');
console.log('=' .repeat(50));

// Test codes covering all categories
const testCodes = [
  '000', // Vacant
  '001', // Residential - Single Family
  '002', // Residential - Mobile Homes
  '010', // Commercial - Vacant
  '017', // Office Buildings
  '021', // Restaurant
  '039', // Hotel/Motel
  '040', // Industrial - Vacant
  '050', // Industrial - Improved
  '066', // Orchard Groves
  '071', // Churches
  '083', // Public Schools
  '091', // Utility
  '098', // Centrally Assessed
  '099'  // Acreage Not Zoned Agricultural
];

let passedTests = 0;
let failedTests = 0;

testCodes.forEach(code => {
  const result = getDORUseCode(code);

  if (result) {
    console.log(`✓ Code ${code}: ${result.category} - ${result.description}`);
    passedTests++;
  } else {
    console.log(`✗ Code ${code}: FAILED - No result returned`);
    failedTests++;
  }
});

console.log('\n' + '=' .repeat(50));
console.log(`Test Results: ${passedTests} passed, ${failedTests} failed`);

if (failedTests === 0) {
  console.log('✅ All DOR codes are working correctly!');
} else {
  console.log('❌ Some DOR codes failed. Check the implementation.');
}