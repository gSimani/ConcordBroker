/**
 * ConcordBroker Connection Monitor Agent
 * Continuously monitors MCP Server connections, prevents port conflicts,
 * and maintains healthy service connections across all Claude Code sessions
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const EventEmitter = require('events');

class ConnectionMonitorAgent extends EventEmitter {
  constructor() {
    super();
    this.agentId = `monitor-${Date.now()}`;
    this.isRunning = false;
    this.monitoringInterval = null;
    this.healthCheckInterval = 15000; // Check every 15 seconds
    this.recoveryAttempts = 0;
    this.maxRecoveryAttempts = 3;

    // Load environment
    this.loadEnvironment();

    // Port management
    this.primaryPort = process.env.MCP_PORT || '3005';
    this.backupPorts = ['3006', '3007', '3008', '3009'];
    this.currentPort = this.primaryPort;
    this.apiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key-claude';

    // State tracking
    this.lastHealthStatus = null;
    this.portConflicts = new Map();
    this.serviceStatus = new Map();
    this.mcpServerPid = null;

    // File paths
    this.logFile = path.join(__dirname, 'logs', 'connection-monitor.log');
    this.statusFile = path.join(__dirname, 'logs', 'monitor-status.json');
    this.lockFile = path.join(__dirname, '.monitor-lock');

    // Ensure log directory exists
    this.ensureLogDirectory();

    // Bind methods
    this.handleExit = this.handleExit.bind(this);
  }

  loadEnvironment() {
    const envMcpPath = path.join(__dirname, '.env.mcp');
    if (fs.existsSync(envMcpPath)) {
      try {
        const envContent = fs.readFileSync(envMcpPath, 'utf8');
        const envLines = envContent.split('\n');

        for (const line of envLines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              process.env[key] = valueParts.join('=');
            }
          }
        }
      } catch (error) {
        this.log(`Error loading .env.mcp: ${error.message}`, 'error');
      }
    }
  }

  ensureLogDirectory() {
    const logDir = path.dirname(this.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      agent: this.agentId,
      message
    };

    const logLine = `[${timestamp}] [${level.toUpperCase()}] [${this.agentId}] ${message}`;
    console.log(logLine);

    try {
      fs.appendFileSync(this.logFile, JSON.stringify(logEntry) + '\n');
    } catch (e) {
      // Ignore log file errors
    }

    // Emit log event for external listeners
    this.emit('log', logEntry);
  }

  async start() {
    // Check if another monitor is already running
    if (await this.isAnotherMonitorRunning()) {
      this.log('Another monitor agent is already running, exiting', 'warn');
      return false;
    }

    this.createLockFile();
    this.isRunning = true;
    this.log('Connection Monitor Agent starting...', 'info');

    // Set up exit handlers
    process.on('SIGINT', this.handleExit);
    process.on('SIGTERM', this.handleExit);
    process.on('exit', this.handleExit);

    // Initial setup
    await this.performInitialSetup();

    // Start monitoring loop
    this.startMonitoringLoop();

    this.log('Connection Monitor Agent is now active', 'info');
    return true;
  }

  async isAnotherMonitorRunning() {
    if (!fs.existsSync(this.lockFile)) {
      return false;
    }

    try {
      const lockData = JSON.parse(fs.readFileSync(this.lockFile, 'utf8'));
      const lockAge = Date.now() - lockData.timestamp;

      // If lock is older than 2 minutes, consider it stale
      if (lockAge > 120000) {
        fs.unlinkSync(this.lockFile);
        return false;
      }

      // Check if process is actually running
      if (process.platform === 'win32') {
        try {
          const { execSync } = require('child_process');
          execSync(`tasklist /PID ${lockData.pid}`, { timeout: 2000 });
          return true; // Process exists
        } catch (e) {
          fs.unlinkSync(this.lockFile);
          return false; // Process doesn't exist
        }
      }

      return true;
    } catch (error) {
      fs.unlinkSync(this.lockFile);
      return false;
    }
  }

  createLockFile() {
    const lockData = {
      pid: process.pid,
      timestamp: Date.now(),
      agentId: this.agentId
    };

    fs.writeFileSync(this.lockFile, JSON.stringify(lockData, null, 2));
  }

  async performInitialSetup() {
    this.log('Performing initial setup and conflict resolution...', 'info');

    // Scan for port conflicts
    await this.scanPortConflicts();

    // Ensure MCP Server is running
    await this.ensureMCPServerRunning();

    // Test all service connections
    await this.testAllServices();
  }

  async scanPortConflicts() {
    this.log('Scanning for port conflicts...', 'info');

    const portsToCheck = [this.primaryPort, ...this.backupPorts];

    for (const port of portsToCheck) {
      const conflicts = await this.checkPortConflicts(port);
      if (conflicts.length > 0) {
        this.portConflicts.set(port, conflicts);
        this.log(`Port ${port} has ${conflicts.length} conflicts`, 'warn');
      }
    }
  }

  async checkPortConflicts(port) {
    if (process.platform !== 'win32') {
      return []; // Only implemented for Windows for now
    }

    try {
      const { execSync } = require('child_process');
      const netstatOutput = execSync(`netstat -ano | findstr :${port}`, {
        encoding: 'utf8',
        timeout: 3000
      });

      const conflicts = [];
      const lines = netstatOutput.trim().split('\n');

      for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 5) {
          const pid = parts[4];
          const state = parts[3];

          conflicts.push({
            pid,
            state,
            line: line.trim()
          });
        }
      }

      return conflicts;
    } catch (error) {
      return []; // No conflicts found or command failed
    }
  }

  async ensureMCPServerRunning() {
    this.log('Checking MCP Server status...', 'info');

    const serverUrl = `http://localhost:${this.currentPort}`;

    try {
      const response = await axios.get(`${serverUrl}/health`, {
        timeout: 5000,
        headers: { 'x-api-key': this.apiKey }
      });

      if (response.data && response.data.status === 'healthy') {
        this.log(`MCP Server is healthy on port ${this.currentPort}`, 'info');
        this.lastHealthStatus = response.data;
        return true;
      }
    } catch (error) {
      this.log(`MCP Server not responding on port ${this.currentPort}: ${error.message}`, 'warn');
    }

    // Try to start or restart MCP Server
    return await this.startMCPServer();
  }

  async startMCPServer() {
    this.log('Starting MCP Server...', 'info');

    // Kill any conflicting processes first
    await this.resolvePortConflicts();

    try {
      const serverPath = path.join(__dirname, 'mcp-server');

      const serverProcess = spawn('npm', ['start'], {
        cwd: serverPath,
        env: {
          ...process.env,
          MCP_PORT: this.currentPort,
          DISABLE_LANGCHAIN: 'true',
          NODE_ENV: 'development'
        },
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      this.mcpServerPid = serverProcess.pid;

      // Log output
      serverProcess.stdout.on('data', (data) => {
        this.log(`[MCP Server] ${data.toString().trim()}`, 'debug');
      });

      serverProcess.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (!output.includes('DeprecationWarning')) {
          this.log(`[MCP Server Error] ${output}`, 'warn');
        }
      });

      // Wait for server to be ready
      await this.waitForServerReady(30000); // 30 second timeout

      this.log(`MCP Server started successfully on port ${this.currentPort}`, 'info');
      return true;

    } catch (error) {
      this.log(`Failed to start MCP Server: ${error.message}`, 'error');

      // Try backup port
      if (this.backupPorts.length > 0) {
        this.currentPort = this.backupPorts.shift();
        this.log(`Trying backup port ${this.currentPort}...`, 'info');
        return await this.startMCPServer();
      }

      return false;
    }
  }

  async waitForServerReady(timeout = 30000) {
    const startTime = Date.now();
    const serverUrl = `http://localhost:${this.currentPort}`;

    while (Date.now() - startTime < timeout) {
      try {
        const response = await axios.get(`${serverUrl}/health`, {
          timeout: 3000,
          headers: { 'x-api-key': this.apiKey }
        });

        if (response.data && response.data.status === 'healthy') {
          return true;
        }
      } catch (error) {
        // Continue waiting
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Server failed to become ready within timeout');
  }

  async resolvePortConflicts() {
    const conflicts = this.portConflicts.get(this.currentPort);
    if (!conflicts || conflicts.length === 0) {
      return;
    }

    this.log(`Resolving ${conflicts.length} port conflicts on ${this.currentPort}...`, 'info');

    for (const conflict of conflicts) {
      try {
        if (process.platform === 'win32') {
          const { execSync } = require('child_process');
          execSync(`taskkill /PID ${conflict.pid} /F`, { timeout: 3000 });
          this.log(`Killed conflicting process ${conflict.pid}`, 'info');
        }
      } catch (error) {
        this.log(`Failed to kill process ${conflict.pid}: ${error.message}`, 'warn');
      }
    }

    // Wait for processes to terminate
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Clear conflicts
    this.portConflicts.delete(this.currentPort);
  }

  async testAllServices() {
    this.log('Testing all service connections...', 'info');

    const services = [
      { name: 'Supabase', endpoint: '/api/supabase/User?limit=1', critical: true },
      { name: 'Vercel', endpoint: '/api/vercel/project', critical: true },
      { name: 'Railway', endpoint: '/api/railway/status', critical: false },
      { name: 'GitHub', endpoint: '/api/github/commits?limit=1', critical: false }
    ];

    for (const service of services) {
      const status = await this.testServiceConnection(service);
      this.serviceStatus.set(service.name, status);
    }

    const healthyServices = Array.from(this.serviceStatus.values()).filter(s => s.healthy).length;
    this.log(`Service status: ${healthyServices}/${services.length} healthy`, 'info');
  }

  async testServiceConnection(service) {
    const serverUrl = `http://localhost:${this.currentPort}`;

    try {
      const response = await axios.get(`${serverUrl}${service.endpoint}`, {
        headers: { 'x-api-key': this.apiKey },
        timeout: 8000
      });

      return {
        healthy: true,
        lastCheck: new Date().toISOString(),
        responseTime: Date.now(),
        error: null
      };

    } catch (error) {
      const status = {
        healthy: false,
        lastCheck: new Date().toISOString(),
        error: error.message.substring(0, 100)
      };

      if (service.critical) {
        this.log(`Critical service ${service.name} failed: ${error.message}`, 'error');
      } else {
        this.log(`Service ${service.name} failed: ${error.message}`, 'warn');
      }

      return status;
    }
  }

  startMonitoringLoop() {
    this.log('Starting continuous monitoring loop...', 'info');

    this.monitoringInterval = setInterval(async () => {
      try {
        await this.performMonitoringCycle();
      } catch (error) {
        this.log(`Monitoring cycle error: ${error.message}`, 'error');
      }
    }, this.healthCheckInterval);
  }

  async performMonitoringCycle() {
    // Check MCP Server health
    const serverHealthy = await this.checkMCPServerHealth();

    if (!serverHealthy) {
      this.log('MCP Server unhealthy, attempting recovery...', 'warn');
      await this.attemptRecovery();
    }

    // Check for new port conflicts
    await this.scanPortConflicts();

    // Test critical services
    await this.testCriticalServices();

    // Update status file
    this.updateStatusFile();
  }

  async checkMCPServerHealth() {
    const serverUrl = `http://localhost:${this.currentPort}`;

    try {
      const response = await axios.get(`${serverUrl}/health`, {
        timeout: 5000,
        headers: { 'x-api-key': this.apiKey }
      });

      if (response.data && response.data.status === 'healthy') {
        this.lastHealthStatus = response.data;
        this.recoveryAttempts = 0; // Reset recovery counter
        return true;
      }
    } catch (error) {
      this.log(`Health check failed: ${error.message}`, 'warn');
    }

    return false;
  }

  async testCriticalServices() {
    const criticalServices = ['Supabase', 'Vercel'];

    for (const serviceName of criticalServices) {
      const service = { name: serviceName, endpoint: this.getServiceEndpoint(serviceName), critical: true };
      const status = await this.testServiceConnection(service);
      this.serviceStatus.set(serviceName, status);

      if (!status.healthy) {
        this.log(`Critical service ${serviceName} is down`, 'error');
      }
    }
  }

  getServiceEndpoint(serviceName) {
    const endpoints = {
      'Supabase': '/api/supabase/User?limit=1',
      'Vercel': '/api/vercel/project',
      'Railway': '/api/railway/status',
      'GitHub': '/api/github/commits?limit=1'
    };

    return endpoints[serviceName] || '/health';
  }

  async attemptRecovery() {
    if (this.recoveryAttempts >= this.maxRecoveryAttempts) {
      this.log('Max recovery attempts reached, manual intervention required', 'error');
      this.emit('critical', 'Max recovery attempts reached');
      return false;
    }

    this.recoveryAttempts++;
    this.log(`Recovery attempt ${this.recoveryAttempts}/${this.maxRecoveryAttempts}...`, 'info');

    // Try to restart MCP Server
    const success = await this.startMCPServer();

    if (success) {
      this.log('Recovery successful', 'info');
      this.emit('recovery', 'MCP Server recovered');
    } else {
      this.log('Recovery failed', 'error');
    }

    return success;
  }

  updateStatusFile() {
    const status = {
      agentId: this.agentId,
      timestamp: new Date().toISOString(),
      isRunning: this.isRunning,
      currentPort: this.currentPort,
      mcpServerPid: this.mcpServerPid,
      lastHealthStatus: this.lastHealthStatus,
      serviceStatus: Object.fromEntries(this.serviceStatus),
      portConflicts: Object.fromEntries(this.portConflicts),
      recoveryAttempts: this.recoveryAttempts
    };

    try {
      fs.writeFileSync(this.statusFile, JSON.stringify(status, null, 2));
    } catch (error) {
      this.log(`Failed to update status file: ${error.message}`, 'warn');
    }
  }

  async stop() {
    this.log('Stopping Connection Monitor Agent...', 'info');

    this.isRunning = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.cleanup();
    this.log('Connection Monitor Agent stopped', 'info');
  }

  handleExit() {
    if (this.isRunning) {
      this.stop();
    }
  }

  cleanup() {
    // Remove lock file
    try {
      if (fs.existsSync(this.lockFile)) {
        fs.unlinkSync(this.lockFile);
      }
    } catch (error) {
      // Ignore cleanup errors
    }

    // Remove event listeners
    process.removeListener('SIGINT', this.handleExit);
    process.removeListener('SIGTERM', this.handleExit);
    process.removeListener('exit', this.handleExit);
  }

  // Public API for external monitoring
  getStatus() {
    return {
      isRunning: this.isRunning,
      currentPort: this.currentPort,
      lastHealthStatus: this.lastHealthStatus,
      serviceStatus: Object.fromEntries(this.serviceStatus),
      recoveryAttempts: this.recoveryAttempts
    };
  }
}

// Auto-start when executed directly
if (require.main === module) {
  const agent = new ConnectionMonitorAgent();

  agent.on('log', (logEntry) => {
    // External log handlers can listen to this event
  });

  agent.on('critical', (message) => {
    console.error(`CRITICAL: ${message}`);
  });

  agent.on('recovery', (message) => {
    console.log(`RECOVERY: ${message}`);
  });

  agent.start().catch(error => {
    console.error('Failed to start Connection Monitor Agent:', error);
    process.exit(1);
  });
}

module.exports = ConnectionMonitorAgent;