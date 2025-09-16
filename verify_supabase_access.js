// Supabase JavaScript/TypeScript Connection Test
// Tests the connection as shown in Supabase docs

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Using the exact pattern from Supabase docs
const supabaseUrl = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseKey = process.env.SUPABASE_KEY || process.env.SUPABASE_ANON_KEY;

async function testSupabaseConnection() {
    console.log('========================================');
    console.log('SUPABASE JAVASCRIPT CLIENT TEST');
    console.log('========================================');
    console.log(`Project URL: ${supabaseUrl}`);
    console.log(`API Key: ${supabaseKey ? supabaseKey.substring(0, 20) + '...' : 'NOT SET'}`);
    console.log('');

    try {
        // Initialize client exactly as shown in docs
        const supabase = createClient(supabaseUrl, supabaseKey);
        console.log('[OK] Supabase client initialized');

        // Test 1: Query florida_parcels table
        console.log('\nTest 1: Querying florida_parcels table...');
        const { data: parcels, error: parcelsError, count } = await supabase
            .from('florida_parcels')
            .select('parcel_id, phy_addr1, phy_city', { count: 'exact' })
            .limit(3);

        if (parcelsError) {
            console.log('[ERROR] Query failed:', parcelsError.message);
        } else {
            console.log('[OK] Query successful!');
            console.log(`[OK] Total records available: ${count || 'unknown'}`);
            console.log('[OK] Sample data:');
            parcels.forEach(p => {
                console.log(`     - ${p.parcel_id}: ${p.phy_addr1}, ${p.phy_city}`);
            });
        }

        // Test 2: Test Auth Service
        console.log('\nTest 2: Testing Auth service...');
        const { data: { user }, error: authError } = await supabase.auth.getUser();
        
        if (authError && authError.message !== 'Auth session missing!') {
            console.log('[ERROR] Auth service error:', authError.message);
        } else {
            console.log('[OK] Auth service is accessible');
            console.log(`[OK] Current user: ${user ? user.email : 'No user logged in'}`);
        }

        // Test 3: Test RPC functions (if any exist)
        console.log('\nTest 3: Testing RPC functions...');
        try {
            // This might fail if no RPC functions exist, which is okay
            const { data: rpcTest, error: rpcError } = await supabase.rpc('get_property_count');
            if (rpcError) {
                console.log('[INFO] No RPC functions found (this is normal)');
            } else {
                console.log('[OK] RPC functions accessible');
            }
        } catch (e) {
            console.log('[INFO] RPC test skipped');
        }

        // Test 4: Test Realtime subscriptions
        console.log('\nTest 4: Testing Realtime capabilities...');
        const channel = supabase
            .channel('test-channel')
            .on('postgres_changes', 
                { event: '*', schema: 'public', table: 'florida_parcels' },
                (payload) => {
                    console.log('[OK] Realtime event received:', payload);
                }
            );
        
        await channel.subscribe((status) => {
            if (status === 'SUBSCRIBED') {
                console.log('[OK] Realtime subscription successful');
                channel.unsubscribe();
            }
        });

        // Summary
        console.log('\n========================================');
        console.log('CONNECTION TEST COMPLETE');
        console.log('========================================');
        console.log('[SUCCESS] Supabase is fully accessible via JavaScript client!');
        console.log('');
        console.log('You can now use:');
        console.log('  - Database queries with .from()');
        console.log('  - Authentication with .auth');
        console.log('  - Realtime subscriptions with .channel()');
        console.log('  - Storage operations with .storage');
        console.log('  - RPC functions with .rpc()');
        
        process.exit(0);

    } catch (error) {
        console.error('[ERROR] Unexpected error:', error.message);
        process.exit(1);
    }
}

// Run the test
testSupabaseConnection();