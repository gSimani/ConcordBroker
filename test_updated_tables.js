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

async function testUpdatedTables() {
  console.log('🔍 Testing data fetching with updated table names...\n');
  console.log(`📡 Supabase URL: ${supabaseUrl}\n`);
  
  // Test properties - using the same ones we populated
  const testProperties = [
    '064210010010',
    '064210010011', 
    '064210015020',
    '494116370240',
    '514228131130',
    '504203060330'
  ];
  
  const results = [];
  
  for (const parcelId of testProperties) {
    console.log(`\n📍 Testing Property: ${parcelId}`);
    console.log('='.repeat(50));
    
    const result = {
      property: parcelId,
      parcelId: parcelId,
      tabs: {}
    };
    
    // Test 1: Core Property Info - Check both florida_parcels AND properties tables
    console.log('\n1️⃣ Core Property Info Tab:');
    try {
      // Check florida_parcels first
      const { data: floridaParcel, error: fpError } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .limit(1);
      
      // Check properties table (as per updated hook)
      const { data: propertiesData, error: pError } = await supabase
        .from('properties')
        .select('*')
        .eq('parcel_id', parcelId)
        .limit(1);
      
      if (floridaParcel && floridaParcel.length > 0) {
        const prop = floridaParcel[0];
        console.log(`   ✅ Found in florida_parcels`);
        console.log(`   - Address: ${prop.phy_addr1 || 'N/A'}`);
        console.log(`   - Owner: ${prop.owner_name || 'N/A'}`);
        console.log(`   - Value: $${prop.taxable_value || 0}`);
        result.tabs['core'] = {
          status: 'success',
          message: 'Data found in florida_parcels',
          dataFound: prop
        };
      } else if (pError && pError.message.includes('does not exist')) {
        console.log(`   ⚠️ properties table does not exist`);
        result.tabs['core'] = {
          status: 'no-table',
          message: 'properties table not found'
        };
      } else if (propertiesData && propertiesData.length > 0) {
        const prop = propertiesData[0];
        console.log(`   ✅ Found in properties table`);
        result.tabs['core'] = {
          status: 'success',
          message: 'Data found in properties',
          dataFound: prop
        };
      } else {
        console.log(`   ⚠️ No data found in either table`);
        result.tabs['core'] = {
          status: 'no-data',
          message: 'No property data found'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['core'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 2: Sales History - property_sales_history table
    console.log('\n2️⃣ Sales History (property_sales_history):');
    try {
      const { data: salesHistory, error } = await supabase
        .from('property_sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false });
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ property_sales_history table does not exist`);
        result.tabs['sales'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (salesHistory && salesHistory.length > 0) {
        console.log(`   ✅ Found ${salesHistory.length} sales`);
        salesHistory.slice(0, 3).forEach(sale => {
          console.log(`   - ${sale.sale_date}: $${sale.sale_price} (${sale.sale_type})`);
        });
        result.tabs['sales'] = {
          status: 'success',
          message: `${salesHistory.length} sales found`,
          dataFound: salesHistory
        };
      } else {
        console.log(`   ⚠️ No sales history found`);
        result.tabs['sales'] = {
          status: 'no-data',
          message: 'No sales history'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['sales'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 3: Sunbiz Info - sunbiz_corporate table
    console.log('\n3️⃣ Sunbiz Info Tab (sunbiz_corporate):');
    try {
      const { data: sunbizData, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .eq('parcel_id', parcelId)
        .limit(5);
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ sunbiz_corporate table does not exist`);
        result.tabs['sunbiz'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (sunbizData && sunbizData.length > 0) {
        console.log(`   ✅ Found ${sunbizData.length} business entities`);
        result.tabs['sunbiz'] = {
          status: 'success',
          message: `${sunbizData.length} entities found`,
          dataFound: sunbizData
        };
      } else {
        console.log(`   ⚠️ No business entities found`);
        result.tabs['sunbiz'] = {
          status: 'no-data',
          message: 'No business entities'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['sunbiz'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 4: NAV Assessments - nav_assessments table
    console.log('\n4️⃣ NAV Assessments (nav_assessments):');
    try {
      const { data: navData, error } = await supabase
        .from('nav_assessments')
        .select('*')
        .eq('parcel_id', parcelId);
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ nav_assessments table does not exist`);
        result.tabs['nav'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (navData && navData.length > 0) {
        console.log(`   ✅ Found ${navData.length} NAV assessments`);
        result.tabs['nav'] = {
          status: 'success',
          message: `${navData.length} assessments found`,
          dataFound: navData
        };
      } else {
        console.log(`   ⚠️ No NAV assessments found`);
        result.tabs['nav'] = {
          status: 'no-data',
          message: 'No NAV assessments'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['nav'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 5: Property Tax Info - tax_certificates table
    console.log('\n5️⃣ Property Tax Info Tab (tax_certificates):');
    try {
      const { data: taxCerts, error } = await supabase
        .from('tax_certificates')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('certificate_year', { ascending: false });
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ tax_certificates table does not exist`);
        result.tabs['taxes'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (taxCerts && taxCerts.length > 0) {
        console.log(`   ✅ Found ${taxCerts.length} tax certificates`);
        result.tabs['taxes'] = {
          status: 'success',
          message: `${taxCerts.length} certificates found`,
          dataFound: taxCerts
        };
      } else {
        console.log(`   ⚠️ No tax certificates found`);
        result.tabs['taxes'] = {
          status: 'no-data',
          message: 'No tax certificates'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['taxes'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 6: Permits - building_permits table
    console.log('\n6️⃣ Permit Tab (building_permits):');
    try {
      const { data: permits, error } = await supabase
        .from('building_permits')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('application_date', { ascending: false });
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ building_permits table does not exist`);
        result.tabs['permits'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (permits && permits.length > 0) {
        console.log(`   ✅ Found ${permits.length} permits`);
        result.tabs['permits'] = {
          status: 'success',
          message: `${permits.length} permits found`,
          dataFound: permits
        };
      } else {
        console.log(`   ⚠️ No permits found`);
        result.tabs['permits'] = {
          status: 'no-data',
          message: 'No permits'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['permits'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 7: Foreclosure - foreclosure_cases table
    console.log('\n7️⃣ Foreclosure Tab (foreclosure_cases):');
    try {
      const { data: foreclosures, error } = await supabase
        .from('foreclosure_cases')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('filing_date', { ascending: false });
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ foreclosure_cases table does not exist`);
        result.tabs['foreclosure'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (foreclosures && foreclosures.length > 0) {
        console.log(`   ✅ Found ${foreclosures.length} foreclosure cases`);
        result.tabs['foreclosure'] = {
          status: 'success',
          message: `${foreclosures.length} cases found`,
          dataFound: foreclosures
        };
      } else {
        console.log(`   ⚠️ No foreclosure cases found`);
        result.tabs['foreclosure'] = {
          status: 'no-data',
          message: 'No foreclosure cases'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['foreclosure'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 8: Sales Tax Deed - tax_deed_sales table
    console.log('\n8️⃣ Sales Tax Deed Tab (tax_deed_sales):');
    try {
      const { data: taxDeeds, error } = await supabase
        .from('tax_deed_sales')
        .select('*')
        .eq('parcel_id', parcelId);
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ tax_deed_sales table does not exist`);
        result.tabs['taxdeed'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (taxDeeds && taxDeeds.length > 0) {
        console.log(`   ✅ Found ${taxDeeds.length} tax deed sales`);
        result.tabs['taxdeed'] = {
          status: 'success',
          message: `${taxDeeds.length} sales found`,
          dataFound: taxDeeds
        };
      } else {
        console.log(`   ⚠️ No tax deed sales found`);
        result.tabs['taxdeed'] = {
          status: 'no-data',
          message: 'No tax deed sales'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['taxdeed'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 9: Tax Lien - tax_liens table
    console.log('\n9️⃣ Tax Lien Tab (tax_liens):');
    try {
      const { data: taxLiens, error } = await supabase
        .from('tax_liens')
        .select('*')
        .eq('parcel_id', parcelId);
      
      if (error && error.message.includes('does not exist')) {
        console.log(`   ⚠️ tax_liens table does not exist`);
        result.tabs['taxlien'] = {
          status: 'no-table',
          message: 'Table does not exist'
        };
      } else if (taxLiens && taxLiens.length > 0) {
        console.log(`   ✅ Found ${taxLiens.length} tax liens`);
        result.tabs['taxlien'] = {
          status: 'success',
          message: `${taxLiens.length} liens found`,
          dataFound: taxLiens
        };
      } else {
        console.log(`   ⚠️ No tax liens found`);
        result.tabs['taxlien'] = {
          status: 'no-data',
          message: 'No tax liens'
        };
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['taxlien'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 10: Analysis Tab (uses aggregated data)
    console.log('\n🔟 Analysis Tab:');
    if (result.tabs['core']?.status === 'success') {
      console.log(`   ✅ Analysis available (uses core property data)`);
      result.tabs['analysis'] = {
        status: 'success',
        message: 'Analysis available'
      };
    } else {
      console.log(`   ⚠️ Analysis requires core property data`);
      result.tabs['analysis'] = {
        status: 'no-data',
        message: 'Requires core property data'
      };
    }
    
    results.push(result);
  }
  
  // Summary Report
  console.log('\n\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY REPORT');
  console.log('='.repeat(60));
  
  const tabNames = ['core', 'sales', 'sunbiz', 'nav', 'taxes', 'permits', 'foreclosure', 'taxdeed', 'taxlien', 'analysis'];
  const summary = {};
  
  tabNames.forEach(tab => {
    summary[tab] = { success: 0, error: 0, noData: 0, noTable: 0 };
  });
  
  results.forEach(result => {
    Object.entries(result.tabs).forEach(([tab, data]) => {
      if (data.status === 'success') summary[tab].success++;
      else if (data.status === 'error') summary[tab].error++;
      else if (data.status === 'no-table') summary[tab].noTable++;
      else summary[tab].noData++;
    });
  });
  
  console.log('\nResults by Tab:');
  tabNames.forEach(tab => {
    const s = summary[tab];
    const total = testProperties.length;
    console.log(`\n${tab.toUpperCase()}:`);
    if (s.success > 0) console.log(`  ✅ Success: ${s.success}/${total} (${Math.round(s.success/total*100)}%)`);
    if (s.noTable > 0) console.log(`  📦 Table Missing: ${s.noTable}/${total}`);
    if (s.error > 0) console.log(`  ❌ Errors: ${s.error}/${total}`);
    if (s.noData > 0) console.log(`  ⚠️ No Data: ${s.noData}/${total}`);
  });
  
  // Tables that need to be created
  console.log('\n\n📦 MISSING TABLES:');
  const missingTables = new Set();
  results.forEach(result => {
    Object.entries(result.tabs).forEach(([tab, data]) => {
      if (data.status === 'no-table') {
        if (tab === 'core') missingTables.add('properties');
        if (tab === 'sales') missingTables.add('property_sales_history');
        if (tab === 'sunbiz') missingTables.add('sunbiz_corporate');
        if (tab === 'nav') missingTables.add('nav_assessments');
        if (tab === 'taxes') missingTables.add('tax_certificates');
        if (tab === 'permits') missingTables.add('building_permits');
        if (tab === 'foreclosure') missingTables.add('foreclosure_cases');
        if (tab === 'taxdeed') missingTables.add('tax_deed_sales');
        if (tab === 'taxlien') missingTables.add('tax_liens');
      }
    });
  });
  
  if (missingTables.size > 0) {
    console.log('The following tables need to be created:');
    [...missingTables].forEach(table => {
      console.log(`  - ${table}`);
    });
  } else {
    console.log('All tables exist!');
  }
  
  // Properties with data
  console.log('\n\n✅ WORKING PROPERTIES:');
  results.forEach(result => {
    const workingTabs = Object.entries(result.tabs)
      .filter(([_, data]) => data.status === 'success')
      .map(([tab]) => tab);
    
    if (workingTabs.length > 0) {
      console.log(`\n${result.parcelId}:`);
      workingTabs.forEach(tab => console.log(`  ✓ ${tab}`));
    }
  });
  
  console.log('\n\n💡 NEXT STEPS:');
  console.log('1. Create missing tables in Supabase SQL editor');
  console.log('2. Run the data population script to add sample data');
  console.log('3. Test the property pages in the browser');
  
  console.log('\n📋 TEST URLS:');
  testProperties.forEach(parcelId => {
    console.log(`http://localhost:5175/property/${parcelId}`);
  });
  
  return results;
}

// Run the test
testUpdatedTables().then(() => {
  console.log('\n✅ Test completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Test failed:', error);
  process.exit(1);
});