#!/usr/bin/env node
/**
 * Environment Variable Synchronizer Agent
 * Syncs .env files across all worktrees automatically
 *
 * Features:
 * - Watches main repo .env files for changes
 * - Auto-syncs to all worktrees
 * - Encrypts sensitive values
 * - Supports different configs for testing/production
 * - Integrates with Claude Code hooks
 *
 * Usage:
 *   node env-sync-agent.js          # Start watching
 *   node env-sync-agent.js --sync   # Sync once
 *   node env-sync-agent.js --hook   # Hook integration mode
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

// Configuration
const BASE_DIR = 'C:/Users/gsima/Documents/MyProject';
const MAIN_REPO = `${BASE_DIR}/ConcordBroker`;

const ENV_FILES = [
  '.env',
  '.env.local',
  '.env.mcp',
  'apps/web/.env',
];

const WORKTREE_PATTERNS = [
  `${BASE_DIR}/ConcordBroker-*`,
];

// Sensitive keys to encrypt
const SENSITIVE_KEYS = [
  'API_KEY',
  'SECRET',
  'TOKEN',
  'PASSWORD',
  'PRIVATE_KEY',
  'SERVICE_ROLE_KEY',
];

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

class EnvSyncAgent {
  constructor() {
    this.worktrees = [];
    this.encryptionKey = this.getEncryptionKey();
    this.watchedFiles = new Map();
  }

  getEncryptionKey() {
    // Use machine ID as encryption key base
    try {
      const machineId = execSync('wmic csproduct get uuid', { encoding: 'utf-8' })
        .split('\n')[1]
        .trim();
      return crypto.createHash('sha256').update(machineId).digest();
    } catch (error) {
      log('Warning: Could not get machine ID, using fallback key', 'yellow');
      return crypto.randomBytes(32);
    }
  }

  encrypt(value) {
    try {
      const iv = crypto.randomBytes(16);
      const cipher = crypto.createCipheriv('aes-256-cbc', this.encryptionKey, iv);

      let encrypted = cipher.update(value, 'utf8', 'hex');
      encrypted += cipher.final('hex');

      return `ENC:${iv.toString('hex')}:${encrypted}`;
    } catch (error) {
      log(`Encryption error: ${error.message}`, 'red');
      return value;
    }
  }

  decrypt(encryptedValue) {
    try {
      if (!encryptedValue.startsWith('ENC:')) {
        return encryptedValue;
      }

      const parts = encryptedValue.substring(4).split(':');
      const iv = Buffer.from(parts[0], 'hex');
      const encrypted = parts[1];

      const decipher = crypto.createDecipheriv('aes-256-cbc', this.encryptionKey, iv);

      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');

      return decrypted;
    } catch (error) {
      log(`Decryption error: ${error.message}`, 'red');
      return encryptedValue;
    }
  }

  isSensitiveKey(key) {
    return SENSITIVE_KEYS.some(pattern => key.toUpperCase().includes(pattern));
  }

  parseEnvFile(filePath) {
    if (!fs.existsSync(filePath)) {
      return {};
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const env = {};

    content.split('\n').forEach(line => {
      line = line.trim();

      // Skip comments and empty lines
      if (!line || line.startsWith('#')) {
        return;
      }

      const match = line.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();

        // Remove quotes
        if ((value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.substring(1, value.length - 1);
        }

        env[key] = value;
      }
    });

    return env;
  }

  writeEnvFile(filePath, env, encrypt = false) {
    const lines = [];

    lines.push(`# Auto-synced by Environment Synchronizer Agent`);
    lines.push(`# Last sync: ${new Date().toISOString()}`);
    lines.push('');

    Object.entries(env).forEach(([key, value]) => {
      if (encrypt && this.isSensitiveKey(key) && !value.startsWith('ENC:')) {
        value = this.encrypt(value);
      }

      // Add quotes if value contains spaces
      if (value.includes(' ')) {
        value = `"${value}"`;
      }

      lines.push(`${key}=${value}`);
    });

    fs.writeFileSync(filePath, lines.join('\n') + '\n');
  }

  async discoverWorktrees() {
    this.worktrees = [];

    try {
      const output = execSync('git worktree list', { cwd: MAIN_REPO, encoding: 'utf-8' });
      const lines = output.split('\n').filter(line => line.trim());

      lines.forEach(line => {
        const match = line.match(/^(.+?)\s+([a-f0-9]+)\s+\[(.+)\]/);
        if (match) {
          const worktreePath = match[1].trim();
          const branch = match[3].trim();

          // Skip main repo
          if (worktreePath !== MAIN_REPO) {
            this.worktrees.push({ path: worktreePath, branch });
          }
        }
      });

      log(`Discovered ${this.worktrees.length} worktrees`, 'cyan');
    } catch (error) {
      log(`Error discovering worktrees: ${error.message}`, 'red');
    }
  }

  async syncEnvFile(envFileName, targetWorktree = null) {
    const sourceFile = path.join(MAIN_REPO, envFileName);

    if (!fs.existsSync(sourceFile)) {
      log(`Source file not found: ${envFileName}`, 'yellow');
      return;
    }

    // Parse source environment
    const sourceEnv = this.parseEnvFile(sourceFile);
    const keyCount = Object.keys(sourceEnv).length;

    log(`\n📄 Syncing ${envFileName} (${keyCount} variables)...`, 'blue');

    const worktreesToSync = targetWorktree ? [targetWorktree] : this.worktrees;
    let syncedCount = 0;

    for (const worktree of worktreesToSync) {
      const targetFile = path.join(worktree.path, envFileName);
      const targetDir = path.dirname(targetFile);

      // Create directory if it doesn't exist
      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }

      // Check if file already exists
      const existingEnv = this.parseEnvFile(targetFile);

      // Merge with existing (don't overwrite worktree-specific vars)
      const mergedEnv = { ...sourceEnv, ...existingEnv };

      // Determine if this is a testing worktree
      const isTestingWorktree = worktree.branch.includes('test') ||
                                 worktree.branch.includes('experimental');

      // Write file (encrypt if not testing)
      this.writeEnvFile(targetFile, mergedEnv, !isTestingWorktree);

      log(`  ✅ Synced to ${worktree.branch}`, 'green');
      syncedCount++;
    }

    log(`  📊 Synced ${envFileName} to ${syncedCount} worktrees\n`, 'cyan');
  }

  async syncAll() {
    log('🔄 Starting environment synchronization...', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

    await this.discoverWorktrees();

    if (this.worktrees.length === 0) {
      log('No worktrees found to sync', 'yellow');
      return;
    }

    for (const envFile of ENV_FILES) {
      await this.syncEnvFile(envFile);
    }

    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log('✅ Synchronization complete!', 'green');
  }

  async startWatching() {
    log('👁️  Environment Synchronizer Agent Started', 'bright');
    log('   Watching for .env file changes...', 'cyan');
    log('   Press Ctrl+C to stop\n', 'yellow');

    await this.discoverWorktrees();

    // Watch each env file
    for (const envFile of ENV_FILES) {
      const filePath = path.join(MAIN_REPO, envFile);

      if (!fs.existsSync(filePath)) {
        continue;
      }

      const watcher = fs.watch(filePath, async (eventType, filename) => {
        if (eventType === 'change') {
          log(`\n🔔 Detected change in ${envFile}`, 'yellow');
          await this.syncEnvFile(envFile);
        }
      });

      this.watchedFiles.set(envFile, watcher);
      log(`  📁 Watching: ${envFile}`, 'cyan');
    }

    // Handle shutdown
    process.on('SIGINT', () => {
      log('\n\n🛑 Stopping Environment Synchronizer...', 'yellow');

      this.watchedFiles.forEach((watcher, file) => {
        watcher.close();
        log(`  Stopped watching: ${file}`, 'cyan');
      });

      log('✅ Agent stopped', 'green');
      process.exit(0);
    });

    // Keep process alive
    await new Promise(() => {});
  }

  async runHook(hookType, data = {}) {
    log(`🪝 Hook triggered: ${hookType}`, 'cyan');

    switch (hookType) {
      case 'post-change':
        // Check if any .env files changed
        const changedFiles = data.files || [];
        const envChanged = changedFiles.some(file =>
          ENV_FILES.some(envFile => file.includes(envFile))
        );

        if (envChanged) {
          log('  Detected .env file change, syncing...', 'yellow');
          await this.syncAll();
        }
        break;

      case 'worktree-created':
        // Sync to newly created worktree
        if (data.worktreePath) {
          const worktree = { path: data.worktreePath, branch: data.branch || 'unknown' };
          log(`  Syncing env to new worktree: ${data.branch}`, 'yellow');

          for (const envFile of ENV_FILES) {
            await this.syncEnvFile(envFile, worktree);
          }
        }
        break;

      case 'dependency-update':
        // Re-sync after dependency updates (may have new env vars)
        log('  Dependency updated, checking for new env vars...', 'yellow');
        await this.syncAll();
        break;

      default:
        log(`  Unknown hook type: ${hookType}`, 'yellow');
    }
  }
}

// CLI Interface
async function main() {
  const agent = new EnvSyncAgent();
  const args = process.argv.slice(2);

  if (args.includes('--sync')) {
    // One-time sync
    await agent.syncAll();
  } else if (args.includes('--hook')) {
    // Hook mode
    const hookType = args[args.indexOf('--hook') + 1] || 'post-change';
    const dataIndex = args.indexOf('--data');
    const data = dataIndex >= 0 ? JSON.parse(args[dataIndex + 1]) : {};

    await agent.runHook(hookType, data);
  } else {
    // Watch mode (default)
    await agent.startWatching();
  }
}

if (require.main === module) {
  main().catch(error => {
    log(`Fatal error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = { EnvSyncAgent };
