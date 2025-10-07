/**
 * Production Parity Monitor Agent
 * AI-powered continuous monitoring and auto-sync for production-local parity
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

class ParityMonitorAgent {
    constructor(config = {}) {
        this.config = {
            checkInterval: config.checkInterval || 60000, // Check every minute
            autoSync: config.autoSync || false,
            services: config.services || ['vercel', 'railway', 'supabase'],
            webhookUrl: config.webhookUrl || null,
            logLevel: config.logLevel || 'info',
            ...config
        };

        this.state = {
            lastCheck: null,
            lastSync: null,
            productionCommit: null,
            localCommit: null,
            drifts: [],
            isHealthy: true
        };

        this.monitors = {
            vercel: new VercelMonitor(),
            railway: new RailwayMonitor(),
            supabase: new SupabaseMonitor(),
            git: new GitMonitor()
        };
    }

    async start() {
        console.log('🤖 Parity Monitor Agent starting...');
        await this.initialize();
        this.startMonitoring();
    }

    async initialize() {
        // Load previous state if exists
        try {
            const stateFile = path.join(__dirname, '.parity-state.json');
            const stateData = await fs.readFile(stateFile, 'utf8');
            this.state = { ...this.state, ...JSON.parse(stateData) };
        } catch (err) {
            // No previous state
        }

        // Initial check
        await this.performHealthCheck();
    }

    startMonitoring() {
        setInterval(async () => {
            await this.performHealthCheck();
            await this.checkForDrift();

            if (this.config.autoSync && this.state.drifts.length > 0) {
                await this.autoSync();
            }
        }, this.config.checkInterval);
    }

    async performHealthCheck() {
        const checks = {
            git: await this.monitors.git.checkHealth(),
            vercel: await this.monitors.vercel.checkHealth(),
            railway: await this.monitors.railway.checkHealth(),
            supabase: await this.monitors.supabase.checkHealth(),
            environment: await this.checkEnvironmentHealth(),
            dependencies: await this.checkDependencies()
        };

        this.state.isHealthy = Object.values(checks).every(check => check.healthy);
        this.state.lastCheck = new Date().toISOString();

        if (!this.state.isHealthy) {
            this.logIssues(checks);
            await this.notifyIssues(checks);
        }

        return checks;
    }

    async checkForDrift() {
        const drifts = [];

        // Check Git drift
        const gitDrift = await this.monitors.git.checkDrift();
        if (gitDrift) drifts.push(gitDrift);

        // Check environment drift
        const envDrift = await this.checkEnvironmentDrift();
        if (envDrift) drifts.push(envDrift);

        // Check schema drift (Supabase)
        const schemaDrift = await this.monitors.supabase.checkSchemaDrift();
        if (schemaDrift) drifts.push(schemaDrift);

        this.state.drifts = drifts;

        if (drifts.length > 0) {
            console.warn('⚠️ Drift detected:', drifts);
            await this.notifyDrift(drifts);
        }

        return drifts;
    }

    async autoSync() {
        console.log('🔄 Auto-syncing to resolve drift...');

        for (const drift of this.state.drifts) {
            try {
                switch (drift.type) {
                    case 'git':
                        await this.syncGitCommit(drift.targetCommit);
                        break;
                    case 'environment':
                        await this.syncEnvironment(drift.service);
                        break;
                    case 'schema':
                        await this.syncDatabaseSchema();
                        break;
                }
            } catch (error) {
                console.error(`Failed to sync ${drift.type}:`, error);
                await this.notifyError(error);
            }
        }

        this.state.lastSync = new Date().toISOString();
        await this.saveState();
    }

    async syncGitCommit(targetCommit) {
        console.log(`Syncing to commit ${targetCommit}...`);
        await execAsync(`git fetch --all && git checkout ${targetCommit}`);
    }

    async syncEnvironment(service) {
        console.log(`Syncing ${service} environment...`);

        switch (service) {
            case 'vercel':
                await execAsync('vercel env pull .env.local --environment=production --yes');
                break;
            case 'railway':
                await execAsync('railway variables > .env.railway');
                break;
        }

        // Process and clean environment files
        await this.processEnvironmentFiles();
    }

    async syncDatabaseSchema() {
        console.log('Syncing database schema...');
        await execAsync('supabase db pull && supabase db push');
    }

    async processEnvironmentFiles() {
        // Clean and merge environment files
        const envFiles = ['.env.local', '.env.railway', '.env.vercel.production'];
        const mergedEnv = {};

        for (const file of envFiles) {
            try {
                const content = await fs.readFile(file, 'utf8');
                const vars = this.parseEnvFile(content);
                Object.assign(mergedEnv, vars);
            } catch (err) {
                // File doesn't exist
            }
        }

        // Override with local URLs
        mergedEnv['VITE_API_URL'] = 'http://localhost:8000';
        mergedEnv['NEXT_PUBLIC_API_URL'] = 'http://localhost:8000';

        // Write consolidated env file
        const envContent = Object.entries(mergedEnv)
            .map(([key, value]) => `${key}=${value}`)
            .join('\n');

        await fs.writeFile('.env.local', envContent);
    }

    parseEnvFile(content) {
        const vars = {};
        const lines = content.split('\n');

        for (const line of lines) {
            const match = line.match(/^([^=]+)=(.*)$/);
            if (match) {
                vars[match[1]] = match[2];
            }
        }

        return vars;
    }

    async checkEnvironmentHealth() {
        const requiredVars = [
            'VITE_SUPABASE_URL',
            'VITE_SUPABASE_ANON_KEY',
            'VITE_API_URL'
        ];

        try {
            const envContent = await fs.readFile('.env.local', 'utf8');
            const vars = this.parseEnvFile(envContent);

            const missing = requiredVars.filter(v => !vars[v]);

            return {
                healthy: missing.length === 0,
                missing
            };
        } catch (err) {
            return {
                healthy: false,
                error: 'No .env.local file'
            };
        }
    }

    async checkDependencies() {
        try {
            const packageJson = JSON.parse(await fs.readFile('package.json', 'utf8'));
            const lockExists = await fs.access('package-lock.json').then(() => true).catch(() => false);

            return {
                healthy: lockExists,
                version: packageJson.version
            };
        } catch (err) {
            return {
                healthy: false,
                error: err.message
            };
        }
    }

    async checkEnvironmentDrift() {
        // Compare local env with production
        try {
            const { stdout: prodVars } = await execAsync('vercel env ls --environment=production');
            const localVars = await this.getLocalEnvironmentVars();

            const prodKeys = this.extractEnvKeys(prodVars);
            const localKeys = Object.keys(localVars);

            const missing = prodKeys.filter(k => !localKeys.includes(k));
            const extra = localKeys.filter(k => !prodKeys.includes(k));

            if (missing.length > 0 || extra.length > 0) {
                return {
                    type: 'environment',
                    service: 'vercel',
                    missing,
                    extra
                };
            }
        } catch (err) {
            console.error('Error checking environment drift:', err);
        }

        return null;
    }

    extractEnvKeys(vercelOutput) {
        // Parse Vercel CLI output to extract env var names
        const lines = vercelOutput.split('\n');
        const keys = [];

        for (const line of lines) {
            const match = line.match(/^\s*([A-Z_]+)\s+/);
            if (match) {
                keys.push(match[1]);
            }
        }

        return keys;
    }

    async getLocalEnvironmentVars() {
        try {
            const content = await fs.readFile('.env.local', 'utf8');
            return this.parseEnvFile(content);
        } catch (err) {
            return {};
        }
    }

    logIssues(checks) {
        console.log('\n=== PARITY HEALTH CHECK ===');

        for (const [service, check] of Object.entries(checks)) {
            if (!check.healthy) {
                console.log(`❌ ${service}:`, check);
            } else {
                console.log(`✅ ${service}: Healthy`);
            }
        }
    }

    async notifyIssues(checks) {
        if (this.config.webhookUrl) {
            // Send webhook notification
            const unhealthy = Object.entries(checks)
                .filter(([_, check]) => !check.healthy)
                .map(([service, check]) => ({ service, ...check }));

            await this.sendWebhook({
                type: 'health_check_failed',
                timestamp: new Date().toISOString(),
                issues: unhealthy
            });
        }
    }

    async notifyDrift(drifts) {
        if (this.config.webhookUrl) {
            await this.sendWebhook({
                type: 'drift_detected',
                timestamp: new Date().toISOString(),
                drifts
            });
        }
    }

    async notifyError(error) {
        if (this.config.webhookUrl) {
            await this.sendWebhook({
                type: 'sync_error',
                timestamp: new Date().toISOString(),
                error: error.message
            });
        }
    }

    async sendWebhook(data) {
        try {
            const fetch = (await import('node-fetch')).default;
            await fetch(this.config.webhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } catch (err) {
            console.error('Failed to send webhook:', err);
        }
    }

    async saveState() {
        const stateFile = path.join(__dirname, '.parity-state.json');
        await fs.writeFile(stateFile, JSON.stringify(this.state, null, 2));
    }
}

// Service Monitors
class GitMonitor {
    async checkHealth() {
        try {
            const { stdout } = await execAsync('git status --porcelain');
            const hasChanges = stdout.trim().length > 0;

            return {
                healthy: true,
                hasUncommittedChanges: hasChanges
            };
        } catch (err) {
            return {
                healthy: false,
                error: err.message
            };
        }
    }

    async checkDrift() {
        try {
            const { stdout: localCommit } = await execAsync('git rev-parse HEAD');
            const { stdout: remoteCommit } = await execAsync('git ls-remote origin HEAD');

            const local = localCommit.trim();
            const remote = remoteCommit.split('\t')[0].trim();

            if (local !== remote) {
                return {
                    type: 'git',
                    localCommit: local,
                    targetCommit: remote
                };
            }
        } catch (err) {
            console.error('Git drift check failed:', err);
        }

        return null;
    }
}

class VercelMonitor {
    async checkHealth() {
        try {
            const { stdout } = await execAsync('vercel whoami');
            return {
                healthy: stdout.includes('@'),
                user: stdout.trim()
            };
        } catch (err) {
            return {
                healthy: false,
                error: 'Not logged in to Vercel'
            };
        }
    }
}

class RailwayMonitor {
    async checkHealth() {
        try {
            const { stdout } = await execAsync('railway whoami');
            return {
                healthy: true,
                user: stdout.trim()
            };
        } catch (err) {
            return {
                healthy: false,
                error: 'Not logged in to Railway'
            };
        }
    }
}

class SupabaseMonitor {
    async checkHealth() {
        try {
            const { stdout } = await execAsync('supabase status');
            return {
                healthy: !stdout.includes('stopped'),
                status: stdout.trim()
            };
        } catch (err) {
            return {
                healthy: false,
                error: 'Supabase not running'
            };
        }
    }

    async checkSchemaDrift() {
        try {
            const { stdout } = await execAsync('supabase db diff');
            if (stdout.trim().length > 0) {
                return {
                    type: 'schema',
                    diff: stdout
                };
            }
        } catch (err) {
            console.error('Schema drift check failed:', err);
        }

        return null;
    }
}

// Export and run
module.exports = ParityMonitorAgent;

// Run if called directly
if (require.main === module) {
    const agent = new ParityMonitorAgent({
        checkInterval: 60000, // Check every minute
        autoSync: process.argv.includes('--auto-sync'),
        logLevel: process.argv.includes('--verbose') ? 'debug' : 'info'
    });

    agent.start().catch(console.error);

    // Handle shutdown gracefully
    process.on('SIGINT', async () => {
        console.log('\n👋 Shutting down monitor agent...');
        await agent.saveState();
        process.exit(0);
    });
}