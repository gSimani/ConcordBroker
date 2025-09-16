const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Comprehensive Playwright test to verify that ConcordBroker is using live Supabase data only
 * Tests the property profile page and verifies no mock/hardcoded data is being used
 */

const MOCK_DATA_VALUES = [
  // Mock property IDs and addresses from mockProperties.ts
  '064210010010',
  '1234 Ocean Boulevard',
  'Ocean Properties LLC',
  '567 Las Olas Way', 
  'Las Olas Investments',
  // Other mock indicators
  'FL-0001',
  'FL-0002',
  'mockProperties',
  'DEMO_',
  'test-property'
];

const EXPECTED_SUPABASE_PATTERNS = [
  'supabase.co',
  'postgresql://',
  'rest/v1/',
  'auth/v1/',
  'storage/v1/'
];

async function runLiveDataVerification() {
    console.log('🔍 Starting Live Data Verification Test...\n');
    
    // Create test results directory
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const resultsDir = path.join(__dirname, 'test-results', `live-data-verification-${timestamp}`);
    if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
    }

    const browser = await chromium.launch({ 
        headless: false, // Set to true for CI environments
        devtools: true,  // Enable devtools for better network monitoring
        slowMo: 500      // Slow down actions for observation
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        recordVideo: {
            dir: resultsDir,
            size: { width: 1920, height: 1080 }
        }
    });
    
    const page = await context.newPage();
    
    // Arrays to collect findings
    const networkRequests = [];
    const consoleMessages = [];
    const errors = [];
    const findings = [];
    const supabaseQueries = [];
    const mockDataDetected = [];

    // Set up console monitoring for live data indicators
    page.on('console', (msg) => {
        const message = {
            type: msg.type(),
            text: msg.text(),
            timestamp: new Date().toISOString()
        };
        consoleMessages.push(message);
        
        // Check for live data indicators
        const text = msg.text().toLowerCase();
        if (text.includes('live') || text.includes('supabase') || text.includes('database')) {
            console.log(`📋 [${msg.type()}] Live Data Indicator: ${msg.text()}`);
            findings.push(`✅ Live data console message: ${msg.text()}`);
        }

        // Check for mock data indicators
        const mockIndicators = ['mock', 'demo', 'test data', 'hardcoded', 'placeholder'];
        if (mockIndicators.some(indicator => text.includes(indicator))) {
            console.log(`⚠️ [${msg.type()}] Mock Data Indicator: ${msg.text()}`);
            mockDataDetected.push(msg.text());
        }
    });

    // Set up error monitoring
    page.on('pageerror', (error) => {
        const errorInfo = {
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        };
        errors.push(errorInfo);
        console.log(`❌ Page Error: ${error.message}`);
    });

    // Set up comprehensive network monitoring
    page.on('request', (request) => {
        const requestInfo = {
            method: request.method(),
            url: request.url(),
            timestamp: new Date().toISOString(),
            headers: request.headers(),
            resourceType: request.resourceType()
        };
        networkRequests.push(requestInfo);
        
        // Log Supabase requests specifically
        if (request.url().includes('supabase.co')) {
            console.log(`🌐 Supabase Request: ${request.method()} ${request.url()}`);
            supabaseQueries.push(requestInfo);
        }

        // Flag any requests to localhost:8000 API
        if (request.url().includes('localhost:8000')) {
            console.log(`🔗 API Request: ${request.method()} ${request.url()}`);
        }

        // Flag any requests that might be mock data endpoints
        const mockEndpointPatterns = ['/mock', '/demo', '/test-data', '/sample'];
        if (mockEndpointPatterns.some(pattern => request.url().includes(pattern))) {
            console.log(`⚠️ Potential Mock Data Request: ${request.url()}`);
            mockDataDetected.push(`Mock endpoint: ${request.url()}`);
        }
    });

    // Monitor responses for data content
    page.on('response', async (response) => {
        if (response.url().includes('supabase.co') && response.status() < 400) {
            try {
                const responseBody = await response.text();
                console.log(`📡 Supabase Response: ${response.status()} - ${response.url()}`);
                
                // Check if response contains actual data vs empty/mock responses
                if (responseBody && responseBody.length > 10) {
                    findings.push(`✅ Supabase response with data: ${response.url()}`);
                    
                    // Check for specific table queries
                    if (response.url().includes('tax_deed_sales')) {
                        findings.push(`✅ Tax Deed Sales table queried successfully`);
                        console.log(`📊 Tax Deed Sales data loaded from Supabase`);
                    }
                }
            } catch (e) {
                console.log(`Could not read Supabase response body: ${e.message}`);
            }
        }

        // Check for error responses from any data sources
        if (response.status() >= 400) {
            errors.push({
                type: 'HTTP Error',
                status: response.status(),
                url: response.url(),
                timestamp: new Date().toISOString()
            });
        }
    });

    try {
        // Navigate to the specific property profile page
        const targetUrl = 'http://localhost:5174/properties/parkland/12681-nw-78-mnr';
        console.log(`🔍 Navigating to: ${targetUrl}\n`);
        
        await page.goto(targetUrl, { 
            waitUntil: 'networkidle',
            timeout: 60000 
        });

        // Wait for initial content load
        await page.waitForTimeout(3000);

        // Take initial screenshot
        await page.screenshot({ 
            path: path.join(resultsDir, 'property-page-initial.png'),
            fullPage: true 
        });

        console.log('📸 Initial screenshot taken\n');

        // Verify page loaded correctly
        const title = await page.title();
        console.log(`📄 Page Title: ${title}`);

        // Check for critical UI elements
        const criticalElements = [
            { selector: 'h1, h2', name: 'Main headings' },
            { selector: '[role="tab"], .tab', name: 'Property tabs' },
            { selector: '.property-info, .property-details', name: 'Property information sections' },
            { selector: 'button', name: 'Interactive buttons' }
        ];

        console.log('\n🔍 Checking for critical UI elements...');
        for (const element of criticalElements) {
            const count = await page.locator(element.selector).count();
            if (count > 0) {
                console.log(`✅ Found ${count} ${element.name}`);
                findings.push(`✅ UI Element present: ${element.name} (${count})`);
            } else {
                console.log(`❌ Missing: ${element.name}`);
                findings.push(`❌ Missing UI element: ${element.name}`);
            }
        }

        // Wait for any network requests to complete
        await page.waitForTimeout(2000);

        // Test Tax Deed Sales tab specifically
        console.log('\n🎯 Testing Tax Deed Sales Tab...');
        
        try {
            // Look for tax deed tab or link
            const taxDeedSelectors = [
                'text=Tax Deed',
                'text=Tax Deed Sales',
                '[data-testid*="tax-deed"]',
                'button:has-text("Tax Deed")',
                '.tab:has-text("Tax")'
            ];

            let taxDeedElement = null;
            for (const selector of taxDeedSelectors) {
                const element = page.locator(selector).first();
                if (await element.count() > 0) {
                    taxDeedElement = element;
                    console.log(`✅ Found Tax Deed tab with selector: ${selector}`);
                    break;
                }
            }

            if (taxDeedElement) {
                // Take screenshot before clicking
                await page.screenshot({ 
                    path: path.join(resultsDir, 'before-tax-deed-click.png'),
                    fullPage: true 
                });

                await taxDeedElement.click();
                console.log('✅ Clicked Tax Deed tab');
                
                // Wait for tab content to load
                await page.waitForTimeout(3000);
                
                // Take screenshot after clicking
                await page.screenshot({ 
                    path: path.join(resultsDir, 'tax-deed-tab-active.png'),
                    fullPage: true 
                });

                findings.push('✅ Tax Deed Sales tab successfully activated');
            } else {
                console.log('❌ Could not find Tax Deed Sales tab');
                findings.push('❌ Tax Deed Sales tab not found');
            }
        } catch (e) {
            console.log(`⚠️ Error testing Tax Deed tab: ${e.message}`);
            findings.push(`⚠️ Tax Deed tab test failed: ${e.message}`);
        }

        // Check page content for mock data values
        console.log('\n🔍 Scanning page content for mock data...');
        const pageContent = await page.content();
        
        for (const mockValue of MOCK_DATA_VALUES) {
            if (pageContent.includes(mockValue)) {
                console.log(`⚠️ Found mock data value: ${mockValue}`);
                mockDataDetected.push(`Page content contains mock value: ${mockValue}`);
            }
        }

        if (mockDataDetected.length === 0) {
            console.log('✅ No mock data values found in page content');
            findings.push('✅ Page content free of mock data values');
        }

        // Test various tabs to ensure they're using live data
        const tabTests = [
            'Overview',
            'Analysis', 
            'Taxes',
            'Sunbiz',
            'Core Property'
        ];

        console.log('\n🔄 Testing other property tabs...');
        for (const tabName of tabTests) {
            try {
                const tabElement = page.locator(`text=${tabName}`).first();
                if (await tabElement.count() > 0) {
                    await tabElement.click();
                    await page.waitForTimeout(2000);
                    
                    // Take screenshot of each tab
                    await page.screenshot({ 
                        path: path.join(resultsDir, `tab-${tabName.toLowerCase().replace(' ', '-')}.png`),
                        fullPage: true 
                    });
                    
                    console.log(`✅ Tested ${tabName} tab`);
                    findings.push(`✅ ${tabName} tab loaded successfully`);
                }
            } catch (e) {
                console.log(`⚠️ Could not test ${tabName} tab: ${e.message}`);
            }
        }

        // Final comprehensive screenshot
        await page.screenshot({ 
            path: path.join(resultsDir, 'property-page-final.png'),
            fullPage: true 
        });

        // Test mobile responsiveness
        console.log('\n📱 Testing mobile responsiveness...');
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(1000);
        
        await page.screenshot({ 
            path: path.join(resultsDir, 'property-page-mobile.png'),
            fullPage: true 
        });
        
        // Reset to desktop
        await page.setViewportSize({ width: 1920, height: 1080 });

    } catch (error) {
        console.log(`❌ Test failed: ${error.message}`);
        errors.push({
            type: 'Test Error',
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        
        // Take error screenshot
        try {
            await page.screenshot({ 
                path: path.join(resultsDir, 'error-screenshot.png'),
                fullPage: true 
            });
        } catch (screenshotError) {
            console.log('Could not take error screenshot');
        }
    }

    await browser.close();

    // Generate comprehensive report
    const report = generateDetailedReport({
        findings,
        networkRequests,
        consoleMessages,
        errors,
        supabaseQueries,
        mockDataDetected,
        resultsDir
    });

    // Write report to file
    const reportPath = path.join(resultsDir, 'live-data-verification-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    const summaryPath = path.join(resultsDir, 'verification-summary.txt');
    fs.writeFileSync(summaryPath, generateTextSummary(report));

    // Print summary to console
    console.log('\n' + '='.repeat(80));
    console.log('📋 LIVE DATA VERIFICATION REPORT');
    console.log('='.repeat(80));

    printReport(report);

    console.log('\n' + '='.repeat(80));
    console.log(`📁 Test Results saved to: ${resultsDir}`);
    console.log('='.repeat(80));

    return report;
}

function generateDetailedReport(data) {
    const { findings, networkRequests, consoleMessages, errors, supabaseQueries, mockDataDetected, resultsDir } = data;
    
    // Analyze network requests
    const supabaseRequests = networkRequests.filter(req => req.url.includes('supabase.co'));
    const mockEndpointRequests = networkRequests.filter(req => 
        ['/mock', '/demo', '/test-data', '/sample'].some(pattern => req.url.includes(pattern))
    );
    const apiRequests = networkRequests.filter(req => req.url.includes('localhost:8000'));

    // Analyze console messages for data source indicators
    const liveDataMessages = consoleMessages.filter(msg => {
        const text = msg.text.toLowerCase();
        return text.includes('live') || text.includes('supabase') || text.includes('database');
    });

    const mockDataMessages = consoleMessages.filter(msg => {
        const text = msg.text.toLowerCase();
        return ['mock', 'demo', 'test data', 'hardcoded'].some(indicator => text.includes(indicator));
    });

    // Calculate verification score
    let verificationScore = 0;
    let maxScore = 0;

    // Scoring criteria
    maxScore += 30; // Supabase requests (30 points)
    if (supabaseRequests.length > 0) verificationScore += 30;

    maxScore += 20; // No mock data detected (20 points) 
    if (mockDataDetected.length === 0) verificationScore += 20;

    maxScore += 20; // Live data console messages (20 points)
    if (liveDataMessages.length > 0) verificationScore += 20;

    maxScore += 15; // No mock endpoint requests (15 points)
    if (mockEndpointRequests.length === 0) verificationScore += 15;

    maxScore += 10; // Tax deed table queried (10 points)
    const taxDeedQueried = supabaseQueries.some(req => req.url.includes('tax_deed_sales'));
    if (taxDeedQueried) verificationScore += 10;

    maxScore += 5; // No errors (5 points)
    if (errors.length === 0) verificationScore += 5;

    const verificationPercentage = Math.round((verificationScore / maxScore) * 100);

    return {
        timestamp: new Date().toISOString(),
        testResults: {
            verificationScore,
            maxScore,
            verificationPercentage,
            isUsingLiveData: verificationPercentage >= 70,
            passedVerification: mockDataDetected.length === 0 && supabaseRequests.length > 0
        },
        findings,
        dataSourceAnalysis: {
            supabaseRequests: supabaseRequests.length,
            supabaseQueries: supabaseQueries.map(q => ({
                method: q.method,
                url: q.url,
                timestamp: q.timestamp
            })),
            mockEndpointRequests: mockEndpointRequests.length,
            apiRequests: apiRequests.length,
            taxDeedTableQueried: taxDeedQueried
        },
        mockDataAnalysis: {
            mockDataDetected: mockDataDetected.length,
            mockDataItems: mockDataDetected,
            liveDataIndicators: liveDataMessages.length,
            mockDataIndicators: mockDataMessages.length
        },
        networkSummary: {
            totalRequests: networkRequests.length,
            supabaseRequests: supabaseRequests.length,
            errorRequests: networkRequests.filter(req => errors.some(e => e.url === req.url)).length
        },
        consoleSummary: {
            totalMessages: consoleMessages.length,
            errorMessages: consoleMessages.filter(m => m.type === 'error').length,
            liveDataMessages: liveDataMessages.length,
            mockDataMessages: mockDataMessages.length
        },
        errors: errors.length,
        errorDetails: errors,
        resultsDirectory: resultsDir
    };
}

function generateTextSummary(report) {
    const { testResults, dataSourceAnalysis, mockDataAnalysis, networkSummary, consoleSummary } = report;
    
    return `LIVE DATA VERIFICATION SUMMARY
===============================

🎯 OVERALL RESULT: ${testResults.passedVerification ? 'PASSED ✅' : 'FAILED ❌'}
📊 Verification Score: ${testResults.verificationScore}/${testResults.maxScore} (${testResults.verificationPercentage}%)
🌐 Using Live Data: ${testResults.isUsingLiveData ? 'YES ✅' : 'NO ❌'}

DATA SOURCE ANALYSIS:
-------------------
🔗 Supabase Requests: ${dataSourceAnalysis.supabaseRequests}
📋 Tax Deed Table Queried: ${dataSourceAnalysis.taxDeedTableQueried ? 'YES ✅' : 'NO ❌'}
🚫 Mock Endpoints: ${dataSourceAnalysis.mockEndpointRequests}
🔌 API Requests: ${dataSourceAnalysis.apiRequests}

MOCK DATA ANALYSIS:
------------------
⚠️ Mock Data Items Detected: ${mockDataAnalysis.mockDataDetected}
✅ Live Data Indicators: ${mockDataAnalysis.liveDataIndicators}
🚫 Mock Data Indicators: ${mockDataAnalysis.mockDataIndicators}

NETWORK SUMMARY:
---------------
📡 Total Requests: ${networkSummary.totalRequests}
🌐 Supabase Requests: ${networkSummary.supabaseRequests}
❌ Error Requests: ${networkSummary.errorRequests}

CONSOLE SUMMARY:
---------------
📋 Total Messages: ${consoleSummary.totalMessages}
❌ Error Messages: ${consoleSummary.errorMessages}
✅ Live Data Messages: ${consoleSummary.liveDataMessages}
⚠️ Mock Data Messages: ${consoleSummary.mockDataMessages}

VERDICT:
--------
${testResults.passedVerification 
    ? '✅ The application is successfully using live Supabase data without mock data.'
    : '❌ The application may still be using mock data or has data source issues.'
}

Test completed at: ${report.timestamp}
`;
}

function printReport(report) {
    const { testResults, dataSourceAnalysis, mockDataAnalysis } = report;

    console.log(`\n🎯 OVERALL VERIFICATION: ${testResults.passedVerification ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`📊 Score: ${testResults.verificationScore}/${testResults.maxScore} (${testResults.verificationPercentage}%)`);
    console.log(`🌐 Using Live Data: ${testResults.isUsingLiveData ? '✅ YES' : '❌ NO'}`);

    console.log('\n🔗 DATA SOURCE ANALYSIS:');
    console.log(`   Supabase Requests: ${dataSourceAnalysis.supabaseRequests}`);
    console.log(`   Tax Deed Table Queried: ${dataSourceAnalysis.taxDeedTableQueried ? '✅' : '❌'}`);
    console.log(`   Mock Endpoints Called: ${dataSourceAnalysis.mockEndpointRequests}`);

    if (dataSourceAnalysis.supabaseQueries.length > 0) {
        console.log('\n📋 SUPABASE QUERIES MADE:');
        dataSourceAnalysis.supabaseQueries.forEach((query, index) => {
            console.log(`   ${index + 1}. ${query.method} ${query.url}`);
        });
    }

    console.log('\n⚠️ MOCK DATA ANALYSIS:');
    console.log(`   Mock Data Items Detected: ${mockDataAnalysis.mockDataDetected}`);
    console.log(`   Live Data Indicators: ${mockDataAnalysis.liveDataIndicators}`);
    
    if (mockDataAnalysis.mockDataItems.length > 0) {
        console.log('\n🚨 MOCK DATA DETECTED:');
        mockDataAnalysis.mockDataItems.forEach((item, index) => {
            console.log(`   ${index + 1}. ${item}`);
        });
    }

    console.log('\n🎯 KEY FINDINGS:');
    report.findings.slice(-10).forEach(finding => {
        console.log(`   ${finding}`);
    });

    if (report.findings.length > 10) {
        console.log(`   ... and ${report.findings.length - 10} more findings`);
    }

    if (report.errors > 0) {
        console.log(`\n❌ ERRORS ENCOUNTERED: ${report.errors}`);
        report.errorDetails.slice(-3).forEach(error => {
            console.log(`   ${error.type}: ${error.message}`);
        });
    } else {
        console.log('\n✅ NO ERRORS ENCOUNTERED');
    }

    // Final recommendation
    console.log('\n🏁 RECOMMENDATION:');
    if (testResults.passedVerification) {
        console.log('   ✅ Application is successfully using live Supabase data.');
        console.log('   ✅ No mock data contamination detected.');
        console.log('   ✅ Ready for production deployment.');
    } else if (testResults.verificationPercentage >= 50) {
        console.log('   ⚠️ Application is partially using live data.');
        console.log('   ⚠️ Some components may still use mock data.');
        console.log('   🔧 Review mock data detections and fix remaining issues.');
    } else {
        console.log('   ❌ Application appears to be using significant mock data.');
        console.log('   🔧 Verify database connections and component data sources.');
        console.log('   🚫 Not recommended for production until issues are resolved.');
    }
}

// Run the test when script is executed directly
if (require.main === module) {
    runLiveDataVerification()
        .then(report => {
            const exitCode = report.testResults.passedVerification ? 0 : 1;
            console.log(`\nExiting with code: ${exitCode}`);
            process.exit(exitCode);
        })
        .catch(error => {
            console.error('Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = { runLiveDataVerification };