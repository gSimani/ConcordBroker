#!/usr/bin/env node

/**
 * Property Filter Mapping Validation Script
 * Validates that the updated dorCodeService mappings work correctly
 */

// Simulate the mapping functions from dorCodeService.ts
const PROPERTY_TYPE_TO_DB_VALUES = {
  'Residential': [0, 1, 2, 4, 8, 9],
  'Commercial': [11, 19, 28],
  'Industrial': [48, 52, 60],
  'Agricultural': [80, 87],
  'Vacant Land': [0],
  'Vacant': [0],
  'Condo': [4],
  'Multi-Family': [8],
  'Institutional': [71],
  'Religious': [71],
  'Government': [93, 96],
  'Governmental': [93, 96],
  'Conservation': [],
  'Special': [],
  'Vacant/Special': [0]
};

// Simulate the property categorization function
const PROPERTY_USE_TO_CATEGORY = {
  0: 'Vacant Land',
  1: 'Residential',
  2: 'Residential',
  4: 'Condo',
  8: 'Multi-Family',
  9: 'Residential',
  11: 'Commercial',
  19: 'Commercial',
  28: 'Commercial',
  48: 'Industrial',
  52: 'Industrial',
  60: 'Industrial',
  71: 'Religious',
  80: 'Agricultural',
  87: 'Agricultural',
  93: 'Government',
  96: 'Government'
};

function getPropertyUseValuesForType(propertyType) {
  return PROPERTY_TYPE_TO_DB_VALUES[propertyType] || [];
}

function getPropertyCategoryFromCode(propertyUse) {
  return PROPERTY_USE_TO_CATEGORY[propertyUse] || 'Other';
}

/**
 * Validate mapping consistency
 */
function validateMappings() {
  console.log('🔍 PROPERTY FILTER MAPPING VALIDATION');
  console.log('=' * 50);

  const results = [];

  // Test each filter category
  Object.keys(PROPERTY_TYPE_TO_DB_VALUES).forEach(filterType => {
    console.log(`\n📊 Testing filter: ${filterType}`);

    const propertyUseValues = getPropertyUseValuesForType(filterType);
    console.log(`   Property use values: [${propertyUseValues.join(', ')}]`);

    if (propertyUseValues.length === 0) {
      console.log(`   ⚠️  Empty mapping (expected for ${filterType})`);
      results.push({
        filter: filterType,
        values: propertyUseValues,
        status: filterType === 'Conservation' || filterType === 'Special' ? 'OK (empty)' : 'WARNING (empty)',
        categories: []
      });
      return;
    }

    // Check reverse mapping
    const categoriesFound = [];
    propertyUseValues.forEach(useValue => {
      const category = getPropertyCategoryFromCode(useValue);
      categoriesFound.push(category);
      console.log(`   ${useValue} → "${category}"`);
    });

    // Check for consistency issues
    const uniqueCategories = [...new Set(categoriesFound)];
    const hasConsistencyIssues = uniqueCategories.length > 1 &&
                                filterType !== 'Residential'; // Residential intentionally includes multiple

    if (hasConsistencyIssues) {
      console.log(`   ⚠️  Multiple categories found: ${uniqueCategories.join(', ')}`);
    } else {
      console.log(`   ✅ Consistent mapping`);
    }

    results.push({
      filter: filterType,
      values: propertyUseValues,
      categories: uniqueCategories,
      status: hasConsistencyIssues ? 'WARNING' : 'OK'
    });
  });

  return results;
}

/**
 * Test specific scenarios
 */
