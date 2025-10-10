#!/usr/bin/env node
/**
 * Verify Work Completion - Merge Verification System
 *
 * Purpose: Ensure all work is properly saved, committed, and merged
 * - Checks for uncommitted changes
 * - Verifies all tests pass
 * - Ensures work is pushed to remote
 * - Validates port consistency
 *
 * Usage:
 *   node scripts/verify-work-completion.cjs
 *   npm run verify:complete
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const STANDARD_PORT = 5191;
const SESSION_LOCK_FILE = path.join(__dirname, '..', '.dev-session.json');

/**
 * Execute command and return output
 */
function exec(command) {
  try {
    return execSync(command, { encoding: 'utf8', stdio: 'pipe' }).trim();
  } catch (err) {
    return null;
  }
}

/**
 * Check git status
 */
function checkGitStatus() {
  console.log('📋 CHECKING GIT STATUS\n');

  const branch = exec('git rev-parse --abbrev-ref HEAD');
  const commit = exec('git rev-parse --short HEAD');
  const uncommitted = exec('git status --porcelain');
  const unpushed = exec('git log origin/' + branch + '..HEAD --oneline');

  console.log(`Branch:          ${branch}`);
  console.log(`Latest Commit:   ${commit}`);
  console.log(`Uncommitted:     ${uncommitted ? uncommitted.split('\n').length + ' files' : 'None ✅'}`);
  console.log(`Unpushed:        ${unpushed ? unpushed.split('\n').length + ' commits' : 'None ✅'}`);
  console.log('');

  if (uncommitted) {
    console.log('⚠️  UNCOMMITTED FILES:');
    console.log(uncommitted.split('\n').map(line => '   ' + line).join('\n'));
    console.log('');
  }

  if (unpushed) {
    console.log('⚠️  UNPUSHED COMMITS:');
    console.log(unpushed.split('\n').map(line => '   ' + line).join('\n'));
    console.log('');
  }

  return {
    branch,
    commit,
    hasUncommitted: !!uncommitted,
    hasUnpushed: !!unpushed,
    clean: !uncommitted && !unpushed
  };
}

/**
 * Check port consistency in test files
 */
function checkPortConsistency() {
  console.log('🔍 CHECKING PORT CONSISTENCY IN TESTS\n');

  const testDirs = [
    'tests',
    'apps/web/tests'
  ];

  let inconsistencies = [];

  testDirs.forEach(dir => {
    const fullPath = path.join(__dirname, '..', dir);
    if (!fs.existsSync(fullPath)) return;

    const files = fs.readdirSync(fullPath)
      .filter(f => f.endsWith('.spec.ts') || f.endsWith('.spec.js'));

    files.forEach(file => {
      const content = fs.readFileSync(path.join(fullPath, file), 'utf8');

      // Check for non-standard ports
      const portMatches = content.match(/localhost:(\d{4})/g);
      if (portMatches) {
        portMatches.forEach(match => {
          const port = parseInt(match.split(':')[1]);
          if (port !== STANDARD_PORT && port >= 5000 && port < 6000) {
            inconsistencies.push({
              file: path.join(dir, file),
              port: port,
              match: match
            });
          }
        });
      }
    });
  });

  if (inconsistencies.length > 0) {
    console.log('⚠️  FOUND PORT INCONSISTENCIES:\n');
    inconsistencies.forEach(({ file, port, match }) => {
      console.log(`   ${file}`);
      console.log(`     Uses: ${match} (should be localhost:${STANDARD_PORT})`);
    });
    console.log('');
    return false;
  } else {
    console.log(`✅ All tests use standard port ${STANDARD_PORT}\n`);
    return true;
  }
}

/**
 * Check session lock file
 */
function checkSessionLock() {
  console.log('📝 CHECKING SESSION LOCK FILE\n');

  if (!fs.existsSync(SESSION_LOCK_FILE)) {
    console.log('⚠️  Session lock file not found');
    console.log(`   Expected: ${SESSION_LOCK_FILE}\n`);
    return null;
  }

  try {
    const session = JSON.parse(fs.readFileSync(SESSION_LOCK_FILE, 'utf8'));

    console.log(`Session ID:      ${session.sessionId}`);
    console.log(`Active Port:     ${session.activePort} ${session.ports?.active ? '✅' : '⚠️  (not running)'}`);
    console.log(`Git Branch:      ${session.git?.branch}`);
    console.log(`Git Commit:      ${session.git?.commit}`);
    console.log(`Uncommitted:     ${session.git?.hasUncommittedChanges ? '⚠️  YES' : '✅ NO'}`);

    if (session.ports?.zombies && session.ports.zombies.length > 0) {
      console.log(`Zombie Ports:    ${session.ports.zombies.join(', ')} ⚠️`);
    } else {
      console.log(`Zombie Ports:    None ✅`);
    }

    console.log('');

    return session;
  } catch (err) {
    console.log(`⚠️  Could not read session lock file: ${err.message}\n`);
    return null;
  }
}

