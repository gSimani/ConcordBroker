import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: '.env' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function checkTableStructure() {
  console.log('🔍 Checking property_sales_history table structure...\n');

  try {
    // Try to insert a minimal test record to see what columns exist
    const testRecord = {
      parcel_id: 'TEST123',
      sale_date: '2024-01-01',
      sale_price: 100000
    };

    const { data: insertData, error: insertError } = await supabase
      .from('property_sales_history')
      .insert(testRecord)
      .select();

    if (insertError) {
      console.log('⚠️ Insert failed, checking error for column info:');
      console.log(insertError.message);

      // Try with different column names
      const testRecord2 = {
        parcel_id: 'TEST123',
        sale_year: 2024,
        sale_month: 1,
        sale_price: 100000,
        or_book: '12345',
        or_page: '678',
        quality_code: 'Q',
        verification_code: 'WD'
      };

      const { data: insertData2, error: insertError2 } = await supabase
        .from('property_sales_history')
        .insert(testRecord2)
        .select();

      if (insertError2) {
        console.log('\n⚠️ Second insert failed:');
        console.log(insertError2.message);
      } else if (insertData2) {
        console.log('\n✅ Successfully inserted test record with columns:');
        const columns = Object.keys(insertData2[0]);
        columns.forEach(col => console.log(`  - ${col}`));

        // Clean up test record
        await supabase
          .from('property_sales_history')
          .delete()
          .eq('parcel_id', 'TEST123');
      }
    } else if (insertData) {
      console.log('✅ Successfully inserted test record with columns:');
      const columns = Object.keys(insertData[0]);
      columns.forEach(col => console.log(`  - ${col}`));

      // Clean up test record
      await supabase
        .from('property_sales_history')
        .delete()
        .eq('parcel_id', 'TEST123');
    }

  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

checkTableStructure().catch(console.error);