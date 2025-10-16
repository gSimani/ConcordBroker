/**
 * Permanent Memory System for ConcordBroker MCP Server
 * Ensures rules are always followed and work is verified
 */

const fs = require('fs').promises;
const path = require('path');
const { createClient } = require('redis');

class PermanentMemorySystem {
  constructor() {
    this.memoryPath = path.join(__dirname, '../.memory');
    this.rulesPath = path.join(__dirname, '../CLAUDE.md');
    this.redisClient = null;
    this.memory = {
      rules: [],
      sessions: [],
      verifications: [],
      integrations: {},
      lastCheck: null
    };
  }

  async initialize() {
    console.log('🧠 Initializing Permanent Memory System...');

    // Create memory directory
    try {
      await fs.mkdir(this.memoryPath, { recursive: true });
    } catch (error) {
      // Directory exists
    }

    // Initialize Redis for distributed memory
    await this.initializeRedis();

    // Load rules from CLAUDE.md
    await this.loadRules();

    // Load previous memory state
    await this.loadMemory();

    // Start memory persistence loop
    this.startPersistenceLoop();

    console.log('✅ Permanent Memory System initialized');
    console.log(`📋 Loaded ${this.memory.rules.length} rules`);
    console.log(`💾 Memory path: ${this.memoryPath}`);
  }

