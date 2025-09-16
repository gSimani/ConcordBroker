#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
dotenv.config({ path: join(__dirname, 'apps/web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkTableStructure() {
  console.log('[INFO] Checking florida_parcels table structure...\n');
  
  try {
    // Get one existing record to see the structure
    const { data: existing, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .limit(1);
    
    if (error) {
      console.log('❌ Error fetching data:', error.message);
      return;
    }
    
    if (existing && existing.length > 0) {
      console.log('✅ Found existing record. Column structure:');
      console.log('=' .repeat(60));
      
      const record = existing[0];
      const columns = Object.keys(record).sort();
      
      columns.forEach(col => {
        const value = record[col];
        const type = value === null ? 'null' : typeof value;
        console.log(`  ${col}: ${type} = ${JSON.stringify(value)}`);
      });
      
      console.log('\n📊 Summary:');
      console.log(`Total columns: ${columns.length}`);
      console.log('\nRequired columns found:');
      const requiredCols = ['parcel_id', 'year', 'phy_addr1', 'owner_name', 'taxable_value'];
      requiredCols.forEach(col => {
        if (columns.includes(col)) {
          console.log(`  ✅ ${col}`);
        } else {
          console.log(`  ❌ ${col} - MISSING`);
        }
      });
      
      // Now insert a test record with the correct structure
      console.log('\n[TEST] Attempting to insert sample data...');
      
      // Build a minimal record based on the existing structure
      const testRecord = {
        parcel_id: 'TEST123456',
        year: 2024  // This appears to be the required field
      };
      
      // Add other fields if they exist in the table
      if (columns.includes('phy_addr1')) testRecord.phy_addr1 = 'TEST ADDRESS';
      if (columns.includes('phy_city')) testRecord.phy_city = 'FORT LAUDERDALE';
      if (columns.includes('phy_state')) testRecord.phy_state = 'FL';
      if (columns.includes('phy_zipcd')) testRecord.phy_zipcd = '33301';
      if (columns.includes('owner_name')) testRecord.owner_name = 'TEST OWNER';
      if (columns.includes('taxable_value')) testRecord.taxable_value = 100000;
      if (columns.includes('county')) testRecord.county = 'BROWARD';
      
      console.log('\nInserting test record:', testRecord);
      
      const { error: insertError } = await supabase
        .from('florida_parcels')
        .insert(testRecord);
      
      if (insertError) {
        console.log('❌ Insert failed:', insertError.message);
      } else {
        console.log('✅ Test insert successful!');
        
        // Clean up test record
        await supabase
          .from('florida_parcels')
          .delete()
          .eq('parcel_id', 'TEST123456');
        console.log('✅ Cleaned up test record');
      }
      
    } else {
      console.log('⚠️ No existing records found in florida_parcels table');
      console.log('The table might be empty or not accessible');
    }
    
  } catch (e) {
    console.error('❌ Error:', e);
  }
}

// Run the check
checkTableStructure().then(() => {
  console.log('\n✅ Check completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Check failed:', error);
  process.exit(1);
});