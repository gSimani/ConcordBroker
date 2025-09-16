/**
 * Claude Code Robust Session Initializer
 * Automatically starts MCP server with improved error handling and failsafe mechanisms
 * Addresses all connection issues encountered during setup
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

class RobustClaudeCodeInitializer {
  constructor() {
    this.mcpServerProcess = null;
    this.sessionFile = path.join(__dirname, '.claude-session');
    this.logFile = path.join(__dirname, 'mcp-server', 'claude-init.log');

    // Load MCP-specific environment
    this.loadMCPEnvironment();

    // Configuration with failsafes
    this.serverPort = process.env.MCP_PORT || '3005';
    this.apiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key-claude';
    this.serverUrl = `http://localhost:${this.serverPort}`;
    this.maxRetries = 20;
    this.retryDelay = 3000;

    // Track initialization state
    this.initializationState = {
      environmentLoaded: false,
      serverStarted: false,
      servicesConnected: false,
      allHealthy: false
    };
  }

  loadMCPEnvironment() {
    const envMcpPath = path.join(__dirname, '.env.mcp');
    if (fs.existsSync(envMcpPath)) {
      try {
        const envContent = fs.readFileSync(envMcpPath, 'utf8');
        const envLines = envContent.split('\n');

        let loadedVars = 0;
        for (const line of envLines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            const [key, ...valueParts] = trimmed.split('=');
            if (key && valueParts.length > 0) {
              const value = valueParts.join('=');
              process.env[key] = value;
              loadedVars++;
            }
          }
        }

        this.initializationState.environmentLoaded = true;
        this.log(`✅ Loaded ${loadedVars} environment variables from .env.mcp`);
      } catch (error) {
        this.log(`⚠️ Error loading .env.mcp: ${error.message}`);
      }
    } else {
      this.log('⚠️ .env.mcp not found, using environment defaults');
    }
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);

    try {
      if (!fs.existsSync(path.dirname(this.logFile))) {
        fs.mkdirSync(path.dirname(this.logFile), { recursive: true });
      }
      fs.appendFileSync(this.logFile, logMessage + '\n');
    } catch (e) {
      // Ignore log file errors
    }
  }

  async init() {
    this.log('🚀 Claude Code Robust Initializer starting...');
    this.log(`Using port: ${this.serverPort}, API key: ${this.apiKey.substring(0, 10)}...`);

    try {
      // Step 1: Check if already running
      if (await this.checkExistingServer()) {
        this.log('✅ MCP Server already running and healthy');
        return;
      }

      // Step 2: Clean up any problematic processes
      await this.forceCleanup();

      // Step 3: Start server with retries
      await this.startServerWithRetries();

      // Step 4: Wait for server to be ready
      await this.waitForServerWithHealthCheck();

      // Step 5: Test core services
      await this.testCoreServices();

      // Step 6: Create session marker
      this.createSessionMarker();

      this.log('🎉 Claude Code initialization completed successfully!');
      this.log(`📡 MCP Server running at: ${this.serverUrl}`);
      this.log(`🔑 API Key: ${this.apiKey.substring(0, 10)}...`);

    } catch (error) {
      this.log(`❌ Initialization failed: ${error.message}`);
      this.log('🔄 Attempting recovery...');
      await this.attemptRecovery();
    }
  }

  async checkExistingServer() {
    try {
      const response = await axios.get(`${this.serverUrl}/health`, {
        timeout: 3000,
        headers: { 'x-api-key': this.apiKey }
      });

      if (response.data && response.data.status === 'healthy') {
        return true;
      }
    } catch (error) {
      // Server not running or not healthy
    }
    return false;
  }

  async forceCleanup() {
    this.log('🧹 Performing comprehensive cleanup...');

    // Kill processes on our port (Windows specific)
    if (process.platform === 'win32') {
      try {
        const { execSync } = require('child_process');

        // Find processes on our port
        try {
          const netstatOutput = execSync(`netstat -ano | findstr :${this.serverPort}`, {
            encoding: 'utf8',
            timeout: 5000
          });

          if (netstatOutput.trim()) {
            this.log(`Found processes on port ${this.serverPort}, terminating...`);

            const lines = netstatOutput.trim().split('\n');
            const pids = new Set();

            for (const line of lines) {
              const parts = line.trim().split(/\s+/);
              if (parts.length >= 5 && parts[4] !== '0') {
                pids.add(parts[4]);
              }
            }

            for (const pid of pids) {
              try {
                execSync(`taskkill /PID ${pid} /F`, { timeout: 3000 });
                this.log(`Killed process ${pid}`);
              } catch (e) {
                // Process might already be dead
              }
            }

            // Wait for processes to fully terminate
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } catch (e) {
          // No processes found, which is fine
        }

        // Also kill any orphaned node processes that might interfere
        try {
          execSync('taskkill /F /IM node.exe /FI "WINDOWTITLE eq *mcp*" 2>nul', { timeout: 5000 });
        } catch (e) {
          // No matching processes
        }

      } catch (error) {
        this.log(`Cleanup warning: ${error.message.substring(0, 100)}...`);
      }
    }

    // Additional cleanup wait
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  async startServerWithRetries() {
    this.log('🔧 Starting MCP Server with retry mechanism...');

    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        this.log(`Starting server attempt ${attempt}/3...`);

        const serverPath = path.join(__dirname, 'mcp-server');

        this.mcpServerProcess = spawn('npm', ['start'], {
          cwd: serverPath,
          env: {
            ...process.env,
            NODE_ENV: 'development',
            MCP_AUTO_START: 'true',
            DISABLE_LANGCHAIN: 'true' // Critical: disable problematic LangChain
          },
          detached: false,
          stdio: ['ignore', 'pipe', 'pipe']
        });

        // Capture output
        this.mcpServerProcess.stdout.on('data', (data) => {
          const output = data.toString().trim();
          if (output) {
            this.log(`[MCP Server] ${output}`);
          }
        });

        this.mcpServerProcess.stderr.on('data', (data) => {
          const output = data.toString().trim();
          if (output && !output.includes('DeprecationWarning')) {
            this.log(`[MCP Server Error] ${output}`);
          }
        });

        this.mcpServerProcess.on('error', (error) => {
          this.log(`Server process error: ${error.message}`);
        });

        this.mcpServerProcess.on('exit', (code) => {
          this.log(`MCP Server exited with code ${code}`);
          this.initializationState.serverStarted = false;
        });

        this.log(`MCP Server started with PID: ${this.mcpServerProcess.pid}`);
        this.initializationState.serverStarted = true;
        return;

      } catch (error) {
        this.log(`Start attempt ${attempt} failed: ${error.message}`);
        if (attempt < 3) {
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      }
    }

    throw new Error('Failed to start MCP Server after 3 attempts');
  }

  async waitForServerWithHealthCheck() {
    this.log('⏳ Waiting for MCP Server to be fully ready...');

    for (let i = 0; i < this.maxRetries; i++) {
      try {
        const response = await axios.get(`${this.serverUrl}/health`, {
          timeout: 5000,
          headers: { 'x-api-key': this.apiKey }
        });

        if (response.data && response.data.status === 'healthy') {
          this.log('✅ MCP Server is healthy and ready!');

          // Log service statuses
          if (response.data.services) {
            this.log('Service Status Summary:');
            Object.entries(response.data.services).forEach(([service, status]) => {
              const icon = status.status === 'healthy' || status.status === 'configured' ? '✅' : '⚠️';
              this.log(`  ${icon} ${service}: ${status.status}`);
            });
          }

          this.initializationState.allHealthy = true;
          return true;
        }
      } catch (error) {
        this.log(`Health check attempt ${i + 1}/${this.maxRetries}: ${error.message.substring(0, 50)}...`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      }
    }

    throw new Error('MCP Server failed to become healthy within timeout period');
  }

  async testCoreServices() {
    this.log('🔌 Testing core service connections...');

    const coreServices = [
      { name: 'Supabase', endpoint: '/api/supabase/User?limit=1' },
      { name: 'Vercel', endpoint: '/api/vercel/project' },
      { name: 'GitHub', endpoint: '/api/github/commits?limit=1' }
    ];

    let connectedCount = 0;
    for (const service of coreServices) {
      try {
        const response = await axios.get(`${this.serverUrl}${service.endpoint}`, {
          headers: { 'x-api-key': this.apiKey },
          timeout: 10000
        });

        if (response.data) {
          this.log(`✅ ${service.name} connection verified`);
          connectedCount++;
        }
      } catch (error) {
        this.log(`⚠️ ${service.name} test failed: ${error.message.substring(0, 80)}...`);
      }
    }

    this.log(`Successfully tested ${connectedCount}/${coreServices.length} core services`);
    this.initializationState.servicesConnected = connectedCount > 0;
  }

  async attemptRecovery() {
    this.log('🔄 Attempting recovery procedures...');

    // Try alternate port if current one fails
    const alternatePorts = ['3006', '3007', '3008'];

    for (const port of alternatePorts) {
      try {
        this.log(`Trying alternate port ${port}...`);
        this.serverPort = port;
        this.serverUrl = `http://localhost:${port}`;

        // Update environment
        process.env.MCP_PORT = port;

        await this.forceCleanup();
        await this.startServerWithRetries();
        await this.waitForServerWithHealthCheck();

        this.log(`✅ Recovery successful on port ${port}`);
        break;

      } catch (error) {
        this.log(`Recovery attempt on port ${port} failed: ${error.message}`);
      }
    }
  }

  createSessionMarker() {
    try {
      const sessionData = {
        startTime: new Date().toISOString(),
        pid: this.mcpServerProcess?.pid,
        port: this.serverPort,
        apiKey: this.apiKey.substring(0, 10) + '...',
        state: this.initializationState,
        url: this.serverUrl
      };

      fs.writeFileSync(this.sessionFile, JSON.stringify(sessionData, null, 2));
      this.log('📝 Session marker created');
    } catch (error) {
      this.log(`Warning: Could not create session marker: ${error.message}`);
    }
  }

  async cleanup() {
    this.log('🧹 Cleaning up resources...');

    if (this.mcpServerProcess) {
      try {
        this.mcpServerProcess.kill('SIGTERM');
        // Wait for graceful shutdown
        await new Promise(resolve => setTimeout(resolve, 2000));

        if (!this.mcpServerProcess.killed) {
          this.mcpServerProcess.kill('SIGKILL');
        }
      } catch (error) {
        this.log(`Cleanup error: ${error.message}`);
      }
    }

    // Remove session file
    try {
      if (fs.existsSync(this.sessionFile)) {
        fs.unlinkSync(this.sessionFile);
      }
    } catch (error) {
      // Ignore session file cleanup errors
    }
  }
}

// Auto-start when this file is executed
if (require.main === module) {
  const initializer = new RobustClaudeCodeInitializer();

  // Handle cleanup on exit
  process.on('SIGINT', async () => {
    await initializer.cleanup();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await initializer.cleanup();
    process.exit(0);
  });

  // Handle unhandled errors
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    initializer.cleanup().then(() => process.exit(1));
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    initializer.cleanup().then(() => process.exit(1));
  });

  // Start initialization with error handling
  initializer.init().catch(error => {
    console.error('Fatal initialization error:', error);
    initializer.cleanup().then(() => process.exit(1));
  });
}

module.exports = RobustClaudeCodeInitializer;