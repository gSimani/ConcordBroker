// Simple API endpoint test without browser
// Using built-in fetch (Node.js 18+)

async function testAPIEndpoints() {
    console.log('🔍 Testing API Endpoints for Property: 12681 NW 78 MNR, Parkland');
    console.log('='.repeat(60));
    
    const baseURL = 'http://localhost:8000';
    const parcelId = '474131031040'; // From the logs
    
    const endpoints = [
        {
            name: 'Root API',
            url: `${baseURL}/`,
            method: 'GET'
        },
        {
            name: 'API Docs',
            url: `${baseURL}/docs`,
            method: 'GET'
        },
        {
            name: 'Parcel Data',
            url: `${baseURL}/api/parcels/${parcelId}`,
            method: 'GET'
        },
        {
            name: 'Sales Data',
            url: `${baseURL}/api/sales/${parcelId}`,
            method: 'GET'
        },
        {
            name: 'Property Search - General',
            url: `${baseURL}/api/properties/search?limit=10`,
            method: 'GET'
        },
        {
            name: 'Property Search - Parkland',
            url: `${baseURL}/api/properties/search?city=Parkland&limit=10`,
            method: 'GET'
        },
        {
            name: 'Property Search - Address',
            url: `${baseURL}/api/properties/search?address=12681+nw+78+mnr&limit=10`,
            method: 'GET'
        },
        {
            name: 'Properties Stats',
            url: `${baseURL}/api/properties/stats/overview`,
            method: 'GET'
        }
    ];
    
    const results = [];
    
    for (const endpoint of endpoints) {
        try {
            console.log(`\n🌐 Testing: ${endpoint.name}`);
            console.log(`   URL: ${endpoint.url}`);
            
            const startTime = Date.now();
            const response = await fetch(endpoint.url, {
                method: endpoint.method,
                headers: {
                    'Accept': 'application/json',
                    'User-Agent': 'API-Diagnostic-Test/1.0'
                }
            });
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            const result = {
                name: endpoint.name,
                url: endpoint.url,
                status: response.status,
                statusText: response.statusText,
                duration: duration,
                success: response.ok,
                headers: Object.fromEntries(response.headers.entries())
            };
            
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    try {
                        const data = await response.json();
                        result.data = data;
                        result.dataSize = JSON.stringify(data).length;
                        
                        // Analyze the data
                        if (Array.isArray(data)) {
                            result.recordCount = data.length;
                        } else if (typeof data === 'object' && data !== null) {
                            result.hasData = Object.keys(data).length > 0;
                        }
                        
                        console.log(`   ✅ SUCCESS (${response.status}) - ${duration}ms`);
                        if (result.recordCount !== undefined) {
                            console.log(`   📊 Records: ${result.recordCount}`);
                        }
                        if (result.dataSize) {
                            console.log(`   💾 Data size: ${result.dataSize} bytes`);
                        }
                    } catch (jsonError) {
                        result.jsonError = jsonError.message;
                        console.log(`   ⚠️ SUCCESS but JSON parse failed: ${jsonError.message}`);
                    }
                } else {
                    console.log(`   ✅ SUCCESS (${response.status}) - ${duration}ms - Non-JSON response`);
                }
            } else {
                try {
                    const errorData = await response.text();
                    result.errorData = errorData;
                    console.log(`   ❌ FAILED (${response.status}) - ${response.statusText} - ${duration}ms`);
                    console.log(`   🔍 Error: ${errorData.substring(0, 200)}${errorData.length > 200 ? '...' : ''}`);
                } catch (textError) {
                    console.log(`   ❌ FAILED (${response.status}) - ${response.statusText} - ${duration}ms`);
                    console.log(`   🔍 Could not read error data: ${textError.message}`);
                }
            }
            
            results.push(result);
            
        } catch (error) {
            console.log(`   💥 NETWORK ERROR: ${error.message}`);
            results.push({
                name: endpoint.name,
                url: endpoint.url,
                error: error.message,
                success: false
            });
        }
    }
    
    // Generate summary report
    console.log('\n📊 SUMMARY REPORT');
    console.log('='.repeat(60));
    
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    console.log(`✅ Successful: ${successful.length}/${results.length}`);
    console.log(`❌ Failed: ${failed.length}/${results.length}`);
    
    if (failed.length > 0) {
        console.log('\n❌ FAILED ENDPOINTS:');
        failed.forEach(result => {
            console.log(`   • ${result.name}: ${result.status || 'Network Error'} - ${result.error || result.statusText}`);
        });
    }
    
    // Check specific issues
    const parcelResult = results.find(r => r.name === 'Parcel Data');
    const salesResult = results.find(r => r.name === 'Sales Data');
    
    console.log('\n🔍 SPECIFIC PROPERTY ANALYSIS:');
    console.log(`Parcel ID: ${parcelId} (12681 NW 78 MNR, Parkland)`);
    
    if (parcelResult) {
        if (parcelResult.success && parcelResult.data) {
            console.log(`✅ Parcel data found: ${JSON.stringify(parcelResult.data).length} bytes`);
        } else if (parcelResult.status === 404) {
            console.log(`❌ Parcel not found in database (404)`);
        } else {
            console.log(`❌ Parcel fetch failed: ${parcelResult.status} ${parcelResult.statusText}`);
        }
    }
    
    if (salesResult) {
        if (salesResult.success && salesResult.data) {
            console.log(`✅ Sales data found: ${JSON.stringify(salesResult.data).length} bytes`);
        } else if (salesResult.status === 404) {
            console.log(`❌ Sales data not found in database (404)`);
        } else {
            console.log(`❌ Sales fetch failed: ${salesResult.status} ${salesResult.statusText}`);
        }
    }
    
    // Check if general search works
    const generalSearch = results.find(r => r.name === 'Property Search - General');
    if (generalSearch && generalSearch.success) {
        console.log(`✅ General property search works (${generalSearch.recordCount || 0} properties)`);
    }
    
    const parklandSearch = results.find(r => r.name === 'Property Search - Parkland');
    if (parklandSearch && parklandSearch.success) {
        console.log(`✅ Parkland property search works (${parklandSearch.recordCount || 0} properties)`);
    }
    
    const addressSearch = results.find(r => r.name === 'Property Search - Address');
    if (addressSearch && addressSearch.success) {
        console.log(`✅ Address search works (${addressSearch.recordCount || 0} properties)`);
    }
    
    console.log('\n💡 DIAGNOSIS:');
    console.log('='.repeat(60));
    
    if (parcelResult && parcelResult.status === 404) {
        console.log('🎯 ROOT CAUSE: The specific parcel ID (474131031040) does not exist in the database');
        console.log('   This means either:');
        console.log('   1. The property data was never imported');
        console.log('   2. The property exists but with a different parcel ID');
        console.log('   3. The address-to-parcel-ID mapping is incorrect');
    }
    
    if (generalSearch && generalSearch.success && generalSearch.recordCount > 0) {
        console.log('✅ Database connectivity is working (other properties can be found)');
    } else {
        console.log('❌ Database connectivity issues detected');
    }
    
    console.log('\n🛠️ RECOMMENDED ACTIONS:');
    console.log('1. Check if property exists in database with different parcel ID');
    console.log('2. Verify the address parsing logic');
    console.log('3. Check if Broward County parcel data includes this property');
    console.log('4. Verify the property address format and spelling');
    
    return results;
}

// Run the test
console.log('🧪 API Endpoint Diagnostic Test');
console.log('Starting comprehensive API testing...\n');

testAPIEndpoints()
    .then(results => {
        console.log('\n✅ Test completed successfully');
    })
    .catch(error => {
        console.error('❌ Test failed:', error.message);
    });