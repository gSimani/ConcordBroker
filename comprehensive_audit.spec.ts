import { test, expect } from '@playwright/test';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

test.describe('ConcordBroker Website Audit', () => {
  let auditResults = {
    supabase: {
      connectionTest: null,
      floridaParcelsQuery: null,
      propertySalesHistoryQuery: null,
      rlsPolicies: null,
      tableAccess: null
    },
    localhost: {
      pageLoaded: false,
      consoleErrors: [],
      networkErrors: [],
      propertiesLoaded: false,
      infiniteLoading: false,
      screenshots: []
    },
    production: {
      pageLoaded: false,
      consoleErrors: [],
      networkErrors: [],
      propertiesLoaded: false,
      infiniteLoading: false,
      screenshots: []
    },
    comparison: {
      differences: []
    }
  };

  test.beforeAll(async () => {
    console.log('🔍 Starting Comprehensive ConcordBroker Audit...\n');
  });

  test('1. Test Supabase Database Connectivity', async () => {
    console.log('\n📊 Testing Supabase Database...');

    const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

    // Test 1: Basic connection
    try {
      const { error } = await supabase.from('florida_parcels').select('count', { count: 'exact', head: true });
      auditResults.supabase.connectionTest = error ? { success: false, error: error.message } : { success: true };
      console.log('   ✓ Supabase connection:', auditResults.supabase.connectionTest.success ? 'SUCCESS' : 'FAILED');
      if (error) console.log('   Error:', error.message);
    } catch (err) {
      auditResults.supabase.connectionTest = { success: false, error: err.message };
      console.log('   ✗ Connection failed:', err.message);
    }

    // Test 2: Query florida_parcels (limit 1)
    try {
      const { data, error, count } = await supabase
        .from('florida_parcels')
        .select('*', { count: 'exact' })
        .limit(1);

      auditResults.supabase.floridaParcelsQuery = {
        success: !error,
        rowsReturned: data?.length || 0,
        totalCount: count,
        error: error?.message,
        sample: data?.[0]
      };

      console.log('   ✓ florida_parcels query:', auditResults.supabase.floridaParcelsQuery.success ? 'SUCCESS' : 'FAILED');
      console.log('   Total records:', count);
      if (error) console.log('   Error:', error.message);
    } catch (err) {
      auditResults.supabase.floridaParcelsQuery = { success: false, error: err.message };
      console.log('   ✗ Query failed:', err.message);
    }

    // Test 3: Query property_sales_history
    try {
      const { data, error, count } = await supabase
        .from('property_sales_history')
        .select('*', { count: 'exact' })
        .limit(1);

      auditResults.supabase.propertySalesHistoryQuery = {
        success: !error,
        rowsReturned: data?.length || 0,
        totalCount: count,
        error: error?.message,
        sample: data?.[0]
      };

      console.log('   ✓ property_sales_history query:', auditResults.supabase.propertySalesHistoryQuery.success ? 'SUCCESS' : 'FAILED');
      console.log('   Total records:', count);
      if (error) console.log('   Error:', error.message);
    } catch (err) {
      auditResults.supabase.propertySalesHistoryQuery = { success: false, error: err.message };
      console.log('   ✗ Query failed:', err.message);
    }

    // Test 4: Check RLS policies (try to query without filters)
    try {
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id,county,owner_name,just_value')
        .limit(5);

      auditResults.supabase.rlsPolicies = {
        blocking: !!error,
        errorMessage: error?.message,
        canReadWithoutFilter: !error,
        sampleData: data
      };

      console.log('   ✓ RLS policies check:', error ? 'BLOCKING' : 'ALLOWING reads');
      if (error) console.log('   RLS Error:', error.message);
    } catch (err) {
      auditResults.supabase.rlsPolicies = { blocking: true, error: err.message };
      console.log('   ✗ RLS check failed:', err.message);
    }

    // Test 5: Check table access
    const tables = ['florida_parcels', 'property_sales_history', 'florida_entities', 'sunbiz_corporate', 'tax_certificates'];
    auditResults.supabase.tableAccess = {};

    console.log('\n   Testing table access:');
    for (const table of tables) {
      try {
        const { error, count } = await supabase
          .from(table)
          .select('*', { count: 'exact', head: true });

        auditResults.supabase.tableAccess[table] = {
          accessible: !error,
          count: count,
          error: error?.message
        };

        console.log(`   ${!error ? '✓' : '✗'} ${table}:`, !error ? `${count} records` : error.message);
      } catch (err) {
        auditResults.supabase.tableAccess[table] = { accessible: false, error: err.message };
        console.log(`   ✗ ${table}:`, err.message);
      }
    }
  });

  test('2. Test Localhost Properties Page', async ({ page }) => {
    console.log('\n🏠 Testing Localhost (http://localhost:5181/properties)...');

    const consoleMessages = [];
    const errors = [];
    const networkFailures = [];

    // Capture console messages
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push({ type: msg.type(), text });
      if (msg.type() === 'error') {
        errors.push(text);
      }
    });

    // Capture network failures
    page.on('requestfailed', request => {
      networkFailures.push({
        url: request.url(),
        method: request.method(),
        failure: request.failure()?.errorText
      });
    });

    try {
      // Navigate to localhost
      const response = await page.goto('http://localhost:5181/properties', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      auditResults.localhost.pageLoaded = response?.ok() || false;
      console.log('   ✓ Page loaded:', auditResults.localhost.pageLoaded ? 'YES' : 'NO');
      console.log('   Response status:', response?.status());

      // Take initial screenshot
      await page.screenshot({ path: 'audit_localhost_initial.png', fullPage: true });
      auditResults.localhost.screenshots.push('audit_localhost_initial.png');
      console.log('   ✓ Screenshot saved: audit_localhost_initial.png');

      // Wait a bit for any dynamic content
      await page.waitForTimeout(3000);

      // Check for loading states
      const loadingSpinners = await page.locator('[data-loading="true"], .loading, .spinner').count();
      auditResults.localhost.infiniteLoading = loadingSpinners > 0;
      console.log('   Loading spinners found:', loadingSpinners);

      // Check if properties are displayed
      const propertyCards = await page.locator('[data-testid="property-card"], .property-card, [class*="PropertyCard"]').count();
      auditResults.localhost.propertiesLoaded = propertyCards > 0;
      console.log('   ✓ Property cards found:', propertyCards);

      // Check for "0 Properties Found" or empty states
      const emptyStateText = await page.locator('text=/0 Properties|No properties|No results/i').count();
      if (emptyStateText > 0) {
        console.log('   ⚠ Empty state detected');
      }

      // Take final screenshot
      await page.screenshot({ path: 'audit_localhost_final.png', fullPage: true });
      auditResults.localhost.screenshots.push('audit_localhost_final.png');

      // Wait for infinite loading check
      await page.waitForTimeout(5000);
      const stillLoading = await page.locator('[data-loading="true"], .loading, .spinner').count();
      if (stillLoading > 0) {
        auditResults.localhost.infiniteLoading = true;
        console.log('   ⚠ INFINITE LOADING DETECTED');
      }

    } catch (error) {
      console.log('   ✗ Error loading page:', error.message);
      auditResults.localhost.pageLoaded = false;
      errors.push(error.message);
    }

    auditResults.localhost.consoleErrors = errors;
    auditResults.localhost.networkErrors = networkFailures;

    console.log('\n   Console Errors:', errors.length);
    errors.forEach(err => console.log('     -', err));

    console.log('   Network Failures:', networkFailures.length);
    networkFailures.forEach(fail => console.log('     -', fail.url, fail.failure));
  });

  test('3. Test Production Website', async ({ page }) => {
    console.log('\n🌐 Testing Production (https://www.concordbroker.com/properties)...');

    const consoleMessages = [];
    const errors = [];
    const networkFailures = [];

    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push({ type: msg.type(), text });
      if (msg.type() === 'error') {
        errors.push(text);
      }
    });

    page.on('requestfailed', request => {
      networkFailures.push({
        url: request.url(),
        method: request.method(),
        failure: request.failure()?.errorText
      });
    });

    try {
      const response = await page.goto('https://www.concordbroker.com/properties', {
        waitUntil: 'networkidle',
        timeout: 30000
      });

      auditResults.production.pageLoaded = response?.ok() || false;
      console.log('   ✓ Page loaded:', auditResults.production.pageLoaded ? 'YES' : 'NO');
      console.log('   Response status:', response?.status());

      await page.screenshot({ path: 'audit_production_initial.png', fullPage: true });
      auditResults.production.screenshots.push('audit_production_initial.png');
      console.log('   ✓ Screenshot saved: audit_production_initial.png');

      await page.waitForTimeout(3000);

      const loadingSpinners = await page.locator('[data-loading="true"], .loading, .spinner').count();
      auditResults.production.infiniteLoading = loadingSpinners > 0;
      console.log('   Loading spinners found:', loadingSpinners);

      const propertyCards = await page.locator('[data-testid="property-card"], .property-card, [class*="PropertyCard"]').count();
      auditResults.production.propertiesLoaded = propertyCards > 0;
      console.log('   ✓ Property cards found:', propertyCards);

      const emptyStateText = await page.locator('text=/0 Properties|No properties|No results/i').count();
      if (emptyStateText > 0) {
        console.log('   ⚠ Empty state detected');
      }

      await page.screenshot({ path: 'audit_production_final.png', fullPage: true });
      auditResults.production.screenshots.push('audit_production_final.png');

      await page.waitForTimeout(5000);
      const stillLoading = await page.locator('[data-loading="true"], .loading, .spinner').count();
      if (stillLoading > 0) {
        auditResults.production.infiniteLoading = true;
        console.log('   ⚠ INFINITE LOADING DETECTED');
      }

    } catch (error) {
      console.log('   ✗ Error loading page:', error.message);
      auditResults.production.pageLoaded = false;
      errors.push(error.message);
    }

    auditResults.production.consoleErrors = errors;
    auditResults.production.networkErrors = networkFailures;

    console.log('\n   Console Errors:', errors.length);
    errors.forEach(err => console.log('     -', err));

    console.log('   Network Failures:', networkFailures.length);
    networkFailures.forEach(fail => console.log('     -', fail.url, fail.failure));
  });

  test('4. Compare Localhost vs Production', async () => {
    console.log('\n📊 Comparing Localhost vs Production...');

    if (auditResults.localhost.pageLoaded !== auditResults.production.pageLoaded) {
      auditResults.comparison.differences.push('Page load status differs');
    }

    if (auditResults.localhost.propertiesLoaded !== auditResults.production.propertiesLoaded) {
      auditResults.comparison.differences.push('Properties loading differs');
    }

    if (auditResults.localhost.infiniteLoading !== auditResults.production.infiniteLoading) {
      auditResults.comparison.differences.push('Infinite loading state differs');
    }

    console.log('   Differences found:', auditResults.comparison.differences.length);
    auditResults.comparison.differences.forEach(diff => console.log('     -', diff));
  });

  test.afterAll(async () => {
    // Write comprehensive audit report
    const fs = require('fs');
    const reportPath = 'WEBSITE_AUDIT_REPORT.md';

    let report = `# ConcordBroker Website Audit Report
Generated: ${new Date().toISOString()}

## Executive Summary

### Critical Issues Found:
`;

    const criticalIssues = [];

    if (!auditResults.supabase.connectionTest?.success) {
      criticalIssues.push('❌ Supabase database connection FAILED');
    }

    if (!auditResults.supabase.floridaParcelsQuery?.success) {
      criticalIssues.push('❌ Cannot query florida_parcels table');
    }

    if (auditResults.supabase.rlsPolicies?.blocking) {
      criticalIssues.push('⚠️ RLS policies may be blocking data access');
    }

    if (!auditResults.localhost.pageLoaded) {
      criticalIssues.push('❌ Localhost website failed to load');
    }

    if (auditResults.localhost.infiniteLoading) {
      criticalIssues.push('❌ Localhost has INFINITE LOADING state');
    }

    if (!auditResults.localhost.propertiesLoaded) {
      criticalIssues.push('❌ Localhost - NO PROPERTIES DISPLAYED');
    }

    if (!auditResults.production.propertiesLoaded) {
      criticalIssues.push('❌ Production - NO PROPERTIES DISPLAYED');
    }

    report += criticalIssues.length > 0
      ? criticalIssues.map(issue => `- ${issue}`).join('\n')
      : '✅ No critical issues found!\n';

    report += `\n\n## 1. Supabase Database Tests

### Connection Test
- **Status:** ${auditResults.supabase.connectionTest?.success ? '✅ SUCCESS' : '❌ FAILED'}
${auditResults.supabase.connectionTest?.error ? `- **Error:** ${auditResults.supabase.connectionTest.error}` : ''}

### florida_parcels Table
- **Status:** ${auditResults.supabase.floridaParcelsQuery?.success ? '✅ SUCCESS' : '❌ FAILED'}
- **Total Records:** ${auditResults.supabase.floridaParcelsQuery?.totalCount || 'Unknown'}
- **Rows Returned:** ${auditResults.supabase.floridaParcelsQuery?.rowsReturned || 0}
${auditResults.supabase.floridaParcelsQuery?.error ? `- **Error:** ${auditResults.supabase.floridaParcelsQuery.error}` : ''}

### property_sales_history Table
- **Status:** ${auditResults.supabase.propertySalesHistoryQuery?.success ? '✅ SUCCESS' : '❌ FAILED'}
- **Total Records:** ${auditResults.supabase.propertySalesHistoryQuery?.totalCount || 'Unknown'}
- **Rows Returned:** ${auditResults.supabase.propertySalesHistoryQuery?.rowsReturned || 0}
${auditResults.supabase.propertySalesHistoryQuery?.error ? `- **Error:** ${auditResults.supabase.propertySalesHistoryQuery.error}` : ''}

### RLS Policies Check
- **Blocking Reads:** ${auditResults.supabase.rlsPolicies?.blocking ? '⚠️ YES' : '✅ NO'}
${auditResults.supabase.rlsPolicies?.errorMessage ? `- **Error:** ${auditResults.supabase.rlsPolicies.errorMessage}` : ''}
- **Can Read Without Filter:** ${auditResults.supabase.rlsPolicies?.canReadWithoutFilter ? '✅ YES' : '❌ NO'}

### Table Access Summary
`;

    for (const [table, access] of Object.entries(auditResults.supabase.tableAccess || {})) {
      report += `- **${table}:** ${access.accessible ? '✅' : '❌'} (${access.count || 0} records)\n`;
      if (access.error) report += `  - Error: ${access.error}\n`;
    }

    report += `\n## 2. Localhost Testing (http://localhost:5181/properties)

### Page Load
- **Status:** ${auditResults.localhost.pageLoaded ? '✅ SUCCESS' : '❌ FAILED'}
- **Properties Loaded:** ${auditResults.localhost.propertiesLoaded ? '✅ YES' : '❌ NO'}
- **Infinite Loading:** ${auditResults.localhost.infiniteLoading ? '❌ YES' : '✅ NO'}

### Console Errors (${auditResults.localhost.consoleErrors?.length || 0})
\`\`\`
${auditResults.localhost.consoleErrors?.join('\n') || 'None'}
\`\`\`

### Network Failures (${auditResults.localhost.networkErrors?.length || 0})
${auditResults.localhost.networkErrors?.length > 0
  ? auditResults.localhost.networkErrors.map(fail => `- ${fail.url}: ${fail.failure}`).join('\n')
  : 'None'}

### Screenshots
${auditResults.localhost.screenshots?.map(s => `- ${s}`).join('\n')}

## 3. Production Testing (https://www.concordbroker.com/properties)

### Page Load
- **Status:** ${auditResults.production.pageLoaded ? '✅ SUCCESS' : '❌ FAILED'}
- **Properties Loaded:** ${auditResults.production.propertiesLoaded ? '✅ YES' : '❌ NO'}
- **Infinite Loading:** ${auditResults.production.infiniteLoading ? '❌ YES' : '✅ NO'}

### Console Errors (${auditResults.production.consoleErrors?.length || 0})
\`\`\`
${auditResults.production.consoleErrors?.join('\n') || 'None'}
\`\`\`

### Network Failures (${auditResults.production.networkErrors?.length || 0})
${auditResults.production.networkErrors?.length > 0
  ? auditResults.production.networkErrors.map(fail => `- ${fail.url}: ${fail.failure}`).join('\n')
  : 'None'}

### Screenshots
${auditResults.production.screenshots?.map(s => `- ${s}`).join('\n')}

## 4. Root Cause Analysis

`;

    // Root cause analysis
    if (!auditResults.supabase.floridaParcelsQuery?.success) {
      report += `### Database Query Failure
The florida_parcels table cannot be queried. This is likely due to:
1. RLS policies blocking anonymous access
2. Missing table or incorrect table name
3. Invalid Supabase credentials

**Fix Required:** Check RLS policies in Supabase dashboard for florida_parcels table.

`;
    }

    if (auditResults.localhost.consoleErrors?.some(err => err.includes('Supabase'))) {
      report += `### Supabase Client Error
Console shows Supabase-related errors. Check:
1. Environment variables are loaded correctly
2. Supabase client initialization in the app
3. API key validity

**Fix Required:** Verify \`.env.local\` is being read and Supabase client is properly initialized.

`;
    }

    if (!auditResults.localhost.propertiesLoaded && auditResults.localhost.pageLoaded) {
      report += `### Properties Not Loading
The page loads but no properties are displayed. This indicates:
1. Data fetch is failing silently
2. Empty response from database
3. Frontend rendering issue

**Fix Required:** Add error logging in PropertySearch component's searchProperties function.

`;
    }

    report += `\n## 5. Recommended Fixes

### Immediate Actions Required:

1. **Check PropertySearch.tsx searchProperties function**
   - File: \`apps/web/src/pages/properties/PropertySearch.tsx\`
   - Add comprehensive error logging
   - Verify Supabase query syntax
   - Check if data is being set to state correctly

2. **Verify Supabase RLS Policies**
   - Go to Supabase Dashboard → Authentication → Policies
   - Check florida_parcels table policies
   - Ensure anonymous read access is enabled

3. **Test Direct Database Query**
   - Run this in browser console on localhost:5181:
   \`\`\`javascript
   const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
   const supabase = createClient(
     'https://pmispwtdngkcmsrsjwbp.supabase.co',
     'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
   );
   const { data, error } = await supabase.from('florida_parcels').select('*').limit(5);
   console.log({ data, error });
   \`\`\`

4. **Add Debug Logging**
   - Add console.log statements in searchProperties function
   - Log query parameters, response data, and errors
   - Verify state updates are happening

5. **Check Network Tab**
   - Open browser DevTools → Network tab
   - Look for Supabase API calls
   - Check response status and data

### Files to Review:

1. \`apps/web/src/pages/properties/PropertySearch.tsx\` - Main search component
2. \`apps/web/src/lib/supabase.ts\` - Supabase client initialization
3. \`apps/web/.env.local\` - Environment variables
4. \`apps/web/src/hooks/useOptimizedPropertySearch.ts\` - Search hook

---

**Next Steps:**
1. Review the screenshots generated by this audit
2. Check the console errors for specific failure points
3. Implement the recommended fixes
4. Re-run this audit to verify fixes

**Audit Complete** ✅
`;

    fs.writeFileSync(reportPath, report);
    console.log(`\n✅ Comprehensive audit report saved to: ${reportPath}`);
    console.log('\n📊 Audit Results Summary:');
    console.log(JSON.stringify(auditResults, null, 2));
  });
});
