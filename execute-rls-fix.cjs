/**
 * Execute RLS Fix for Data Loading
 *
 * This script will guide you through fixing RLS policies to enable data loading
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
require('dotenv').config({ path: '.env.mcp' });

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

console.log('\n🔧 RLS Policy Fix for Data Loading\n');
console.log('=' + '='.repeat(79));

if (!supabaseUrl || !supabaseKey) {
  console.error('\n❌ Missing Supabase credentials!');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Extract project reference from URL
const projectRef = supabaseUrl.replace('https://', '').split('.')[0];

async function checkRLSStatus() {
  console.log('\n📊 Step 1: Checking Current RLS Status\n');

  // Try to check RLS via information_schema
  const { data, error } = await supabase
    .from('pg_tables')
    .select('tablename, rowsecurity')
    .eq('schemaname', 'public')
    .in('tablename', ['florida_parcels', 'sunbiz_corporate', 'florida_entities']);

  if (error) {
    console.log('   ⚠️  Cannot query RLS status directly via API');
    console.log('   This is expected - RLS info requires SQL access');
  } else if (data) {
    console.log('   RLS Status:');
    data.forEach(table => {
      console.log(`   - ${table.tablename}: ${table.rowsecurity ? 'ENABLED' : 'DISABLED'}`);
    });
  }
}

async function testInsert() {
  console.log('\n🧪 Step 2: Testing INSERT Operation\n');

  const testRecord = {
    parcel_id: 'RLS-TEST-' + Date.now(),
    county: 'TEST',
    year: 2025,
    owner_name: 'RLS TEST',
    updated_at: new Date().toISOString()
  };

  const { data, error, status } = await supabase
    .from('florida_parcels')
    .insert([testRecord]);

  console.log(`   Status: ${status}`);

  if (error || status === 404) {
    console.log('   ❌ INSERT blocked (RLS issue confirmed)');
    return false;
  } else {
    console.log('   ✅ INSERT successful! RLS is fixed!');

    // Clean up test record
    await supabase
      .from('florida_parcels')
      .delete()
      .eq('parcel_id', testRecord.parcel_id);

    return true;
  }
}

async function provideInstructions() {
  console.log('\n📝 Step 3: Manual RLS Fix Required\n');
  console.log('Since automated RLS fix via API is not possible, please follow these steps:\n');

  console.log('1️⃣  Open Supabase SQL Editor:');
  console.log(`   https://supabase.com/dashboard/project/${projectRef}/sql/new\n`);

  console.log('2️⃣  Copy and paste this SQL (Option 1 - Simplest):\n');
  console.log('   ┌─────────────────────────────────────────────────────┐');
  console.log('   │ ALTER TABLE florida_parcels DISABLE ROW LEVEL SECURITY; │');
  console.log('   └─────────────────────────────────────────────────────┘\n');

  console.log('3️⃣  Click "Run" or press Ctrl+Enter\n');

  console.log('4️⃣  Expected result: "Success. No rows returned"\n');

  console.log('5️⃣  Return here and run:');
  console.log('   node load-broward-stream.cjs\n');

  console.log('📄 Full SQL file available: fix-rls-policies.sql');
  console.log('   (includes alternative methods and re-enable instructions)\n');

  console.log('⚠️  IMPORTANT: After loading data, re-enable RLS:');
  console.log('   ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;\n');
}

async function main() {
  try {
    // Step 1: Check RLS status (may not work via API)
    await checkRLSStatus();

    // Step 2: Test if insert works
    const insertWorks = await testInsert();

    if (insertWorks) {
      console.log('\n✅ RLS is already fixed! Ready to load data.\n');
      console.log('Run: node load-broward-stream.cjs\n');
    } else {
      // Step 3: Provide manual instructions
      await provideInstructions();

      console.log('=' + '='.repeat(79));
      console.log('\n⏸️  Waiting for you to fix RLS...');
      console.log('After running the SQL, come back and run this script again to verify.\n');
      console.log('Or jump straight to loading: node load-broward-stream.cjs\n');
    }

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  }
}

main();
