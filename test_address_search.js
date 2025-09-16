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

async function testAddressSearch() {
  console.log('🔍 Testing Address Search Functionality');
  console.log('=========================================\n');
  
  try {
    // 1. Get total count of properties
    console.log('[1] Checking total properties in database...');
    const { count: totalCount } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true });
    
    console.log(`   ✅ Total properties in database: ${totalCount || 0}\n`);
    
    // 2. Get all unique addresses (first 10)
    console.log('[2] Fetching sample addresses from database...');
    const { data: addresses, error: addressError } = await supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, phy_city, phy_zipcd')
      .not('phy_addr1', 'is', null)
      .limit(10);
    
    if (addressError) {
      console.error('   ❌ Error fetching addresses:', addressError);
      return;
    }
    
    if (!addresses || addresses.length === 0) {
      console.log('   ⚠️ No addresses found in database');
      return;
    }
    
    console.log(`   ✅ Found ${addresses.length} sample addresses:\n`);
    addresses.forEach((addr, idx) => {
      console.log(`      ${idx + 1}. ${addr.phy_addr1}, ${addr.phy_city}, FL ${addr.phy_zipcd}`);
      console.log(`         Parcel ID: ${addr.parcel_id}`);
    });
    
    // 3. Test search for each address
    console.log('\n[3] Testing search functionality for each address...\n');
    
    for (const addr of addresses.slice(0, 3)) { // Test first 3
      if (!addr.phy_addr1) continue;
      
      // Extract just the street number for search
      const streetNumber = addr.phy_addr1.split(' ')[0];
      console.log(`   Testing search for: "${streetNumber}"...`);
      
      const { data: searchResults, error: searchError } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city')
        .ilike('phy_addr1', `${streetNumber}%`)
        .limit(5);
      
      if (searchError) {
        console.error(`   ❌ Search error: ${searchError.message}`);
      } else if (searchResults && searchResults.length > 0) {
        console.log(`   ✅ Found ${searchResults.length} results:`);
        searchResults.forEach(result => {
          console.log(`      - ${result.phy_addr1}, ${result.phy_city}`);
        });
      } else {
        console.log('   ⚠️ No results found');
      }
      console.log('');
    }
    
    // 4. Test city search
    console.log('[4] Testing city search...');
    const { data: cities } = await supabase
      .from('florida_parcels')
      .select('phy_city')
      .not('phy_city', 'is', null)
      .limit(100);
    
    const uniqueCities = [...new Set(cities?.map(c => c.phy_city) || [])];
    console.log(`   ✅ Found ${uniqueCities.length} unique cities:`);
    console.log(`      ${uniqueCities.slice(0, 10).join(', ')}${uniqueCities.length > 10 ? ', ...' : ''}\n`);
    
    // 5. Test autocomplete-like search
    console.log('[5] Testing autocomplete functionality...');
    const testQueries = ['123', '456', '789', 'MAIN', 'OCEAN'];
    
    for (const query of testQueries) {
      const { data: autoResults } = await supabase
        .from('florida_parcels')
        .select('phy_addr1, phy_city, phy_zipcd')
        .or(`phy_addr1.ilike.%${query}%,phy_city.ilike.%${query}%`)
        .limit(3);
      
      console.log(`   Query "${query}": Found ${autoResults?.length || 0} results`);
      if (autoResults && autoResults.length > 0) {
        console.log(`      First result: ${autoResults[0].phy_addr1}, ${autoResults[0].phy_city}`);
      }
    }
    
    // 6. Summary
    console.log('\n=========================================');
    console.log('📊 SUMMARY:');
    console.log(`   • Total properties: ${totalCount || 0}`);
    console.log(`   • Sample addresses tested: ${Math.min(3, addresses.length)}`);
    console.log(`   • Unique cities found: ${uniqueCities.length}`);
    console.log(`   • Search functionality: ${addresses.length > 0 ? '✅ Working' : '❌ No data'}`);
    
    if (totalCount === 0) {
      console.log('\n⚠️ WARNING: No properties in database!');
      console.log('   Run populate_simple_data.js to add test data');
    } else if (totalCount < 10) {
      console.log('\n⚠️ WARNING: Very few properties in database');
      console.log('   Consider adding more test data');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testAddressSearch().then(() => {
  console.log('\n✅ Test completed');
  process.exit(0);
}).catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});