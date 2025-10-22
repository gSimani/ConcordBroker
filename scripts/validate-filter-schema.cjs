#!/usr/bin/env node
/**
 * Database Schema Validation for Filter System
 * Verifies all assumed database columns exist in florida_parcels table
 * Part of the Filter System Fix - validates backend data requirements
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Expected columns for all 19 filters
const FILTER_COLUMN_MAPPINGS = [
  // Value filters
  { filter: 'minValue/maxValue', column: 'just_value', type: 'numeric', critical: true },

  // Size filters
  { filter: 'minSqft/maxSqft', column: 'living_area', type: 'numeric', critical: true },
  { filter: 'minLandSqft/maxLandSqft', column: 'land_sqft', type: 'numeric', critical: true },

  // Year filters
  { filter: 'minYearBuilt/maxYearBuilt', column: 'year_built', type: 'numeric', critical: true },

  // Location filters
  { filter: 'county', column: 'county', type: 'text', critical: true },
  { filter: 'city', column: 'phy_city', type: 'text', critical: true },
  { filter: 'zipCode', column: 'phy_zipcd', type: 'text', critical: true },

  // Property type filters
  { filter: 'propertyUseCode/subUsageCode', column: 'dor_uc', type: 'text', critical: true },

  // Assessment filters
  { filter: 'minAssessedValue/maxAssessedValue', column: 'taxable_value', type: 'numeric', critical: true },

  // Boolean filters (need research)
  { filter: 'taxExempt', column: 'homestead_exemption', type: 'text', critical: false },
  { filter: 'hasPool', column: 'pool_ind', type: 'text', critical: false },
  { filter: 'waterfront', column: 'waterfront_ind', type: 'text', critical: false },

  // Sales history (separate table)
  { filter: 'recentlySold', column: 'sale_date1', type: 'date', critical: false },

  // Additional useful columns
  { filter: 'display', column: 'parcel_id', type: 'text', critical: true },
  { filter: 'display', column: 'owner_name', type: 'text', critical: true },
  { filter: 'display', column: 'phy_addr1', type: 'text', critical: true },
  { filter: 'display', column: 'land_value', type: 'numeric', critical: true },
  { filter: 'display', column: 'building_value', type: 'numeric', critical: true },
  { filter: 'display', column: 'bedrooms', type: 'numeric', critical: false },
  { filter: 'display', column: 'bathrooms', type: 'numeric', critical: false },
];

async function validateDatabaseSchema() {
  console.log('🔍 Validating Database Schema for Filter System\n');
  console.log('=' .repeat(80));

  // Initialize Supabase client
  const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error('❌ ERROR: Supabase credentials not found in environment');
    console.error('   Required: NEXT_PUBLIC_SUPABASE_URL or VITE_SUPABASE_URL');
    console.error('   Required: SUPABASE_SERVICE_ROLE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY');
    process.exit(1);
  }

  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    // Query actual schema from database
    console.log('📊 Querying florida_parcels table schema...\n');

    const { data: columns, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .limit(1);

    if (error) {
      console.error('❌ ERROR querying database:', error.message);
      process.exit(1);
    }

    if (!columns || columns.length === 0) {
      console.error('❌ ERROR: florida_parcels table is empty or does not exist');
      process.exit(1);
    }

    // Get actual column names from the first row
    const actualColumns = Object.keys(columns[0]);
    console.log(`✅ Found ${actualColumns.length} columns in florida_parcels table\n`);

    // Validate each expected column
    const results = {
      found: [],
      missing: [],
      criticalMissing: []
    };

    // Get unique columns (deduplicate)
    const uniqueColumns = [...new Set(FILTER_COLUMN_MAPPINGS.map(m => m.column))];

    console.log('🔎 Validating Filter Columns:\n');

    uniqueColumns.forEach(expectedColumn => {
      const mapping = FILTER_COLUMN_MAPPINGS.find(m => m.column === expectedColumn);
      const exists = actualColumns.includes(expectedColumn);

      if (exists) {
        results.found.push({ column: expectedColumn, ...mapping });
        console.log(`  ✅ ${expectedColumn.padEnd(25)} - ${mapping.filter} (${mapping.type})`);
      } else {
        results.missing.push({ column: expectedColumn, ...mapping });
        if (mapping.critical) {
          results.criticalMissing.push({ column: expectedColumn, ...mapping });
          console.log(`  ❌ ${expectedColumn.padEnd(25)} - ${mapping.filter} (${mapping.type}) [CRITICAL]`);
        } else {
          console.log(`  ⚠️  ${expectedColumn.padEnd(25)} - ${mapping.filter} (${mapping.type}) [OPTIONAL]`);
        }
      }
    });

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('\n📊 VALIDATION SUMMARY:\n');
    console.log(`  ✅ Found:            ${results.found.length} / ${uniqueColumns.length} columns`);
    console.log(`  ❌ Missing:          ${results.missing.length} columns`);
    console.log(`  🚨 Critical Missing: ${results.criticalMissing.length} columns`);

    // Test data sample
    console.log('\n📦 Testing Data Sample:\n');
    const { data: sample, error: sampleError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, county, just_value, living_area, land_sqft, year_built')
      .not('just_value', 'is', null)
      .limit(3);

    if (!sampleError && sample && sample.length > 0) {
      sample.forEach((row, i) => {
        console.log(`  Property ${i + 1}:`);
        console.log(`    Parcel:      ${row.parcel_id}`);
        console.log(`    County:      ${row.county}`);
        console.log(`    Value:       $${(row.just_value || 0).toLocaleString()}`);
        console.log(`    Building:    ${(row.living_area || 0).toLocaleString()} sq ft`);
        console.log(`    Land:        ${(row.land_sqft || 0).toLocaleString()} sq ft`);
        console.log(`    Year Built:  ${row.year_built || 'N/A'}`);
        console.log('');
      });
    }

    // Recommendations for missing columns
    if (results.missing.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:\n');

      if (results.missing.find(m => m.column === 'homestead_exemption')) {
        console.log('  📌 Tax Exempt Filter:');
        console.log('     - Column "homestead_exemption" not found');
        console.log('     - Check alternative columns: exempt_value, exemption_type');
        console.log('     - May need to query exemptions from separate table\n');
      }

      if (results.missing.find(m => m.column === 'pool_ind')) {
        console.log('  📌 Pool Filter:');
        console.log('     - Column "pool_ind" not found');
        console.log('     - Needs NAP (property characteristics) table join');
        console.log('     - Alternative: Search property descriptions for "pool"\n');
      }

      if (results.missing.find(m => m.column === 'waterfront_ind')) {
        console.log('  📌 Waterfront Filter:');
        console.log('     - Column "waterfront_ind" not found');
        console.log('     - Needs NAP table or geographic boundary check');
        console.log('     - May require external data source\n');
      }
    }

    // Exit status
    console.log('='.repeat(80));
    if (results.criticalMissing.length > 0) {
      console.log('\n❌ VALIDATION FAILED: Critical columns missing');
      console.log('\n🔧 ACTION REQUIRED:');
      results.criticalMissing.forEach(m => {
        console.log(`   - Fix filter: ${m.filter} (missing column: ${m.column})`);
      });
      process.exit(1);
    } else if (results.missing.length > 0) {
      console.log('\n⚠️  VALIDATION PASSED WITH WARNINGS: Optional columns missing');
      console.log('   All critical filters have required columns');
      console.log(`   ${results.missing.length} optional filters need implementation`);
      process.exit(0);
    } else {
      console.log('\n✅ VALIDATION PASSED: All columns found!');
      console.log('   All 19 filters have database support');
      process.exit(0);
    }

  } catch (err) {
    console.error('\n❌ VALIDATION ERROR:', err.message);
    console.error(err.stack);
    process.exit(1);
  }
}

// Run validation
validateDatabaseSchema().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
