#!/usr/bin/env node

/**
 * ConcordBroker Verification Agent
 *
 * Permanent, always-active verification sub-agent that automatically checks
 * and verifies all work after changes are made to the project.
 *
 * Features:
 * - Continuous file watching
 * - Automatic test selection based on changes
 * - Intelligent verification routing
 * - Real-time status reporting
 * - Self-healing capabilities
 */

const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const http = require('http');

// Configuration
const CONFIG = {
  port: 3009,
  logDir: path.join(__dirname, 'logs'),
  statusFile: path.join(__dirname, 'logs', 'verification-status.json'),
  watchDirs: [
    path.join(__dirname, 'apps', 'web', 'src'),
    path.join(__dirname, 'apps', 'api'),
    path.join(__dirname, 'mcp-server'),
  ],
  ignorePatterns: [
    /node_modules/,
    /\.git/,
    /dist/,
    /build/,
    /coverage/,
    /\.cache/,
    /playwright-report/,
    /test-results/,
  ],
  verificationTimeout: 120000, // 2 minutes
  debounceDelay: 2000, // 2 seconds
};

// Verification state
let verificationQueue = [];
let isVerifying = false;
let lastVerification = null;
let verificationHistory = [];
let fileWatchers = [];

// Ensure logs directory exists
if (!fs.existsSync(CONFIG.logDir)) {
  fs.mkdirSync(CONFIG.logDir, { recursive: true });
}

// Initialize status file
function initializeStatus() {
  const initialStatus = {
    agentStarted: new Date().toISOString(),
    status: 'active',
    port: CONFIG.port,
    verificationCount: 0,
    lastVerification: null,
    currentlyVerifying: false,
    history: [],
  };

  fs.writeFileSync(CONFIG.statusFile, JSON.stringify(initialStatus, null, 2));
  console.log('✅ Verification agent status initialized');
}

// Update status file
function updateStatus(updates) {
  try {
    const current = JSON.parse(fs.readFileSync(CONFIG.statusFile, 'utf-8'));
    const updated = { ...current, ...updates, lastUpdate: new Date().toISOString() };
    fs.writeFileSync(CONFIG.statusFile, JSON.stringify(updated, null, 2));
  } catch (error) {
    console.error('❌ Failed to update status:', error.message);
  }
}

// Execute command with promise
function executeCommand(command, options = {}) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error(`Command timeout: ${command}`));
    }, CONFIG.verificationTimeout);

    exec(command, options, (error, stdout, stderr) => {
      clearTimeout(timeout);
      if (error) {
        reject({ error, stdout, stderr });
      } else {
        resolve({ stdout, stderr });
      }
    });
  });
}

// Determine verification steps based on file type
function getVerificationSteps(filePath) {
  const steps = [];
  const ext = path.extname(filePath);
  const relativePath = path.relative(__dirname, filePath);

  // TypeScript/React files
  if (['.ts', '.tsx'].includes(ext) && relativePath.includes('apps/web')) {
    steps.push(
      { name: 'TypeScript Check', command: 'npm run verify:types', critical: true },
      { name: 'ESLint', command: 'npm run verify:lint', critical: true },
    );

    // If it's a component file, add Playwright tests
    if (relativePath.includes('/components/') || relativePath.includes('/pages/')) {
      const testFile = relativePath.replace(/\.(tsx|ts)$/, '.spec.ts');
      if (fs.existsSync(path.join(__dirname, testFile))) {
        steps.push({
          name: 'Component Tests',
          command: `npx playwright test ${testFile}`,
          critical: false,
        });
      }
    }

    // If it's PropertySearch, run property search tests
    if (relativePath.includes('PropertySearch.tsx')) {
      steps.push({
        name: 'Property Search Tests',
        command: 'npx playwright test apps/web/tests/verify_property_search_fix.spec.ts',
        critical: true,
      });
    }
  }

  // Python files
  if (ext === '.py' && relativePath.includes('apps/api')) {
    steps.push(
      { name: 'Python Syntax', command: `python -m py_compile "${filePath}"`, critical: true },
      { name: 'API Health', command: 'curl -f http://localhost:8000/health', critical: false },
    );
  }

  // JSON/Config files
  if (['.json', '.yml', '.yaml'].includes(ext)) {
    steps.push({
      name: 'JSON Validation',
      command: `node -e "JSON.parse(require('fs').readFileSync('${filePath}', 'utf-8'))"`,
      critical: true,
    });
  }

  // MCP server files
  if (relativePath.includes('mcp-server')) {
    steps.push({
      name: 'MCP Health',
      command: 'curl -f http://localhost:3005/health',
      critical: false,
    });
  }

  return steps;
}

