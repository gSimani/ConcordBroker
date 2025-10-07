#!/usr/bin/env node
/**
 * ConcordBroker AI Data Flow System Auto-Startup
 * Integrates with Claude Code sessions to automatically start AI monitoring
 *
 * This script is called automatically when Claude Code starts in this project
 */

const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');

// Configuration
const CONFIG = {
    AI_SYSTEM_DIR: path.join(__dirname, 'mcp-server', 'ai-agents'),
    LOGS_DIR: path.join(__dirname, 'logs'),
    PORTS: {
        MCP_SERVER: 3001,
        DATA_ORCHESTRATOR: 8001,
        FASTAPI_ENDPOINTS: 8002,
        AI_INTEGRATION: 8003,
        DASHBOARD: 8004
    },
    STARTUP_TIMEOUT: 30000, // 30 seconds
    PYTHON_ENV: process.env.PYTHON_ENV || 'python'
};

// Logging utility
class Logger {
    constructor(logFile) {
        this.logFile = logFile;
        this.ensureLogDir();
    }

    ensureLogDir() {
        if (!fs.existsSync(CONFIG.LOGS_DIR)) {
            fs.mkdirSync(CONFIG.LOGS_DIR, { recursive: true });
        }
    }

    log(level, message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            data
        };

        const logLine = `${timestamp} [${level}] ${message}${data ? ' ' + JSON.stringify(data) : ''}\n`;

        // Console output
        console.log(`🤖 AI System [${level}] ${message}`);

        // File output
        if (this.logFile) {
            fs.appendFileSync(this.logFile, logLine);
        }
    }

    info(message, data) { this.log('INFO', message, data); }
    warn(message, data) { this.log('WARN', message, data); }
    error(message, data) { this.log('ERROR', message, data); }
    success(message, data) { this.log('SUCCESS', message, data); }
}

// Port checker utility
function checkPort(port) {
    return new Promise((resolve) => {
        const server = net.createServer();
        server.listen(port, () => {
            server.once('close', () => resolve(false)); // Port is available
            server.close();
        });
        server.on('error', () => resolve(true)); // Port is in use
    });
}

// Service health checker
async function checkServiceHealth(port, endpoint = '/health') {
    try {
        const response = await fetch(`http://localhost:${port}${endpoint}`);
        return response.ok;
    } catch {
        return false;
    }
}

// AI System Manager
class AISystemManager {
    constructor() {
        this.logger = new Logger(path.join(CONFIG.LOGS_DIR, 'ai_system_startup.log'));
        this.processes = new Map();
        this.isInitialized = false;
    }

    async initialize() {
        this.logger.info('🚀 Initializing ConcordBroker AI Data Flow System...');

        try {
            // Check prerequisites
            await this.checkPrerequisites();

            // Start services in order
            await this.startDataOrchestrator();
            await this.startFastAPIEndpoints();
            await this.startAIIntegration();
            await this.startDashboard();

            this.isInitialized = true;
            this.logger.success('🎉 AI Data Flow System fully initialized!');

            // Register cleanup handlers
            this.registerCleanupHandlers();

            // Start health monitoring
            this.startHealthMonitoring();

            return true;

        } catch (error) {
            this.logger.error('❌ AI System initialization failed', { error: error.message });
            await this.cleanup();
            return false;
        }
    }

    async checkPrerequisites() {
        this.logger.info('🔍 Checking prerequisites...');

        // Check if Python is available
        try {
            const pythonVersion = await this.execCommand('python --version');
            this.logger.info('✅ Python available', { version: pythonVersion.trim() });
        } catch {
            try {
                const python3Version = await this.execCommand('python3 --version');
                this.logger.info('✅ Python3 available', { version: python3Version.trim() });
                CONFIG.PYTHON_ENV = 'python3';
            } catch {
                throw new Error('Python not found. Please install Python 3.8+');
            }
        }

        // Check if AI system directory exists
        if (!fs.existsSync(CONFIG.AI_SYSTEM_DIR)) {
            throw new Error(`AI system directory not found: ${CONFIG.AI_SYSTEM_DIR}`);
        }

        // Check for required Python files
        const requiredFiles = [
            'data_flow_orchestrator.py',
            'monitoring_agents.py',
            'self_healing_system.py',
            'mcp_integration.py'
        ];

        for (const file of requiredFiles) {
            const filePath = path.join(CONFIG.AI_SYSTEM_DIR, file);
            if (!fs.existsSync(filePath)) {
                throw new Error(`Required AI system file not found: ${file}`);
            }
        }

        // Check environment variables
        const requiredEnvVars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'];
        const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

        if (missingVars.length > 0) {
            this.logger.warn('⚠️ Missing optional environment variables', { missing: missingVars });
        }

        this.logger.success('✅ Prerequisites check completed');
    }

