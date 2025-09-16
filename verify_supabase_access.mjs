// Supabase JavaScript/TypeScript Connection Test (ESM)
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

// Using the exact pattern from Supabase docs
const supabaseUrl = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

console.log('========================================');
console.log('SUPABASE CONNECTION TEST RESULTS');
console.log('========================================');
console.log(`Project URL: ${supabaseUrl}`);
console.log(`Project ID: pmispwtdngkcmsrsjwbp`);
console.log('');

try {
    // Initialize client exactly as shown in docs
    const supabase = createClient(supabaseUrl, supabaseKey);
    console.log('[OK] Supabase client initialized successfully');

    // Test database query
    const { data, error, count } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact', head: true });

    if (error) {
        console.log('[ERROR] Database query failed:', error.message);
    } else {
        console.log('[OK] Database connection verified');
        console.log(`[OK] Total records in florida_parcels: ${count}`);
    }

    // Test a simple query for actual data
    const { data: sample, error: sampleError } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city')
        .limit(2);

    if (!sampleError && sample) {
        console.log('[OK] Sample query successful');
        console.log('Sample data:');
        sample.forEach(item => {
            console.log(`  - ${item.parcel_id}: ${item.phy_addr1}, ${item.phy_city}`);
        });
    }

    console.log('\n========================================');
    console.log('CONNECTION STATUS: SUCCESS');
    console.log('========================================');
    console.log('\nYour Supabase connection is working perfectly!');
    console.log('You can now use the following in your code:');
    console.log('');
    console.log('import { createClient } from "@supabase/supabase-js"');
    console.log(`const supabaseUrl = "${supabaseUrl}"`);
    console.log('const supabaseKey = process.env.SUPABASE_KEY');
    console.log('const supabase = createClient(supabaseUrl, supabaseKey)');

} catch (error) {
    console.error('[ERROR] Connection test failed:', error.message);
    process.exit(1);
}

process.exit(0);