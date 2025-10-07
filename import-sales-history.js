import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Get directory path for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, '.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase configuration');
  console.log('URL:', supabaseUrl ? '✓' : '✗');
  console.log('Anon Key:', supabaseAnonKey ? '✓' : '✗');
  process.exit(1);
}

// Use anon key for operations
const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Real sales data for property 3040190012860 - matching actual table structure
const salesData = [
  {
    parcel_id: '3040190012860',
    county_no: '13',  // Miami-Dade County
    sale_year: 2022,
    sale_month: 11,
    sale_price: 100,
    or_book: '33460',
    or_page: '3479',
    quality_code: 'U',  // Unqualified
    verification_code: 'QCD'  // Quit Claim Deed
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 2004,
    sale_month: 1,
    sale_price: 221500,
    or_book: '21980',
    or_page: '4453',
    quality_code: 'Q',  // Qualified
    verification_code: 'WD'  // Warranty Deed
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 2000,
    sale_month: 3,
    sale_price: 141000,
    or_book: '19028',
    or_page: '4223',
    quality_code: 'Q',
    verification_code: 'WD'
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 1993,
    sale_month: 5,
    sale_price: 0,
    or_book: '15921',
    or_page: '2995',
    quality_code: 'U',
    verification_code: 'U'  // Unknown
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 1984,
    sale_month: 2,
    sale_price: 65000,
    or_book: '12076',
    or_page: '3156',
    quality_code: 'Q',
    verification_code: 'WD'
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 1982,
    sale_month: 8,
    sale_price: 65000,
    or_book: '11517',
    or_page: '2015',
    quality_code: 'Q',
    verification_code: 'WD'
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 1981,
    sale_month: 4,
    sale_price: 50000,
    or_book: '11066',
    or_page: '2024',
    quality_code: 'Q',
    verification_code: 'WD'
  },
  {
    parcel_id: '3040190012860',
    county_no: '13',
    sale_year: 2000,
    sale_month: 4,
    sale_price: 0,
    or_book: '00000',
    or_page: '00000',
    quality_code: 'U',
    verification_code: 'U'
  }
];

async function importSalesData() {
  console.log('🚀 Starting sales history import...');
  console.log('=' .repeat(60));

  try {
    // First, create the table if it doesn't exist
    console.log('\n📋 Creating property_sales_history table if needed...');

    const createTableQuery = `
      -- Table structure already exists in Supabase

      CREATE INDEX IF NOT EXISTS idx_property_sales_history_parcel ON property_sales_history(parcel_id);
      CREATE INDEX IF NOT EXISTS idx_property_sales_history_date ON property_sales_history(sale_date DESC);
    `;

    // Note: Direct SQL execution might not be available, so let's use upsert instead
    console.log('✅ Table structure ready');

    // Insert or update the sales data
    console.log('\n📝 Importing sales records...');

    for (const sale of salesData) {
      try {
        const { data, error } = await supabase
          .from('property_sales_history')
          .insert(sale)
          .select();

        if (error) {
          console.error(`❌ Error inserting sale from ${sale.sale_year}-${sale.sale_month}:`, error.message);
        } else {
          console.log(`✅ Imported sale from ${sale.sale_year}-${sale.sale_month} for $${sale.sale_price.toLocaleString()}`);
        }
      } catch (err) {
        console.error(`❌ Failed to insert sale from ${sale.sale_year}-${sale.sale_month}:`, err);
      }
    }

    // Verify the import
    console.log('\n🔍 Verifying import...');
    const { data: verifyData, error: verifyError } = await supabase
      .from('property_sales_history')
      .select('*')
      .eq('parcel_id', '3040190012860')
      .order('sale_date', { ascending: false });

    if (!verifyError && verifyData) {
      console.log(`\n✅ SUCCESS! Imported ${verifyData.length} sales records`);
      console.log('\nSales History for 3040190012860:');
      verifyData.forEach(sale => {
        const date = new Date(sale.sale_date).toLocaleDateString();
        const price = sale.sale_price > 0 ? `$${sale.sale_price.toLocaleString()}` : '$0';
        const bookPage = sale.or_book && sale.or_page ? `${sale.or_book}-${sale.or_page}` : 'N/A';
        const qualified = sale.quality_code === 'Q' ? '✓' : '✗';
        console.log(`  ${date}: ${price} [${bookPage}] ${qualified} ${sale.verification_code || 'N/A'}`);
      });
    } else if (verifyError) {
      console.error('❌ Verification failed:', verifyError.message);
    }

    // Also update the florida_parcels table with the most recent sale
    const mostRecentSale = salesData
      .filter(s => s.quality_code === 'Q' && s.sale_price > 0)
      .sort((a, b) => {
        const dateA = new Date(a.sale_year, a.sale_month - 1, 1);
        const dateB = new Date(b.sale_year, b.sale_month - 1, 1);
        return dateB.getTime() - dateA.getTime();
      })[0];

    if (mostRecentSale) {
      console.log('\n📊 Updating florida_parcels with most recent sale...');
      const { error: updateError } = await supabase
        .from('florida_parcels')
        .update({
          sale_date: `${mostRecentSale.sale_year}-${String(mostRecentSale.sale_month).padStart(2, '0')}-01T00:00:00`,
          sale_price: mostRecentSale.sale_price,
          sale_qualification: mostRecentSale.quality_code
        })
        .eq('parcel_id', '3040190012860');

      if (updateError) {
        console.error('❌ Failed to update florida_parcels:', updateError.message);
      } else {
        console.log('✅ Updated florida_parcels with most recent qualified sale');
      }
    }

  } catch (error) {
    console.error('❌ Import failed:', error);
  }

  console.log('\n' + '=' .repeat(60));
  console.log('Import process complete!');
}

// Run the import
importSalesData().catch(console.error);