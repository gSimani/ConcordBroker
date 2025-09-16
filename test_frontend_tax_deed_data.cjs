const { createClient } = require('@supabase/supabase-js');

// Supabase configuration
const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

async function testFrontendDataFlow() {
    console.log('🔍 Testing Tax Deed Frontend Data Flow...\n');
    
    // Initialize Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
    
    try {
        // Test 1: Try the exact query the component uses
        console.log('=== Test 1: Component Query (tax_deed_bidding_items) ===');
        
        let query = supabase
            .from('tax_deed_bidding_items')
            .select('*')
            .order('created_at', { ascending: false })
            .limit(100);

        const { data, error } = await query;
        
        if (error) {
            console.error('❌ Query Error:', error);
            return;
        }
        
        console.log(`✅ Query successful: ${data.length} records returned`);
        
        // Apply the same mapping the component does
        const mappedData = data.map(item => ({
            id: item.id,
            composite_key: `${item.tax_deed_number}_${item.parcel_id}`,
            auction_id: item.auction_id,
            tax_deed_number: item.tax_deed_number,
            parcel_number: item.parcel_id,
            parcel_url: `https://web.bcpa.net/BcpaClient/#/Record/${item.parcel_id}`,
            tax_certificate_number: item.tax_certificate_number,
            legal_description: item.legal_situs_address || '',
            situs_address: item.legal_situs_address || '',
            city: 'Fort Lauderdale',
            state: 'FL',
            zip_code: '',
            homestead: item.homestead_exemption === 'Y',
            assessed_value: item.assessed_value,
            opening_bid: item.opening_bid || 0,
            best_bid: item.current_bid,
            winning_bid: item.winning_bid,
            winner_name: item.applicant_name,
            close_time: item.close_time,
            status: item.item_status || 'Active',
            applicant: item.applicant_name || '',
            applicant_companies: [],
            gis_map_url: `https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id=${item.parcel_id}`,
            sunbiz_matched: false,
            sunbiz_entity_names: [],
            sunbiz_entity_ids: [],
            auction_date: item.auction_date || item.created_at,
            auction_description: item.auction_description || 'Tax Deed Sale'
        }));
        
        console.log(`✅ Mapped data: ${mappedData.length} items`);
        
        // Test 2: Apply frontend filtering logic
        console.log('\n=== Test 2: Frontend Filtering Analysis ===');
        
        // Simulate the 3 different tabs
        const now = new Date();
        
        // Upcoming filter (like the component does)
        const upcomingFiltered = mappedData.filter(p => {
            if (p.close_time) {
                return new Date(p.close_time) > now;
            }
            return p.status === 'Active' || p.status === 'Upcoming';
        });
        
        // Past filter
        const pastFiltered = mappedData.filter(p => {
            if (p.close_time) {
                return new Date(p.close_time) <= now;
            }
            return p.status === 'Sold' || p.status === 'Closed' || p.status === 'Past';
        });
        
        // Cancelled filter
        const cancelledFiltered = mappedData.filter(p => 
            p.status === 'Cancelled' || p.status === 'Canceled' || p.status === 'Removed'
        );
        
        console.log(`📊 Filtering Results:`);
        console.log(`   Total items: ${mappedData.length}`);
        console.log(`   Upcoming: ${upcomingFiltered.length}`);
        console.log(`   Past: ${pastFiltered.length}`);
        console.log(`   Cancelled: ${cancelledFiltered.length}`);
        
        // Test 3: Analyze why only 8 items show
        console.log('\n=== Test 3: Debugging "Only 8 Items" Issue ===');
        
        // Check for items with missing addresses
        const withAddress = upcomingFiltered.filter(p => 
            p.legal_description && 
            p.legal_description !== 'Address not available' &&
            !p.parcel_number.startsWith('UNKNOWN')
        );
        
        const withoutAddress = upcomingFiltered.filter(p => 
            !p.legal_description || 
            p.legal_description === 'Address not available' ||
            p.parcel_number.startsWith('UNKNOWN')
        );
        
        console.log(`📍 Address Analysis:`);
        console.log(`   Upcoming with valid address: ${withAddress.length}`);
        console.log(`   Upcoming without address: ${withoutAddress.length}`);
        
        // Show sample items that should be visible
        console.log('\n=== Sample Upcoming Items (should be visible) ===');
        withAddress.slice(0, 8).forEach((item, i) => {
            console.log(`${i + 1}. ${item.tax_deed_number} - ${item.situs_address}`);
            console.log(`   Status: ${item.status}, Close: ${item.close_time}`);
            console.log(`   Bid: $${item.opening_bid}, Parcel: ${item.parcel_number}`);
        });
        
        // Test 4: Check if there's an API endpoint being used instead
        console.log('\n=== Test 4: API vs Direct Query Comparison ===');
        
        const analysis = {
            timestamp: new Date().toISOString(),
            source: 'tax_deed_bidding_items',
            total_in_db: mappedData.length,
            frontend_filters: {
                upcoming: upcomingFiltered.length,
                past: pastFiltered.length,
                cancelled: cancelledFiltered.length
            },
            address_analysis: {
                upcoming_with_address: withAddress.length,
                upcoming_without_address: withoutAddress.length
            },
            sample_items: withAddress.slice(0, 8).map(item => ({
                tax_deed_number: item.tax_deed_number,
                address: item.situs_address,
                status: item.status,
                parcel: item.parcel_number,
                opening_bid: item.opening_bid,
                close_time: item.close_time
            })),
            findings: {
                expected_on_website: withAddress.length,
                actual_on_website: 8, // From original report
                potential_issues: [
                    withAddress.length < 8 ? 'Database has fewer valid items than website shows' : 'Database has more valid items than website shows',
                    withoutAddress.length > 0 ? `${withoutAddress.length} items have invalid addresses/parcels` : 'All items have valid addresses',
                    'Frontend may be using different query or filters',
                    'There may be additional client-side filtering'
                ]
            }
        };
        
        // Save results
        const fs = require('fs');
        fs.writeFileSync('frontend_data_flow_analysis.json', JSON.stringify(analysis, null, 2));
        
        console.log('\n=== CONCLUSION ===');
        console.log(`✅ Database contains ${mappedData.length} total tax deed items`);
        console.log(`📊 Frontend should show ${withAddress.length} upcoming items`);
        console.log(`🔍 Website currently shows 8 items`);
        console.log(`${withAddress.length === 8 ? '✅' : '❌'} Database matches website count`);
        
        if (withAddress.length !== 8) {
            console.log(`\n🚨 MISMATCH DETECTED:`);
            console.log(`   Database has ${withAddress.length} valid upcoming items`);
            console.log(`   Website displays 8 items`);
            console.log(`   Difference: ${withAddress.length - 8} items`);
        }
        
        return analysis;
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        return null;
    }
}

// Run the test
testFrontendDataFlow()
    .then(result => {
        console.log('\n📝 Results saved to: frontend_data_flow_analysis.json');
        process.exit(0);
    })
    .catch(error => {
        console.error('💥 Test failed:', error);
        process.exit(1);
    });