import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: 'apps/web/.env' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

async function verifyRealSalesData() {
  console.log('========================================');
  console.log('VERIFYING ACTUAL SALES DATA IN DATABASE');
  console.log('========================================\n');

  // Check property_sales_history for our test property
  console.log('Checking property_sales_history for 514124070600...\n');

  const { data: salesData, error } = await supabase
    .from('property_sales_history')
    .select('*')
    .eq('parcel_id', '514124070600')
    .order('sale_year', { ascending: false });

  if (error) {
    console.error('Error:', error);
    return;
  }

  if (salesData && salesData.length > 0) {
    console.log(`✅ FOUND ${salesData.length} SALES RECORDS:\n`);
    salesData.forEach((sale, index) => {
      console.log(`Sale #${index + 1}:`);
      console.log(`  Date: ${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')} (Generated: ${sale.sale_date})`);
      console.log(`  Price: $${sale.sale_price?.toLocaleString()}`);
      console.log(`  Book/Page: ${sale.or_book} / ${sale.or_page}`);
      console.log(`  Quality Code: ${sale.quality_code}`);
      console.log(`  Verification: ${sale.verification_code}`);
      console.log(`  County: ${sale.county_no}`);
      console.log('---');
    });
  } else {
    console.log('❌ No sales found for this property');
  }

  // Now let's find properties that DO have real sales data
  console.log('\n========================================');
  console.log('FINDING PROPERTIES WITH REAL SALES DATA');
  console.log('========================================\n');

  // Get a sample of properties with multiple sales
  const { data: propertiesWithSales, error: propError } = await supabase
    .from('property_sales_history')
    .select('parcel_id')
    .gte('sale_price', 100000)
    .eq('quality_code', 'Q')
    .limit(100);

  if (!propError && propertiesWithSales) {
    // Count sales per property
    const propertyCounts = {};
    propertiesWithSales.forEach(record => {
      propertyCounts[record.parcel_id] = (propertyCounts[record.parcel_id] || 0) + 1;
    });

    // Find properties with multiple sales
    const multiSaleProperties = Object.entries(propertyCounts)
      .filter(([_, count]) => count >= 3)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    console.log('TOP PROPERTIES WITH MULTIPLE SALES:\n');

    for (const [parcelId, count] of multiSaleProperties) {
      console.log(`\n📍 Parcel ID: ${parcelId} (${count} sales)`);

      // Get property details from florida_parcels
      const { data: propertyInfo } = await supabase
        .from('florida_parcels')
        .select('phy_addr1, phy_city, county, owner_name')
        .eq('parcel_id', parcelId)
        .single();

      if (propertyInfo) {
        console.log(`   Address: ${propertyInfo.phy_addr1}, ${propertyInfo.phy_city}`);
        console.log(`   County: ${propertyInfo.county}`);
        console.log(`   Owner: ${propertyInfo.owner_name}`);
      }

      // Get recent sales
      const { data: recentSales } = await supabase
        .from('property_sales_history')
        .select('sale_year, sale_month, sale_price, verification_code')
        .eq('parcel_id', parcelId)
        .order('sale_year', { ascending: false })
        .limit(3);

      if (recentSales) {
        console.log('   Recent Sales:');
        recentSales.forEach(sale => {
          console.log(`     - ${sale.sale_year}: $${sale.sale_price?.toLocaleString()} (${sale.verification_code})`);
        });
      }
    }
  }

  console.log('\n\n💡 RECOMMENDATION:');
  console.log('Use one of the properties listed above to test the Sales History display,');
  console.log('as they have real, existing sales data in the database.');
}

verifyRealSalesData();