/**
 * Claude Code Session Initializer
 * Automatically starts MCP server and establishes service connections
 * This script runs automatically when Claude Code starts
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

class ClaudeCodeMCPInitializer {
  constructor() {
    this.mcpServerProcess = null;
    // Use the dedicated port from .env.mcp
    this.serverPort = process.env.MCP_PORT || '3005';
    this.serverUrl = `http://localhost:${this.serverPort}`;
    this.apiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key-claude';
    this.maxRetries = 15; // Increased for reliability
    this.retryDelay = 3000; // Longer delay for stability
    this.sessionFile = path.join(__dirname, '.claude-session');
    this.logFile = path.join(__dirname, 'mcp-server', 'claude-init.log');

    // Load environment from .env.mcp
    this.loadMCPEnvironment();
  }

  loadMCPEnvironment() {
    // Load .env.mcp file for MCP-specific settings
    const envMcpPath = path.join(__dirname, '.env.mcp');
    if (fs.existsSync(envMcpPath)) {
      const envContent = fs.readFileSync(envMcpPath, 'utf8');
      const envLines = envContent.split('\n');

      for (const line of envLines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const [key, ...valueParts] = trimmed.split('=');
          if (key && valueParts.length > 0) {
            const value = valueParts.join('=');
            process.env[key] = value;
          }
        }
      }

      // Update port and API key from loaded environment
      this.serverPort = process.env.MCP_PORT || '3005';
      this.serverUrl = `http://localhost:${this.serverPort}`;
      this.apiKey = process.env.MCP_API_KEY || 'concordbroker-mcp-key-claude';

      this.log('✅ Loaded MCP environment configuration');
    } else {
      this.log('⚠️ .env.mcp not found, using default settings');
    }
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);

    // Also write to log file
    try {
      fs.appendFileSync(this.logFile, logMessage + '\n');
    } catch (e) {
      // Ignore log file errors
    }
  }

  async init() {
    this.log('🚀 Claude Code MCP Initializer starting...');
    
    // Check if this is a new session
    if (this.isNewSession()) {
      this.log('📝 New Claude Code session detected');
      await this.startMCPServer();
      await this.waitForServer();
      await this.initializeServices();
      await this.verifyConnections();
      this.createSessionMarker();
    } else {
      this.log('✅ MCP Server already running for this session');
      await this.checkServerHealth();
    }
  }

  isNewSession() {
    // Check if session file exists and is recent (within last hour)
    try {
      if (fs.existsSync(this.sessionFile)) {
        const stats = fs.statSync(this.sessionFile);
        const hourAgo = Date.now() - (60 * 60 * 1000);
        if (stats.mtimeMs > hourAgo) {
          return false;
        }
      }
    } catch (error) {
      this.log(`Session check error: ${error.message}`);
    }
    return true;
  }

  createSessionMarker() {
    fs.writeFileSync(this.sessionFile, JSON.stringify({
      startTime: new Date().toISOString(),
      pid: this.mcpServerProcess?.pid,
      services: this.connectedServices
    }, null, 2));
  }

  async startMCPServer() {
    this.log('🔧 Starting MCP Server...');
    
    // Kill any existing MCP server processes
    await this.killExistingServers();
    
    // Start the MCP server
    const serverPath = path.join(__dirname, 'mcp-server');
    
    this.mcpServerProcess = spawn('node', ['server.js'], {
      cwd: serverPath,
      env: {
        ...process.env,
        NODE_ENV: 'production',
        MCP_AUTO_START: 'true'
      },
      detached: false,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    // Capture server output
    this.mcpServerProcess.stdout.on('data', (data) => {
      this.log(`[MCP Server] ${data.toString().trim()}`);
    });

    this.mcpServerProcess.stderr.on('data', (data) => {
      this.log(`[MCP Server Error] ${data.toString().trim()}`);
    });

    this.mcpServerProcess.on('error', (error) => {
      this.log(`Failed to start MCP Server: ${error.message}`);
    });

    this.mcpServerProcess.on('exit', (code) => {
      this.log(`MCP Server exited with code ${code}`);
    });

    this.log(`MCP Server started with PID: ${this.mcpServerProcess.pid}`);
  }

  async killExistingServers() {
    try {
      // Check if server is already running on our dedicated port
      const response = await axios.get(`${this.serverUrl}/health`, { timeout: 2000 });
      if (response.data) {
        this.log(`⚠️ Found existing MCP Server on port ${this.serverPort}, shutting down...`);

        // Try graceful shutdown first
        try {
          await axios.post(`${this.serverUrl}/shutdown`, {}, {
            timeout: 3000,
            headers: { 'x-api-key': this.apiKey }
          });
        } catch (e) {
          // Server might not have shutdown endpoint, that's okay
        }

        // Wait for graceful shutdown
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (error) {
      // No existing server found, which is fine
    }

    // Kill any orphaned Node processes on our port (Windows)
    if (process.platform === 'win32') {
      try {
        const { execSync } = require('child_process');
        const netstatOutput = execSync(`netstat -ano | findstr :${this.serverPort}`, {
          encoding: 'utf8',
          timeout: 5000
        });

        if (netstatOutput.trim()) {
          this.log(`Found processes on port ${this.serverPort}, terminating...`);
          // Extract PIDs and kill them
          const lines = netstatOutput.trim().split('\n');
          const pids = new Set();

          for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 5) {
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
        }
      } catch (e) {
        // No process found on port, which is fine
      }
    }
  }

  async waitForServer() {
    this.log('⏳ Waiting for MCP Server to be ready...');
    
    for (let i = 0; i < this.maxRetries; i++) {
      try {
        const response = await axios.get(`${this.serverUrl}/health`, { timeout: 2000 });
        if (response.data && response.data.status === 'healthy') {
          this.log('✅ MCP Server is ready!');
          return true;
        }
      } catch (error) {
        this.log(`Waiting for server... (attempt ${i + 1}/${this.maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      }
    }
    
    throw new Error('MCP Server failed to start within timeout period');
  }

  async initializeServices() {
    this.log('🔌 Initializing service connections...');
    this.connectedServices = [];

    const services = [
      { name: 'Vercel', endpoint: '/api/vercel/project' },
      { name: 'Railway', endpoint: '/api/railway/status' },
      { name: 'Supabase', endpoint: '/api/supabase/User?limit=1' },
      { name: 'GitHub', endpoint: '/api/github/commits?limit=1' },
      { name: 'OpenAI', endpoint: '/api/openai/models', optional: true },
      { name: 'HuggingFace', endpoint: '/api/huggingface/models', optional: true }
    ];

    for (const service of services) {
      try {
        this.log(`Connecting to ${service.name}...`);
        const response = await axios.get(`${this.serverUrl}${service.endpoint}`, {
          headers: { 'x-api-key': this.apiKey },
          timeout: 8000 // Increased timeout
        });

        if (response.data) {
          this.log(`✅ ${service.name} connected successfully`);
          this.connectedServices.push(service.name);
        }
      } catch (error) {
        if (service.optional) {
          this.log(`ℹ️ ${service.name} connection optional, skipping: ${error.message.substring(0, 50)}...`);
        } else {
          this.log(`⚠️ ${service.name} connection failed: ${error.message.substring(0, 100)}...`);
        }
      }
    }

    this.log(`Successfully connected to ${this.connectedServices.length} services`);
  }

  async verifyConnections() {
    this.log('🔍 Verifying all connections...');

    try {
      const response = await axios.get(`${this.serverUrl}/health`, {
        headers: { 'x-api-key': this.apiKey },
        timeout: 10000
      });

      if (response.data && response.data.status === 'healthy') {
        this.log('✅ All service connections verified');
        this.log(`Connected services: ${this.connectedServices.join(', ')}`);

        // Display detailed service status
        if (response.data.services) {
          Object.entries(response.data.services).forEach(([service, status]) => {
            const icon = status.status === 'healthy' || status.status === 'configured' ? '✅' : '⚠️';
            this.log(`  ${icon} ${service}: ${status.status}`);
          });
        }

        return true;
      }
    } catch (error) {
      this.log(`⚠️ Connection verification failed: ${error.message.substring(0, 100)}...`);
    }

    return false;
  }

  async checkServerHealth() {
    try {
      const response = await axios.get(`${this.serverUrl}/health`, { timeout: 2000 });
      if (response.data && response.data.status === 'healthy') {
        this.log('✅ MCP Server is healthy');
        
        // Display service status
        if (response.data.services) {
          this.log('Service Status:');
          Object.entries(response.data.services).forEach(([service, status]) => {
            const icon = status.status === 'healthy' || status.status === 'configured' ? '✅' : '⚠️';
            this.log(`  ${icon} ${service}: ${status.status}`);
          });
        }
      }
    } catch (error) {
      this.log(`⚠️ MCP Server health check failed: ${error.message}`);
      this.log('Attempting to restart MCP Server...');
      await this.startMCPServer();
      await this.waitForServer();
    }
  }

  async establishWebSocketConnection() {
    this.log('🔌 Establishing WebSocket connection...');

    try {
      const WebSocket = require('ws');
      const wsUrl = `ws://localhost:${this.serverPort}`;

      this.ws = new WebSocket(wsUrl, {
        headers: { 'x-api-key': this.apiKey }
      });

      this.ws.on('open', () => {
        this.log('✅ WebSocket connected');

        // Subscribe to health updates
        this.ws.send(JSON.stringify({ type: 'health' }));
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          if (message.type === 'health_update') {
            // Silently track health updates
            this.lastHealthUpdate = message.data;
          }
        } catch (e) {
          // Ignore malformed messages
        }
      });

      this.ws.on('error', (error) => {
        this.log(`WebSocket error: ${error.message}`);
      });

      this.ws.on('close', () => {
        this.log('WebSocket connection closed');
      });
    } catch (error) {
      this.log(`Failed to establish WebSocket connection: ${error.message}`);
    }
  }

  async cleanup() {
    this.log('🧹 Cleaning up MCP Server...');
    
    if (this.ws) {
      this.ws.close();
    }
    
    if (this.mcpServerProcess) {
      this.mcpServerProcess.kill('SIGTERM');
    }
    
    // Remove session file
    if (fs.existsSync(this.sessionFile)) {
      fs.unlinkSync(this.sessionFile);
    }
  }
}

// Auto-start when this file is loaded
if (require.main === module) {
  const initializer = new ClaudeCodeMCPInitializer();
  
  // Handle cleanup on exit
  process.on('SIGINT', async () => {
    await initializer.cleanup();
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    await initializer.cleanup();
    process.exit(0);
  });
  
  // Start initialization
  initializer.init().catch(error => {
    console.error('Failed to initialize MCP Server:', error);
    process.exit(1);
  });
}

module.exports = ClaudeCodeMCPInitializer;