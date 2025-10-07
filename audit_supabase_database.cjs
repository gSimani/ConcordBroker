/**
 * Comprehensive Supabase Database Audit
 * Analyzes structure, performance, and data quality
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.mcp' });

const client = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

const KNOWN_TABLES = [
  'florida_parcels',
  'property_sales_history',
  'florida_entities',
  'sunbiz_corporate',
  'tax_certificates',
  'dor_use_codes'
];

async function auditDatabase() {
  console.log('='.repeat(80));
  console.log('COMPREHENSIVE SUPABASE DATABASE AUDIT');
  console.log('='.repeat(80));
  console.log();

  const results = {
    tables: {},
    issues: [],
    recommendations: [],
    summary: {}
  };

  // 1. Check each table's existence and basic stats
  console.log('📊 PHASE 1: Table Analysis\n');

  for (const tableName of KNOWN_TABLES) {
    console.log(`Analyzing: ${tableName}`);
    const tableAudit = {
      name: tableName,
      exists: false,
      rowCount: 0,
      sampleData: null,
      columns: [],
      issues: []
    };

    try {
      // Get row count
      const { count, error: countError } = await client
        .from(tableName)
        .select('*', { count: 'exact', head: true });

      if (countError) {
        tableAudit.issues.push(`Table not accessible: ${countError.message}`);
        results.issues.push(`❌ ${tableName}: ${countError.message}`);
      } else {
        tableAudit.exists = true;
        tableAudit.rowCount = count || 0;

        // Get sample row to analyze structure
        const { data: sample, error: sampleError } = await client
          .from(tableName)
          .select('*')
          .limit(1);

        if (!sampleError && sample && sample.length > 0) {
          tableAudit.sampleData = sample[0];
          tableAudit.columns = Object.keys(sample[0]);

          // Analyze column types and null values
          for (const col of tableAudit.columns) {
            const val = sample[0][col];
            if (val === null || val === undefined) {
              tableAudit.issues.push(`Column '${col}' has null value in sample`);
            }
          }
        }

        console.log(`  ✅ Exists: ${count?.toLocaleString() || 0} rows, ${tableAudit.columns.length} columns`);
      }
    } catch (error) {
      tableAudit.issues.push(`Error accessing table: ${error.message}`);
      results.issues.push(`❌ ${tableName}: ${error.message}`);
      console.log(`  ❌ Error: ${error.message}`);
    }

    results.tables[tableName] = tableAudit;
    console.log();
  }

  // 2. Check florida_parcels (main table)
  console.log('\n📋 PHASE 2: florida_parcels Deep Analysis\n');

  if (results.tables.florida_parcels?.exists) {
    const table = 'florida_parcels';

    // Check for missing critical fields
    const { data: parcels, error } = await client
      .from(table)
      .select('parcel_id, county, year, owner_name, just_value, phy_addr1, property_use')
      .limit(1000);

    if (!error && parcels) {
      let missingParcelId = 0, missingCounty = 0, missingYear = 0;
      let missingOwner = 0, missingValue = 0, missingAddress = 0, missingUse = 0;

      parcels.forEach(row => {
        if (!row.parcel_id) missingParcelId++;
        if (!row.county) missingCounty++;
        if (!row.year) missingYear++;
        if (!row.owner_name) missingOwner++;
        if (!row.just_value || row.just_value === 0) missingValue++;
        if (!row.phy_addr1) missingAddress++;
        if (!row.property_use) missingUse++;
      });

      console.log('Critical Field Completeness (sample of 1000):');
      console.log(`  parcel_id: ${((1000 - missingParcelId) / 10).toFixed(1)}% complete`);
      console.log(`  county: ${((1000 - missingCounty) / 10).toFixed(1)}% complete`);
      console.log(`  year: ${((1000 - missingYear) / 10).toFixed(1)}% complete`);
      console.log(`  owner_name: ${((1000 - missingOwner) / 10).toFixed(1)}% complete`);
      console.log(`  just_value: ${((1000 - missingValue) / 10).toFixed(1)}% complete`);
      console.log(`  phy_addr1: ${((1000 - missingAddress) / 10).toFixed(1)}% complete`);
      console.log(`  property_use: ${((1000 - missingUse) / 10).toFixed(1)}% complete`);

      if (missingParcelId > 0) results.issues.push(`❌ ${missingParcelId} parcels missing parcel_id`);
      if (missingValue > 100) results.issues.push(`⚠️  ${missingValue} parcels missing just_value`);
      if (missingUse > 100) results.issues.push(`⚠️  ${missingUse} parcels missing property_use`);
    }
  }

  // 3. Check property_sales_history
  console.log('\n📋 PHASE 3: property_sales_history Analysis\n');

  if (results.tables.property_sales_history?.exists) {
    const { data: sales, error } = await client
      .from('property_sales_history')
      .select('parcel_id, sale_price, sale_date, quality_code')
      .limit(1000);

    if (!error && sales) {
      let missingPrice = 0, missingDate = 0, invalidPrice = 0;
      let minPrice = Infinity, maxPrice = 0, totalPrice = 0;

      sales.forEach(row => {
        if (!row.sale_price) missingPrice++;
        if (!row.sale_date) missingDate++;
        if (row.sale_price && row.sale_price < 100) invalidPrice++;
        if (row.sale_price) {
          minPrice = Math.min(minPrice, row.sale_price);
          maxPrice = Math.max(maxPrice, row.sale_price);
          totalPrice += row.sale_price;
        }
      });

      console.log('Sales Data Quality (sample of 1000):');
      console.log(`  sale_price: ${((1000 - missingPrice) / 10).toFixed(1)}% complete`);
      console.log(`  sale_date: ${((1000 - missingDate) / 10).toFixed(1)}% complete`);
      console.log(`  Invalid prices (<$100): ${invalidPrice}`);
      if (sales.length > 0) {
        console.log(`  Price range: $${(minPrice / 100).toFixed(2)} - $${(maxPrice / 100).toLocaleString()}`);
        console.log(`  Average: $${((totalPrice / sales.length) / 100).toLocaleString()}`);
      }

      if (invalidPrice > 10) results.issues.push(`⚠️  ${invalidPrice} sales with price < $100`);
    }
  }

  // 4. Check relationships and foreign keys
  console.log('\n🔗 PHASE 4: Relationship Analysis\n');

  if (results.tables.florida_parcels?.exists && results.tables.property_sales_history?.exists) {
    const { data: orphanedSales } = await client
      .from('property_sales_history')
      .select('parcel_id')
      .limit(100);

    if (orphanedSales && orphanedSales.length > 0) {
      let orphanCount = 0;
      for (const sale of orphanedSales.slice(0, 20)) {
        const { data } = await client
          .from('florida_parcels')
          .select('parcel_id')
          .eq('parcel_id', sale.parcel_id)
          .limit(1);

        if (!data || data.length === 0) orphanCount++;
      }

      if (orphanCount > 0) {
        console.log(`  ⚠️  Found ${orphanCount}/20 sales with no matching parcel`);
        results.issues.push(`⚠️  Orphaned sales records detected (${orphanCount}/20 sample)`);
      } else {
        console.log('  ✅ Sales-to-Parcels relationship healthy');
      }
    }
  }

  // 5. Performance Analysis
  console.log('\n⚡ PHASE 5: Performance Analysis\n');

  const perfTests = [
    { table: 'florida_parcels', filter: 'county', value: 'BROWARD' },
    { table: 'florida_parcels', filter: 'just_value', range: [100000, 500000] },
    { table: 'property_sales_history', filter: 'sale_date', range: ['2023-01-01', '2023-12-31'] }
  ];

  for (const test of perfTests) {
    const start = Date.now();
    let query = client.from(test.table).select('*', { count: 'exact', head: true });

    if (test.range) {
      query = query.gte(test.filter, test.range[0]).lte(test.filter, test.range[1]);
    } else {
      query = query.eq(test.filter, test.value);
    }

    const { count, error } = await query;
    const duration = Date.now() - start;

    if (!error) {
      console.log(`  ${test.table}.${test.filter}: ${duration}ms (${count?.toLocaleString() || 0} results)`);
      if (duration > 2000) {
        results.recommendations.push(`🔧 Add index on ${test.table}.${test.filter} (query took ${duration}ms)`);
      }
    }
  }

  // 6. Generate Summary
  console.log('\n' + '='.repeat(80));
  console.log('AUDIT SUMMARY');
  console.log('='.repeat(80));
  console.log();

  const totalRows = Object.values(results.tables).reduce((sum, t) => sum + (t.rowCount || 0), 0);
  const existingTables = Object.values(results.tables).filter(t => t.exists).length;

  console.log(`📊 Total Tables: ${existingTables}/${KNOWN_TABLES.length}`);
  console.log(`📊 Total Records: ${totalRows.toLocaleString()}`);
  console.log(`📊 Issues Found: ${results.issues.length}`);
  console.log(`📊 Recommendations: ${results.recommendations.length}`);
  console.log();

  if (results.issues.length > 0) {
    console.log('🚨 ISSUES:\n');
    results.issues.forEach(issue => console.log(`  ${issue}`));
    console.log();
  }

  if (results.recommendations.length > 0) {
    console.log('💡 RECOMMENDATIONS:\n');
    results.recommendations.forEach(rec => console.log(`  ${rec}`));
    console.log();
  }

  // Critical recommendations based on findings
  console.log('🎯 CRITICAL RECOMMENDATIONS:\n');

  if (results.tables.florida_parcels?.rowCount === 0) {
    console.log('  ❗ URGENT: florida_parcels table is empty - need to import data');
  }

  if (results.tables.property_sales_history?.rowCount < 100000) {
    console.log('  ⚠️  property_sales_history has fewer records than expected');
  }

  console.log('  ✅ Add composite index: (parcel_id, county, year) on florida_parcels');
  console.log('  ✅ Add index: sale_date on property_sales_history');
  console.log('  ✅ Add index: quality_code on property_sales_history');
  console.log('  ✅ Add full-text search index on owner_name in florida_parcels');
  console.log('  ✅ Consider partitioning florida_parcels by county for better performance');
  console.log('  ✅ Enable Row Level Security (RLS) on all tables');
  console.log('  ✅ Set up automated VACUUM and ANALYZE schedules');

  console.log('\n' + '='.repeat(80));
  console.log('Audit complete!');
  console.log('='.repeat(80));
}

auditDatabase().catch(console.error);
