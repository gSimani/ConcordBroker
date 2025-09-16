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

async function populateSimpleData() {
  console.log('[INFO] Populating simple property data...');
  console.log(`[INFO] Target: ${supabaseUrl}\n`);
  
  // Test parcel IDs
  const testParcels = [
    '064210010010',
    '064210010011', 
    '064210015020',
    '494116370240',
    '514228131130',
    '504203060330'
  ];
  
  try {
    // Step 1: Clean up duplicates
    console.log('[1] Cleaning duplicate entries...');
    
    for (const parcelId of testParcels) {
      try {
        await supabase
          .from('florida_parcels')
          .delete()
          .eq('parcel_id', parcelId);
        console.log(`  ✓ Cleaned ${parcelId}`);
      } catch (e) {
        console.log(`  ⚠ ${parcelId}: ${e.message}`);
      }
    }
    
    // Step 2: Insert simple property data (without homestead_exemption)
    console.log('\n[2] Inserting property data...');
    
    const properties = [
      {
        parcel_id: '064210010010',
        year: 2025,  // Required field
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
        data_source: 'Sample Data'
      },
      {
        parcel_id: '064210010011',
        year: 2025,
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
        data_source: 'Sample Data'
      },
      {
        parcel_id: '064210015020',
        year: 2025,
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
        data_source: 'Sample Data'
      },
      {
        parcel_id: '494116370240',
        year: 2025,
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
        data_source: 'Sample Data'
      },
      {
        parcel_id: '514228131130',
        year: 2025,
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
        data_source: 'Sample Data'
      },
      {
        parcel_id: '504203060330',
        year: 2025,
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
        data_source: 'Sample Data'
      }
    ];
    
    for (const prop of properties) {
      try {
        const { error } = await supabase
          .from('florida_parcels')
          .insert(prop);
        
        if (error) throw error;
        console.log(`  ✅ Inserted: ${prop.parcel_id} - ${prop.phy_addr1}`);
        console.log(`     Owner: ${prop.owner_name}`);
        console.log(`     Value: $${prop.taxable_value.toLocaleString()}`);
      } catch (e) {
        console.log(`  ❌ Error with ${prop.parcel_id}: ${e.message}`);
      }
    }
    
    // Step 3: Verify the data
    console.log('\n[3] Verifying data...');
    
    for (const parcelId of testParcels) {
      try {
        const { data, error } = await supabase
          .from('florida_parcels')
          .select('parcel_id, phy_addr1, owner_name, taxable_value')
          .eq('parcel_id', parcelId);
        
        if (error) throw error;
        
        if (data && data.length === 1) {
          const prop = data[0];
          console.log(`  ✅ ${parcelId}: ${prop.phy_addr1}`);
          console.log(`     Owner: ${prop.owner_name}`);
          console.log(`     Value: $${(prop.taxable_value || 0).toLocaleString()}`);
        } else if (data && data.length > 1) {
          console.log(`  ⚠️ ${parcelId}: Found ${data.length} duplicates`);
        } else {
          console.log(`  ❌ ${parcelId}: Not found`);
        }
      } catch (e) {
        console.log(`  ❌ Error checking ${parcelId}: ${e.message}`);
      }
    }
    
    console.log('\n✅ Data population completed!');
    console.log('\n📊 TEST URLS:');
    console.log('You can now test these properties:');
    for (const parcelId of testParcels) {
      console.log(`  http://localhost:5175/property/${parcelId}`);
    }
    
    console.log('\n💡 NEXT STEPS:');
    console.log('1. The Core Property Info tab should now show data');
    console.log('2. To enable other tabs, run create_all_tables.sql in Supabase SQL editor');
    console.log('3. Then run this script again to populate sales history and other data');
    
  } catch (e) {
    console.error('\n❌ Error:', e);
  }
}

// Run the function
populateSimpleData().then(() => {
  console.log('\n✅ Script completed');
  process.exit(0);
}).catch(error => {
  console.error('\n❌ Script failed:', error);
  process.exit(1);
});