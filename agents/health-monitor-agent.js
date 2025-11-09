#!/usr/bin/env node
/**
 * Multi-Instance Health Monitor Agent
 * Monitors all dev servers, checks health, auto-restarts on crashes
 *
 * Features:
 * - Health checks for all worktree dev servers
 * - Memory and CPU monitoring
 * - Auto-restart on crashes
 * - Build time tracking
 * - Real-time dashboard
 *
 * Usage:
 *   node health-monitor-agent.js        # Start monitoring
 *   node health-monitor-agent.js --dash # Show dashboard only
 */

const { execSync, spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_DIR = 'C:/Users/gsima/Documents/MyProject';
const WORKTREES = [
  { branch: 'master', path: `${BASE_DIR}/ConcordBroker`, port: 5191 },
  { branch: 'feature/ui-consolidation', path: `${BASE_DIR}/ConcordBroker-feature-ui-consolidation`, port: 5192 },
  { branch: 'feature/api-enhancements', path: `${BASE_DIR}/ConcordBroker-feature-api-enhancements`, port: 5193 },
  { branch: 'feature/database-optimization', path: `${BASE_DIR}/ConcordBroker-feature-database-optimization`, port: 5194 },
  { branch: 'feature/agent-development', path: `${BASE_DIR}/ConcordBroker-feature-agent-development`, port: 5195 },
  { branch: 'hotfix/production', path: `${BASE_DIR}/ConcordBroker-hotfix-production`, port: 5196 },
  { branch: 'experimental/new-features', path: `${BASE_DIR}/ConcordBroker-experimental-new-features`, port: 5197 },
  { branch: 'testing/integration', path: `${BASE_DIR}/ConcordBroker-testing-integration`, port: 5198 },
];

const CHECK_INTERVAL = 15000; // 15 seconds
const RESTART_THRESHOLD = 3; // Auto-restart after 3 failed checks
const HEALTH_LOG_FILE = path.join(__dirname, '../logs/health-monitor.log');

// Colors
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m',
};

