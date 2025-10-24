/**
 * Test Single Record Insert
 * Debug RLS and schema issues
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.mcp' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY;

console.log('Testing single record insert...\n');
console.log('Using Service Role Key:', supabaseKey ? 'YES' : 'NO');
console.log('Key type:', supabaseKey ? (supabaseKey.startsWith('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6') ? 'SERVICE_ROLE' : 'ANON') : 'NONE');
console.log('');

const supabase = createClient(supabaseUrl, supabaseKey);

async function testInsert() {
  const testRecord = {
    parcel_id: 'TEST-001',
    county: 'BROWARD',
    year: 2025,
    owner_name: 'TEST OWNER',
    phy_addr1: '123 TEST ST',
    owner_city: 'TEST CITY',
    owner_state: 'FL',
    just_value: 100000,
    updated_at: new Date().toISOString()
  };

  console.log('Test record:');
  console.log(JSON.stringify(testRecord, null, 2));
  console.log('');

  console.log('Attempting insert...');
  const { data, error, status, statusText } = await supabase
    .from('florida_parcels')
    .insert([testRecord]);

  console.log('\nResult:');
  console.log('Status:', status, statusText);
  console.log('Error:', error ? JSON.stringify(error, null, 2) : 'None');
  console.log('Data:', data ? JSON.stringify(data, null, 2) : 'None');

  if (!error) {
    console.log('\n✅ Insert successful!');

    // Try to read it back
    console.log('\nReading record back...');
    const { data: readData, error: readError } = await supabase
      .from('florida_parcels')
      .select('*')
      .eq('parcel_id', 'TEST-001')
      .single();

    console.log('Read result:');
    console.log('Error:', readError ? JSON.stringify(readError, null, 2) : 'None');
    console.log('Data:', readData ? JSON.stringify(readData, null, 2) : 'None');
  } else {
    console.log('\n❌ Insert failed!');
    console.log('Full error object:', JSON.stringify(error));
  }
}

testInsert();
