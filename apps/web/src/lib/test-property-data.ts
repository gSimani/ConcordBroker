import { supabase } from './supabase';

interface TestResult {
  property: string;
  parcelId: string;
  tabs: {
    [key: string]: {
      status: 'success' | 'error' | 'no-data';
      message: string;
      dataFound?: any;
    };
  };
}

export async function testPropertyDataFetching() {
  console.log('🔍 Starting comprehensive property data test...\n');
  
  // Test properties - mix of different parcel IDs
  const testProperties = [
    '064210010010',
    '064210010011', 
    '064210015020',
    '494116370240',
    '514228131130',
    '504203060330',
    '484125220010'
  ];
  
  const results: TestResult[] = [];
  
  for (const parcelId of testProperties) {
    console.log(`\n📍 Testing Property: ${parcelId}`);
    console.log('=' .repeat(50));
    
    const result: TestResult = {
      property: parcelId,
      parcelId: parcelId,
      tabs: {}
    };
    
    // Test 1: Core Property Info - florida_parcels table
    console.log('\n1️⃣ Core Property Info Tab:');
    try {
      const { data: floridaParcel, error } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .single();
      
      if (error) throw error;
      
      if (floridaParcel) {
        console.log(`   ✅ Found in florida_parcels`);
        console.log(`   - Address: ${floridaParcel.phy_addr1 || 'N/A'}`);
        console.log(`   - Owner: ${floridaParcel.owner_name || 'N/A'}`);
        console.log(`   - Value: $${floridaParcel.taxable_value || 0}`);
        console.log(`   - Year Built: ${floridaParcel.year_built || 'N/A'}`);
        result.tabs['core'] = {
          status: 'success',
          message: 'Data found',
          dataFound: floridaParcel
        };
      } else {
        // Try fl_properties as fallback
        const { data: flProperty } = await supabase
          .from('fl_properties')
          .select('*')
          .eq('parcel_id', parcelId)
          .single();
        
        if (flProperty) {
          console.log(`   ✅ Found in fl_properties (fallback)`);
          result.tabs['core'] = {
            status: 'success',
            message: 'Data found in fl_properties',
            dataFound: flProperty
          };
        } else {
          console.log(`   ⚠️ No data found in either table`);
          result.tabs['core'] = {
            status: 'no-data',
            message: 'No property data found'
          };
        }
      }
    } catch (error: any) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['core'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 2: Sales History
    console.log('\n2️⃣ Sales History (in Core Property):');
    try {
      // Check property_sales_history
      const { data: salesHistory, error: salesError } = await supabase
        .from('property_sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false });
      
      if (!salesError && salesHistory && salesHistory.length > 0) {
        console.log(`   ✅ Found ${salesHistory.length} sales in property_sales_history`);
        salesHistory.slice(0, 3).forEach(sale => {
          console.log(`   - ${sale.sale_date}: $${sale.sale_price} (${sale.sale_type})`);
        });
        result.tabs['sales'] = {
          status: 'success',
          message: `${salesHistory.length} sales found`,
          dataFound: salesHistory
        };
      } else {
        // Try fl_sdf_sales as fallback
        const { data: sdfSales } = await supabase
          .from('fl_sdf_sales')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });
        
        if (sdfSales && sdfSales.length > 0) {
          console.log(`   ✅ Found ${sdfSales.length} sales in fl_sdf_sales`);
          result.tabs['sales'] = {
            status: 'success',
            message: `${sdfSales.length} sales in fl_sdf_sales`,
            dataFound: sdfSales
          };
        } else {
          console.log(`   ⚠️ No sales history found`);
          result.tabs['sales'] = {
            status: 'no-data',
            message: 'No sales history'
          };
        }
      }
    } catch (error: any) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['sales'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 3: Sunbiz Info
    console.log('\n3️⃣ Sunbiz Info Tab:');
    try {
      const { data: sunbizData, error } = await supabase
        .from('sunbiz_corporate_filings')
        .select('*')
        .or(`principal_address.ilike.%${parcelId}%,mailing_address.ilike.%${parcelId}%`)
        .limit(5);
      
      if (!error && sunbizData && sunbizData.length > 0) {
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
    } catch (error: any) {
      console.log(`   ❌ Error: ${error.message}`);
      result.tabs['sunbiz'] = {
        status: 'error',
        message: error.message
      };
    }
    
    // Test 4: Property Tax Info
    console.log('\n4️⃣ Property Tax Info Tab:');
    try {
      const { data: taxCerts, error } = await supabase
        .from('tax_certificates')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('certificate_year', { ascending: false });
      
      if (!error && taxCerts && taxCerts.length > 0) {
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
    } catch (error: any) {
      if (error.message.includes('does not exist')) {
        console.log(`   ⚠️ Tax certificates table does not exist`);
        result.tabs['taxes'] = {
          status: 'no-data',
          message: 'Table does not exist'
        };
      } else {
        console.log(`   ❌ Error: ${error.message}`);
        result.tabs['taxes'] = {
          status: 'error',
          message: error.message
        };
      }
    }
    
    // Test 5: Permit Tab
    console.log('\n5️⃣ Permit Tab:');
    try {
      const { data: permits, error } = await supabase
        .from('building_permits')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('application_date', { ascending: false });
      
      if (!error && permits && permits.length > 0) {
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
    } catch (error: any) {
      if (error.message.includes('does not exist')) {
        console.log(`   ⚠️ Permits table does not exist`);
        result.tabs['permits'] = {
          status: 'no-data',
          message: 'Table does not exist'
        };
      } else {
        console.log(`   ❌ Error: ${error.message}`);
        result.tabs['permits'] = {
          status: 'error',
          message: error.message
        };
      }
    }
    
    // Test 6: Foreclosure Tab
    console.log('\n6️⃣ Foreclosure Tab:');
    try {
      const { data: foreclosures, error } = await supabase
        .from('foreclosure_cases')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('filing_date', { ascending: false });
      
      if (!error && foreclosures && foreclosures.length > 0) {
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
    } catch (error: any) {
      if (error.message.includes('does not exist')) {
        console.log(`   ⚠️ Foreclosure table does not exist`);
        result.tabs['foreclosure'] = {
          status: 'no-data',
          message: 'Table does not exist'
        };
      } else {
        console.log(`   ❌ Error: ${error.message}`);
        result.tabs['foreclosure'] = {
          status: 'error',
          message: error.message
        };
      }
    }
    
    // Test 7: Sales Tax Deed Tab
    console.log('\n7️⃣ Sales Tax Deed Tab:');
    try {
      const { data: taxDeeds, error } = await supabase
        .from('tax_deed_bidding_items')
        .select('*')
        .eq('parcel_id', parcelId);
      
      if (!error && taxDeeds && taxDeeds.length > 0) {
        console.log(`   ✅ Found ${taxDeeds.length} tax deed items`);
        result.tabs['taxdeed'] = {
          status: 'success',
          message: `${taxDeeds.length} items found`,
          dataFound: taxDeeds
        };
      } else {
        console.log(`   ⚠️ No tax deed items found`);
        result.tabs['taxdeed'] = {
          status: 'no-data',
          message: 'No tax deed items'
        };
      }
    } catch (error: any) {
      if (error.message.includes('does not exist')) {
        console.log(`   ⚠️ Tax deed table does not exist`);
        result.tabs['taxdeed'] = {
          status: 'no-data',
          message: 'Table does not exist'
        };
      } else {
        console.log(`   ❌ Error: ${error.message}`);
        result.tabs['taxdeed'] = {
          status: 'error',
          message: error.message
        };
      }
    }
    
    // Test 8: Tax Lien Tab
    console.log('\n8️⃣ Tax Lien Tab:');
    try {
      const { data: taxLiens, error } = await supabase
        .from('tax_lien_certificates')
        .select('*')
        .eq('parcel_id', parcelId);
      
      if (!error && taxLiens && taxLiens.length > 0) {
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
    } catch (error: any) {
      if (error.message.includes('does not exist')) {
        console.log(`   ⚠️ Tax lien table does not exist`);
        result.tabs['taxlien'] = {
          status: 'no-data',
          message: 'Table does not exist'
        };
      } else {
        console.log(`   ❌ Error: ${error.message}`);
        result.tabs['taxlien'] = {
          status: 'error',
          message: error.message
        };
      }
    }
    
    // Test 9: Analysis Tab (uses aggregated data)
    console.log('\n9️⃣ Analysis Tab:');
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
  
  const tabNames = ['core', 'sales', 'sunbiz', 'taxes', 'permits', 'foreclosure', 'taxdeed', 'taxlien', 'analysis'];
  const summary: { [key: string]: { success: number; error: number; noData: number } } = {};
  
  tabNames.forEach(tab => {
    summary[tab] = { success: 0, error: 0, noData: 0 };
  });
  
  results.forEach(result => {
    Object.entries(result.tabs).forEach(([tab, data]) => {
      if (data.status === 'success') summary[tab].success++;
      else if (data.status === 'error') summary[tab].error++;
      else summary[tab].noData++;
    });
  });
  
  console.log('\nResults by Tab:');
  tabNames.forEach(tab => {
    const s = summary[tab];
    const total = s.success + s.error + s.noData;
    console.log(`\n${tab.toUpperCase()}:`);
    console.log(`  ✅ Success: ${s.success}/${total} (${Math.round(s.success/total*100)}%)`);
    console.log(`  ❌ Errors: ${s.error}/${total}`);
    console.log(`  ⚠️ No Data: ${s.noData}/${total}`);
  });
  
  // Properties with issues
  console.log('\n\n🔴 Properties with Data Issues:');
  results.forEach(result => {
    const issues = Object.entries(result.tabs)
      .filter(([_, data]) => data.status !== 'success')
      .map(([tab, data]) => `${tab}: ${data.message}`);
    
    if (issues.length > 0) {
      console.log(`\n${result.parcelId}:`);
      issues.forEach(issue => console.log(`  - ${issue}`));
    }
  });
  
  // Recommendations
  console.log('\n\n💡 RECOMMENDATIONS:');
  console.log('1. Populate missing tables using the schema deployment scripts');
  console.log('2. Import actual property data from Florida Revenue sources');
  console.log('3. Run data population script for sample data: /admin/populate-data');
  console.log('4. Check Supabase dashboard for table structure issues');
  
  return results;
}

// Make it available in browser console
if (typeof window !== 'undefined') {
  (window as any).testPropertyData = testPropertyDataFetching;
}