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
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function checkTableStructure() {
  console.log('🔍 Checking property_sales_history table structure...\n');

  try {
    // Try to get one record to see what columns exist
    const { data, error } = await supabase
      .from('property_sales_history')
      .select('*')
      .limit(1);

    if (error) {
      console.error('Error:', error);
      if (error.message.includes('does not exist')) {
        console.log('\n❌ Table property_sales_history does not exist!');
        console.log('Creating table...\n');

        // Since we can't run SQL directly, let's try to insert a dummy record
        // This will create the table if it doesn't exist
        const { error: insertError } = await supabase
          .from('property_sales_history')
          .insert({
            parcel_id: 'TEST_DELETE_ME',
            sale_date: '2000-01-01',
            sale_price: 0
          });

        if (insertError) {
          console.error('Failed to create table:', insertError);
        } else {
          console.log('✅ Table created successfully');
          // Delete the dummy record
          await supabase
            .from('property_sales_history')
            .delete()
            .eq('parcel_id', 'TEST_DELETE_ME');
        }
      }
      return;
    }

    if (data && data.length > 0) {
      console.log('✅ Table exists with columns:');
      const columns = Object.keys(data[0]);
      columns.forEach(col => console.log(`  - ${col}`));
    } else {
      console.log('✅ Table exists but is empty');

      // Try to insert a test record to discover columns
      const testRecord = {
        parcel_id: 'TEST123',
        sale_date: '2024-01-01',
        sale_price: 100000,
        or_book: '12345',
        or_page: '678',
        deed_type: 'Warranty Deed',
        sale_qualification: 'Qualified',
        qual_cd: 'Q',
        grantor_name: 'Test Seller',
        grantee_name: 'Test Buyer',
        is_qualified_sale: true
      };

      const { data: insertData, error: insertError } = await supabase
        .from('property_sales_history')
        .insert(testRecord)
        .select();

      if (insertError) {
        console.log('\n⚠️ Some columns may not exist:');
        console.log(insertError.message);
      } else if (insertData) {
        console.log('\n✅ Successfully inserted test record with columns:');
        const columns = Object.keys(insertData[0]);
        columns.forEach(col => console.log(`  - ${col}`));

        // Clean up test record
        await supabase
          .from('property_sales_history')
          .delete()
          .eq('parcel_id', 'TEST123');
      }
    }

  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

checkTableStructure().catch(console.error);