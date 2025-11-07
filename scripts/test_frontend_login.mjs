#!/usr/bin/env node
/**
 * Frontend Login Simulation Test
 * Simulates the exact login flow that happens in the browser
 */

import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

// Supabase configuration (same as frontend)
const supabaseUrl = 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

console.log('='.repeat(60));
console.log('Frontend Login Simulation Test');
console.log('='.repeat(60));

async function testLogin(email, password) {
  console.log(`\n[TEST] Testing login with:`);
  console.log(`  Email: ${email}`);
  console.log(`  Password: ${password.replace(/./g, '*')}`);

  try {
    // Step 1: Query for user (exact same as frontend)
    console.log('\n[STEP 1] Querying for user...');
    const { data: users, error: queryError } = await supabase
      .from('admin_users')
      .select('*')
      .eq('email', email.toLowerCase())
      .eq('status', 'active')
      .limit(1);

    if (queryError) {
      console.log('[FAIL] Query error:', queryError);
      return false;
    }

    if (!users || users.length === 0) {
      console.log('[FAIL] User not found');
      return false;
    }

    console.log('[PASS] User found:', users[0].email);

    const user = users[0];

    // Step 2: Check password hash exists
    console.log('\n[STEP 2] Checking password hash...');
    if (!user.password_hash) {
      console.log('[FAIL] No password hash set');
      return false;
    }

    console.log('[PASS] Password hash exists');

    // Step 3: Verify password (exact same as frontend)
    console.log('\n[STEP 3] Verifying password with bcrypt...');
    const passwordValid = await bcrypt.compare(password, user.password_hash);

    if (!passwordValid) {
      console.log('[FAIL] Password does not match');
      return false;
    }

    console.log('[PASS] Password verified successfully');

    // Step 4: Simulate session storage (frontend would do this)
    console.log('\n[STEP 4] Would set session storage:');
    console.log('  adminAuthenticated: true');
    console.log('  adminUserId:', user.id);
    console.log('  adminUserEmail:', user.email);
    console.log('  adminUserName:', user.name);
    console.log('  adminUserRole:', user.role);

    console.log('\n[SUCCESS] Login simulation completed successfully!');
    return true;

  } catch (err) {
    console.log('[ERROR] Exception:', err);
    return false;
  }
}

async function runTests() {
  // Test 1: Correct credentials
  console.log('\n' + '='.repeat(60));
  console.log('TEST 1: Login with correct credentials');
  console.log('='.repeat(60));
  const test1 = await testLogin('admin@concordbroker.com', 'Admin123!');

  // Test 2: Wrong password
  console.log('\n' + '='.repeat(60));
  console.log('TEST 2: Login with wrong password (should fail)');
  console.log('='.repeat(60));
  const test2 = await testLogin('admin@concordbroker.com', 'wrongpassword');

  // Test 3: Wrong email
  console.log('\n' + '='.repeat(60));
  console.log('TEST 3: Login with wrong email (should fail)');
  console.log('='.repeat(60));
  const test3 = await testLogin('wrong@email.com', 'Admin123!');

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('Test Summary');
  console.log('='.repeat(60));
  console.log(`Test 1 (correct credentials): ${test1 ? 'PASS ✓' : 'FAIL ✗'}`);
  console.log(`Test 2 (wrong password): ${!test2 ? 'PASS ✓' : 'FAIL ✗'}`);
  console.log(`Test 3 (wrong email): ${!test3 ? 'PASS ✓' : 'FAIL ✗'}`);

  const allPassed = test1 && !test2 && !test3;

  if (allPassed) {
    console.log('\n🎉 All tests passed! The login system is working correctly.');
    console.log('\nYou can now login at:');
    console.log('  URL: http://localhost:5191/admin/login');
    console.log('  Email: admin@concordbroker.com');
    console.log('  Password: Admin123!');
    process.exit(0);
  } else {
    console.log('\n❌ Some tests failed. Please check the errors above.');
    process.exit(1);
  }
}

runTests().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