// Run verification for a file
async function verifyFile(filePath) {
  const startTime = Date.now();
  const steps = getVerificationSteps(filePath);

  if (steps.length === 0) {
    console.log(`⏭️  No verification needed for: ${path.relative(__dirname, filePath)}`);
    return { skipped: true };
  }

  console.log(`\n🔍 Verifying: ${path.relative(__dirname, filePath)}`);
  console.log(`   Running ${steps.length} verification step(s)...`);

  const results = {
    file: path.relative(__dirname, filePath),
    timestamp: new Date().toISOString(),
    duration: 0,
    steps: [],
    passed: true,
    critical_failures: [],
  };

  for (const step of steps) {
    const stepStart = Date.now();
    console.log(`   ⏳ ${step.name}...`);

    try {
      const { stdout, stderr } = await executeCommand(step.command);
      const stepDuration = Date.now() - stepStart;

      results.steps.push({
        name: step.name,
        passed: true,
        duration: stepDuration,
        output: stdout.substring(0, 500), // Limit output
      });

      console.log(`   ✅ ${step.name} (${stepDuration}ms)`);
    } catch (error) {
      const stepDuration = Date.now() - stepStart;
      const isCritical = step.critical;

      results.steps.push({
        name: step.name,
        passed: false,
        critical: isCritical,
        duration: stepDuration,
        error: error.error?.message || 'Command failed',
        output: error.stderr || error.stdout,
      });

      console.log(`   ${isCritical ? '❌' : '⚠️'} ${step.name} FAILED (${stepDuration}ms)`);

      if (isCritical) {
        results.critical_failures.push(step.name);
        results.passed = false;
      }
    }
  }

  results.duration = Date.now() - startTime;

  // Save verification result
  saveVerificationResult(results);

  // Print summary
  console.log(`\n📊 Verification Summary:`);
  console.log(`   File: ${results.file}`);
  console.log(`   Duration: ${results.duration}ms`);
  console.log(`   Status: ${results.passed ? '✅ PASSED' : '❌ FAILED'}`);
  if (results.critical_failures.length > 0) {
    console.log(`   Critical Failures: ${results.critical_failures.join(', ')}`);
  }

  return results;
}

// Save verification result
function saveVerificationResult(result) {
  verificationHistory.push(result);

  // Keep only last 50 results
  if (verificationHistory.length > 50) {
    verificationHistory = verificationHistory.slice(-50);
  }

  updateStatus({
    verificationCount: verificationHistory.length,
    lastVerification: result,
    currentlyVerifying: false,
    history: verificationHistory.slice(-10), // Last 10 in status
  });

  // Also append to detailed log
  const logFile = path.join(CONFIG.logDir, 'verification-history.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(result) + '\n');
}

// Process verification queue
async function processQueue() {
  if (isVerifying || verificationQueue.length === 0) {
    return;
  }

  isVerifying = true;
  updateStatus({ currentlyVerifying: true });

  const filePath = verificationQueue.shift();

  try {
    await verifyFile(filePath);
  } catch (error) {
    console.error('❌ Verification error:', error);
  }

  isVerifying = false;
  updateStatus({ currentlyVerifying: false });

  // Process next item if any
  if (verificationQueue.length > 0) {
    setTimeout(processQueue, 100);
  }
}

// Debounced file change handler
const fileChangeHandlers = new Map();

function handleFileChange(filePath) {
  // Clear existing timeout for this file
  if (fileChangeHandlers.has(filePath)) {
    clearTimeout(fileChangeHandlers.get(filePath));
  }

  // Set new timeout
  const timeout = setTimeout(() => {
    fileChangeHandlers.delete(filePath);

    // Add to queue if not already present
    if (!verificationQueue.includes(filePath)) {
      console.log(`\n📝 File changed: ${path.relative(__dirname, filePath)}`);
      verificationQueue.push(filePath);
      processQueue();
    }
  }, CONFIG.debounceDelay);

  fileChangeHandlers.set(filePath, timeout);
}

// Setup file watchers
function setupFileWatchers() {
  console.log('👀 Setting up file watchers...');

  for (const dir of CONFIG.watchDirs) {
    if (!fs.existsSync(dir)) {
      console.log(`   ⚠️  Directory not found: ${dir}`);
      continue;
    }

    try {
      const watcher = fs.watch(dir, { recursive: true }, (eventType, filename) => {
        if (!filename) return;

        const filePath = path.join(dir, filename);

        // Skip if matches ignore patterns
        if (CONFIG.ignorePatterns.some(pattern => pattern.test(filePath))) {
          return;
        }

        // Only process files that exist and are files (not directories)
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          handleFileChange(filePath);
        }
      });

      fileWatchers.push(watcher);
      console.log(`   ✅ Watching: ${path.relative(__dirname, dir)}`);
    } catch (error) {
      console.error(`   ❌ Failed to watch ${dir}:`, error.message);
    }
  }

  console.log(`✅ File watchers active (${fileWatchers.length} directories)\n`);
}

