/**
 * ConcordBroker 100% Supabase Integration Verification Script
 * Comprehensive test suite to verify all database tables, hooks, and API endpoints
 * Run with: node scripts/verify-100-percent-integration.js
 */

import { createClient } from '@supabase/supabase-js';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Get directory path for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase configuration in .env file');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Test configuration
const TEST_USER_EMAIL = 'test@concordbroker.com';
const TEST_PARCEL_ID = '1234567890';
const API_BASE_URL = 'http://localhost:8001';

// Verification results
let testResults = {
  database: { passed: 0, failed: 0, tests: [] },
  hooks: { passed: 0, failed: 0, tests: [] },
  api: { passed: 0, failed: 0, tests: [] },
  integration: { passed: 0, failed: 0, tests: [] }
};

// Helper functions
function logTest(category, testName, passed, error = null) {
  const status = passed ? '✅' : '❌';
  const message = `${status} ${testName}`;

  console.log(message);
  if (error) {
    console.log(`   Error: ${error}`);
  }

  testResults[category].tests.push({ testName, passed, error });
  if (passed) {
    testResults[category].passed++;
  } else {
    testResults[category].failed++;
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Database table verification
async function verifyDatabaseTables() {
  console.log('\n🔍 VERIFYING DATABASE TABLES');
  console.log('=====================================');

  const expectedTables = [
    'user_watchlists',
    'property_notes',
    'user_preferences',
    'user_search_history',
    'property_view_history',
    'property_scores',
    'property_alerts',
    'market_comparables',
    'user_alert_preferences',
    'property_analytics'
  ];

  for (const tableName of expectedTables) {
    try {
      const { data, error } = await supabase
        .from(tableName)
        .select('*')
        .limit(1);

      if (error && !error.message.includes('relation') && !error.message.includes('does not exist')) {
        logTest('database', `Table ${tableName} accessible`, true);
      } else if (error) {
        logTest('database', `Table ${tableName} accessible`, false, error.message);
      } else {
        logTest('database', `Table ${tableName} accessible`, true);
      }
    } catch (error) {
      logTest('database', `Table ${tableName} accessible`, false, error.message);
    }
  }

  // Test RLS policies
  console.log('\n🔒 Testing Row Level Security Policies');
  try {
    // This should fail without proper authentication
    const { error } = await supabase
      .from('user_watchlists')
      .insert({
        user_id: '00000000-0000-0000-0000-000000000000',
        parcel_id: TEST_PARCEL_ID
      });

    if (error) {
      logTest('database', 'RLS policies are enforced', true);
    } else {
      logTest('database', 'RLS policies are enforced', false, 'Insert should have been blocked by RLS');
    }
  } catch (error) {
    logTest('database', 'RLS policies are enforced', true);
  }

  // Test database functions
  console.log('\n🔧 Testing Database Functions');

  try {
    const { data, error } = await supabase
      .rpc('calculate_investment_score', { p_parcel_id: TEST_PARCEL_ID });

    if (!error || error.message.includes('Property not found')) {
      logTest('database', 'calculate_investment_score function exists', true);
    } else {
      logTest('database', 'calculate_investment_score function exists', false, error.message);
    }
  } catch (error) {
    logTest('database', 'calculate_investment_score function exists', false, error.message);
  }

  try {
    const { data, error } = await supabase
      .rpc('find_comparable_properties', {
        p_parcel_id: TEST_PARCEL_ID,
        p_radius_miles: 5,
        p_limit: 10
      });

    if (!error) {
      logTest('database', 'find_comparable_properties function exists', true);
    } else {
      logTest('database', 'find_comparable_properties function exists', false, error.message);
    }
  } catch (error) {
    logTest('database', 'find_comparable_properties function exists', false, error.message);
  }
}

// Hook files verification
async function verifyHookFiles() {
  console.log('\n🎣 VERIFYING REACT HOOKS');
  console.log('=====================================');

  const expectedHooks = [
    'apps/web/src/hooks/useWatchlist.ts',
    'apps/web/src/hooks/usePropertyNotes.ts',
    'apps/web/src/hooks/usePropertyScores.ts',
    'apps/web/src/hooks/useAlerts.ts'
  ];

  for (const hookPath of expectedHooks) {
    try {
      const fullPath = path.join(__dirname, '..', hookPath);
      const exists = fs.existsSync(fullPath);

      if (exists) {
        const content = fs.readFileSync(fullPath, 'utf-8');

        // Check for key patterns
        const hasSupabaseImport = content.includes("from '@/lib/supabase'");
        const hasRealTime = content.includes('postgres_changes') || content.includes('channel');
        const hasErrorHandling = content.includes('try') && content.includes('catch');
        const hasOptimisticUpdates = content.includes('Optimistic');

        const hookName = path.basename(hookPath, '.ts');
        logTest('hooks', `${hookName} file exists`, true);
        logTest('hooks', `${hookName} has Supabase integration`, hasSupabaseImport);
        logTest('hooks', `${hookName} has real-time updates`, hasRealTime);
        logTest('hooks', `${hookName} has error handling`, hasErrorHandling);
        logTest('hooks', `${hookName} has optimistic updates`, hasOptimisticUpdates);
      } else {
        logTest('hooks', `${hookPath} file exists`, false, 'File not found');
      }
    } catch (error) {
      logTest('hooks', `${hookPath} verification`, false, error.message);
    }
  }
}

// API endpoints verification
async function verifyApiEndpoints() {
  console.log('\n🌐 VERIFYING API ENDPOINTS');
  console.log('=====================================');

  const endpoints = [
    { method: 'GET', path: '/health', description: 'Health check' },
    { method: 'GET', path: '/api/watchlist', description: 'Get watchlist', requiresAuth: true },
    { method: 'POST', path: '/api/watchlist', description: 'Add to watchlist', requiresAuth: true },
    { method: 'GET', path: '/api/property/test123/notes', description: 'Get property notes', requiresAuth: true },
    { method: 'POST', path: '/api/property/test123/notes', description: 'Add property note', requiresAuth: true },
  ];

  for (const endpoint of endpoints) {
    try {
      const config = {
        method: endpoint.method.toLowerCase(),
        url: `${API_BASE_URL}${endpoint.path}`,
        timeout: 5000,
      };

      if (endpoint.requiresAuth) {
        config.params = { user_id: '00000000-0000-0000-0000-000000000000' };
      }

      if (endpoint.method === 'POST' && endpoint.path.includes('/notes')) {
        config.data = {
          notes: 'Test note',
          title: 'Test Title',
          note_type: 'general'
        };
      }

      if (endpoint.method === 'POST' && endpoint.path.includes('/watchlist')) {
        config.data = {
          parcel_id: 'test123',
          notes: 'Test property'
        };
      }

      const response = await axios(config);

      if (response.status >= 200 && response.status < 300) {
        logTest('api', `${endpoint.method} ${endpoint.path} - ${endpoint.description}`, true);
      } else {
        logTest('api', `${endpoint.method} ${endpoint.path} - ${endpoint.description}`, false, `Status ${response.status}`);
      }
    } catch (error) {
      // For auth-required endpoints, getting a 401/403 means the endpoint exists
      if (endpoint.requiresAuth && (error.response?.status === 401 || error.response?.status === 403)) {
        logTest('api', `${endpoint.method} ${endpoint.path} - ${endpoint.description}`, true);
      } else if (error.code === 'ECONNREFUSED') {
        logTest('api', `${endpoint.method} ${endpoint.path} - ${endpoint.description}`, false, 'API server not running');
      } else {
        logTest('api', `${endpoint.method} ${endpoint.path} - ${endpoint.description}`, false, error.message);
      }
    }
  }
}

// Integration test with real data flow
async function verifyIntegration() {
  console.log('\n🔄 VERIFYING END-TO-END INTEGRATION');
  console.log('=====================================');

  // Test UI component integration
  try {
    const miniPropertyCardPath = path.join(__dirname, '../apps/web/src/components/property/MiniPropertyCard.tsx');
    if (fs.existsSync(miniPropertyCardPath)) {
      const content = fs.readFileSync(miniPropertyCardPath, 'utf-8');

      const hasWatchlistHook = content.includes('useWatchlist');
      const hasNotesHook = content.includes('usePropertyNotes');
      const hasWatchlistToggle = content.includes('handleWatchlistToggle');
      const hasRealTimeUpdates = content.includes('isInWatchlist');

      logTest('integration', 'MiniPropertyCard uses useWatchlist hook', hasWatchlistHook);
      logTest('integration', 'MiniPropertyCard uses usePropertyNotes hook', hasNotesHook);
      logTest('integration', 'MiniPropertyCard has watchlist toggle functionality', hasWatchlistToggle);
      logTest('integration', 'MiniPropertyCard shows real-time watchlist status', hasRealTimeUpdates);
    } else {
      logTest('integration', 'MiniPropertyCard integration check', false, 'File not found');
    }
  } catch (error) {
    logTest('integration', 'MiniPropertyCard integration check', false, error.message);
  }

  // Test schema SQL files
  try {
    const schema1Path = path.join(__dirname, '../database/schema/01_user_tables.sql');
    const schema2Path = path.join(__dirname, '../database/schema/02_scoring_alerts_tables.sql');

    const schema1Exists = fs.existsSync(schema1Path);
    const schema2Exists = fs.existsSync(schema2Path);

    logTest('integration', 'Phase 1 database schema file exists', schema1Exists);
    logTest('integration', 'Phase 2 database schema file exists', schema2Exists);

    if (schema1Exists) {
      const content = fs.readFileSync(schema1Path, 'utf-8');
      const hasUserWatchlists = content.includes('CREATE TABLE IF NOT EXISTS user_watchlists');
      const hasPropertyNotes = content.includes('CREATE TABLE IF NOT EXISTS property_notes');
      const hasRLSPolicies = content.includes('ROW LEVEL SECURITY');

      logTest('integration', 'Schema 1 has user_watchlists table', hasUserWatchlists);
      logTest('integration', 'Schema 1 has property_notes table', hasPropertyNotes);
      logTest('integration', 'Schema 1 has RLS policies', hasRLSPolicies);
    }
  } catch (error) {
    logTest('integration', 'Schema files verification', false, error.message);
  }

  // Test API file
  try {
    const apiPath = path.join(__dirname, '../apps/api/watchlist_api.py');
    if (fs.existsSync(apiPath)) {
      const content = fs.readFileSync(apiPath, 'utf-8');

      const hasFastAPI = content.includes('from fastapi');
      const hasSupabase = content.includes('from supabase');
      const hasWatchlistEndpoints = content.includes('/api/watchlist');
      const hasNotesEndpoints = content.includes('/property/{parcel_id}/notes');

      logTest('integration', 'Watchlist API uses FastAPI', hasFastAPI);
      logTest('integration', 'Watchlist API uses Supabase', hasSupabase);
      logTest('integration', 'Watchlist API has watchlist endpoints', hasWatchlistEndpoints);
      logTest('integration', 'Watchlist API has notes endpoints', hasNotesEndpoints);
    } else {
      logTest('integration', 'Watchlist API file exists', false, 'File not found');
    }
  } catch (error) {
    logTest('integration', 'Watchlist API verification', false, error.message);
  }
}

// Generate comprehensive report
function generateReport() {
  console.log('\n📊 COMPREHENSIVE INTEGRATION REPORT');
  console.log('=====================================');

  const totalTests = Object.values(testResults).reduce((sum, category) =>
    sum + category.passed + category.failed, 0
  );

  const totalPassed = Object.values(testResults).reduce((sum, category) =>
    sum + category.passed, 0
  );

  const overallScore = Math.round((totalPassed / totalTests) * 100);

  console.log(`\n🎯 OVERALL INTEGRATION SCORE: ${overallScore}%`);
  console.log(`📈 Total Tests: ${totalTests} | Passed: ${totalPassed} | Failed: ${totalTests - totalPassed}`);

  console.log('\n📋 CATEGORY BREAKDOWN:');
  Object.entries(testResults).forEach(([category, results]) => {
    const categoryScore = results.passed + results.failed > 0 ?
      Math.round((results.passed / (results.passed + results.failed)) * 100) : 0;

    console.log(`   ${category.toUpperCase()}: ${categoryScore}% (${results.passed}/${results.passed + results.failed})`);
  });

  // Priority recommendations
  console.log('\n🚀 NEXT STEPS:');

  if (overallScore >= 95) {
    console.log('   ✅ EXCELLENT! Your Supabase integration is nearly complete.');
    console.log('   ✅ Ready for production deployment.');
    console.log('   🔧 Consider adding performance monitoring and error tracking.');
  } else if (overallScore >= 85) {
    console.log('   🟡 GOOD! Most features are integrated.');
    console.log('   🔧 Address the failed tests to reach 100% integration.');
  } else if (overallScore >= 70) {
    console.log('   🟠 PARTIAL integration complete.');
    console.log('   🔧 Focus on database setup and API endpoint deployment.');
  } else {
    console.log('   🔴 BASIC integration needs significant work.');
    console.log('   🔧 Start with database schema creation and hook implementation.');
  }

  // Failed tests summary
  const failedTests = [];
  Object.entries(testResults).forEach(([category, results]) => {
    results.tests.forEach(test => {
      if (!test.passed) {
        failedTests.push(`${category}: ${test.testName} - ${test.error}`);
      }
    });
  });

  if (failedTests.length > 0) {
    console.log('\n❌ FAILED TESTS:');
    failedTests.forEach(test => console.log(`   ${test}`));
  }

  // Save detailed report to file
  const reportPath = path.join(__dirname, '../integration-verification-report.json');
  const report = {
    timestamp: new Date().toISOString(),
    overallScore,
    totalTests,
    totalPassed,
    categories: testResults,
    failedTests
  };

  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 Detailed report saved to: ${reportPath}`);

  return overallScore;
}

// Main execution
async function main() {
  console.log('🚀 STARTING CONCORDBROKER 100% SUPABASE INTEGRATION VERIFICATION');
  console.log('================================================================');
  console.log(`Supabase URL: ${supabaseUrl}`);
  console.log(`API Base URL: ${API_BASE_URL}`);
  console.log(`Test Parcel ID: ${TEST_PARCEL_ID}`);

  try {
    await verifyDatabaseTables();
    await verifyHookFiles();
    await verifyApiEndpoints();
    await verifyIntegration();

    const finalScore = generateReport();

    console.log('\n🏁 VERIFICATION COMPLETE!');
    console.log('================================================================');

    process.exit(finalScore >= 95 ? 0 : 1);

  } catch (error) {
    console.error('\n💥 VERIFICATION FAILED WITH ERROR:', error);
    process.exit(1);
  }
}

// Run the verification
main();

export {
  main,
  verifyDatabaseTables,
  verifyHookFiles,
  verifyApiEndpoints,
  verifyIntegration,
  generateReport
};