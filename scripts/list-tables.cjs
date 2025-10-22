#!/usr/bin/env node
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

async function listTables() {
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;

  const supabase = createClient(supabaseUrl, supabaseKey);

  // Try to list tables using RPC
  const { data, error } = await supabase.rpc('get_tables');

  if (error) {
    console.log('Trying alternative method...');
    // Try querying information_schema
    const { data: tables, error: err2 } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'public');

    if (err2) {
      console.log('Error:', err2.message);
      // Last resort - try listing known tables
      console.log('\nTrying to query known tables:');
      const testTables = ['florida_parcels', 'property_sales_history', 'User', 'tax_certificates'];
      for (const table of testTables) {
        const { data, error } = await supabase.from(table).select('*').limit(1);
        if (!error && data) {
          console.log(`✅ Table "${table}" exists (${data.length} sample rows)`);
        } else {
          console.log(`❌ Table "${table}" - ${error?.message || 'unknown error'}`);
        }
      }
    } else {
      console.log('Tables:', tables);
    }
  } else {
    console.log('Tables:', data);
  }
}

listTables();