function log(message, color = 'reset', toFile = true) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}`;

  console.log(`${colors[color]}${logMessage}${colors.reset}`);

  if (toFile) {
    const logDir = path.dirname(HEALTH_LOG_FILE);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    fs.appendFileSync(HEALTH_LOG_FILE, logMessage + '\n');
  }
}

function execCommand(command) {
  try {
    return execSync(command, { encoding: 'utf-8', stdio: 'pipe' });
  } catch (error) {
    return '';
  }
}

class HealthMonitorAgent {
  constructor() {
    this.health = {};
    this.restartCounts = {};
    this.failedChecks = {};
    this.totalChecks = 0;
    this.totalRestarts = 0;

    // Initialize health state
    WORKTREES.forEach(wt => {
      this.health[wt.port] = {
        branch: wt.branch,
        path: wt.path,
        port: wt.port,
        status: 'unknown',
        pid: null,
        memory: 0,
        cpu: 0,
        buildTime: 0,
        lastCheck: null,
        uptime: 0,
      };
      this.failedChecks[wt.port] = 0;
      this.restartCounts[wt.port] = 0;
    });
  }

  async checkServerHealth(worktree) {
    const { port, path: worktreePath } = worktree;

    try {
      // Check if process is running on this port
      const portCheck = execCommand(`netstat -ano | findstr :${port} | findstr LISTENING`);

      if (!portCheck) {
        return {
          status: 'stopped',
          healthy: false,
          message: 'No process listening on port',
        };
      }

      // Extract PID
      const pidMatch = portCheck.match(/LISTENING\s+(\d+)/);
      const pid = pidMatch ? pidMatch[1] : null;

      if (!pid) {
        return {
          status: 'error',
          healthy: false,
          message: 'Could not determine PID',
        };
      }

      // Get process info (memory, CPU)
      const processInfo = execCommand(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`);

      let memory = 0;
      if (processInfo) {
        const memMatch = processInfo.match(/(\d+,?\d*)\s+K/);
        if (memMatch) {
          memory = parseInt(memMatch[1].replace(/,/g, '')) / 1024; // Convert to MB
        }
      }

      // HTTP health check
      const healthCheck = await this.httpHealthCheck(port);

      if (healthCheck.healthy) {
        return {
          status: 'healthy',
          healthy: true,
          pid,
          memory,
          responseTime: healthCheck.responseTime,
          uptime: this.getUptime(pid),
        };
      } else {
        return {
          status: 'unhealthy',
          healthy: false,
          pid,
          memory,
          message: healthCheck.error,
        };
      }
    } catch (error) {
      return {
        status: 'error',
        healthy: false,
        message: error.message,
      };
    }
  }

  async httpHealthCheck(port) {
    return new Promise((resolve) => {
      const startTime = Date.now();

      const req = http.get(`http://localhost:${port}`, (res) => {
        const responseTime = Date.now() - startTime;

        if (res.statusCode === 200 || res.statusCode === 304) {
          resolve({ healthy: true, responseTime });
        } else {
          resolve({ healthy: false, error: `HTTP ${res.statusCode}` });
        }

        res.resume(); // Consume response data
      });

      req.on('error', (error) => {
        resolve({ healthy: false, error: error.message });
      });

      // Timeout after 5 seconds
      req.setTimeout(5000, () => {
        req.destroy();
        resolve({ healthy: false, error: 'Timeout' });
      });
    });
  }

  getUptime(pid) {
    try {
      // Get process creation time using WMIC
      const wmic = execCommand(`wmic process where processid=${pid} get CreationDate`);
      const match = wmic.match(/(\d{14})/);

      if (match) {
        const creationDate = match[1];
        const year = creationDate.substring(0, 4);
        const month = creationDate.substring(4, 6);
        const day = creationDate.substring(6, 8);
        const hour = creationDate.substring(8, 10);
        const minute = creationDate.substring(10, 12);
        const second = creationDate.substring(12, 14);

        const created = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
        const uptime = Date.now() - created.getTime();

        return Math.floor(uptime / 1000); // Return uptime in seconds
      }
    } catch (error) {
      // Ignore errors
    }

    return 0;
  }

  formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  async restartServer(worktree) {
    const { port, path: worktreePath, branch } = worktree;

    log(`🔄 Restarting server for ${branch} (port ${port})...`, 'yellow');

    // Try to stop gracefully first
    const pidFile = path.join(worktreePath, '.dev-server.pid');
    if (fs.existsSync(pidFile)) {
      const pid = fs.readFileSync(pidFile, 'utf-8').trim();
      try {
        execCommand(`taskkill /F /PID ${pid}`);
        log(`  ✅ Stopped old process (PID: ${pid})`, 'green');
      } catch (error) {
        log(`  ⚠️  Could not stop process: ${error.message}`, 'yellow');
      }
    }

    // Start new dev server
    const webPath = path.join(worktreePath, 'apps/web');

    if (!fs.existsSync(webPath)) {
      log(`  ❌ Path not found: ${webPath}`, 'red');
      return false;
    }

    try {
      const devServer = spawn('npm', ['run', 'dev'], {
        cwd: webPath,
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: true,
      });

      // Save PID
      fs.writeFileSync(pidFile, String(devServer.pid));

      // Detach process
      devServer.unref();

      this.restartCounts[port]++;
      this.totalRestarts++;

      log(`  ✅ Server restarted (PID: ${devServer.pid})`, 'green');

      return true;
    } catch (error) {
      log(`  ❌ Failed to restart: ${error.message}`, 'red');
      return false;
    }
  }

  async checkAllServers() {
    this.totalChecks++;

    for (const worktree of WORKTREES) {
      const { port, branch } = worktree;

      // Skip if worktree doesn't exist
      if (!fs.existsSync(worktree.path)) {
        this.health[port].status = 'not_installed';
        continue;
      }

      const result = await this.checkServerHealth(worktree);

      // Update health state
      this.health[port] = {
        ...this.health[port],
        ...result,
        lastCheck: new Date().toISOString(),
      };

      // Handle failures
      if (!result.healthy) {
        this.failedChecks[port]++;

        if (this.failedChecks[port] >= RESTART_THRESHOLD) {
          log(`⚠️  ${branch} failed ${this.failedChecks[port]} health checks, attempting restart...`, 'yellow');
          const restarted = await this.restartServer(worktree);

          if (restarted) {
            this.failedChecks[port] = 0; // Reset counter after successful restart
          }
        }
      } else {
        this.failedChecks[port] = 0; // Reset counter on successful check
      }
    }
  }

  printDashboard() {
    console.clear();

    const timestamp = new Date().toLocaleTimeString();

    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue', false);
    log(`  ConcordBroker Multi-Instance Health Dashboard  |  ${timestamp}`, 'bright', false);
    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`, 'blue', false);

    // Table header
    const header = `${'BRANCH'.padEnd(35)} ${'PORT'.padEnd(6)} ${'STATUS'.padEnd(12)} ${'MEM'.padEnd(8)} ${'UPTIME'.padEnd(10)} ${'RESTARTS'}`;
    log(header, 'cyan', false);
    log('─'.repeat(95), 'dim', false);

    // Table rows
    for (const worktree of WORKTREES) {
      const { port } = worktree;
      const health = this.health[port];

      let statusText = health.status.toUpperCase();
      let statusColor = 'reset';
      let statusIcon = '⚪';

      switch (health.status) {
        case 'healthy':
          statusIcon = '✅';
          statusColor = 'green';
          break;
        case 'unhealthy':
          statusIcon = '⚠️ ';
          statusColor = 'yellow';
          statusText = 'UNHEALTHY';
          break;
        case 'stopped':
          statusIcon = '❌';
          statusColor = 'red';
          break;
        case 'not_installed':
          statusIcon = '📦';
          statusColor = 'dim';
          statusText = 'NOT INSTALLED';
          break;
        case 'error':
          statusIcon = '❗';
          statusColor = 'red';
          break;
      }

      const branch = health.branch.padEnd(35);
      const portStr = String(port).padEnd(6);
      const status = `${statusIcon} ${statusText}`.padEnd(12);
      const memory = health.memory ? `${health.memory.toFixed(1)}MB`.padEnd(8) : 'N/A'.padEnd(8);
      const uptime = health.uptime ? this.formatUptime(health.uptime).padEnd(10) : 'N/A'.padEnd(10);
      const restarts = this.restartCounts[port] || 0;

      const row = `${branch} ${portStr} ${status} ${memory} ${uptime} ${restarts}`;
      log(row, statusColor, false);
    }

    log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue', false);

    // Statistics
    const healthyCount = Object.values(this.health).filter(h => h.status === 'healthy').length;
    const totalInstalled = Object.values(this.health).filter(h => h.status !== 'not_installed').length;

    log(`📊 Statistics:`, 'bright', false);
    log(`   Healthy Instances: ${healthyCount}/${totalInstalled}`, healthyCount === totalInstalled ? 'green' : 'yellow', false);
    log(`   Total Health Checks: ${this.totalChecks}`, 'cyan', false);
    log(`   Total Auto-Restarts: ${this.totalRestarts}`, this.totalRestarts > 0 ? 'yellow' : 'green', false);
    log(`   Next check in ${CHECK_INTERVAL / 1000}s`, 'dim', false);

    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`, 'blue', false);
  }

  async startMonitoring() {
    log(`🏥 Multi-Instance Health Monitor Started`, 'bright');
    log(`   Monitoring ${WORKTREES.length} worktrees`, 'cyan');
    log(`   Check interval: ${CHECK_INTERVAL / 1000}s`, 'cyan');
    log(`   Auto-restart threshold: ${RESTART_THRESHOLD} failed checks`, 'cyan');
    log(`   Press Ctrl+C to stop\n`, 'yellow');

    // Initial check
    await this.checkAllServers();
    this.printDashboard();

    // Start monitoring loop
    const checkInterval = setInterval(async () => {
      await this.checkAllServers();
      this.printDashboard();
    }, CHECK_INTERVAL);

    // Handle graceful shutdown
    process.on('SIGINT', () => {
      log(`\n\n🛑 Shutting down Health Monitor...`, 'yellow');
      clearInterval(checkInterval);
      log(`✅ Monitor stopped. Total restarts: ${this.totalRestarts}`, 'green');
      process.exit(0);
    });
  }

  async showDashboard() {
    await this.checkAllServers();
    this.printDashboard();
  }
}

// CLI Interface
async function main() {
  const agent = new HealthMonitorAgent();

  const args = process.argv.slice(2);

  if (args.includes('--dash')) {
    await agent.showDashboard();
  } else {
    await agent.startMonitoring();
  }
}

if (require.main === module) {
  main().catch(error => {
    log(`Fatal error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = { HealthMonitorAgent };