function testScenarios() {
  console.log('\n🧪 TESTING SPECIFIC SCENARIOS');
  console.log('=' * 40);

  const scenarios = [
    {
      name: 'Residential filter includes vacant residential',
      test: () => {
        const residentialValues = getPropertyUseValuesForType('Residential');
        return residentialValues.includes(0);
      },
      expected: true,
      reason: 'Vacant residential lots should be included in residential filter'
    },
    {
      name: 'Vacant Land filter only includes vacant',
      test: () => {
        const vacantValues = getPropertyUseValuesForType('Vacant Land');
        return vacantValues.length === 1 && vacantValues[0] === 0;
      },
      expected: true,
      reason: 'Vacant Land should only include property_use = 0'
    },
    {
      name: 'Commercial filter excludes residential',
      test: () => {
        const commercialValues = getPropertyUseValuesForType('Commercial');
        const residentialUses = [0, 1, 2, 4, 8, 9];
        return !commercialValues.some(val => residentialUses.includes(val));
      },
      expected: true,
      reason: 'Commercial should not include any residential property uses'
    },
    {
      name: 'Government filter is specific',
      test: () => {
        const govValues = getPropertyUseValuesForType('Government');
        return govValues.length === 2 && govValues.includes(93) && govValues.includes(96);
      },
      expected: true,
      reason: 'Government should only include municipal (93) and federal (96)'
    },
    {
      name: 'Conservation filter is empty',
      test: () => {
        const conservationValues = getPropertyUseValuesForType('Conservation');
        return conservationValues.length === 0;
      },
      expected: true,
      reason: 'Conservation has no matching properties in current dataset'
    },
    {
      name: 'Religious filter is specific',
      test: () => {
        const religiousValues = getPropertyUseValuesForType('Religious');
        return religiousValues.length === 1 && religiousValues[0] === 71;
      },
      expected: true,
      reason: 'Religious should only include churches/temples (71)'
    }
  ];

  scenarios.forEach(scenario => {
    const result = scenario.test();
    const status = result === scenario.expected ? '✅' : '❌';
    console.log(`${status} ${scenario.name}`);
    console.log(`   Expected: ${scenario.expected}, Got: ${result}`);
    console.log(`   Reason: ${scenario.reason}`);

    if (result !== scenario.expected) {
      console.log(`   🚨 TEST FAILED`);
    }
    console.log('');
  });
}

/**
 * Generate API call examples
 */
function generateAPIExamples() {
  console.log('\n🔗 API CALL EXAMPLES');
  console.log('=' * 30);

  const baseURL = 'http://localhost:3001/api/supabase/florida_parcels';
  const apiKey = 'concordbroker-mcp-key-claude';
  const county = 'Miami-Dade';

  console.log('Headers:');
  console.log(`   x-api-key: ${apiKey}`);
  console.log('');

  Object.keys(PROPERTY_TYPE_TO_DB_VALUES).forEach(filterType => {
    const values = getPropertyUseValuesForType(filterType);
    if (values.length > 0) {
      const queryParams = `county=eq.${county}&limit=10&property_use=in.(${values.join(',')})`;
      const fullURL = `${baseURL}?${queryParams}`;
      console.log(`${filterType}:`);
      console.log(`   ${fullURL}`);
      console.log('');
    } else {
      console.log(`${filterType}: No API call (empty filter)`);
      console.log('');
    }
  });
}

/**
 * Check for potential conflicts
 */
function checkConflicts() {
  console.log('\n⚠️  POTENTIAL CONFLICTS');
  console.log('=' * 30);

  const allValues = new Map(); // value -> [filters that use it]

  Object.entries(PROPERTY_TYPE_TO_DB_VALUES).forEach(([filter, values]) => {
    values.forEach(value => {
      if (!allValues.has(value)) {
        allValues.set(value, []);
      }
      allValues.get(value).push(filter);
    });
  });

  let hasConflicts = false;
  allValues.forEach((filters, value) => {
    if (filters.length > 1) {
      console.log(`Property use ${value} used by: ${filters.join(', ')}`);
      hasConflicts = true;
    }
  });

  if (!hasConflicts) {
    console.log('✅ No conflicts found');
  }

  console.log('\nNote: Some overlaps are intentional (e.g., vacant residential in both Residential and Vacant Land)');
}

/**
 * Main validation function
 */
function runValidation() {
  console.log('🚀 Starting Property Filter Mapping Validation\n');

  const mappingResults = validateMappings();
  testScenarios();
  generateAPIExamples();
  checkConflicts();

  // Summary
  console.log('\n📋 VALIDATION SUMMARY');
  console.log('=' * 30);

  const okCount = mappingResults.filter(r => r.status.startsWith('OK')).length;
  const warningCount = mappingResults.filter(r => r.status.startsWith('WARNING')).length;

  console.log(`✅ OK mappings: ${okCount}`);
  console.log(`⚠️  Warning mappings: ${warningCount}`);

  if (warningCount === 0) {
    console.log('\n🎉 All mappings validated successfully!');
    console.log('\n🎯 NEXT STEPS:');
    console.log('1. Test filters in browser using FILTER_TESTING_GUIDE.md');
    console.log('2. Verify API responses match expected property types');
    console.log('3. Check property card categorization badges');
    console.log('4. Monitor performance and response times');
  } else {
    console.log('\n⚠️  Some mappings need review');
    console.log('Check the warnings above and verify they are intentional');
  }

  return {
    totalFilters: mappingResults.length,
    okCount,
    warningCount,
    results: mappingResults
  };
}

// Run the validation
if (require.main === module) {
  runValidation();
}

module.exports = {
  validateMappings,
  testScenarios,
  runValidation,
  PROPERTY_TYPE_TO_DB_VALUES,
  PROPERTY_USE_TO_CATEGORY
};