  async initializeRedis() {
    // Skip Redis if URL is not configured
    if (!process.env.REDIS_URL) {
      console.log('⚠️  Redis not configured, using local memory only');
      this.redisClient = null;
      return;
    }

    try {
      this.redisClient = createClient({
        url: process.env.REDIS_URL,
        socket: {
          connectTimeout: 3000, // 3 second timeout
          reconnectStrategy: false // Don't auto-reconnect
        }
      });

      // Suppress error logging during connection attempt
      let errorHandler = () => {};
      this.redisClient.on('error', errorHandler);

      // Try to connect with timeout
      const connectPromise = this.redisClient.connect();
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Connection timeout')), 3000)
      );

      await Promise.race([connectPromise, timeoutPromise]);

      // Replace with real error handler after successful connection
      this.redisClient.removeListener('error', errorHandler);
      this.redisClient.on('error', (err) => {
        console.log('⚠️  Redis warning:', err.message);
      });

      console.log('✅ Redis memory cache connected');
    } catch (error) {
      console.log('⚠️  Redis not available, using local memory only');
      if (this.redisClient) {
        try {
          await this.redisClient.quit();
        } catch {}
      }
      this.redisClient = null;
    }
  }

  async loadRules() {
    try {
      const rulesContent = await fs.readFile(this.rulesPath, 'utf8');

      // Parse CLAUDE.md for rules
      const rules = [];

      // Extract Golden Rules
      const goldenRulesMatch = rulesContent.match(/### Rule 4: Golden Rules[\s\S]*?(?=###|$)/);
      if (goldenRulesMatch) {
        const goldenRules = goldenRulesMatch[0]
          .split('\n')
          .filter(line => line.trim().startsWith('1.') || line.trim().startsWith('2.') ||
                         line.trim().startsWith('3.') || line.trim().startsWith('4.') ||
                         line.trim().startsWith('5.'))
          .map(line => line.replace(/^\d+\.\s*\*\*/, '').replace(/\*\*$/, '').trim());
        rules.push(...goldenRules);
      }

      // Extract Rule 1: ONE UI Website - ONE Port - ONE Branch
      const rule1Match = rulesContent.match(/### Rule 1:.*?\n([\s\S]*?)(?=###|$)/);
      if (rule1Match) {
        rules.push('ONE UI Website - ONE Port (5191) - ONE Branch');
        rules.push('Kill zombie ports (5177-5180)');
        rules.push('Standard dev port: 5191');
      }

      // Extract Rule 2: Continuous Merge
      const rule2Match = rulesContent.match(/### Rule 2:.*?\n([\s\S]*?)(?=###|$)/);
      if (rule2Match) {
        rules.push('Commit after EVERY feature/fix');
        rules.push('Push commits immediately');
        rules.push('Never have uncommitted changes at end of session');
      }

      // Extract Rule 3: Verify Work Complete
      const rule3Match = rulesContent.match(/### Rule 3:.*?\n([\s\S]*?)(?=###|$)/);
      if (rule3Match) {
        rules.push('Run npm run verify:complete before ending session');
        rules.push('All changes must be committed to git');
        rules.push('All commits must be pushed to remote');
        rules.push('No zombie dev servers running');
      }

      this.memory.rules = rules;

      // Store in Redis
      if (this.redisClient) {
        await this.redisClient.set('concordbroker:rules', JSON.stringify(rules));
      }

    } catch (error) {
      console.error('❌ Error loading rules:', error.message);
    }
  }

  async loadMemory() {
    try {
      const memoryFile = path.join(this.memoryPath, 'state.json');
      const content = await fs.readFile(memoryFile, 'utf8');
      const savedMemory = JSON.parse(content);

      this.memory = {
        ...this.memory,
        ...savedMemory,
        lastCheck: new Date().toISOString()
      };

      console.log('✅ Previous memory state restored');
    } catch (error) {
      // No previous memory, start fresh
      console.log('📝 Starting with fresh memory state');
    }
  }

  async saveMemory() {
    try {
      const memoryFile = path.join(this.memoryPath, 'state.json');
      await fs.writeFile(
        memoryFile,
        JSON.stringify(this.memory, null, 2),
        'utf8'
      );

      // Also save to Redis
      if (this.redisClient) {
        await this.redisClient.set(
          'concordbroker:memory:state',
          JSON.stringify(this.memory),
          { EX: 86400 } // 24 hour expiry
        );
      }
    } catch (error) {
      console.error('❌ Error saving memory:', error.message);
    }
  }

  startPersistenceLoop() {
    // Save memory every 5 minutes
    setInterval(() => {
      this.saveMemory();
    }, 5 * 60 * 1000);

    // Check rules every 10 minutes
    setInterval(() => {
      this.checkRuleCompliance();
    }, 10 * 60 * 1000);
  }

  async recordSession(sessionData) {
    const session = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...sessionData
    };

    this.memory.sessions.push(session);

    // Keep only last 100 sessions
    if (this.memory.sessions.length > 100) {
      this.memory.sessions = this.memory.sessions.slice(-100);
    }

    await this.saveMemory();
    return session;
  }

  async recordVerification(verificationType, result) {
    const verification = {
      type: verificationType,
      result,
      timestamp: new Date().toISOString(),
      passed: result.success || result.passed || false
    };

    this.memory.verifications.push(verification);

    // Keep only last 200 verifications
    if (this.memory.verifications.length > 200) {
      this.memory.verifications = this.memory.verifications.slice(-200);
    }

    await this.saveMemory();
    return verification;
  }

  async recordIntegration(serviceName, status) {
    this.memory.integrations[serviceName] = {
      status,
      lastCheck: new Date().toISOString()
    };

    await this.saveMemory();
  }

  async checkRuleCompliance() {
    console.log('🔍 Checking rule compliance...');

    const checks = {
      gitStatus: await this.checkGitStatus(),
      portStatus: await this.checkPortStatus(),
      commitStatus: await this.checkCommitStatus()
    };

    const violations = [];

    if (checks.gitStatus.uncommittedChanges) {
      violations.push('Rule violation: Uncommitted changes detected');
    }

    if (checks.portStatus.zombiePorts.length > 0) {
      violations.push(`Rule violation: Zombie ports detected: ${checks.portStatus.zombiePorts.join(', ')}`);
    }

    if (checks.portStatus.wrongPort) {
      violations.push('Rule violation: Frontend not on port 5191');
    }

    if (violations.length > 0) {
      console.warn('⚠️  Rule violations detected:');
      violations.forEach(v => console.warn(`   - ${v}`));

      await this.recordVerification('rule_compliance', {
        passed: false,
        violations,
        checks
      });
    } else {
      console.log('✅ All rules compliant');
      await this.recordVerification('rule_compliance', {
        passed: true,
        checks
      });
    }

    return { violations, checks };
  }

  async checkGitStatus() {
    try {
      const { execSync } = require('child_process');
      const status = execSync('git status --porcelain', { encoding: 'utf8' });
      return {
        uncommittedChanges: status.trim().length > 0,
        details: status
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  async checkPortStatus() {
    try {
      const { execSync } = require('child_process');
      const ports = execSync('netstat -ano | findstr "LISTENING"', { encoding: 'utf8' });

      const zombiePorts = [5177, 5178, 5179, 5180].filter(port =>
        ports.includes(`:${port}`)
      );

      const has5191 = ports.includes(':5191');
      const has5173 = ports.includes(':5173');

      return {
        zombiePorts,
        wrongPort: has5173 && !has5191,
        correctPort: has5191
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  async checkCommitStatus() {
    try {
      const { execSync } = require('child_process');
      const unpushed = execSync('git log @{u}.. --oneline', { encoding: 'utf8' });
      return {
        hasUnpushedCommits: unpushed.trim().length > 0,
        details: unpushed
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  getRules() {
    return this.memory.rules;
  }

  getRecentSessions(count = 10) {
    return this.memory.sessions.slice(-count);
  }

  getRecentVerifications(count = 20) {
    return this.memory.verifications.slice(-count);
  }

  getIntegrationStatus() {
    return this.memory.integrations;
  }

  async getMemoryStats() {
    return {
      rules: this.memory.rules.length,
      sessions: this.memory.sessions.length,
      verifications: this.memory.verifications.length,
      integrations: Object.keys(this.memory.integrations).length,
      lastCheck: this.memory.lastCheck,
      redisConnected: this.redisClient !== null
    };
  }

  async shutdown() {
    console.log('🛑 Shutting down Permanent Memory System...');
    await this.saveMemory();
    if (this.redisClient) {
      await this.redisClient.quit();
    }
    console.log('✅ Memory saved and connections closed');
  }
}

module.exports = PermanentMemorySystem;
