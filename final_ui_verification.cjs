const puppeteer = require('puppeteer');

async function finalUIVerification() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    const results = {
        timestamp: new Date().toISOString(),
        tests: [],
        summary: { passed: 0, failed: 0, total: 0 }
    };

    async function runTest(name, testFunction) {
        console.log(`\n🧪 ${name}`);
        const startTime = Date.now();

        try {
            const result = await testFunction();
            const duration = Date.now() - startTime;

            results.tests.push({
                name,
                status: 'passed',
                duration,
                result
            });

            results.summary.passed++;
            console.log(`✅ ${name} - PASSED (${duration}ms)`);

            if (result && typeof result === 'object') {
                Object.entries(result).forEach(([key, value]) => {
                    console.log(`   ${key}: ${value}`);
                });
            }

        } catch (error) {
            const duration = Date.now() - startTime;

            results.tests.push({
                name,
                status: 'failed',
                duration,
                error: error.message
            });

            results.summary.failed++;
            console.log(`❌ ${name} - FAILED (${duration}ms): ${error.message}`);
        }

        results.summary.total++;
    }

    try {
        console.log('🚀 Final ConcordBroker UI Verification\n');

        // Test 1: Home page loads
        await runTest('Home Page Load', async () => {
            await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0', timeout: 15000 });
            await new Promise(resolve => setTimeout(resolve, 2000));

            const title = await page.title();
            const hasContent = await page.$eval('body', el => el.innerText.includes('ConcordBroker'));

            await page.screenshot({ path: './final_home_verification.png', fullPage: true });

            return { title_correct: title.includes('ConcordBroker'), has_content: hasContent };
        });

        // Test 2: Properties page loads (the main issue)
        await runTest('Properties Page Load', async () => {
            await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle0', timeout: 15000 });
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Check if error boundary is showing
            const hasError = await page.$('[data-testid="error-boundary-container"]');

            if (hasError) {
                const errorText = await page.$eval('[data-testid="error-boundary-container"]', el => el.innerText);
                throw new Error(`Page shows error: ${errorText.substring(0, 200)}`);
            }

            // Check for search functionality
            const hasSearchInput = await page.$('#property-search-input-1, input[placeholder*="search"], input[placeholder*="address"]');
            const hasSearchForm = await page.$('#property-search-form-1, form');
            const pageTitle = await page.$eval('h1', el => el.innerText || '').catch(() => '');

            await page.screenshot({ path: './final_properties_verification.png', fullPage: true });

            return {
                no_error: !hasError,
                has_search_input: !!hasSearchInput,
                has_search_form: !!hasSearchForm,
                page_title: pageTitle
            };
        });

        // Test 3: Search functionality
        await runTest('Search Input Functionality', async () => {
            // Should be on properties page from previous test
            const searchInput = await page.$('#property-search-input-1, input[placeholder*="search"], input[placeholder*="address"]');

            if (!searchInput) {
                throw new Error('Search input not found');
            }

            await searchInput.click();
            await searchInput.type('Miami', { delay: 100 });

            // Take screenshot of typing
            await page.screenshot({ path: './final_search_typing.png', fullPage: true });

            const inputValue = await searchInput.evaluate(el => el.value);

            return { input_accepts_text: inputValue === 'Miami' };
        });

        // Test 4: County dropdown
        await runTest('County Dropdown Functionality', async () => {
            const countySelect = await page.$('#county-filter-select-1, select');

            if (!countySelect) {
                // Try clicking on a select trigger (Radix UI)
                const selectTrigger = await page.$('[data-testid*="county"], [id*="county"]');
                if (selectTrigger) {
                    await selectTrigger.click();
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    const hasOptions = await page.$$('[role="option"], [data-value]');

                    return { dropdown_opens: hasOptions.length > 0, options_count: hasOptions.length };
                }

                throw new Error('County dropdown not found');
            }

            return { county_dropdown_found: true };
        });

        // Test 5: Search button
        await runTest('Search Button Functionality', async () => {
            const searchButton = await page.$('#search-submit-button-1, button[type="submit"], button:contains("Search")');

            if (!searchButton) {
                // Try to find any search button
                const buttons = await page.$$('button');
                let searchButtonFound = false;

                for (const button of buttons) {
                    const text = await button.evaluate(el => el.innerText);
                    if (text.toLowerCase().includes('search')) {
                        searchButtonFound = true;

                        // Try clicking it
                        await button.click();
                        await new Promise(resolve => setTimeout(resolve, 2000));

                        await page.screenshot({ path: './final_search_click.png', fullPage: true });

                        break;
                    }
                }

                return { search_button_found: searchButtonFound };
            }

            await searchButton.click();
            await new Promise(resolve => setTimeout(resolve, 2000));

            return { search_button_clickable: true };
        });

        // Test 6: Dashboard navigation
        await runTest('Dashboard Navigation', async () => {
            await page.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle0', timeout: 15000 });
            await new Promise(resolve => setTimeout(resolve, 2000));

            const hasError = await page.$('[data-testid="error-boundary-container"]');
            const url = page.url();

            await page.screenshot({ path: './final_dashboard_verification.png', fullPage: true });

            return {
                dashboard_loads: !hasError,
                correct_url: url.includes('/dashboard')
            };
        });

        // Test 7: Analytics navigation
        await runTest('Analytics Navigation', async () => {
            await page.goto('http://localhost:5173/analytics', { waitUntil: 'networkidle0', timeout: 15000 });
            await new Promise(resolve => setTimeout(resolve, 2000));

            const hasError = await page.$('[data-testid="error-boundary-container"]');
            const url = page.url();

            await page.screenshot({ path: './final_analytics_verification.png', fullPage: true });

            return {
                analytics_loads: !hasError,
                correct_url: url.includes('/analytics')
            };
        });

        // Test 8: Console errors check
        await runTest('Console Errors Check', async () => {
            const errors = [];

            page.on('console', msg => {
                if (msg.type() === 'error') {
                    errors.push(msg.text());
                }
            });

            // Reload properties page to catch any errors
            await page.goto('http://localhost:5173/properties', { waitUntil: 'networkidle0' });
            await new Promise(resolve => setTimeout(resolve, 3000));

            const criticalErrors = errors.filter(error =>
                error.includes('TypeError') ||
                error.includes('ReferenceError') ||
                error.includes('Failed to load') ||
                error.includes('500')
            );

            return {
                total_errors: errors.length,
                critical_errors: criticalErrors.length,
                has_critical_errors: criticalErrors.length > 0
            };
        });

        console.log('\n' + '='.repeat(60));
        console.log('📊 FINAL UI VERIFICATION SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total Tests: ${results.summary.total}`);
        console.log(`Passed: ${results.summary.passed} ✅`);
        console.log(`Failed: ${results.summary.failed} ${results.summary.failed > 0 ? '❌' : ''}`);
        console.log(`Success Rate: ${Math.round((results.summary.passed / results.summary.total) * 100)}%`);

        const criticalTests = ['Properties Page Load', 'Search Input Functionality'];
        const criticalResults = results.tests.filter(test => criticalTests.includes(test.name));
        const criticalPassed = criticalResults.filter(test => test.status === 'passed').length;

        console.log(`\n🔥 Critical Functionality: ${criticalPassed}/${criticalResults.length} working`);

        if (results.summary.failed > 0) {
            console.log('\n❌ Failed Tests:');
            results.tests.filter(test => test.status === 'failed').forEach(test => {
                console.log(`   - ${test.name}: ${test.error}`);
            });
        }

        console.log('\n📸 Screenshots saved:');
        console.log('   - final_home_verification.png');
        console.log('   - final_properties_verification.png');
        console.log('   - final_search_typing.png');
        console.log('   - final_search_click.png');
        console.log('   - final_dashboard_verification.png');
        console.log('   - final_analytics_verification.png');

        return results;

    } catch (error) {
        console.error('❌ Final verification failed:', error.message);
    } finally {
        await browser.close();
    }
}

finalUIVerification().catch(console.error);