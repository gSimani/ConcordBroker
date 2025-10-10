#!/usr/bin/env node
/**
 * Ensure Single Dev Server - Port Management System
 *
 * Purpose: Prevent port conflicts and duplicate development servers
 * - Kills zombie dev servers on old ports (5177, 5178, etc.)
 * - Ensures only ONE dev server runs at a time
 * - Enforces standard port 5191
 *
 * Usage:
 *   node scripts/ensure-single-dev-server.cjs
 *   npm run dev:clean  (kills zombies then starts dev)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const STANDARD_PORT = 5191;
const OLD_PORTS = [5177, 5178, 5179, 5180]; // Zombie ports to kill
const SESSION_LOCK_FILE = path.join(__dirname, '..', '.dev-session.json');

/**
 * Check if a port is in use
 */
function checkPort(port) {
  try {
    const result = execSync(
      `netstat -ano | findstr :${port} | findstr LISTENING`,
      { encoding: 'utf8', stdio: 'pipe' }
    );
    return result.trim().length > 0;
  } catch {
    return false;
  }
}

/**
 * Get PID using a specific port
 */
function getPID(port) {
  try {
    const result = execSync(
      `netstat -ano | findstr :${port} | findstr LISTENING`,
      { encoding: 'utf8', stdio: 'pipe' }
    );

    // Extract PID from last column
    const match = result.trim().match(/\s+(\d+)\s*$/);
    return match ? match[1] : null;
  } catch {
    return null;
  }
}

/**
 * Kill process by PID
 */
function killProcess(pid) {
  try {
    execSync(`taskkill /F /PID ${pid}`, { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

/**
 * Kill all dev servers on old ports
 */
function killZombiePorts() {
  console.log('🔍 Scanning for zombie dev servers...\n');

  let zombiesFound = false;

  OLD_PORTS.forEach(port => {
    if (checkPort(port)) {
      zombiesFound = true;
      const pid = getPID(port);

      console.log(`⚠️  WARNING: Found zombie dev server`);
      console.log(`   Port: ${port}`);
      console.log(`   PID: ${pid || 'Unknown'}`);

      if (pid) {
        console.log(`   Killing process...`);
        if (killProcess(pid)) {
          console.log(`   ✅ Successfully killed PID ${pid}\n`);
        } else {
          console.log(`   ❌ Failed to kill PID ${pid}\n`);
          console.log(`   Manual cleanup required: taskkill /F /PID ${pid}\n`);
        }
      }
    }
  });

  if (!zombiesFound) {
    console.log('✅ No zombie dev servers found\n');
  }
}

/**
 * Check standard port status
 */
function checkStandardPort() {
  console.log(`📡 Checking standard development port ${STANDARD_PORT}...\n`);

  if (checkPort(STANDARD_PORT)) {
    const pid = getPID(STANDARD_PORT);
    console.log(`✅ Port ${STANDARD_PORT} is active (PID: ${pid || 'Unknown'})`);
    console.log(`   This is the correct port for development\n`);
    return true;
  } else {
    console.log(`📍 Port ${STANDARD_PORT} is available`);
    console.log(`   Ready to start dev server\n`);
    return false;
  }
}

/**
 * Get current git info
 */
function getGitInfo() {
  try {
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    const commit = execSync('git rev-parse --short HEAD', { encoding: 'utf8' }).trim();
    const dirty = execSync('git status --porcelain', { encoding: 'utf8' }).trim().length > 0;

    return { branch, commit, dirty };
  } catch {
    return { branch: 'unknown', commit: 'unknown', dirty: false };
  }
}

/**
 * Update session lock file
 */
function updateSessionLock() {
  const git = getGitInfo();

  const session = {
    activePort: STANDARD_PORT,
    sessionId: new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19),
    timestamp: new Date().toISOString(),
    git: {
      branch: git.branch,
      commit: git.commit,
      hasUncommittedChanges: git.dirty
    },
    ports: {
      standard: STANDARD_PORT,
      active: checkPort(STANDARD_PORT),
      zombies: OLD_PORTS.filter(p => checkPort(p))
    }
  };

  try {
    fs.writeFileSync(SESSION_LOCK_FILE, JSON.stringify(session, null, 2));
    console.log(`📝 Session lock file updated: ${SESSION_LOCK_FILE}\n`);
  } catch (err) {
    console.log(`⚠️  Could not update session lock file: ${err.message}\n`);
  }
}

/**
 * Display port registry
 */
function displayPortRegistry() {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('              PORT REGISTRY - ACTIVE SERVICES              ');
  console.log('═══════════════════════════════════════════════════════════\n');

  const ports = [
    { port: 3001, name: 'MCP Server (Primary)', expected: true },
    { port: 3005, name: 'MCP Server (Ultimate)', expected: true },
    { port: 5191, name: 'Dev Server (STANDARD)', expected: true },
    { port: 8000, name: 'FastAPI Backend', expected: true },
    { port: 8001, name: 'AI Data Flow Orchestrator', expected: false },
    { port: 8003, name: 'LangChain Integration', expected: false },
  ];

  ports.forEach(({ port, name, expected }) => {
    const active = checkPort(port);
    const status = active ? '✅ ACTIVE' : (expected ? '⚠️  INACTIVE' : '○  Inactive');
    const pid = active ? getPID(port) : null;

    console.log(`${status}  Port ${port.toString().padEnd(5)} - ${name}`);
    if (pid) {
      console.log(`           PID: ${pid}`);
    }
  });

  console.log('\n═══════════════════════════════════════════════════════════\n');
}

/**
 * Main execution
 */
function main() {
  console.log('\n');
  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║     PORT MANAGEMENT SYSTEM - ENSURE SINGLE DEV SERVER    ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  console.log('\n');

  // Step 1: Kill zombies
  killZombiePorts();

  // Step 2: Check standard port
  const portActive = checkStandardPort();

  // Step 3: Display port registry
  displayPortRegistry();

  // Step 4: Update session lock
  updateSessionLock();

  // Step 5: Final status
  const git = getGitInfo();
  console.log('📊 CURRENT SESSION STATUS');
  console.log('─────────────────────────────────────────────────────────────');
  console.log(`Branch:  ${git.branch}`);
  console.log(`Commit:  ${git.commit}`);
  console.log(`Dirty:   ${git.dirty ? '⚠️  YES - Uncommitted changes exist' : '✅ NO - Clean working directory'}`);
  console.log(`Port:    ${STANDARD_PORT} (${portActive ? 'Active' : 'Available'})`);
  console.log('─────────────────────────────────────────────────────────────\n');

  if (git.dirty) {
    console.log('⚠️  REMINDER: Commit your changes before ending session!');
    console.log('   git add -A');
    console.log('   git commit -m "your message"');
    console.log('   git push\n');
  }

  console.log('✅ Port management check complete\n');
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { checkPort, killZombiePorts, updateSessionLock };
