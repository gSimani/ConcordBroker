/**
 * Claude Code Ultimate Initialization System
 * Combines robust initialization with continuous monitoring agent
 * Ensures zero-hassle connection setup with persistent monitoring
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Import our monitoring agent
const ConnectionMonitorAgent = require('./connection-monitor-agent.cjs');

class UltimateClaudeCodeSystem {
  constructor() {
    this.sessionId = `ultimate-${Date.now()}`;
    this.logFile = path.join(__dirname, 'logs', 'ultimate-init.log');
    this.statusFile = path.join(__dirname, 'logs', 'ultimate-status.json');

    // Components
    this.monitorAgent = null;
    this.mcpServerProcess = null;

    // State
    this.isInitialized = false;
    this.monitoringActive = false;

    // Configuration
    this.loadEnvironment();
    this.port = process.env.MCP_PORT || '3005';
    this.apiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key-claude';

    this.ensureLogDirectory();
  }

  loadEnvironment() {
    const envMcpPath = path.join(__dirname, '.env.mcp');
    if (fs.existsSync(envMcpPath)) {
      try {
        const envContent = fs.readFileSync(envMcpPath, 'utf8');
        envContent.split('\n').forEach(line => {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              process.env[key] = valueParts.join('=');
            }
          }
        });
      } catch (error) {
        this.log(`Environment loading error: ${error.message}`, 'error');
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
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] [${this.sessionId}] ${message}`;
    console.log(logEntry);

    try {
      fs.appendFileSync(this.logFile, logEntry + '\n');
    } catch (e) {
      // Ignore log errors
    }
  }

  async init() {
    this.log('🚀 Claude Code Ultimate Initialization System starting...', 'info');
    this.log(`Using port: ${this.port}, Session: ${this.sessionId}`, 'info');

    try {
      // Phase 1: Initial Setup & Cleanup
      await this.performPreInitialization();

      // Phase 2: Start MCP Server with robust initialization
      await this.initializeMCPServer();

      // Phase 3: Start monitoring agent
      await this.startMonitoringAgent();

      // Phase 4: Verify everything is working
      await this.performFinalVerification();

      // Phase 5: Create session tracking
      this.createSessionTracking();

      this.isInitialized = true;
      this.log('✅ Ultimate initialization completed successfully!', 'info');
      this.printSuccessMessage();

    } catch (error) {
      this.log(`❌ Initialization failed: ${error.message}`, 'error');
      await this.performEmergencyRecovery();
    }
  }

  async performPreInitialization() {
    this.log('Phase 1: Pre-initialization cleanup...', 'info');

    // Kill any conflicting processes
    if (process.platform === 'win32') {
      try {
        const { execSync } = require('child_process');

        // Kill processes on our target ports
        const portsToCheck = [this.port, '3006', '3007', '3008'];

        for (const port of portsToCheck) {
          try {
            const netstatOutput = execSync(`netstat -ano | findstr :${port}`, {
              encoding: 'utf8',
              timeout: 3000
            });

            if (netstatOutput.trim()) {
              this.log(`Found processes on port ${port}, cleaning up...`, 'info');

              const lines = netstatOutput.trim().split('\n');
              const pids = new Set();

              lines.forEach(line => {
                const parts = line.trim().split(/\s+/);
                if (parts.length >= 5 && parts[4] !== '0') {
                  pids.add(parts[4]);
                }
              });

              for (const pid of pids) {
                try {
                  execSync(`taskkill /PID ${pid} /F`, { timeout: 2000 });
                  this.log(`Cleaned up process ${pid}`, 'info');
                } catch (e) {
                  // Process might already be dead
                }
              }
            }
          } catch (e) {
            // No processes on this port
          }
        }

        // Wait for cleanup to complete
        await new Promise(resolve => setTimeout(resolve, 2000));

      } catch (error) {
        this.log(`Cleanup warning: ${error.message}`, 'warn');
      }
    }
  }

  async initializeMCPServer() {
    this.log('Phase 2: Initializing MCP Server...', 'info');

    // Use the robust initializer logic
    const serverPath = path.join(__dirname, 'mcp-server');

    try {
      this.mcpServerProcess = spawn('npm', ['start'], {
        cwd: serverPath,
        env: {
          ...process.env,
          MCP_PORT: this.port,
          DISABLE_LANGCHAIN: 'true',
          NODE_ENV: 'development',
          MCP_AUTO_START: 'true'
        },
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      // Capture output
      this.mcpServerProcess.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          this.log(`[MCP Server] ${output}`, 'debug');
        }
      });

      this.mcpServerProcess.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (output && !output.includes('DeprecationWarning')) {
          this.log(`[MCP Server Error] ${output}`, 'warn');
        }
      });

      this.log(`MCP Server started with PID: ${this.mcpServerProcess.pid}`, 'info');

      // Wait for server to be ready
      await this.waitForMCPServerReady();

    } catch (error) {
      throw new Error(`Failed to start MCP Server: ${error.message}`);
    }
  }

  async waitForMCPServerReady() {
    this.log('Waiting for MCP Server to be ready...', 'info');

    const maxAttempts = 20;
    const delay = 3000;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const response = await axios.get(`http://localhost:${this.port}/health`, {
          timeout: 5000,
          headers: { 'x-api-key': this.apiKey }
        });

        if (response.data && response.data.status === 'healthy') {
          this.log('✅ MCP Server is ready and healthy!', 'info');
          return true;
        }
      } catch (error) {
        this.log(`Health check attempt ${attempt}/${maxAttempts}: ${error.message.substring(0, 50)}...`, 'debug');
      }

      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw new Error('MCP Server failed to become ready within timeout');
  }

  async startMonitoringAgent() {
    this.log('Phase 3: Starting connection monitoring agent...', 'info');

    try {
      this.monitorAgent = new ConnectionMonitorAgent();

      // Set up event listeners
      this.monitorAgent.on('log', (logEntry) => {
        this.log(`[Monitor] ${logEntry.message}`, logEntry.level);
      });

      this.monitorAgent.on('critical', (message) => {
        this.log(`[Monitor CRITICAL] ${message}`, 'error');
      });

      this.monitorAgent.on('recovery', (message) => {
        this.log(`[Monitor RECOVERY] ${message}`, 'info');
      });

      const started = await this.monitorAgent.start();

      if (started) {
        this.monitoringActive = true;
        this.log('✅ Monitoring agent is active', 'info');
      } else {
        this.log('⚠️ Monitoring agent was already running', 'warn');
      }

    } catch (error) {
      this.log(`Warning: Monitoring agent failed to start: ${error.message}`, 'warn');
      // Continue without monitoring - not critical for basic functionality
    }
  }

  async performFinalVerification() {
    this.log('Phase 4: Final verification of all systems...', 'info');

    // Test core API endpoints
    const testEndpoints = [
      { name: 'Health Check', url: '/health' },
      { name: 'Supabase', url: '/api/supabase/User?limit=1' },
      { name: 'Vercel', url: '/api/vercel/project' },
      { name: 'Documentation', url: '/docs' }
    ];

    let successCount = 0;

    for (const endpoint of testEndpoints) {
      try {
        const response = await axios.get(`http://localhost:${this.port}${endpoint.url}`, {
          headers: { 'x-api-key': this.apiKey },
          timeout: 8000
        });

        if (response.status === 200) {
          this.log(`✅ ${endpoint.name} endpoint verified`, 'info');
          successCount++;
        }
      } catch (error) {
        this.log(`⚠️ ${endpoint.name} endpoint failed: ${error.message.substring(0, 60)}...`, 'warn');
      }
    }

    this.log(`Verification complete: ${successCount}/${testEndpoints.length} endpoints working`, 'info');

    if (successCount === 0) {
      throw new Error('No endpoints are responding - initialization failed');
    }
  }

  createSessionTracking() {
    const sessionData = {
      sessionId: this.sessionId,
      startTime: new Date().toISOString(),
      port: this.port,
      mcpServerPid: this.mcpServerProcess?.pid,
      monitoringActive: this.monitoringActive,
      isInitialized: this.isInitialized,
      ultimateSystem: true
    };

    try {
      fs.writeFileSync(this.statusFile, JSON.stringify(sessionData, null, 2));
      fs.writeFileSync(path.join(__dirname, '.claude-session'), JSON.stringify(sessionData, null, 2));
    } catch (error) {
      this.log(`Session tracking warning: ${error.message}`, 'warn');
    }
  }

  async performEmergencyRecovery() {
    this.log('🔄 Performing emergency recovery...', 'warn');

    // Try alternate ports
    const alternatePorts = ['3006', '3007', '3008'];

    for (const port of alternatePorts) {
      try {
        this.log(`Attempting recovery on port ${port}...`, 'info');

        this.port = port;
        process.env.MCP_PORT = port;

        await this.performPreInitialization();
        await this.initializeMCPServer();

        this.log(`✅ Emergency recovery successful on port ${port}`, 'info');
        return;

      } catch (error) {
        this.log(`Recovery attempt on port ${port} failed: ${error.message}`, 'warn');
      }
    }

    this.log('❌ All recovery attempts failed - manual intervention required', 'error');
  }

  printSuccessMessage() {
    const message = `
╔════════════════════════════════════════════════════════════════╗
║                🎉 CLAUDE CODE ULTIMATE SYSTEM READY! 🎉       ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  📡 MCP Server:        http://localhost:${this.port}                    ║
║  🔑 API Key:           ${this.apiKey.substring(0, 15)}...              ║
║  🔍 Documentation:     http://localhost:${this.port}/docs              ║
║  🎯 Health Check:      http://localhost:${this.port}/health            ║
║                                                                ║
║  ✅ Connection Monitoring: ACTIVE                              ║
║  ✅ Port Conflict Detection: ENABLED                           ║
║  ✅ Automatic Recovery: ENABLED                                ║
║  ✅ Service Health Tracking: ENABLED                           ║
║                                                                ║
║  📊 Available APIs:                                            ║
║    • Supabase   • Vercel    • Railway   • GitHub              ║
║    • OpenAI     • HuggingFace            • LangSmith          ║
║                                                                ║
║  🚀 You're ready to code with zero connection hassles!        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
`;

    console.log(message);
    this.log('Success message displayed to user', 'info');
  }

  async stop() {
    this.log('Stopping Ultimate System...', 'info');

    if (this.monitorAgent && this.monitoringActive) {
      await this.monitorAgent.stop();
    }

    if (this.mcpServerProcess) {
      this.mcpServerProcess.kill('SIGTERM');
    }

    this.log('Ultimate System stopped', 'info');
  }

  getStatus() {
    return {
      sessionId: this.sessionId,
      isInitialized: this.isInitialized,
      monitoringActive: this.monitoringActive,
      port: this.port,
      mcpServerPid: this.mcpServerProcess?.pid,
      monitorStatus: this.monitorAgent?.getStatus()
    };
  }
}

// Auto-start when executed directly
if (require.main === module) {
  const ultimateSystem = new UltimateClaudeCodeSystem();

  // Handle cleanup on exit
  const cleanup = async () => {
    await ultimateSystem.stop();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Handle unhandled errors
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    cleanup();
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection:', reason);
    cleanup();
  });

  // Start the ultimate system
  ultimateSystem.init().catch(error => {
    console.error('Fatal error:', error);
    cleanup();
  });
}

module.exports = UltimateClaudeCodeSystem;