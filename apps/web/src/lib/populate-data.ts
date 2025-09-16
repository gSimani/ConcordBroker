import { supabase } from './supabase';

export async function populateSampleData() {
  console.log('[INFO] Starting sample data population...');
  
  // Sample properties data
  const sampleProperties = [
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
    }
  ];
  
  // Populate florida_parcels table
  console.log('[1] Populating florida_parcels table...');
  for (const prop of sampleProperties) {
    try {
      // Check if record exists
      const { data: existing } = await supabase
        .from('florida_parcels')
        .select('parcel_id')
        .eq('parcel_id', prop.parcel_id)
        .single();
      
      if (existing) {
        // Update existing record
        const { error } = await supabase
          .from('florida_parcels')
          .update(prop)
          .eq('parcel_id', prop.parcel_id);
        
        if (error) throw error;
        console.log(`✓ Updated: ${prop.parcel_id} - ${prop.phy_addr1}`);
      } else {
        // Insert new record
        const { error } = await supabase
          .from('florida_parcels')
          .insert(prop);
        
        if (error) throw error;
        console.log(`✓ Inserted: ${prop.parcel_id} - ${prop.phy_addr1}`);
      }
    } catch (error: any) {
      console.error(`✗ Error with ${prop.parcel_id}:`, error.message);
    }
  }
  
  // Sample sales history data
  const sampleSales = [
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
    }
  ];
  
  console.log('[2] Populating property_sales_history table...');
  for (const sale of sampleSales) {
    try {
      const { error } = await supabase
        .from('property_sales_history')
        .insert(sale);
      
      if (error) {
        if (error.message.includes('does not exist')) {
          console.log('⚠ property_sales_history table does not exist - skipping sales data');
          break;
        }
        throw error;
      }
      console.log(`✓ Inserted sale: ${sale.sale_date} - $${sale.sale_price.toLocaleString()}`);
    } catch (error: any) {
      console.error('✗ Error inserting sale:', error.message);
    }
  }
  
  // Verify the data
  console.log('[3] Verifying inserted data...');
  try {
    const { data, error } = await supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, owner_name, taxable_value')
      .limit(5);
    
    if (error) throw error;
    
    if (data && data.length > 0) {
      console.log(`[SUCCESS] Found ${data.length} properties in database:`);
      data.forEach(prop => {
        console.log(`  - ${prop.parcel_id}: ${prop.phy_addr1} (Owner: ${prop.owner_name}, Value: $${(prop.taxable_value || 0).toLocaleString()})`);
      });
    } else {
      console.log('[WARNING] No data found after insertion');
    }
  } catch (error: any) {
    console.error('[ERROR] Could not verify data:', error.message);
  }
  
  console.log('\n[SUCCESS] Sample data population completed!');
  console.log('\nYou can now navigate to properties like:');
  console.log('  - http://localhost:5174/property/064210010010');
  console.log('  - http://localhost:5174/property/064210010011');
  console.log('  - http://localhost:5174/property/064210015020');
  
  return true;
}

// Export for use in browser console
if (typeof window !== 'undefined') {
  (window as any).populateSampleData = populateSampleData;
}