#!/usr/bin/env node
/**
 * Worktree Lifecycle Agent
 * Automates worktree creation, configuration, and startup
 *
 * Usage:
 *   node worktree-lifecycle-agent.js start feature/ui-consolidation
 *   node worktree-lifecycle-agent.js stop feature/ui-consolidation
 *   node worktree-lifecycle-agent.js restart feature/ui-consolidation
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Configuration
const BASE_DIR = 'C:/Users/gsima/Documents/MyProject';
const MAIN_REPO = `${BASE_DIR}/ConcordBroker`;

const PORT_MAP = {
  'master': 5191,
  'feature/ui-consolidation': 5192,
  'feature/api-enhancements': 5193,
  'feature/database-optimization': 5194,
  'feature/agent-development': 5195,
  'hotfix/production': 5196,
  'experimental/new-features': 5197,
  'testing/integration': 5198,
};

// Color output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function execCommand(command, cwd = MAIN_REPO) {
  try {
    return execSync(command, { cwd, encoding: 'utf-8', stdio: 'pipe' });
  } catch (error) {
    throw new Error(`Command failed: ${command}\n${error.message}`);
  }
}

class WorktreeLifecycleAgent {
  constructor(branch) {
    this.branch = branch;
    this.worktreeName = `ConcordBroker-${branch.replace(/\//g, '-')}`;
    this.worktreePath = `${BASE_DIR}/${this.worktreeName}`;
    this.port = PORT_MAP[branch] || 5199;
    this.devServerProcess = null;
  }

  async start() {
    log('🚀 Worktree Lifecycle Agent Starting...', 'bright');
    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue');

    try {
      await this.createWorktree();
      await this.configurePort();
      await this.installDependencies();
      await this.startDevServer();
      await this.openClaudeCode();

      log(`\n✅ Worktree lifecycle completed successfully!`, 'green');
      log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue');
      log(`Branch: ${this.branch}`, 'bright');
      log(`Path: ${this.worktreePath}`, 'yellow');
      log(`Port: ${this.port}`, 'green');
      log(`URL: http://localhost:${this.port}`, 'blue');
      log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue');
    } catch (error) {
      log(`\n❌ Error: ${error.message}`, 'red');
      process.exit(1);
    }
  }

  async createWorktree() {
    log(`\n[1/5] Creating worktree for branch: ${this.branch}...`, 'blue');

    // Check if worktree already exists
    if (fs.existsSync(this.worktreePath)) {
      log(`  ⚠️  Worktree already exists, skipping creation`, 'yellow');
      return;
    }

    try {
      // Check if branch exists locally
      const localBranches = execCommand('git branch --list', MAIN_REPO);
      const remoteBranches = execCommand('git branch -r --list', MAIN_REPO);

      if (localBranches.includes(this.branch)) {
        // Branch exists locally
        execCommand(`git worktree add "${this.worktreePath}" "${this.branch}"`, MAIN_REPO);
      } else if (remoteBranches.includes(`origin/${this.branch}`)) {
        // Branch exists on remote
        execCommand(`git worktree add "${this.worktreePath}" -b "${this.branch}" "origin/${this.branch}"`, MAIN_REPO);
      } else {
        // Create new branch
        log(`  📝 Branch doesn't exist, creating new branch...`, 'yellow');
        execCommand(`git worktree add "${this.worktreePath}" -b "${this.branch}"`, MAIN_REPO);
      }

      log(`  ✅ Worktree created successfully`, 'green');
    } catch (error) {
      throw new Error(`Failed to create worktree: ${error.message}`);
    }
  }

  async configurePort() {
    log(`\n[2/5] Configuring port ${this.port}...`, 'blue');

    const viteConfigPath = path.join(this.worktreePath, 'apps/web/vite.config.ts');

    if (!fs.existsSync(viteConfigPath)) {
      throw new Error(`vite.config.ts not found at ${viteConfigPath}`);
    }

    // Backup original config
    const backupPath = `${viteConfigPath}.backup`;
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(viteConfigPath, backupPath);
    }

    // Update port in vite config
    let config = fs.readFileSync(viteConfigPath, 'utf-8');
    config = config.replace(/port:\s*\d+,/, `port: ${this.port},`);
    fs.writeFileSync(viteConfigPath, config);

    log(`  ✅ Port configured to ${this.port}`, 'green');
  }

  async installDependencies() {
    log(`\n[3/5] Installing dependencies...`, 'blue');

    const nodeModulesPath = path.join(this.worktreePath, 'node_modules');

    // Check if node_modules already exists and is recent
    if (fs.existsSync(nodeModulesPath)) {
      const stats = fs.statSync(nodeModulesPath);
      const ageInHours = (Date.now() - stats.mtimeMs) / (1000 * 60 * 60);

      if (ageInHours < 24) {
        log(`  ⚠️  node_modules is recent (${ageInHours.toFixed(1)}h old), skipping install`, 'yellow');
        return;
      }
    }

    try {
      log(`  📦 Running npm install (this may take a few minutes)...`, 'yellow');
      execCommand('npm install', this.worktreePath);
      log(`  ✅ Dependencies installed successfully`, 'green');
    } catch (error) {
      throw new Error(`Failed to install dependencies: ${error.message}`);
    }
  }

  async startDevServer() {
    log(`\n[4/5] Starting dev server on port ${this.port}...`, 'blue');

    // Check if port is already in use
    try {
      const portCheck = execCommand(`netstat -ano | findstr :${this.port}`);
      if (portCheck) {
        log(`  ⚠️  Port ${this.port} is already in use, server may already be running`, 'yellow');
        return;
      }
    } catch (error) {
      // Port not in use, continue
    }

    // Start dev server in background
    const webPath = path.join(this.worktreePath, 'apps/web');

    log(`  🔄 Starting Vite dev server...`, 'yellow');

    // Spawn dev server as detached process
    this.devServerProcess = spawn('npm', ['run', 'dev'], {
      cwd: webPath,
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
    });

    // Save PID for later management
    const pidFile = path.join(this.worktreePath, '.dev-server.pid');
    fs.writeFileSync(pidFile, String(this.devServerProcess.pid));

    // Wait for server to start (check for "ready" message)
    await new Promise((resolve) => {
      const timeout = setTimeout(() => {
        log(`  ✅ Dev server started (PID: ${this.devServerProcess.pid})`, 'green');
        resolve();
      }, 3000);

      this.devServerProcess.stdout.on('data', (data) => {
        if (data.toString().includes('ready') || data.toString().includes('Local')) {
          clearTimeout(timeout);
          log(`  ✅ Dev server ready on http://localhost:${this.port}`, 'green');
          resolve();
        }
      });
    });

    // Detach the process so it continues running
    this.devServerProcess.unref();
  }

  async openClaudeCode() {
    log(`\n[5/5] Opening Claude Code...`, 'blue');

    try {
      // Try to open in Claude Code
      // This will open a new window with the worktree
      const command = os.platform() === 'win32'
        ? `code "${this.worktreePath}"`
        : `open -a "Visual Studio Code" "${this.worktreePath}"`;

      execCommand(command);
      log(`  ✅ Claude Code opened in new window`, 'green');
    } catch (error) {
      log(`  ⚠️  Could not auto-open Claude Code, please open manually:`, 'yellow');
      log(`     ${this.worktreePath}`, 'yellow');
    }
  }

  async stop() {
    log(`\n🛑 Stopping worktree: ${this.branch}...`, 'yellow');

    // Read PID file
    const pidFile = path.join(this.worktreePath, '.dev-server.pid');

    if (fs.existsSync(pidFile)) {
      const pid = fs.readFileSync(pidFile, 'utf-8').trim();

      try {
        // Kill dev server process
        if (os.platform() === 'win32') {
          execCommand(`taskkill /F /PID ${pid}`);
        } else {
          execCommand(`kill -9 ${pid}`);
        }

        fs.unlinkSync(pidFile);
        log(`  ✅ Dev server stopped (PID: ${pid})`, 'green');
      } catch (error) {
        log(`  ⚠️  Could not stop dev server (PID: ${pid})`, 'yellow');
      }
    } else {
      log(`  ⚠️  No running dev server found`, 'yellow');
    }
  }

  async restart() {
    await this.stop();
    await this.start();
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    log('Usage: node worktree-lifecycle-agent.js [start|stop|restart] BRANCH_NAME', 'red');
    log('Example: node worktree-lifecycle-agent.js start feature/ui-consolidation', 'yellow');
    process.exit(1);
  }

  const [command, branch] = args;
  const agent = new WorktreeLifecycleAgent(branch);

  switch (command) {
    case 'start':
      await agent.start();
      break;
    case 'stop':
      await agent.stop();
      break;
    case 'restart':
      await agent.restart();
      break;
    default:
      log(`Unknown command: ${command}`, 'red');
      log('Valid commands: start, stop, restart', 'yellow');
      process.exit(1);
  }
}

if (require.main === module) {
  main().catch(error => {
    log(`Fatal error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = { WorktreeLifecycleAgent };
