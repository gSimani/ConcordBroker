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

// Sales data for property 06-18-24-0350-000-34900 based on user's requirements
const salesData = [
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32', // Lake County
    sale_year: 2022,
    sale_month: 11,
    sale_day: 7,
    sale_price: 100,
    or_book: '33460',
    or_page: '3479',
    quality_code: 'U', // Unqualified - Corrective, tax or QCD
    verification_code: 'QCD',
    grantor_name: 'OSLAIDA VALIDO',
    grantee_name: 'Unknown',
    deed_type: 'Quit Claim Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32', // Lake County
    sale_year: 2004,
    sale_month: 1,
    sale_day: 1,
    sale_price: 221500,
    or_book: '21980',
    or_page: '4453',
    quality_code: 'Q', // Qualified
    verification_code: 'WD',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Warranty Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 2000,
    sale_month: 3,
    sale_day: 1,
    sale_price: 141000,
    or_book: '19028',
    or_page: '4223',
    quality_code: 'Q', // Qualified
    verification_code: 'WD',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Warranty Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 1993,
    sale_month: 5,
    sale_day: 1,
    sale_price: 0,
    or_book: '15921',
    or_page: '2995',
    quality_code: 'U', // Unqualified
    verification_code: 'U',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Unknown'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 1984,
    sale_month: 2,
    sale_day: 1,
    sale_price: 65000,
    or_book: '12076',
    or_page: '3156',
    quality_code: 'Q', // Qualified
    verification_code: 'WD',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Warranty Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 1982,
    sale_month: 8,
    sale_day: 1,
    sale_price: 65000,
    or_book: '11517',
    or_page: '2015',
    quality_code: 'Q', // Qualified
    verification_code: 'WD',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Warranty Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 1981,
    sale_month: 4,
    sale_day: 1,
    sale_price: 50000,
    or_book: '11066',
    or_page: '2024',
    quality_code: 'Q', // Qualified
    verification_code: 'WD',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Warranty Deed'
  },
  {
    parcel_id: '06-18-24-0350-000-34900',
    county_no: '32',
    sale_year: 2000,
    sale_month: 4,
    sale_day: 1,
    sale_price: 0,
    or_book: '00000',
    or_page: '00000',
    quality_code: 'U', // Unqualified
    verification_code: 'U',
    grantor_name: 'Unknown',
    grantee_name: 'Unknown',
    deed_type: 'Unknown'
  }
];

async function importSalesData() {
  console.log('🚀 Starting sales history import for 06-18-24-0350-000-34900...');
  console.log('=' .repeat(70));

  try {
    // Import the sales data
    console.log('\n📝 Importing 8 sales records...');

    for (const sale of salesData) {
      try {
        // Create sale_date from year/month/day
        const saleDate = `${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}-${String(sale.sale_day).padStart(2, '0')}`;

        const salesRecord = {
          parcel_id: sale.parcel_id,
          county_no: sale.county_no,
          sale_year: sale.sale_year,
          sale_month: sale.sale_month,
          sale_price: sale.sale_price,
          or_book: sale.or_book,
          or_page: sale.or_page,
          quality_code: sale.quality_code,
          verification_code: sale.verification_code
        };

        const { data, error } = await supabase
          .from('property_sales_history')
          .insert(salesRecord)
          .select();

        if (error) {
          console.error(`❌ Error inserting sale from ${saleDate}:`, error.message);
        } else {
          const price = sale.sale_price > 0 ? `$${sale.sale_price.toLocaleString()}` : '$0';
          const bookPage = `${sale.or_book}-${sale.or_page}`;
          console.log(`✅ Imported ${saleDate}: ${price} [${bookPage}] ${sale.quality_code}`);
        }
      } catch (err) {
        console.error(`❌ Failed to insert sale from ${sale.sale_year}:`, err);
      }
    }

    // Verify the import
    console.log('\n🔍 Verifying import...');
    const { data: verifyData, error: verifyError } = await supabase
      .from('property_sales_history')
      .select('*')
      .eq('parcel_id', '06-18-24-0350-000-34900')
      .order('sale_date', { ascending: false });

    if (!verifyError && verifyData) {
      console.log(`\n✅ SUCCESS! Imported ${verifyData.length} sales records`);
      console.log('\nSales History for 06-18-24-0350-000-34900:');
      verifyData.forEach(sale => {
        const date = new Date(sale.sale_date).toLocaleDateString();
        const price = sale.sale_price > 0 ? `$${sale.sale_price.toLocaleString()}` : '$0';
        const bookPage = sale.or_book && sale.or_page ? `${sale.or_book}-${sale.or_page}` : 'N/A';
        const qualified = sale.quality_code === 'Q' ? '✓ Qualified' : '✗ Unqualified';
        const grantor = sale.grantor_name && sale.grantor_name !== 'Unknown' ? ` from ${sale.grantor_name}` : '';
        console.log(`  ${date}: ${price} [${bookPage}] ${qualified}${grantor}`);
      });
    } else if (verifyError) {
      console.error('❌ Verification failed:', verifyError.message);
    }

    // Update the florida_parcels table with the most recent qualified sale
    const mostRecentQualifiedSale = salesData
      .filter(s => s.quality_code === 'Q' && s.sale_price > 0)
      .sort((a, b) => {
        const dateA = new Date(a.sale_year, a.sale_month - 1, a.sale_day || 1);
        const dateB = new Date(b.sale_year, b.sale_month - 1, b.sale_day || 1);
        return dateB.getTime() - dateA.getTime();
      })[0];

    if (mostRecentQualifiedSale) {
      console.log('\n📊 Updating florida_parcels with most recent qualified sale...');
      const saleDate = `${mostRecentQualifiedSale.sale_year}-${String(mostRecentQualifiedSale.sale_month).padStart(2, '0')}-${String(mostRecentQualifiedSale.sale_day || 1).padStart(2, '0')}T00:00:00`;

      const { error: updateError } = await supabase
        .from('florida_parcels')
        .update({
          sale_date: saleDate,
          sale_price: mostRecentQualifiedSale.sale_price,
          sale_qualification: mostRecentQualifiedSale.quality_code
        })
        .eq('parcel_id', '06-18-24-0350-000-34900');

      if (updateError) {
        console.error('❌ Failed to update florida_parcels:', updateError.message);
      } else {
        console.log('✅ Updated florida_parcels with most recent qualified sale');
        console.log(`   ${saleDate.split('T')[0]}: $${mostRecentQualifiedSale.sale_price.toLocaleString()}`);
      }
    }

  } catch (error) {
    console.error('❌ Import failed:', error);
  }

  console.log('\n' + '=' .repeat(70));
  console.log('Import process complete!');
}

// Run the import
importSalesData().catch(console.error);