    async startDataOrchestrator() {
        this.logger.info('🔄 Starting Data Flow Orchestrator...');

        const isPortBusy = await checkPort(CONFIG.PORTS.DATA_ORCHESTRATOR);
        if (isPortBusy) {
            this.logger.info('📊 Data Orchestrator already running');
            return;
        }

        const process = spawn(CONFIG.PYTHON_ENV, [
            path.join(CONFIG.AI_SYSTEM_DIR, 'data_flow_orchestrator.py')
        ], {
            cwd: CONFIG.AI_SYSTEM_DIR,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PORT: CONFIG.PORTS.DATA_ORCHESTRATOR }
        });

        this.setupProcessLogging(process, 'DataOrchestrator');
        this.processes.set('data_orchestrator', process);

        // Wait for service to be ready
        await this.waitForService(CONFIG.PORTS.DATA_ORCHESTRATOR, 'Data Orchestrator');
        this.logger.success('✅ Data Flow Orchestrator started');
    }

    async startFastAPIEndpoints() {
        this.logger.info('⚡ Starting FastAPI Data Endpoints...');

        const isPortBusy = await checkPort(CONFIG.PORTS.FASTAPI_ENDPOINTS);
        if (isPortBusy) {
            this.logger.info('⚡ FastAPI endpoints already running');
            return;
        }

        const process = spawn(CONFIG.PYTHON_ENV, [
            path.join(__dirname, 'mcp-server', 'fastapi-endpoints', 'data_endpoints.py')
        ], {
            cwd: path.join(__dirname, 'mcp-server', 'fastapi-endpoints'),
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PORT: CONFIG.PORTS.FASTAPI_ENDPOINTS }
        });

        this.setupProcessLogging(process, 'FastAPI');
        this.processes.set('fastapi_endpoints', process);

        await this.waitForService(CONFIG.PORTS.FASTAPI_ENDPOINTS, 'FastAPI Endpoints');
        this.logger.success('✅ FastAPI Data Endpoints started');
    }

    async startAIIntegration() {
        this.logger.info('🤖 Starting AI Integration System...');

        const isPortBusy = await checkPort(CONFIG.PORTS.AI_INTEGRATION);
        if (isPortBusy) {
            this.logger.info('🤖 AI Integration already running');
            return;
        }

        const process = spawn(CONFIG.PYTHON_ENV, [
            path.join(CONFIG.AI_SYSTEM_DIR, 'mcp_integration.py')
        ], {
            cwd: CONFIG.AI_SYSTEM_DIR,
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PORT: CONFIG.PORTS.AI_INTEGRATION }
        });

        this.setupProcessLogging(process, 'AIIntegration');
        this.processes.set('ai_integration', process);

        await this.waitForService(CONFIG.PORTS.AI_INTEGRATION, 'AI Integration', '/ai-system/health');
        this.logger.success('✅ AI Integration System started');
    }

    async startDashboard() {
        this.logger.info('📊 Starting Monitoring Dashboard...');

        const isPortBusy = await checkPort(CONFIG.PORTS.DASHBOARD);
        if (isPortBusy) {
            this.logger.info('📊 Dashboard already running');
            return;
        }

        const process = spawn(CONFIG.PYTHON_ENV, [
            path.join(__dirname, 'mcp-server', 'monitoring', 'dashboard_server.py')
        ], {
            cwd: path.join(__dirname, 'mcp-server', 'monitoring'),
            stdio: ['ignore', 'pipe', 'pipe'],
            env: { ...process.env, PORT: CONFIG.PORTS.DASHBOARD }
        });

        this.setupProcessLogging(process, 'Dashboard');
        this.processes.set('dashboard', process);

        await this.waitForService(CONFIG.PORTS.DASHBOARD, 'Monitoring Dashboard');
        this.logger.success('✅ Monitoring Dashboard started');
    }

    setupProcessLogging(process, serviceName) {
        process.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                this.logger.info(`${serviceName}: ${output}`);
            }
        });

        process.stderr.on('data', (data) => {
            const output = data.toString().trim();
            if (output && !output.includes('WARNING')) {
                this.logger.error(`${serviceName} Error: ${output}`);
            }
        });

        process.on('exit', (code, signal) => {
            if (code !== 0) {
                this.logger.error(`${serviceName} exited`, { code, signal });
            } else {
                this.logger.info(`${serviceName} stopped gracefully`);
            }
        });
    }

    async waitForService(port, serviceName, endpoint = '/health') {
        const startTime = Date.now();
        const timeout = CONFIG.STARTUP_TIMEOUT;

        while (Date.now() - startTime < timeout) {
            try {
                const isHealthy = await checkServiceHealth(port, endpoint);
                if (isHealthy) {
                    return;
                }
            } catch {
                // Service not ready yet
            }

            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        throw new Error(`${serviceName} failed to start within ${timeout}ms`);
    }

    startHealthMonitoring() {
        this.logger.info('💓 Starting health monitoring...');

        setInterval(async () => {
            const services = [
                { name: 'Data Orchestrator', port: CONFIG.PORTS.DATA_ORCHESTRATOR },
                { name: 'FastAPI Endpoints', port: CONFIG.PORTS.FASTAPI_ENDPOINTS },
                { name: 'AI Integration', port: CONFIG.PORTS.AI_INTEGRATION, endpoint: '/ai-system/health' },
                { name: 'Dashboard', port: CONFIG.PORTS.DASHBOARD }
            ];

            for (const service of services) {
                const isHealthy = await checkServiceHealth(service.port, service.endpoint);
                if (!isHealthy) {
                    this.logger.warn(`❌ ${service.name} health check failed`);
                }
            }
        }, 60000); // Check every minute
    }

    registerCleanupHandlers() {
        const cleanup = async (signal) => {
            this.logger.info(`🛑 Received ${signal}, shutting down AI system...`);
            await this.cleanup();
            process.exit(0);
        };

        process.on('SIGINT', cleanup);
        process.on('SIGTERM', cleanup);
        process.on('beforeExit', cleanup);
    }

    async cleanup() {
        this.logger.info('🧹 Cleaning up AI system processes...');

        for (const [name, process] of this.processes) {
            try {
                process.kill('SIGTERM');
                this.logger.info(`Terminated ${name}`);
            } catch (error) {
                this.logger.error(`Failed to terminate ${name}`, { error: error.message });
            }
        }

        // Wait a bit for graceful shutdown
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Force kill if needed
        for (const [name, process] of this.processes) {
            try {
                if (!process.killed) {
                    process.kill('SIGKILL');
                    this.logger.info(`Force killed ${name}`);
                }
            } catch {
                // Process already dead
            }
        }

        this.processes.clear();
        this.logger.success('✅ AI system cleanup completed');
    }

    execCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(new Error(stderr || error.message));
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    getSystemStatus() {
        return {
            initialized: this.isInitialized,
            services: {
                data_orchestrator: `http://localhost:${CONFIG.PORTS.DATA_ORCHESTRATOR}`,
                fastapi_endpoints: `http://localhost:${CONFIG.PORTS.FASTAPI_ENDPOINTS}`,
                ai_integration: `http://localhost:${CONFIG.PORTS.AI_INTEGRATION}/ai-system/health`,
                dashboard: `http://localhost:${CONFIG.PORTS.DASHBOARD}`
            },
            processes: Array.from(this.processes.keys())
        };
    }
}

