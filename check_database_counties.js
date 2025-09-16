#!/usr/bin/env node

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, 'apps/web/.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

async function checkDatabaseCounties() {
  console.log('📊 CHECKING ACTUAL DATABASE CONTENT');
  console.log('====================================\n');

  // Get distinct counties
  const { data: counties, error: countiesError } = await supabase
    .from('florida_parcels')
    .select('county')
    .limit(50000);

  if (countiesError) {
    console.error('Error fetching counties:', countiesError);
    return;
  }

  const uniqueCounties = [...new Set(counties.map(c => c.county).filter(Boolean))];
  
  console.log('Counties in database:');
  uniqueCounties.forEach(county => {
    console.log(`  • ${county}`);
  });

  console.log(`\nTotal unique counties: ${uniqueCounties.length}`);

  // Get count per county
  for (const county of uniqueCounties) {
    const { count } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('county', county);
    
    console.log(`${county}: ${count?.toLocaleString() || 0} properties`);
  }

  // Check if we have data from other Florida counties
  const otherCounties = ['MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH', 'DUVAL', 'PINELLAS'];
  
  console.log('\nChecking for other major Florida counties:');
  for (const county of otherCounties) {
    const { count } = await supabase
      .from('florida_parcels')
      .select('*', { count: 'exact', head: true })
      .eq('county', county);
    
    console.log(`  ${county}: ${count || 0} properties`);
  }

  console.log('\n💡 CONCLUSION:');
  if (uniqueCounties.length === 1 && uniqueCounties[0] === 'BROWARD') {
    console.log('  ⚠️ Database currently contains ONLY BROWARD county data.');
    console.log('  This is a DATA limitation, not a CODE restriction.');
    console.log('  The search code is unrestricted, but only BROWARD data exists.');
    console.log('\n  To have truly unrestricted search across Florida:');
    console.log('  1. Import data from other Florida counties');
    console.log('  2. The search will automatically include them (no code changes needed)');
  } else {
    console.log('  ✅ Database contains multiple counties!');
    console.log('  The search should work across all counties.');
  }
}

checkDatabaseCounties().catch(console.error);