/**
 * Direct Database Query
 * Use SQL to query database for accurate counts
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

console.log('🔗 Connecting to Supabase...');
console.log(`   URL: ${supabaseUrl}`);
console.log(`   Key: ${supabaseKey ? supabaseKey.substring(0, 20) + '...' : 'NOT SET'}\n`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials!');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function queryDatabase() {
  console.log('📊 Querying database tables...\n');

  try {
    // Query using PostgREST to list tables
    console.log('1. Attempting to get table list...\n');

    const tables = [
      'florida_parcels',
      'sunbiz_corporate',
      'florida_entities',
      'property_sales_history',
      'tax_certificates',
      'sunbiz_entities',
      'sunbiz_corporations',
      'sunbiz_officer_contacts'
    ];

    for (const tableName of tables) {
      try {
        // Try to select count
        const { count, error, status, statusText } = await supabase
          .from(tableName)
          .select('*', { count: 'exact', head: true });

        if (error) {
          console.log(`❌ ${tableName.padEnd(30)} - Error: ${error.message} (Status: ${status})`);
        } else {
          console.log(`✅ ${tableName.padEnd(30)} - ${(count || 0).toLocaleString()} records`);

          // If records exist, get a sample
          if (count && count > 0) {
            const { data, error: sampleError } = await supabase
              .from(tableName)
              .select('*')
              .limit(1);

            if (!sampleError && data && data[0]) {
              const columns = Object.keys(data[0]);
              console.log(`   Columns (${columns.length}): ${columns.slice(0, 10).join(', ')}${columns.length > 10 ? '...' : ''}`);
            }
          }
        }
      } catch (err) {
        console.log(`❌ ${tableName.padEnd(30)} - Exception: ${err.message}`);
      }
    }

    // Try to get schema info using raw SQL if we have service role
    if (process.env.SUPABASE_SERVICE_ROLE_KEY) {
      console.log('\n2. Attempting to query information schema...\n');

      try {
        const { data, error } = await supabase
          .from('information_schema.tables')
          .select('table_name')
          .eq('table_schema', 'public');

        if (!error && data) {
          console.log(`Found ${data.length} tables in public schema:`);
          data.slice(0, 20).forEach(t => console.log(`   - ${t.table_name}`));
        } else if (error) {
          console.log(`   Could not query information schema: ${error.message}`);
        }
      } catch (err) {
        console.log(`   Could not access information schema: ${err.message}`);
      }
    }

  } catch (error) {
    console.error('\n❌ Query failed:', error.message);
  }
}

queryDatabase();
