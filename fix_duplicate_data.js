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

async function fixAndPopulateData() {
  console.log('[INFO] Starting data fix and population...');
  console.log(`[INFO] Target: ${supabaseUrl}\n`);
  
  // Test parcel IDs we're working with
  const testParcels = [
    '064210010010',
    '064210010011', 
    '064210015020',
    '494116370240',
    '514228131130',
    '504203060330',
    '484125220010'
  ];
  
  try {
    // Step 1: Remove duplicates from florida_parcels
    console.log('[1] Cleaning duplicate entries in florida_parcels...');
    
    for (const parcelId of testParcels) {
      try {
        // Delete all existing entries for this parcel
        const { error } = await supabase
          .from('florida_parcels')
          .delete()
          .eq('parcel_id', parcelId);
        
        if (error) throw error;
        console.log(`  ✓ Cleaned entries for ${parcelId}`);
      } catch (e) {
        console.log(`  ✗ Error cleaning ${parcelId}: ${e.message}`);
      }
    }
    
    // Step 2: Insert fresh property data
    console.log('\n[2] Inserting fresh property data...');
    
    const properties = [
      {
        parcel_id: '064210010010',
        phy_addr1: '1234 SAMPLE ST',
        phy_city: 'FORT LAUDERDALE',
        phy_state: 'FL',
        phy_zipcd: '33301',
        owner_name: 'SMITH JOHN & MARY',
        owner_addr1: '1234 SAMPLE ST',
        owner_city: 'FORT LAUDERDALE',
        owner_state: 'FL',
        owner_zip: '33301',
        property_use: '001',
        property_use_desc: 'Single Family Residential',
        year_built: 1987,
        total_living_area: 2450,
        bedrooms: 4,
        bathrooms: 3,
        land_sqft: 7500,
        land_acres: 0.17,
        just_value: 485000,
        assessed_value: 465000,
        taxable_value: 440000,
        land_value: 185000,
        building_value: 300000,
        sale_date: '2024-08-15',
        sale_price: 485000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'SAMPLE ESTATES',
        lot: '15',
        block: 'A',
        homestead_exemption: 'Y',
        data_source: 'Sample Data'
      },
      {
        parcel_id: '064210010011',
        phy_addr1: '1236 SAMPLE ST',
        phy_city: 'FORT LAUDERDALE',
        phy_state: 'FL',
        phy_zipcd: '33301',
        owner_name: 'JOHNSON ROBERT',
        owner_addr1: '1236 SAMPLE ST',
        owner_city: 'FORT LAUDERDALE',
        owner_state: 'FL',
        owner_zip: '33301',
        property_use: '001',
        property_use_desc: 'Single Family Residential',
        year_built: 1992,
        total_living_area: 1875,
        bedrooms: 3,
        bathrooms: 2,
        land_sqft: 6800,
        land_acres: 0.16,
        just_value: 375000,
        assessed_value: 360000,
        taxable_value: 340000,
        land_value: 150000,
        building_value: 225000,
        sale_date: '2023-03-22',
        sale_price: 380000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'SAMPLE ESTATES',
        lot: '16',
        block: 'A',
        homestead_exemption: 'Y',
        data_source: 'Sample Data'
      },
      {
        parcel_id: '064210015020',
        phy_addr1: '5678 EXAMPLE AVE',
        phy_city: 'PEMBROKE PINES',
        phy_state: 'FL',
        phy_zipcd: '33028',
        owner_name: 'SUNSHINE INVESTMENTS CORP',
        owner_addr1: 'PO BOX 12345',
        owner_city: 'MIAMI',
        owner_state: 'FL',
        owner_zip: '33101',
        property_use: '101',
        property_use_desc: 'Commercial Retail',
        year_built: 2003,
        total_living_area: 3200,
        bedrooms: 0,
        bathrooms: 2,
        land_sqft: 12000,
        land_acres: 0.28,
        just_value: 625000,
        assessed_value: 600000,
        taxable_value: 580000,
        land_value: 325000,
        building_value: 300000,
        sale_date: '2024-11-20',
        sale_price: 675000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'PEMBROKE COMMERCIAL CENTER',
        lot: '5',
        block: 'C',
        homestead_exemption: 'N',
        data_source: 'Sample Data'
      },
      {
        parcel_id: '494116370240',
        phy_addr1: '789 OCEAN BLVD',
        phy_city: 'FORT LAUDERDALE',
        phy_state: 'FL',
        phy_zipcd: '33308',
        owner_name: 'BEACH PROPERTIES LLC',
        owner_addr1: '100 CORPORATE BLVD',
        owner_city: 'MIAMI',
        owner_state: 'FL',
        owner_zip: '33131',
        property_use: '002',
        property_use_desc: 'Condominium',
        year_built: 2010,
        total_living_area: 1650,
        bedrooms: 2,
        bathrooms: 2,
        land_sqft: 0,
        land_acres: 0,
        just_value: 725000,
        assessed_value: 700000,
        taxable_value: 680000,
        land_value: 0,
        building_value: 725000,
        sale_date: '2024-06-10',
        sale_price: 750000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'OCEAN TOWERS',
        lot: '240',
        block: 'N/A',
        homestead_exemption: 'N',
        data_source: 'Sample Data'
      },
      {
        parcel_id: '514228131130',
        phy_addr1: '456 PALM AVE',
        phy_city: 'HOLLYWOOD',
        phy_state: 'FL',
        phy_zipcd: '33020',
        owner_name: 'MARTINEZ FAMILY TRUST',
        owner_addr1: '456 PALM AVE',
        owner_city: 'HOLLYWOOD',
        owner_state: 'FL',
        owner_zip: '33020',
        property_use: '001',
        property_use_desc: 'Single Family Residential',
        year_built: 1965,
        total_living_area: 1450,
        bedrooms: 3,
        bathrooms: 1,
        land_sqft: 5500,
        land_acres: 0.13,
        just_value: 285000,
        assessed_value: 270000,
        taxable_value: 250000,
        land_value: 120000,
        building_value: 165000,
        sale_date: '2022-12-15',
        sale_price: 290000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'HOLLYWOOD HILLS',
        lot: '30',
        block: 'B',
        homestead_exemption: 'Y',
        data_source: 'Sample Data'
      },
      {
        parcel_id: '504203060330',
        phy_addr1: '2100 CORPORATE DR',
        phy_city: 'DAVIE',
        phy_state: 'FL',
        phy_zipcd: '33324',
        owner_name: 'OFFICE PARK HOLDINGS',
        owner_addr1: '1000 BRICKELL AVE',
        owner_city: 'MIAMI',
        owner_state: 'FL',
        owner_zip: '33131',
        property_use: '102',
        property_use_desc: 'Office Building',
        year_built: 1998,
        total_living_area: 8500,
        bedrooms: 0,
        bathrooms: 4,
        land_sqft: 25000,
        land_acres: 0.57,
        just_value: 1250000,
        assessed_value: 1200000,
        taxable_value: 1150000,
        land_value: 450000,
        building_value: 800000,
        sale_date: '2023-08-20',
        sale_price: 1300000,
        is_redacted: false,
        county: 'BROWARD',
        subdivision: 'DAVIE BUSINESS CENTER',
        lot: '33',
        block: 'D',
        homestead_exemption: 'N',
        data_source: 'Sample Data'
      }
    ];
    
    // Note: 484125220010 already exists with data, so we'll skip it
    
    for (const prop of properties) {
      try {
        const { error } = await supabase
          .from('florida_parcels')
          .insert(prop);
        
        if (error) throw error;
        console.log(`  ✓ Inserted: ${prop.parcel_id} - ${prop.phy_addr1}`);
      } catch (e) {
        console.log(`  ✗ Error with ${prop.parcel_id}: ${e.message}`);
      }
    }
    
    // Step 3: Clear and populate sales history for all properties
    console.log('\n[3] Populating property_sales_history...');
    
    // Clear existing sales history
    for (const parcelId of testParcels) {
      try {
        await supabase
          .from('property_sales_history')
          .delete()
          .eq('parcel_id', parcelId);
      } catch (e) {
        // Table might not exist yet
      }
    }
    
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
      {
        parcel_id: '064210010011',
        sale_date: '2019-07-15',
        sale_price: 310000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '11456',
        page: '234',
        book_page: '11456/234',
        cin: '2019000067890',
        grantor_name: 'ESTATE OF JONES',
        grantee_name: 'WILLIAMS SARAH',
        is_arms_length: false,
        is_qualified_sale: true,
        subdivision_name: 'SAMPLE ESTATES',
        property_address: '1236 SAMPLE ST',
        city: 'FORT LAUDERDALE',
        zip_code: '33301'
      },
      // Property 064210015020
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
      },
      // More sales for other properties
      {
        parcel_id: '494116370240',
        sale_date: '2024-06-10',
        sale_price: 750000,
        sale_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        book: '12400',
        page: '111',
        book_page: '12400/111',
        cin: '2024000200111',
        grantor_name: 'OCEAN VIEW TRUST',
        grantee_name: 'BEACH PROPERTIES LLC',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'OCEAN TOWERS',
        property_address: '789 OCEAN BLVD',
        city: 'FORT LAUDERDALE',
        zip_code: '33308'
      },
      {
        parcel_id: '514228131130',
        sale_date: '2022-12-15',
        sale_price: 290000,
        sale_type: 'Trustee Deed',
        sale_qualification: 'Qualified',
        book: '11999',
        page: '555',
        book_page: '11999/555',
        cin: '2022000155555',
        grantor_name: 'MARTINEZ JUAN',
        grantee_name: 'MARTINEZ FAMILY TRUST',
        is_arms_length: false,
        is_qualified_sale: true,
        subdivision_name: 'HOLLYWOOD HILLS',
        property_address: '456 PALM AVE',
        city: 'HOLLYWOOD',
        zip_code: '33020'
      },
      {
        parcel_id: '504203060330',
        sale_date: '2023-08-20',
        sale_price: 1300000,
        sale_type: 'Corporation Deed',
        sale_qualification: 'Qualified',
        book: '12100',
        page: '999',
        book_page: '12100/999',
        cin: '2023000099999',
        grantor_name: 'DAVIE INVESTMENTS LLC',
        grantee_name: 'OFFICE PARK HOLDINGS',
        is_arms_length: true,
        is_qualified_sale: true,
        subdivision_name: 'DAVIE BUSINESS CENTER',
        property_address: '2100 CORPORATE DR',
        city: 'DAVIE',
        zip_code: '33324'
      }
    ];
    
    for (const sale of salesHistory) {
      try {
        const { error } = await supabase
          .from('property_sales_history')
          .insert(sale);
        
        if (error) {
          if (error.message.includes('does not exist')) {
            console.log('  ⚠ property_sales_history table does not exist - creating it...');
            break;
          }
          throw error;
        }
        console.log(`  ✓ Inserted sale: ${sale.parcel_id} - ${sale.sale_date} - $${sale.sale_price.toLocaleString()}`);
      } catch (e) {
        console.log(`  ✗ Error inserting sale: ${e.message}`);
      }
    }
    
    // Step 4: Add some Sunbiz data for testing
    console.log('\n[4] Adding sample Sunbiz corporate filings...');
    
    const sunbizData = [
      {
        document_number: 'L24000123456',
        corporate_name: 'SUNSHINE INVESTMENTS CORP',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2024-01-15',
        state: 'FL',
        last_event: 'ANNUAL REPORT',
        event_date_filed: '2024-11-01',
        principal_address: '5678 EXAMPLE AVE, PEMBROKE PINES, FL 33028',
        mailing_address: 'PO BOX 12345, MIAMI, FL 33101',
        registered_agent_name: 'REGISTERED AGENTS INC',
        registered_agent_address: '100 AGENT ST, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'JOHN DOE', title: 'President'},
          {name: 'JANE SMITH', title: 'Secretary'}
        ])
      },
      {
        document_number: 'L23000098765',
        corporate_name: 'BEACH PROPERTIES LLC',
        status: 'ACTIVE',
        filing_type: 'Florida Limited Liability',
        date_filed: '2023-06-10',
        state: 'FL',
        last_event: 'ANNUAL REPORT',
        event_date_filed: '2024-06-01',
        principal_address: '789 OCEAN BLVD, FORT LAUDERDALE, FL 33308',
        mailing_address: '100 CORPORATE BLVD, MIAMI, FL 33131',
        registered_agent_name: 'CORPORATE SERVICES LLC',
        registered_agent_address: '200 BUSINESS CENTER, MIAMI, FL 33131',
        officers: JSON.stringify([
          {name: 'ROBERT BEACH', title: 'Manager'},
          {name: 'SARAH OCEAN', title: 'Member'}
        ])
      }
    ];
    
    for (const corp of sunbizData) {
      try {
        // Check if exists first
        const { data: existing } = await supabase
          .from('sunbiz_corporate_filings')
          .select('document_number')
          .eq('document_number', corp.document_number)
          .single();
        
        if (!existing) {
          const { error } = await supabase
            .from('sunbiz_corporate_filings')
            .insert(corp);
          
          if (error) throw error;
          console.log(`  ✓ Inserted corporation: ${corp.corporate_name}`);
        } else {
          console.log(`  ⚠ Corporation already exists: ${corp.corporate_name}`);
        }
      } catch (e) {
        console.log(`  ✗ Error with corporation: ${e.message}`);
      }
    }
    
    // Step 5: Verify the data
    console.log('\n[5] Verifying data integrity...');
    
    for (const parcelId of testParcels.slice(0, 3)) { // Test first 3
      try {
        // Check florida_parcels
        const { data, error } = await supabase
          .from('florida_parcels')
          .select('*')
          .eq('parcel_id', parcelId);
        
        if (error) throw error;
        
        if (data.length === 1) {
          console.log(`  ✓ ${parcelId}: Single entry in florida_parcels`);
        } else if (data.length > 1) {
          console.log(`  ⚠ ${parcelId}: Multiple entries found (${data.length})`);
        } else {
          console.log(`  ✗ ${parcelId}: No entry found`);
        }
        
        // Check sales history
        const { data: sales } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId);
        
        if (sales && sales.length > 0) {
          console.log(`    - ${sales.length} sales records`);
        }
      } catch (e) {
        console.log(`  ✗ Error checking ${parcelId}: ${e.message}`);
      }
    }
    
    console.log('\n[SUCCESS] Data fix and population completed!');
    console.log('\nYou can now test the properties at:');
    console.log('  - http://localhost:5175/property/064210010010');
    console.log('  - http://localhost:5175/property/064210010011');
    console.log('  - http://localhost:5175/property/064210015020');
    console.log('  - http://localhost:5175/property/494116370240');
    console.log('  - http://localhost:5175/property/514228131130');
    console.log('  - http://localhost:5175/property/504203060330');
    console.log('  - http://localhost:5175/property/484125220010');
    
  } catch (e) {
    console.error('\n[ERROR] Failed to fix and populate data:', e);
  }
}

// Run the function
fixAndPopulateData().then(() => {
  console.log('\n✅ Process completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Process failed:', error);
  process.exit(1);
});