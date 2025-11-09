#!/usr/bin/env node
/**
 * Agent Hook Integration Test Suite
 * Tests all agents with their hook integrations
 */

const { EnvSyncAgent } = require('./env-sync-agent.cjs');
const { CodeQualityAgent } = require('./code-quality-agent.cjs');
const { AutoCommitAgent } = require('./auto-commit-agent.cjs');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${colors[color]}[${timestamp}] ${message}${colors.reset}`);
}

async function testEnvSyncAgent() {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  log('Testing Environment Sync Agent', 'bright');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

  try {
    const agent = new EnvSyncAgent();

    // Test encryption/decryption
    log('\n1. Testing encryption...', 'cyan');
    const testValue = 'test-secret-key-12345';
    const encrypted = agent.encrypt(testValue);
    const decrypted = agent.decrypt(encrypted);

    if (decrypted === testValue) {
      log('   ✅ Encryption/Decryption works', 'green');
    } else {
      log('   ❌ Encryption/Decryption failed', 'red');
      return false;
    }

    // Test sensitive key detection
    log('\n2. Testing sensitive key detection...', 'cyan');
    const isSensitive = agent.isSensitiveKey('SUPABASE_API_KEY');
    if (isSensitive) {
      log('   ✅ Sensitive key detection works', 'green');
    } else {
      log('   ❌ Sensitive key detection failed', 'red');
      return false;
    }

    // Test hook integration
    log('\n3. Testing hook integration...', 'cyan');
    await agent.runHook('post-change', { files: ['.env'] });
    log('   ✅ Hook integration works', 'green');

    return true;
  } catch (error) {
    log(`   ❌ Test failed: ${error.message}`, 'red');
    return false;
  }
}

async function testCodeQualityAgent() {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  log('Testing Code Quality Agent', 'bright');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

  try {
    const agent = new CodeQualityAgent();

    // Test agent initialization
    log('\n1. Testing agent initialization...', 'cyan');
    if (agent.workingDir && agent.errors && agent.warnings) {
      log('   ✅ Agent initialized correctly', 'green');
    } else {
      log('   ❌ Agent initialization failed', 'red');
      return false;
    }

    // Test hook integration
    log('\n2. Testing hook integration...', 'cyan');

    // Test post-change hook (non-blocking)
    await agent.runHook('post-change', {});
    log('   ✅ post-change hook works', 'green');

    return true;
  } catch (error) {
    log(`   ❌ Test failed: ${error.message}`, 'red');
    return false;
  }
}

async function testAutoCommitAgent() {
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  log('Testing Auto-Commit Agent', 'bright');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

  try {
    const agent = new AutoCommitAgent();

    // Test agent initialization
    log('\n1. Testing agent initialization...', 'cyan');
    if (agent.workingDir && agent.commitInterval) {
      log('   ✅ Agent initialized correctly', 'green');
    } else {
      log('   ❌ Agent initialization failed', 'red');
      return false;
    }

    // Test uncommitted changes detection
    log('\n2. Testing git status check...', 'cyan');
    const hasChanges = agent.hasUncommittedChanges();
    log(`   ℹ️  Uncommitted changes: ${hasChanges}`, 'cyan');

    // Test changed files detection
    log('\n3. Testing changed files detection...', 'cyan');
    const files = agent.getChangedFiles();
    log(`   ℹ️  Changed files: ${files.length}`, 'cyan');

    // Test commit message generation
    log('\n4. Testing commit message generation...', 'cyan');
    const message = agent.generateCommitMessage();
    if (message && message.startsWith('Auto-commit:')) {
      log(`   ✅ Generated message: ${message.split('\n')[0]}`, 'green');
    } else {
      log('   ❌ Message generation failed', 'red');
      return false;
    }

    // Test hook integration
    log('\n5. Testing hook integration...', 'cyan');
    await agent.runHook('post-save', { file: 'test.ts' });
    log('   ✅ Hook integration works', 'green');

    return true;
  } catch (error) {
    log(`   ❌ Test failed: ${error.message}`, 'red');
    return false;
  }
}

async function runAllTests() {
  log('🧪 Agent Hook Integration Test Suite', 'bright');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

  const results = {
    envSync: false,
    codeQuality: false,
    autoCommit: false,
  };

  // Run tests
  results.envSync = await testEnvSyncAgent();
  results.codeQuality = await testCodeQualityAgent();
  results.autoCommit = await testAutoCommitAgent();

  // Print summary
  log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  log('📊 Test Summary', 'bright');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

  const testResults = [
    { name: 'Environment Sync Agent', result: results.envSync },
    { name: 'Code Quality Agent', result: results.codeQuality },
    { name: 'Auto-Commit Agent', result: results.autoCommit },
  ];

  testResults.forEach(({ name, result }) => {
    const status = result ? '✅ PASSED' : '❌ FAILED';
    const color = result ? 'green' : 'red';
    log(`${status.padEnd(12)} ${name}`, color);
  });

  const passedCount = Object.values(results).filter(r => r).length;
  const totalCount = Object.keys(results).length;

  log(`\n📊 Total: ${passedCount}/${totalCount} tests passed`, passedCount === totalCount ? 'green' : 'yellow');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

  return passedCount === totalCount;
}

if (require.main === module) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      log(`Fatal error: ${error.message}`, 'red');
      process.exit(1);
    });
}

module.exports = { runAllTests };
