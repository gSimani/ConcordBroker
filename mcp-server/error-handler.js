/**
 * MCP Server Error Handler
 * Handles errors and attempts recovery
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { spawn } = require('child_process');

class MCPErrorHandler {
  constructor() {
    this.maxRetries = 3;
    this.retryDelay = 5000;
    this.logFile = path.join(__dirname, 'error.log');
  }

  log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level}] ${message}\n`;
    console.log(logMessage);
    fs.appendFileSync(this.logFile, logMessage);
  }

  async handleError(error) {
    this.log(`Error detected: ${error.message}`, 'ERROR');
    
    // Determine error type and appropriate recovery action
    if (error.message.includes('ECONNREFUSED')) {
      await this.handleConnectionError();
    } else if (error.message.includes('EADDRINUSE')) {
      await this.handlePortInUseError();
    } else if (error.message.includes('API')) {
      await this.handleAPIError(error);
    } else {
      await this.handleGenericError(error);
    }
  }

  async handleConnectionError() {
    this.log('Connection error detected, attempting to restart MCP Server...', 'WARN');
    
    for (let i = 0; i < this.maxRetries; i++) {
      try {
        // Check if server is responding
        await axios.get('http://localhost:3001/health', { timeout: 2000 });
        this.log('Server is responding', 'INFO');
        return true;
      } catch (error) {
        this.log(`Restart attempt ${i + 1}/${this.maxRetries}`, 'INFO');
        
        // Try to start the server
        const serverProcess = spawn('node', ['server.js'], {
          cwd: __dirname,
          detached: false,
          stdio: 'inherit'
        });
        
        // Wait for server to start
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        
        // Check if server started successfully
        try {
          await axios.get('http://localhost:3001/health', { timeout: 2000 });
          this.log('Server restarted successfully', 'INFO');
          return true;
        } catch (e) {
          this.log('Server restart failed', 'ERROR');
        }
      }
    }
    
    this.log('Failed to restart server after maximum retries', 'ERROR');
    return false;
  }

  async handlePortInUseError() {
    this.log('Port 3001 is already in use', 'ERROR');
    
    if (process.platform === 'win32') {
      try {
        const { execSync } = require('child_process');
        
        // Find process using port 3001
        const output = execSync('netstat -ano | findstr :3001', { encoding: 'utf8' });
        const lines = output.split('\n');
        
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          if (parts.length >= 5) {
            const pid = parts[parts.length - 1];
            this.log(`Killing process ${pid} using port 3001`, 'INFO');
            
            try {
              execSync(`taskkill /PID ${pid} /F`);
              this.log(`Process ${pid} killed`, 'INFO');
            } catch (e) {
              this.log(`Failed to kill process ${pid}`, 'ERROR');
            }
          }
        }
        
        // Wait a moment for port to be released
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Try to start server again
        return await this.handleConnectionError();
        
      } catch (error) {
        this.log('Failed to free port 3001', 'ERROR');
      }
    } else {
      this.log('Please manually kill the process using port 3001', 'ERROR');
    }
    
    return false;
  }

  async handleAPIError(error) {
    this.log(`API Error: ${error.message}`, 'ERROR');
    
    // Check which service is failing
    const services = ['vercel', 'railway', 'supabase', 'github', 'huggingface', 'openai'];
    
    for (const service of services) {
      if (error.message.toLowerCase().includes(service)) {
        this.log(`${service} service error detected`, 'WARN');
        await this.checkServiceCredentials(service);
      }
    }
  }

  async checkServiceCredentials(service) {
    const envFile = path.join(__dirname, '..', '.env.mcp');
    
    if (!fs.existsSync(envFile)) {
      this.log('.env.mcp file not found!', 'ERROR');
      this.log('Please create .env.mcp with your API credentials', 'ERROR');
      return false;
    }
    
    const envContent = fs.readFileSync(envFile, 'utf8');
    const serviceKeys = {
      vercel: 'VERCEL_API_TOKEN',
      railway: 'RAILWAY_API_TOKEN',
      supabase: 'SUPABASE_URL',
      github: 'GITHUB_API_TOKEN',
      huggingface: 'HUGGINGFACE_API_TOKEN',
      openai: 'OPENAI_API_KEY'
    };
    
    const key = serviceKeys[service];
    if (key && !envContent.includes(`${key}=`)) {
      this.log(`${key} not found in .env.mcp`, 'ERROR');
      this.log(`Please add ${key} to your .env.mcp file`, 'ERROR');
      return false;
    }
    
    this.log(`${service} credentials appear to be configured`, 'INFO');
    return true;
  }

  async handleGenericError(error) {
    this.log(`Generic error: ${error.message}`, 'ERROR');
    this.log('Stack trace:', 'DEBUG');
    this.log(error.stack, 'DEBUG');
    
    // Try basic recovery
    await this.handleConnectionError();
  }

  async checkSystemHealth() {
    this.log('Performing system health check...', 'INFO');
    
    const checks = {
      'Node.js': this.checkNodeVersion(),
      'Dependencies': this.checkDependencies(),
      'Port availability': this.checkPort(),
      'Environment variables': this.checkEnvVars(),
      'Server connectivity': this.checkServerConnectivity()
    };
    
    for (const [check, result] of Object.entries(checks)) {
      const status = await result;
      this.log(`${check}: ${status ? '✅ OK' : '❌ FAILED'}`, status ? 'INFO' : 'ERROR');
    }
  }

  async checkNodeVersion() {
    try {
      const { execSync } = require('child_process');
      const version = execSync('node --version', { encoding: 'utf8' }).trim();
      const major = parseInt(version.split('.')[0].replace('v', ''));
      return major >= 14;
    } catch (error) {
      return false;
    }
  }

  async checkDependencies() {
    const requiredModules = ['express', 'axios', 'ws', 'dotenv'];
    const modulesPath = path.join(__dirname, 'node_modules');
    
    if (!fs.existsSync(modulesPath)) {
      return false;
    }
    
    for (const module of requiredModules) {
      if (!fs.existsSync(path.join(modulesPath, module))) {
        return false;
      }
    }
    
    return true;
  }

  async checkPort() {
    try {
      await axios.get('http://localhost:3001/health', { timeout: 1000 });
      return true;
    } catch (error) {
      // Port might be free (which is good) or server is down
      return true;
    }
  }

  async checkEnvVars() {
    const envFile = path.join(__dirname, '..', '.env.mcp');
    return fs.existsSync(envFile);
  }

  async checkServerConnectivity() {
    try {
      await axios.get('http://localhost:3001/health', { timeout: 2000 });
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Run if called directly
if (require.main === module) {
  const handler = new MCPErrorHandler();
  
  // Check for error argument
  const errorMessage = process.argv[2];
  
  if (errorMessage) {
    handler.handleError(new Error(errorMessage));
  } else {
    handler.checkSystemHealth();
  }
}

module.exports = MCPErrorHandler;