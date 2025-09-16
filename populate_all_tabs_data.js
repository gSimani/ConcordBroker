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

async function populateAllTabsData() {
  console.log('[INFO] Populating data for all property tabs...');
  console.log(`[INFO] Target: ${supabaseUrl}\n`);
  
  // Test properties
  const testProperties = [
    '064210010010',
    '064210010011', 
    '064210015020',
    '494116370240',
    '514228131130',
    '504203060330'
  ];
  
  try {
    // 1. Populate property_sales_history
    console.log('[1] Populating property_sales_history...');
    
    const salesHistory = [
      // Property 064210010010
      {
        parcel_id: '064210010010',
        sale_date: '2024-08-15',
        sale_price: 485000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '12345',
        page: '678',
        book_page: '12345/678',
        cin: '2024000123456',
        grantor_name: 'BROWN ROBERT',
        grantee_name: 'SMITH JOHN & MARY',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'SAMPLE ESTATES',
        property_address: '1234 SAMPLE ST',
        city: 'FORT LAUDERDALE',
        zip_code: '33301'
      },
      {
        parcel_id: '064210010010',
        sale_date: '2021-03-22',
        sale_price: 380000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '11890',
        page: '456',
        book_page: '11890/456',
        cin: '2021000098765',
        grantor_name: 'DAVIS MICHAEL',
        grantee_name: 'BROWN ROBERT',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'SAMPLE ESTATES',
        property_address: '1234 SAMPLE ST',
        city: 'FORT LAUDERDALE',
        zip_code: '33301'
      },
      {
        parcel_id: '064210010010',
        sale_date: '2018-11-10',
        sale_price: 320000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '11234',
        page: '789',
        book_page: '11234/789',
        cin: '2018000054321',
        grantor_name: 'ORIGINAL OWNER',
        grantee_name: 'DAVIS MICHAEL',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'SAMPLE ESTATES',
        property_address: '1234 SAMPLE ST',
        city: 'FORT LAUDERDALE',
        zip_code: '33301'
      },
      // Property 064210010011
      {
        parcel_id: '064210010011',
        sale_date: '2023-03-22',
        sale_price: 380000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '12001',
        page: '123',
        book_page: '12001/123',
        cin: '2023000045678',
        grantor_name: 'WILLIAMS SARAH',
        grantee_name: 'JOHNSON ROBERT',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'SAMPLE ESTATES',
        property_address: '1236 SAMPLE ST',
        city: 'FORT LAUDERDALE',
        zip_code: '33301'
      },
      // Property 064210015020 (Commercial)
      {
        parcel_id: '064210015020',
        sale_date: '2024-11-20',
        sale_price: 675000,
        sale_type: 'Corporation Deed',
        sale_qualification: 'Qualified',
        book: '12456',
        page: '890',
        book_page: '12456/890',
        cin: '2024000234567',
        grantor_name: 'RETAIL VENTURES INC',
        grantee_name: 'SUNSHINE INVESTMENTS CORP',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'PEMBROKE COMMERCIAL CENTER',
        property_address: '5678 EXAMPLE AVE',
        city: 'PEMBROKE PINES',
        zip_code: '33028'
      }
    ];
    
    // Clear existing sales
    for (const parcelId of testProperties) {
      await supabase.from('property_sales_history').delete().eq('parcel_id', parcelId);
    }
    
    for (const sale of salesHistory) {
      try {
        const { error } = await supabase.from('property_sales_history').insert(sale);
        if (error) throw error;
        console.log(`  ✅ Added sale: ${sale.parcel_id} - ${sale.sale_date}`);
      } catch (e) {
        console.log(`  ⚠️ ${sale.parcel_id}: ${e.message}`);
      }
    }
    
    // 2. Create and populate nav_assessments
    console.log('\n[2] Populating nav_assessments...');
    
    const navAssessments = [
      {
        parcel_id: '064210010010',
        assessment_year: 2024,
        assessment_type: 'CDD',
        assessment_amount: 1250.00,
        district_name: 'SAMPLE ESTATES CDD',
        district_id: 'CDD-001',
        description: 'Community Development District Assessment'
      },
      {
        parcel_id: '064210010010',
        assessment_year: 2024,
        assessment_type: 'HOA',
        assessment_amount: 450.00,
        district_name: 'SAMPLE ESTATES HOA',
        district_id: 'HOA-001',
        description: 'Homeowners Association Fee'
      },
      {
        parcel_id: '064210010011',
        assessment_year: 2024,
        assessment_type: 'CDD',
        assessment_amount: 1250.00,
        district_name: 'SAMPLE ESTATES CDD',
        district_id: 'CDD-001',
        description: 'Community Development District Assessment'
      },
      {
        parcel_id: '064210015020',
        assessment_year: 2024,
        assessment_type: 'COMMERCIAL',
        assessment_amount: 3500.00,
        district_name: 'PEMBROKE BUSINESS DISTRICT',
        district_id: 'PBD-001',
        description: 'Commercial Property Special Assessment'
      }
    ];
    
    // Clear existing assessments
    for (const parcelId of testProperties) {
      await supabase.from('nav_assessments').delete().eq('parcel_id', parcelId);
    }
    
    for (const assessment of navAssessments) {
      try {
        const { error } = await supabase.from('nav_assessments').insert(assessment);
        if (error) throw error;
        console.log(`  ✅ Added NAV: ${assessment.parcel_id} - ${assessment.assessment_type}`);
      } catch (e) {
        console.log(`  ⚠️ ${assessment.parcel_id}: ${e.message}`);
      }
    }
    
    // 3. Populate tax_certificates
    console.log('\n[3] Populating tax_certificates...');
    
    const taxCertificates = [
      {
        parcel_id: '064210010010',
        certificate_year: 2022,
        certificate_number: 'TC-2022-001234',
        tax_amount: 8500.00,
        interest_rate: 18.00,
        bidder_name: 'TAX LIEN CAPITAL LLC',
        bidder_address: '100 INVESTOR BLVD, MIAMI, FL 33131',
        certificate_face_value: 8500.00,
        certificate_status: 'REDEEMED',
        redemption_date: '2023-06-15',
        redemption_amount: 9350.00
      },
      {
        parcel_id: '064210010011',
        certificate_year: 2023,
        certificate_number: 'TC-2023-002345',
        tax_amount: 6800.00,
        interest_rate: 16.00,
        bidder_name: 'FLORIDA TAX INVESTMENTS',
        bidder_address: '200 TAX CERT WAY, ORLANDO, FL 32801',
        certificate_face_value: 6800.00,
        certificate_status: 'ACTIVE',
        redemption_date: null,
        redemption_amount: null
      }
    ];
    
    for (const cert of taxCertificates) {
      try {
        const { error } = await supabase.from('tax_certificates').insert(cert);
        if (error) throw error;
        console.log(`  ✅ Added tax cert: ${cert.parcel_id} - ${cert.certificate_year}`);
      } catch (e) {
        console.log(`  ⚠️ ${cert.parcel_id}: ${e.message}`);
      }
    }
    
    // 4. Populate building_permits
    console.log('\n[4] Populating building_permits...');
    
    const permits = [
      {
        parcel_id: '064210010010',
        permit_number: 'BP-2024-001234',
        permit_type: 'ROOF',
        permit_description: 'Replace roof shingles',
        application_date: '2024-03-15',
        issue_date: '2024-03-20',
        completion_date: '2024-04-10',
        permit_status: 'COMPLETED',
        estimated_value: 15000.00,
        contractor_name: 'QUALITY ROOFING INC',
        contractor_license: 'CCC057854',
        owner_name: 'SMITH JOHN & MARY',
        work_description: 'Complete roof replacement with architectural shingles'
      },
      {
        parcel_id: '064210010010',
        permit_number: 'BP-2023-005678',
        permit_type: 'POOL',
        permit_description: 'Install swimming pool',
        application_date: '2023-06-01',
        issue_date: '2023-06-15',
        completion_date: '2023-08-30',
        permit_status: 'COMPLETED',
        estimated_value: 45000.00,
        contractor_name: 'AQUA POOLS LLC',
        contractor_license: 'CPC1457890',
        owner_name: 'SMITH JOHN & MARY',
        work_description: 'Install 15x30 gunite pool with spa'
      },
      {
        parcel_id: '064210015020',
        permit_number: 'BP-2024-009876',
        permit_type: 'COMMERCIAL',
        permit_description: 'Interior renovation',
        application_date: '2024-09-01',
        issue_date: '2024-09-10',
        completion_date: null,
        permit_status: 'ACTIVE',
        estimated_value: 125000.00,
        contractor_name: 'COMMERCIAL BUILDERS INC',
        contractor_license: 'CGC1234567',
        owner_name: 'SUNSHINE INVESTMENTS CORP',
        work_description: 'Complete interior renovation of retail space'
      }
    ];
    
    for (const permit of permits) {
      try {
        const { error } = await supabase.from('building_permits').insert(permit);
        if (error) throw error;
        console.log(`  ✅ Added permit: ${permit.parcel_id} - ${permit.permit_type}`);
      } catch (e) {
        console.log(`  ⚠️ ${permit.parcel_id}: ${e.message}`);
      }
    }
    
    // 5. Populate foreclosure_cases
    console.log('\n[5] Populating foreclosure_cases...');
    
    const foreclosures = [
      {
        parcel_id: '514228131130',
        case_number: 'FC-2023-001234',
        filing_date: '2023-02-15',
        case_status: 'DISMISSED',
        plaintiff_name: 'FIRST NATIONAL BANK',
        defendant_name: 'MARTINEZ FAMILY TRUST',
        attorney_name: 'FORECLOSURE LAW GROUP',
        attorney_phone: '(954) 555-0100',
        judgment_amount: 250000.00,
        judgment_date: null,
        sale_date: null,
        sale_amount: null,
        case_type: 'RESIDENTIAL FORECLOSURE',
        court_location: 'BROWARD COUNTY CIRCUIT COURT'
      }
    ];
    
    for (const fc of foreclosures) {
      try {
        const { error } = await supabase.from('foreclosure_cases').insert(fc);
        if (error) throw error;
        console.log(`  ✅ Added foreclosure: ${fc.parcel_id} - ${fc.case_status}`);
      } catch (e) {
        console.log(`  ⚠️ ${fc.parcel_id}: ${e.message}`);
      }
    }
    
    // 6. Populate tax_deed_sales
    console.log('\n[6] Populating tax_deed_sales...');
    
    const taxDeedSales = [
      {
        parcel_id: '514228131130',
        batch_number: 'TD-2023-BATCH-001',
        item_number: 'TD-2023-001234',
        auction_date: '2023-05-15',
        minimum_bid: 25000.00,
        assessed_value: 250000.00,
        property_address: '456 PALM AVE',
        property_description: 'Single Family Home, 3BR/1BA',
        certificate_holder: 'TAX CERTIFICATE HOLDER LLC',
        certificate_number: 'TC-2021-005678',
        certificate_face_value: 5000.00,
        winning_bid: 125000.00,
        winning_bidder: 'INVESTMENT PROPERTIES LLC',
        auction_status: 'SOLD'
      }
    ];
    
    for (const td of taxDeedSales) {
      try {
        const { error } = await supabase.from('tax_deed_sales').insert(td);
        if (error) throw error;
        console.log(`  ✅ Added tax deed: ${td.parcel_id} - ${td.auction_status}`);
      } catch (e) {
        console.log(`  ⚠️ ${td.parcel_id}: ${e.message}`);
      }
    }
    
    // 7. Populate tax_liens
    console.log('\n[7] Populating tax_liens...');
    
    const taxLiens = [
      {
        parcel_id: '064210010011',
        certificate_number: 'TL-2023-002345',
        certificate_year: 2023,
        tax_amount: 6800.00,
        interest_rate: 16.00,
        certificate_holder: 'FLORIDA TAX INVESTMENTS',
        purchase_date: '2023-06-01',
        purchase_price: 6800.00,
        redemption_status: 'ACTIVE',
        redemption_date: null,
        redemption_amount: null,
        expiration_date: '2030-06-01'
      }
    ];
    
    for (const lien of taxLiens) {
      try {
        const { error } = await supabase.from('tax_liens').insert(lien);
        if (error) throw error;
        console.log(`  ✅ Added tax lien: ${lien.parcel_id} - ${lien.redemption_status}`);
      } catch (e) {
        console.log(`  ⚠️ ${lien.parcel_id}: ${e.message}`);
      }
    }
    
    // 8. Test verification
    console.log('\n[8] Verifying populated data...');
    
    for (const parcelId of testProperties.slice(0, 3)) {
      console.log(`\n📍 ${parcelId}:`);
      
      // Check each table
      const tables = [
        { name: 'property_sales_history', field: 'sale_date' },
        { name: 'nav_assessments', field: 'assessment_type' },
        { name: 'tax_certificates', field: 'certificate_year' },
        { name: 'building_permits', field: 'permit_type' },
        { name: 'foreclosure_cases', field: 'case_status' },
        { name: 'tax_deed_sales', field: 'auction_status' },
        { name: 'tax_liens', field: 'redemption_status' }
      ];
      
      for (const table of tables) {
        try {
          const { data, error } = await supabase
            .from(table.name)
            .select('*')
            .eq('parcel_id', parcelId);
          
          if (error) {
            if (error.message.includes('does not exist')) {
              console.log(`  ⚠️ ${table.name}: Table not found`);
            } else {
              console.log(`  ❌ ${table.name}: ${error.message}`);
            }
          } else if (data && data.length > 0) {
            console.log(`  ✅ ${table.name}: ${data.length} records`);
          } else {
            console.log(`  ⚠️ ${table.name}: No data`);
          }
        } catch (e) {
          console.log(`  ❌ ${table.name}: ${e.message}`);
        }
      }
    }
    
    console.log('\n✅ Data population completed!');
    console.log('\n📊 TEST URLS:');
    console.log('Test these properties to see all tabs with data:');
    testProperties.forEach(parcelId => {
      console.log(`  http://localhost:5175/property/${parcelId}`);
    });
    
    console.log('\n💡 EXPECTED RESULTS:');
    console.log('✅ Core Property Info - All properties');
    console.log('✅ Sales History - 064210010010, 064210010011, 064210015020');
    console.log('✅ NAV Assessments - 064210010010, 064210010011, 064210015020');
    console.log('✅ Tax Certificates - 064210010010, 064210010011');
    console.log('✅ Building Permits - 064210010010, 064210015020');
    console.log('✅ Foreclosure - 514228131130');
    console.log('✅ Tax Deed Sales - 514228131130');
    console.log('✅ Tax Liens - 064210010011');
    console.log('✅ Analysis - All properties');
    
  } catch (e) {
    console.error('\n❌ Error:', e);
  }
}

// Run the function
populateAllTabsData().then(() => {
  console.log('\n✅ Script completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Script failed:', error);
  process.exit(1);
});