// HTTP server for status and control
function startHttpServer() {
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');

    if (req.url === '/health') {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'healthy',
        agent: 'verification-agent',
        port: CONFIG.port,
        uptime: process.uptime(),
        verificationCount: verificationHistory.length,
        isVerifying,
        queueLength: verificationQueue.length,
      }));
    } else if (req.url === '/status') {
      res.writeHead(200);
      res.end(fs.readFileSync(CONFIG.statusFile, 'utf-8'));
    } else if (req.url === '/history') {
      res.writeHead(200);
      res.end(JSON.stringify(verificationHistory, null, 2));
    } else if (req.url === '/queue') {
      res.writeHead(200);
      res.end(JSON.stringify({
        queue: verificationQueue.map(f => path.relative(__dirname, f)),
        isVerifying,
      }, null, 2));
    } else {
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  });

  server.listen(CONFIG.port, () => {
    console.log(`🌐 Verification agent listening on http://localhost:${CONFIG.port}`);
    console.log(`   /health   - Health check`);
    console.log(`   /status   - Current status`);
    console.log(`   /history  - Verification history`);
    console.log(`   /queue    - Current queue\n`);
  });

  return server;
}

// Main startup
function main() {
  console.log('\n🚀 Starting ConcordBroker Verification Agent...\n');

  // Initialize
  initializeStatus();

  // Start HTTP server
  const server = startHttpServer();

  // Setup file watchers
  setupFileWatchers();

  console.log('✅ Verification agent is ACTIVE and ready!\n');
  console.log('   Monitoring for file changes...');
  console.log('   Automatic verification will run on detected changes.\n');

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Shutting down verification agent...');

    fileWatchers.forEach(watcher => watcher.close());
    server.close();

    updateStatus({
      status: 'stopped',
      stoppedAt: new Date().toISOString(),
    });

    console.log('✅ Verification agent stopped gracefully.\n');
    process.exit(0);
  });

  // Handle errors
  process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught exception:', error);
    updateStatus({
      status: 'error',
      lastError: error.message,
      errorAt: new Date().toISOString(),
    });
  });
}

// CLI handling
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.includes('--status')) {
    if (fs.existsSync(CONFIG.statusFile)) {
      console.log(fs.readFileSync(CONFIG.statusFile, 'utf-8'));
    } else {
      console.log('No status file found. Agent may not be running.');
    }
    process.exit(0);
  } else if (args.includes('--restart')) {
    console.log('Restarting verification agent...');
    exec('taskkill /F /IM node.exe /FI "WINDOWTITLE eq verification-agent*"', () => {
      setTimeout(() => {
        spawn('node', [__filename], {
          detached: true,
          stdio: 'inherit',
          windowsVerbatimArguments: true,
        });
      }, 1000);
    });
    process.exit(0);
  } else {
    main();
  }
}

module.exports = { CONFIG, getVerificationSteps, verifyFile };
