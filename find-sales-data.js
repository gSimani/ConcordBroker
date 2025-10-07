import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '.env' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase configuration');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function findSalesData() {
  const parcelId = '06-18-24-0350-000-34900';
  console.log('🔍 Searching for sales data for parcel:', parcelId);
  console.log('=' .repeat(60));

  // Check property_sales_history table
  console.log('\n1️⃣ Checking property_sales_history table...');
  const { data: propSales, error: propError } = await supabase
    .from('property_sales_history')
    .select('*')
    .eq('parcel_id', parcelId)
    .order('sale_date', { ascending: false });

  console.log(`Found: ${propSales?.length || 0} records`);
  if (propError) console.log('Error:', propError.message);

  if (propSales?.length > 0) {
    console.log('\n📊 property_sales_history data:');
    propSales.forEach(sale => {
      const date = new Date(sale.sale_date).toLocaleDateString();
      const price = sale.sale_price > 0 ? `$${sale.sale_price.toLocaleString()}` : '$0';
      const bookPage = sale.or_book && sale.or_page ? `${sale.or_book}-${sale.or_page}` : 'N/A';
      console.log(`  ${date}: ${price} [${bookPage}] ${sale.quality_code || sale.verification_code}`);
    });
  }

  // Check fl_sdf_sales table
  console.log('\n2️⃣ Checking fl_sdf_sales table...');
  const { data: sdfSales, error: sdfError } = await supabase
    .from('fl_sdf_sales')
    .select('*')
    .eq('parcel_id', parcelId)
    .order('sale_date', { ascending: false });

  console.log(`Found: ${sdfSales?.length || 0} records`);
  if (sdfError) console.log('Error:', sdfError.message);

  if (sdfSales?.length > 0) {
    console.log('\n📊 fl_sdf_sales data:');
    sdfSales.forEach(sale => {
      const date = new Date(sale.sale_date).toLocaleDateString();
      const price = sale.sale_price > 0 ? `$${sale.sale_price.toLocaleString()}` : '$0';
      const bookPage = sale.or_book && sale.or_page ? `${sale.or_book}-${sale.or_page}` : 'N/A';
      console.log(`  ${date}: ${price} [${bookPage}] ${sale.qual_cd}`);
    });
  }

  // Check florida_parcels for sale_date/sale_price
  console.log('\n3️⃣ Checking florida_parcels table...');
  const { data: flParcels, error: flError } = await supabase
    .from('florida_parcels')
    .select('parcel_id, sale_date, sale_price, sale_qualification, county')
    .eq('parcel_id', parcelId);

  console.log(`Found: ${flParcels?.length || 0} records`);
  if (flError) console.log('Error:', flError.message);

  if (flParcels?.length > 0) {
    console.log('\n📊 florida_parcels data:');
    flParcels.forEach(parcel => {
      if (parcel.sale_date && parcel.sale_price) {
        const date = new Date(parcel.sale_date).toLocaleDateString();
        const price = parcel.sale_price > 0 ? `$${parcel.sale_price.toLocaleString()}` : '$0';
        console.log(`  ${date}: ${price} [${parcel.sale_qualification}] County: ${parcel.county}`);
      }
    });
  }

  // Check for similar parcel IDs (in case of formatting differences)
  console.log('\n4️⃣ Checking for similar parcel IDs...');
  const { data: similarParcels, error: similarError } = await supabase
    .from('property_sales_history')
    .select('parcel_id')
    .like('parcel_id', '%0350%')
    .limit(10);

  if (similarParcels?.length > 0) {
    console.log('Similar parcel IDs found:');
    similarParcels.forEach(p => console.log(`  ${p.parcel_id}`));
  }

  console.log('\n' + '=' .repeat(60));
  console.log('Search complete!');
}

findSalesData().catch(console.error);