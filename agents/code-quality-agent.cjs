#!/usr/bin/env node
/**
 * Code Quality Gate Agent
 * Runs linting, type-checking, and auto-fixes before commits
 *
 * Features:
 * - Pre-commit quality checks
 * - Auto-fixes common issues (formatting, imports)
 * - Type checking with TypeScript
 * - ESLint validation
 * - Prevents commits with errors
 * - Integrates with Claude Code hooks
 *
 * Usage:
 *   node code-quality-agent.js                    # Check current worktree
 *   node code-quality-agent.js --hook pre-commit  # Hook integration
 *   node code-quality-agent.js --fix              # Auto-fix issues
 *   node code-quality-agent.js --all              # Check all worktrees
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

class CodeQualityAgent {
  constructor(workingDir = process.cwd()) {
    this.workingDir = workingDir;
    this.errors = [];
    this.warnings = [];
    this.fixed = [];
    this.passed = true;
  }

  async checkTypeScript() {
    log('\n📘 Running TypeScript type checking...', 'blue');

    const tsconfigPath = path.join(this.workingDir, 'tsconfig.json');

    if (!fs.existsSync(tsconfigPath)) {
      log('  ⚠️  No tsconfig.json found, skipping TypeScript check', 'yellow');
      return true;
    }

    const result = execCommand('npx tsc --noEmit', this.workingDir);

    if (result.error) {
      const output = result.output || '';
      const errorCount = (output.match(/error TS/g) || []).length;

      this.errors.push({
        type: 'typescript',
        count: errorCount,
        message: `${errorCount} type error(s) found`,
      });

      log(`  ❌ TypeScript: ${errorCount} error(s)`, 'red');
      this.passed = false;
      return false;
    }

    log('  ✅ TypeScript: No errors', 'green');
    return true;
  }

  async checkESLint(autoFix = false) {
    log('\n🔍 Running ESLint...', 'blue');

    const eslintConfig = path.join(this.workingDir, '.eslintrc.cjs');

    if (!fs.existsSync(eslintConfig)) {
      log('  ⚠️  No .eslintrc.cjs found, skipping ESLint', 'yellow');
      return true;
    }

    const fixFlag = autoFix ? '--fix' : '';
    const result = execCommand(`npx eslint . --ext ts,tsx ${fixFlag}`, this.workingDir);

    if (result.error) {
      const output = result.output || '';
      const errorCount = (output.match(/error/gi) || []).length;
      const warningCount = (output.match(/warning/gi) || []).length;

      if (errorCount > 0) {
        this.errors.push({
          type: 'eslint',
          count: errorCount,
          message: `${errorCount} ESLint error(s)`,
        });
        log(`  ❌ ESLint: ${errorCount} error(s), ${warningCount} warning(s)`, 'red');
        this.passed = false;
      } else {
        this.warnings.push({
          type: 'eslint',
          count: warningCount,
          message: `${warningCount} ESLint warning(s)`,
        });
        log(`  ⚠️  ESLint: ${warningCount} warning(s)`, 'yellow');
      }

      return errorCount === 0;
    }

    if (autoFix) {
      log('  ✅ ESLint: Auto-fixed issues', 'green');
      this.fixed.push('ESLint auto-fixes applied');
    } else {
      log('  ✅ ESLint: No errors', 'green');
    }

    return true;
  }

  async checkPrettier(autoFix = false) {
    log('\n✨ Running Prettier...', 'blue');

    const prettierConfig = path.join(this.workingDir, '.prettierrc');

    if (!fs.existsSync(prettierConfig)) {
      log('  ⚠️  No .prettierrc found, skipping Prettier', 'yellow');
      return true;
    }

    const checkCommand = autoFix
      ? 'npx prettier --write "src/**/*.{ts,tsx,css}"'
      : 'npx prettier --check "src/**/*.{ts,tsx,css}"';

    const result = execCommand(checkCommand, this.workingDir);

    if (result.error && !autoFix) {
      const output = result.output || '';
      const fileCount = (output.match(/\.(ts|tsx|css)/g) || []).length;

      this.warnings.push({
        type: 'prettier',
        count: fileCount,
        message: `${fileCount} file(s) need formatting`,
      });

      log(`  ⚠️  Prettier: ${fileCount} file(s) need formatting`, 'yellow');
      return true; // Formatting issues are warnings, not blockers
    }

    if (autoFix) {
      log('  ✅ Prettier: Formatted files', 'green');
      this.fixed.push('Prettier formatting applied');
    } else {
      log('  ✅ Prettier: All files formatted correctly', 'green');
    }

    return true;
  }

  async checkUnusedImports() {
    log('\n📦 Checking for unused imports...', 'blue');

    // This is a simple check - you could use ts-prune or similar tools
    const srcPath = path.join(this.workingDir, 'src');

    if (!fs.existsSync(srcPath)) {
      log('  ⚠️  No src directory found', 'yellow');
      return true;
    }

    // For now, just report that this check would run
    // In a real implementation, you'd use a tool like ts-prune
    log('  ℹ️  Unused import check: Would run ts-prune here', 'cyan');

    return true;
  }

  async runAllChecks(autoFix = false) {
    log('🔒 Code Quality Gate Agent Starting...', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log(`Working directory: ${this.workingDir}`, 'cyan');

    if (autoFix) {
      log('Mode: Auto-fix enabled', 'yellow');
    }

    // Run checks
    await this.checkTypeScript();
    await this.checkESLint(autoFix);
    await this.checkPrettier(autoFix);
    await this.checkUnusedImports();

    // Print summary
    this.printSummary();

    return this.passed;
  }

  printSummary() {
    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log('📊 Quality Check Summary', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');

    if (this.errors.length > 0) {
      log('\n❌ ERRORS:', 'red');
      this.errors.forEach(err => {
        log(`   ${err.type}: ${err.message}`, 'red');
      });
    }

    if (this.warnings.length > 0) {
      log('\n⚠️  WARNINGS:', 'yellow');
      this.warnings.forEach(warn => {
        log(`   ${warn.type}: ${warn.message}`, 'yellow');
      });
    }

    if (this.fixed.length > 0) {
      log('\n✨ AUTO-FIXED:', 'green');
      this.fixed.forEach(fix => {
        log(`   ${fix}`, 'green');
      });
    }

    if (this.passed && this.errors.length === 0) {
      log('\n✅ All quality checks passed!', 'green');
    } else {
      log('\n❌ Quality gate FAILED - fix errors before committing', 'red');
    }

    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');
  }

  async runHook(hookType, data = {}) {
    log(`🪝 Hook triggered: ${hookType}`, 'cyan');

    switch (hookType) {
      case 'pre-commit':
        log('  Running pre-commit quality checks...', 'yellow');

        // Auto-fix on pre-commit
        const passed = await this.runAllChecks(true);

        if (!passed) {
          log('\n❌ Commit blocked due to quality issues', 'red');
          log('   Fix the errors above and try again', 'yellow');
          process.exit(1);
        }

        log('\n✅ Pre-commit checks passed, proceeding with commit', 'green');
        break;

      case 'post-change':
        // Run checks without auto-fix, just inform
        log('  Running post-change quality checks...', 'yellow');
        await this.runAllChecks(false);
        break;

      case 'pre-push':
        log('  Running pre-push quality checks...', 'yellow');

        const pushPassed = await this.runAllChecks(false);

        if (!pushPassed) {
          log('\n❌ Push blocked due to quality issues', 'red');
          log('   Fix the errors above before pushing', 'yellow');
          process.exit(1);
        }

        log('\n✅ Pre-push checks passed', 'green');
        break;

      default:
        log(`  Unknown hook type: ${hookType}`, 'yellow');
    }
  }

  async checkAllWorktrees() {
    log('🔄 Checking code quality in all worktrees...', 'bright');
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
      log(`   Path: ${worktree.path}`, 'dim');

      const agent = new CodeQualityAgent(worktree.path);
      const passed = await agent.runAllChecks(false);

      results.push({
        branch: worktree.branch,
        passed,
        errors: agent.errors.length,
        warnings: agent.warnings.length,
      });
    }

    // Print final summary
    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log('📊 All Worktrees Summary', 'bright');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');

    const passedCount = results.filter(r => r.passed).length;
    const totalErrors = results.reduce((sum, r) => sum + r.errors, 0);
    const totalWarnings = results.reduce((sum, r) => sum + r.warnings, 0);

    results.forEach(result => {
      const status = result.passed ? '✅' : '❌';
      const errStr = result.errors > 0 ? ` ${result.errors} errors` : '';
      const warnStr = result.warnings > 0 ? ` ${result.warnings} warnings` : '';
      const summary = errStr || warnStr || 'clean';

      log(`${status} ${result.branch.padEnd(35)} ${summary}`, result.passed ? 'green' : 'red');
    });

    log(`\n📊 Statistics:`, 'bright');
    log(`   Passed: ${passedCount}/${results.length}`, passedCount === results.length ? 'green' : 'yellow');
    log(`   Total Errors: ${totalErrors}`, totalErrors === 0 ? 'green' : 'red');
    log(`   Total Warnings: ${totalWarnings}`, totalWarnings === 0 ? 'green' : 'yellow');

    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', 'blue');
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--all')) {
    // Check all worktrees
    const agent = new CodeQualityAgent();
    await agent.checkAllWorktrees();
    return;
  }

  const agent = new CodeQualityAgent();

  if (args.includes('--hook')) {
    // Hook mode
    const hookType = args[args.indexOf('--hook') + 1] || 'pre-commit';
    const dataIndex = args.indexOf('--data');
    const data = dataIndex >= 0 ? JSON.parse(args[dataIndex + 1]) : {};

    await agent.runHook(hookType, data);
  } else if (args.includes('--fix')) {
    // Auto-fix mode
    const passed = await agent.runAllChecks(true);
    process.exit(passed ? 0 : 1);
  } else {
    // Check mode (default)
    const passed = await agent.runAllChecks(false);
    process.exit(passed ? 0 : 1);
  }
}

if (require.main === module) {
  main().catch(error => {
    log(`Fatal error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = { CodeQualityAgent };