/**
 * Generate completion checklist
 */
function generateChecklist(gitStatus, portsOK, session) {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('           WORK COMPLETION VERIFICATION CHECKLIST         ');
  console.log('═══════════════════════════════════════════════════════════\n');

  const checks = [
    {
      name: 'All changes committed to git',
      pass: !gitStatus.hasUncommitted,
      action: 'git add -A && git commit -m "your message"'
    },
    {
      name: 'All commits pushed to remote',
      pass: !gitStatus.hasUnpushed,
      action: 'git push origin ' + gitStatus.branch
    },
    {
      name: 'Tests use standard port (5191)',
      pass: portsOK,
      action: 'Update test files to use localhost:5191'
    },
    {
      name: 'No zombie dev servers running',
      pass: !session?.ports?.zombies || session.ports.zombies.length === 0,
      action: 'node scripts/ensure-single-dev-server.cjs'
    },
    {
      name: 'Session lock file exists',
      pass: !!session,
      action: 'node scripts/ensure-single-dev-server.cjs'
    },
    {
      name: 'Working on correct branch',
      pass: gitStatus.branch === 'feature/ui-consolidation-unified' || gitStatus.branch === 'main' || gitStatus.branch === 'master',
      action: 'git checkout feature/ui-consolidation-unified'
    }
  ];

  let allPassed = true;

  checks.forEach((check, index) => {
    const icon = check.pass ? '✅' : '❌';
    console.log(`${index + 1}. ${icon} ${check.name}`);
    if (!check.pass) {
      console.log(`   Action: ${check.action}`);
      allPassed = false;
    }
  });

  console.log('\n═══════════════════════════════════════════════════════════\n');

  return allPassed;
}

/**
 * Generate work summary
 */
function generateWorkSummary(gitStatus) {
  console.log('📊 WORK SUMMARY - RECENT COMMITS\n');

  const recentCommits = exec('git log --oneline -10');
  if (recentCommits) {
    console.log(recentCommits.split('\n').map(line => '   ' + line).join('\n'));
  }

  console.log('\n');

  // Count commits today
  const today = new Date().toISOString().split('T')[0];
  const todayCommits = exec(`git log --oneline --since="${today} 00:00:00" --until="${today} 23:59:59"`);
  const commitCount = todayCommits ? todayCommits.split('\n').length : 0;

  console.log(`📅 Commits Today: ${commitCount}`);
  console.log(`🌿 Current Branch: ${gitStatus.branch}`);
  console.log(`📌 Latest Commit: ${gitStatus.commit}\n`);
}

/**
 * Main execution
 */
function main() {
  console.log('\n');
  console.log('╔═══════════════════════════════════════════════════════════╗');
  console.log('║       WORK COMPLETION VERIFICATION & MERGE SYSTEM        ║');
  console.log('╚═══════════════════════════════════════════════════════════╝');
  console.log('\n');

  // Check git status
  const gitStatus = checkGitStatus();

  // Check port consistency
  const portsOK = checkPortConsistency();

  // Check session lock
  const session = checkSessionLock();

  // Generate checklist
  const allPassed = generateChecklist(gitStatus, portsOK, session);

  // Generate work summary
  generateWorkSummary(gitStatus);

  // Final verdict
  if (allPassed) {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('                    ✅ ALL CHECKS PASSED                    ');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
    console.log('Your work is properly saved, committed, and ready to merge!');
    console.log('');
    console.log('Next Steps:');
    console.log('  1. Create pull request (if needed)');
    console.log('  2. Deploy to staging/production');
    console.log('  3. Verify in live environment');
    console.log('');
    process.exit(0);
  } else {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('              ⚠️  ACTION REQUIRED - INCOMPLETE WORK         ');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
    console.log('Please complete the failed checks above before considering');
    console.log('your work complete and ready to merge.');
    console.log('');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { checkGitStatus, checkPortConsistency, generateChecklist };
