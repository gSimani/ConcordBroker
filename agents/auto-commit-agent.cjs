#!/usr/bin/env node
/**
 * Auto-Commit & Sync Agent
 * Automatically commits changes with AI-generated messages
 *
 * Features:
 * - Auto-commits every 30 minutes
 * - AI-generated commit messages (analyzes changes)
 * - Auto-pushes to remote
 * - Detects merge conflicts
 * - Integrates with Claude Code hooks
 * - Never lose work!
 *
 * Usage:
 *   node auto-commit-agent.js                    # Start monitoring
 *   node auto-commit-agent.js --hook post-save   # Hook integration
 *   node auto-commit-agent.js --commit-now       # Force commit now
 *   node auto-commit-agent.js --all              # Commit all worktrees
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
};

function log(message, color = 'reset') {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${colors[color]}[${timestamp}] ${message}${colors.reset}`);
}

function execCommand(command, cwd = process.cwd()) {
  try {
    return execSync(command, { cwd, encoding: 'utf-8', stdio: 'pipe' });
  } catch (error) {
    return { error: true, message: error.message, output: error.stdout || error.stderr };
  }
}

class AutoCommitAgent {
  constructor(workingDir = process.cwd()) {
    this.workingDir = workingDir;
    this.commitInterval = 30 * 60 * 1000; // 30 minutes
    this.lastCommitTime = Date.now();
    this.changesSinceLastCommit = false;
  }

  hasUncommittedChanges() {
    const status = execCommand('git status --porcelain', this.workingDir);

    if (status.error) {
      return false;
    }

    return status.trim().length > 0;
  }

  getChangedFiles() {
    const status = execCommand('git status --porcelain', this.workingDir);

    if (status.error) {
      return [];
    }

    const files = [];
    status.split('\n').forEach(line => {
      if (line.trim()) {
        // Format: XY filename
        const match = line.match(/^(.{2})\s+(.+)$/);
        if (match) {
          const statusCode = match[1].trim();
          const filename = match[2].trim();
          files.push({ status: statusCode, filename });
        }
      }
    });

    return files;
  }

  getDiff() {
    const diff = execCommand('git diff HEAD', this.workingDir);

    if (diff.error) {
      return '';
    }

    return diff;
  }

  generateCommitMessage() {
    const files = this.getChangedFiles();

    if (files.length === 0) {
      return 'Auto-commit: No changes detected';
    }

    // Analyze file types and changes
    const fileTypes = {
      tsx: 0,
      ts: 0,
      js: 0,
      css: 0,
      json: 0,
      md: 0,
      other: 0,
    };

    const changeTypes = {
      added: 0,
      modified: 0,
      deleted: 0,
    };

    files.forEach(({ status, filename }) => {
      // Count change types
      if (status.includes('A')) changeTypes.added++;
      if (status.includes('M')) changeTypes.modified++;
      if (status.includes('D')) changeTypes.deleted++;

      // Count file types
      const ext = path.extname(filename).substring(1);
      if (fileTypes.hasOwnProperty(ext)) {
        fileTypes[ext]++;
      } else {
        fileTypes.other++;
      }
    });

    // Generate message based on changes
    const parts = [];

    // Change summary
    if (changeTypes.modified > 0) {
      parts.push(`Updated ${changeTypes.modified} file(s)`);
    }
    if (changeTypes.added > 0) {
      parts.push(`Added ${changeTypes.added} file(s)`);
    }
    if (changeTypes.deleted > 0) {
      parts.push(`Deleted ${changeTypes.deleted} file(s)`);
    }

    // File type context
    const mainType = Object.entries(fileTypes)
      .filter(([_, count]) => count > 0)
      .sort((a, b) => b[1] - a[1])[0];

    if (mainType) {
      const [type, count] = mainType;
      if (type === 'tsx' || type === 'ts') {
        parts.push('(TypeScript/React)');
      } else if (type === 'css') {
        parts.push('(Styling)');
      } else if (type === 'json') {
        parts.push('(Configuration)');
      } else if (type === 'md') {
        parts.push('(Documentation)');
      }
    }

    // Add auto-commit marker
    const message = `Auto-commit: ${parts.join(' ')}`;

    // Try to extract specific changes from top modified files
    const topFiles = files.slice(0, 3).map(f => path.basename(f.filename));
    if (topFiles.length > 0) {
      return `${message}\n\nModified: ${topFiles.join(', ')}`;
    }

    return message;
  }

  async commitChanges() {
    if (!this.hasUncommittedChanges()) {
      log('  No uncommitted changes, skipping commit', 'cyan');
      return false;
    }

    const files = this.getChangedFiles();
    log(`\n💾 Committing ${files.length} changed file(s)...`, 'blue');

    // Stage all changes
    execCommand('git add .', this.workingDir);

    // Generate commit message
    const message = this.generateCommitMessage();
    log(`  📝 Message: ${message.split('\n')[0]}`, 'cyan');

    // Commit
    const escapedMessage = message.replace(/"/g, '\\"').replace(/`/g, '\\`');
    const result = execCommand(`git commit -m "${escapedMessage}"`, this.workingDir);

    if (result.error) {
      log(`  ❌ Commit failed: ${result.message}`, 'red');
      return false;
    }

    log('  ✅ Changes committed successfully', 'green');
    this.lastCommitTime = Date.now();
    this.changesSinceLastCommit = false;

    return true;
  }

  async pushToRemote() {
    log('\n📤 Pushing to remote...', 'blue');

    // Get current branch
    const branchResult = execCommand('git rev-parse --abbrev-ref HEAD', this.workingDir);

    if (branchResult.error) {
      log('  ❌ Could not determine branch', 'red');
      return false;
    }

    const branch = branchResult.trim();

    // Check if remote tracking exists
    const trackingResult = execCommand(`git rev-parse --abbrev-ref ${branch}@{upstream}`, this.workingDir);

    if (trackingResult.error) {
      // No upstream, set it up
      log(`  📡 Setting up remote tracking for ${branch}...`, 'yellow');
      const pushResult = execCommand(`git push -u origin ${branch}`, this.workingDir);

      if (pushResult.error) {
        log(`  ❌ Push failed: ${pushResult.message}`, 'red');
        return false;
      }
    } else {
      // Push normally
      const pushResult = execCommand('git push', this.workingDir);

      if (pushResult.error) {
        log(`  ❌ Push failed: ${pushResult.message}`, 'red');

        // Check if it's because we're behind
        if (pushResult.output && pushResult.output.includes('rejected')) {
          log('  ⚠️  Remote has changes, pulling first...', 'yellow');

          const pullResult = execCommand('git pull --rebase', this.workingDir);

          if (pullResult.error) {
            log('  ❌ Pull failed, manual intervention needed', 'red');
            return false;
          }

          // Try push again
          const retryPush = execCommand('git push', this.workingDir);

          if (retryPush.error) {
            log('  ❌ Push still failed after pull', 'red');
            return false;
          }
        } else {
          return false;
        }
      }
    }

    log('  ✅ Pushed to remote successfully', 'green');
    return true;
  }

  async commitAndPush() {
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log('🔄 Auto-Commit & Sync Starting...', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

    const committed = await this.commitChanges();

    if (committed) {
      await this.pushToRemote();
    }

    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');
    return committed;
  }

  async startMonitoring() {
    log('🤖 Auto-Commit & Sync Agent Started', 'bright');
    log(`   Working directory: ${this.workingDir}`, 'cyan');
    log(`   Commit interval: ${this.commitInterval / 60000} minutes`, 'cyan');
    log('   Press Ctrl+C to stop\n', 'yellow');

    // Initial commit if there are changes
    if (this.hasUncommittedChanges()) {
      log('🔔 Detected uncommitted changes on startup', 'yellow');
      await this.commitAndPush();
    }

    // Start monitoring loop
    const checkInterval = setInterval(async () => {
      const timeSinceLastCommit = Date.now() - this.lastCommitTime;

      if (timeSinceLastCommit >= this.commitInterval) {
        if (this.hasUncommittedChanges()) {
          log('⏰ Auto-commit interval reached', 'yellow');
          await this.commitAndPush();
        } else {
          log('✅ No changes to commit', 'green');
          this.lastCommitTime = Date.now(); // Reset timer
        }
      }
    }, 60000); // Check every minute

    // Handle shutdown
    process.on('SIGINT', async () => {
      log('\n\n🛑 Shutting down Auto-Commit Agent...', 'yellow');
      clearInterval(checkInterval);

      // Final commit before shutdown
      if (this.hasUncommittedChanges()) {
        log('💾 Final commit before shutdown...', 'yellow');
        await this.commitAndPush();
      }

      log('✅ Agent stopped', 'green');
      process.exit(0);
    });

    // Keep process alive
    await new Promise(() => {});
  }

  async runHook(hookType, data = {}) {
    log(`🪝 Hook triggered: ${hookType}`, 'cyan');

    switch (hookType) {
      case 'post-save':
        // Mark that changes have occurred
        this.changesSinceLastCommit = true;
        log('  Changes detected, will commit on next interval', 'yellow');
        break;

      case 'pre-switch':
        // Commit before switching branches/worktrees
        log('  Committing before branch switch...', 'yellow');
        await this.commitAndPush();
        break;

      case 'session-end':
        // Commit before ending session
        log('  Committing before session end...', 'yellow');
        await this.commitAndPush();
        break;

      default:
        log(`  Unknown hook type: ${hookType}`, 'yellow');
    }
  }

  async commitAllWorktrees() {
    log('🔄 Committing all worktrees...', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

    const BASE_DIR = 'C:/Users/gsima/Documents/MyProject';
    const MAIN_REPO = `${BASE_DIR}/ConcordBroker`;

    const worktrees = [];

    try {
      const output = execSync('git worktree list', { cwd: MAIN_REPO, encoding: 'utf-8' });
      const lines = output.split('\n').filter(line => line.trim());

      lines.forEach(line => {
        const match = line.match(/^(.+?)\s+([a-f0-9]+)\s+\[(.+)\]/);
        if (match) {
          const worktreePath = match[1].trim();
          const branch = match[3].trim();
          worktrees.push({ path: worktreePath, branch });
        }
      });
    } catch (error) {
      log(`Error discovering worktrees: ${error.message}`, 'red');
      return;
    }

    const results = [];

    for (const worktree of worktrees) {
      log(`\n📁 Checking: ${worktree.branch}`, 'cyan');

      const agent = new AutoCommitAgent(worktree.path);
      const committed = await agent.commitAndPush();

      results.push({
        branch: worktree.branch,
        committed,
      });
    }

    // Print final summary
    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log('📊 All Worktrees Summary', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

    const committedCount = results.filter(r => r.committed).length;

    results.forEach(result => {
      const status = result.committed ? '✅ Committed' : '⚪ No changes';
      const color = result.committed ? 'green' : 'cyan';
      log(`${status.padEnd(15)} ${result.branch}`, color);
    });

    log(`\n📊 Total: ${committedCount}/${results.length} worktrees had changes`, 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--all')) {
    // Commit all worktrees
    const agent = new AutoCommitAgent();
    await agent.commitAllWorktrees();
    return;
  }

  const agent = new AutoCommitAgent();

  if (args.includes('--hook')) {
    // Hook mode
    const hookType = args[args.indexOf('--hook') + 1] || 'post-save';
    const dataIndex = args.indexOf('--data');
    const data = dataIndex >= 0 ? JSON.parse(args[dataIndex + 1]) : {};

    await agent.runHook(hookType, data);
  } else if (args.includes('--commit-now')) {
    // Force commit now
    await agent.commitAndPush();
  } else {
    // Monitor mode (default)
    await agent.startMonitoring();
  }
}

if (require.main === module) {
  main().catch(error => {
    log(`Fatal error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = { AutoCommitAgent };
