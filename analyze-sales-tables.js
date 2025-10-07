import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: 'apps/web/.env' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

async function analyzeAllSalesTables() {
  console.log('========================================');
  console.log('ANALYZING ALL SALES-RELATED TABLES IN SUPABASE');
  console.log('========================================\n');

  const results = {
    tablesWithData: [],
    emptyTables: [],
    missingTables: [],
    totalRecordsFound: 0
  };

  // List of all potential sales-related tables to check
  const tablesToCheck = [
    'property_sales_history',
    'fl_sdf_sales',
    'property_sales',
    'florida_parcels',
    'fl_sales',
    'sales_data',
    'property_transactions',
    'deed_records',
    'florida_sales',
    'broward_sales',
    'miami_dade_sales',
    'palm_beach_sales'
  ];

  for (const tableName of tablesToCheck) {
    console.log(`\nChecking table: ${tableName}`);
    console.log('-'.repeat(40));

    try {
      // First, try to get a count of records
      const { count, error: countError } = await supabase
        .from(tableName)
        .select('*', { count: 'exact', head: true });

      if (countError) {
        if (countError.code === 'PGRST205') {
          console.log(`❌ Table does not exist`);
          results.missingTables.push(tableName);
        } else {
          console.log(`⚠️ Error accessing table: ${countError.message}`);
        }
        continue;
      }

      console.log(`✅ Table exists with ${count || 0} total records`);

      // If table has data, get sample records and column info
      if (count > 0) {
        const { data: sampleData, error: sampleError } = await supabase
          .from(tableName)
          .select('*')
          .limit(1);

        if (!sampleError && sampleData && sampleData.length > 0) {
          const columns = Object.keys(sampleData[0]);
          console.log(`📋 Columns: ${columns.join(', ')}`);

          // Check for sales-related columns
          const salesColumns = columns.filter(col =>
            col.includes('sale') ||
            col.includes('price') ||
            col.includes('deed') ||
            col.includes('book') ||
            col.includes('page') ||
            col.includes('transaction')
          );

          if (salesColumns.length > 0) {
            console.log(`💰 Sales-related columns: ${salesColumns.join(', ')}`);

            // Check specifically for our test property
            if (tableName === 'florida_parcels' || columns.includes('parcel_id')) {
              const { data: propertyCheck, error: propError } = await supabase
                .from(tableName)
                .select('*')
                .eq('parcel_id', '514124070600')
                .limit(1);

              if (!propError && propertyCheck && propertyCheck.length > 0) {
                console.log(`🏠 Property 514124070600 found in this table`);

                // Check if it has sales data
                const record = propertyCheck[0];
                const hasSalesData = salesColumns.some(col => record[col] && record[col] !== null);

                if (hasSalesData) {
                  console.log(`📊 Property HAS sales data in this table:`);
                  salesColumns.forEach(col => {
                    if (record[col]) {
                      console.log(`   - ${col}: ${record[col]}`);
                    }
                  });
                } else {
                  console.log(`⚪ Property exists but NO sales data populated`);
                }
              }
            }
          }

          results.tablesWithData.push({
            name: tableName,
            count: count,
            columns: columns.length,
            salesColumns: salesColumns
          });
        }
      } else {
        results.emptyTables.push(tableName);
      }

      results.totalRecordsFound += count || 0;

    } catch (err) {
      console.log(`❌ Exception: ${err.message}`);
    }
  }

  console.log('\n\n========================================');
  console.log('SUMMARY REPORT');
  console.log('========================================');

  console.log('\n📊 TABLES WITH DATA:');
  results.tablesWithData.forEach(table => {
    console.log(`   ✅ ${table.name}: ${table.count.toLocaleString()} records, ${table.columns} columns`);
    if (table.salesColumns.length > 0) {
      console.log(`      Sales columns: ${table.salesColumns.join(', ')}`);
    }
  });

  console.log('\n📭 EMPTY TABLES:');
  results.emptyTables.forEach(table => {
    console.log(`   ⚪ ${table}`);
  });

  console.log('\n❌ MISSING TABLES:');
  results.missingTables.forEach(table => {
    console.log(`   ❌ ${table}`);
  });

  console.log(`\n📈 TOTAL RECORDS ACROSS ALL TABLES: ${results.totalRecordsFound.toLocaleString()}`);

  // Now check for any sales data for property 514124070600
  console.log('\n\n========================================');
  console.log('SEARCHING FOR SALES DATA FOR PROPERTY: 514124070600');
  console.log('========================================');

  const foundSalesData = [];

  for (const table of results.tablesWithData) {
    try {
      const { data, error } = await supabase
        .from(table.name)
        .select('*')
        .or('parcel_id.eq.514124070600,parcel.eq.514124070600,property_id.eq.514124070600')
        .limit(10);

      if (!error && data && data.length > 0) {
        console.log(`\n✅ Found ${data.length} records in ${table.name}:`);
        data.forEach(record => {
          // Look for any sales-related data
          const salesInfo = {};
          Object.keys(record).forEach(key => {
            if (key.includes('sale') || key.includes('price') || key.includes('deed') ||
                key.includes('book') || key.includes('page') || key.includes('date')) {
              if (record[key] !== null && record[key] !== '') {
                salesInfo[key] = record[key];
              }
            }
          });

          if (Object.keys(salesInfo).length > 0) {
            foundSalesData.push({ table: table.name, data: salesInfo });
            console.log(JSON.stringify(salesInfo, null, 2));
          }
        });
      }
    } catch (err) {
      // Skip errors for tables that don't have the expected columns
    }
  }

  if (foundSalesData.length === 0) {
    console.log('\n❌ NO SALES DATA FOUND for property 514124070600 in any table');
  }

  return results;
}

analyzeAllSalesTables();