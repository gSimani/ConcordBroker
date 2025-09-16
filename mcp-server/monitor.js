/**
 * Vercel Deployment Monitor
 * Real-time monitoring of ConcordBroker deployments
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  PROJECT_ID: 'prj_l6jgk7483iwPCcaYarq7sMgt2m7L',
  API_TOKEN: 't9AK4qQ51TyAc0K0ZLk7tN0H',
  CHECK_INTERVAL: 30000, // 30 seconds
  LOG_FILE: path.join(__dirname, 'deployment.log')
};

class DeploymentMonitor {
  constructor() {
    this.apiToken = CONFIG.API_TOKEN;
    this.projectId = CONFIG.PROJECT_ID;
    this.lastDeploymentId = null;
    this.stats = {
      totalDeployments: 0,
      successfulDeployments: 0,
      failedDeployments: 0,
      averageDeployTime: 0
    };
  }

  /**
   * Start monitoring
   */
  async start() {
    console.log('🔍 Starting Vercel Deployment Monitor');
    console.log(`📊 Monitoring project: ${this.projectId}`);
    console.log(`⏱️  Check interval: ${CONFIG.CHECK_INTERVAL / 1000} seconds\n`);

    // Initial check
    await this.checkDeployments();

    // Set up interval
    setInterval(async () => {
      await this.checkDeployments();
    }, CONFIG.CHECK_INTERVAL);

    // Handle graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n\n📊 Final Statistics:');
      this.printStats();
      process.exit(0);
    });
  }

  /**
   * Check recent deployments
   */
  async checkDeployments() {
    try {
      const deployments = await this.getDeployments(5);
      
      if (deployments.deployments && deployments.deployments.length > 0) {
        const latest = deployments.deployments[0];
        
        // Check if this is a new deployment
        if (latest.uid !== this.lastDeploymentId) {
          this.lastDeploymentId = latest.uid;
          await this.handleNewDeployment(latest);
        }

        // Update current status
        this.updateStatus(latest);
      }
    } catch (error) {
      console.error('❌ Monitoring error:', error.message);
      this.logToFile(`ERROR: ${error.message}`);
    }
  }

  /**
   * Handle new deployment detected
   */
  async handleNewDeployment(deployment) {
    console.log('\n🚀 New Deployment Detected!');
    console.log(`   ID: ${deployment.uid}`);
    console.log(`   URL: ${deployment.url}`);
    console.log(`   Status: ${deployment.readyState}`);
    console.log(`   Creator: ${deployment.creator?.username || 'Unknown'}`);
    console.log(`   Created: ${new Date(deployment.created).toLocaleString()}`);

    this.stats.totalDeployments++;

    // Track deployment progress
    await this.trackDeploymentProgress(deployment.uid);

    // Log deployment
    this.logToFile(`NEW_DEPLOYMENT: ${deployment.uid} - ${deployment.url}`);

    // Check deployment health
    if (deployment.readyState === 'READY') {
      await this.checkDeploymentHealth(deployment.url);
    }
  }

  /**
   * Track deployment progress
   */
  async trackDeploymentProgress(deploymentId) {
    const startTime = Date.now();
    let isComplete = false;
    let attempts = 0;
    const maxAttempts = 60; // 30 minutes max

    console.log('   ⏳ Tracking deployment progress...');

    while (!isComplete && attempts < maxAttempts) {
      try {
        const deployment = await this.getDeployment(deploymentId);
        
        switch (deployment.readyState) {
          case 'READY':
            const deployTime = (Date.now() - startTime) / 1000;
            console.log(`   ✅ Deployment successful! (${deployTime.toFixed(1)}s)`);
            this.stats.successfulDeployments++;
            this.updateAverageDeployTime(deployTime);
            isComplete = true;
            break;
            
          case 'ERROR':
            console.log(`   ❌ Deployment failed!`);
            this.stats.failedDeployments++;
            await this.getDeploymentLogs(deploymentId);
            isComplete = true;
            break;
            
          case 'CANCELED':
            console.log(`   ⚠️ Deployment canceled`);
            isComplete = true;
            break;
            
          default:
            process.stdout.write(`\r   ⏳ Status: ${deployment.readyState}...`);
        }
        
        if (!isComplete) {
          await this.sleep(5000); // Check every 5 seconds
          attempts++;
        }
      } catch (error) {
        console.error(`   ❌ Error tracking deployment: ${error.message}`);
        break;
      }
    }

    if (!isComplete && attempts >= maxAttempts) {
      console.log(`   ⚠️ Deployment tracking timeout`);
    }
  }

  /**
   * Check deployment health
   */
  async checkDeploymentHealth(deploymentUrl) {
    console.log('\n🏥 Health Check:');
    
    const checks = [
      { path: '/', name: 'Homepage' },
      { path: '/api/health', name: 'API Health' },
      { path: '/properties', name: 'Properties Page' }
    ];

    for (const check of checks) {
      try {
        const url = `https://${deploymentUrl}${check.path}`;
        const response = await this.checkUrl(url);
        
        if (response.statusCode === 200) {
          console.log(`   ✅ ${check.name}: OK (${response.responseTime}ms)`);
        } else {
          console.log(`   ⚠️ ${check.name}: Status ${response.statusCode}`);
        }
      } catch (error) {
        console.log(`   ❌ ${check.name}: Failed`);
      }
    }
  }

  /**
   * Update current status
   */
  updateStatus(deployment) {
    const status = `[${new Date().toLocaleTimeString()}] Latest: ${deployment.url} - ${deployment.readyState}`;
    process.stdout.write(`\r${status}`);
  }

  /**
   * Get deployment logs
   */
  async getDeploymentLogs(deploymentId) {
    try {
      const logs = await this.makeRequest('GET', `/v2/deployments/${deploymentId}/events?limit=10`);
      
      if (logs && logs.length > 0) {
        console.log('\n   📋 Recent logs:');
        logs.forEach(log => {
          console.log(`      ${log.created}: ${log.text}`);
        });
      }
    } catch (error) {
      console.log('   Could not retrieve logs');
    }
  }

  /**
   * Get deployments from Vercel API
   */
  async getDeployments(limit = 10) {
    return this.makeRequest('GET', `/v6/deployments?projectId=${this.projectId}&limit=${limit}`);
  }

  /**
   * Get single deployment
   */
  async getDeployment(deploymentId) {
    return this.makeRequest('GET', `/v13/deployments/${deploymentId}`);
  }

  /**
   * Check URL health
   */
  checkUrl(url) {
    return new Promise((resolve) => {
      const startTime = Date.now();
      
      https.get(url, (res) => {
        const responseTime = Date.now() - startTime;
        resolve({
          statusCode: res.statusCode,
          responseTime
        });
      }).on('error', () => {
        resolve({ statusCode: 0, responseTime: 0 });
      });
    });
  }

  /**
   * Make API request to Vercel
   */
  makeRequest(method, path) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.vercel.com',
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);
            resolve(parsed);
          } catch (error) {
            reject(new Error(`Parse error: ${data}`));
          }
        });
      });

      req.on('error', reject);
      req.end();
    });
  }

  /**
   * Update average deploy time
   */
  updateAverageDeployTime(time) {
    const total = this.stats.successfulDeployments;
    const currentAvg = this.stats.averageDeployTime;
    this.stats.averageDeployTime = ((currentAvg * (total - 1)) + time) / total;
  }

  /**
   * Print statistics
   */
  printStats() {
    console.log(`   Total Deployments: ${this.stats.totalDeployments}`);
    console.log(`   Successful: ${this.stats.successfulDeployments}`);
    console.log(`   Failed: ${this.stats.failedDeployments}`);
    console.log(`   Average Deploy Time: ${this.stats.averageDeployTime.toFixed(1)}s`);
    
    const successRate = this.stats.totalDeployments > 0 
      ? (this.stats.successfulDeployments / this.stats.totalDeployments * 100).toFixed(1)
      : 0;
    console.log(`   Success Rate: ${successRate}%`);
  }

  /**
   * Log to file
   */
  logToFile(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    
    fs.appendFileSync(CONFIG.LOG_FILE, logMessage);
  }

  /**
   * Sleep helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Start monitor
if (require.main === module) {
  const monitor = new DeploymentMonitor();
  monitor.start().catch(console.error);
}

module.exports = DeploymentMonitor;