#!/usr/bin/env node
/**
 * Port Conflict Resolution Agent
 * Monitors ports 5191-5198 and auto-resolves conflicts
 *
 * Features:
 * - Detects zombie processes on worktree ports
 * - Auto-kills processes on wrong ports
 * - Maintains port registry
 * - Prevents port conflicts before they happen
 * - Real-time monitoring every 10 seconds
 *
 * Usage:
 *   node port-conflict-agent.js        # Start monitoring
 *   node port-conflict-agent.js --once # Check once and exit
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const MONITORED_PORTS = [5191, 5192, 5193, 5194, 5195, 5196, 5197, 5198];
const CHECK_INTERVAL = 10000; // 10 seconds
const PORT_REGISTRY_FILE = path.join(__dirname, '../.port-registry.json');

const PORT_ASSIGNMENTS = {
  5191: 'master',
  5192: 'feature/ui-consolidation',
  5193: 'feature/api-enhancements',
  5194: 'feature/database-optimization',
  5195: 'feature/agent-development',
  5196: 'hotfix/production',
  5197: 'experimental/new-features',
  5198: 'testing/integration',
};

// Colors
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

function execCommand(command) {
  try {
    return execSync(command, { encoding: 'utf-8', stdio: 'pipe' });
  } catch (error) {
    return '';
  }
}

class PortConflictAgent {
  constructor() {
    this.portRegistry = this.loadRegistry();
    this.conflictsResolved = 0;
    this.isRunning = false;
  }

  loadRegistry() {
    if (fs.existsSync(PORT_REGISTRY_FILE)) {
      try {
        return JSON.parse(fs.readFileSync(PORT_REGISTRY_FILE, 'utf-8'));
      } catch (error) {
        log(`Warning: Could not load port registry: ${error.message}`, 'yellow');
      }
    }
    return {};
  }

  saveRegistry() {
    try {
      fs.writeFileSync(PORT_REGISTRY_FILE, JSON.stringify(this.portRegistry, null, 2));
    } catch (error) {
      log(`Warning: Could not save port registry: ${error.message}`, 'yellow');
    }
  }

  getPortProcesses(port) {
    const output = execCommand(`netstat -ano | findstr :${port}`);

    if (!output) return [];

    const processes = [];
    const lines = output.split('\n').filter(line => line.trim());

    for (const line of lines) {
      const match = line.match(/LISTENING\s+(\d+)/);
      if (match) {
        const pid = match[1];
        const processInfo = execCommand(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`);

        if (processInfo) {
          const [processName] = processInfo.split(',').map(s => s.replace(/"/g, '').trim());
          processes.push({ pid, processName, port });
        }
      }
    }

    return processes;
  }

  killProcess(pid, processName) {
    try {
      execCommand(`taskkill /F /PID ${pid}`);
      log(`  ✅ Killed process: ${processName} (PID: ${pid})`, 'green');
      return true;
    } catch (error) {
      log(`  ❌ Failed to kill process ${pid}: ${error.message}`, 'red');
      return false;
    }
  }

  async checkPort(port) {
    const processes = this.getPortProcesses(port);
    const expectedBranch = PORT_ASSIGNMENTS[port];

    if (processes.length === 0) {
      // Port is free
      if (this.portRegistry[port]) {
        delete this.portRegistry[port];
        this.saveRegistry();
      }
      return { status: 'free', port, expectedBranch };
    }

    if (processes.length === 1) {
      const [process] = processes;

      // Check if this is a legitimate Node/Vite process
      const isNodeProcess = process.processName.toLowerCase().includes('node');

      if (isNodeProcess) {
        // Check if this port is registered
        if (!this.portRegistry[port]) {
          // Register this port
          this.portRegistry[port] = {
            pid: process.pid,
            processName: process.processName,
            branch: expectedBranch,
            startedAt: new Date().toISOString(),
          };
          this.saveRegistry();
          return { status: 'active', port, process, expectedBranch };
        }

        // Port is registered and active
        return { status: 'active', port, process, expectedBranch };
      } else {
        // Non-Node process on our port - this is a conflict!
        return { status: 'conflict', port, process, expectedBranch, reason: 'non-node-process' };
      }
    }

    // Multiple processes on same port - definite conflict
    return { status: 'conflict', port, processes, expectedBranch, reason: 'multiple-processes' };
  }

  async resolveConflict(result) {
    const { port, process, processes, reason } = result;

    log(`\n⚠️  PORT CONFLICT DETECTED on port ${port}`, 'red');
    log(`   Expected: ${PORT_ASSIGNMENTS[port]}`, 'yellow');
    log(`   Reason: ${reason}`, 'yellow');

    if (reason === 'non-node-process') {
      log(`   Rogue process: ${process.processName} (PID: ${process.pid})`, 'red');
      log(`   🔧 Auto-resolving conflict...`, 'cyan');

      if (this.killProcess(process.pid, process.processName)) {
        this.conflictsResolved++;
        delete this.portRegistry[port];
        this.saveRegistry();
        log(`   ✅ Conflict resolved! Port ${port} is now free`, 'green');
        return true;
      }
    }

    if (reason === 'multiple-processes') {
      log(`   Multiple processes detected:`, 'red');
      processes.forEach(p => {
        log(`     - ${p.processName} (PID: ${p.pid})`, 'yellow');
      });

      log(`   🔧 Auto-resolving conflict...`, 'cyan');

      let resolved = true;
      for (const p of processes) {
        if (!this.killProcess(p.pid, p.processName)) {
          resolved = false;
        }
      }

      if (resolved) {
        this.conflictsResolved++;
        delete this.portRegistry[port];
        this.saveRegistry();
        log(`   ✅ All conflicts resolved! Port ${port} is now free`, 'green');
        return true;
      }
    }

    return false;
  }

  async checkAllPorts() {
    const results = await Promise.all(
      MONITORED_PORTS.map(port => this.checkPort(port))
    );

    const conflicts = results.filter(r => r.status === 'conflict');
    const active = results.filter(r => r.status === 'active');
    const free = results.filter(r => r.status === 'free');

    // Resolve conflicts
    if (conflicts.length > 0) {
      for (const conflict of conflicts) {
        await this.resolveConflict(conflict);
      }
    }

    return { conflicts, active, free, total: results.length };
  }

  async printStatus() {
    const { conflicts, active, free } = await this.checkAllPorts();

    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue');
    log(`Port Status Report`, 'bright');
    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, 'blue');

    if (active.length > 0) {
      log(`\n✅ Active Ports (${active.length}):`, 'green');
      active.forEach(({ port, process, expectedBranch }) => {
        log(`   ${port} → ${expectedBranch} (${process.processName}, PID: ${process.pid})`, 'green');
      });
    }

    if (free.length > 0) {
      log(`\n⚪ Free Ports (${free.length}):`, 'cyan');
      free.forEach(({ port, expectedBranch }) => {
        log(`   ${port} → ${expectedBranch} (available)`, 'cyan');
      });
    }

    if (conflicts.length > 0) {
      log(`\n❌ Conflicts (${conflicts.length}):`, 'red');
      conflicts.forEach(({ port, expectedBranch, reason }) => {
        log(`   ${port} → ${expectedBranch} (${reason})`, 'red');
      });
    }

    log(`\n📊 Statistics:`, 'bright');
    log(`   Conflicts Resolved: ${this.conflictsResolved}`, 'yellow');
    log(`   Active Worktrees: ${active.length}/${MONITORED_PORTS.length}`, 'green');

    log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`, 'blue');
  }

  async startMonitoring() {
    this.isRunning = true;

    log(`🔍 Port Conflict Resolution Agent Started`, 'bright');
    log(`   Monitoring ports: ${MONITORED_PORTS.join(', ')}`, 'cyan');
    log(`   Check interval: ${CHECK_INTERVAL / 1000}s`, 'cyan');
    log(`   Press Ctrl+C to stop\n`, 'yellow');

    // Initial check
    await this.printStatus();

    // Start monitoring loop
    const checkInterval = setInterval(async () => {
      const { conflicts } = await this.checkAllPorts();

      if (conflicts.length > 0) {
        await this.printStatus();
      }
    }, CHECK_INTERVAL);

    // Handle graceful shutdown
    process.on('SIGINT', () => {
      log(`\n\n🛑 Shutting down Port Conflict Agent...`, 'yellow');
      clearInterval(checkInterval);
      this.saveRegistry();
      log(`✅ Agent stopped. Conflicts resolved: ${this.conflictsResolved}`, 'green');
      process.exit(0);
    });
  }

  async runOnce() {
    log(`🔍 Running single port check...`, 'bright');
    await this.printStatus();
  }
}

// CLI Interface
async function main() {
  const agent = new PortConflictAgent();

  const args = process.argv.slice(2);

  if (args.includes('--once')) {
    await agent.runOnce();
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

module.exports = { PortConflictAgent };