// Main execution
async function main() {
    console.log('\n🤖 ===== ConcordBroker AI Data Flow System =====');
    console.log('🚀 Auto-starting with Claude Code session...\n');

    const aiSystem = new AISystemManager();

    try {
        const success = await aiSystem.initialize();

        if (success) {
            const status = aiSystem.getSystemStatus();

            console.log('\n✨ ===== AI SYSTEM READY =====');
            console.log(`📊 Dashboard: ${status.services.dashboard}`);
            console.log(`🔗 AI API: ${status.services.ai_integration}`);
            console.log(`⚡ Data API: ${status.services.fastapi_endpoints}`);
            console.log(`🔄 Orchestrator: ${status.services.data_orchestrator}`);
            console.log('\n🎯 ACTIVE FEATURES:');
            console.log('   ✅ Real-time data flow monitoring');
            console.log('   ✅ AI-powered anomaly detection');
            console.log('   ✅ Self-healing data integrity');
            console.log('   ✅ Performance optimization');
            console.log('   ✅ Entity linking & deduplication');
            console.log('   ✅ Tax certificate monitoring');
            console.log('   ✅ Sales history validation');
            console.log('   ✅ Interactive monitoring dashboard');
            console.log('\n📋 JUPYTER NOTEBOOKS:');
            console.log('   📓 mcp-server/notebooks/data_flow_monitoring.ipynb');
            console.log('\n🔧 Claude Code Integration: ACTIVE');
            console.log('========================\n');

            // Keep the process running
            return new Promise(() => {}); // Never resolves, keeps process alive

        } else {
            console.error('\n❌ AI System initialization failed');
            process.exit(1);
        }

    } catch (error) {
        console.error('\n❌ Fatal error:', error.message);
        process.exit(1);
    }
}

// Export for use in other modules
module.exports = {
    AISystemManager,
    CONFIG
};

// Run if called directly
if (require.main === module) {
    main().catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}